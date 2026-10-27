"""Test data for the recommendation app."""

from __future__ import annotations

from apps.recommendation.models import FinalDecision, FinalDecisionType


def make_final_decision(
    case, user, *, decision: str = FinalDecisionType.ADOPT_WITH_CRITERIA, recommendation=None
) -> FinalDecision:
    """A KFT final decision on the case's latest recommendation."""
    return FinalDecision.objects.create(
        case=case,
        recommendation=recommendation or case.recommendations.latest("computed_at"),
        decision=decision,
        reason="Alasan pengujian.",
        decided_by=user,
    )
