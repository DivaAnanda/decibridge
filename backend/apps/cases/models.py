from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

CASE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")


def validate_case_id(value: str) -> None:
    if not CASE_ID_PATTERN.match(value):
        raise ValidationError(
            _("case_id must be UPPER_SNAKE_CASE, 3-64 chars, e.g. HF_ARNI_ACEI_001"),
            code="invalid_case_id",
        )


class CaseStatus(models.TextChoices):
    """Status state machine for a Case.

    Transitions are enforced by state_machine.py — never write to .status directly
    from views; always go through CaseStateMachine.transition().
    """

    DRAFT = "draft", _("Draft")
    IN_REVIEW = "in_review", _("Dalam tinjauan")
    APPROVED = "approved", _("Disetujui")
    LOCKED = "locked", _("Terkunci")
    ARCHIVED = "archived", _("Diarsipkan")


class CasePerspective(models.TextChoices):
    HOSPITAL = "hospital", _("Rumah Sakit")
    PAYER_BPJS = "payer_bpjs", _("BPJS / Pembayar")
    SOCIETAL = "societal", _("Masyarakat")


class Case(models.Model):
    """One formulary decision (e.g. ARNI vs ACEI for HFrEF).

    Field names mirror the brief's `01_case_meta` sheet so Excel import in
    Sprint 3 has a 1:1 mapping.
    """

    case_id = models.CharField(
        max_length=64,
        unique=True,
        validators=[validate_case_id],
        help_text=_("Slug seperti HF_ARNI_ACEI_001"),
    )
    case_title = models.CharField(max_length=255)
    technology = models.CharField(
        max_length=255,
        help_text=_("Intervensi / teknologi yang dievaluasi (mis. Sacubitril/valsartan)"),
    )
    comparator = models.CharField(max_length=255)
    indication = models.CharField(max_length=255)
    population = models.TextField(blank=True, default="")
    setting = models.CharField(max_length=255, blank=True, default="")
    perspective = models.CharField(
        max_length=32, choices=CasePerspective.choices, default=CasePerspective.HOSPITAL
    )

    status = models.CharField(
        max_length=16,
        choices=CaseStatus.choices,
        default=CaseStatus.DRAFT,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cases_created",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Case")
        verbose_name_plural = _("Cases")

    def __str__(self) -> str:
        return f"{self.case_id} — {self.case_title}"

    @property
    def is_editable(self) -> bool:
        return self.status in {CaseStatus.DRAFT, CaseStatus.IN_REVIEW}

    @property
    def is_locked(self) -> bool:
        return self.status in {CaseStatus.LOCKED, CaseStatus.ARCHIVED}


class DecisionQuestion(models.Model):
    """PICO-style decision question(s) attached to a Case.

    Maps to the brief's decision_questions table; a case can have multiple
    questions if the appraisal covers more than one subpopulation.
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="decision_questions")
    order = models.PositiveSmallIntegerField(default=1)
    question_text = models.TextField(help_text=_("Pertanyaan klinis lengkap"))
    pico_population = models.CharField(max_length=255, blank=True, default="")
    pico_intervention = models.CharField(max_length=255, blank=True, default="")
    pico_comparator = models.CharField(max_length=255, blank=True, default="")
    pico_outcome = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ["case", "order"]
        unique_together = [("case", "order")]
        verbose_name = _("Decision Question")
        verbose_name_plural = _("Decision Questions")

    def __str__(self) -> str:
        return f"{self.case.case_id} Q{self.order}"


class CaseVersionStatus(models.TextChoices):
    DRAFT = "draft", _("Draft (v0.x)")
    LOCKED = "locked", _("Locked (v1.x)")
    ARCHIVED = "archived", _("Archived")


class CaseVersion(models.Model):
    """Semantic version snapshot of a Case.

    Sprint 2 creates v0.1.0 implicitly when a case is born. Later sprints
    (8 + 10) handle lock-on-approval and major-revision bumps to v1.x / v2.x.
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="versions")
    version_number = models.CharField(
        max_length=32,
        help_text=_("Semantic version, e.g. 0.1.0 or 1.0.0"),
    )
    status = models.CharField(
        max_length=16, choices=CaseVersionStatus.choices, default=CaseVersionStatus.DRAFT
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_versions_locked",
    )
    lock_reason = models.TextField(blank=True, default="")
    diff = models.JSONField(blank=True, null=True, help_text=_("Field-level diff from prior version"))
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="case_versions_created",
    )

    class Meta:
        ordering = ["case", "-created_at"]
        unique_together = [("case", "version_number")]
        verbose_name = _("Case Version")
        verbose_name_plural = _("Case Versions")

    def __str__(self) -> str:
        return f"{self.case.case_id} v{self.version_number}"
