"""Append-only audit log.

Design notes:
- Rows are INSERT-only. Any UPDATE or DELETE on this table is a bug.
  Enforced application-side via `Meta.permissions = []` and an overridden
  `delete()`; a future migration will add a database-level rule to deny
  UPDATE/DELETE outright.
- `actor` is nullable (system-initiated actions, failed-login attempts).
- `target` uses GenericForeignKey so any model can be audited.
- `diff` stores `{field: {"old": ..., "new": ...}}` as JSONB.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AuditLogQuerySet(models.QuerySet):
    def for_target(self, instance: models.Model) -> "AuditLogQuerySet":
        ct = ContentType.objects.get_for_model(type(instance))
        return self.filter(target_content_type=ct, target_object_id=str(instance.pk))


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "login_success", _("Login success")
        LOGIN_FAILED = "login_failed", _("Login failed")
        LOGOUT = "logout", _("Logout")
        CREATE = "create", _("Create")
        UPDATE = "update", _("Update")
        DELETE = "delete", _("Delete")
        APPROVE = "approve", _("Approve")
        LOCK = "lock", _("Lock version")
        UPLOAD = "upload", _("File upload")
        DOWNLOAD = "download", _("File download")
        PERMISSION_DENIED = "permission_denied", _("Permission denied")

    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    target_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    target_object_id = models.CharField(max_length=64, blank=True, default="")
    target = GenericForeignKey("target_content_type", "target_object_id")
    diff = models.JSONField(blank=True, null=True, help_text="Field-level old/new changes")
    metadata = models.JSONField(blank=True, null=True, help_text="Extra context (session, reason)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True, editable=False)

    objects = AuditLogQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Audit log entry")
        verbose_name_plural = _("Audit log")
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["target_content_type", "target_object_id"]),
        ]
        permissions = []  # No add/change/delete via Django admin

    def __str__(self) -> str:
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.action} by {self.actor or 'system'}"

    @classmethod
    def record(
        cls,
        *,
        action: str | Action,
        actor: Any | None = None,
        target: models.Model | None = None,
        diff: dict | None = None,
        metadata: dict | None = None,
        ip: str | None = None,
        user_agent: str = "",
    ) -> "AuditLog":
        kwargs: dict[str, Any] = {
            "action": action.value if isinstance(action, cls.Action) else action,
            "actor": actor if (actor and getattr(actor, "is_authenticated", False)) else None,
            "diff": diff,
            "metadata": metadata,
            "ip_address": ip,
            "user_agent": user_agent[:512],
        }
        if target is not None:
            kwargs["target_content_type"] = ContentType.objects.get_for_model(type(target))
            kwargs["target_object_id"] = str(target.pk)
        return cls.objects.create(**kwargs)

    # Append-only enforcement. A future DB-level rule will harden this.
    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise PermissionError("AuditLog entries are append-only and may not be deleted.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is not None:
            raise PermissionError("AuditLog entries are append-only and may not be modified.")
        super().save(*args, **kwargs)
