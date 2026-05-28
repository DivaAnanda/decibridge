"""Pure-function tests for the EtD aggregation engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from apps.etd.aggregation import aggregate_domain, aggregate_overall


@dataclass
class FakeAppraisal:
    judgement: int
    certainty: str


class TestAggregateDomain:
    def test_empty_returns_nulls(self):
        result = aggregate_domain("problem", [])
        assert result.appraisal_count == 0
        assert result.mean_judgement is None
        assert result.combined_domain_score is None

    def test_single_appraisal(self):
        result = aggregate_domain(
            "problem", [FakeAppraisal(judgement=100, certainty="high")]
        )
        assert result.appraisal_count == 1
        assert result.mean_judgement == Decimal("100.00")
        assert result.dominant_certainty == "high"
        assert result.certainty_score == Decimal("100")
        # combined = mean of judgement (100) and certainty score (100)
        assert result.combined_domain_score == Decimal("100.00")

    def test_three_appraisals_mean_and_median(self):
        appraisals = [
            FakeAppraisal(judgement=100, certainty="high"),
            FakeAppraisal(judgement=75, certainty="moderate"),
            FakeAppraisal(judgement=50, certainty="moderate"),
        ]
        result = aggregate_domain("desirable_effects", appraisals)
        # (100 + 75 + 50) / 3 = 75
        assert result.mean_judgement == Decimal("75.00")
        # sorted: 50, 75, 100 → median 75
        assert result.median_judgement == Decimal("75.00")
        # 2x moderate, 1x high → dominant = moderate (75)
        assert result.dominant_certainty == "moderate"
        # combined = (75 + 75) / 2 = 75
        assert result.combined_domain_score == Decimal("75.00")

    def test_tie_breaks_to_lower_certainty(self):
        # 1 high, 1 low — tied. Tie-break: prefer lower (more conservative).
        appraisals = [
            FakeAppraisal(judgement=100, certainty="high"),
            FakeAppraisal(judgement=100, certainty="low"),
        ]
        result = aggregate_domain("certainty_of_evidence", appraisals)
        assert result.dominant_certainty == "low"


class TestAggregateOverall:
    def test_no_completed_returns_nulls(self):
        from apps.etd.aggregation import DomainAggregate

        empties = [
            DomainAggregate(
                domain_slug=f"d{i}",
                appraisal_count=0,
                mean_judgement=None,
                median_judgement=None,
                dominant_certainty=None,
                certainty_score=None,
                combined_domain_score=None,
            )
            for i in range(9)
        ]
        result = aggregate_overall(empties, total_domains=9)
        assert result.domains_completed == 0
        assert result.evidence_strength_score is None

    def test_partial_completion(self):
        from apps.etd.aggregation import DomainAggregate

        per_domain = [
            DomainAggregate(
                domain_slug="problem",
                appraisal_count=2,
                mean_judgement=Decimal("100.00"),
                median_judgement=Decimal("100.00"),
                dominant_certainty="high",
                certainty_score=Decimal("100"),
                combined_domain_score=Decimal("100.00"),
            ),
            DomainAggregate(
                domain_slug="equity",
                appraisal_count=2,
                mean_judgement=Decimal("50.00"),
                median_judgement=Decimal("50.00"),
                dominant_certainty="low",
                certainty_score=Decimal("50"),
                combined_domain_score=Decimal("50.00"),
            ),
        ] + [
            DomainAggregate(
                domain_slug=f"d{i}",
                appraisal_count=0,
                mean_judgement=None,
                median_judgement=None,
                dominant_certainty=None,
                certainty_score=None,
                combined_domain_score=None,
            )
            for i in range(7)
        ]
        result = aggregate_overall(per_domain, total_domains=9)
        assert result.domains_completed == 2
        assert result.domains_total == 9
        # Mean of (100, 50) = 75
        assert result.evidence_strength_score == Decimal("75.00")
