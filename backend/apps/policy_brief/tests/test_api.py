from __future__ import annotations

import pytest
from rest_framework import status

from apps.policy_brief.models import GenerationStatus, PolicyBriefDocument


def _list_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/policy-briefs/"


def _download_url(case_id: str, brief_id: int, fmt: str) -> str:
    return f"/api/v1/cases/{case_id}/policy-briefs/{brief_id}/download/{fmt}/"


@pytest.mark.django_db
class TestGenerationGate:
    def test_draft_case_cannot_generate(self, hta_client, pilot_case):
        # pilot_case is still draft — no rec, no approval.
        response = hta_client.post(_list_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_in_review_case_cannot_generate(self, hta_client, case_in_review):
        # In review but not yet approved.
        response = hta_client.post(_list_url(case_in_review.case_id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_approved_case_without_recommendation_cannot_generate(
        self, hta_client, pilot_case, hta_user, ketua_user
    ):
        # Force approved status WITHOUT a Recommendation row.
        from apps.cases.state_machine import transition as case_transition

        case_transition(pilot_case, "submit", hta_user)
        case_transition(pilot_case, "approve", ketua_user)

        response = hta_client.post(_list_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "rekomendasi" in response.data["detail"].lower()

    def test_hta_can_generate(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        response = hta_client.post(_list_url(case.case_id))
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["version"] == 1
        assert response.data["status"] == GenerationStatus.COMPLETED.value

    def test_sekretaris_can_generate(self, sekretaris_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        response = sekretaris_client.post(_list_url(case.case_id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_ketua_can_generate(self, ketua_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        response = ketua_client.post(_list_url(case.case_id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_kft_member_cannot_generate(self, kft_member_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        response = kft_member_client.post(_list_url(case.case_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestVersioning:
    def test_versions_monotonically_increase(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        r1 = hta_client.post(_list_url(case.case_id))
        r2 = hta_client.post(_list_url(case.case_id))
        r3 = hta_client.post(_list_url(case.case_id))
        assert r1.data["version"] == 1
        assert r2.data["version"] == 2
        assert r3.data["version"] == 3
        assert PolicyBriefDocument.objects.filter(case=case).count() == 3

    def test_list_returns_all_versions_newest_first(
        self, hta_client, approved_case_with_rec
    ):
        case, _ = approved_case_with_rec
        hta_client.post(_list_url(case.case_id))
        hta_client.post(_list_url(case.case_id))
        response = hta_client.get(_list_url(case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert [b["version"] for b in response.data] == [2, 1]


@pytest.mark.django_db
class TestListVisibility:
    def test_every_role_can_list(
        self,
        hta_client,
        sekretaris_client,
        ketua_client,
        kft_member_client,
        approved_case_with_rec,
    ):
        case, _ = approved_case_with_rec
        hta_client.post(_list_url(case.case_id))

        for client in (hta_client, sekretaris_client, ketua_client, kft_member_client):
            response = client.get(_list_url(case.case_id))
            assert response.status_code == status.HTTP_200_OK
            assert len(response.data) == 1


@pytest.mark.django_db
class TestDownload:
    def test_download_docx_serves_file(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        gen = hta_client.post(_list_url(case.case_id))
        brief_id = gen.data["id"]

        response = hta_client.get(_download_url(case.case_id, brief_id, "docx"))
        assert response.status_code == status.HTTP_200_OK
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert f"v{gen.data['version']}.docx" in response["Content-Disposition"] or (
            "policy_brief" in response["Content-Disposition"]
        )

    def test_download_pdf_serves_file(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        gen = hta_client.post(_list_url(case.case_id))
        brief_id = gen.data["id"]

        response = hta_client.get(_download_url(case.case_id, brief_id, "pdf"))
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"

    def test_kft_member_can_download(
        self, hta_client, kft_member_client, approved_case_with_rec
    ):
        case, _ = approved_case_with_rec
        gen = hta_client.post(_list_url(case.case_id))
        brief_id = gen.data["id"]

        response = kft_member_client.get(_download_url(case.case_id, brief_id, "pdf"))
        assert response.status_code == status.HTTP_200_OK

    def test_unknown_format_rejected(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        gen = hta_client.post(_list_url(case.case_id))
        brief_id = gen.data["id"]

        response = hta_client.get(_download_url(case.case_id, brief_id, "xlsx"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestImmutability:
    def test_cannot_update_existing_brief(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        hta_client.post(_list_url(case.case_id))
        brief = PolicyBriefDocument.objects.first()

        brief.docx_sha256 = "tampered"
        with pytest.raises(PermissionError):
            brief.save()

    def test_cannot_delete_brief(self, hta_client, approved_case_with_rec):
        case, _ = approved_case_with_rec
        hta_client.post(_list_url(case.case_id))
        brief = PolicyBriefDocument.objects.first()

        with pytest.raises(PermissionError):
            brief.delete()

    def test_identity_fields_immutable(self, hta_client, approved_case_with_rec):
        """Even a save with a different version (before terminal) should fail."""
        case, _ = approved_case_with_rec
        hta_client.post(_list_url(case.case_id))
        brief = PolicyBriefDocument.objects.first()
        # Status is already COMPLETED, so the post-terminal guard catches this
        # too; but the test name is about identity. Force a fresh non-terminal row.
        brief.status = GenerationStatus.GENERATING  # in-memory only
        brief.version = brief.version + 1
        with pytest.raises(PermissionError):
            brief.save()
