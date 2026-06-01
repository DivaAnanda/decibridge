"""Pure-function tests for weight aggregation."""

from __future__ import annotations

from decimal import Decimal

from apps.recommendation.aggregation import aggregate_per_domain


class TestAggregatePerDomain:
    def test_empty_returns_nulls(self):
        result = aggregate_per_domain({"problem": []})
        assert result["problem"].vote_count == 0
        assert result["problem"].chosen_weight is None
        assert result["problem"].normalized_weight is None

    def test_mean_is_default(self):
        result = aggregate_per_domain({"problem": [40, 60, 80]})
        assert result["problem"].vote_count == 3
        assert result["problem"].mean_weight == Decimal("60.00")
        assert result["problem"].chosen_weight == Decimal("60.00")

    def test_median_method(self):
        result = aggregate_per_domain({"problem": [10, 50, 90]}, method="median")
        assert result["problem"].median_weight == Decimal("50.00")
        assert result["problem"].chosen_weight == Decimal("50.00")

    def test_normalisation_sums_to_one(self):
        result = aggregate_per_domain({"a": [50], "b": [50], "c": [50], "d": [50]})
        total = sum(r.normalized_weight for r in result.values())
        # Decimal arithmetic — should be exactly 1
        assert total == Decimal("1.0000")
