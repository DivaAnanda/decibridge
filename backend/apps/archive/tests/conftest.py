"""Archive test fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation


@pytest.fixture
def locked_case(pilot_case, hta_user, ketua_user):
    """Case driven through: draft → submit → recommendation → approve → lock.

    Not yet archived. Used as the starting point for archive tests.
    """
    case_transition(pilot_case, "submit", hta_user)
    Recommendation.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        evidence_strength_score=Decimal("90"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        cba_score=Decimal("100"),
        composite_score=Decimal("92.00"),
        traffic_light="green",
        justification_text="Test.",
        cba_criteria_count=0,
        cba_satisfied_count=0,
        algorithm_version="1.0.0",
        weight_aggregation_method="mean",
        computed_by=hta_user,
    )
    case_transition(pilot_case, "approve", ketua_user)
    case_transition(pilot_case, "lock", ketua_user)
    pilot_case.refresh_from_db()
    return pilot_case


@pytest.fixture
def archived_case(locked_case, ketua_user):
    """Case driven all the way through to archived. Triggers manifest generation."""
    case_transition(locked_case, "archive", ketua_user)
    locked_case.refresh_from_db()
    return locked_case
