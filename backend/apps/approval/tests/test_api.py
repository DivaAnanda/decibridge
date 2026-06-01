from __future__ import annotations

import pytest
from rest_framework import status

from apps.approval.models import Approval
from apps.cases.models import CaseStatus


def _sign_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/approvals/sign/"


def _list_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/approvals/"


def _payload(rec_id: int, *, decision="approved", password="TestPass123!", **extra) -> dict:
    base = {
        "recommendation_id": rec_id,
        "decision": decision,
        "confirmation_acknowledged": True,
        "password": password,
        "reason": "",
    }
    base.update(extra)
    return base


@pytest.mark.django_db
class TestApprovalGate:
    def test_ketua_can_approve(self, ketua_client, case_in_review, green_recommendation):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Approval.objects.filter(case=case_in_review).count() == 1
        case_in_review.refresh_from_db()
        assert case_in_review.status == CaseStatus.APPROVED

    def test_hta_cannot_approve(self, hta_client, case_in_review, green_recommendation):
        response = hta_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_cannot_approve(self, kft_member_client, case_in_review, green_recommendation):
        response = kft_member_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSignaturePreconditions:
    def test_wrong_password_rejected(self, ketua_client, case_in_review, green_recommendation):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk, password="WrongPassword"),
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Approval.objects.count() == 0
        case_in_review.refresh_from_db()
        assert case_in_review.status == CaseStatus.IN_REVIEW

    def test_unchecked_confirmation_rejected(
        self, ketua_client, case_in_review, green_recommendation
    ):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk, confirmation_acknowledged=False),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_draft_case_cannot_be_signed(
        self, ketua_client, pilot_case, draft_recommendation
    ):
        # pilot_case stays in 'draft' (no submit transition). Sign-off requires in_review.
        response = ketua_client.post(
            _sign_url(pilot_case.case_id),
            _payload(draft_recommendation.pk),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRejectionFlow:
    def test_rejection_requires_reason(
        self, ketua_client, case_in_review, green_recommendation
    ):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk, decision="rejected", reason=""),
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_rejection_sends_case_back_to_draft(
        self, ketua_client, case_in_review, green_recommendation
    ):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(
                green_recommendation.pk,
                decision="rejected",
                reason="Data CEA belum lengkap.",
            ),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        case_in_review.refresh_from_db()
        assert case_in_review.status == CaseStatus.DRAFT
        assert Approval.objects.filter(decision="rejected").count() == 1

    def test_revision_request_also_returns_to_draft(
        self, ketua_client, case_in_review, green_recommendation
    ):
        response = ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(
                green_recommendation.pk,
                decision="revision_requested",
                reason="Mohon tambahkan referensi pediatrik.",
            ),
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        case_in_review.refresh_from_db()
        assert case_in_review.status == CaseStatus.DRAFT


@pytest.mark.django_db
class TestApprovalImmutability:
    def test_cannot_update(self, ketua_client, case_in_review, green_recommendation):
        ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        approval = Approval.objects.first()
        approval.reason = "tampered"
        with pytest.raises(PermissionError):
            approval.save()

    def test_cannot_delete(self, ketua_client, case_in_review, green_recommendation):
        ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        approval = Approval.objects.first()
        with pytest.raises(PermissionError):
            approval.delete()


@pytest.mark.django_db
class TestApprovalList:
    def test_any_viewer_can_list(
        self, kft_member_client, ketua_client, case_in_review, green_recommendation
    ):
        ketua_client.post(
            _sign_url(case_in_review.case_id),
            _payload(green_recommendation.pk),
            format="json",
        )
        response = kft_member_client.get(_list_url(case_in_review.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["decision"] == "approved"
