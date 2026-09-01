"""Cost-offset Budget Impact Analysis engine (R4, aligned to the lecturer's model in V1).

Pure function. No Django imports, no DB access. Implements the cost-offset BIA
from `../Brief/DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx` sheet `03_BIA`:

    patients_intervention = eligible x uptake x market_share
    incremental_drug_cost = patients_intervention x (drug_cost_int - drug_cost_comp)
    event_cost_offset     = patients_intervention x (event_prob_comp - event_prob_int) x event_cost
    incremental_other     = patients_intervention x (other_cost_int - other_cost_comp)
    net_budget_impact     = incremental_drug_cost - event_cost_offset + incremental_other

**market_share defaults to 1.0.** The lecturer's model computes ARNI patients as
`eligible x uptake` alone — introducing a second multiplier is exactly the double
counting he flagged. The field is retained (default 1) so an institution that
genuinely splits treated patients between the two arms can still model it.

Two outputs:
  * `year_rows`   — per-year projection over the horizon (undiscounted, standard for BIA)
  * `scenario_rows` — one-year net impact per uptake scenario (his low/medium/high table)

Severity/budget-score classify cumulative net impact against one annual pharmacy
budget, mirroring the legacy bands so the traffic-light synthesis stays calibrated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

ALGORITHM_VERSION = "2.0.0"

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
NOT_ASSESSED = "not_assessed"


@dataclass(frozen=True)
class BIAAlternativeParams:
    drug_cost: Decimal
    event_probability: Decimal
    other_cost: Decimal = ZERO


@dataclass(frozen=True)
class BIAYearParams:
    year: int
    eligible_population: Decimal
    uptake: Decimal
    market_share: Decimal = ONE


@dataclass(frozen=True)
class BIAScenario:
    label: str
    uptake: Decimal


@dataclass(frozen=True)
class BIAInput:
    horizon_years: int
    annual_budget_baseline: Decimal | None
    event_cost: Decimal
    intervention: BIAAlternativeParams
    comparator: BIAAlternativeParams
    years: list[BIAYearParams]
    scenarios: list[BIAScenario] = field(default_factory=list)
    scenario_eligible_population: Decimal = ZERO
    scenario_market_share: Decimal = ONE


@dataclass(frozen=True)
class BIAComponents:
    """The four cost-offset components for one patient cohort."""

    patients_intervention: Decimal
    incremental_drug_cost: Decimal
    event_cost_offset: Decimal
    incremental_other: Decimal
    net_budget_impact: Decimal


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
class BIAScenarioResult:
    label: str
    uptake: Decimal
    eligible_population: Decimal
    patients_intervention: Decimal
    incremental_drug_cost: Decimal
    event_cost_offset: Decimal
    net_budget_impact: Decimal


@dataclass(frozen=True)
class BIAResult:
    year_rows: list[BIAYearResult]
    scenario_rows: list[BIAScenarioResult]
    cumulative_net_impact: Decimal
    pct_of_total_baseline: Decimal
    severity: str
    budget_score: int | None
    interpretation_text: str
    algorithm_version: str = ALGORITHM_VERSION


def _components(
    patients_int: Decimal,
    iv: BIAAlternativeParams,
    comp: BIAAlternativeParams,
    event_cost: Decimal,
) -> BIAComponents:
    incremental_drug = patients_int * (iv.drug_cost - comp.drug_cost)
    offset = patients_int * (comp.event_probability - iv.event_probability) * event_cost
    incremental_other = patients_int * (iv.other_cost - comp.other_cost)
    return BIAComponents(
        patients_intervention=patients_int,
        incremental_drug_cost=incremental_drug,
        event_cost_offset=offset,
        incremental_other=incremental_other,
        net_budget_impact=incremental_drug - offset + incremental_other,
    )


def compute_bia(inp: BIAInput) -> BIAResult:
    iv, comp = inp.intervention, inp.comparator

    rows: list[BIAYearResult] = []
    cumulative = ZERO
    for yp in inp.years:
        patients_int = yp.eligible_population * yp.uptake * yp.market_share
        patients_comp = yp.eligible_population * yp.uptake * (ONE - yp.market_share)
        c = _components(patients_int, iv, comp, inp.event_cost)
        cumulative += c.net_budget_impact

        pct = (
            (c.net_budget_impact / inp.annual_budget_baseline * Decimal("100"))
            if inp.annual_budget_baseline and inp.annual_budget_baseline > 0
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
                incremental_drug_cost=c.incremental_drug_cost,
                event_cost_offset=c.event_cost_offset,
                incremental_other=c.incremental_other,
                net_budget_impact=c.net_budget_impact,
                cumulative_net_impact=cumulative,
                pct_of_annual_baseline=pct,
            )
        )

    # One-year scenario table (low / medium / high uptake).
    scenario_rows: list[BIAScenarioResult] = []
    for s in inp.scenarios:
        patients_int = inp.scenario_eligible_population * s.uptake * inp.scenario_market_share
        c = _components(patients_int, iv, comp, inp.event_cost)
        scenario_rows.append(
            BIAScenarioResult(
                label=s.label,
                uptake=s.uptake,
                eligible_population=inp.scenario_eligible_population,
                patients_intervention=patients_int,
                incremental_drug_cost=c.incremental_drug_cost,
                event_cost_offset=c.event_cost_offset,
                net_budget_impact=c.net_budget_impact,
            )
        )

    baseline = inp.annual_budget_baseline
    pct_total = (
        (cumulative / (baseline * Decimal(inp.horizon_years)) * Decimal("100"))
        if baseline and baseline > 0
        else ZERO
    )
    severity, budget_score = _classify(cumulative, baseline)

    return BIAResult(
        year_rows=rows,
        scenario_rows=scenario_rows,
        cumulative_net_impact=cumulative,
        pct_of_total_baseline=pct_total,
        severity=severity,
        budget_score=budget_score,
        interpretation_text=_narrative(cumulative, severity, inp.horizon_years, baseline),
    )


def _classify(cumulative: Decimal, baseline: Decimal) -> tuple[str, int | None]:
    """Severity + 0-100 budget sub-score.

    Without an annual budget baseline the impact cannot be judged as a share of
    the budget, so severity is "not assessed" and the sub-score is None — never
    a fabricated value (Phase R3 missing-data rule).
    """
    if baseline is None or baseline <= ZERO:
        return NOT_ASSESSED, None
    if cumulative <= ZERO:
        return COST_SAVING, BUDGET_SCORE_COST_SAVING
    magnitude = abs(cumulative) / baseline
    if magnitude <= MANAGEABLE_FRACTION:
        return MANAGEABLE, BUDGET_SCORE_MANAGEABLE
    if magnitude <= SIGNIFICANT_FRACTION:
        return SIGNIFICANT, BUDGET_SCORE_SIGNIFICANT
    return PROHIBITIVE, BUDGET_SCORE_PROHIBITIVE


def _narrative(cumulative: Decimal, severity: str, horizon: int, baseline: Decimal | None) -> str:
    horizon_label = f"{horizon} tahun"
    if severity == NOT_ASSESSED:
        direction = "menambah beban" if cumulative > ZERO else "menghasilkan penghematan"
        return (
            f"Proyeksi {horizon_label} {direction} bersih {abs(cumulative):,.0f} IDR "
            "setelah cost offset. Persentase terhadap anggaran belum dinilai — "
            "anggaran tahunan baseline belum diisi."
        )
    if cumulative <= ZERO:
        return (
            f"Proyeksi {horizon_label} menghasilkan PENGHEMATAN bersih "
            f"{abs(cumulative):,.0f} IDR setelah cost offset kejadian. "
            "Mendukung adopsi dari sisi anggaran."
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
