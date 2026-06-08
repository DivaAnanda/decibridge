"""ArchiveRecord — the seal on a decision's permanent record.

One ArchiveRecord per Case. Created automatically when the state machine
fires the `archive` transition (apps/cases/state_machine.py). After creation
the row is immutable: save() rejects updates, delete() always raises.

The manifest file lives at:
    media/archives/{case_id}/manifest.json

It contains the SHA-256 of every clinical/financial artifact tied to the
case, so tampering with any underlying row breaks the manifest's seal.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case


# 7-year retention per the brief's Step 15 — configurable but defaulted here.
DEFAULT_RETENTION_YEARS = 7


class ArchiveRecord(models.Model):
    case = models.OneToOneField(
        Case,
        on_delete=models.PROTECT,
        related_name="archive_record",
    )
    archived_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        db_index=True,
        help_text=_(
            "Set explicitly by the service so it matches retention_until exactly. "
            "Falls back to current time if instantiated outside the service."
        ),
    )
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="archives_created",
    )

    manifest_path = models.CharField(
        max_length=512,
        help_text=_("Path relative to MEDIA_ROOT for the manifest JSON file."),
    )
    manifest_sha256 = models.CharField(
        max_length=64,
        help_text=_("SHA-256 of the manifest JSON bytes — tamper detection seal."),
    )
    manifest_size_bytes = models.PositiveIntegerField(default=0)

    retention_until = models.DateTimeField(
        db_index=True,
        help_text=_("Earliest date the archive may be purged. Default = archived_at + 7 years."),
    )
    notes = models.TextField(blank=True, default="")

    # Counts captured at archive time — convenient summary without re-walking
    # the manifest. The full inventory lives in the JSON file.
    artifact_counts = models.JSONField(
        default=dict,
        help_text=_("Inventory summary: {recommendations: N, approvals: M, ...}"),
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ("-archived_at",)
        verbose_name = _("Archive Record")
        verbose_name_plural = _("Archive Records")

    def __str__(self) -> str:
        return f"{self.case.case_id} archived {self.archived_at:%Y-%m-%d}"

    # Append-only invariants ------------------------------------------------
    def save(self, *args, **kwargs) -> None:
        if self.pk is not None:
            raise PermissionError(
                "ArchiveRecord rows are immutable — the archive seal cannot be broken."
            )
        if self.retention_until is None and self.archived_at is not None:
            # archived_at is auto_now_add so on first save it's already set
            # by the time we reach super().save() — but be defensive.
            self.retention_until = self.archived_at + timedelta(
                days=DEFAULT_RETENTION_YEARS * 365
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        raise PermissionError("ArchiveRecord rows cannot be deleted.")
