"""Recommendation-only fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounts.models import RoleSlug
from apps.bia.models import BIAResult
from apps.cea.models import CEAResult
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
def seeded_cea_result(pilot_case, hta_user):
    return CEAResult.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        incremental_cost=Decimal("5000000"),
        incremental_effect=Decimal("0.5000"),
        icer_value=Decimal("10000000"),
        wtop_threshold_used=Decimal("250000000"),
        dominance="cost_effective_safe",
        ce_score=100,
        interpretation_text="seed",
        algorithm_version="1.0.0",
        computed_by=hta_user,
    )


@pytest.fixture
def seeded_bia_result(pilot_case, hta_user):
    return BIAResult.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        year1_drug_cost=Decimal("750000000"),
        year1_comparator_cost_displaced=Decimal("375000000"),
        year1_net_impact=Decimal("375000000"),
        cumulative_impact=Decimal("1500000000"),
        pct_of_annual_budget=Decimal("5.0000"),
        severity="manageable",
        direction="cost_increase",
        budget_score=80,
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
