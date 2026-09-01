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
    BIAScenario,
    BIAYearParams,
    compute_bia,
)
from .engine_deterministic import (
    AlternativeInputs,
    DeterministicInput,
    compute_deterministic,
)
from .engine_psa import (
    AlternativeSpecs,
    ParamSpec,
    PSAInput,
    compute_psa,
)
from .models import (
    Alternative,
    EconBIAResult,
    EconDeterministicResult,
    EconomicModel,
    EconPSAResult,
    ParamKey,
)
from .validation_fixtures import PSA_SEED, PSA_SIMULATIONS

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
        median_los=model.value_of(ParamKey.MEDIAN_LOS, alt),
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
        clinical=(
            {
                "absolute_risk_reduction": str(result.clinical.absolute_risk_reduction),
                "relative_risk": _s(result.clinical.relative_risk),
                "relative_risk_reduction": _s(result.clinical.relative_risk_reduction),
                "nnt": _s(result.clinical.nnt),
                "admission_cost_saving_per_patient_year": str(
                    result.clinical.admission_cost_saving_per_patient_year
                ),
                "los_difference": _s(result.clinical.los_difference),
            }
            if result.clinical
            else {}
        ),
        interpretation_text=result.interpretation_text,
        algorithm_version=result.algorithm_version,
        computed_by=computed_by,
    )


def _s(value) -> str | None:
    return None if value is None else str(value)


# ── Budget Impact Analysis (R4) ─────────────────────────────────────────────

# Mandatory shared scenario parameters for the cost-offset BIA (per year).
# MARKET_SHARE is deliberately NOT required — it defaults to 1.0.
_BIA_SCENARIO_KEYS = [
    ParamKey.ELIGIBLE_POPULATION,
    ParamKey.UPTAKE,
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

    # annual_budget_baseline is OPTIONAL: without it the net impact is still
    # computed, but severity/budget-score come back "not assessed" rather than
    # being fabricated. (The lecturer's workbook has no budget baseline.)
    event_cost = model.value_of(ParamKey.EVENT_COST, Alternative.SHARED)
    if event_cost is None:
        missing.append(f"{ParamKey(ParamKey.EVENT_COST).label} (shared)")

    intervention = _bia_alternative(model, Alternative.INTERVENTION, missing)
    comparator = _bia_alternative(model, Alternative.COMPARATOR, missing)

    years: list[BIAYearParams] = []
    eligible_y1 = Decimal("0")
    for t in range(1, model.horizon_years + 1):
        eligible = model.value_of(ParamKey.ELIGIBLE_POPULATION, Alternative.SHARED, year_index=t)
        uptake = model.value_of(ParamKey.UPTAKE, Alternative.SHARED, year_index=t)
        if eligible is None:
            missing.append(f"{ParamKey(ParamKey.ELIGIBLE_POPULATION).label} (tahun {t})")
        if uptake is None:
            missing.append(f"{ParamKey(ParamKey.UPTAKE).label} (tahun {t})")
        # Optional second multiplier — the lecturer's model omits it (=> 1.0).
        share = model.value_of(ParamKey.MARKET_SHARE, Alternative.SHARED, year_index=t)
        if t == 1:
            eligible_y1 = eligible or Decimal("0")
        years.append(
            BIAYearParams(
                year=t,
                eligible_population=eligible or Decimal("0"),
                uptake=uptake or Decimal("0"),
                market_share=Decimal("1") if share is None else share,
            )
        )

    if missing:
        raise IncompleteModelError(missing)

    # One-year uptake scenarios (sheet 03_BIA). Only those defined are reported.
    scenarios: list[BIAScenario] = []
    for label, key in (
        ("low", ParamKey.UPTAKE_LOW),
        ("medium", ParamKey.UPTAKE_MEDIUM),
        ("high", ParamKey.UPTAKE_HIGH),
    ):
        val = model.value_of(key, Alternative.SHARED)
        if val is not None:
            scenarios.append(BIAScenario(label=label, uptake=val))

    base_share = model.value_of(ParamKey.MARKET_SHARE, Alternative.SHARED)
    return BIAInput(
        horizon_years=model.horizon_years,
        annual_budget_baseline=model.annual_budget_baseline,
        event_cost=event_cost,
        intervention=intervention,
        comparator=comparator,
        years=years,
        scenarios=scenarios,
        scenario_eligible_population=eligible_y1,
        scenario_market_share=Decimal("1") if base_share is None else base_share,
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
        scenarios=[
            {
                "label": s.label,
                "uptake": str(s.uptake),
                "eligible_population": str(s.eligible_population),
                "patients_intervention": str(s.patients_intervention),
                "incremental_drug_cost": str(s.incremental_drug_cost),
                "event_cost_offset": str(s.event_cost_offset),
                "net_budget_impact": str(s.net_budget_impact),
            }
            for s in result.scenario_rows
        ],
        interpretation_text=result.interpretation_text,
        algorithm_version=result.algorithm_version,
        computed_by=computed_by,
    )


# ── Probabilistic Sensitivity Analysis (R5) ─────────────────────────────────

def _find_param(model: EconomicModel, key: str, alt: str):
    rows = list(
        model.parameters.filter(
            key=key, alternative__in=[alt, Alternative.SHARED], year_index__isnull=True
        )
    )
    exact = next((r for r in rows if r.alternative == alt), None)
    return exact or next((r for r in rows if r.alternative == Alternative.SHARED), None)


def _param_spec(model: EconomicModel, key: str, alt: str) -> ParamSpec:
    row = _find_param(model, key, alt)
    if row is None:
        return ParamSpec(value=0.0)
    return ParamSpec(
        value=float(row.value),
        distribution=row.distribution,
        p1=float(row.dist_param1) if row.dist_param1 is not None else None,
        p2=float(row.dist_param2) if row.dist_param2 is not None else None,
    )


def _alternative_specs(model: EconomicModel, alt: str) -> AlternativeSpecs:
    return AlternativeSpecs(
        drug_cost=_param_spec(model, ParamKey.DRUG_COST, alt),
        event_probability=_param_spec(model, ParamKey.EVENT_PROBABILITY, alt),
        event_cost=_param_spec(model, ParamKey.EVENT_COST, alt),
        other_cost=_param_spec(model, ParamKey.OTHER_COST, alt),
        baseline_utility=_param_spec(model, ParamKey.BASELINE_UTILITY, alt),
        event_disutility=_param_spec(model, ParamKey.EVENT_DISUTILITY, alt),
    )


def run_psa(
    model: EconomicModel,
    computed_by: User | None = None,
    *,
    n_simulations: int = PSA_SIMULATIONS,
    seed: int = PSA_SEED,
    wtp_min: float | None = None,
    wtp_max: float | None = None,
    wtp_step: float | None = None,
) -> EconPSAResult:
    """Resolve -> Monte-Carlo -> persist an append-only PSA result.

    build_input() reuse validates the mandatory-parameter set (raises
    IncompleteModelError) AND gives the deterministic base-case point.
    """
    base = compute_deterministic(build_input(model))

    wtp_base = float(model.wtp_threshold)
    lo = wtp_min if wtp_min is not None else 0.0
    hi = wtp_max if wtp_max is not None else wtp_base * 2.0
    step = wtp_step if wtp_step is not None else (hi - lo) / 20.0 or wtp_base / 10.0

    psa_input = PSAInput(
        horizon_years=model.horizon_years,
        cost_discount_rate=float(model.cost_discount_rate),
        outcome_discount_rate=float(model.outcome_discount_rate),
        wtp_base=wtp_base,
        wtp_min=lo,
        wtp_max=hi,
        wtp_step=step,
        n_simulations=n_simulations,
        seed=seed,
        intervention=_alternative_specs(model, Alternative.INTERVENTION),
        comparator=_alternative_specs(model, Alternative.COMPARATOR),
        base_incremental_cost=float(base.incremental_cost),
        base_incremental_qaly=float(base.incremental_qaly),
    )
    result = compute_psa(psa_input)

    return EconPSAResult.objects.create(
        case=model.case,
        input_snapshot={
            "n_simulations": n_simulations,
            "seed": seed,
            "wtp_base": str(wtp_base),
            "wtp_min": lo,
            "wtp_max": hi,
            "wtp_step": step,
        },
        n_simulations=result.n_simulations,
        random_seed=result.seed,
        wtp_base=model.wtp_threshold,
        prob_cost_effective_base=Decimal(str(round(result.prob_cost_effective_base, 4))),
        mean_incremental_cost=Decimal(str(result.mean_incremental_cost)),
        mean_incremental_qaly=Decimal(str(result.mean_incremental_qaly)),
        ceac=result.ceac,
        scatter=result.scatter,
        base_case_incremental_cost=base.incremental_cost,
        base_case_incremental_qaly=base.incremental_qaly,
        interpretation_text=result.interpretation_text,
        algorithm_version=result.algorithm_version,
        computed_by=computed_by,
    )
