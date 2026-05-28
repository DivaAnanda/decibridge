"""Aggregate KFT-member EtD appraisals into per-domain and overall scores.

Pure function. No Django imports at module load (lazy inside functions).
Sprint 7 will layer custom domain weights on top of this; Sprint 6 uses
simple equal weighting.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Iterable

from .models import CERTAINTY_NUMERIC, Certainty


@dataclass(frozen=True)
class DomainAggregate:
    domain_slug: str
    appraisal_count: int
    mean_judgement: Decimal | None
    median_judgement: Decimal | None
    dominant_certainty: str | None
    certainty_score: Decimal | None
    combined_domain_score: Decimal | None  # mean of judgement & certainty (0-100)


@dataclass(frozen=True)
class OverallScore:
    domains_completed: int
    domains_total: int
    evidence_strength_score: Decimal | None  # mean of completed domains' combined scores
    average_certainty: str | None  # mode across all appraisals


def _dominant_certainty(certainties: list[str]) -> str | None:
    if not certainties:
        return None
    # Tie-break: prefer lower certainty (more conservative) on ties.
    order = [Certainty.VERY_LOW, Certainty.LOW, Certainty.MODERATE, Certainty.HIGH]
    counts: dict[str, int] = {}
    for c in certainties:
        counts[c] = counts.get(c, 0) + 1
    max_count = max(counts.values())
    for c in order:
        if counts.get(c.value, 0) == max_count:
            return c.value
    return None


def aggregate_domain(domain_slug: str, appraisals: Iterable) -> DomainAggregate:
    """`appraisals` is an iterable of EtDAppraisal-like objects with
    .judgement (int 0-100), .certainty (str)."""
    appraisals = list(appraisals)
    count = len(appraisals)
    if count == 0:
        return DomainAggregate(
            domain_slug=domain_slug,
            appraisal_count=0,
            mean_judgement=None,
            median_judgement=None,
            dominant_certainty=None,
            certainty_score=None,
            combined_domain_score=None,
        )

    judgements = [Decimal(a.judgement) for a in appraisals]
    certainties = [a.certainty for a in appraisals]

    mean_j = (sum(judgements) / Decimal(count)).quantize(Decimal("0.01"))
    median_j = Decimal(median(judgements)).quantize(Decimal("0.01"))

    dominant = _dominant_certainty(certainties)
    cert_score = Decimal(CERTAINTY_NUMERIC[dominant]) if dominant else None

    if cert_score is not None:
        combined = ((mean_j + cert_score) / Decimal("2")).quantize(Decimal("0.01"))
    else:
        combined = mean_j

    return DomainAggregate(
        domain_slug=domain_slug,
        appraisal_count=count,
        mean_judgement=mean_j,
        median_judgement=median_j,
        dominant_certainty=dominant,
        certainty_score=cert_score,
        combined_domain_score=combined,
    )


def aggregate_overall(
    domain_aggregates: list[DomainAggregate], total_domains: int
) -> OverallScore:
    """Overall evidence-strength score = mean of completed-domain combined scores.

    Domains with zero appraisals are excluded from the mean but counted in
    `domains_completed` denominator only when they have data.
    """
    completed = [d for d in domain_aggregates if d.combined_domain_score is not None]

    if not completed:
        return OverallScore(
            domains_completed=0,
            domains_total=total_domains,
            evidence_strength_score=None,
            average_certainty=None,
        )

    scores = [d.combined_domain_score for d in completed]  # type: ignore[misc]
    evidence_strength = (sum(scores) / Decimal(len(scores))).quantize(Decimal("0.01"))

    all_certainties = [d.dominant_certainty for d in completed if d.dominant_certainty]
    avg_certainty = _dominant_certainty(all_certainties)

    return OverallScore(
        domains_completed=len(completed),
        domains_total=total_domains,
        evidence_strength_score=evidence_strength,
        average_certainty=avg_certainty,
    )
