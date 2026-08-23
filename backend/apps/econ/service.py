"""Service layer: resolve stored parameters -> run the pure engine -> persist.

Keeps Django/ORM concerns out of `engine_deterministic.py`. Resolution uses
`EconomicModel.value_of` with alternative + shared fallback.

Missing-data policy for R2 is minimal: a missing mandatory parameter raises
`IncompleteModelError` listing the gaps. Phase R3 turns this into the richer
"Belum dapat dihitung" API state; the structured gap list is already produced
here so R3 can surface it directly.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model

from .engine_bia import (
    BIAAlternativeParams,
    BIAInput,
    BIAYearParams,
    compute_bia,
)
from .engine_deterministic import (
    AlternativeInputs,
    DeterministicInput,
    compute_deterministic,
)
from .models import (
    Alternative,
    EconBIAResult,
    EconDeterministicResult,
    EconomicModel,
    ParamKey,
)

User = get_user_model()

# Parameters required to run the deterministic engine, by alternative.
_REQUIRED_PER_ALTERNATIVE = [
    ParamKey.DRUG_COST,
    ParamKey.EVENT_PROBABILITY,
]
# Shared/either parameters (resolved with shared fallback).
_REQUIRED_SHARED = [
    ParamKey.EVENT_COST,
    ParamKey.BASELINE_UTILITY,
    ParamKey.EVENT_DISUTILITY,
]
# other_cost is optional; defaults to 0 when absent.


class IncompleteModelError(Exception):
    """Raised when mandatory parameters are missing. Carries the gap list."""

    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"Model ekonomi belum lengkap: {', '.join(missing)}")


def _resolve_alternative(model: EconomicModel, alt: str, missing: list[str]) -> AlternativeInputs:
    def need(key: str) -> Decimal:
        val = model.value_of(key, alt)
        if val is None:
            missing.append(f"{ParamKey(key).label} ({alt})")
            return Decimal("0")
        return val

    drug_cost = need(ParamKey.DRUG_COST)
    event_probability = need(ParamKey.EVENT_PROBABILITY)
    event_cost = need(ParamKey.EVENT_COST)
    baseline_utility = need(ParamKey.BASELINE_UTILITY)
    event_disutility = need(ParamKey.EVENT_DISUTILITY)
    other_cost = model.value_of(ParamKey.OTHER_COST, alt) or Decimal("0")

    return AlternativeInputs(
        drug_cost=drug_cost,
        event_probability=event_probability,
        event_cost=event_cost,
        other_cost=other_cost,
        baseline_utility=baseline_utility,
        event_disutility=event_disutility,
    )


def build_input(model: EconomicModel) -> DeterministicInput:
    """Resolve stored parameters into a pure engine input. Raises IncompleteModelError."""
    missing: list[str] = []
    intervention = _resolve_alternative(model, Alternative.INTERVENTION, missing)
    comparator = _resolve_alternative(model, Alternative.COMPARATOR, missing)
    if missing:
        raise IncompleteModelError(missing)

    return DeterministicInput(
        horizon_years=model.horizon_years,
        cost_discount_rate=model.cost_discount_rate,
        outcome_discount_rate=model.outcome_discount_rate,
        wtp_threshold=model.wtp_threshold,
        intervention=intervention,
        comparator=comparator,
    )


def _year_rows_json(rows) -> list[dict]:
    return [
        {
            "year": r.year,
            "annual_cost": str(r.annual_cost),
            "discounted_cost": str(r.discounted_cost),
            "annual_qaly": str(r.annual_qaly),
            "discounted_qaly": str(r.discounted_qaly),
        }
        for r in rows
    ]


def run_deterministic(model: EconomicModel, computed_by: User | None = None) -> EconDeterministicResult:
    """Resolve -> compute -> persist an append-only deterministic result."""
    engine_input = build_input(model)
    result = compute_deterministic(engine_input)

    return EconDeterministicResult.objects.create(
        case=model.case,
        input_snapshot=engine_input.snapshot(),
        total_cost_intervention=result.intervention.total_cost,
        total_cost_comparator=result.comparator.total_cost,
        total_qaly_intervention=result.intervention.total_qaly,
        total_qaly_comparator=result.comparator.total_qaly,
        incremental_cost=result.incremental_cost,
        incremental_qaly=result.incremental_qaly,
        icer=result.icer,
        nmb_intervention=result.nmb_intervention,
        nmb_comparator=result.nmb_comparator,
        inb=result.inb,
        wtp_threshold_used=result.wtp_threshold,
        decision_code=result.decision_code,
        is_cost_effective=result.is_cost_effective,
        is_dominant=result.is_dominant,
        is_dominated=result.is_dominated,
        per_year={
            "intervention": _year_rows_json(result.intervention.year_rows),
            "comparator": _year_rows_json(result.comparator.year_rows),
        },
        cost_breakdown={
            "intervention": {
                "drug": str(result.intervention.drug_cost_total),
                "event": str(result.intervention.event_cost_total),
                "other": str(result.intervention.other_cost_total),
            },
            "comparator": {
                "drug": str(result.comparator.drug_cost_total),
                "event": str(result.comparator.event_cost_total),
                "other": str(result.comparator.other_cost_total),
            },
        },
        interpretation_text=result.interpretation_text,
        algorithm_version=result.algorithm_version,
        computed_by=computed_by,
    )


# ── Budget Impact Analysis (R4) ─────────────────────────────────────────────

# Shared scenario parameters required by the cost-offset BIA, resolved per year.
_BIA_SCENARIO_KEYS = [
    ParamKey.ELIGIBLE_POPULATION,
    ParamKey.UPTAKE,
    ParamKey.MARKET_SHARE,
]


def _bia_alternative(model: EconomicModel, alt: str, missing: list[str]) -> BIAAlternativeParams:
    def need(key: str) -> Decimal:
        val = model.value_of(key, alt)
        if val is None:
            missing.append(f"{ParamKey(key).label} ({alt})")
            return Decimal("0")
        return val

    drug_cost = need(ParamKey.DRUG_COST)
    event_probability = need(ParamKey.EVENT_PROBABILITY)
    other_cost = model.value_of(ParamKey.OTHER_COST, alt) or Decimal("0")
    return BIAAlternativeParams(
        drug_cost=drug_cost, event_probability=event_probability, other_cost=other_cost
    )


def build_bia_input(model: EconomicModel) -> BIAInput:
    """Resolve stored parameters into a pure BIA engine input. Raises IncompleteModelError."""
    missing: list[str] = []

    if model.annual_budget_baseline is None:
        missing.append("Anggaran farmasi tahunan baseline")

    event_cost = model.value_of(ParamKey.EVENT_COST, Alternative.SHARED)
    if event_cost is None:
        missing.append(f"{ParamKey(ParamKey.EVENT_COST).label} (shared)")

    intervention = _bia_alternative(model, Alternative.INTERVENTION, missing)
    comparator = _bia_alternative(model, Alternative.COMPARATOR, missing)

    years: list[BIAYearParams] = []
    for t in range(1, model.horizon_years + 1):
        resolved = {}
        for key in _BIA_SCENARIO_KEYS:
            val = model.value_of(key, Alternative.SHARED, year_index=t)
            if val is None:
                missing.append(f"{ParamKey(key).label} (tahun {t})")
            resolved[key] = val or Decimal("0")
        years.append(
            BIAYearParams(
                year=t,
                eligible_population=resolved[ParamKey.ELIGIBLE_POPULATION],
                uptake=resolved[ParamKey.UPTAKE],
                market_share=resolved[ParamKey.MARKET_SHARE],
            )
        )

    if missing:
        raise IncompleteModelError(missing)

    return BIAInput(
        horizon_years=model.horizon_years,
        annual_budget_baseline=model.annual_budget_baseline,
        event_cost=event_cost,
        intervention=intervention,
        comparator=comparator,
        years=years,
    )


def _bia_year_rows_json(rows) -> list[dict]:
    return [
        {
            "year": r.year,
            "eligible_population": str(r.eligible_population),
            "uptake": str(r.uptake),
            "market_share": str(r.market_share),
            "patients_intervention": str(r.patients_intervention),
            "patients_comparator": str(r.patients_comparator),
            "incremental_drug_cost": str(r.incremental_drug_cost),
            "event_cost_offset": str(r.event_cost_offset),
            "incremental_other": str(r.incremental_other),
            "net_budget_impact": str(r.net_budget_impact),
            "cumulative_net_impact": str(r.cumulative_net_impact),
            "pct_of_annual_baseline": str(r.pct_of_annual_baseline),
        }
        for r in rows
    ]


def run_bia(model: EconomicModel, computed_by: User | None = None) -> EconBIAResult:
    """Resolve -> compute -> persist an append-only cost-offset BIA result."""
    bia_input = build_bia_input(model)
    result = compute_bia(bia_input)

    return EconBIAResult.objects.create(
        case=model.case,
        input_snapshot={
            "horizon_years": bia_input.horizon_years,
            "annual_budget_baseline": str(bia_input.annual_budget_baseline),
            "event_cost": str(bia_input.event_cost),
        },
        cumulative_net_impact=result.cumulative_net_impact,
        pct_of_total_baseline=result.pct_of_total_baseline,
        annual_budget_baseline=bia_input.annual_budget_baseline,
        severity=result.severity,
        budget_score=result.budget_score,
        per_year=_bia_year_rows_json(result.year_rows),
        interpretation_text=result.interpretation_text,
        algorithm_version=result.algorithm_version,
        computed_by=computed_by,
    )
