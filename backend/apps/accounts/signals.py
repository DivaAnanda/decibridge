"""Signal handlers for login/logout events.

Logs to the append-only AuditLog. Imported by AccountsConfig.ready().
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.http import HttpRequest


def _client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def on_user_logged_in(sender: Any, request: HttpRequest | None, user: Any, **kwargs: Any) -> None:
    from apps.audit.models import AuditLog

    ip = _client_ip(request)
    if ip:
        user.last_login_ip = ip
        user.save(update_fields=["last_login_ip"])
    AuditLog.record(
        action=AuditLog.Action.LOGIN_SUCCESS,
        actor=user,
        target=user,
        ip=ip,
        metadata={"session_key": request.session.session_key if request else None},
    )


@receiver(user_logged_out)
def on_user_logged_out(sender: Any, request: HttpRequest | None, user: Any, **kwargs: Any) -> None:
    from apps.audit.models import AuditLog

    AuditLog.record(
        action=AuditLog.Action.LOGOUT,
        actor=user,
        target=user,
        ip=_client_ip(request),
    )


@receiver(user_login_failed)
def on_user_login_failed(sender: Any, credentials: dict, request: HttpRequest | None = None, **kwargs: Any) -> None:
    from apps.audit.models import AuditLog

    AuditLog.record(
        action=AuditLog.Action.LOGIN_FAILED,
        actor=None,
        target=None,
        ip=_client_ip(request),
        metadata={"email_attempted": credentials.get("email") or credentials.get("username")},
    )
