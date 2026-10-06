"""Saving the parameter table must not wipe what the table does not show.

The table never sent the PSA distribution fields, and the bulk save defaulted
missing ones to "fixed", so one click on "Simpan Parameter" reset every
distribution and the PSA quietly became deterministic. Found while loading
DB_DEMO_HF_001: 10 distributions before a UI-shaped save, 0 after.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.econ.models import EconomicParameter

pytestmark = pytest.mark.django_db

URL = "/api/v1/cases/DB_DEMO_HF_001/econ/parameters/"

# Exactly the fields EconTab sent before the fix.
TABLE_FIELDS = (
    "key", "alternative", "year_index", "value", "unit", "param_type",
    "data_status", "source_reference", "source_year", "notes", "label",
)


@pytest.fixture
def demo(hta_user):
    call_command("seed_demo_training_case", stdout=StringIO())


def _distributions():
    return {
        (p.key, p.alternative, p.year_index): (p.distribution, p.dist_param1, p.dist_param2)
        for p in EconomicParameter.objects.filter(economic_model__case__case_id="DB_DEMO_HF_001")
    }


def _table_payload(client):
    rows = client.get(URL).data
    return [{k: r[k] for k in TABLE_FIELDS} for r in rows]


class TestSavePreservesUnsentFields:
    def test_table_save_keeps_psa_distributions(self, hta_client, demo):
        before = _distributions()
        assert sum(1 for d in before.values() if d[0] != "fixed") == 10

        response = hta_client.put(URL, _table_payload(hta_client), format="json")

        assert response.status_code == 200, response.data
        assert _distributions() == before

    def test_explicit_distribution_is_still_updated(self, hta_client, demo):
        payload = _table_payload(hta_client)
        target = next(r for r in payload if r["key"] == "event_cost")
        target.update({"distribution": "lognormal", "dist_param1": "6000000", "dist_param2": "600000"})

        hta_client.put(URL, payload, format="json")

        p = EconomicParameter.objects.get(
            economic_model__case__case_id="DB_DEMO_HF_001", key="event_cost"
        )
        assert p.distribution == "lognormal"
        assert p.dist_param2 == Decimal("600000")

    def test_edit_changes_only_the_value(self, hta_client, demo):
        payload = _table_payload(hta_client)
        target = next(
            r for r in payload if r["key"] == "drug_cost" and r["alternative"] == "intervention"
        )
        target["value"] = "13200000"

        hta_client.put(URL, payload, format="json")

        p = EconomicParameter.objects.get(
            economic_model__case__case_id="DB_DEMO_HF_001",
            key="drug_cost",
            alternative="intervention",
        )
        assert p.value == Decimal("13200000")
        assert p.distribution == "gamma"
        assert p.unit == "IDR/pasien/tahun"

    def test_editing_does_not_reassign_the_creator(self, sekretaris_client, hta_user, demo):
        """The old upsert rewrote created_by on every save as well."""
        payload = [
            {k: r[k] for k in TABLE_FIELDS} for r in sekretaris_client.get(URL).data
        ]

        sekretaris_client.put(URL, payload, format="json")

        creators = set(
            EconomicParameter.objects.filter(
                economic_model__case__case_id="DB_DEMO_HF_001"
            ).values_list("created_by", flat=True)
        )
        assert creators == {hta_user.pk}
