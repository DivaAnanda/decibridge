from __future__ import annotations

import pytest
from rest_framework import status

from apps.etd.models import EtDAppraisal, ReferenceCitation


@pytest.mark.django_db
class TestDomainList:
    def test_returns_all_9_seeded_domains(self, hta_client):
        response = hta_client.get("/api/v1/etd/domains/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 9
        slugs = {d["slug"] for d in response.data}
        assert "problem" in slugs and "acceptability" in slugs


def _ref_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/references/"


def _appraisal_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/etd/appraisals/"


def _summary_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/etd/summary/"


@pytest.mark.django_db
class TestReferences:
    PAYLOAD = {
        "reference_type": "journal_article",
        "citation_text": "Smith J et al. 2024. Test. NEJM.",
        "authors": "Smith J",
        "publication_year": 2024,
        "title": "Test ref",
        "journal_name": "NEJM",
        "doi_pmid": "10.1056/test",
    }

    def test_hta_can_create_reference(self, hta_client, pilot_case):
        response = hta_client.post(_ref_url(pilot_case.case_id), self.PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert ReferenceCitation.objects.filter(case=pilot_case).count() == 1

    def test_kft_member_cannot_create_reference(self, kft_member_client, pilot_case):
        response = kft_member_client.post(_ref_url(pilot_case.case_id), self.PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_can_list_references(self, kft_member_client, reference_factory, pilot_case):
        reference_factory()
        response = kft_member_client.get(_ref_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestAppraisalUpsert:
    def test_kft_member_can_submit_appraisal(self, api_client, kft_three, pilot_case):
        member = kft_three[0]
        api_client.force_authenticate(member)
        response = api_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 75, "certainty": "high", "narrative": "Beban besar."},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert EtDAppraisal.objects.filter(case=pilot_case, member=member).count() == 1

    def test_repeat_submit_updates_in_place(self, api_client, kft_three, pilot_case):
        member = kft_three[0]
        api_client.force_authenticate(member)
        api_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 50, "certainty": "low"},
            format="json",
        )
        response = api_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 100, "certainty": "high"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK  # update path, not create
        assert EtDAppraisal.objects.filter(case=pilot_case, member=member).count() == 1
        assert EtDAppraisal.objects.get(case=pilot_case, member=member).judgement == 100

    def test_hta_analyst_cannot_submit_appraisal(self, hta_client, pilot_case):
        response = hta_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 75},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_judgement_rejected(self, api_client, kft_three, pilot_case):
        api_client.force_authenticate(kft_three[0])
        response = api_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 42},  # not in {0,25,50,75,100}
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSummary:
    def test_empty_case_returns_nulls(self, kft_member_client, pilot_case):
        response = kft_member_client.get(_summary_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["overall"]["domains_completed"] == 0
        assert response.data["overall"]["evidence_strength_score"] is None
        assert len(response.data["per_domain"]) == 9

    def test_aggregates_multi_member_votes(
        self, kft_member_client, kft_three, appraisal_factory, pilot_case
    ):
        appraisal_factory(kft_three[0], domain_slug="problem", judgement=100, certainty="high")
        appraisal_factory(kft_three[1], domain_slug="problem", judgement=75, certainty="moderate")
        appraisal_factory(kft_three[2], domain_slug="problem", judgement=50, certainty="moderate")
        response = kft_member_client.get(_summary_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        problem = next(d for d in response.data["per_domain"] if d["domain_slug"] == "problem")
        assert problem["appraisal_count"] == 3
        assert problem["mean_judgement"] == "75.00"
        assert problem["dominant_certainty"] == "moderate"


@pytest.mark.django_db
class TestLockedCase:
    def test_locked_case_rejects_new_appraisal(self, api_client, kft_three, pilot_case):
        pilot_case.status = "locked"
        pilot_case.save()
        api_client.force_authenticate(kft_three[0])
        response = api_client.post(
            _appraisal_url(pilot_case.case_id),
            {"domain_slug": "problem", "judgement": 100, "certainty": "high"},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestOwnershipGuard:
    def test_member_cannot_delete_others_appraisal(
        self, api_client, kft_three, appraisal_factory, pilot_case
    ):
        appraisal_factory(kft_three[0], domain_slug="problem")
        api_client.force_authenticate(kft_three[1])  # different member
        url = f"/api/v1/cases/{pilot_case.case_id}/etd/appraisals/problem/"
        response = api_client.delete(url)
        # Member 1 has no appraisal for that domain → 404 (object lookup is scoped to caller)
        assert response.status_code == status.HTTP_404_NOT_FOUND
