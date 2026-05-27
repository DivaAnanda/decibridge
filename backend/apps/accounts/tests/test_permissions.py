from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import RoleSlug
from apps.accounts.permissions import HasRole, IsKetuaKFT


@pytest.mark.django_db
class TestRolePermissions:
    def test_ketua_permission_blocks_hta(self, hta_user):
        factory = APIRequestFactory()
        request = factory.get("/")
        force_authenticate(request, user=hta_user)
        request.user = hta_user
        assert IsKetuaKFT().has_permission(request, None) is False

    def test_ketua_permission_allows_ketua(self, ketua_user):
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = ketua_user
        assert IsKetuaKFT().has_permission(request, None) is True

    def test_any_of_matches_one_of_many(self, hta_user):
        permission_cls = HasRole.any_of(RoleSlug.HTA_ANALYST, RoleSlug.KETUA_KFT)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = hta_user
        assert permission_cls().has_permission(request, None) is True

    def test_all_of_requires_every_role(self, hta_user):
        permission_cls = HasRole.all_of(RoleSlug.HTA_ANALYST, RoleSlug.KETUA_KFT)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = hta_user
        assert permission_cls().has_permission(request, None) is False

    def test_superuser_bypasses_role_check(self, user_factory):
        admin = user_factory(email="admin@example.com", is_superuser=True, is_staff=True)
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = admin
        assert IsKetuaKFT().has_permission(request, None) is True


@pytest.mark.django_db
class TestRoleSeeding:
    def test_all_five_roles_exist(self):
        from apps.accounts.models import Role
        slugs = set(Role.objects.values_list("slug", flat=True))
        assert slugs == {
            "admin_it",
            "hta_analyst",
            "farmasi_sekretaris",
            "kft_member",
            "ketua_kft",
        }
