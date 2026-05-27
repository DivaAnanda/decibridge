from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework import status

from apps.audit.models import AuditLog
from apps.cea.models import CEAInput, CEAResult


def _input_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/cea/input/"


def _compute_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/cea/compute/"


def _results_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/cea/results/"


@pytest.mark.django_db
class TestCEAInputCRUD:
    def test_initial_get_returns_204(self, hta_client, pilot_case):
        response = hta_client.get(_input_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_hta_can_create_input(self, hta_client, pilot_case, cea_input_payload):
        response = hta_client.put(_input_url(pilot_case.case_id), cea_input_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert CEAInput.objects.filter(case=pilot_case).exists()

    def test_kft_member_cannot_create_input(self, kft_member_client, pilot_case, cea_input_payload):
        response = kft_member_client.put(_input_url(pilot_case.case_id), cea_input_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_can_view_input(self, kft_member_client, cea_input):
        response = kft_member_client.get(_input_url(cea_input.case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["drug_cost_per_unit"] == "10000000.00"

    def test_update_replaces_values(self, hta_client, cea_input, cea_input_payload):
        new_payload = {**cea_input_payload, "drug_cost_per_unit": "12000000.00"}
        response = hta_client.put(_input_url(cea_input.case.case_id), new_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        cea_input.refresh_from_db()
        assert cea_input.drug_cost_per_unit == Decimal("12000000.00")

    def test_negative_cost_rejected(self, hta_client, pilot_case, cea_input_payload):
        bad = {**cea_input_payload, "drug_cost_per_unit": "-1.00"}
        response = hta_client.put(_input_url(pilot_case.case_id), bad, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCEACompute:
    def test_compute_without_input_returns_400(self, hta_client, pilot_case):
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_compute_creates_immutable_result(self, hta_client, cea_input):
        response = hta_client.post(_compute_url(cea_input.case.case_id))
        assert response.status_code == status.HTTP_201_CREATED, response.data
        # ICER = 5M / 0.5 = 10M (cost-effective safe vs 250M WTOP)
        assert response.data["icer_value"] == "10000000.00"
        assert response.data["dominance"] == "cost_effective_safe"
        assert response.data["ce_score"] == 100
        assert CEAResult.objects.filter(case=cea_input.case).count() == 1

    def test_each_compute_appends_a_new_row(self, hta_client, cea_input):
        hta_client.post(_compute_url(cea_input.case.case_id))
        hta_client.post(_compute_url(cea_input.case.case_id))
        assert CEAResult.objects.filter(case=cea_input.case).count() == 2

    def test_compute_writes_audit_entry(self, hta_client, cea_input):
        before = AuditLog.objects.count()
        hta_client.post(_compute_url(cea_input.case.case_id))
        after = AuditLog.objects.count()
        assert after >= before + 1

    def test_kft_member_cannot_compute(self, kft_member_client, cea_input):
        response = kft_member_client.post(_compute_url(cea_input.case.case_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_can_list_results(self, hta_client, kft_member_client, cea_input):
        hta_client.post(_compute_url(cea_input.case.case_id))
        response = kft_member_client.get(_results_url(cea_input.case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestCEAImmutability:
    def test_cea_result_cannot_be_updated(self, hta_client, cea_input):
        hta_client.post(_compute_url(cea_input.case.case_id))
        result = CEAResult.objects.first()
        result.interpretation_text = "tampered"
        with pytest.raises(PermissionError):
            result.save()

    def test_cea_result_cannot_be_deleted(self, hta_client, cea_input):
        hta_client.post(_compute_url(cea_input.case.case_id))
        result = CEAResult.objects.first()
        with pytest.raises(PermissionError):
            result.delete()
