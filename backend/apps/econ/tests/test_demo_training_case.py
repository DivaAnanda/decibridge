"""DB_DEMO_HF_001 must reproduce the training package's 11_INSTRUCTOR_KEY.

The package is the first independent reference for PSA as well as CEA and BIA,
so these assertions double as numerical validation of all three engines.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.cases.models import Case
from apps.econ.models import EconomicParameter

pytestmark = pytest.mark.django_db

CASE_ID = "DB_DEMO_HF_001"


@pytest.fixture
def demo_case(hta_user):
    call_command("seed_demo_training_case", stdout=StringIO())
    return Case.objects.get(case_id=CASE_ID)


def _close(actual, expected, tolerance="0.01") -> bool:
    return abs(Decimal(str(actual)) - Decimal(str(expected))) <= Decimal(tolerance)


class TestInstructorKeyDeterministic:
    def test_costs_and_qalys(self, demo_case):
        r = demo_case.econ_deterministic_results.latest("computed_at")

        assert _close(r.total_cost_intervention, "16500000")
        assert _close(r.total_cost_comparator, "4100000")
        assert _close(r.incremental_cost, "12400000")
        assert _close(r.total_qaly_intervention, "0.75", "0.0000001")
        assert _close(r.total_qaly_comparator, "0.695", "0.0000001")
        assert _close(r.incremental_qaly, "0.055", "0.0000001")

    def test_icer_nmb_inb(self, demo_case):
        r = demo_case.econ_deterministic_results.latest("computed_at")

        assert _close(r.icer, "225454545.45")
        assert _close(r.nmb_intervention, "208500000")
        assert _close(r.nmb_comparator, "204400000")
        assert _close(r.inb, "4100000")


class TestInstructorKeyBIA:
    def test_three_year_net_budget_impact(self, demo_case):
        """Needs the separate BIA horizon: the package runs CEA over 1 year and
        BIA over 3, which a single shared horizon could not reproduce."""
        r = demo_case.econ_bia_results.latest("computed_at")

        nets = [Decimal(row["net_budget_impact"]) for row in r.per_year]
        assert len(nets) == 3
        assert _close(nets[0], "496000000")
        assert _close(nets[1], "954800000")
        assert _close(nets[2], "1488000000")
        assert _close(r.cumulative_net_impact, "2938800000")

    def test_patients_per_year(self, demo_case):
        r = demo_case.econ_bia_results.latest("computed_at")

        assert [Decimal(row["patients_intervention"]) for row in r.per_year] == [
            Decimal("40"),
            Decimal("77"),
            Decimal("120"),
        ]


class TestInstructorKeyPSA:
    def test_probability_cost_effective(self, demo_case):
        """The key allows "± several points if RNG differs"; 3 points is used."""
        r = demo_case.econ_psa_results.latest("computed_at")

        assert r.n_simulations == 5000
        assert r.random_seed == 42
        assert abs(Decimal(str(r.prob_cost_effective_base)) - Decimal("0.5634")) <= Decimal("0.03")

    def test_mean_increments(self, demo_case):
        r = demo_case.econ_psa_results.latest("computed_at")

        cost = Decimal(str(r.mean_incremental_cost))
        qaly = Decimal(str(r.mean_incremental_qaly))
        assert abs(cost - Decimal("12407194.25")) / Decimal("12407194.25") < Decimal("0.01")
        assert abs(qaly - Decimal("0.0546")) / Decimal("0.0546") < Decimal("0.03")


class TestLabellingAndSafety:
    def test_case_is_labelled_synthetic(self, demo_case):
        assert "sintetis" in demo_case.case_title.lower()
        model = demo_case.economic_model
        assert "SINTETIS" in model.notes

    def test_every_parameter_has_unit_and_source(self, demo_case):
        params = EconomicParameter.objects.filter(economic_model__case=demo_case)

        assert params.count() == 16
        assert all(p.unit and p.source_reference for p in params)

    def test_market_share_is_left_unset(self, demo_case):
        """The package's 'baseline share = 0' is a different concept; storing 0
        in our market_share multiplier would zero the whole BIA."""
        assert not EconomicParameter.objects.filter(
            economic_model__case=demo_case, key="market_share"
        ).exists()

    def test_source_register_is_loaded_as_references(self, demo_case):
        assert demo_case.references.count() == 6

    def test_rerun_does_not_duplicate(self, demo_case):
        call_command("seed_demo_training_case", stdout=StringIO())

        assert EconomicParameter.objects.filter(economic_model__case=demo_case).count() == 16
        assert demo_case.econ_deterministic_results.count() == 1
        assert demo_case.references.count() == 6

    def test_rerun_keeps_a_students_edit(self, demo_case):
        """The 10_VERSI exercise changes ARNI to Rp1.100.000/bulan; a deploy must
        not quietly undo that."""
        p = EconomicParameter.objects.get(
            economic_model__case=demo_case, key="drug_cost", alternative="intervention"
        )
        p.value = Decimal("13200000")
        p.save()

        call_command("seed_demo_training_case", stdout=StringIO())

        p.refresh_from_db()
        assert p.value == Decimal("13200000")

    def test_reset_restores_package_values(self, demo_case):
        p = EconomicParameter.objects.get(
            economic_model__case=demo_case, key="drug_cost", alternative="intervention"
        )
        p.value = Decimal("13200000")
        p.save()

        call_command("seed_demo_training_case", "--reset", stdout=StringIO())

        p.refresh_from_db()
        assert p.value == Decimal("14400000")
