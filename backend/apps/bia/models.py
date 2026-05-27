"""BIA (Budget Impact Analysis) data model.

Same shape as the CEA app:

- BIAInput: editable inputs per case. One row per case (OneToOne).
- BIAResult: immutable snapshot of one computation. Append-only.

Math (per the brief's §5):
    YearN_NetImpact = N_patients × Uptake_N × MarketShare_N × (UnitCost_Drug − UnitCost_Comparator)

Year-2 is linearly interpolated between Year-1 and Year-3 when the
projection horizon is 3 years.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case


class ProjectionHorizon(models.IntegerChoices):
    ONE_YEAR = 1, _("1 tahun")
    THREE_YEAR = 3, _("3 tahun")


class BIAInput(models.Model):
    """Inputs to the budget-impact projection. One per case."""

    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="bia_input")

    # ── Population & adoption ────────────────────────────────────────────
    eligible_population = models.PositiveIntegerField(
        _("Estimasi populasi pasien yang memenuhi syarat"),
        help_text=_("Jumlah pasien per tahun yang berpotensi menerima intervensi"),
    )

    # Uptake = % of eligible population that uses the new intervention
    patient_uptake_year1 = models.DecimalField(
        _("Uptake tahun 1 (0-1)"),
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        help_text=_("Proporsi pasien yang menerima intervensi pada Tahun 1, contoh 0.30 untuk 30%"),
    )
    patient_uptake_year3 = models.DecimalField(
        _("Uptake tahun 3 (0-1)"),
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )

    # Market share = % of treated patients on the drug under evaluation
    # (as opposed to the comparator)
    market_share_year1 = models.DecimalField(
        _("Pangsa pasar tahun 1 (0-1)"),
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )
    market_share_year3 = models.DecimalField(
        _("Pangsa pasar tahun 3 (0-1)"),
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )

    # ── Costs (IDR) ──────────────────────────────────────────────────────
    unit_cost_drug = models.DecimalField(
        _("Biaya intervensi per pasien per tahun (IDR)"),
        max_digits=15,
        decimal_places=2,
    )
    unit_cost_comparator = models.DecimalField(
        _("Biaya komparator per pasien per tahun (IDR)"),
        max_digits=15,
        decimal_places=2,
    )

    # ── Budget context ───────────────────────────────────────────────────
    budget_baseline = models.DecimalField(
        _("Anggaran farmasi tahunan baseline (IDR)"),
        max_digits=18,
        decimal_places=2,
        help_text=_("Total anggaran obat RS per tahun — digunakan untuk hitung % dampak"),
    )
    projection_horizon = models.PositiveSmallIntegerField(
        _("Horison proyeksi (tahun)"),
        choices=ProjectionHorizon.choices,
        default=ProjectionHorizon.THREE_YEAR,
    )

    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bia_inputs_created",
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bia_inputs_edited",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("BIA Input")
        verbose_name_plural = _("BIA Inputs")

    def __str__(self) -> str:
        return f"BIA inputs for {self.case.case_id}"


class Severity(models.TextChoices):
    COST_SAVING = "cost_saving", _("Cost-saving (penghematan)")
    MANAGEABLE = "manageable", _("Manageable (<=10% anggaran)")
    SIGNIFICANT = "significant", _("Significant (10-50% anggaran)")
    PROHIBITIVE = "prohibitive", _("Prohibitive (>50% anggaran)")


class Direction(models.TextChoices):
    SAVINGS = "savings", _("Penghematan bersih")
    MIXED = "mixed", _("Campuran")
    COST_INCREASE = "cost_increase", _("Beban biaya tambahan")


class BIAResult(models.Model):
    """One immutable BIA computation. Append-only."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="bia_results")
    input_snapshot = models.JSONField(help_text=_("BIAInput field values at compute time"))

    # ── Per-year breakdown ───────────────────────────────────────────────
    year1_drug_cost = models.DecimalField(max_digits=18, decimal_places=2)
    year1_comparator_cost_displaced = models.DecimalField(max_digits=18, decimal_places=2)
    year1_net_impact = models.DecimalField(max_digits=18, decimal_places=2)

    year2_net_impact_interpolated = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )

    year3_drug_cost = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    year3_comparator_cost_displaced = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    year3_net_impact = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    cumulative_impact = models.DecimalField(max_digits=18, decimal_places=2)
    pct_of_annual_budget = models.DecimalField(
        max_digits=8, decimal_places=4,
        help_text=_("Cumulative impact divided by annual budget (×100 for percent)"),
    )

    # ── Classification ───────────────────────────────────────────────────
    severity = models.CharField(max_length=24, choices=Severity.choices)
    direction = models.CharField(max_length=24, choices=Direction.choices)
    budget_score = models.PositiveSmallIntegerField(
        help_text=_("0-100 contribution to traffic-light synthesis (20% weight)"),
    )
    interpretation_text = models.TextField(blank=True, default="")
    algorithm_version = models.CharField(max_length=16, default="1.0.0")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bia_results_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("BIA Result")
        verbose_name_plural = _("BIA Results")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} BIA #{self.pk} — {self.severity} ({self.direction})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("BIAResult rows are immutable; re-compute to create a new row.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("BIAResult rows are append-only and cannot be deleted.")
