"""Pure deterministic-engine tests (Phase R2). No DB required."""

from __future__ import annotations

from decimal import Decimal

from apps.econ.engine_deterministic import (
    AlternativeInputs,
    DeterministicInput,
    compute_deterministic,
)


def _approx(actual: Decimal, expected: Decimal, tol: Decimal) -> bool:
    return abs(actual - expected) <= tol


# Tolerances from the lecturer's workbook sheet 09_DATA_MAP_QC (QC01-QC08).
TOL_COST = Decimal("1")
TOL_QALY = Decimal("0.000001")
TOL_ICER = Decimal("10")


def _arni_acei_case() -> DeterministicInput:
    """The lecturer's REAL parameters (workbook sheet 01_INPUTS).

    Supersedes the reverse-engineered placeholders used before the workbook
    arrived. Reproduces sheet 02_DETERMINISTIC exactly.
    """
    shared = dict(event_cost=Decimal("6889093"), baseline_utility=Decimal("0.7"),
                  event_disutility=Decimal("0.1"), other_cost=Decimal("0"))
    return DeterministicInput(
        horizon_years=1,
        cost_discount_rate=Decimal("0.03"),
        outcome_discount_rate=Decimal("0.03"),
        wtp_threshold=Decimal("85000000"),
        intervention=AlternativeInputs(
            drug_cost=Decimal("15399360"), event_probability=Decimal("0.45"),
            median_los=Decimal("4"), **shared
        ),
        comparator=AlternativeInputs(
            drug_cost=Decimal("324000"), event_probability=Decimal("0.7077"),
            median_los=Decimal("5"), **shared
        ),
    )


class TestClinicalOutputs:
    """Secondary clinical validation metrics (workbook sheet 02_DETERMINISTIC)."""

    def test_matches_workbook(self):
        c = compute_deterministic(_arni_acei_case()).clinical
        assert _approx(c.absolute_risk_reduction, Decimal("0.2577"), Decimal("1e-9"))
        assert _approx(c.relative_risk, Decimal("0.6358626536668079"), Decimal("1e-12"))
        assert _approx(c.relative_risk_reduction, Decimal("0.36413734633319206"), Decimal("1e-12"))
        assert _approx(c.nnt, Decimal("3.880481179666279"), Decimal("1e-9"))
        assert c.los_difference == Decimal("-1")
        assert _approx(
            c.admission_cost_saving_per_patient_year, Decimal("1775319.2661"), Decimal("0.0001")
        )


class TestAcceptanceCase:
    """Reproduce HF_ARNI_ACEI_001 reference results within lecturer tolerances."""

    def test_totals(self):
        r = compute_deterministic(_arni_acei_case())
        assert _approx(r.intervention.total_cost, Decimal("18499451.85"), TOL_COST)
        assert _approx(r.comparator.total_cost, Decimal("5199411.1161"), TOL_COST)
        assert _approx(r.intervention.total_qaly, Decimal("0.655"), TOL_QALY)
        assert _approx(r.comparator.total_qaly, Decimal("0.62923"), TOL_QALY)

    def test_incrementals_and_icer(self):
        r = compute_deterministic(_arni_acei_case())
        assert _approx(r.incremental_cost, Decimal("13300040.7339"), TOL_COST)
        assert _approx(r.incremental_qaly, Decimal("0.02577"), TOL_QALY)
        assert r.icer is not None
        assert _approx(r.icer, Decimal("516105577.5669392"), TOL_ICER)

    def test_nmb_inb_and_decision(self):
        r = compute_deterministic(_arni_acei_case())
        assert _approx(r.inb, Decimal("-11109590.7339"), TOL_COST)
        assert r.is_cost_effective is False
        assert r.decision_code == "not_cost_effective"
        assert r.is_dominant is False and r.is_dominated is False


class TestDiscounting:
    def test_two_year_cost_discount(self):
        # Alt with annual_cost 100, annual_qaly 1.0, 10% cost discount, 0% outcome.
        alt = AlternativeInputs(
            drug_cost=Decimal("100"), event_probability=Decimal("0"),
            event_cost=Decimal("0"), other_cost=Decimal("0"),
            baseline_utility=Decimal("1.0"), event_disutility=Decimal("0"),
        )
        inp = DeterministicInput(
            horizon_years=2, cost_discount_rate=Decimal("0.10"),
            outcome_discount_rate=Decimal("0"), wtp_threshold=Decimal("50000000"),
            intervention=alt, comparator=alt,
        )
        r = compute_deterministic(inp)
        # 100 + 100/1.1 = 190.90909...
        assert _approx(r.intervention.total_cost, Decimal("190.9090909"), Decimal("0.0001"))
        # QALY undiscounted (rate 0): 1.0 + 1.0 = 2.0
        assert r.intervention.total_qaly == Decimal("2.0")
        # Identical alternatives → zero increments, ICER undefined.
        assert r.incremental_cost == Decimal("0")
        assert r.incremental_qaly == Decimal("0")
        assert r.icer is None


class TestDecisionRules:
    def _alt(self, drug, prob):
        return AlternativeInputs(
            drug_cost=Decimal(drug), event_probability=Decimal(prob),
            event_cost=Decimal("10000000"), other_cost=Decimal("0"),
            baseline_utility=Decimal("0.8"), event_disutility=Decimal("0.4"),
        )

    def _run(self, intervention, comparator):
        return compute_deterministic(DeterministicInput(
            horizon_years=1, cost_discount_rate=Decimal("0"),
            outcome_discount_rate=Decimal("0"), wtp_threshold=Decimal("100000000"),
            intervention=intervention, comparator=comparator,
        ))

    def test_dominant_when_cheaper_and_more_effective(self):
        # Intervention: lower drug cost AND lower event prob (more effective).
        r = self._run(self._alt("1000000", "0.10"), self._alt("2000000", "0.30"))
        assert r.is_dominant is True
        assert r.decision_code == "dominant"

    def test_dominated_when_pricier_and_less_effective(self):
        r = self._run(self._alt("3000000", "0.40"), self._alt("1000000", "0.10"))
        assert r.is_dominated is True
        assert r.decision_code == "dominated"

    def test_zero_incremental_qaly_gives_na_icer(self):
        # Same event prob → same QALY → Δqaly 0; different cost.
        r = self._run(self._alt("2000000", "0.20"), self._alt("1000000", "0.20"))
        assert r.incremental_qaly == Decimal("0")
        assert r.icer is None
