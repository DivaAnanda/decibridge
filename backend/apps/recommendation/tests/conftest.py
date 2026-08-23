"""Recommendation-only fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounts.models import RoleSlug
from apps.econ.models import EconBIAResult, EconDeterministicResult
from apps.etd.models import EtDAppraisal
from apps.recommendation.models import CBACriterion, DomainWeightVote


@pytest.fixture
def member_factory(user_factory, role_factory):
    def _make(email: str):
        user = user_factory(email=email, full_name=f"KFT {email}")
        user.groups.add(role_factory(RoleSlug.KFT_MEMBER).group)
        return user

    return _make


@pytest.fixture
def kft_three(member_factory):
    return [member_factory(f"kft{i}@example.com") for i in range(1, 4)]


@pytest.fixture
def etd_domains(db):
    from apps.etd.models import EtDDomain

    return list(EtDDomain.objects.all().order_by("order"))


@pytest.fixture
def seeded_econ_result(pilot_case, hta_user):
    """Deterministic econ result that maps to CE sub-score 100 (ICER well under WTP)."""
    return EconDeterministicResult.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        total_cost_intervention=Decimal("18499451.85"),
        total_cost_comparator=Decimal("5199411.1161"),
        total_qaly_intervention=Decimal("0.655"),
        total_qaly_comparator=Decimal("0.62923"),
        incremental_cost=Decimal("13300040.7339"),
        incremental_qaly=Decimal("0.5000"),
        icer=Decimal("10000000"),
        nmb_intervention=Decimal("1"),
        nmb_comparator=Decimal("0"),
        inb=Decimal("1"),
        wtp_threshold_used=Decimal("250000000"),
        decision_code="cost_effective",
        is_cost_effective=True,
        is_dominant=False,
        is_dominated=False,
        interpretation_text="seed",
        algorithm_version="2.0.0",
        computed_by=hta_user,
    )


@pytest.fixture
def seeded_bia_result(pilot_case, hta_user):
    """Econ cost-offset BIA result feeding budget_score 80 (manageable)."""
    return EconBIAResult.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        cumulative_net_impact=Decimal("1500000000"),
        pct_of_total_baseline=Decimal("3.0000"),
        annual_budget_baseline=Decimal("50000000000"),
        severity="manageable",
        budget_score=80,
        per_year=[],
        interpretation_text="seed",
        algorithm_version="1.0.0",
        computed_by=hta_user,
    )


@pytest.fixture
def seeded_etd_votes(pilot_case, etd_domains, kft_three):
    """One appraisal per member per domain, judgement=75, certainty=high."""
    for d in etd_domains:
        for m in kft_three:
            EtDAppraisal.objects.create(
                case=pilot_case, domain=d, member=m, judgement=75, certainty="high"
            )


@pytest.fixture
def seeded_weights(pilot_case, etd_domains, kft_three):
    for d in etd_domains:
        for m in kft_three:
            DomainWeightVote.objects.create(
                case=pilot_case, domain=d, member=m, weight=50
            )


@pytest.fixture
def cba_factory(pilot_case, hta_user):
    def _make(name: str, *, is_satisfied: bool = False, order: int = 1) -> CBACriterion:
        return CBACriterion.objects.create(
            case=pilot_case,
            order=order,
            criterion_name=name,
            operator="is_present",
            is_satisfied=is_satisfied,
            created_by=hta_user,
            last_edited_by=hta_user,
        )

    return _make
