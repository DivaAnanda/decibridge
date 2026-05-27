from __future__ import annotations

import pytest

from apps.audit.models import AuditLog


@pytest.mark.django_db
class TestAuditLogAppendOnly:
    def test_record_creates_entry(self, hta_user):
        entry = AuditLog.record(
            action=AuditLog.Action.LOGIN_SUCCESS,
            actor=hta_user,
            target=hta_user,
            ip="127.0.0.1",
        )
        assert entry.pk is not None
        assert entry.action == "login_success"
        assert entry.actor == hta_user

    def test_cannot_be_modified(self, hta_user):
        entry = AuditLog.record(action=AuditLog.Action.LOGIN_SUCCESS, actor=hta_user)
        entry.action = "logout"
        with pytest.raises(PermissionError):
            entry.save()

    def test_cannot_be_deleted(self, hta_user):
        entry = AuditLog.record(action=AuditLog.Action.LOGIN_SUCCESS, actor=hta_user)
        with pytest.raises(PermissionError):
            entry.delete()


@pytest.mark.django_db
class TestLoginAuditTrail:
    def test_successful_login_writes_audit_entry(self, api_client, hta_user):
        before = AuditLog.objects.filter(action="login_success").count()
        api_client.post(
            "/api/v1/auth/login/",
            {"email": hta_user.email, "password": "TestPass123!"},
            format="json",
        )
        after = AuditLog.objects.filter(action="login_success").count()
        assert after == before + 1

    def test_failed_login_writes_audit_entry(self, api_client, hta_user):
        before = AuditLog.objects.filter(action="login_failed").count()
        api_client.post(
            "/api/v1/auth/login/",
            {"email": hta_user.email, "password": "WrongPass"},
            format="json",
        )
        after = AuditLog.objects.filter(action="login_failed").count()
        assert after == before + 1


@pytest.mark.django_db
class TestUserMutationAudit:
    def test_user_update_creates_update_entry(self, hta_user):
        before = AuditLog.objects.filter(action="update").for_target(hta_user).count()
        hta_user.full_name = "Renamed User"
        hta_user.save()
        after = AuditLog.objects.filter(action="update").for_target(hta_user).count()
        assert after == before + 1
