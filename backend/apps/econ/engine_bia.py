"""Cost-offset Budget Impact Analysis engine (Phase R4).

Pure function. No Django imports, no DB access. Implements the lecturer's
cost-offset BIA (`../Brief/Hasil Checking DeciBridge.docx`, "Perbaiki metode BIA"):
the old BIA compared only drug totals; this adds the **event cost offset** so a
drug that prevents events (e.g. rehospitalisations) shows its budget savings.

Per year t (1-indexed), using shared scenario params (population/uptake/market share)
and per-alternative clinical/cost params resolved upstream:

    patients_intervention = eligible × uptake × market_share
    patients_comparator   = eligible × uptake × (1 − market_share)

    incremental_drug_cost = patients_intervention × (drug_cost_int − drug_cost_comp)
    event_cost_offset     = patients_intervention × (event_prob_comp − event_prob_int) × event_cost
    incremental_other     = patients_intervention × (other_cost_int − other_cost_comp)
    net_budget_impact     = incremental_drug_cost − event_cost_offset + incremental_other

`uptake` = proportion of the eligible population actually treated.
`market_share` = proportion of TREATED patients who receive the intervention
(vs the comparator). So `eligible × uptake × market_share` never double-counts.

BIA is undiscounted (standard). Severity/budget-score classify the cumulative net
impact against one annual pharmacy budget, mirroring the legacy bands so the
traffic-light synthesis stays calibrated.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

ALGORITHM_VERSION = "1.0.0"

ZERO = Decimal("0")
ONE = Decimal("1")

# Severity thresholds — fraction of one annual budget.
MANAGEABLE_FRACTION = Decimal("0.10")
SIGNIFICANT_FRACTION = Decimal("0.50")

BUDGET_SCORE_COST_SAVING = 100
BUDGET_SCORE_MANAGEABLE = 80
BUDGET_SCORE_SIGNIFICANT = 50
BUDGET_SCORE_PROHIBITIVE = 0

COST_SAVING = "cost_saving"
MANAGEABLE = "manageable"
SIGNIFICANT = "significant"
PROHIBITIVE = "prohibitive"


@dataclass(frozen=True)
class BIAAlternativeParams:
    drug_cost: Decimal
    event_probability: Decimal
    other_cost: Decimal


@dataclass(frozen=True)
class BIAYearParams:
    year: int
    eligible_population: Decimal
    uptake: Decimal
    market_share: Decimal


@dataclass(frozen=True)
class BIAInput:
    horizon_years: int
    annual_budget_baseline: Decimal
    event_cost: Decimal
    intervention: BIAAlternativeParams
    comparator: BIAAlternativeParams
    years: list[BIAYearParams]


@dataclass(frozen=True)
class BIAYearResult:
    year: int
    eligible_population: Decimal
    uptake: Decimal
    market_share: Decimal
    patients_intervention: Decimal
    patients_comparator: Decimal
    incremental_drug_cost: Decimal
    event_cost_offset: Decimal
    incremental_other: Decimal
    net_budget_impact: Decimal
    cumulative_net_impact: Decimal
    pct_of_annual_baseline: Decimal


@dataclass(frozen=True)
class BIAResult:
    year_rows: list[BIAYearResult]
    cumulative_net_impact: Decimal
    pct_of_total_baseline: Decimal
    severity: str
    budget_score: int
    interpretation_text: str
    algorithm_version: str = ALGORITHM_VERSION


def compute_bia(inp: BIAInput) -> BIAResult:
    iv, comp = inp.intervention, inp.comparator
    drug_delta = iv.drug_cost - comp.drug_cost
    prob_delta = comp.event_probability - iv.event_probability  # positive = fewer events
    other_delta = iv.other_cost - comp.other_cost

    rows: list[BIAYearResult] = []
    cumulative = ZERO
    for yp in inp.years:
        patients_int = yp.eligible_population * yp.uptake * yp.market_share
        patients_comp = yp.eligible_population * yp.uptake * (ONE - yp.market_share)

        incremental_drug = patients_int * drug_delta
        offset = patients_int * prob_delta * inp.event_cost
        incremental_other = patients_int * other_delta
        net = incremental_drug - offset + incremental_other
        cumulative += net

        pct = (
            (net / inp.annual_budget_baseline * Decimal("100"))
            if inp.annual_budget_baseline > 0
            else ZERO
        )
        rows.append(
            BIAYearResult(
                year=yp.year,
                eligible_population=yp.eligible_population,
                uptake=yp.uptake,
                market_share=yp.market_share,
                patients_intervention=patients_int,
                patients_comparator=patients_comp,
                incremental_drug_cost=incremental_drug,
                event_cost_offset=offset,
                incremental_other=incremental_other,
                net_budget_impact=net,
                cumulative_net_impact=cumulative,
                pct_of_annual_baseline=pct,
            )
        )

    baseline = inp.annual_budget_baseline
    pct_total = (
        (cumulative / (baseline * Decimal(inp.horizon_years)) * Decimal("100"))
        if baseline > 0
        else ZERO
    )
    severity, budget_score = _classify(cumulative, baseline)

    return BIAResult(
        year_rows=rows,
        cumulative_net_impact=cumulative,
        pct_of_total_baseline=pct_total,
        severity=severity,
        budget_score=budget_score,
        interpretation_text=_narrative(cumulative, severity, inp.horizon_years, baseline),
    )


def _classify(cumulative: Decimal, baseline: Decimal) -> tuple[str, int]:
    if cumulative <= ZERO:
        return COST_SAVING, BUDGET_SCORE_COST_SAVING
    magnitude = abs(cumulative) / baseline if baseline > 0 else ZERO
    if magnitude <= MANAGEABLE_FRACTION:
        return MANAGEABLE, BUDGET_SCORE_MANAGEABLE
    if magnitude <= SIGNIFICANT_FRACTION:
        return SIGNIFICANT, BUDGET_SCORE_SIGNIFICANT
    return PROHIBITIVE, BUDGET_SCORE_PROHIBITIVE


def _narrative(cumulative: Decimal, severity: str, horizon: int, baseline: Decimal) -> str:
    horizon_label = f"{horizon} tahun"
    if cumulative <= ZERO:
        return (
            f"Proyeksi {horizon_label} menghasilkan PENGHEMATAN bersih "
            f"{abs(cumulative):,.0f} IDR setelah cost offset kejadian. Mendukung adopsi dari sisi anggaran."
        )
    phrase = {
        MANAGEABLE: "masih dapat dikelola dalam anggaran rutin.",
        SIGNIFICANT: "signifikan — perlu perencanaan ulang atau realokasi anggaran.",
        PROHIBITIVE: "melebihi 50% anggaran tahunan — memerlukan persetujuan tambahan / CBA ketat.",
    }[severity]
    return (
        f"Proyeksi {horizon_label} menambah beban bersih {cumulative:,.0f} IDR "
        f"(setelah cost offset), {phrase}"
    )
