"""Formal sign-off events on a case's recommendation.

One immutable row per signature attempt. Three decision types:
  - APPROVED: Ketua KFT accepts the recommendation; case transitions to 'approved'.
  - REJECTED: hard rejection; case transitions back to 'draft' with reason.
  - REVISION_REQUESTED: soft rejection; case transitions back to 'draft' with reason.

Approval is intentionally separate from lock per the design choice — the
Ketua KFT first signs to approve, then later issues a separate 'lock'
transition once any post-approval CBA refinement is settled.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.cases.models import Case
from apps.recommendation.models import Recommendation


class ApprovalDecision(models.TextChoices):
    APPROVED = "approved", _("Disetujui")
    REJECTED = "rejected", _("Ditolak")
    REVISION_REQUESTED = "revision_requested", _("Minta Revisi")


class Approval(models.Model):
    """One Ketua KFT sign-off event. Immutable append-only."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="approvals")
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.PROTECT,
        related_name="approvals",
        help_text=_("Exact recommendation row that was reviewed and signed."),
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approvals_made",
    )
    decision = models.CharField(max_length=24, choices=ApprovalDecision.choices)
    confirmation_acknowledged = models.BooleanField(
        default=False,
        help_text=_("Checkbox 'Saya konfirmasi...' was ticked at sign time."),
    )
    password_verified_at = models.DateTimeField(
        help_text=_("Server-side check_password() success timestamp."),
    )
    reason = models.TextField(
        blank=True,
        default="",
        help_text=_("Required for REJECTED and REVISION_REQUESTED."),
    )
    signed_at = models.DateTimeField(default=timezone.now, editable=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["-signed_at"]
        verbose_name = _("Approval")
        verbose_name_plural = _("Approvals")
        indexes = [models.Index(fields=["case", "-signed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} → {self.decision} by {self.approver.email} at {self.signed_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError(
                "Approval rows are immutable; create a new row for any change."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Approval rows are append-only and cannot be deleted.")
