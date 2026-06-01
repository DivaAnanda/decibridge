"""Recommendation synthesis data model.

Three editable tables + one immutable result table:

- `DomainWeightVote`: one row per (case, EtD domain, KFT member). Each
  member assigns a 0-100 importance weight to each domain. Aggregation
  (mean/median) feeds the synthesis engine.

- `CBACriterion`: flat list of criteria per case, ANDed. Each is a
  manually-checked boolean (the system doesn't evaluate patient data
  against operators in Sprint 7 — that lands when Excel intake arrives).
  Operator + value are still captured for future automation.

- `Recommendation`: immutable append-only result of one
  "Hitung Rekomendasi" run. Stores the full input snapshot, sub-scores,
  composite score, traffic-light, and justification narrative.
"""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case
from apps.etd.models import EtDDomain


class DomainWeightVote(models.Model):
    """Per-member, per-domain weight vote (0-100)."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="weight_votes")
    domain = models.ForeignKey(
        EtDDomain, on_delete=models.PROTECT, related_name="weight_votes"
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="weight_votes",
    )
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Bobot kepentingan 0-100 untuk domain ini menurut anggota"),
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = [("case", "domain", "member")]
        ordering = ["case", "domain__order", "member__email"]
        verbose_name = _("Domain Weight Vote")
        verbose_name_plural = _("Domain Weight Votes")
        indexes = [models.Index(fields=["case", "domain"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} / {self.domain.slug} / {self.member.email} = {self.weight}"


class CBAOperator(models.TextChoices):
    EQUALS = "equals", _("Sama dengan")
    NOT_EQUALS = "not_equals", _("Tidak sama dengan")
    GREATER_THAN = "greater_than", _("Lebih besar dari")
    LESS_THAN = "less_than", _("Lebih kecil dari")
    IN_LIST = "in_list", _("Dalam daftar (comma-separated)")
    IS_PRESENT = "is_present", _("Ada / Terdapat")


class CBACriterion(models.Model):
    """One conditional-access criterion. AND-joined with other criteria."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="cba_criteria")
    order = models.PositiveSmallIntegerField(default=1)
    criterion_name = models.CharField(
        max_length=200,
        help_text=_("Nama singkat, mis. 'Diresepkan oleh kardiolog'"),
    )
    field_reference = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text=_("Field klinis yang dirujuk, mis. 'prescriber.specialty'"),
    )
    operator = models.CharField(max_length=24, choices=CBAOperator.choices, default=CBAOperator.IS_PRESENT)
    expected_value = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_satisfied = models.BooleanField(
        default=False,
        help_text=_("Centang manual oleh KFT bila kriteria terpenuhi pada konteks RS"),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cba_criteria_created",
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cba_criteria_edited",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["case", "order"]
        verbose_name = _("CBA Criterion")
        verbose_name_plural = _("CBA Criteria")

    def __str__(self) -> str:
        return f"{self.case.case_id} #{self.order}: {self.criterion_name}"


class TrafficLight(models.TextChoices):
    GREEN = "green", _("HIJAU — Adopsi tanpa syarat")
    YELLOW = "yellow", _("KUNING — Adopsi bersyarat (CBA)")
    RED = "red", _("MERAH — Tidak direkomendasikan")


class Recommendation(models.Model):
    """One immutable synthesis run."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="recommendations")
    input_snapshot = models.JSONField(
        help_text=_("CEA result, BIA result, EtD summary, weights, CBA criteria at compute time"),
    )

    # Sub-scores (0-100)
    evidence_strength_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ce_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    budget_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    cba_score = models.DecimalField(max_digits=6, decimal_places=2)

    # Composite (weighted)
    composite_score = models.DecimalField(max_digits=6, decimal_places=2)
    traffic_light = models.CharField(max_length=8, choices=TrafficLight.choices)

    justification_text = models.TextField(blank=True, default="")
    cba_criteria_count = models.PositiveSmallIntegerField(default=0)
    cba_satisfied_count = models.PositiveSmallIntegerField(default=0)
    algorithm_version = models.CharField(max_length=16, default="1.0.0")
    weight_aggregation_method = models.CharField(max_length=16, default="mean")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("Recommendation")
        verbose_name_plural = _("Recommendations")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} → {self.traffic_light} ({self.composite_score})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError(
                "Recommendation rows are immutable; re-compute to create a new row."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Recommendation rows are append-only and cannot be deleted.")
