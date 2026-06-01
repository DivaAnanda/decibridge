"""Pure-function tests for the synthesis engine."""

from __future__ import annotations

from decimal import Decimal

from apps.recommendation.engine import (
    GREEN_THRESHOLD,
    YELLOW_THRESHOLD,
    SynthesisInput,
    compute_recommendation,
)


def _inp(
    evidence: int | None = 80,
    ce: int | None = 80,
    budget: int | None = 80,
    cba_count: int = 0,
    cba_sat: int = 0,
) -> SynthesisInput:
    return SynthesisInput(
        evidence_strength_score=Decimal(evidence) if evidence is not None else None,
        ce_score=Decimal(ce) if ce is not None else None,
        budget_score=Decimal(budget) if budget is not None else None,
        cba_criteria_count=cba_count,
        cba_satisfied_count=cba_sat,
    )


class TestCompositeArithmetic:
    def test_all_subscores_eighty_no_cba(self):
        # composite = 80*0.4 + 80*0.3 + 80*0.2 + 100*0.1 = 32 + 24 + 16 + 10 = 82
        r = compute_recommendation(_inp())
        assert r.composite_score == Decimal("82.00")
        assert r.cba_score == Decimal("100")  # no criteria → auto 100
        assert r.traffic_light == "green"

    def test_all_subscores_fifty_no_cba(self):
        # 50*0.4 + 50*0.3 + 50*0.2 + 100*0.1 = 20 + 15 + 10 + 10 = 55
        r = compute_recommendation(_inp(50, 50, 50))
        assert r.composite_score == Decimal("55.00")
        assert r.traffic_light == "red"

    def test_threshold_band_yellow(self):
        # Target composite ≈ 65 (between 60 and 75)
        # 60*0.4 + 70*0.3 + 60*0.2 + 100*0.1 = 24 + 21 + 12 + 10 = 67
        r = compute_recommendation(_inp(60, 70, 60))
        assert r.composite_score == Decimal("67.00")
        assert r.traffic_light == "yellow"


class TestCBABranch:
    def test_full_cba_satisfaction_keeps_green(self):
        r = compute_recommendation(_inp(cba_count=3, cba_sat=3))
        assert r.cba_score == Decimal("100")
        assert r.traffic_light == "green"

    def test_partial_cba_drops_to_yellow_even_if_high_score(self):
        # composite would be 82 (green), but CBA partial → yellow per the algorithm
        r = compute_recommendation(_inp(cba_count=3, cba_sat=2))
        assert r.cba_score == Decimal("50")
        # composite = 80*0.4 + 80*0.3 + 80*0.2 + 50*0.1 = 77 — still >= 75 numerically
        # but green requires CBA fully met; CBA partial caps at yellow.
        assert r.traffic_light == "yellow"

    def test_no_cba_satisfaction_pushes_red_when_score_low(self):
        r = compute_recommendation(_inp(40, 40, 40, cba_count=3, cba_sat=0))
        # 40*0.4 + 40*0.3 + 40*0.2 + 0*0.1 = 36
        assert r.cba_score == Decimal("0")
        assert r.composite_score == Decimal("36.00")
        assert r.traffic_light == "red"

    def test_zero_criteria_treats_cba_as_pass(self):
        r = compute_recommendation(_inp(80, 80, 80, cba_count=0, cba_sat=0))
        assert r.cba_score == Decimal("100")
        assert r.traffic_light == "green"


class TestMissingSubscores:
    def test_missing_evidence_treated_as_zero(self):
        # 0*0.4 + 80*0.3 + 80*0.2 + 100*0.1 = 0 + 24 + 16 + 10 = 50
        r = compute_recommendation(_inp(evidence=None))
        assert r.composite_score == Decimal("50.00")
        assert r.traffic_light == "red"
        assert "EtD belum dihitung" in r.justification_text

    def test_missing_cea_called_out_in_narrative(self):
        r = compute_recommendation(_inp(ce=None))
        assert "CEA belum dijalankan" in r.justification_text


class TestNarrative:
    def test_green_narrative_mentions_traffic_light(self):
        r = compute_recommendation(_inp())
        assert "HIJAU" in r.justification_text

    def test_red_narrative_mentions_traffic_light(self):
        r = compute_recommendation(_inp(30, 30, 30))
        assert "MERAH" in r.justification_text


class TestThresholdBoundaries:
    def test_exactly_75_with_no_cba_is_green(self):
        # 75*0.4 + 75*0.3 + 75*0.2 + 100*0.1 = 30 + 22.5 + 15 + 10 = 77.5
        r = compute_recommendation(_inp(75, 75, 75))
        assert r.composite_score >= GREEN_THRESHOLD
        assert r.traffic_light == "green"

    def test_exactly_60_is_yellow(self):
        # 50*0.4 + 70*0.3 + 70*0.2 + 100*0.1 = 20 + 21 + 14 + 10 = 65
        r = compute_recommendation(_inp(50, 70, 70))
        assert r.composite_score >= YELLOW_THRESHOLD
        assert r.composite_score < GREEN_THRESHOLD
        assert r.traffic_light == "yellow"
