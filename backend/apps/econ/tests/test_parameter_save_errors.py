"""The lecturer's failed save on HF_ARNI_ACEI_0510, reproduced.

He entered all ten parameters with probabilities as percentages (70, 30). The
backend rejected those two rows, the atomic save discarded the eight valid ones
too, and the frontend showed only "Gagal menyimpan parameter." - so "Hitung"
then reported every parameter missing although he could see all of them filled.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.econ.models import EconomicModel, EconomicParameter

pytestmark = pytest.mark.django_db


def _url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/econ/parameters/"


@pytest.fixture
def econ_model(pilot_case, hta_user):
    return EconomicModel.objects.create(
        case=pilot_case,
        horizon_years=1,
        cost_discount_rate=Decimal("0"),
        outcome_discount_rate=Decimal("0"),
        wtp_threshold=Decimal("85000000"),
        created_by=hta_user,
    )


def _row(key, alternative, value, param_type, unit=""):
    return {
        "key": key,
        "alternative": alternative,
        "value": value,
        "unit": unit,
        "param_type": param_type,
        "data_status": "observed",
        "source_reference": "rs",
    }


LECTURER_ROWS = [
    _row("drug_cost", "intervention", "1000000", "cost", "rupiah"),
    _row("drug_cost", "comparator", "1500000", "cost", "rupiah"),
    _row("event_probability", "intervention", "70", "probability", "persen"),
    _row("event_probability", "comparator", "30", "probability", "persen"),
    _row("event_cost", "intervention", "300000", "cost", "rupiah"),
    _row("event_cost", "comparator", "400000", "cost", "rupiah"),
    _row("baseline_utility", "intervention", "0.8", "utility", "u"),
    _row("baseline_utility", "comparator", "0.9", "utility", "u"),
    _row("event_disutility", "intervention", "0.02", "disutility", "d"),
    _row("event_disutility", "comparator", "0.03", "disutility", "d"),
]


class TestFailedSaveIsExplained:
    def test_each_bad_row_is_identified(self, hta_client, pilot_case, econ_model):
        response = hta_client.put(_url(pilot_case.case_id), LECTURER_ROWS, format="json")

        assert response.status_code == 400
        flagged = {(e["key"], e["alternative"]) for e in response.data["row_errors"]}
        assert flagged == {
            ("event_probability", "intervention"),
            ("event_probability", "comparator"),
        }

    def test_message_names_the_percent_conversion(self, hta_client, pilot_case, econ_model):
        response = hta_client.put(_url(pilot_case.case_id), LECTURER_ROWS, format="json")

        messages = [e["message"] for e in response.data["row_errors"]]
        assert any("untuk 70% isi 0.7" in m for m in messages), messages
        assert any("untuk 30% isi 0.3" in m for m in messages), messages

    def test_rows_point_at_their_position_in_the_table(
        self, hta_client, pilot_case, econ_model
    ):
        response = hta_client.put(_url(pilot_case.case_id), LECTURER_ROWS, format="json")

        assert sorted(e["index"] for e in response.data["row_errors"]) == [2, 3]

    def test_detail_says_nothing_was_saved(self, hta_client, pilot_case, econ_model):
        response = hta_client.put(_url(pilot_case.case_id), LECTURER_ROWS, format="json")

        assert "tidak ada parameter yang disimpan" in response.data["detail"]
        assert EconomicParameter.objects.filter(economic_model=econ_model).count() == 0

    def test_corrected_rows_save(self, hta_client, pilot_case, econ_model):
        fixed = [dict(r) for r in LECTURER_ROWS]
        fixed[2]["value"] = "0.7"
        fixed[3]["value"] = "0.3"

        response = hta_client.put(_url(pilot_case.case_id), fixed, format="json")

        assert response.status_code == 200, response.data
        assert EconomicParameter.objects.filter(economic_model=econ_model).count() == 10


class TestRateIsAProportion:
    def test_market_share_over_one_is_rejected(self, hta_client, pilot_case, econ_model):
        """His earlier screenshot had a market share of 11, i.e. 1100%."""
        rows = [_row("market_share", "intervention", "11", "rate")]

        response = hta_client.put(_url(pilot_case.case_id), rows, format="json")

        assert response.status_code == 400
        assert "untuk 11% isi 0.11" in response.data["row_errors"][0]["message"]

    def test_uptake_within_range_saves(self, hta_client, pilot_case, econ_model):
        rows = [_row("uptake", "intervention", "0.3", "rate")]

        response = hta_client.put(_url(pilot_case.case_id), rows, format="json")

        assert response.status_code == 200, response.data


class TestMissingMessageMentionsShared:
    def test_shared_parameters_are_labelled_as_allowed_in_bersama(
        self, hta_client, pilot_case, econ_model
    ):
        response = hta_client.post(f"/api/v1/cases/{pilot_case.case_id}/econ/compute/")

        missing = response.data["missing"]
        assert any("atau Bersama" in m and "Biaya per kejadian" in m for m in missing)
        assert not any("atau Bersama" in m and "Biaya obat" in m for m in missing)


class TestErrorShapeAcrossDRFVersions:
    """DRF 3.17 reports bulk errors as a list, 3.18 as a dict keyed by index.

    The Docker image resolved 3.18 while the local venv had 3.17, so the API
    tests passed locally and the deployed container raised a 500. Both shapes
    are exercised directly here, independent of the installed version.
    """

    ROWS = [
        {"key": "drug_cost", "alternative": "intervention"},
        {"key": "event_probability", "alternative": "intervention"},
        {"key": "event_probability", "alternative": "comparator"},
    ]
    MESSAGE = "untuk 70% isi 0.7"

    def test_list_shape(self):
        from apps.econ.views import _row_errors

        errors = [{}, {"value": [self.MESSAGE]}, {"value": ["untuk 30% isi 0.3"]}]

        rows = _row_errors(self.ROWS, errors)

        assert [(r["index"], r["key"], r["alternative"]) for r in rows] == [
            (1, "event_probability", "intervention"),
            (2, "event_probability", "comparator"),
        ]

    def test_dict_shape(self):
        from apps.econ.views import _row_errors

        errors = {2: {"value": ["untuk 30% isi 0.3"]}, 1: {"value": [self.MESSAGE]}}

        rows = _row_errors(self.ROWS, errors)

        assert [(r["index"], r["alternative"]) for r in rows] == [
            (1, "intervention"),
            (2, "comparator"),
        ]
        assert rows[0]["message"] == self.MESSAGE

    def test_non_dict_item_errors_are_kept(self):
        from apps.econ.views import _row_errors

        rows = _row_errors(self.ROWS, {0: ["Baris tidak valid."]})

        assert rows == [
            {
                "index": 0,
                "key": "drug_cost",
                "alternative": "intervention",
                "field": "non_field_errors",
                "message": "Baris tidak valid.",
            }
        ]
