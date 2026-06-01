"""Approval-only fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation


@pytest.fixture
def case_in_review(pilot_case, hta_user):
    """Walk the pilot case to in_review status (where sign-off is allowed)."""
    case_transition(pilot_case, "submit", hta_user)
    pilot_case.refresh_from_db()
    return pilot_case


def _build_green_recommendation(case, user):
    return Recommendation.objects.create(
        case=case,
        input_snapshot={"dummy": True},
        evidence_strength_score=Decimal("90"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        cba_score=Decimal("100"),
        composite_score=Decimal("92.00"),
        traffic_light="green",
        justification_text="Green test fixture.",
        cba_criteria_count=0,
        cba_satisfied_count=0,
        algorithm_version="1.0.0",
        weight_aggregation_method="mean",
        computed_by=user,
    )


@pytest.fixture
def green_recommendation(case_in_review, hta_user):
    return _build_green_recommendation(case_in_review, hta_user)


@pytest.fixture
def draft_recommendation(pilot_case, hta_user):
    """Recommendation row attached to a still-draft case (no submit transition).

    Used to verify sign-off preconditions reject non-in_review cases.
    """
    return _build_green_recommendation(pilot_case, hta_user)
