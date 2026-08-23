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

from .engine_deterministic import (
    AlternativeInputs,
    DeterministicInput,
    compute_deterministic,
)
from .models import (
    Alternative,
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
