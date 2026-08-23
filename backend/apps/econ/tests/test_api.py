"""API tests for the econ endpoints (Phase R2)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.econ.validation_fixtures import VALIDATION_PARAMETERS

BASE = "/api/v1/cases/HF_ARNI_ACEI_001/econ"

MODEL_PAYLOAD = {
    "horizon_years": 1,
    "cost_discount_rate": "0",
    "outcome_discount_rate": "0",
    "wtp_threshold": "85000000",
}


def _param_payload() -> list[dict]:
    return [
        {
            "key": str(s["key"]),
            "alternative": str(s["alternative"]),
            "value": str(s["value"]),
            "param_type": str(s["param_type"]),
            "data_status": str(s["data_status"]),
            "unit": s.get("unit", ""),
        }
        for s in VALIDATION_PARAMETERS
    ]


@pytest.mark.django_db
class TestEconModelEndpoint:
    def test_put_creates_then_get_returns(self, hta_client, pilot_case):
        resp = hta_client.put(f"{BASE}/model/", MODEL_PAYLOAD, format="json")
        assert resp.status_code == 201

        got = hta_client.get(f"{BASE}/model/")
        assert got.status_code == 200
        assert got.data["horizon_years"] == 1
        assert Decimal(got.data["wtp_threshold"]) == Decimal("85000000")

    def test_get_returns_204_when_absent(self, hta_client, pilot_case):
        resp = hta_client.get(f"{BASE}/model/")
        assert resp.status_code == 204


@pytest.mark.django_db
class TestEconParametersAndCompute:
    def _seed(self, client):
        client.put(f"{BASE}/model/", MODEL_PAYLOAD, format="json")
        return client.put(f"{BASE}/parameters/", _param_payload(), format="json")

    def test_bulk_put_then_list(self, hta_client, pilot_case):
        resp = self._seed(hta_client)
        assert resp.status_code == 200
        listed = hta_client.get(f"{BASE}/parameters/")
        assert len(listed.data) == len(VALIDATION_PARAMETERS)

    def test_compute_reproduces_acceptance(self, hta_client, pilot_case):
        self._seed(hta_client)
        resp = hta_client.post(f"{BASE}/compute/")
        assert resp.status_code == 201
        assert abs(Decimal(resp.data["icer"]) - Decimal("516105577.5669")) <= Decimal("100")
        assert abs(Decimal(resp.data["inb"]) - Decimal("-11109590.7339")) <= Decimal("1")
        assert resp.data["decision_code"] == "not_cost_effective"

    def test_compute_without_params_returns_400_with_missing(self, hta_client, pilot_case):
        hta_client.put(f"{BASE}/model/", MODEL_PAYLOAD, format="json")
        resp = hta_client.post(f"{BASE}/compute/")
        assert resp.status_code == 400
        assert resp.data["missing"]


@pytest.mark.django_db
class TestEconPermissions:
    def test_viewer_can_read_but_not_edit(self, hta_client, kft_member_client, pilot_case):
        hta_client.put(f"{BASE}/model/", MODEL_PAYLOAD, format="json")

        # KFT member is a viewer: GET ok, PUT forbidden.
        assert kft_member_client.get(f"{BASE}/model/").status_code == 200
        assert kft_member_client.put(f"{BASE}/model/", MODEL_PAYLOAD, format="json").status_code == 403
        assert kft_member_client.post(f"{BASE}/compute/").status_code == 403
