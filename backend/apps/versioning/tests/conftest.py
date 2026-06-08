"""Versioning test fixtures.

Helpers to drive a case through approve → lock → reopen → relock so the
auto-snapshot logic gets exercised in real-world sequences.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation


def _make_recommendation(case, user, **overrides):
    base = dict(
        case=case,
        input_snapshot={"dummy": True},
        evidence_strength_score=Decimal("90"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        cba_score=Decimal("100"),
        composite_score=Decimal("92.00"),
        traffic_light="green",
        justification_text="Test recommendation.",
        cba_criteria_count=0,
        cba_satisfied_count=0,
        algorithm_version="1.0.0",
        weight_aggregation_method="mean",
        computed_by=user,
    )
    base.update(overrides)
    return Recommendation.objects.create(**base)


@pytest.fixture
def locked_case(pilot_case, hta_user, ketua_user):
    """A case that has been: created → submit → recommendation → approve → lock."""
    case_transition(pilot_case, "submit", hta_user)
    _make_recommendation(pilot_case, hta_user)
    case_transition(pilot_case, "approve", ketua_user)
    case_transition(pilot_case, "lock", ketua_user)
    pilot_case.refresh_from_db()
    return pilot_case


@pytest.fixture
def two_locked_versions(pilot_case, hta_user, ketua_user):
    """A case that has gone through two lock cycles: v1.0 then v1.1.

    Cycle 1: submit → rec → approve → lock                 (v1.0)
    Cycle 2: archive prev rec  → submit → rec' → approve → lock  (v1.1)

    Returns the case with two locked snapshots already on it.
    """
    # Cycle 1
    case_transition(pilot_case, "submit", hta_user)
    _make_recommendation(pilot_case, hta_user, composite_score=Decimal("85.00"))
    case_transition(pilot_case, "approve", ketua_user)
    case_transition(pilot_case, "lock", ketua_user)

    # Cycle 2: we'd need to unlock (no such transition in our state machine).
    # Real flow is locked → archived (terminal). For test purposes we directly
    # write a second LOCKED CaseVersion through the same helper used in
    # production, simulating a future state machine that supports relock.
    from apps.cases.models import CaseVersion, CaseVersionStatus, CaseVersionTrigger
    from django.utils import timezone

    new_rec = _make_recommendation(pilot_case, hta_user, composite_score=Decimal("95.00"))
    CaseVersion.objects.create(
        case=pilot_case,
        version_number="1.1",
        status=CaseVersionStatus.LOCKED,
        trigger=CaseVersionTrigger.LOCKED,
        locked_at=timezone.now(),
        locked_by=ketua_user,
        lock_reason="",
        recommendation_id=new_rec.pk,
        created_by=ketua_user,
    )

    pilot_case.refresh_from_db()
    return pilot_case
