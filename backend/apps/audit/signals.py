"""Generic audit hooks.

Sprint 1 keeps the auto-audit list narrow (just the User model). As future
sprints add Case / Recommendation / Approval etc., register them here with
`register_auditable(Model)`.
"""

from __future__ import annotations

from typing import Any

from crum import get_current_request, get_current_user
from django.db.models import Model
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import client_ip
from .models import AuditLog

_AUDITABLE: set[type[Model]] = set()
_PRE_SNAPSHOTS: dict[tuple[str, str], dict[str, Any]] = {}


def register_auditable(model: type[Model]) -> None:
    """Mark a model so every save/delete writes to AuditLog."""
    _AUDITABLE.add(model)


def _is_auditable(model: type[Model]) -> bool:
    return any(issubclass(model, m) for m in _AUDITABLE)


def _serialize(instance: Model) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in instance._meta.fields:
        if field.name in {"password", "last_login"}:
            continue
        value = getattr(instance, field.attname, None)
        try:
            out[field.name] = str(value) if value is not None else None
        except Exception:
            out[field.name] = "<unserializable>"
    return out


def _diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        key: {"old": old.get(key), "new": new.get(key)}
        for key in set(old) | set(new)
        if old.get(key) != new.get(key)
    }


@receiver(pre_save)
def snapshot_before_save(sender: type[Model], instance: Model, **kwargs: Any) -> None:
    if not _is_auditable(sender) or instance.pk is None:
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    _PRE_SNAPSHOTS[(sender.__name__, str(instance.pk))] = _serialize(previous)


@receiver(post_save)
def log_save(sender: type[Model], instance: Model, created: bool, **kwargs: Any) -> None:
    if not _is_auditable(sender):
        return
    key = (sender.__name__, str(instance.pk))
    request = get_current_request()
    actor = get_current_user()
    new_state = _serialize(instance)

    if created:
        AuditLog.record(
            action=AuditLog.Action.CREATE,
            actor=actor,
            target=instance,
            diff={k: {"old": None, "new": v} for k, v in new_state.items()},
            ip=client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
        )
    else:
        previous = _PRE_SNAPSHOTS.pop(key, {})
        diff = _diff(previous, new_state)
        if not diff:
            return
        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=actor,
            target=instance,
            diff=diff,
            ip=client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
        )


@receiver(post_delete)
def log_delete(sender: type[Model], instance: Model, **kwargs: Any) -> None:
    if not _is_auditable(sender):
        return
    request = get_current_request()
    AuditLog.record(
        action=AuditLog.Action.DELETE,
        actor=get_current_user(),
        target=instance,
        diff={k: {"old": v, "new": None} for k, v in _serialize(instance).items()},
        ip=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else ""),
    )


# Register the User model for automatic auditing.
def _wire_default_models() -> None:
    from apps.accounts.models import User

    register_auditable(User)


_wire_default_models()
