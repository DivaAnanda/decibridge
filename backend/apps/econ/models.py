"""High-precision, fully-editable economic model for HTA cost-utility analysis.

Introduced in the post-demo revision (see `docs/revision-plan.md`, Phase R1) in
response to the lecturer's feedback that the "CEA Quick" MVP lacked:

  * numeric precision (costs were `DECIMAL(15,2)`, QALY `DECIMAL(10,4)`);
  * a parameterised economic model (only totals were captured, not the drug
    cost / event probability / utility / disutility / discount inputs behind them);
  * per-parameter provenance metadata (source, year, observed/proxy/assumption).

This app is **additive** — the legacy `apps/cea` "Quick" path is untouched so the
existing demo/archive cases keep working. The new deterministic + probabilistic
engines (Phases R2, R5) read from these tables.

Two tables:

  * `EconomicModel`  — one per case. Structural scalars shared by both
    alternatives: analysis horizon, cost/outcome discount rates, WTP threshold.
  * `EconomicParameter` — the editable parameter registry. One row per
    (key, alternative, year). Carries full provenance metadata and a change
    counter. **Mutable by design** — the lecturer requires every parameter to be
    editable and never hardcoded. Every edit is audited (AuditLog + django-simple-history).

Precision policy (lecturer requirement): store at full precision, never round in
the calculation layer. Rounding happens only at the presentation layer.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case

# ── Precision constants ─────────────────────────────────────────────────────
# Cost fields: DECIMAL(20,4) per the lecturer's spec.
COST_MAX_DIGITS = 20
COST_DECIMAL_PLACES = 4
# Probability / utility / QALY: DECIMAL(18,10) per the spec.
RATE_MAX_DIGITS = 18
RATE_DECIMAL_PLACES = 10
# Parameter registry stores heterogeneous values (costs AND probabilities) in one
# column, so it needs the union of both: 18 integer digits + 10 fractional.
VALUE_MAX_DIGITS = 28
VALUE_DECIMAL_PLACES = 10

# WTP for the lecturer's validation case (HF_ARNI_ACEI_001). Editable per case.
DEFAULT_WTP_IDR = Decimal("85000000.0000")


class Alternative(models.TextChoices):
    INTERVENTION = "intervention", _("Intervensi")
    COMPARATOR = "comparator", _("Komparator")
    SHARED = "shared", _("Bersama (kedua alternatif)")


class ParamType(models.TextChoices):
    """Drives presentation-layer rounding and range validation."""

    COST = "cost", _("Biaya")
    PROBABILITY = "probability", _("Probabilitas")
    UTILITY = "utility", _("Utility")
    DISUTILITY = "disutility", _("Disutility")
    RATE = "rate", _("Rasio / tingkat")
    COUNT = "count", _("Jumlah")


class DataStatus(models.TextChoices):
    OBSERVED = "observed", _("Observed (data teramati)")
    PROXY = "proxy", _("Proxy (pendekatan)")
    ASSUMPTION = "assumption", _("Assumption (asumsi ilustratif)")


class Distribution(models.TextChoices):
    """PSA uncertainty distribution for a parameter.

    Two generic params (dist_param1, dist_param2) are interpreted per distribution:
      * FIXED     — held at `value`, not sampled.
      * BETA      — param1 = alpha, param2 = beta   (probabilities / utilities, [0,1]).
      * GAMMA     — param1 = shape, param2 = scale  (costs, >= 0).
      * LOGNORMAL — param1 = mean,  param2 = SE     (costs, >= 0; converted to log-space).
      * NORMAL    — param1 = mean,  param2 = SD.
    """

    FIXED = "fixed", _("Tetap (tidak disampel)")
    BETA = "beta", _("Beta (probabilitas/utility)")
    GAMMA = "gamma", _("Gamma (biaya)")
    LOGNORMAL = "lognormal", _("Log-normal (biaya)")
    NORMAL = "normal", _("Normal")


class ParamKey(models.TextChoices):
    """Canonical parameter vocabulary the engines read by key.

    Values are stable identifiers; labels are the default Indonesian display
    names (a user may override the per-row `label`).
    """

    DRUG_COST = "drug_cost", _("Biaya obat per pasien per tahun")
    EVENT_PROBABILITY = "event_probability", _("Probabilitas kejadian / rehospitalisasi")
    EVENT_COST = "event_cost", _("Biaya per kejadian / rawat inap")
    OTHER_COST = "other_cost", _("Biaya tambahan lain per pasien per tahun")
    BASELINE_UTILITY = "baseline_utility", _("Utility dasar")
    EVENT_DISUTILITY = "event_disutility", _("Disutility kejadian")
    ELIGIBLE_POPULATION = "eligible_population", _("Jumlah populasi eligible")
    UPTAKE = "uptake", _("Uptake (proporsi eligible yang diobati)")
    # Optional. The lecturer's validation model uses uptake ALONE
    # (patients = eligible x uptake); this defaults to 1.0 when absent so the
    # two multipliers never double-count.
    MARKET_SHARE = "market_share", _("Market share (opsional; default 1,0)")
    UPTAKE_LOW = "uptake_low", _("Uptake skenario rendah")
    UPTAKE_MEDIUM = "uptake_medium", _("Uptake skenario menengah")
    UPTAKE_HIGH = "uptake_high", _("Uptake skenario tinggi")
    MEDIAN_LOS = "median_los", _("Median length of stay (hari/admisi)")


# Parameter types that must stay within [0, 1].
_UNIT_INTERVAL_TYPES = {ParamType.PROBABILITY, ParamType.UTILITY, ParamType.DISUTILITY}


class EconomicModel(models.Model):
    """Structural scalars for one case's cost-utility analysis. One per case."""

    case = models.OneToOneField(
        Case, on_delete=models.CASCADE, related_name="economic_model"
    )

    horizon_years = models.PositiveSmallIntegerField(
        _("Horizon analisis (tahun)"),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Jumlah tahun proyeksi. Discounting memakai eksponen (t-1)."),
    )
    cost_discount_rate = models.DecimalField(
        _("Discount rate biaya"),
        max_digits=9,
        decimal_places=6,
        default=Decimal("0"),
        help_text=_("mis. 0.03 untuk 3% per tahun"),
    )
    outcome_discount_rate = models.DecimalField(
        _("Discount rate outcome/QALY"),
        max_digits=9,
        decimal_places=6,
        default=Decimal("0"),
        help_text=_("mis. 0.03 untuk 3% per tahun"),
    )
    wtp_threshold = models.DecimalField(
        _("WTP threshold (IDR per QALY)"),
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        default=DEFAULT_WTP_IDR,
    )
    annual_budget_baseline = models.DecimalField(
        _("Anggaran farmasi tahunan baseline (IDR)"),
        max_digits=COST_MAX_DIGITS,
        decimal_places=COST_DECIMAL_PLACES,
        null=True,
        blank=True,
        help_text=_("Dasar perhitungan % dampak anggaran (BIA)"),
    )

    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="economic_models_created",
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="economic_models_edited",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Economic Model")
        verbose_name_plural = _("Economic Models")

    def __str__(self) -> str:
        return f"Economic model for {self.case.case_id}"

    def value_of(
        self,
        key: str,
        alternative: str,
        year_index: int | None = None,
    ) -> Decimal | None:
        """Resolve one parameter value with sensible fallbacks.

        - If `year_index` is given, prefer the year-specific row, then a
          year-agnostic (null year_index) row.
        - Falls back from a specific alternative to a `shared` row.
        Returns None when nothing matches (caller decides how to treat missing).
        """
        candidates = list(
            self.parameters.filter(
                key=key, alternative__in=[alternative, Alternative.SHARED]
            )
        )
        if not candidates:
            return None

        def pick(alt: str) -> EconomicParameter | None:
            rows = [p for p in candidates if p.alternative == alt]
            if year_index is not None:
                exact = next((p for p in rows if p.year_index == year_index), None)
                if exact:
                    return exact
                return next((p for p in rows if p.year_index is None), None)
            agnostic = next((p for p in rows if p.year_index is None), None)
            return agnostic or (rows[0] if rows else None)

        return (
            param.value
            if (param := pick(alternative)) is not None
            else (shared.value if (shared := pick(Alternative.SHARED)) is not None else None)
        )


class EconomicParameter(models.Model):
    """One editable economic-model parameter with full provenance metadata.

    Mutable (parameters are meant to be edited), audited via AuditLog +
    HistoricalRecords. `version` is a human-facing change counter that
    auto-increments on every edit.
    """

    economic_model = models.ForeignKey(
        EconomicModel, on_delete=models.CASCADE, related_name="parameters"
    )

    key = models.CharField(
        _("Kunci parameter"),
        max_length=40,
        choices=ParamKey.choices,
        help_text=_("Identifier kanonik yang dibaca oleh engine"),
    )
    label = models.CharField(
        _("Nama parameter"),
        max_length=160,
        blank=True,
        default="",
        help_text=_("Nama tampilan; kosong = pakai label default dari key"),
    )
    alternative = models.CharField(
        max_length=16, choices=Alternative.choices, default=Alternative.SHARED
    )
    year_index = models.PositiveSmallIntegerField(
        _("Tahun ke-"),
        null=True,
        blank=True,
        help_text=_("Kosong = berlaku untuk semua tahun. Isi 1..horizon untuk nilai per-tahun."),
    )

    value = models.DecimalField(
        _("Nilai"),
        max_digits=VALUE_MAX_DIGITS,
        decimal_places=VALUE_DECIMAL_PLACES,
    )
    unit = models.CharField(_("Satuan"), max_length=40, blank=True, default="")
    param_type = models.CharField(
        _("Tipe"), max_length=16, choices=ParamType.choices, default=ParamType.COST
    )

    # ── Provenance metadata (lecturer requirement) ──────────────────────────
    data_status = models.CharField(
        _("Status data"),
        max_length=16,
        choices=DataStatus.choices,
        default=DataStatus.ASSUMPTION,
    )
    source_reference = models.TextField(_("Sumber data"), blank=True, default="")
    source_year = models.PositiveSmallIntegerField(
        _("Tahun sumber"), null=True, blank=True
    )
    notes = models.TextField(_("Catatan / asumsi"), blank=True, default="")

    # ── PSA uncertainty (Phase R5) ──────────────────────────────────────
    distribution = models.CharField(
        _("Distribusi PSA"),
        max_length=16,
        choices=Distribution.choices,
        default=Distribution.FIXED,
    )
    dist_param1 = models.DecimalField(
        _("Parameter distribusi 1"),
        max_digits=VALUE_MAX_DIGITS,
        decimal_places=VALUE_DECIMAL_PLACES,
        null=True,
        blank=True,
        help_text=_("alpha (beta) / shape (gamma) / mean (lognormal, normal)"),
    )
    dist_param2 = models.DecimalField(
        _("Parameter distribusi 2"),
        max_digits=VALUE_MAX_DIGITS,
        decimal_places=VALUE_DECIMAL_PLACES,
        null=True,
        blank=True,
        help_text=_("beta (beta) / scale (gamma) / SE (lognormal, normal)"),
    )

    version = models.PositiveIntegerField(
        _("Versi"), default=1, help_text=_("Naik otomatis setiap kali nilai diedit")
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="econ_params_created",
    )
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="econ_params_edited",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Economic Parameter")
        verbose_name_plural = _("Economic Parameters")
        ordering = ["key", "alternative", "year_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["economic_model", "key", "alternative", "year_index"],
                name="uniq_econ_param_key_alt_year",
                # Treat two year-agnostic rows (year_index IS NULL) as duplicates.
                # Without this, Postgres considers NULLs distinct and lets them
                # both through (Django 5.0+/Postgres 15+ feature).
                nulls_distinct=False,
            )
        ]

    def __str__(self) -> str:
        yr = f" y{self.year_index}" if self.year_index is not None else ""
        return f"{self.economic_model.case.case_id}:{self.key}:{self.alternative}{yr} = {self.value}"

    @property
    def display_label(self) -> str:
        return self.label or ParamKey(self.key).label

    def clean(self) -> None:
        super().clean()
        if self.param_type in _UNIT_INTERVAL_TYPES and self.value is not None:
            if not (Decimal("0") <= self.value <= Decimal("1")):
                raise ValidationError(
                    {"value": _("Probabilitas/utility harus berada pada rentang 0–1.")}
                )
        if self.param_type == ParamType.COST and self.value is not None and self.value < 0:
            raise ValidationError({"value": _("Biaya tidak boleh negatif.")})

    def save(self, *args, **kwargs):
        # Auto-increment the human-facing change counter on every edit.
        if self.pk is not None:
            self.version = (self.version or 0) + 1
        super().save(*args, **kwargs)


class EconDeterministicResult(models.Model):
    """One immutable deterministic cost-utility computation. Append-only.

    Each press of "Hitung" creates a new row with the resolved input snapshot
    and every computed output at full precision (rounding happens only in the
    presentation layer). Never updated; deletion forbidden (audit invariant).
    """

    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="econ_deterministic_results"
    )
    input_snapshot = models.JSONField(help_text=_("Resolved engine inputs at compute time"))

    # ── Totals per alternative ───────────────────────────────────────────
    total_cost_intervention = models.DecimalField(max_digits=30, decimal_places=10)
    total_cost_comparator = models.DecimalField(max_digits=30, decimal_places=10)
    total_qaly_intervention = models.DecimalField(max_digits=RATE_MAX_DIGITS, decimal_places=RATE_DECIMAL_PLACES)
    total_qaly_comparator = models.DecimalField(max_digits=RATE_MAX_DIGITS, decimal_places=RATE_DECIMAL_PLACES)

    # ── Deterministic CEA outputs ────────────────────────────────────────
    incremental_cost = models.DecimalField(max_digits=30, decimal_places=10)
    incremental_qaly = models.DecimalField(max_digits=RATE_MAX_DIGITS, decimal_places=RATE_DECIMAL_PLACES)
    icer = models.DecimalField(
        max_digits=30, decimal_places=10, null=True, blank=True,
        help_text=_("Null when incremental QALY is zero (N/A, no division)"),
    )
    nmb_intervention = models.DecimalField(max_digits=30, decimal_places=10)
    nmb_comparator = models.DecimalField(max_digits=30, decimal_places=10)
    inb = models.DecimalField(max_digits=30, decimal_places=10)
    wtp_threshold_used = models.DecimalField(max_digits=COST_MAX_DIGITS, decimal_places=COST_DECIMAL_PLACES)

    decision_code = models.CharField(max_length=24)
    is_cost_effective = models.BooleanField()
    is_dominant = models.BooleanField()
    is_dominated = models.BooleanField()

    # Per-year breakdown + cost breakdown for the UI (before/after discounting).
    per_year = models.JSONField(default=dict)
    cost_breakdown = models.JSONField(default=dict)
    # Secondary clinical validation metrics (ARR, RR, RRR, NNT, LOS diff).
    clinical = models.JSONField(default=dict, blank=True)

    interpretation_text = models.TextField(blank=True, default="")
    algorithm_version = models.CharField(max_length=16, default="2.0.0")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="econ_results_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("Deterministic Result")
        verbose_name_plural = _("Deterministic Results")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        icer = "N/A" if self.icer is None else f"{self.icer:,.0f}"
        return f"{self.case.case_id} deterministic #{self.pk} — ICER {icer} ({self.decision_code})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("EconDeterministicResult rows are immutable; re-compute to create a new row.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("EconDeterministicResult rows are append-only and cannot be deleted.")


class EconBIAResult(models.Model):
    """One immutable cost-offset Budget Impact Analysis run. Append-only."""

    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="econ_bia_results"
    )
    input_snapshot = models.JSONField(help_text=_("Resolved BIA inputs at compute time"))

    cumulative_net_impact = models.DecimalField(max_digits=30, decimal_places=10)
    pct_of_total_baseline = models.DecimalField(max_digits=12, decimal_places=4)
    annual_budget_baseline = models.DecimalField(
        max_digits=COST_MAX_DIGITS, decimal_places=COST_DECIMAL_PLACES, null=True, blank=True
    )
    severity = models.CharField(max_length=16)
    # Null = "not assessed" (no annual budget baseline supplied). Never 0 — a
    # missing component must not be scored (Phase R3 missing-data rule).
    budget_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text=_("0-100 contribution to the traffic-light synthesis (20% weight)"),
    )

    # Per-year breakdown (eligible, uptake, patients, incremental drug cost,
    # event cost offset, net impact, cumulative, % baseline).
    per_year = models.JSONField(default=list)
    # One-year uptake scenarios (low / medium / high) — workbook sheet 03_BIA.
    scenarios = models.JSONField(default=list, blank=True)

    interpretation_text = models.TextField(blank=True, default="")
    algorithm_version = models.CharField(max_length=16, default="1.0.0")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="econ_bia_results_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("BIA Result (econ)")
        verbose_name_plural = _("BIA Results (econ)")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} BIA #{self.pk} — {self.cumulative_net_impact:,.0f} ({self.severity})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("EconBIAResult rows are immutable; re-compute to create a new row.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("EconBIAResult rows are append-only and cannot be deleted.")


class EconPSAResult(models.Model):
    """One immutable Probabilistic Sensitivity Analysis run. Append-only.

    Stores the run config (n simulations, seed), the CEAC curve, the CE-plane
    scatter cloud, and summary statistics. Reproducible: same seed + same
    parameters → identical output.
    """

    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="econ_psa_results"
    )
    input_snapshot = models.JSONField(help_text=_("Run config + resolved base params"))

    n_simulations = models.PositiveIntegerField()
    random_seed = models.BigIntegerField()
    wtp_base = models.DecimalField(max_digits=COST_MAX_DIGITS, decimal_places=COST_DECIMAL_PLACES)

    prob_cost_effective_base = models.DecimalField(max_digits=6, decimal_places=4)
    mean_incremental_cost = models.DecimalField(max_digits=30, decimal_places=10)
    mean_incremental_qaly = models.DecimalField(max_digits=RATE_MAX_DIGITS, decimal_places=RATE_DECIMAL_PLACES)

    # CEAC curve: [{"wtp": "...", "prob": "..."}, ...]
    ceac = models.JSONField(default=list)
    # CE-plane scatter: [[inc_qaly, inc_cost], ...] (one per iteration)
    scatter = models.JSONField(default=list)
    # Deterministic base-case point plotted over the cloud.
    base_case_incremental_cost = models.DecimalField(max_digits=30, decimal_places=10)
    base_case_incremental_qaly = models.DecimalField(max_digits=RATE_MAX_DIGITS, decimal_places=RATE_DECIMAL_PLACES)

    interpretation_text = models.TextField(blank=True, default="")
    algorithm_version = models.CharField(max_length=16, default="1.0.0")

    computed_at = models.DateTimeField(default=timezone.now, editable=False)
    computed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="econ_psa_results_computed",
    )

    class Meta:
        ordering = ["-computed_at"]
        verbose_name = _("PSA Result")
        verbose_name_plural = _("PSA Results")
        indexes = [models.Index(fields=["case", "-computed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_id} PSA #{self.pk} — P(CE)={self.prob_cost_effective_base}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("EconPSAResult rows are immutable; re-compute to create a new row.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("EconPSAResult rows are append-only and cannot be deleted.")
