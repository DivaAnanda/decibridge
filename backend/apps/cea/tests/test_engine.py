"""Pure-function tests for the CEA engine.

No DB. No fixtures. These pin down the math.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cea.engine import (
    CE_SCORE_AT_THRESHOLD,
    CE_SCORE_INEFFECTIVE,
    CE_SCORE_SAFE,
    CE_SCORE_UNCERTAIN,
    COST_EFFECTIVE_AT_THRESHOLD,
    COST_EFFECTIVE_SAFE,
    COST_INEFFECTIVE,
    COST_SAVING,
    COST_UNCERTAIN,
    DOMINATED,
    FRONTIER_AMBIGUOUS,
    CEAComputationInput,
    compute_cea,
)

WTOP = Decimal("250000000")  # 250M IDR — Indonesia HTA-ish default


def _inp(
    drug_cost,
    comp_cost,
    drug_eff,
    comp_eff,
    wtop=WTOP,
) -> CEAComputationInput:
    return CEAComputationInput(
        drug_cost_per_unit=Decimal(str(drug_cost)),
        comparator_cost_per_unit=Decimal(str(comp_cost)),
        drug_efficacy_value=Decimal(str(drug_eff)),
        comparator_efficacy_value=Decimal(str(comp_eff)),
        wtop_threshold=wtop,
    )


class TestIcerArithmetic:
    def test_known_value_matches_manual_calc(self):
        # ICER = (10_000_000 - 5_000_000) / (2.5 - 2.0)
        #     = 5_000_000 / 0.5
        #     = 10_000_000.00
        result = compute_cea(_inp(10_000_000, 5_000_000, 2.5, 2.0))
        assert result.icer_value == Decimal("10000000.00")
        # Tolerance per the plan: within 0.01%
        manual = Decimal("10000000")
        deviation = abs(result.icer_value - manual) / manual
        assert deviation < Decimal("0.0001")

    def test_incremental_terms_recorded(self):
        result = compute_cea(_inp(10_000_000, 5_000_000, 2.5, 2.0))
        assert result.incremental_cost == Decimal("5000000")
        assert result.incremental_effect == Decimal("0.5000")


class TestStrongDominance:
    def test_cost_saving_when_cheaper_and_more_effective(self):
        # Drug: cheaper (-1M) AND more effective (+0.5 QALY) → strongly dominant
        result = compute_cea(_inp(5_000_000, 6_000_000, 2.5, 2.0))
        assert result.dominance == COST_SAVING
        assert result.ce_score == CE_SCORE_SAFE
        assert "lebih murah" in result.interpretation_text.lower()

    def test_dominated_when_costlier_and_less_effective(self):
        result = compute_cea(_inp(10_000_000, 5_000_000, 1.5, 2.0))
        assert result.dominance == DOMINATED
        assert result.ce_score == CE_SCORE_INEFFECTIVE
        assert "dominated" in result.interpretation_text.lower()


class TestCostEffectivenessBands:
    def test_safe_zone_below_80_percent_wtop(self):
        # ICER target: 100M (below 0.8 * 250M = 200M)
        # Δcost / Δeffect = 100M → 100M cost diff with 1.0 effect diff
        result = compute_cea(_inp(150_000_000, 50_000_000, 2.0, 1.0))
        assert result.icer_value == Decimal("100000000.00")
        assert result.dominance == COST_EFFECTIVE_SAFE
        assert result.ce_score == CE_SCORE_SAFE

    def test_at_threshold_band_80_to_100_percent_wtop(self):
        # ICER = 225M (between 200M and 250M)
        result = compute_cea(_inp(275_000_000, 50_000_000, 2.0, 1.0))
        assert result.icer_value == Decimal("225000000.00")
        assert result.dominance == COST_EFFECTIVE_AT_THRESHOLD
        assert result.ce_score == CE_SCORE_AT_THRESHOLD

    def test_uncertain_band_100_to_150_percent_wtop(self):
        # ICER = 300M (between 250M and 375M)
        result = compute_cea(_inp(350_000_000, 50_000_000, 2.0, 1.0))
        assert result.icer_value == Decimal("300000000.00")
        assert result.dominance == COST_UNCERTAIN
        assert result.ce_score == CE_SCORE_UNCERTAIN

    def test_ineffective_above_150_percent_wtop(self):
        # ICER = 500M (above 375M)
        result = compute_cea(_inp(550_000_000, 50_000_000, 2.0, 1.0))
        assert result.icer_value == Decimal("500000000.00")
        assert result.dominance == COST_INEFFECTIVE
        assert result.ce_score == CE_SCORE_INEFFECTIVE


class TestFrontierAmbiguous:
    def test_zero_effect_difference_returns_ambiguous(self):
        result = compute_cea(_inp(10_000_000, 5_000_000, 2.0, 2.0))
        assert result.dominance == FRONTIER_AMBIGUOUS
        assert result.icer_value is None
        assert "non-inferiority" in result.interpretation_text.lower()

    def test_tiny_effect_difference_treated_as_zero(self):
        # 0.00005 < EPSILON (0.0001)
        result = compute_cea(_inp(10_000_000, 5_000_000, 2.00005, 2.0))
        assert result.dominance == FRONTIER_AMBIGUOUS


class TestThresholdSensitivityFlag:
    def test_icer_inside_band_flags_true(self):
        # ICER = 240M — within ±20% of 250M (200M-300M)
        result = compute_cea(_inp(290_000_000, 50_000_000, 2.0, 1.0))
        assert result.icer_value == Decimal("240000000.00")
        assert result.threshold_sensitivity_flag is True

    def test_icer_far_below_band_flags_false(self):
        # ICER = 100M — well below the 200M-300M band
        result = compute_cea(_inp(150_000_000, 50_000_000, 2.0, 1.0))
        assert result.threshold_sensitivity_flag is False


class TestSensitivity:
    def test_adverse_sensitivity_is_worse_than_baseline(self):
        # Baseline ICER positive; adverse should be larger
        result = compute_cea(_inp(150_000_000, 50_000_000, 2.0, 1.0))
        assert result.sensitivity_low_icer is not None
        assert result.sensitivity_low_icer > result.icer_value

    def test_favourable_sensitivity_is_better_than_baseline(self):
        result = compute_cea(_inp(150_000_000, 50_000_000, 2.0, 1.0))
        assert result.sensitivity_high_icer is not None
        assert result.sensitivity_high_icer < result.icer_value


class TestSnapshotSerialisation:
    def test_decimals_serialise_as_strings(self):
        inp = _inp(10_000_000, 5_000_000, 2.5, 2.0)
        snap = inp.snapshot()
        assert snap["drug_cost_per_unit"] == "10000000"
        assert snap["wtop_threshold"] == "250000000"
        # Ensure JSON-safe
        import json

        json.dumps(snap)  # no exception
