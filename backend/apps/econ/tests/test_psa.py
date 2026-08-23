"""PSA service + API tests (Phase R5)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.econ.models import EconomicModel, EconomicParameter, EconPSAResult
from apps.econ.service import run_psa
from apps.econ.validation_fixtures import MODEL_SCALARS, VALIDATION_PARAMETERS

BASE = "/api/v1/cases/HF_ARNI_ACEI_001/econ"


@pytest.fixture
def seeded_full_model(pilot_case, hta_user) -> EconomicModel:
    model = EconomicModel.objects.create(case=pilot_case, created_by=hta_user, **MODEL_SCALARS)
    for spec in VALIDATION_PARAMETERS:
        EconomicParameter.objects.create(
            economic_model=model,
            key=spec["key"],
            alternative=spec["alternative"],
            value=spec["value"],
            param_type=spec["param_type"],
            unit=spec.get("unit", ""),
            data_status=spec["data_status"],
            distribution=spec.get("distribution", "fixed"),
            dist_param1=spec.get("dist_param1"),
            dist_param2=spec.get("dist_param2"),
            created_by=hta_user,
        )
    return model


@pytest.mark.django_db
class TestRunPSA:
    def test_reproducible_same_seed(self, seeded_full_model, hta_user):
        a = run_psa(seeded_full_model, computed_by=hta_user, n_simulations=1000, seed=7)
        b = run_psa(seeded_full_model, computed_by=hta_user, n_simulations=1000, seed=7)
        assert a.prob_cost_effective_base == b.prob_cost_effective_base
        assert a.scatter[:10] == b.scatter[:10]

    def test_outputs_present(self, seeded_full_model, hta_user):
        r = run_psa(seeded_full_model, computed_by=hta_user, n_simulations=1000, seed=1)
        assert len(r.scatter) == 1000
        assert len(r.ceac) >= 2
        assert Decimal("0") <= r.prob_cost_effective_base <= Decimal("1")

    def test_append_only(self, seeded_full_model, hta_user):
        r = run_psa(seeded_full_model, computed_by=hta_user, n_simulations=500, seed=1)
        with pytest.raises(PermissionError):
            r.save()
        with pytest.raises(PermissionError):
            r.delete()


@pytest.mark.django_db
class TestPSAApi:
    def _seed(self, client):
        payload = {**{k: str(v) for k, v in MODEL_SCALARS.items()}, "horizon_years": 1}
        client.put(f"{BASE}/model/", payload, format="json")
        params = [
            {
                "key": str(s["key"]),
                "alternative": str(s["alternative"]),
                "value": str(s["value"]),
                "param_type": str(s["param_type"]),
                "data_status": str(s["data_status"]),
                "unit": s.get("unit", ""),
                "distribution": s.get("distribution", "fixed"),
                "dist_param1": str(s["dist_param1"]) if s.get("dist_param1") is not None else None,
                "dist_param2": str(s["dist_param2"]) if s.get("dist_param2") is not None else None,
            }
            for s in VALIDATION_PARAMETERS
        ]
        client.put(f"{BASE}/parameters/", params, format="json")

    def test_compute_returns_ceac_and_scatter(self, hta_client, pilot_case):
        self._seed(hta_client)
        resp = hta_client.post(f"{BASE}/psa/compute/", {"n_simulations": 800, "seed": 3}, format="json")
        assert resp.status_code == 201, resp.data
        assert len(resp.data["scatter"]) == 800
        assert len(resp.data["ceac"]) >= 2
        assert resp.data["n_simulations"] == 800

    def test_viewer_cannot_compute(self, hta_client, kft_member_client, pilot_case):
        self._seed(hta_client)
        assert kft_member_client.post(f"{BASE}/psa/compute/").status_code == 403

    def test_persisted(self, hta_client, pilot_case):
        self._seed(hta_client)
        hta_client.post(f"{BASE}/psa/compute/", {"n_simulations": 500}, format="json")
        assert EconPSAResult.objects.filter(case=pilot_case).count() == 1
