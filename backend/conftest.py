"""Project-wide pytest fixtures.

Lives at backend/conftest.py so every test file under apps/ inherits these.
App-local conftests can still add per-app fixtures.
"""

from __future__ import annotations

import django
import pytest
from django.conf import settings


def pytest_configure() -> None:
    if not settings.configured:
        django.setup()


# ── HTTP client ──────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


# ── Users + roles ────────────────────────────────────────────────────────
@pytest.fixture
def user_factory(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def _make(email: str = "user@example.com", password: str = "TestPass123!", **extra):
        return User.objects.create_user(
            email=email,
            password=password,
            full_name=extra.pop("full_name", "Test User"),
            **extra,
        )

    return _make


@pytest.fixture
def role_factory(db):
    from apps.accounts.models import Role, RoleSlug

    def _get(slug):
        slug_value = slug.value if isinstance(slug, RoleSlug) else slug
        return Role.objects.get(slug=slug_value)

    return _get


def _user_with_role(user_factory, role_factory, email: str, full_name: str, role_slug):
    user = user_factory(email=email, full_name=full_name)
    user.groups.add(role_factory(role_slug).group)
    return user


@pytest.fixture
def hta_role(role_factory):
    from apps.accounts.models import RoleSlug

    return role_factory(RoleSlug.HTA_ANALYST)


@pytest.fixture
def ketua_role(role_factory):
    from apps.accounts.models import RoleSlug

    return role_factory(RoleSlug.KETUA_KFT)


@pytest.fixture
def hta_user(user_factory, role_factory):
    from apps.accounts.models import RoleSlug

    return _user_with_role(user_factory, role_factory, "hta@example.com", "HTA Analyst", RoleSlug.HTA_ANALYST)


@pytest.fixture
def ketua_user(user_factory, role_factory):
    from apps.accounts.models import RoleSlug

    return _user_with_role(user_factory, role_factory, "ketua@example.com", "Ketua KFT", RoleSlug.KETUA_KFT)


@pytest.fixture
def sekretaris_user(user_factory, role_factory):
    from apps.accounts.models import RoleSlug

    return _user_with_role(
        user_factory, role_factory, "sekre@example.com", "Sekretaris KFT", RoleSlug.FARMASI_SEKRETARIS
    )


@pytest.fixture
def kft_member_user(user_factory, role_factory):
    from apps.accounts.models import RoleSlug

    return _user_with_role(
        user_factory, role_factory, "member@example.com", "Anggota KFT", RoleSlug.KFT_MEMBER
    )


@pytest.fixture
def admin_it_user(user_factory, role_factory):
    from apps.accounts.models import RoleSlug

    return _user_with_role(
        user_factory, role_factory, "adminit@example.com", "Admin IT", RoleSlug.ADMIN_IT
    )


# ── Authenticated DRF clients ────────────────────────────────────────────
# Each fixture builds its OWN APIClient so tests that request multiple authed
# clients in one test don't trample each other's credentials.
def _make_authed_client(user, password="TestPass123!"):
    from rest_framework.test import APIClient

    client = APIClient()
    response = client.post(
        "/api/v1/auth/login/",
        {"email": user.email, "password": password},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def authed_client(hta_user):
    return _make_authed_client(hta_user)


@pytest.fixture
def hta_client(hta_user):
    return _make_authed_client(hta_user)


@pytest.fixture
def sekretaris_client(sekretaris_user):
    return _make_authed_client(sekretaris_user)


@pytest.fixture
def ketua_client(ketua_user):
    return _make_authed_client(ketua_user)


@pytest.fixture
def kft_member_client(kft_member_user):
    return _make_authed_client(kft_member_user)


@pytest.fixture
def admin_it_client(admin_it_user):
    return _make_authed_client(admin_it_user)


# ── Domain fixtures shared across apps ───────────────────────────────────
@pytest.fixture
def pilot_case(db, hta_user):
    from apps.cases.models import Case, CasePerspective

    return Case.objects.create(
        case_id="HF_ARNI_ACEI_001",
        case_title="ARNI vs ACEI pada pasien HFrEF",
        technology="Sacubitril/valsartan",
        comparator="ACE inhibitor",
        indication="Heart failure with reduced ejection fraction",
        population="Pasien HFrEF rawat jalan/rawat inap sesuai kriteria RS",
        setting="KFT Rumah Sakit",
        perspective=CasePerspective.HOSPITAL,
        created_by=hta_user,
    )
