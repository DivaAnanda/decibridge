"""Pure cost-offset BIA engine tests (Phase R4). No DB required."""

from __future__ import annotations

from decimal import Decimal

from apps.econ.engine_bia import (
    BIAAlternativeParams,
    BIAInput,
    BIAYearParams,
    compute_bia,
)


def _input(*, drug_int, drug_comp, prob_int, prob_comp, event_cost, uptake, share,
           eligible=1000, baseline=Decimal("50000000000"), horizon=1) -> BIAInput:
    years = [
        BIAYearParams(year=t, eligible_population=Decimal(eligible),
                      uptake=Decimal(str(uptake)), market_share=Decimal(str(share)))
        for t in range(1, horizon + 1)
    ]
    return BIAInput(
        horizon_years=horizon,
        annual_budget_baseline=baseline,
        event_cost=Decimal(str(event_cost)),
        intervention=BIAAlternativeParams(drug_cost=Decimal(str(drug_int)),
                                          event_probability=Decimal(str(prob_int)),
                                          other_cost=Decimal("0")),
        comparator=BIAAlternativeParams(drug_cost=Decimal(str(drug_comp)),
                                        event_probability=Decimal(str(prob_comp)),
                                        other_cost=Decimal("0")),
        years=years,
    )


class TestCostOffset:
    def test_hand_computed_single_year(self):
        # patients_int = 1000*0.5*0.5 = 250
        # incremental_drug = 250*(10M-5M) = 1,250,000,000
        # offset = 250*(0.30-0.19)*20M = 250*0.11*20M = 550,000,000
        # net = 1,250,000,000 - 550,000,000 = 700,000,000
        r = compute_bia(_input(drug_int=10_000_000, drug_comp=5_000_000,
                               prob_int="0.19", prob_comp="0.30", event_cost=20_000_000,
                               uptake="0.5", share="0.5"))
        row = r.year_rows[0]
        assert row.patients_intervention == Decimal("250.000")
        assert row.incremental_drug_cost == Decimal("1250000000")
        assert row.event_cost_offset == Decimal("550000000.00")
        assert row.net_budget_impact == Decimal("700000000.00")
        assert r.cumulative_net_impact == Decimal("700000000.00")
        assert r.severity == "manageable"
        assert r.budget_score == 80

    def test_offset_can_flip_to_cost_saving(self):
        # Large event-cost offset (big prob reduction, expensive events) → net negative.
        r = compute_bia(_input(drug_int=6_000_000, drug_comp=5_000_000,
                               prob_int="0.10", prob_comp="0.50", event_cost=50_000_000,
                               uptake="0.5", share="0.5"))
        # incremental_drug = 250*1M = 250,000,000
        # offset = 250*0.40*50M = 5,000,000,000  → net = 250M - 5,000M = -4,750,000,000
        assert r.cumulative_net_impact < Decimal("0")
        assert r.severity == "cost_saving"
        assert r.budget_score == 100

    def test_patients_split_by_market_share(self):
        r = compute_bia(_input(drug_int=10_000_000, drug_comp=5_000_000,
                               prob_int="0.2", prob_comp="0.3", event_cost=10_000_000,
                               uptake="0.8", share="0.25"))
        row = r.year_rows[0]
        # eligible 1000 * uptake 0.8 = 800 treated; 25% on intervention = 200, 75% = 600
        assert row.patients_intervention == Decimal("200.000")
        assert row.patients_comparator == Decimal("600.000")
