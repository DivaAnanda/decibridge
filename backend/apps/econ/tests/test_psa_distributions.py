"""The PSA set-up is edited on its own screen, through its own endpoint.

Until now a distribution could only be set by a seeder or a workbook import, so
steps 37-39 of the training package ("pilih gamma", "pilih beta") could not be
done by hand. The endpoint carries no value: choosing a distribution must never
write back a stale base case, and a table save never writes back a stale
distribution.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.cases.models import Case, CaseStatus
from apps.econ.models import EconomicModel, EconomicParameter, EconPSAResult
from apps.econ.psa_distributions import distribution_errors

CASE_ID = "DB_DEMO_HF_001"
BASE = f"/api/v1/cases/{CASE_ID}/econ"
URL = f"{BASE}/psa/distributions/"

# 05_PSA of the training package, as someone would type it into the editor.
# Costs are annualised here (x12), so the scales are the sheet's x12 as well.
PACKAGE_INPUTS = [
    ("drug_cost", "intervention", "gamma", "100", "144000"),
    ("drug_cost", "comparator", "gamma", "100", "12000"),
    ("event_probability", "intervention", "beta", "60", "140"),
    ("event_probability", "comparator", "beta", "90", "110"),
    ("event_cost", "shared", "gamma", "100", "60000"),
    ("baseline_utility", "intervention", "beta", "36.4", "10.2666666667"),
    ("baseline_utility", "comparator", "beta", "38.8088888889", "13.6355555556"),
    ("event_disutility", "shared", "beta", "9.9", "89.1"),
    ("other_cost", "intervention", "gamma", "100", "3000"),
    ("other_cost", "comparator", "gamma", "100", "2000"),
]


@pytest.fixture
def demo(hta_user):
    call_command("seed_demo_training_case", stdout=StringIO())
    return Case.objects.get(case_id=CASE_ID)


def _param(key: str, alternative: str) -> EconomicParameter:
    return EconomicParameter.objects.get(
        economic_model__case__case_id=CASE_ID,
        key=key,
        alternative=alternative,
        year_index=None,
    )


def _row(param: EconomicParameter, distribution: str, p1=None, p2=None) -> dict:
    return {"id": param.pk, "distribution": distribution, "dist_param1": p1, "dist_param2": p2}


class TestDistributionErrors:
    def test_fixed_needs_nothing(self):
        assert distribution_errors("cost", "fixed", None, None) == {}

    def test_complete_set_ups_pass(self):
        assert distribution_errors("cost", "gamma", Decimal("100"), Decimal("144000")) == {}
        assert distribution_errors("probability", "beta", Decimal("60"), Decimal("140")) == {}
        assert distribution_errors("cost", "lognormal", Decimal("6000000"), Decimal("600000")) == {}
        assert distribution_errors("utility", "normal", Decimal("0.78"), Decimal("0.06")) == {}

    def test_missing_second_parameter_is_named(self):
        errors = distribution_errors("cost", "gamma", Decimal("100"), None)

        assert list(errors) == ["dist_param2"]
        assert "scale" in errors["dist_param2"]

    def test_non_positive_parameters_are_rejected(self):
        errors = distribution_errors("probability", "beta", Decimal("0"), Decimal("-1"))

        assert set(errors) == {"dist_param1", "dist_param2"}

    def test_unknown_distribution_is_an_error_not_a_crash(self):
        assert list(distribution_errors("utility", "Beta", Decimal("1"), Decimal("1"))) == [
            "distribution"
        ]

    def test_normal_mean_may_be_zero(self):
        assert distribution_errors("cost", "normal", Decimal("0"), Decimal("5")) == {}

    def test_beta_is_refused_for_a_cost(self):
        errors = distribution_errors("cost", "beta", Decimal("2"), Decimal("3"))

        assert list(errors) == ["distribution"]

    @pytest.mark.parametrize("distribution", ["gamma", "lognormal"])
    @pytest.mark.parametrize("param_type", ["probability", "utility", "disutility"])
    def test_cost_distributions_are_refused_for_proportions(self, distribution, param_type):
        """The package says of utility: 'Jangan gunakan gamma'."""
        errors = distribution_errors(param_type, distribution, Decimal("1"), Decimal("1"))

        assert list(errors) == ["distribution"]


@pytest.mark.django_db
class TestSaveDistributions:
    def test_sets_a_distribution(self, hta_client, demo):
        target = _param("event_cost", "shared")

        response = hta_client.put(
            URL, [_row(target, "lognormal", "6000000", "600000")], format="json"
        )

        assert response.status_code == 200, response.data
        assert len(response.data) == 16
        target.refresh_from_db()
        assert target.distribution == "lognormal"
        assert target.dist_param1 == Decimal("6000000")
        assert target.dist_param2 == Decimal("600000")

    def test_never_writes_the_value(self, hta_client, demo):
        target = _param("drug_cost", "intervention")
        row = {**_row(target, "gamma", "100", "132000"), "value": "1", "unit": "x"}

        hta_client.put(URL, [row], format="json")

        target.refresh_from_db()
        assert target.value == Decimal("14400000")
        assert target.unit == "IDR/pasien/tahun"
        assert target.dist_param2 == Decimal("132000")

    def test_writes_only_the_distribution_columns(self, hta_client, demo):
        """The row is read before it is saved; a full-row save would write its
        value back over a table save that landed in between."""
        target = _param("drug_cost", "intervention")

        with CaptureQueriesContext(connection) as queries:
            hta_client.put(URL, [_row(target, "gamma", "100", "132000")], format="json")

        updates = [
            q["sql"] for q in queries if q["sql"].startswith('UPDATE "econ_economicparameter"')
        ]
        assert len(updates) == 1
        assert '"distribution"' in updates[0]
        assert '"value"' not in updates[0]

    def test_fixed_clears_the_parameters(self, hta_client, demo):
        target = _param("drug_cost", "intervention")

        hta_client.put(URL, [_row(target, "fixed", "100", "144000")], format="json")

        target.refresh_from_db()
        assert (target.distribution, target.dist_param1, target.dist_param2) == ("fixed", None, None)

    def test_one_invalid_row_saves_nothing_and_says_which(self, hta_client, demo):
        good = _param("event_cost", "shared")
        bad = _param("drug_cost", "intervention")

        response = hta_client.put(
            URL,
            [_row(good, "lognormal", "6000000", "600000"), _row(bad, "gamma", "100", None)],
            format="json",
        )

        assert response.status_code == 400
        assert "detail" in response.data
        errors = response.data["row_errors"]
        assert [(e["index"], e["id"], e["field"]) for e in errors] == [(1, bad.pk, "dist_param2")]
        good.refresh_from_db()
        assert good.distribution == "gamma"

    def test_beta_on_a_cost_is_refused(self, hta_client, demo):
        target = _param("drug_cost", "intervention")

        response = hta_client.put(URL, [_row(target, "beta", "2", "3")], format="json")

        assert response.status_code == 400
        assert response.data["row_errors"][0]["field"] == "distribution"

    def test_parameter_psa_does_not_sample_is_refused(self, hta_client, demo):
        population = EconomicParameter.objects.get(
            economic_model__case=demo, key="eligible_population", year_index=1
        )

        response = hta_client.put(URL, [_row(population, "normal", "200", "20")], format="json")

        assert response.status_code == 400
        assert response.data["row_errors"][0]["field"] == "id"
        population.refresh_from_db()
        assert population.distribution == "fixed"

    def test_parameter_of_another_case_is_refused(self, hta_client, demo, pilot_case, hta_user):
        other_model = EconomicModel.objects.create(
            case=pilot_case, wtp_threshold=Decimal("85000000"), created_by=hta_user
        )
        foreign = EconomicParameter.objects.create(
            economic_model=other_model,
            key="drug_cost",
            alternative="intervention",
            value=Decimal("1000"),
            param_type="cost",
            created_by=hta_user,
        )

        response = hta_client.put(URL, [_row(foreign, "gamma", "100", "10")], format="json")

        assert response.status_code == 400
        foreign.refresh_from_db()
        assert foreign.distribution == "fixed"

    def test_unchanged_rows_keep_their_version(self, hta_client, demo):
        target = _param("drug_cost", "intervention")
        before = target.version

        hta_client.put(URL, [_row(target, "gamma", "100", "144000")], format="json")

        target.refresh_from_db()
        assert target.version == before

    def test_payload_must_be_a_list(self, hta_client, demo):
        assert hta_client.put(URL, {"id": 1}, format="json").status_code == 400

    def test_viewer_cannot_edit(self, kft_member_client, demo):
        target = _param("drug_cost", "intervention")

        response = kft_member_client.put(URL, [_row(target, "fixed")], format="json")

        assert response.status_code == 403

    def test_locked_case_is_read_only(self, hta_client, demo):
        Case.objects.filter(pk=demo.pk).update(status=CaseStatus.LOCKED)
        target = _param("drug_cost", "intervention")

        response = hta_client.put(URL, [_row(target, "fixed")], format="json")

        assert response.status_code == 403
        target.refresh_from_db()
        assert target.distribution == "gamma"


@pytest.mark.django_db
class TestRunUsesTheSetUp:
    def test_entering_the_package_by_hand_reproduces_the_seeded_result(self, hta_client, demo):
        seeded = demo.econ_psa_results.latest("computed_at")
        sampled = [_param(key, alt) for key, alt, *_ in PACKAGE_INPUTS]
        hta_client.put(URL, [_row(p, "fixed") for p in sampled], format="json")

        response = hta_client.put(
            URL,
            [_row(_param(key, alt), dist, p1, p2) for key, alt, dist, p1, p2 in PACKAGE_INPUTS],
            format="json",
        )
        assert response.status_code == 200, response.data
        rerun = hta_client.post(
            f"{BASE}/psa/compute/", {"n_simulations": 5000, "seed": 42}, format="json"
        )

        assert rerun.status_code == 201, rerun.data
        assert Decimal(rerun.data["prob_cost_effective_base"]) == seeded.prob_cost_effective_base
        assert rerun.data["scatter"][:5] == seeded.scatter[:5]

    def test_incomplete_distribution_blocks_the_run(self, hta_client, demo):
        """The engine used to substitute 1.0 for a missing second parameter."""
        EconomicParameter.objects.filter(pk=_param("drug_cost", "intervention").pk).update(
            dist_param2=None
        )

        response = hta_client.post(f"{BASE}/psa/compute/", {"seed": 42}, format="json")

        assert response.status_code == 422
        assert any("scale" in gap for gap in response.data["missing"])
        assert demo.econ_psa_results.count() == 1

    def test_unknown_stored_distribution_blocks_the_run_with_a_reason(self, hta_client, demo):
        """A workbook import stores this column as typed, e.g. "Beta"."""
        EconomicParameter.objects.filter(pk=_param("baseline_utility", "intervention").pk).update(
            distribution="Beta"
        )

        response = hta_client.post(f"{BASE}/psa/compute/", {"seed": 42}, format="json")

        assert response.status_code == 422
        assert any("'Beta' tidak dikenal" in gap for gap in response.data["missing"])

    def test_run_records_the_inputs_it_used(self, hta_client, demo):
        response = hta_client.post(f"{BASE}/psa/compute/", {"seed": 42}, format="json")

        inputs = response.data["input_snapshot"]["inputs"]
        drug = next(
            p
            for p in inputs["parameters"]
            if p["key"] == "drug_cost" and p["alternative"] == "intervention"
        )
        assert drug == {
            "key": "drug_cost",
            "alternative": "intervention",
            "value": "14400000",
            "distribution": "gamma",
            "dist_param1": "100",
            "dist_param2": "144000",
        }
        assert inputs["model"]["wtp_threshold"] == "300000000"


@pytest.mark.django_db
class TestStaleness:
    def _latest(self, client) -> dict:
        return client.get(f"{BASE}/psa/results/latest/").data

    def test_seeded_result_is_current(self, hta_client, demo):
        assert self._latest(hta_client)["is_stale"] is False

    def test_stale_after_a_distribution_changes(self, hta_client, demo):
        target = _param("event_cost", "shared")

        hta_client.put(URL, [_row(target, "lognormal", "6000000", "600000")], format="json")

        assert self._latest(hta_client)["is_stale"] is True

    def test_stale_after_a_sampled_value_changes(self, hta_client, demo):
        target = _param("drug_cost", "intervention")
        target.value = Decimal("13200000")
        target.save()

        assert self._latest(hta_client)["is_stale"] is True

    def test_not_stale_after_a_bia_only_value_changes(self, hta_client, demo):
        population = EconomicParameter.objects.get(
            economic_model__case=demo, key="eligible_population", year_index=1
        )
        population.value = Decimal("250")
        population.save()

        assert self._latest(hta_client)["is_stale"] is False

    def test_current_again_after_a_rerun(self, hta_client, demo):
        target = _param("event_cost", "shared")
        hta_client.put(URL, [_row(target, "lognormal", "6000000", "600000")], format="json")

        rerun = hta_client.post(f"{BASE}/psa/compute/", {"seed": 42}, format="json")

        assert rerun.data["is_stale"] is False

    def test_unknown_for_results_older_than_the_record(self, hta_client, demo):
        EconPSAResult.objects.filter(case=demo).update(input_snapshot={"seed": 42})

        assert self._latest(hta_client)["is_stale"] is None
