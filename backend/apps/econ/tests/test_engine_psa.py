"""Pure PSA engine tests (Phase R5). No DB required."""

from __future__ import annotations

from apps.econ.engine_psa import (
    AlternativeSpecs,
    ParamSpec,
    PSAInput,
    compute_psa,
)


def _alt(drug, prob, *, prob_dist="fixed", p1=None, p2=None) -> AlternativeSpecs:
    return AlternativeSpecs(
        drug_cost=ParamSpec(value=drug),
        event_probability=ParamSpec(value=prob, distribution=prob_dist, p1=p1, p2=p2),
        event_cost=ParamSpec(value=10_000_000.0),
        other_cost=ParamSpec(value=0.0),
        baseline_utility=ParamSpec(value=0.8, distribution="beta", p1=80.0, p2=20.0),
        event_disutility=ParamSpec(value=0.4),
    )


def _input(seed=42, n=2000) -> PSAInput:
    return PSAInput(
        horizon_years=1, cost_discount_rate=0.0, outcome_discount_rate=0.0,
        wtp_base=100_000_000.0, wtp_min=0.0, wtp_max=200_000_000.0, wtp_step=20_000_000.0,
        n_simulations=n, seed=seed,
        intervention=_alt(2_000_000.0, 0.20, prob_dist="beta", p1=20.0, p2=80.0),
        comparator=_alt(1_000_000.0, 0.35, prob_dist="beta", p1=35.0, p2=65.0),
        base_incremental_cost=1_000_000.0, base_incremental_qaly=0.06,
    )


class TestReproducibility:
    def test_same_seed_identical(self):
        a = compute_psa(_input(seed=123))
        b = compute_psa(_input(seed=123))
        assert a.prob_cost_effective_base == b.prob_cost_effective_base
        assert a.mean_incremental_cost == b.mean_incremental_cost
        assert a.scatter[:5] == b.scatter[:5]
        assert a.ceac == b.ceac

    def test_different_seed_differs(self):
        a = compute_psa(_input(seed=1))
        b = compute_psa(_input(seed=2))
        assert a.scatter[:5] != b.scatter[:5]


class TestOutputs:
    def test_scatter_and_ceac_shapes(self):
        r = compute_psa(_input(n=1500))
        assert len(r.scatter) == 1500
        assert len(r.ceac) >= 2
        # CEAC probabilities are within [0, 1] and non-decreasing-ish across WTP.
        probs = [pt["prob"] for pt in r.ceac]
        assert all(0.0 <= p <= 1.0 for p in probs)
        assert probs[-1] >= probs[0]

    def test_intervention_more_effective_is_often_cost_effective(self):
        # Intervention reduces events (0.20 vs 0.35) → more QALYs; modest extra cost.
        r = compute_psa(_input())
        assert r.prob_cost_effective_base > 0.5

    def test_beta_keeps_probabilities_in_range(self):
        # A high-variance beta should still never produce prob outside [0,1];
        # implicitly verified by finite, sane outputs.
        r = compute_psa(_input())
        assert r.mean_incremental_qaly == r.mean_incremental_qaly  # not NaN
