"""Round 5 item 1: no sign-off or lock on a missing or outdated PSA.

Pak Anom: "Sign-Off: tambah cek PSA. Kalau PSA belum dikerjakan atau sudah tidak
sesuai input terbaru -> belum boleh sign-off/lock." A recommendation computed before
its inputs changed is held back the same way (23092026 Panduan, section 15: CEA, BIA,
PSA, EtD and the recommendation must come from one version of the inputs).

Decisions already locked keep the rules they were locked under: the archive
integrity check, which runs on every deploy, and brief generation do not ask for PSA.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.approval.models import Approval, ApprovalDecision
from apps.approval.tests.conftest import _build_green_recommendation, _make_dossier_complete
from apps.cases.completeness import evaluate_readiness
from apps.cases.integrity import evaluate_integrity
from apps.cases.models import Case, CaseStatus
from apps.econ.models import EconDeterministicResult, EconomicModel
from apps.econ.tests.factories import make_psa_result
from apps.recommendation.tests.factories import make_final_decision

pytestmark = pytest.mark.django_db

PSA = "PSA dijalankan pada input terbaru"
CURRENT_REC = "Rekomendasi sesuai input terbaru"


def _requirement(report: dict, key: str) -> dict:
    return next(r for r in report["requirements"] if r["key"] == key)


def _change_an_input(case) -> None:
    model = EconomicModel.objects.get(case=case)
    model.wtp_threshold = Decimal("100000000")
    model.save()


def _force_status(case, status: str) -> None:
    Case.objects.filter(pk=case.pk).update(status=status)
    case.refresh_from_db()


@pytest.fixture
def ready_case(pilot_case, hta_user):
    """Everything sign-off needs, PSA and recommendation current."""
    _make_dossier_complete(pilot_case, hta_user)
    _build_green_recommendation(pilot_case, hta_user)
    make_final_decision(pilot_case, hta_user)
    return pilot_case


class TestPSARequirement:
    def test_the_complete_fixture_is_ready(self, ready_case):
        assert evaluate_readiness(ready_case, action="approve")["is_ready"] is True

    def test_no_psa_blocks_approval(self, pilot_case):
        report = evaluate_readiness(pilot_case, action="approve")

        psa = _requirement(report, "psa")
        assert psa["mandatory"] is True
        assert psa["satisfied"] is False
        assert psa["detail"] == "PSA belum dijalankan"
        assert PSA in report["missing"]

    def test_psa_is_not_asked_for_at_submit(self, pilot_case):
        report = evaluate_readiness(pilot_case, action="submit")

        assert _requirement(report, "psa")["mandatory"] is False

    def test_psa_on_the_current_inputs_passes(self, pilot_case, hta_user):
        make_psa_result(pilot_case, hta_user)

        psa = _requirement(evaluate_readiness(pilot_case, action="lock"), "psa")

        assert psa["satisfied"] is True
        assert "1,000 iterasi" in psa["detail"]
        assert "seed 42" in psa["detail"]

    def test_psa_is_outdated_once_an_input_changes(self, pilot_case, hta_user):
        make_psa_result(pilot_case, hta_user)
        _change_an_input(pilot_case)

        psa = _requirement(evaluate_readiness(pilot_case, action="approve"), "psa")

        assert psa["satisfied"] is False
        assert "jalankan ulang" in psa["detail"].lower()

    def test_psa_without_recorded_inputs_must_be_rerun(self, pilot_case, hta_user):
        make_psa_result(pilot_case, hta_user, record_inputs=False)

        psa = _requirement(evaluate_readiness(pilot_case, action="approve"), "psa")

        assert psa["satisfied"] is False
        assert "13 Oktober 2026" in psa["detail"]

    def test_only_the_latest_run_counts(self, pilot_case, hta_user):
        make_psa_result(pilot_case, hta_user, record_inputs=False)
        make_psa_result(pilot_case, hta_user)

        psa = _requirement(evaluate_readiness(pilot_case, action="approve"), "psa")

        assert psa["satisfied"] is True


class TestRecommendationMustBeCurrent:
    def test_recommendation_computed_before_the_economics_blocks(self, ready_case, hta_user):
        latest = EconDeterministicResult.objects.filter(case=ready_case).latest("computed_at")
        latest.pk = None
        latest.computed_at = timezone.now()
        latest.save()

        report = evaluate_readiness(ready_case, action="approve")

        current = _requirement(report, "recommendation_current")
        assert current["satisfied"] is False
        assert "CEA" in current["detail"]
        assert CURRENT_REC in report["missing"]

    def test_no_recommendation_is_reported_plainly(self, pilot_case):
        current = _requirement(evaluate_readiness(pilot_case), "recommendation_current")

        assert current["satisfied"] is False
        assert current["detail"] == "Belum ada rekomendasi"


class TestEndpointsRefuse:
    def test_sign_off_is_refused_on_an_outdated_psa(self, ketua_client, ready_case):
        _force_status(ready_case, CaseStatus.IN_REVIEW)
        _change_an_input(ready_case)
        rec = ready_case.recommendations.latest("computed_at")

        response = ketua_client.post(
            reverse("approval:sign", args=[ready_case.case_id]),
            {
                "recommendation_id": rec.pk,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": "TestPass123!",
            },
            format="json",
        )

        assert response.status_code == 422
        assert PSA in response.data["missing"]
        ready_case.refresh_from_db()
        assert ready_case.status == CaseStatus.IN_REVIEW
        assert not Approval.objects.filter(case=ready_case).exists()

    def test_lock_is_refused_when_the_psa_predates_recorded_inputs(
        self, ketua_client, pilot_case, hta_user, ketua_user
    ):
        """A case signed before this rule, with a PSA from before 2026-10-13."""
        _make_dossier_complete(pilot_case, hta_user)
        make_psa_result(pilot_case, hta_user, record_inputs=False)
        rec = _build_green_recommendation(pilot_case, hta_user)
        decision = make_final_decision(pilot_case, ketua_user, recommendation=rec)
        Approval.objects.create(
            case=pilot_case,
            recommendation=rec,
            final_decision=decision,
            approver=ketua_user,
            decision=ApprovalDecision.APPROVED,
            confirmation_acknowledged=True,
            password_verified_at=timezone.now(),
        )
        _force_status(pilot_case, CaseStatus.APPROVED)

        response = ketua_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/", {"action": "lock"}, format="json"
        )

        assert response.status_code == 422
        assert response.data["missing"] == [PSA]
        pilot_case.refresh_from_db()
        assert pilot_case.status == CaseStatus.APPROVED


class TestLockedDecisionsKeepTheirRules:
    def test_integrity_audit_does_not_ask_for_psa(self, pilot_case):
        failures = evaluate_integrity(pilot_case)["failures"]

        assert PSA not in failures
        assert CURRENT_REC not in failures

    def test_brief_does_not_ask_for_psa(self, pilot_case):
        report = evaluate_readiness(pilot_case, action="brief")

        assert PSA not in report["missing"]
        assert CURRENT_REC not in report["missing"]


class TestChecklistOnLockedCases:
    def test_a_locked_case_is_shown_against_the_rules_it_was_locked_under(
        self, hta_client, pilot_case
    ):
        """Old locked cases have no PSA; their checklist must not turn red for it."""
        _force_status(pilot_case, CaseStatus.LOCKED)

        report = hta_client.get(f"/api/v1/cases/{pilot_case.case_id}/readiness/").data

        assert _requirement(report, "psa")["mandatory"] is False
        assert _requirement(report, "signoff")["mandatory"] is True
