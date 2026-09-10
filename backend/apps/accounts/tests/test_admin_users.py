"""Round 3 (L4): Admin IT user administration."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import RoleSlug
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db

User = get_user_model()


def _list_url() -> str:
    return reverse("accounts:admin_user_list")


def _detail_url(user_id: int) -> str:
    return reverse("accounts:admin_user_detail", args=[user_id])


def _reset_url(user_id: int) -> str:
    return reverse("accounts:admin_user_force_password_reset", args=[user_id])


class TestAccessControl:
    def test_admin_it_can_list_users(self, admin_it_client):
        assert admin_it_client.get(_list_url()).status_code == 200

    @pytest.mark.parametrize(
        "client_fixture",
        ["hta_client", "sekretaris_client", "ketua_client", "kft_member_client"],
    )
    def test_other_roles_cannot_list_users(self, request, client_fixture):
        client = request.getfixturevalue(client_fixture)
        assert client.get(_list_url()).status_code == 403

    def test_anonymous_cannot_list_users(self, api_client):
        assert api_client.get(_list_url()).status_code == 401


class TestListing:
    def test_listing_includes_roles_and_status(self, admin_it_client, hta_user):
        response = admin_it_client.get(_list_url())

        row = next(r for r in response.data if r["id"] == hta_user.id)
        assert RoleSlug.HTA_ANALYST in row["roles"]
        assert row["is_active"] is True

    def test_search_filters_by_email(self, admin_it_client, hta_user):
        response = admin_it_client.get(_list_url(), {"search": hta_user.email})

        assert [r["id"] for r in response.data] == [hta_user.id]

    def test_listing_never_exposes_a_password(self, admin_it_client, hta_user):
        response = admin_it_client.get(_list_url())

        assert all("password" not in r for r in response.data)


class TestDeactivation:
    def test_admin_can_deactivate_an_account(self, admin_it_client, hta_user):
        response = admin_it_client.patch(
            _detail_url(hta_user.id), {"is_active": False}, format="json"
        )

        assert response.status_code == 200
        hta_user.refresh_from_db()
        assert hta_user.is_active is False

    def test_admin_cannot_deactivate_themselves(self, admin_it_client, admin_it_user):
        response = admin_it_client.patch(
            _detail_url(admin_it_user.id), {"is_active": False}, format="json"
        )

        assert response.status_code == 400
        admin_it_user.refresh_from_db()
        assert admin_it_user.is_active is True

    def test_deactivation_is_audited(self, admin_it_client, hta_user):
        admin_it_client.patch(_detail_url(hta_user.id), {"is_active": False}, format="json")

        entry = AuditLog.objects.filter(action=AuditLog.Action.UPDATE).latest("created_at")
        assert entry.metadata["module"] == "user_administration"
        assert entry.diff["after"]["is_active"] is False


class TestRoleAssignment:
    def test_admin_can_replace_roles(self, admin_it_client, hta_user):
        response = admin_it_client.patch(
            _detail_url(hta_user.id), {"roles": [RoleSlug.KFT_MEMBER]}, format="json"
        )

        assert response.status_code == 200
        assert response.data["roles"] == [RoleSlug.KFT_MEMBER.value]

    def test_admin_cannot_drop_their_own_admin_role(self, admin_it_client, admin_it_user):
        response = admin_it_client.patch(
            _detail_url(admin_it_user.id), {"roles": [RoleSlug.KFT_MEMBER]}, format="json"
        )

        assert response.status_code == 400
        admin_it_user.refresh_from_db()
        assert RoleSlug.ADMIN_IT in admin_it_user.role_slugs

    def test_unknown_role_is_rejected(self, admin_it_client, hta_user):
        response = admin_it_client.patch(
            _detail_url(hta_user.id), {"roles": ["wizard"]}, format="json"
        )

        assert response.status_code == 400

    def test_empty_payload_is_rejected(self, admin_it_client, hta_user):
        assert admin_it_client.patch(_detail_url(hta_user.id), {}, format="json").status_code == 400


class TestForcedPasswordReset:
    def test_admin_can_force_a_reset(self, admin_it_client, hta_user):
        response = admin_it_client.post(_reset_url(hta_user.id))

        assert response.status_code == 200
        hta_user.refresh_from_db()
        assert hta_user.must_change_password is True

    def test_forcing_twice_is_refused(self, admin_it_client, hta_user):
        admin_it_client.post(_reset_url(hta_user.id))

        assert admin_it_client.post(_reset_url(hta_user.id)).status_code == 409

    def test_reset_does_not_change_the_password(self, admin_it_client, hta_user):
        original = hta_user.password

        admin_it_client.post(_reset_url(hta_user.id))

        hta_user.refresh_from_db()
        assert hta_user.password == original

    def test_changing_the_password_clears_the_flag(self, hta_client, hta_user):
        hta_user.must_change_password = True
        hta_user.save(update_fields=["must_change_password"])

        response = hta_client.post(
            reverse("accounts:password_change"),
            {"current_password": "TestPass123!", "new_password": "BrandNewPass456!"},
            format="json",
        )

        assert response.status_code == 200, response.data
        hta_user.refresh_from_db()
        assert hta_user.must_change_password is False


class TestLoginHistory:
    def test_admin_can_read_login_history(self, admin_it_client):
        response = admin_it_client.get(reverse("accounts:admin_login_history"))

        assert response.status_code == 200

    def test_other_roles_cannot(self, sekretaris_client):
        response = sekretaris_client.get(reverse("accounts:admin_login_history"))

        assert response.status_code == 403

    def test_only_failed_filter_excludes_successes(self, admin_it_client, hta_user):
        AuditLog.record(action=AuditLog.Action.LOGIN_SUCCESS, actor=hta_user)
        AuditLog.record(action=AuditLog.Action.LOGIN_FAILED, metadata={"email": "x@y.z"})

        response = admin_it_client.get(
            reverse("accounts:admin_login_history"), {"only_failed": "true"}
        )

        assert response.data
        assert all(r["action"] == AuditLog.Action.LOGIN_FAILED for r in response.data)
