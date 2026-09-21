"""Round 3 re-read: gate requirements the lecturer named that were missing.

Item 1 of the mandatory-fixes list reads:

    "Terapkan aturan di backend bahwa kasus tidak dapat dikunci apabila PICO,
     CEA, BIA, sembilan domain EtD, rekomendasi, dan dua tahap sign-off belum
     lengkap."

PICO and the recorded sign-off were both absent from the gate. The Ketua report
separately asked that archiving not be a unilateral Admin IT action.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command

from apps.cases.completeness import evaluate_readiness
from apps.cases.models import Case, CaseStatus, DecisionQuestion
from apps.cases.state_machine import transition

pytestmark = pytest.mark.django_db


def _keys(readiness) -> dict[str, bool]:
    return {r["key"]: r["satisfied"] for r in readiness["requirements"]}


def _add_pico(case) -> DecisionQuestion:
    return DecisionQuestion.objects.create(
        case=case,
        order=1,
        question_text="Apakah ARNI perlu masuk formularium?",
        pico_population="Pasien HFrEF dewasa",
        pico_intervention="ARNI",
        pico_comparator="ACEI",
        pico_outcome="Rehospitalisasi 12 bulan",
    )


class TestPicoRequirement:
    def test_case_without_a_decision_question_fails_pico(self, pilot_case):
        assert _keys(evaluate_readiness(pilot_case))["pico"] is False

    def test_partially_filled_pico_does_not_count(self, pilot_case):
        DecisionQuestion.objects.create(
            case=pilot_case,
            order=1,
            question_text="Sebagian saja",
            pico_population="Pasien HFrEF",
            pico_intervention="ARNI",
            pico_comparator="",
            pico_outcome="",
        )

        assert _keys(evaluate_readiness(pilot_case))["pico"] is False

    def test_complete_pico_satisfies_the_requirement(self, pilot_case):
        _add_pico(pilot_case)

        assert _keys(evaluate_readiness(pilot_case))["pico"] is True

    def test_missing_pico_is_listed_among_the_gaps(self, pilot_case):
        assert "Pertanyaan keputusan (PICO) lengkap" in evaluate_readiness(pilot_case)["missing"]


class TestSignoffRequirement:
    def test_signoff_is_advisory_when_approving(self, pilot_case):
        """A signature cannot exist before the case is approved."""
        readiness = evaluate_readiness(pilot_case, action="approve")

        signoff = next(r for r in readiness["requirements"] if r["key"] == "signoff")
        assert signoff["mandatory"] is False

    def test_signoff_is_mandatory_when_locking(self, pilot_case):
        readiness = evaluate_readiness(pilot_case, action="lock")

        signoff = next(r for r in readiness["requirements"] if r["key"] == "signoff")
        assert signoff["mandatory"] is True
        assert "Sign-off Ketua KFT tercatat" in readiness["missing"]

    def test_lock_is_refused_without_a_recorded_signature(
        self, pilot_case, ketua_user, hta_user
    ):
        """The raw approve transition writes no Approval row, so this path could
        previously reach `locked` with no signature on file."""
        _add_pico(pilot_case)
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "approve", ketua_user)

        with pytest.raises(ValidationError) as exc:
            transition(pilot_case, "lock", ketua_user, enforce_completeness=True)

        assert "Sign-off Ketua KFT tercatat" in exc.value.params["missing"]


class TestArchiveAuthority:
    def test_admin_it_can_no_longer_archive_alone(self, pilot_case, admin_it_user):
        Case.objects.filter(pk=pilot_case.pk).update(status=CaseStatus.LOCKED)
        pilot_case.refresh_from_db()

        with pytest.raises(PermissionDenied):
            transition(pilot_case, "archive", admin_it_user, reason="retensi")

    def test_ketua_can_archive_with_a_reason(self, pilot_case, ketua_user):
        Case.objects.filter(pk=pilot_case.pk).update(status=CaseStatus.LOCKED)
        pilot_case.refresh_from_db()

        transition(pilot_case, "archive", ketua_user, reason="Digantikan versi baru")

        pilot_case.refresh_from_db()
        assert pilot_case.status == CaseStatus.ARCHIVED

    def test_archiving_requires_a_stated_reason(self, pilot_case, ketua_user):
        Case.objects.filter(pk=pilot_case.pk).update(status=CaseStatus.LOCKED)
        pilot_case.refresh_from_db()

        with pytest.raises(ValidationError):
            transition(pilot_case, "archive", ketua_user, reason="")


class TestValidatedDataStatus:
    def test_validated_is_an_accepted_parameter_status(self, pilot_case, hta_user):
        from apps.econ.models import DataStatus, EconomicModel, EconomicParameter

        model = EconomicModel.objects.create(
            case=pilot_case,
            horizon_years=1,
            cost_discount_rate=Decimal("0.03"),
            outcome_discount_rate=Decimal("0.03"),
            wtp_threshold=Decimal("85000000"),
            created_by=hta_user,
        )
        param = EconomicParameter.objects.create(
            economic_model=model,
            key="drug_cost",
            alternative="intervention",
            value=Decimal("15399360"),
            param_type="cost",
            data_status=DataStatus.VALIDATED,
            created_by=hta_user,
        )

        param.full_clean()
        assert param.data_status == "validated"


class TestSignoffFixtureCommand:
    def test_command_creates_both_in_review_cases(self, hta_user, kft_member_user):
        call_command("seed_signoff_test_cases", stdout=StringIO())

        incomplete = Case.objects.get(case_id="SIGNOFF_TEST_INCOMPLETE")
        complete = Case.objects.get(case_id="SIGNOFF_TEST_COMPLETE")
        assert incomplete.status == CaseStatus.IN_REVIEW
        assert complete.status == CaseStatus.IN_REVIEW

    def test_incomplete_fixture_is_refused_at_approval(self, hta_user, kft_member_user):
        call_command("seed_signoff_test_cases", stdout=StringIO())
        case = Case.objects.get(case_id="SIGNOFF_TEST_INCOMPLETE")

        readiness = evaluate_readiness(case, action="approve")

        assert readiness["is_ready"] is False
        assert _keys(readiness)["pico"] is True
        assert _keys(readiness)["economic_analysis"] is False

    def test_complete_fixture_passes_the_approval_gate(self, hta_user, kft_member_user):
        call_command("seed_signoff_test_cases", stdout=StringIO())
        case = Case.objects.get(case_id="SIGNOFF_TEST_COMPLETE")

        readiness = evaluate_readiness(case, action="approve")

        assert readiness["is_ready"] is True, readiness["missing"]

    def test_command_is_idempotent(self, hta_user, kft_member_user):
        call_command("seed_signoff_test_cases", stdout=StringIO())
        call_command("seed_signoff_test_cases", stdout=StringIO())

        assert Case.objects.filter(case_id="SIGNOFF_TEST_COMPLETE").count() == 1
