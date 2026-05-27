"""Pure BIA computation engine.

No Django imports. No DB access. Trivially testable.

Per the brief's §5:
    YearN_NetImpact = N × Uptake_N × MarketShare_N × (UnitCost_Drug − UnitCost_Comparator)

For a 3-year horizon, Year-2 is linearly interpolated between Y1 and Y3.
Cumulative = sum of (Y1, Y2 if horizon=3, Y3 if horizon=3).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

ALGORITHM_VERSION = "1.0.0"

# Severity thresholds — fraction of one annual budget
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

DIRECTION_SAVINGS = "savings"
DIRECTION_MIXED = "mixed"
DIRECTION_COST_INCREASE = "cost_increase"


@dataclass(frozen=True)
class BIAComputationInput:
    eligible_population: int
    patient_uptake_year1: Decimal
    patient_uptake_year3: Decimal
    market_share_year1: Decimal
    market_share_year3: Decimal
    unit_cost_drug: Decimal
    unit_cost_comparator: Decimal
    budget_baseline: Decimal
    projection_horizon: int  # 1 or 3

    def snapshot(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in d.items()}


@dataclass(frozen=True)
class BIAComputationResult:
    year1_drug_cost: Decimal
    year1_comparator_cost_displaced: Decimal
    year1_net_impact: Decimal
    year2_net_impact_interpolated: Decimal | None
    year3_drug_cost: Decimal | None
    year3_comparator_cost_displaced: Decimal | None
    year3_net_impact: Decimal | None
    cumulative_impact: Decimal
    pct_of_annual_budget: Decimal
    severity: str
    direction: str
    budget_score: int
    interpretation_text: str
    algorithm_version: str = ALGORITHM_VERSION


def _per_year_impact(
    n: int, uptake: Decimal, market_share: Decimal, unit_drug: Decimal, unit_comparator: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (drug_cost, comparator_displaced, net_impact) for one projection year."""
    treated_on_drug = Decimal(n) * uptake * market_share
    drug_cost = (treated_on_drug * unit_drug).quantize(Decimal("0.01"))
    comparator_displaced = (treated_on_drug * unit_comparator).quantize(Decimal("0.01"))
    net = (drug_cost - comparator_displaced).quantize(Decimal("0.01"))
    return drug_cost, comparator_displaced, net


def compute_bia(inp: BIAComputationInput) -> BIAComputationResult:
    y1_drug, y1_comp, y1_net = _per_year_impact(
        inp.eligible_population,
        inp.patient_uptake_year1,
        inp.market_share_year1,
        inp.unit_cost_drug,
        inp.unit_cost_comparator,
    )

    y2_net: Decimal | None = None
    y3_drug: Decimal | None = None
    y3_comp: Decimal | None = None
    y3_net: Decimal | None = None

    if inp.projection_horizon == 3:
        y3_drug, y3_comp, y3_net = _per_year_impact(
            inp.eligible_population,
            inp.patient_uptake_year3,
            inp.market_share_year3,
            inp.unit_cost_drug,
            inp.unit_cost_comparator,
        )
        y2_net = ((y1_net + y3_net) / Decimal("2")).quantize(Decimal("0.01"))
        cumulative = (y1_net + y2_net + y3_net).quantize(Decimal("0.01"))
        budget_window = inp.budget_baseline * Decimal("3")
    else:
        cumulative = y1_net
        budget_window = inp.budget_baseline

    pct_of_budget = (cumulative / budget_window * Decimal("100")).quantize(Decimal("0.0001"))

    # ── Direction ────────────────────────────────────────────────────────
    if y1_net <= 0 and (y3_net is None or y3_net <= 0):
        direction = DIRECTION_SAVINGS
    elif y1_net >= 0 and (y3_net is None or y3_net >= 0):
        direction = DIRECTION_COST_INCREASE
    else:
        direction = DIRECTION_MIXED

    # ── Severity (based on |cumulative| vs annual baseline) ──────────────
    magnitude_vs_annual = abs(cumulative) / inp.budget_baseline if inp.budget_baseline > 0 else Decimal("0")

    if cumulative <= 0:
        severity = COST_SAVING
        budget_score = BUDGET_SCORE_COST_SAVING
    elif magnitude_vs_annual <= MANAGEABLE_FRACTION:
        severity = MANAGEABLE
        budget_score = BUDGET_SCORE_MANAGEABLE
    elif magnitude_vs_annual <= SIGNIFICANT_FRACTION:
        severity = SIGNIFICANT
        budget_score = BUDGET_SCORE_SIGNIFICANT
    else:
        severity = PROHIBITIVE
        budget_score = BUDGET_SCORE_PROHIBITIVE

    narrative = _build_narrative(
        cumulative=cumulative,
        pct=pct_of_budget,
        direction=direction,
        severity=severity,
        horizon=inp.projection_horizon,
        budget_baseline=inp.budget_baseline,
    )

    return BIAComputationResult(
        year1_drug_cost=y1_drug,
        year1_comparator_cost_displaced=y1_comp,
        year1_net_impact=y1_net,
        year2_net_impact_interpolated=y2_net,
        year3_drug_cost=y3_drug,
        year3_comparator_cost_displaced=y3_comp,
        year3_net_impact=y3_net,
        cumulative_impact=cumulative,
        pct_of_annual_budget=pct_of_budget,
        severity=severity,
        direction=direction,
        budget_score=budget_score,
        interpretation_text=narrative,
    )


def _build_narrative(
    *,
    cumulative: Decimal,
    pct: Decimal,
    direction: str,
    severity: str,
    horizon: int,
    budget_baseline: Decimal,
) -> str:
    horizon_label = "1 tahun" if horizon == 1 else "3 tahun"
    direction_label = {
        DIRECTION_SAVINGS: "menghasilkan penghematan",
        DIRECTION_COST_INCREASE: "menambah beban biaya",
        DIRECTION_MIXED: "memberi dampak campuran (penghematan dan biaya tambahan)",
    }[direction]

    abs_amount = abs(cumulative)
    abs_pct = abs(pct)

    severity_phrase = {
        COST_SAVING: "Penghematan bersih — rekomendasi mendukung adopsi dari sisi anggaran.",
        MANAGEABLE: f"Dampak kumulatif {abs_pct}% dari anggaran tahunan ({budget_baseline:,.0f} IDR) — masih dapat dikelola dalam anggaran rutin.",
        SIGNIFICANT: f"Dampak kumulatif {abs_pct}% — signifikan, perlu perencanaan ulang anggaran atau realokasi.",
        PROHIBITIVE: f"Dampak kumulatif {abs_pct}% — melebihi 50% anggaran tahunan. Memerlukan persetujuan tambahan dan kemungkinan kebijakan CBA ketat.",
    }[severity]

    return (
        f"Proyeksi {horizon_label} {direction_label} sebesar "
        f"{abs_amount:,.0f} IDR kumulatif. {severity_phrase}"
    )
