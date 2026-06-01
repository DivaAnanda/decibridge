"""Aggregate per-member domain weight votes into a single weight vector.

Pure functions. No Django imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class WeightAggregate:
    domain_slug: str
    vote_count: int
    mean_weight: Decimal | None
    median_weight: Decimal | None
    chosen_weight: Decimal | None  # the value the engine should consume
    normalized_weight: Decimal | None  # share of total after sum-normalisation


def aggregate_per_domain(
    domain_votes: dict[str, list[int]], method: str = "mean"
) -> dict[str, WeightAggregate]:
    """Reduce votes to one weight per domain.

    Args:
        domain_votes: {domain_slug: [vote_int, ...]}
        method: 'mean' or 'median'
    """
    out: dict[str, WeightAggregate] = {}
    chosen_by_slug: dict[str, Decimal] = {}

    for slug, votes in domain_votes.items():
        if not votes:
            out[slug] = WeightAggregate(slug, 0, None, None, None, None)
            continue
        mean_w = (Decimal(sum(votes)) / Decimal(len(votes))).quantize(Decimal("0.01"))
        median_w = Decimal(median(votes)).quantize(Decimal("0.01"))
        chosen = mean_w if method == "mean" else median_w
        chosen_by_slug[slug] = chosen
        out[slug] = WeightAggregate(slug, len(votes), mean_w, median_w, chosen, None)

    total = sum(chosen_by_slug.values()) if chosen_by_slug else Decimal("0")
    for slug, agg in out.items():
        if agg.chosen_weight is None:
            continue
        if total > 0:
            normalised = (agg.chosen_weight / total).quantize(Decimal("0.0001"))
        else:
            normalised = Decimal("0")
        out[slug] = WeightAggregate(
            slug,
            agg.vote_count,
            agg.mean_weight,
            agg.median_weight,
            agg.chosen_weight,
            normalised,
        )

    return out
