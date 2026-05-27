from __future__ import annotations

from decimal import Decimal

import pytest
from rest_framework import status

from apps.audit.models import AuditLog
from apps.bia.models import BIAInput, BIAResult


def _input_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/bia/input/"


def _compute_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/bia/compute/"


def _results_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/bia/results/"


@pytest.mark.django_db
class TestBIAInputCRUD:
    def test_initial_get_returns_204(self, hta_client, pilot_case):
        response = hta_client.get(_input_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_hta_can_create_input(self, hta_client, pilot_case, bia_input_payload):
        response = hta_client.put(_input_url(pilot_case.case_id), bia_input_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert BIAInput.objects.filter(case=pilot_case).exists()

    def test_kft_member_cannot_create_input(self, kft_member_client, pilot_case, bia_input_payload):
        response = kft_member_client.put(_input_url(pilot_case.case_id), bia_input_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_can_view_input(self, kft_member_client, bia_input):
        response = kft_member_client.get(_input_url(bia_input.case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["eligible_population"] == 1000

    def test_uptake_outside_unit_interval_rejected(self, hta_client, pilot_case, bia_input_payload):
        bad = {**bia_input_payload, "patient_uptake_year1": "1.5"}
        response = hta_client.put(_input_url(pilot_case.case_id), bad, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_cost_rejected(self, hta_client, pilot_case, bia_input_payload):
        bad = {**bia_input_payload, "unit_cost_drug": "-1.00"}
        response = hta_client.put(_input_url(pilot_case.case_id), bad, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBIACompute:
    def test_compute_without_input_returns_400(self, hta_client, pilot_case):
        response = hta_client.post(_compute_url(pilot_case.case_id))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_compute_creates_immutable_result(self, hta_client, bia_input):
        response = hta_client.post(_compute_url(bia_input.case.case_id))
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["year1_net_impact"] == "750000000.00"
        assert response.data["year3_net_impact"] == "2100000000.00"
        assert response.data["cumulative_impact"] == "4275000000.00"
        assert response.data["severity"] == "significant"
        assert BIAResult.objects.filter(case=bia_input.case).count() == 1

    def test_each_compute_appends_new_row(self, hta_client, bia_input):
        hta_client.post(_compute_url(bia_input.case.case_id))
        hta_client.post(_compute_url(bia_input.case.case_id))
        assert BIAResult.objects.filter(case=bia_input.case).count() == 2

    def test_compute_writes_audit_entry(self, hta_client, bia_input):
        before = AuditLog.objects.count()
        hta_client.post(_compute_url(bia_input.case.case_id))
        assert AuditLog.objects.count() >= before + 1

    def test_kft_member_cannot_compute(self, kft_member_client, bia_input):
        response = kft_member_client.post(_compute_url(bia_input.case.case_id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_kft_member_can_list_results(self, hta_client, kft_member_client, bia_input):
        hta_client.post(_compute_url(bia_input.case.case_id))
        response = kft_member_client.get(_results_url(bia_input.case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


@pytest.mark.django_db
class TestBIAImmutability:
    def test_bia_result_cannot_be_updated(self, hta_client, bia_input):
        hta_client.post(_compute_url(bia_input.case.case_id))
        result = BIAResult.objects.first()
        result.interpretation_text = "tampered"
        with pytest.raises(PermissionError):
            result.save()

    def test_bia_result_cannot_be_deleted(self, hta_client, bia_input):
        hta_client.post(_compute_url(bia_input.case.case_id))
        result = BIAResult.objects.first()
        with pytest.raises(PermissionError):
            result.delete()
