from __future__ import annotations

import pytest
from rest_framework import status

from apps.recommendation.models import CBACriterion, DomainWeightVote, Recommendation


def _weights_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/weights/"


def _weights_summary_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/weights/summary/"


def _cba_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/cba/"


def _compute_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/recommendation/compute/"


def _results_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/recommendation/results/"


@pytest.mark.django_db
class TestWeightsUpsert:
    def test_kft_member_can_upsert_all_weights(self, api_client, kft_three, pilot_case, etd_domains):
        api_client.force_authenticate(kft_three[0])
        payload = {"weights": {d.slug: 50 for d in etd_domains}}
        response = api_client.post(_weights_url(pilot_case.case_id), payload, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        assert DomainWeightVote.objects.filter(
            case=pilot_case, member=kft_three[0]
        ).count() == 9

    def test_hta_analyst_cannot_vote(self, hta_client, pilot_case, etd_domains):
        payload = {"weights": {d.slug: 50 for d in etd_domains}}
        response = hta_client.post(_weights_url(pilot_case.case_id), payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_weight_range_rejected(self, api_client, kft_three, pilot_case):
        api_client.force_authenticate(kft_three[0])
        payload = {"weights": {"problem": 150}}  # > 100
        response = api_client.post(_weights_url(pilot_case.case_id), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unknown_domain_slug_rejected(self, api_client, kft_three, pilot_case):
        api_client.force_authenticate(kft_three[0])
        payload = {"weights": {"nonexistent_slug": 50}}
        response = api_client.post(_weights_url(pilot_case.case_id), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestWeightsSummary:
    def test_summary_aggregates_across_members(
        self, kft_member_client, pilot_case, etd_domains, seeded_weights
    ):
        response = kft_member_client.get(_weights_summary_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["method"] == "mean"
        assert len(response.data["aggregates"]) == 9
        first = response.data["aggregates"][0]
        assert first["vote_count"] == 3
        assert first["chosen_weight"] == "50.00"


@pytest.mark.django_db
class TestCBACrud:
    PAYLOAD = {
        "criterion_name": "Diresepkan oleh kardiolog",
        "field_reference": "prescriber.specialty",
        "operator": "equals",
        "expected_value": "kardiolog",
        "description": "Untuk memastikan kepatuhan",
    }

    def test_hta_can_create_cba(self, hta_client, pilot_case):
        response = hta_client.post(_cba_url(pilot_case.case_id), self.PAYLOAD, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert CBACriterion.objects.filter(case=pilot_case).count() == 1

    def test_kft_member_cannot_create_cba(self, kft_member_client, pilot_case):
        response = kft_member_client.post(_cba_url(pilot_case.case_id), self.PAYLOAD, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRecommendationCompute:
    def test_compute_with_all_inputs_returns_green(
        self,
        hta_client,
        pilot_case,
        seeded_econ_result,
        seeded_bia_result,
        seeded_etd_votes,
    ):
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_201_CREATED, response.data
        # Evidence 87.5 (judgement 75, certainty high 100 → combined 87.5), CE 100,
        # Budget 80, no CBA → re-normalise: (87.5*.4 + 100*.3 + 80*.2)/0.9 = 90.00
        assert response.data["traffic_light"] == "green"
        assert response.data["cba_score"] is None  # not assessed, never auto-100
        assert Recommendation.objects.filter(case=pilot_case).count() == 1

    def test_compute_without_etd_is_incomplete(
        self, hta_client, pilot_case, seeded_econ_result, seeded_bia_result
    ):
        # No EtD votes → evidence missing → incomplete, NOT a fabricated RED.
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data["missing_components"]
        assert Recommendation.objects.filter(case=pilot_case).count() == 0

    def test_compute_without_econ_is_incomplete(
        self, hta_client, pilot_case, seeded_bia_result, seeded_etd_votes
    ):
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data["missing_components"]

    def test_each_compute_appends_new_row(
        self, hta_client, pilot_case, seeded_econ_result, seeded_bia_result, seeded_etd_votes
    ):
        hta_client.post(_compute_url(pilot_case.case_id))
        hta_client.post(_compute_url(pilot_case.case_id))
        assert Recommendation.objects.filter(case=pilot_case).count() == 2

    def test_kft_member_cannot_compute(
        self,
        kft_member_client,
        pilot_case,
        seeded_econ_result,
        seeded_bia_result,
        seeded_etd_votes,
    ):
        response = kft_member_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_locked_case_rejects_compute(self, hta_client, pilot_case, seeded_econ_result):
        pilot_case.status = "locked"
        pilot_case.save()
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_cba_drops_to_yellow(
        self,
        hta_client,
        pilot_case,
        seeded_econ_result,
        seeded_bia_result,
        seeded_etd_votes,
        cba_factory,
    ):
        cba_factory("A", is_satisfied=True, order=1)
        cba_factory("B", is_satisfied=False, order=2)
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["traffic_light"] == "yellow"
        assert response.data["cba_score"] == "50.00"


@pytest.mark.django_db
class TestRecommendationImmutability:
    def test_cannot_be_updated(
        self, hta_client, pilot_case, seeded_econ_result, seeded_bia_result, seeded_etd_votes
    ):
        hta_client.post(_compute_url(pilot_case.case_id))
        rec = Recommendation.objects.first()
        rec.justification_text = "tampered"
        with pytest.raises(PermissionError):
            rec.save()

    def test_cannot_be_deleted(
        self, hta_client, pilot_case, seeded_econ_result, seeded_bia_result, seeded_etd_votes
    ):
        hta_client.post(_compute_url(pilot_case.case_id))
        rec = Recommendation.objects.first()
        with pytest.raises(PermissionError):
            rec.delete()


@pytest.mark.django_db
class TestResultsList:
    def test_kft_member_can_list_results(
        self,
        hta_client,
        kft_member_client,
        pilot_case,
        seeded_econ_result,
        seeded_bia_result,
        seeded_etd_votes,
    ):
        hta_client.post(_compute_url(pilot_case.case_id))
        response = kft_member_client.get(_results_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
