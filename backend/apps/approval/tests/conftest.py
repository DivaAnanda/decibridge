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


def _make_dossier_complete(case, user):
    """Satisfy the Phase V3 sign-off gate: CEA + BIA + all 9 EtD domains.

    Sign-off is blocked on an incomplete dossier, so any fixture that is about
    to approve a case must supply one. Values are placeholders — these tests
    cover signature mechanics, not the economics.
    """
    from apps.econ.models import EconBIAResult, EconDeterministicResult
    from apps.etd.models import EtDAppraisal, EtDDomain

    EconDeterministicResult.objects.create(
        case=case,
        input_snapshot={"dummy": True},
        total_cost_intervention=Decimal("18499451.85"),
        total_cost_comparator=Decimal("5199411.1161"),
        total_qaly_intervention=Decimal("0.655"),
        total_qaly_comparator=Decimal("0.62923"),
        incremental_cost=Decimal("13300040.7339"),
        incremental_qaly=Decimal("0.02577"),
        icer=Decimal("516105577.5669"),
        nmb_intervention=Decimal("1"),
        nmb_comparator=Decimal("0"),
        inb=Decimal("-11109590.7339"),
        wtp_threshold_used=Decimal("85000000"),
        decision_code="not_cost_effective",
        is_cost_effective=False,
        is_dominant=False,
        is_dominated=False,
        interpretation_text="fixture",
        computed_by=user,
    )
    EconBIAResult.objects.create(
        case=case,
        input_snapshot={"dummy": True},
        cumulative_net_impact=Decimal("399001222.017"),
        pct_of_total_baseline=Decimal("0.798"),
        annual_budget_baseline=Decimal("50000000000"),
        severity="manageable",
        budget_score=80,
        per_year=[],
        scenarios=[],
        interpretation_text="fixture",
        computed_by=user,
    )
    for domain in EtDDomain.objects.all():
        EtDAppraisal.objects.create(
            case=case, domain=domain, member=user, judgement=75, certainty="high"
        )


@pytest.fixture
def green_recommendation(case_in_review, hta_user):
    _make_dossier_complete(case_in_review, hta_user)
    return _build_green_recommendation(case_in_review, hta_user)


@pytest.fixture
def draft_recommendation(pilot_case, hta_user):
    """Recommendation row attached to a still-draft case (no submit transition).

    Used to verify sign-off preconditions reject non-in_review cases.
    """
    return _build_green_recommendation(pilot_case, hta_user)
