"""Probabilistic Sensitivity Analysis engine (Phase R5).

Monte-Carlo over parameter uncertainty. Reproducible: same seed + same
parameter specs → identical output (numpy `default_rng(seed)`).

Distributions (lecturer spec):
    Beta      — probabilities & utilities (naturally bounded [0,1])
    Gamma     — costs (>= 0)
    Log-normal— costs (>= 0), specified by mean + SE
    Normal    — general
    Fixed     — held at the point estimate

Each iteration samples the uncertain parameters, runs the same deterministic
cost-utility math (float domain for speed), and records incremental cost,
incremental QALY, and cost-effective status. Outputs:
    * CE-plane scatter cloud: (Δqaly, Δcost) per iteration + deterministic point
    * CEAC: P(cost-effective) across a WTP range = share of iterations with INB > 0
    * P(cost-effective) at the base-case WTP

This engine works in floats (not Decimal) — Monte-Carlo sampling error dwarfs
float rounding, and 1000+ iterations in Decimal would be needlessly slow. The
deterministic result (Phase R2) remains the exact, full-precision figure.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log, sqrt

import numpy as np

ALGORITHM_VERSION = "1.0.0"

# Distribution codes (mirror models.Distribution values).
FIXED = "fixed"
BETA = "beta"
GAMMA = "gamma"
LOGNORMAL = "lognormal"
NORMAL = "normal"


@dataclass(frozen=True)
class ParamSpec:
    """One parameter's point value + optional uncertainty distribution."""

    value: float
    distribution: str = FIXED
    p1: float | None = None  # alpha / shape / mean
    p2: float | None = None  # beta / scale / SE

    def draw(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.distribution == FIXED or self.p1 is None:
            return np.full(n, self.value)
        if self.distribution == BETA:
            return rng.beta(self.p1, self.p2 if self.p2 else 1.0, size=n)
        if self.distribution == GAMMA:
            return rng.gamma(self.p1, self.p2 if self.p2 else 1.0, size=n)
        if self.distribution == NORMAL:
            return rng.normal(self.p1, self.p2 or 0.0, size=n)
        if self.distribution == LOGNORMAL:
            # p1 = mean, p2 = SE of the variable → convert to underlying normal.
            mean, se = self.p1, (self.p2 or 0.0)
            if mean <= 0:
                return np.full(n, self.value)
            sigma2 = log(1.0 + (se * se) / (mean * mean)) if se > 0 else 0.0
            mu = log(mean) - sigma2 / 2.0
            return rng.lognormal(mu, sqrt(sigma2), size=n)
        return np.full(n, self.value)


@dataclass(frozen=True)
class AlternativeSpecs:
    drug_cost: ParamSpec
    event_probability: ParamSpec
    event_cost: ParamSpec
    other_cost: ParamSpec
    baseline_utility: ParamSpec
    event_disutility: ParamSpec


@dataclass(frozen=True)
class PSAInput:
    horizon_years: int
    cost_discount_rate: float
    outcome_discount_rate: float
    wtp_base: float
    wtp_min: float
    wtp_max: float
    wtp_step: float
    n_simulations: int
    seed: int
    intervention: AlternativeSpecs
    comparator: AlternativeSpecs
    base_incremental_cost: float
    base_incremental_qaly: float


@dataclass(frozen=True)
class PSAResult:
    n_simulations: int
    seed: int
    wtp_base: float
    prob_cost_effective_base: float
    mean_incremental_cost: float
    mean_incremental_qaly: float
    ceac: list[dict]  # [{"wtp": float, "prob": float}]
    scatter: list[list[float]]  # [[dqaly, dcost], ...]
    interpretation_text: str
    algorithm_version: str = ALGORITHM_VERSION


def _totals(specs: AlternativeSpecs, rng, n, horizon, cost_rate, outcome_rate):
    drug = specs.drug_cost.draw(rng, n)
    prob = np.clip(specs.event_probability.draw(rng, n), 0.0, 1.0)
    ecost = specs.event_cost.draw(rng, n)
    other = specs.other_cost.draw(rng, n)
    util = np.clip(specs.baseline_utility.draw(rng, n), 0.0, 1.0)
    disutil = np.clip(specs.event_disutility.draw(rng, n), 0.0, 1.0)

    annual_cost = drug + prob * ecost + other
    annual_qaly = util - prob * disutil

    total_cost = np.zeros(n)
    total_qaly = np.zeros(n)
    for t in range(1, horizon + 1):
        total_cost += annual_cost / ((1.0 + cost_rate) ** (t - 1))
        total_qaly += annual_qaly / ((1.0 + outcome_rate) ** (t - 1))
    return total_cost, total_qaly


def compute_psa(inp: PSAInput) -> PSAResult:
    rng = np.random.default_rng(inp.seed)
    n = inp.n_simulations

    cost_int, qaly_int = _totals(
        inp.intervention, rng, n, inp.horizon_years, inp.cost_discount_rate, inp.outcome_discount_rate
    )
    cost_comp, qaly_comp = _totals(
        inp.comparator, rng, n, inp.horizon_years, inp.cost_discount_rate, inp.outcome_discount_rate
    )

    inc_cost = cost_int - cost_comp
    inc_qaly = qaly_int - qaly_comp

    # CEAC across the WTP range: P(INB > 0) = P(wtp*Δqaly - Δcost > 0).
    wtps = np.arange(inp.wtp_min, inp.wtp_max + inp.wtp_step / 2.0, inp.wtp_step)
    ceac = [
        {"wtp": float(w), "prob": float(np.mean((w * inc_qaly - inc_cost) > 0.0))}
        for w in wtps
    ]

    prob_base = float(np.mean((inp.wtp_base * inc_qaly - inc_cost) > 0.0))

    scatter = [[float(q), float(c)] for q, c in zip(inc_qaly, inc_cost)]

    return PSAResult(
        n_simulations=n,
        seed=inp.seed,
        wtp_base=inp.wtp_base,
        prob_cost_effective_base=prob_base,
        mean_incremental_cost=float(np.mean(inc_cost)),
        mean_incremental_qaly=float(np.mean(inc_qaly)),
        ceac=ceac,
        scatter=scatter,
        interpretation_text=(
            f"PSA {n} iterasi (seed {inp.seed}). Probabilitas cost-effective pada WTP "
            f"{inp.wtp_base:,.0f} IDR = {prob_base * 100:.1f}%. "
            f"Rata-rata incremental cost {np.mean(inc_cost):,.0f} IDR, "
            f"incremental QALY {np.mean(inc_qaly):.4f}."
        ),
    )
