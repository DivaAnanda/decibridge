"""Test data for the economics app that does not need a Monte-Carlo run."""

from __future__ import annotations

from decimal import Decimal

from apps.econ.models import EconomicModel, EconPSAResult
from apps.econ.psa_distributions import psa_input_state


def make_psa_result(case, user, *, record_inputs: bool = True) -> EconPSAResult:
    """A PSA row as `run_psa` stores it, for the case's present set-up.

    `record_inputs=False` gives a row like those written before 2026-10-13,
    which did not record the inputs they were run on.
    """
    model, _ = EconomicModel.objects.get_or_create(case=case, defaults={"created_by": user})
    snapshot: dict = {"n_simulations": 1000, "seed": 42}
    if record_inputs:
        snapshot["inputs"] = psa_input_state(model)
    return EconPSAResult.objects.create(
        case=case,
        input_snapshot=snapshot,
        n_simulations=1000,
        random_seed=42,
        wtp_base=model.wtp_threshold,
        prob_cost_effective_base=Decimal("0.5602"),
        mean_incremental_cost=Decimal("12400000"),
        mean_incremental_qaly=Decimal("0.055"),
        base_case_incremental_cost=Decimal("12400000"),
        base_case_incremental_qaly=Decimal("0.055"),
        interpretation_text="fixture",
        computed_by=user,
    )
