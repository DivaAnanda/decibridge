"""Pure ICER computation engine.

No Django imports. No DB access. Trivially testable.

Formula (per the brief's §5):
    ICER = (Cost_drug - Cost_comparator) / (Efficacy_drug - Efficacy_comparator)

Dominance classification (compared to local WTOP threshold):
    1. |incremental_effect| ≈ 0           → frontier_ambiguous
    2. cost decreases AND effect increases → cost_saving (strongly dominant)
    3. cost increases AND effect decreases → dominated (strongly bad)
    4. ICER ≤ 0.8 * WTOP                  → cost_effective_safe (CE_score 100)
    5. 0.8 * WTOP < ICER ≤ WTOP           → cost_effective_at_threshold (CE_score 80)
    6. WTOP < ICER ≤ 1.5 * WTOP           → cost_uncertain (CE_score 50)
    7. ICER > 1.5 * WTOP                  → cost_ineffective (CE_score 0)

Sensitivity (±20% variance per brief):
    low_icer  = (Δcost * 1.2) / (Δeffect * 0.8)   — adverse case
    high_icer = (Δcost * 0.8) / (Δeffect * 1.2)   — favourable case

A threshold-sensitivity flag fires when ICER sits within ±20% of WTOP —
the result is too close to the threshold to trust without further analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

ALGORITHM_VERSION = "1.0.0"

# Below this incremental-effect magnitude we treat the comparison as
# non-inferior on effect — ICER is undefined.
EFFECT_EPSILON = Decimal("0.0001")

# Score weights matching the brief's traffic-light synthesis.
CE_SCORE_SAFE = 100
CE_SCORE_AT_THRESHOLD = 80
CE_SCORE_UNCERTAIN = 50
CE_SCORE_INEFFECTIVE = 0

# Brief's recommended ±20% variance for one-way sensitivity analysis.
SENSITIVITY_FACTOR = Decimal("0.20")

THRESHOLD_BAND = Decimal("0.20")


# ── Dominance enum (string-typed to match the model choices) ─────────────
COST_SAVING = "cost_saving"
COST_EFFECTIVE_SAFE = "cost_effective_safe"
COST_EFFECTIVE_AT_THRESHOLD = "cost_effective_at_threshold"
COST_UNCERTAIN = "cost_uncertain"
COST_INEFFECTIVE = "cost_ineffective"
DOMINATED = "dominated"
FRONTIER_AMBIGUOUS = "frontier_ambiguous"


@dataclass(frozen=True)
class CEAComputationInput:
    drug_cost_per_unit: Decimal
    comparator_cost_per_unit: Decimal
    drug_efficacy_value: Decimal
    comparator_efficacy_value: Decimal
    wtop_threshold: Decimal
    efficacy_metric: str = "qaly"
    metric_label: str = ""

    def snapshot(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in d.items()}


@dataclass(frozen=True)
class CEAComputationResult:
    incremental_cost: Decimal
    incremental_effect: Decimal
    icer_value: Decimal | None
    wtop_threshold_used: Decimal
    dominance: str
    ce_score: int
    sensitivity_low_icer: Decimal | None
    sensitivity_high_icer: Decimal | None
    threshold_sensitivity_flag: bool
    interpretation_text: str
    algorithm_version: str = ALGORITHM_VERSION


def compute_cea(inp: CEAComputationInput) -> CEAComputationResult:
    incremental_cost = inp.drug_cost_per_unit - inp.comparator_cost_per_unit
    incremental_effect = inp.drug_efficacy_value - inp.comparator_efficacy_value
    wtop = inp.wtop_threshold

    if abs(incremental_effect) < EFFECT_EPSILON:
        return CEAComputationResult(
            incremental_cost=incremental_cost,
            incremental_effect=incremental_effect,
            icer_value=None,
            wtop_threshold_used=wtop,
            dominance=FRONTIER_AMBIGUOUS,
            ce_score=CE_SCORE_UNCERTAIN,
            sensitivity_low_icer=None,
            sensitivity_high_icer=None,
            threshold_sensitivity_flag=False,
            interpretation_text=(
                "Selisih efikasi mendekati nol — ICER tidak terdefinisi. "
                "Lakukan analisis non-inferiority atau cost-minimization."
            ),
        )

    icer = (incremental_cost / incremental_effect).quantize(Decimal("0.01"))

    # ── Strong-dominance cases ───────────────────────────────────────────
    if incremental_cost < 0 and incremental_effect > 0:
        return CEAComputationResult(
            incremental_cost=incremental_cost,
            incremental_effect=incremental_effect,
            icer_value=icer,
            wtop_threshold_used=wtop,
            dominance=COST_SAVING,
            ce_score=CE_SCORE_SAFE,
            sensitivity_low_icer=_sensitivity(incremental_cost, incremental_effect, adverse=True),
            sensitivity_high_icer=_sensitivity(incremental_cost, incremental_effect, adverse=False),
            threshold_sensitivity_flag=False,
            interpretation_text=(
                f"Intervensi lebih murah DAN lebih efektif daripada komparator. "
                f"Penghematan biaya {abs(incremental_cost):,.0f} IDR per pasien "
                f"dengan tambahan {incremental_effect:.3f} unit efikasi. "
                f"Rekomendasi kuat untuk adopsi."
            ),
        )

    if incremental_cost > 0 and incremental_effect < 0:
        return CEAComputationResult(
            incremental_cost=incremental_cost,
            incremental_effect=incremental_effect,
            icer_value=icer,  # positive number, but conceptually 'cost per unit effect lost'
            wtop_threshold_used=wtop,
            dominance=DOMINATED,
            ce_score=CE_SCORE_INEFFECTIVE,
            sensitivity_low_icer=None,
            sensitivity_high_icer=None,
            threshold_sensitivity_flag=False,
            interpretation_text=(
                f"Intervensi lebih MAHAL DAN kurang efektif daripada komparator. "
                f"Dominated — rekomendasikan untuk TIDAK diadopsi."
            ),
        )

    # ── Both cost & effect move same direction → standard ICER ───────────
    # (icer is positive in this branch — either both incremental terms positive
    # or both negative)
    threshold_band_low = wtop * (Decimal("1") - THRESHOLD_BAND)
    threshold_band_high = wtop * (Decimal("1") + THRESHOLD_BAND)
    in_threshold_band = threshold_band_low <= icer <= threshold_band_high

    if icer <= (Decimal("0.8") * wtop):
        dominance = COST_EFFECTIVE_SAFE
        ce_score = CE_SCORE_SAFE
        narrative = (
            f"ICER {icer:,.0f} IDR/unit jauh di bawah ambang WTOP {wtop:,.0f} IDR. "
            "Cost-effective dengan margin aman."
        )
    elif icer <= wtop:
        dominance = COST_EFFECTIVE_AT_THRESHOLD
        ce_score = CE_SCORE_AT_THRESHOLD
        narrative = (
            f"ICER {icer:,.0f} IDR/unit berada di antara 80%–100% ambang WTOP. "
            "Cost-effective di ambang batas — pertimbangkan keterbatasan anggaran."
        )
    elif icer <= (Decimal("1.5") * wtop):
        dominance = COST_UNCERTAIN
        ce_score = CE_SCORE_UNCERTAIN
        narrative = (
            f"ICER {icer:,.0f} IDR/unit melebihi ambang WTOP ({wtop:,.0f}) hingga 1.5×. "
            "Tidak pasti — perlu pertimbangan domain lain (EtD, ekuitas, kebutuhan klinis)."
        )
    else:
        dominance = COST_INEFFECTIVE
        ce_score = CE_SCORE_INEFFECTIVE
        narrative = (
            f"ICER {icer:,.0f} IDR/unit jauh melebihi ambang WTOP {wtop:,.0f} IDR. "
            "Cost-ineffective pada konteks lokal."
        )

    return CEAComputationResult(
        incremental_cost=incremental_cost,
        incremental_effect=incremental_effect,
        icer_value=icer,
        wtop_threshold_used=wtop,
        dominance=dominance,
        ce_score=ce_score,
        sensitivity_low_icer=_sensitivity(incremental_cost, incremental_effect, adverse=True),
        sensitivity_high_icer=_sensitivity(incremental_cost, incremental_effect, adverse=False),
        threshold_sensitivity_flag=in_threshold_band,
        interpretation_text=narrative,
    )


def _sensitivity(
    incremental_cost: Decimal, incremental_effect: Decimal, *, adverse: bool
) -> Decimal | None:
    """One-way sensitivity: shift cost and effect ±20% in the adverse or favourable direction."""
    cost_factor = Decimal("1") + SENSITIVITY_FACTOR if adverse else Decimal("1") - SENSITIVITY_FACTOR
    effect_factor = Decimal("1") - SENSITIVITY_FACTOR if adverse else Decimal("1") + SENSITIVITY_FACTOR

    shifted_effect = incremental_effect * effect_factor
    if abs(shifted_effect) < EFFECT_EPSILON:
        return None
    return ((incremental_cost * cost_factor) / shifted_effect).quantize(Decimal("0.01"))
