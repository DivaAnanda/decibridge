"""Round 5 item 4: revising a locked case makes a new version; the old one stays.

Pak Anom: "Versi: kalau kasus sudah locked dan perlu revisi, buat versi/revisi baru,
jangan mengubah versi yang lama." Analis HTA or Ketua KFT reopens a locked (not
archived) case with a reason. The case returns to Draft, a revision row records the
reason, v1.0 and its snapshot stay as they were, and the next lock becomes v1.1. The
new version needs its own KFT decision and its own signature.
"""

from __future__ import annotations

import pytest
from django.utils import timezone

from apps.approval.models import Approval, ApprovalDecision
from apps.approval.tests.conftest import _build_green_recommendation, _make_dossier_complete
from apps.cases.completeness import evaluate_readiness
from apps.cases.models import Case, CaseStatus, CaseVersion, CaseVersionTrigger
from apps.cases.state_machine import transition
from apps.recommendation.tests.factories import make_final_decision

pytestmark = pytest.mark.django_db

REASON = "Harga ARNI turun setelah negosiasi; hitung ulang dengan harga baru."
SIGNOFF = "Sign-off Ketua KFT tercatat"


def _revise(client, case, reason: str = REASON):
    payload = {"action": "revise", "reason": reason} if reason is not None else {"action": "revise"}
    return client.post(f"/api/v1/cases/{case.case_id}/transition/", payload, format="json")


def _sign(case, user) -> Approval:
    return Approval.objects.create(
        case=case,
        recommendation=case.recommendations.latest("computed_at"),
        final_decision=case.final_decisions.first(),
        approver=user,
        decision=ApprovalDecision.APPROVED,
        confirmation_acknowledged=True,
        password_verified_at=timezone.now(),
    )


def _requirement(report: dict, key: str) -> dict:
    return next(r for r in report["requirements"] if r["key"] == key)


@pytest.fixture
def locked_v1(pilot_case, hta_user, ketua_user, kft_member_user) -> Case:
    _make_dossier_complete(pilot_case, hta_user)
    _build_green_recommendation(pilot_case, hta_user)
    make_final_decision(pilot_case, kft_member_user)
    transition(pilot_case, "submit", hta_user)
    _sign(pilot_case, ketua_user)
    transition(pilot_case, "approve", ketua_user)
    transition(pilot_case, "lock", ketua_user)
    pilot_case.refresh_from_db()
    return pilot_case


def _v1(case) -> CaseVersion:
    return CaseVersion.objects.get(case=case, version_number="1.0")


class TestWhoMayRevise:
    @pytest.mark.parametrize("client_name", ["hta_client", "ketua_client"])
    def test_hta_and_ketua_may(self, request, client_name, locked_v1):
        response = _revise(request.getfixturevalue(client_name), locked_v1)

        assert response.status_code == 200, response.data
        locked_v1.refresh_from_db()
        assert locked_v1.status == CaseStatus.DRAFT

    @pytest.mark.parametrize(
        "client_name", ["sekretaris_client", "kft_member_client", "admin_it_client"]
    )
    def test_other_roles_may_not(self, request, client_name, locked_v1):
        response = _revise(request.getfixturevalue(client_name), locked_v1)

        assert response.status_code == 403
        locked_v1.refresh_from_db()
        assert locked_v1.status == CaseStatus.LOCKED

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_a_reason_is_required(self, hta_client, locked_v1, reason):
        assert _revise(hta_client, locked_v1, reason).status_code == 400

    def test_an_archived_case_cannot_be_revised(self, hta_client, locked_v1, ketua_user):
        transition(locked_v1, "archive", ketua_user, reason="Selesai")

        assert _revise(hta_client, locked_v1).status_code == 400

    def test_only_a_locked_case_can_be_revised(self, hta_client, pilot_case):
        assert _revise(hta_client, pilot_case).status_code == 400

    def test_the_action_is_offered_on_a_locked_case(self, hta_client, locked_v1):
        detail = hta_client.get(f"/api/v1/cases/{locked_v1.case_id}/").data

        assert "revise" in [t["name"] for t in detail["allowed_transitions"]]


class TestTheOldVersionStays:
    def test_a_revision_row_records_the_reason(self, hta_client, hta_user, locked_v1):
        _revise(hta_client, locked_v1)

        row = CaseVersion.objects.get(
            case=locked_v1, trigger=CaseVersionTrigger.REVISION_REQUESTED
        )
        assert row.version_number == "1.1-draft"
        assert row.status == "draft"
        assert row.lock_reason == REASON
        assert row.diff == {"revises_version": "1.0", "revises_version_id": _v1(locked_v1).pk}
        assert row.created_by == hta_user

    def test_v1_and_its_snapshot_are_unchanged(self, hta_client, locked_v1):
        before = _v1(locked_v1).snapshot

        _revise(hta_client, locked_v1)

        v1 = _v1(locked_v1)
        assert v1.status == "locked"
        assert v1.snapshot == before

    def test_the_case_can_be_edited_again(self, hta_client, locked_v1):
        _revise(hta_client, locked_v1)

        response = hta_client.patch(
            f"/api/v1/cases/{locked_v1.case_id}/", {"case_title": "Revisi harga"}, format="json"
        )

        assert response.status_code == 200

    def test_the_next_lock_is_v1_1(
        self, hta_client, locked_v1, hta_user, ketua_user, kft_member_user
    ):
        _revise(hta_client, locked_v1)
        locked_v1.refresh_from_db()
        make_final_decision(locked_v1, kft_member_user)
        transition(locked_v1, "submit", hta_user)
        _sign(locked_v1, ketua_user)
        transition(locked_v1, "approve", ketua_user)
        transition(locked_v1, "lock", ketua_user)

        locked = CaseVersion.objects.filter(case=locked_v1, status="locked").order_by("id")
        assert [v.version_number for v in locked] == ["1.0", "1.1"]
        diff = hta_client.get(
            f"/api/v1/cases/{locked_v1.case_id}/versions/diff/"
            f"?from={locked[0].pk}&to={locked[1].pk}"
        )
        assert diff.status_code == 200

    def test_the_transition_response_lists_the_new_version(self, hta_client, locked_v1):
        versions = _revise(hta_client, locked_v1).data["versions"]

        assert versions[0]["version_number"] == "1.1-draft"

    def test_case_detail_names_each_version_trigger(self, hta_client, locked_v1):
        _revise(hta_client, locked_v1)

        versions = hta_client.get(f"/api/v1/cases/{locked_v1.case_id}/").data["versions"]

        assert versions[0]["trigger"] == "revision_requested"
        assert versions[0]["lock_reason"] == REASON


class TestTheNewVersionNeedsItsOwnDecision:
    def test_the_v1_signature_does_not_lock_v1_1(self, hta_client, locked_v1):
        _revise(hta_client, locked_v1)
        Case.objects.filter(pk=locked_v1.pk).update(status=CaseStatus.APPROVED)

        report = evaluate_readiness(locked_v1, action="lock")

        assert SIGNOFF in report["missing"]
        assert _requirement(report, "signoff")["detail"] == "Belum ada tanda tangan untuk versi ini"

    def test_the_v1_decision_must_be_confirmed_again(self, hta_client, locked_v1):
        _revise(hta_client, locked_v1)

        decision = _requirement(evaluate_readiness(locked_v1, action="approve"), "final_decision")

        assert decision["satisfied"] is False
        assert "versi sebelumnya" in decision["detail"]

    def test_a_new_decision_and_signature_complete_it(
        self, hta_client, locked_v1, ketua_user, kft_member_user
    ):
        _revise(hta_client, locked_v1)
        make_final_decision(locked_v1, kft_member_user)
        _sign(locked_v1, ketua_user)

        assert evaluate_readiness(locked_v1, action="lock")["is_ready"] is True

    def test_cases_never_revised_keep_their_signature(self, locked_v1):
        """An ordinary first lock is judged exactly as before."""
        assert _requirement(evaluate_readiness(locked_v1, action="lock"), "signoff")["satisfied"]


class TestTheNewVersionDoesNotInherit:
    """Code review: a rejection, or v1.0's own rows, carried into v1.1."""

    def test_a_rejection_after_the_revision_does_not_lock_it(
        self, hta_client, locked_v1, ketua_user, kft_member_user
    ):
        _revise(hta_client, locked_v1)
        make_final_decision(locked_v1, kft_member_user)
        Approval.objects.create(
            case=locked_v1,
            recommendation=locked_v1.recommendations.latest("computed_at"),
            final_decision=locked_v1.final_decisions.first(),
            approver=ketua_user,
            decision=ApprovalDecision.REJECTED,
            reason="Belum memadai",
            confirmation_acknowledged=True,
            password_verified_at=timezone.now(),
        )
        Case.objects.filter(pk=locked_v1.pk).update(status=CaseStatus.APPROVED)

        assert SIGNOFF in evaluate_readiness(locked_v1, action="lock")["missing"]

    def test_v1_1_does_not_point_at_the_v1_0_brief_or_signature(
        self, hta_client, locked_v1, hta_user, ketua_user, kft_member_user
    ):
        from apps.policy_brief.models import PolicyBriefDocument

        v1 = _v1(locked_v1)
        old_brief = PolicyBriefDocument.objects.create(
            case=locked_v1, version=1, status="completed", generated_by=hta_user
        )
        _revise(hta_client, locked_v1)
        locked_v1.refresh_from_db()
        make_final_decision(locked_v1, kft_member_user)
        transition(locked_v1, "submit", hta_user)
        new_signature = _sign(locked_v1, ketua_user)
        transition(locked_v1, "approve", ketua_user)
        transition(locked_v1, "lock", ketua_user)

        v1_1 = CaseVersion.objects.get(case=locked_v1, version_number="1.1")
        assert v1_1.policy_brief_document_id != old_brief.pk
        assert v1_1.approval_id == new_signature.pk
        assert v1_1.approval_id != v1.approval_id


class TestRegressionCasesStayLocked:
    """HF_ARNI_ACEI_004 and other flagged legacy cases are the lecturer's fixtures."""

    def test_a_flagged_case_cannot_be_revised(self, hta_client, locked_v1):
        Case.objects.filter(pk=locked_v1.pk).update(integrity_flag="requires_remediation")

        response = _revise(hta_client, locked_v1)

        assert response.status_code == 400
        locked_v1.refresh_from_db()
        assert locked_v1.status == CaseStatus.LOCKED

    def test_the_action_is_not_offered(self, hta_client, locked_v1):
        Case.objects.filter(pk=locked_v1.pk).update(integrity_flag="requires_remediation")

        detail = hta_client.get(f"/api/v1/cases/{locked_v1.case_id}/").data

        assert "revise" not in [t["name"] for t in detail["allowed_transitions"]]
