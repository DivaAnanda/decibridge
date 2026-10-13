"""Rules for a parameter's PSA uncertainty set-up.

One place decides whether a distribution can be sampled, so the editor's save
and the PSA run refuse the same things. Without it the engine fell back
silently: a distribution with no parameters was held fixed, and a missing second
parameter became 1.0.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Distribution, EconomicModel, ParamKey, ParamType

# The parameters engine_psa samples. BIA-only rows (population, uptake) are not.
SAMPLED_KEYS = (
    ParamKey.DRUG_COST,
    ParamKey.EVENT_PROBABILITY,
    ParamKey.EVENT_COST,
    ParamKey.OTHER_COST,
    ParamKey.BASELINE_UTILITY,
    ParamKey.EVENT_DISUTILITY,
)

_BOUNDED_TYPES = {ParamType.PROBABILITY, ParamType.UTILITY, ParamType.DISUTILITY}

_PARAM_NAMES = {
    Distribution.BETA: ("alpha", "beta"),
    Distribution.GAMMA: ("shape", "scale"),
    Distribution.LOGNORMAL: ("mean", "SE"),
    Distribution.NORMAL: ("mean", "SD"),
}


def distribution_errors(
    param_type: str, distribution: str, p1: Decimal | None, p2: Decimal | None
) -> dict[str, str]:
    """Field -> message for a set-up that cannot be sampled; empty when it can."""
    if distribution == Distribution.FIXED:
        return {}

    # A workbook import writes this column as free text, so a stored row can
    # hold something outside the choices (e.g. "Beta").
    names = _PARAM_NAMES.get(distribution)
    if names is None:
        return {"distribution": f"Distribusi '{distribution}' tidak dikenal; pilih ulang."}

    bounded = param_type in _BOUNDED_TYPES
    if distribution == Distribution.BETA and not bounded:
        return {
            "distribution": (
                "Beta hanya untuk probabilitas, utility dan disutility (nilai 0-1). "
                "Untuk biaya pilih Gamma atau Log-normal."
            )
        }
    if distribution in (Distribution.GAMMA, Distribution.LOGNORMAL) and bounded:
        return {
            "distribution": (
                "Gamma dan Log-normal untuk biaya. "
                "Untuk probabilitas, utility dan disutility pilih Beta."
            )
        }

    name1, name2 = names
    errors: dict[str, str] = {}
    if p1 is None:
        errors["dist_param1"] = f"{name1} wajib diisi."
    elif p1 <= 0 and distribution != Distribution.NORMAL:
        errors["dist_param1"] = f"{name1} harus lebih besar dari 0."
    if p2 is None:
        errors["dist_param2"] = f"{name2} wajib diisi."
    elif p2 <= 0:
        errors["dist_param2"] = f"{name2} harus lebih besar dari 0."
    return errors


def sampled_parameters(model: EconomicModel):
    """The rows a PSA run reads: sampled keys, year-agnostic only."""
    return model.parameters.filter(key__in=SAMPLED_KEYS, year_index__isnull=True)


def _canonical(value: Decimal | None) -> str | None:
    # A freshly created row holds Decimal("0") while the same row read back holds
    # Decimal("0E-10"); both must compare equal in a stored snapshot.
    return None if value is None else format(Decimal(value).normalize(), "f")


def psa_input_state(model: EconomicModel) -> dict:
    """Everything a PSA result depends on besides iterations and seed.

    Stored with each result so it can be reproduced after the set-up is edited,
    and compared with the present state to tell whether the result is stale.
    """
    return {
        "model": {
            "horizon_years": model.horizon_years,
            "cost_discount_rate": _canonical(model.cost_discount_rate),
            "outcome_discount_rate": _canonical(model.outcome_discount_rate),
            "wtp_threshold": _canonical(model.wtp_threshold),
        },
        "parameters": [
            {
                "key": p.key,
                "alternative": p.alternative,
                "value": _canonical(p.value),
                "distribution": p.distribution,
                "dist_param1": _canonical(p.dist_param1),
                "dist_param2": _canonical(p.dist_param2),
            }
            for p in sampled_parameters(model).order_by("key", "alternative")
        ],
    }
