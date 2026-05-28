"""EtD-only fixtures. Shared user/case fixtures come from backend/conftest.py."""

from __future__ import annotations

import pytest

from apps.accounts.models import RoleSlug
from apps.etd.models import EtDAppraisal, EtDDomain, ReferenceCitation


@pytest.fixture
def etd_domains(db):
    """All 9 seeded domains, ordered."""
    return list(EtDDomain.objects.all().order_by("order"))


@pytest.fixture
def member_factory(user_factory, role_factory):
    def _make(email: str) -> "User":
        user = user_factory(email=email, full_name=f"KFT Member {email}")
        user.groups.add(role_factory(RoleSlug.KFT_MEMBER).group)
        return user

    return _make


@pytest.fixture
def kft_three(member_factory):
    return [member_factory(f"kft{i}@example.com") for i in range(1, 4)]


@pytest.fixture
def reference_factory(pilot_case, hta_user):
    def _make(**overrides) -> ReferenceCitation:
        defaults = {
            "case": pilot_case,
            "reference_type": "journal_article",
            "citation_text": "Smith J et al. 2024. Test reference. NEJM.",
            "authors": "Smith J",
            "publication_year": 2024,
            "title": "Test reference",
            "journal_name": "NEJM",
            "doi_pmid": "10.1056/test",
            "created_by": hta_user,
        }
        defaults.update(overrides)
        return ReferenceCitation.objects.create(**defaults)

    return _make


@pytest.fixture
def appraisal_factory(pilot_case, etd_domains):
    """Make an appraisal for (case, domain_slug, member, judgement, certainty)."""

    def _make(member, *, domain_slug="problem", judgement=75, certainty="moderate", narrative=""):
        domain = next(d for d in etd_domains if d.slug == domain_slug)
        return EtDAppraisal.objects.create(
            case=pilot_case,
            domain=domain,
            member=member,
            judgement=judgement,
            certainty=certainty,
            narrative=narrative,
        )

    return _make
