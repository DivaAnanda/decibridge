"""Round 5 item 3: the KFT's own decision beside the system's colour and score.

Pak Anom: "Rekomendasi: hasil warna/skor sistem tetap ada, tetapi tambahkan kolom
Keputusan Final KFT + alasan yang diisi manusia." Anggota KFT and Ketua KFT record it,
choosing one of the original brief's five decision types, always with a reason. Rows
are append-only; the latest is the current decision. Sign-off needs a current one and
the signature records which one it signed.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.approval.models import Approval
from apps.approval.tests.conftest import _build_green_recommendation, _make_dossier_complete
from apps.audit.models import AuditLog
from apps.cases.completeness import evaluate_readiness
from apps.cases.decision_snapshot import build_decision_snapshot
from apps.cases.integrity import evaluate_integrity
from apps.cases.models import Case, CaseStatus
from apps.cases.state_machine import transition
from apps.recommendation.models import FinalDecision, FinalDecisionType

from .factories import make_final_decision

pytestmark = pytest.mark.django_db

LABEL = "Keputusan Final KFT tercatat"


def _url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/final-decisions/"


def _force_status(case, status: str) -> None:
    Case.objects.filter(pk=case.pk).update(status=status)
    case.refresh_from_db()


def _requirement(report: dict) -> dict:
    return next(r for r in report["requirements"] if r["key"] == "final_decision")


@pytest.fixture
def case_with_rec(pilot_case, hta_user):
    _make_dossier_complete(pilot_case, hta_user)
    _build_green_recommendation(pilot_case, hta_user)
    return pilot_case


@pytest.fixture
def payload() -> dict:
    return {
        "decision": FinalDecisionType.ADOPT_WITH_CRITERIA,
        "reason": "Biaya per QALY di bawah ambang; akses dibatasi pada pasien EF <= 40%.",
    }


class TestRecording:
    def test_kft_member_records_a_decision(self, kft_member_client, case_with_rec, payload):
        response = kft_member_client.post(_url(case_with_rec.case_id), payload, format="json")

        assert response.status_code == 201, response.data
        latest_rec = case_with_rec.recommendations.latest("computed_at")
        assert response.data["decision"] == "adopt_with_criteria"
        assert "criteria-based access" in response.data["decision_label"]
        assert response.data["reason"] == payload["reason"]
        assert response.data["decided_by_name"] == "Anggota KFT"
        assert response.data["recommendation_id"] == latest_rec.pk
        assert response.data["recommendation_traffic_light"] == "green"
        assert response.data["matches_latest_recommendation"] is True

    def test_ketua_records_a_decision(self, ketua_client, case_with_rec, payload):
        response = ketua_client.post(_url(case_with_rec.case_id), payload, format="json")

        assert response.status_code == 201

    @pytest.mark.parametrize("client_name", ["hta_client", "sekretaris_client", "admin_it_client"])
    def test_other_roles_cannot_record(self, request, client_name, case_with_rec, payload):
        client = request.getfixturevalue(client_name)

        response = client.post(_url(case_with_rec.case_id), payload, format="json")

        assert response.status_code == 403
        assert not FinalDecision.objects.exists()

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_a_reason_is_required(self, kft_member_client, case_with_rec, payload, reason):
        response = kft_member_client.post(
            _url(case_with_rec.case_id), {**payload, "reason": reason}, format="json"
        )

        assert response.status_code == 400
        assert "reason" in response.data

    def test_only_the_five_decision_types(self, kft_member_client, case_with_rec, payload):
        response = kft_member_client.post(
            _url(case_with_rec.case_id), {**payload, "decision": "green"}, format="json"
        )

        assert response.status_code == 400
        assert "decision" in response.data

    def test_needs_a_system_recommendation_first(self, kft_member_client, pilot_case, payload):
        response = kft_member_client.post(_url(pilot_case.case_id), payload, format="json")

        assert response.status_code == 400
        assert "rekomendasi" in response.data["detail"].lower()

    @pytest.mark.parametrize("status", [CaseStatus.APPROVED, CaseStatus.LOCKED])
    def test_refused_once_signed(self, kft_member_client, case_with_rec, payload, status):
        _force_status(case_with_rec, status)

        response = kft_member_client.post(_url(case_with_rec.case_id), payload, format="json")

        assert response.status_code == 400
        assert not FinalDecision.objects.exists()

    def test_recording_is_audited(self, kft_member_client, case_with_rec, payload):
        kft_member_client.post(_url(case_with_rec.case_id), payload, format="json")

        entries = AuditLog.objects.filter(metadata__case_id=case_with_rec.case_id)
        entry = entries.latest("created_at")
        assert entry.diff["final_decision"]["new"]["decision"] == "adopt_with_criteria"


class TestHistory:
    def test_every_decision_is_kept_latest_first(self, kft_member_client, case_with_rec, payload):
        kft_member_client.post(_url(case_with_rec.case_id), payload, format="json")
        kft_member_client.post(
            _url(case_with_rec.case_id),
            {"decision": FinalDecisionType.DEFER, "reason": "Menunggu data RS."},
            format="json",
        )

        rows = kft_member_client.get(_url(case_with_rec.case_id)).data

        assert [r["decision"] for r in rows] == ["defer", "adopt_with_criteria"]

    def test_rows_cannot_be_changed_or_deleted(self, case_with_rec, kft_member_user):
        row = make_final_decision(case_with_rec, kft_member_user)

        row.reason = "diubah"
        with pytest.raises(PermissionError):
            row.save()
        with pytest.raises(PermissionError):
            row.delete()

    def test_a_decision_on_an_older_recommendation_is_flagged(
        self, kft_member_client, case_with_rec, kft_member_user, hta_user
    ):
        make_final_decision(case_with_rec, kft_member_user)
        _build_green_recommendation(case_with_rec, hta_user)

        rows = kft_member_client.get(_url(case_with_rec.case_id)).data

        assert rows[0]["matches_latest_recommendation"] is False

    def test_content_roles_read_admin_it_does_not(self, hta_client, admin_it_client, case_with_rec):
        assert hta_client.get(_url(case_with_rec.case_id)).status_code == 200
        assert admin_it_client.get(_url(case_with_rec.case_id)).status_code == 403


class TestSignOffGate:
    def test_sign_off_needs_a_final_decision(self, case_with_rec):
        report = evaluate_readiness(case_with_rec, action="approve")

        assert _requirement(report)["satisfied"] is False
        assert _requirement(report)["detail"] == "Belum ada keputusan final"
        assert report["missing"] == [LABEL]

    def test_a_current_decision_satisfies_it(self, case_with_rec, kft_member_user):
        make_final_decision(case_with_rec, kft_member_user)

        report = evaluate_readiness(case_with_rec, action="lock")

        assert _requirement(report)["satisfied"] is True
        assert "Anggota KFT" in _requirement(report)["detail"]

    def test_a_recomputed_recommendation_needs_reconfirming(
        self, case_with_rec, kft_member_user, hta_user
    ):
        make_final_decision(case_with_rec, kft_member_user)
        _build_green_recommendation(case_with_rec, hta_user)

        requirement = _requirement(evaluate_readiness(case_with_rec, action="approve"))

        assert requirement["satisfied"] is False
        assert "konfirmasi ulang" in requirement["detail"]

    def test_older_decisions_are_not_reopened(self, pilot_case):
        assert LABEL not in evaluate_integrity(pilot_case)["failures"]
        assert LABEL not in evaluate_readiness(pilot_case, action="brief")["missing"]

    def test_the_signature_records_the_decision_it_signed(
        self, ketua_client, case_with_rec, kft_member_user
    ):
        decision = make_final_decision(case_with_rec, kft_member_user)
        _force_status(case_with_rec, CaseStatus.IN_REVIEW)

        response = ketua_client.post(
            reverse("approval:sign", args=[case_with_rec.case_id]),
            {
                "recommendation_id": decision.recommendation_id,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": "TestPass123!",
            },
            format="json",
        )

        assert response.status_code == 201, response.data
        assert Approval.objects.get(case=case_with_rec).final_decision_id == decision.pk
        assert response.data["final_decision"]["decision"] == "adopt_with_criteria"


class TestRecordedWithTheDecision:
    @pytest.fixture
    def locked(self, case_with_rec, kft_member_user, hta_user, ketua_user):
        make_final_decision(
            case_with_rec, kft_member_user, decision=FinalDecisionType.REASSESS_AFTER_NEGOTIATION
        )
        transition(case_with_rec, "submit", hta_user)
        transition(case_with_rec, "approve", ketua_user)
        transition(case_with_rec, "lock", ketua_user)
        return case_with_rec

    def test_lock_snapshot_carries_it(self, locked):
        block = locked.versions.get(status="locked").snapshot["final_decision"]

        assert block["decision"] == "reassess_after_negotiation"
        assert block["reason"] == "Alasan pengujian."
        assert block["decided_by"] == "Anggota KFT"
        assert block["recommendation_id"] == locked.recommendations.latest("computed_at").pk

    def test_versi_shows_it(self, hta_client, locked):
        version = locked.versions.get(status="locked")

        state = hta_client.get(
            f"/api/v1/cases/{locked.case_id}/versions/{version.pk}/state/"
        ).data

        assert state["final_decision"]["decision_label"].startswith("Kaji ulang")
        assert state["final_decision"]["reason"] == "Alasan pengujian."

    def test_snapshot_without_a_decision_says_so(self, pilot_case):
        assert build_decision_snapshot(pilot_case)["final_decision"] is None

    def test_composite_score_is_still_shown_beside_it(self, kft_member_client, case_with_rec):
        """'hasil warna/skor sistem tetap ada'"""
        latest = kft_member_client.get(
            f"/api/v1/cases/{case_with_rec.case_id}/recommendation/results/latest/"
        ).data

        assert latest["traffic_light"] == "green"
        assert Decimal(latest["composite_score"]) == Decimal("92.00")


class TestSignOffBindsWhatWasShown:
    """Code review: a stale Sign-Off screen could sign something it never showed."""

    @pytest.fixture
    def in_review(self, case_with_rec, kft_member_user):
        decision = make_final_decision(case_with_rec, kft_member_user)
        _force_status(case_with_rec, CaseStatus.IN_REVIEW)
        return case_with_rec, decision

    def _sign(self, client, case, **overrides):
        payload = {
            "recommendation_id": case.recommendations.latest("computed_at").pk,
            "decision": "approved",
            "confirmation_acknowledged": True,
            "password": "TestPass123!",
            **overrides,
        }
        return client.post(reverse("approval:sign", args=[case.case_id]), payload, format="json")

    def test_an_older_recommendation_cannot_be_signed(
        self, ketua_client, in_review, hta_user, kft_member_user
    ):
        case, _ = in_review
        stale_id = case.recommendations.latest("computed_at").pk
        _build_green_recommendation(case, hta_user)
        make_final_decision(case, kft_member_user)

        response = self._sign(ketua_client, case, recommendation_id=stale_id)

        assert response.status_code == 409
        assert not Approval.objects.filter(case=case).exists()

    def test_a_decision_changed_since_the_screen_loaded_is_refused(
        self, ketua_client, in_review, kft_member_user
    ):
        case, shown = in_review
        make_final_decision(case, kft_member_user, decision=FinalDecisionType.DEFER)

        response = self._sign(ketua_client, case, final_decision_id=shown.pk)

        assert response.status_code == 409
        assert not Approval.objects.filter(case=case).exists()

    def test_the_decision_on_screen_is_signed(self, ketua_client, in_review):
        case, shown = in_review

        response = self._sign(ketua_client, case, final_decision_id=shown.pk)

        assert response.status_code == 201, response.data
        assert Approval.objects.get(case=case).final_decision_id == shown.pk

    def test_the_lock_needs_a_signature_on_the_current_decision(
        self, ketua_client, in_review, kft_member_user
    ):
        case, _ = in_review
        assert self._sign(ketua_client, case).status_code == 201
        Case.objects.filter(pk=case.pk).update(status=CaseStatus.IN_REVIEW)
        make_final_decision(case, kft_member_user, decision=FinalDecisionType.DEFER)
        Case.objects.filter(pk=case.pk).update(status=CaseStatus.APPROVED)

        response = ketua_client.post(
            f"/api/v1/cases/{case.case_id}/transition/", {"action": "lock"}, format="json"
        )

        assert response.status_code == 422
        assert "Sign-off Ketua KFT tercatat" in response.data["missing"]
        assert "Minta Revisi" in response.data["detail"]


class TestDecisionCurrentAfterRevision:
    def test_a_decision_from_before_a_revision_is_not_current(
        self, kft_member_client, case_with_rec, kft_member_user, hta_user
    ):
        from apps.cases.models import CaseVersion, CaseVersionTrigger

        make_final_decision(case_with_rec, kft_member_user)
        CaseVersion.objects.create(
            case=case_with_rec,
            version_number="1.1-draft",
            trigger=CaseVersionTrigger.REVISION_REQUESTED,
            created_by=hta_user,
        )

        row = kft_member_client.get(_url(case_with_rec.case_id)).data[0]

        assert row["matches_latest_recommendation"] is True
        assert row["is_current"] is False


def test_recommendation_cannot_be_recomputed_once_approved(hta_client, case_with_rec):
    """It is part of what was signed; recomputing it left the case unable to lock."""
    _force_status(case_with_rec, CaseStatus.APPROVED)

    response = hta_client.post(
        f"/api/v1/cases/{case_with_rec.case_id}/recommendation/compute/", {}, format="json"
    )

    assert response.status_code == 400
    assert "Minta Revisi" in response.data["detail"]
