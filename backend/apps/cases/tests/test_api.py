from __future__ import annotations

import pytest
from rest_framework import status

from apps.audit.models import AuditLog
from apps.cases.models import Case, CaseStatus

PILOT_PAYLOAD = {
    "case_id": "HF_ARNI_ACEI_001",
    "case_title": "ARNI vs ACEI pada pasien HFrEF",
    "technology": "Sacubitril/valsartan",
    "comparator": "ACE inhibitor",
    "indication": "Heart failure with reduced ejection fraction",
    "population": "Pasien HFrEF rawat jalan/rawat inap sesuai kriteria RS",
    "setting": "KFT Rumah Sakit",
    "perspective": "hospital",
}


@pytest.mark.django_db
class TestCaseCreate:
    def test_hta_can_create_case(self, hta_client):
        response = hta_client.post("/api/v1/cases/", PILOT_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["case_id"] == "HF_ARNI_ACEI_001"
        assert response.data["status"] == "draft"
        assert Case.objects.filter(case_id="HF_ARNI_ACEI_001").exists()

    def test_sekretaris_can_create_case(self, sekretaris_client):
        response = sekretaris_client.post("/api/v1/cases/", PILOT_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_kft_member_cannot_create_case(self, kft_member_client):
        response = kft_member_client.post("/api/v1/cases/", PILOT_PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_case_id_rejected(self, hta_client):
        bad = {**PILOT_PAYLOAD, "case_id": "lowercase_bad"}
        response = hta_client.post("/api/v1/cases/", bad, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_with_decision_question(self, hta_client):
        payload = {
            **PILOT_PAYLOAD,
            "decision_question": {
                "question_text": "Apakah ARNI lebih efektif daripada ACEI pada HFrEF?",
                "pico_population": "Pasien HFrEF",
                "pico_intervention": "Sacubitril/valsartan",
                "pico_comparator": "Enalapril",
                "pico_outcome": "Mortalitas kardiovaskular",
            },
        }
        response = hta_client.post("/api/v1/cases/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["decision_questions"]) == 1


@pytest.mark.django_db
class TestCaseList:
    def test_any_role_can_list(self, kft_member_client, pilot_case):
        response = kft_member_client.get("/api/v1/cases/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["case_id"] == pilot_case.case_id

    def test_filter_by_status(self, hta_client, pilot_case):
        response = hta_client.get("/api/v1/cases/?status=draft")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestCaseTransitionEndpoint:
    def test_submit_returns_updated_case(self, hta_client, pilot_case):
        response = hta_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "submit"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["status"] == "in_review"

    def test_hta_cannot_approve(self, hta_client, pilot_case):
        hta_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "submit"},
            format="json",
        )
        response = hta_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "approve"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_send_back_requires_reason(self, hta_client, ketua_client, pilot_case):
        hta_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "submit"},
            format="json",
        )
        response = ketua_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "send_back", "reason": ""},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transition_writes_audit_entry(self, hta_client, pilot_case):
        before = AuditLog.objects.count()
        hta_client.post(
            f"/api/v1/cases/{pilot_case.case_id}/transition/",
            {"action": "submit"},
            format="json",
        )
        after = AuditLog.objects.count()
        assert after >= before + 1
        latest = AuditLog.objects.first()
        assert latest is not None
        assert latest.metadata.get("transition") == "submit"


@pytest.mark.django_db
class TestLockedCaseImmutable:
    def test_locked_case_cannot_be_patched(self, hta_client, pilot_case):
        # Reaching "locked" is not what's under test here, and the Phase V3
        # completeness gate rightly blocks locking an empty dossier via the API
        # — so put the case into the locked state directly.
        pilot_case.status = CaseStatus.LOCKED
        pilot_case.save(update_fields=["status"])

        response = hta_client.patch(
            f"/api/v1/cases/{pilot_case.case_id}/",
            {"case_title": "Tampered"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
