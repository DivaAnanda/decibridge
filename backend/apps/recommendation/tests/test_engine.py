"""Pure-function tests for the synthesis engine (R3 semantics).

R3 changes vs the original:
  * Missing a mandatory component (EtD / CE / BIA) → status "incomplete", no
    traffic light (never a fabricated RED).
  * Empty CBA → "not assessed" (cba_score None), composite re-normalised over the
    present components (never an automatic 100).
"""

from __future__ import annotations

from decimal import Decimal

from apps.recommendation.engine import (
    GREEN_THRESHOLD,
    LABEL_BUDGET,
    LABEL_CE,
    LABEL_EVIDENCE,
    STATUS_COMPLETE,
    STATUS_INCOMPLETE,
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


class TestNoCBARenormalisation:
    def test_all_eighty_no_cba_renormalises_to_eighty(self):
        # (80*.4 + 80*.3 + 80*.2) / 0.9 = 72 / 0.9 = 80.00
        r = compute_recommendation(_inp())
        assert r.status == STATUS_COMPLETE
        assert r.cba_score is None  # not assessed — never auto-100
        assert r.composite_score == Decimal("80.00")
        assert r.traffic_light == "green"

    def test_all_fifty_no_cba(self):
        r = compute_recommendation(_inp(50, 50, 50))
        assert r.composite_score == Decimal("50.00")
        assert r.traffic_light == "red"

    def test_mixed_no_cba_yellow(self):
        # (60*.4 + 70*.3 + 60*.2) / 0.9 = 57 / 0.9 = 63.33
        r = compute_recommendation(_inp(60, 70, 60))
        assert r.composite_score == Decimal("63.33")
        assert r.traffic_light == "yellow"


class TestCBABranch:
    def test_full_cba_satisfaction_keeps_green(self):
        r = compute_recommendation(_inp(cba_count=3, cba_sat=3))
        assert r.cba_score == Decimal("100")
        assert r.composite_score == Decimal("82.00")
        assert r.traffic_light == "green"

    def test_partial_cba_drops_to_yellow(self):
        r = compute_recommendation(_inp(cba_count=3, cba_sat=2))
        assert r.cba_score == Decimal("50")
        assert r.composite_score == Decimal("77.00")
        assert r.traffic_light == "yellow"

    def test_no_cba_satisfaction_pushes_red_when_score_low(self):
        r = compute_recommendation(_inp(40, 40, 40, cba_count=3, cba_sat=0))
        assert r.cba_score == Decimal("0")
        assert r.composite_score == Decimal("36.00")
        assert r.traffic_light == "red"


class TestMissingDataGating:
    def test_missing_evidence_is_incomplete(self):
        r = compute_recommendation(_inp(evidence=None))
        assert r.status == STATUS_INCOMPLETE
        assert r.traffic_light is None
        assert r.composite_score is None
        assert LABEL_EVIDENCE in r.missing_components
        assert "Belum dapat dihitung" in r.justification_text

    def test_missing_ce_is_incomplete(self):
        r = compute_recommendation(_inp(ce=None))
        assert r.status == STATUS_INCOMPLETE
        assert LABEL_CE in r.missing_components

    def test_missing_budget_is_incomplete(self):
        r = compute_recommendation(_inp(budget=None))
        assert r.status == STATUS_INCOMPLETE
        assert LABEL_BUDGET in r.missing_components

    def test_multiple_missing_all_listed(self):
        r = compute_recommendation(_inp(evidence=None, ce=None, budget=None))
        assert set(r.missing_components) == {LABEL_EVIDENCE, LABEL_CE, LABEL_BUDGET}

    def test_empty_cba_alone_does_not_block(self):
        # CBA empty is "not assessed", not a missing mandatory component.
        r = compute_recommendation(_inp(cba_count=0))
        assert r.status == STATUS_COMPLETE


class TestNarrativeAndBoundaries:
    def test_green_narrative_mentions_traffic_light(self):
        assert "HIJAU" in compute_recommendation(_inp()).justification_text

    def test_red_narrative_mentions_traffic_light(self):
        assert "MERAH" in compute_recommendation(_inp(30, 30, 30)).justification_text

    def test_exactly_seventy_five_no_cba_is_green(self):
        # (75*0.9)/0.9 = 75.00
        r = compute_recommendation(_inp(75, 75, 75))
        assert r.composite_score == Decimal("75.00")
        assert r.composite_score >= GREEN_THRESHOLD
        assert r.traffic_light == "green"

    def test_low_mixed_no_cba_is_yellow(self):
        # (50*.4 + 70*.3 + 70*.2)/0.9 = 55/0.9 = 61.11
        r = compute_recommendation(_inp(50, 70, 70))
        assert YELLOW_THRESHOLD <= r.composite_score < GREEN_THRESHOLD
        assert r.traffic_light == "yellow"
