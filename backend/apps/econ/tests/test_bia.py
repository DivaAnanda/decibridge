"""BIA service + API tests (Phase R4)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.econ.models import EconBIAResult, EconomicModel, EconomicParameter
from apps.econ.service import IncompleteModelError, run_bia
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
            created_by=hta_user,
        )
    return model


@pytest.mark.django_db
class TestRunBIA:
    def test_cost_offset_result(self, seeded_full_model, hta_user):
        # Lecturer's model: patients = eligible x uptake = 100 x 0.3 = 30
        # incremental_drug = 30 x (15,399,360 - 324,000)   = 452,260,800
        # offset = 30 x (0.7077 - 0.45) x 6,889,093        =  53,259,577.983
        # net = 399,001,222.017  (workbook sheet 03_BIA, medium scenario / QC10)
        result = run_bia(seeded_full_model, computed_by=hta_user)
        assert result.cumulative_net_impact == Decimal("399001222.0170000000000000000")
        assert result.severity == "manageable"
        assert result.budget_score == 80
        assert len(result.per_year) == 1

    def test_scenarios_match_workbook(self, seeded_full_model, hta_user):
        """QC09-QC11: low / medium / high uptake net budget impact."""
        result = run_bia(seeded_full_model, computed_by=hta_user)
        by_label = {s["label"]: Decimal(s["net_budget_impact"]) for s in result.scenarios}
        assert abs(by_label["low"] - Decimal("133000407.339")) <= Decimal("1")
        assert abs(by_label["medium"] - Decimal("399001222.017")) <= Decimal("1")
        assert abs(by_label["high"] - Decimal("665002036.695")) <= Decimal("1")

    def test_missing_baseline_marks_not_assessed(self, seeded_full_model, hta_user):
        """Without a budget baseline the impact is still computed, but never scored.

        The lecturer's own workbook carries no annual budget baseline, so this
        must not be a hard failure — and the sub-score must be null, not 0.
        """
        seeded_full_model.annual_budget_baseline = None
        seeded_full_model.save()
        result = run_bia(seeded_full_model, computed_by=hta_user)
        assert result.severity == "not_assessed"
        assert result.budget_score is None
        assert result.cumulative_net_impact == Decimal("399001222.0170000000000000000")

    def test_result_is_append_only(self, seeded_full_model, hta_user):
        result = run_bia(seeded_full_model, computed_by=hta_user)
        with pytest.raises(PermissionError):
            result.save()
        with pytest.raises(PermissionError):
            result.delete()


@pytest.mark.django_db
class TestBIAApi:
    def _seed(self, client):
        payload = {**{k: str(v) for k, v in MODEL_SCALARS.items()}}
        payload["horizon_years"] = 1
        client.put(f"{BASE}/model/", payload, format="json")
        params = [
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
        client.put(f"{BASE}/parameters/", params, format="json")

    def test_compute_returns_result(self, hta_client, pilot_case):
        self._seed(hta_client)
        resp = hta_client.post(f"{BASE}/bia/compute/")
        assert resp.status_code == 201, resp.data
        assert resp.data["severity"] == "manageable"
        assert resp.data["budget_score"] == 80

    def test_compute_without_params_is_422(self, hta_client, pilot_case):
        payload = {**{k: str(v) for k, v in MODEL_SCALARS.items()}, "horizon_years": 1}
        hta_client.put(f"{BASE}/model/", payload, format="json")
        resp = hta_client.post(f"{BASE}/bia/compute/")
        assert resp.status_code == 422
        assert resp.data["missing"]

    def test_viewer_cannot_compute(self, hta_client, kft_member_client, pilot_case):
        self._seed(hta_client)
        assert kft_member_client.post(f"{BASE}/bia/compute/").status_code == 403
        assert kft_member_client.get(f"{BASE}/bia/results/").status_code == 200

    def test_result_persisted_and_listed(self, hta_client, pilot_case):
        self._seed(hta_client)
        hta_client.post(f"{BASE}/bia/compute/")
        assert EconBIAResult.objects.filter(case=pilot_case).count() == 1
        listed = hta_client.get(f"{BASE}/bia/results/")
        assert len(listed.data) == 1
