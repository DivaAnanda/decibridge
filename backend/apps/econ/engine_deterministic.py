"""Deterministic cost-utility engine (Phase R2).

Pure function. No Django imports, no DB access — trivially testable and the
single source of truth for the deterministic HTA math the lecturer specified
in `../Brief/Hasil Checking DeciBridge.docx`.

Per alternative, per year t (1-indexed):
    annual_cost_t = drug_cost + (event_probability * event_cost) + other_cost
    disc_cost_t   = annual_cost_t / (1 + cost_discount_rate) ** (t - 1)
    total_cost    = Σ disc_cost_t

    annual_qaly_t = baseline_utility - (event_probability * event_disutility)
    disc_qaly_t   = annual_qaly_t / (1 + outcome_discount_rate) ** (t - 1)
    total_qaly    = Σ disc_qaly_t

Deterministic CEA:
    incremental_cost = total_cost_int - total_cost_comp
    incremental_qaly = total_qaly_int - total_qaly_comp
    ICER             = incremental_cost / incremental_qaly   (None if Δqaly == 0)
    NMB_x            = WTP * total_qaly_x - total_cost_x
    INB              = NMB_int - NMB_comp

Decision rules:
    INB > 0                          -> cost-effective at the chosen WTP
    INB <= 0                         -> not cost-effective
    Δcost < 0 and Δqaly > 0          -> dominant (cheaper AND more effective)
    Δcost > 0 and Δqaly < 0          -> dominated
    Δqaly == 0                       -> ICER = N/A (no division), decide on INB

CRITICAL: nothing is rounded here. Full `Decimal` precision is preserved through
every intermediate; the presentation layer rounds for display only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

ALGORITHM_VERSION = "2.0.0"

ZERO = Decimal("0")
ONE = Decimal("1")


# ── Decision codes ──────────────────────────────────────────────────────────
DOMINANT = "dominant"
DOMINATED = "dominated"
COST_EFFECTIVE = "cost_effective"
NOT_COST_EFFECTIVE = "not_cost_effective"


@dataclass(frozen=True)
class AlternativeInputs:
    """Constant annual clinical/economic inputs for one alternative.

    Values are treated as constant across the horizon; per-year variation is
    handled upstream by resolving year-specific parameters before building this.
    """

    drug_cost: Decimal
    event_probability: Decimal
    event_cost: Decimal
    other_cost: Decimal
    baseline_utility: Decimal
    event_disutility: Decimal
    # Secondary clinical validation field (workbook sheet 02_DETERMINISTIC).
    median_los: Decimal | None = None


@dataclass(frozen=True)
class ClinicalOutputs:
    """Secondary clinical validation metrics (workbook sheet 02_DETERMINISTIC).

        absolute_risk_reduction = p_comparator - p_intervention
        relative_risk           = p_intervention / p_comparator
        relative_risk_reduction = 1 - relative_risk
        nnt                     = 1 / absolute_risk_reduction
        admission_cost_saving   = absolute_risk_reduction x event_cost
        los_difference          = los_intervention - los_comparator
    """

    absolute_risk_reduction: Decimal
    relative_risk: Decimal | None
    relative_risk_reduction: Decimal | None
    nnt: Decimal | None
    admission_cost_saving_per_patient_year: Decimal
    los_difference: Decimal | None


@dataclass(frozen=True)
class DeterministicInput:
    horizon_years: int
    cost_discount_rate: Decimal
    outcome_discount_rate: Decimal
    wtp_threshold: Decimal
    intervention: AlternativeInputs
    comparator: AlternativeInputs

    def snapshot(self) -> dict[str, Any]:
        def conv(v: Any) -> Any:
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, dict):
                return {k: conv(x) for k, x in v.items()}
            return v

        return {k: conv(v) for k, v in asdict(self).items()}


@dataclass(frozen=True)
class YearRow:
    year: int
    annual_cost: Decimal
    discounted_cost: Decimal
    annual_qaly: Decimal
    discounted_qaly: Decimal


@dataclass(frozen=True)
class AlternativeResult:
    total_cost: Decimal
    total_qaly: Decimal
    # Cost breakdown at the (undiscounted) annual level, summed across years.
    drug_cost_total: Decimal
    event_cost_total: Decimal
    other_cost_total: Decimal
    year_rows: list[YearRow] = field(default_factory=list)


@dataclass(frozen=True)
class DeterministicResult:
    intervention: AlternativeResult
    comparator: AlternativeResult
    incremental_cost: Decimal
    incremental_qaly: Decimal
    icer: Decimal | None
    nmb_intervention: Decimal
    nmb_comparator: Decimal
    inb: Decimal
    wtp_threshold: Decimal
    decision_code: str
    is_cost_effective: bool
    is_dominant: bool
    is_dominated: bool
    interpretation_text: str
    clinical: ClinicalOutputs | None = None
    algorithm_version: str = ALGORITHM_VERSION


def _compute_alternative(
    inp: AlternativeInputs, horizon: int, cost_rate: Decimal, outcome_rate: Decimal
) -> AlternativeResult:
    annual_cost = inp.drug_cost + (inp.event_probability * inp.event_cost) + inp.other_cost
    annual_qaly = inp.baseline_utility - (inp.event_probability * inp.event_disutility)

    total_cost = ZERO
    total_qaly = ZERO
    rows: list[YearRow] = []
    for t in range(1, horizon + 1):
        cost_divisor = (ONE + cost_rate) ** (t - 1)
        qaly_divisor = (ONE + outcome_rate) ** (t - 1)
        disc_cost = annual_cost / cost_divisor
        disc_qaly = annual_qaly / qaly_divisor
        total_cost += disc_cost
        total_qaly += disc_qaly
        rows.append(
            YearRow(
                year=t,
                annual_cost=annual_cost,
                discounted_cost=disc_cost,
                annual_qaly=annual_qaly,
                discounted_qaly=disc_qaly,
            )
        )

    # Undiscounted component totals for the cost breakdown display.
    n = Decimal(horizon)
    return AlternativeResult(
        total_cost=total_cost,
        total_qaly=total_qaly,
        drug_cost_total=inp.drug_cost * n,
        event_cost_total=inp.event_probability * inp.event_cost * n,
        other_cost_total=inp.other_cost * n,
        year_rows=rows,
    )


def compute_deterministic(inp: DeterministicInput) -> DeterministicResult:
    intervention = _compute_alternative(
        inp.intervention, inp.horizon_years, inp.cost_discount_rate, inp.outcome_discount_rate
    )
    comparator = _compute_alternative(
        inp.comparator, inp.horizon_years, inp.cost_discount_rate, inp.outcome_discount_rate
    )

    incremental_cost = intervention.total_cost - comparator.total_cost
    incremental_qaly = intervention.total_qaly - comparator.total_qaly

    icer = None if incremental_qaly == ZERO else incremental_cost / incremental_qaly

    nmb_int = inp.wtp_threshold * intervention.total_qaly - intervention.total_cost
    nmb_comp = inp.wtp_threshold * comparator.total_qaly - comparator.total_cost
    inb = nmb_int - nmb_comp

    is_dominant = incremental_cost < ZERO and incremental_qaly > ZERO
    is_dominated = incremental_cost > ZERO and incremental_qaly < ZERO
    is_cost_effective = inb > ZERO

    if is_dominant:
        decision_code = DOMINANT
    elif is_dominated:
        decision_code = DOMINATED
    elif is_cost_effective:
        decision_code = COST_EFFECTIVE
    else:
        decision_code = NOT_COST_EFFECTIVE

    return DeterministicResult(
        intervention=intervention,
        comparator=comparator,
        incremental_cost=incremental_cost,
        incremental_qaly=incremental_qaly,
        icer=icer,
        nmb_intervention=nmb_int,
        nmb_comparator=nmb_comp,
        inb=inb,
        wtp_threshold=inp.wtp_threshold,
        decision_code=decision_code,
        is_cost_effective=is_cost_effective,
        is_dominant=is_dominant,
        is_dominated=is_dominated,
        interpretation_text=_narrative(
            incremental_cost, incremental_qaly, icer, inb, inp.wtp_threshold, decision_code
        ),
        clinical=_clinical_outputs(inp.intervention, inp.comparator),
    )


def _clinical_outputs(iv: AlternativeInputs, comp: AlternativeInputs) -> ClinicalOutputs:
    arr = comp.event_probability - iv.event_probability
    rr = (iv.event_probability / comp.event_probability) if comp.event_probability != ZERO else None
    rrr = (ONE - rr) if rr is not None else None
    nnt = (ONE / arr) if arr != ZERO else None
    los_diff = (
        iv.median_los - comp.median_los
        if iv.median_los is not None and comp.median_los is not None
        else None
    )
    return ClinicalOutputs(
        absolute_risk_reduction=arr,
        relative_risk=rr,
        relative_risk_reduction=rrr,
        nnt=nnt,
        admission_cost_saving_per_patient_year=arr * comp.event_cost,
        los_difference=los_diff,
    )


def _narrative(
    inc_cost: Decimal,
    inc_qaly: Decimal,
    icer: Decimal | None,
    inb: Decimal,
    wtp: Decimal,
    decision: str,
) -> str:
    icer_txt = "N/A (selisih efektivitas nol)" if icer is None else f"{icer:,.2f} IDR/QALY"
    head = (
        f"Incremental cost {inc_cost:,.2f} IDR, incremental QALY {inc_qaly:.6f}, "
        f"ICER {icer_txt}. INB pada WTP {wtp:,.0f} IDR = {inb:,.2f} IDR."
    )
    tail = {
        DOMINANT: "Intervensi DOMINAN — lebih murah dan lebih efektif. Rekomendasi kuat untuk adopsi.",
        DOMINATED: "Intervensi DOMINATED — lebih mahal dan kurang efektif. Rekomendasikan untuk tidak diadopsi.",
        COST_EFFECTIVE: "INB > 0 → intervensi COST-EFFECTIVE pada WTP terpilih.",
        NOT_COST_EFFECTIVE: "INB ≤ 0 → intervensi TIDAK cost-effective pada WTP terpilih.",
    }[decision]
    return f"{head} {tail}"
