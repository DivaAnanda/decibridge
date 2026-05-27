"""CEA (Cost-Effectiveness Analysis) data model.

Two tables:

- `CEAInput`: editable inputs per case (drug + comparator cost/efficacy,
  WTOP threshold). Exactly one input row per case (OneToOne). Edited by
  HTA Analyst / Sekretaris KFT while the case is editable.

- `CEAResult`: immutable snapshot of one computation. Each press of
  "Hitung CEA" creates a new row containing the input snapshot, computed
  ICER, dominance classification, and sensitivity bounds. Never updated;
  deletion is forbidden by the audit-log invariants of Sprint 1.

The math lives in `engine.py` as a pure function so it's trivially
testable without DB fixtures.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case


class EfficacyMetric(models.TextChoices):
    QALY = "qaly", _("QALY (Quality-Adjusted Life Year)")
    LYG = "lyg", _("LYG (Life Year Gained)")
    OTHER = "other", _("Other (specify in metric_label)")


class DataSource(models.TextChoices):
    LITERATURE = "literature", _("Literatur ilmiah")
    LOCAL = "local_data", _("Data lokal RS")
    EXPERT = "expert_opinion", _("Pendapat ahli")
    MIXED = "mixed", _("Campuran")


# 250 million IDR ≈ 1.5× Indonesian GDP per capita (2024) — a defensible default
# Indonesia HTA threshold. Configurable per case.
DEFAULT_WTOP_IDR = Decimal("250000000.00")


class CEAInput(models.Model):
    """Inputs to the ICER calculation. One per case."""

    case = models.OneToOneField(
        Case, on_delete=models.CASCADE, related_name="cea_input"
    )

    # ── Cost side (IDR) ──────────────────────────────────────────────────
    drug_cost_per_unit = models.DecimalField(
        _("Biaya intervensi per unit (IDR)"),
        max_digits=15,
        decimal_places=2,
        help_text=_("Biaya obat/teknologi yang dievaluasi per pasien per periode"),
    )
    comparator_cost_per_unit = models.DecimalField(
        _("Biaya komparator per unit (IDR)"),
        max_digits=15,
        decimal_places=2,
    )

    # ── Effectiveness side ───────────────────────────────────────────────
    efficacy_metric = models.CharField(
        max_length=16, choices=EfficacyMetric.choices, default=EfficacyMetric.QALY
    )
    metric_label = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text=_("Deskripsi metrik bila 'Other' dipilih"),
    )
    drug_efficacy_value = models.DecimalField(
        _("Nilai efikasi intervensi"),
        max_digits=10,
        decimal_places=4,
    )
    comparator_efficacy_value = models.DecimalField(
        _("Nilai efikasi komparator"),
        max_digits=10,
        decimal_places=4,
    )

    # ── Population & threshold ───────────────────────────────────────────
    patient_population_size = models.PositiveIntegerField(
        _("Estimasi populasi pasien"),
        help_text=_("Jumlah pasien yang akan diberikan intervensi per tahun"),
    )
    wtop_threshold = models.DecimalField(
        _("Ambang batas WTOP (IDR per unit efikasi)"),
        max_digits=15,
        decimal_places=2,
        default=DEFAULT_WTOP_IDR,
        help_text=_("Willingness-to-pay per QALY/LYG"),
    )

    # ── Provenance ───────────────────────────────────────────────────────
    data_source = models.CharField(
        max_length=24, choices=DataSource.choices, default=DataSource.LITERATURE
    )
    evidence_year = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cea_inputs_created",
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cea_inputs_edited",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("CEA Input")
        verbose_name_plural = _("CEA Inputs")

    def __str__(self) -> str:
        return f"CEA inputs for {self.case.case_id}"


class Dominance(models.TextChoices):
    COST_SAVING = "cost_saving", _("Cost-saving (dominant)")
    COST_EFFECTIVE_SAFE = "cost_effective_safe", _("Cost-effective (aman)")
    COST_EFFECTIVE_AT_THRESHOLD = "cost_effective_at_threshold", _("Cost-effective (di ambang)")
    COST_UNCERTAIN = "cost_uncertain", _("Tidak pasti")
    COST_INEFFECTIVE = "cost_ineffective", _("Cost-ineffective")
    DOMINATED = "dominated", _("Dominated (lebih mahal & kurang efektif)")
    FRONTIER_AMBIGUOUS = "frontier_ambiguous", _("Ambigu (efek nol)")


class CEAResult(models.Model):
    """One immutable computation result. Append-only.

    Sprint 1's audit invariants forbid deletion. Updates are also blocked
    in `save()`; re-computing creates a NEW row.
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="cea_results")

    # Snapshot of the inputs at compute time — survives later edits.
    input_snapshot = models.JSONField(help_text=_("CEAInput field values at compute time"))

    incremental_cost = models.DecimalField(max_digits=15, decimal_places=2)
    incremental_effect = models.DecimalField(max_digits=12, decimal_places=4)
    icer_value = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text=_("Null when incremental_effect is ~zero (frontier ambiguous)"),
    )
    wtop_threshold_used = models.DecimalField(max_digits=15, decimal_places=2)

    dominance = models.CharField(max_length=32, choices=Dominance.choices)
    ce_score = models.PositiveSmallIntegerField(
        help_text=_("0-100 contribution to the final traffic-light recommendation"),
    )

    sensitivity_low_icer = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text=_("ICER under 20% adverse variance (cost +20%, effect -20%)"),
    )
    sensitivity_high_icer = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text=_("ICER under 20% favourable variance (cost -20%, effect +20%)"),
    )
    threshold_sensitivity_flag = models.BooleanField(
        default=False,
        help_text=_("True when ICER lies within ±20% of WTOP — review carefully"),
    )

    interpretation_text = models.TextField(blank=True, default="")
    algorithm_version = models.CharField(max_length=16, default="1.0.0")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cea_results_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("CEA Result")
        verbose_name_plural = _("CEA Results")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        icer = f"{self.icer_value:,.0f} IDR" if self.icer_value is not None else "N/A"
        return f"{self.case.case_id} CEA #{self.pk} — ICER {icer} ({self.dominance})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("CEAResult rows are immutable; re-compute to create a new row.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("CEAResult rows are append-only and cannot be deleted.")
