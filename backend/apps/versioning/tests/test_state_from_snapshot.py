"""A locked case built on apps.econ must show its figures on the Versi tab.

Such a case has no legacy CEAResult/BIAResult rows, so the pointer-based state
answered "Tidak ada data untuk versi ini" for CEA and BIA although both were in
the lock snapshot. Found while capturing the manual: the training case, locked
with every menu complete, showed no economics under Versi > Keadaan Data.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.cases.models import Case, CaseVersion
from apps.cases.state_machine import transition

pytestmark = pytest.mark.django_db

CASE_ID = "DB_DEMO_HF_001"


@pytest.fixture
def locked_demo(hta_user, ketua_user) -> Case:
    call_command("seed_demo_training_case", stdout=StringIO())
    case = Case.objects.get(case_id=CASE_ID)
    transition(case, "submit", hta_user)
    transition(case, "approve", ketua_user)
    transition(case, "lock", ketua_user)
    return case


def _locked_version(case: Case) -> CaseVersion:
    return CaseVersion.objects.get(case=case, status="locked")


def _state(client, case: Case) -> dict:
    version = _locked_version(case)
    return client.get(f"/api/v1/cases/{case.case_id}/versions/{version.pk}/state/").data


class TestStateReadsTheLockSnapshot:
    def test_deterministic_figures(self, hta_client, locked_demo):
        cea = _state(hta_client, locked_demo)["cea"]

        assert Decimal(cea["incremental_cost"]) == Decimal("12400000")
        assert abs(Decimal(cea["icer"]) - Decimal("225454545.45")) < Decimal("0.01")
        assert Decimal(cea["inb"]) == Decimal("4100000")
        assert cea["decision_code"] == "cost_effective"

    def test_budget_impact_figures_with_each_year(self, hta_client, locked_demo):
        bia = _state(hta_client, locked_demo)["bia"]

        assert Decimal(bia["cumulative_net_impact"]) == Decimal("2938800000")
        assert Decimal(bia["net_impact_year_1"]) == Decimal("496000000")
        assert Decimal(bia["net_impact_year_2"]) == Decimal("954800000")
        assert Decimal(bia["net_impact_year_3"]) == Decimal("1488000000")

    def test_psa_summary(self, hta_client, locked_demo):
        psa = _state(hta_client, locked_demo)["psa"]

        assert psa["n_simulations"] == 5000
        assert psa["random_seed"] == 42
        assert Decimal(psa["prob_cost_effective_base"]) == Decimal("0.5602")

    def test_blocks_stay_flat(self, hta_client, locked_demo):
        """The screen prints key/value rows; nested tables belong to the snapshot."""
        state = _state(hta_client, locked_demo)

        for block in ("cea", "bia", "psa"):
            assert not any(isinstance(v, (dict, list)) for v in state[block].values())


class TestDiffReadsTheLockSnapshot:
    def test_economics_appear_between_creation_and_lock(self, hta_client, hta_user, locked_demo):
        # The seeder builds the case through the ORM, which skips the v0.1 row
        # the API writes on creation.
        created = CaseVersion.objects.create(
            case=locked_demo, version_number="0.1.0", created_by=hta_user
        )
        locked = _locked_version(locked_demo)

        response = hta_client.get(
            f"/api/v1/cases/{CASE_ID}/versions/diff/?from={created.pk}&to={locked.pk}"
        )

        diff = response.data["diff"]
        assert diff["cea"]["icer"]["from"] is None
        assert Decimal(diff["cea"]["icer"]["to"]).quantize(Decimal("0.01")) == Decimal(
            "225454545.45"
        )
        assert "prob_cost_effective_base" in diff["psa"]


class TestSignerAddressIsMasked:
    """Sign-Off and the audit timeline already mask it; this panel printed it in full."""

    @pytest.fixture
    def signed_and_locked(self, hta_user, ketua_user) -> Case:
        from django.utils import timezone

        from apps.approval.models import Approval, ApprovalDecision

        from .conftest import _make_recommendation

        call_command("seed_demo_training_case", stdout=StringIO())
        case = Case.objects.get(case_id=CASE_ID)
        transition(case, "submit", hta_user)
        Approval.objects.create(
            case=case,
            recommendation=_make_recommendation(case, hta_user),
            approver=ketua_user,
            decision=ApprovalDecision.APPROVED,
            confirmation_acknowledged=True,
            password_verified_at=timezone.now(),
            ip_address="203.0.113.77",
        )
        transition(case, "approve", ketua_user)
        transition(case, "lock", ketua_user)
        return case

    def test_other_roles_see_a_masked_address(self, hta_client, signed_and_locked):
        approval = _state(hta_client, signed_and_locked)["approval"]

        assert approval["ip_address"] == "203.0.113.xxx"

    def test_admin_it_sees_the_full_address(self, admin_it_client, signed_and_locked):
        approval = _state(admin_it_client, signed_and_locked)["approval"]

        assert approval["ip_address"] == "203.0.113.77"


class TestLegacyVersions:
    """Versions locked before the snapshot existed keep showing what was locked."""

    @pytest.fixture
    def legacy_result(self, pilot_case, hta_user):
        from apps.cea.models import CEAResult

        return CEAResult.objects.create(
            case=pilot_case,
            input_snapshot={},
            incremental_cost=Decimal("5000000"),
            incremental_effect=Decimal("0.5"),
            icer_value=Decimal("10000000"),
            wtop_threshold_used=Decimal("250000000"),
            dominance="cost_effective",
            ce_score=100,
            interpretation_text="legacy",
            algorithm_version="1.0.0",
            computed_by=hta_user,
        )

    def _version(self, case, user, legacy_result, snapshot) -> CaseVersion:
        return CaseVersion.objects.create(
            case=case,
            version_number="1.0",
            status="locked",
            cea_result_id=legacy_result.pk,
            snapshot=snapshot,
            created_by=user,
        )

    def _cea(self, client, case, version) -> dict:
        return client.get(f"/api/v1/cases/{case.case_id}/versions/{version.pk}/state/").data["cea"]

    def test_no_snapshot_falls_back_to_the_pointer_row(
        self, hta_client, hta_user, pilot_case, legacy_result
    ):
        version = self._version(pilot_case, hta_user, legacy_result, None)

        assert self._cea(hta_client, pilot_case, version)["icer_value"] == "10000000.00"

    def test_backfilled_snapshot_does_not_replace_the_locked_row(
        self, hta_client, hta_user, pilot_case, legacy_result
    ):
        """A backfill reads the case as it is now, which can be later than the lock."""
        later = {"backfilled": True, "econ": {"deterministic": {"icer": "999"}}}
        version = self._version(pilot_case, hta_user, legacy_result, later)

        cea = self._cea(hta_client, pilot_case, version)

        assert cea["icer_value"] == "10000000.00"
        assert "icer" not in cea

    def test_snapshot_taken_at_lock_is_authoritative(
        self, hta_client, hta_user, pilot_case, legacy_result
    ):
        at_lock = {"econ": {"deterministic": {"icer": "203636363.64"}}}
        version = self._version(pilot_case, hta_user, legacy_result, at_lock)

        assert self._cea(hta_client, pilot_case, version)["icer"] == "203636363.64"
