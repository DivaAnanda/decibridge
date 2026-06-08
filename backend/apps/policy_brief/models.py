from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case


class GenerationStatus(models.TextChoices):
    GENERATING = "generating", _("Sedang diproses")
    COMPLETED = "completed", _("Selesai")
    FAILED = "failed", _("Gagal")


class PolicyBriefDocument(models.Model):
    """Generated policy-brief artifact (DOCX + PDF) for a case.

    Append-only — once a brief is generated, the row cannot be edited or deleted.
    To regenerate, create a new row with version+1.

    File layout on disk:
        media/policy_briefs/{case_id}/v{version}.docx
        media/policy_briefs/{case_id}/v{version}.pdf
    """

    case = models.ForeignKey(
        Case,
        on_delete=models.PROTECT,
        related_name="policy_briefs",
    )
    version = models.PositiveIntegerField(
        help_text=_("Monotonically increasing per case. v1 is the first generation."),
    )
    status = models.CharField(
        max_length=16,
        choices=GenerationStatus.choices,
        default=GenerationStatus.GENERATING,
        db_index=True,
    )

    docx_path = models.CharField(max_length=512, blank=True, default="")
    pdf_path = models.CharField(max_length=512, blank=True, default="")
    docx_sha256 = models.CharField(max_length=64, blank=True, default="")
    pdf_sha256 = models.CharField(max_length=64, blank=True, default="")
    docx_size_bytes = models.PositiveIntegerField(default=0)
    pdf_size_bytes = models.PositiveIntegerField(default=0)

    error_message = models.TextField(blank=True, default="")

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="policy_briefs_generated",
    )
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Snapshot of the recommendation row used as the source of truth.
    # Preserved so the brief can be reproduced even if the recommendation table
    # has additional rows appended later.
    source_recommendation_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("ID of the Recommendation row used to generate this brief."),
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ("-generated_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["case", "version"],
                name="unique_policy_brief_per_version",
            ),
        ]
        verbose_name = _("Policy brief document")
        verbose_name_plural = _("Policy brief documents")

    def __str__(self) -> str:
        return f"{self.case.case_id} v{self.version} [{self.status}]"

    # ------------------------------------------------------------------ #
    # Append-only invariant
    # ------------------------------------------------------------------ #
    # A brief row may transition from GENERATING → COMPLETED/FAILED exactly once.
    # After that, every save() must be the same data (idempotent re-saves only).
    # Update of an already-completed/failed row, or of identifying fields, raises.

    # Identity fields that may never change.
    _IMMUTABLE_FIELDS = frozenset(
        {
            "case_id",
            "version",
            "generated_by_id",
            "generated_at",
            "source_recommendation_id",
        }
    )
    # Status flow: must move forward only.
    _TERMINAL_STATUSES = frozenset({GenerationStatus.COMPLETED, GenerationStatus.FAILED})

    def save(self, *args, **kwargs) -> None:
        if self.pk is None:
            super().save(*args, **kwargs)
            return

        previous = type(self).objects.get(pk=self.pk)

        # Identity fields are immutable.
        for field in self._IMMUTABLE_FIELDS:
            if getattr(previous, field) != getattr(self, field):
                raise PermissionError(
                    f"PolicyBriefDocument.{field} is immutable once created."
                )

        # Once terminal, the only legal save is an idempotent no-op.
        if previous.status in self._TERMINAL_STATUSES:
            raise PermissionError(
                "PolicyBriefDocument is append-only after reaching a terminal "
                "status (completed/failed). Regenerate = create a new version."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        raise PermissionError("PolicyBriefDocument rows cannot be deleted.")
