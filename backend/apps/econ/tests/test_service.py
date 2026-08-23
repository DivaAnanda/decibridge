"""End-to-end R2 test: stored parameters -> service -> persisted result.

Proves the DB-backed path reproduces the lecturer's acceptance table, not just
the pure engine.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.econ.models import EconDeterministicResult, EconomicModel, EconomicParameter
from apps.econ.service import IncompleteModelError, run_deterministic
from apps.econ.validation_fixtures import MODEL_SCALARS, VALIDATION_PARAMETERS

TOL_COST = Decimal("1")
TOL_QALY = Decimal("0.000001")
TOL_ICER = Decimal("100")


def _approx(a: Decimal, b: Decimal, tol: Decimal) -> bool:
    return abs(a - b) <= tol


@pytest.fixture
def seeded_model(pilot_case, hta_user) -> EconomicModel:
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
class TestRunDeterministic:
    def test_reproduces_acceptance_table(self, seeded_model, hta_user):
        result = run_deterministic(seeded_model, computed_by=hta_user)

        assert _approx(result.total_cost_intervention, Decimal("18499451.85"), TOL_COST)
        assert _approx(result.total_cost_comparator, Decimal("5199411.1161"), TOL_COST)
        assert _approx(result.total_qaly_intervention, Decimal("0.655"), TOL_QALY)
        assert _approx(result.total_qaly_comparator, Decimal("0.62923"), TOL_QALY)
        assert _approx(result.incremental_cost, Decimal("13300040.7339"), TOL_COST)
        assert _approx(result.incremental_qaly, Decimal("0.02577"), TOL_QALY)
        assert _approx(result.icer, Decimal("516105577.5669"), TOL_ICER)
        assert _approx(result.inb, Decimal("-11109590.7339"), TOL_COST)
        assert result.decision_code == "not_cost_effective"
        assert result.is_cost_effective is False

    def test_persists_snapshot_and_breakdown(self, seeded_model, hta_user):
        result = run_deterministic(seeded_model, computed_by=hta_user)
        assert result.input_snapshot["wtp_threshold"] == "85000000.0000"
        assert "intervention" in result.per_year
        assert Decimal(result.cost_breakdown["intervention"]["drug"]) == Decimal("14699451.85")

    def test_result_is_append_only(self, seeded_model, hta_user):
        result = run_deterministic(seeded_model, computed_by=hta_user)
        with pytest.raises(PermissionError):
            result.save()
        with pytest.raises(PermissionError):
            result.delete()

    def test_recompute_creates_new_row(self, seeded_model, hta_user):
        run_deterministic(seeded_model, computed_by=hta_user)
        run_deterministic(seeded_model, computed_by=hta_user)
        assert EconDeterministicResult.objects.filter(case=seeded_model.case).count() == 2

    def test_missing_parameters_raise_incomplete(self, pilot_case, hta_user):
        bare = EconomicModel.objects.create(case=pilot_case, created_by=hta_user, **MODEL_SCALARS)
        with pytest.raises(IncompleteModelError) as exc:
            run_deterministic(bare, computed_by=hta_user)
        assert exc.value.missing  # non-empty gap list
