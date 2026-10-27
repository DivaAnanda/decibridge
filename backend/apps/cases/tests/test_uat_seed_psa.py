"""The UAT seeder keeps UAT_LENGKAP signable under round 5 item 1.

On production UAT_LENGKAP was seeded in September, before PSA runs recorded their
inputs, so the new gate would refuse its sign-off although nothing about it changed.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.cases.completeness import evaluate_readiness
from apps.cases.models import Case
from apps.econ.models import EconomicModel
from apps.econ.tests.factories import make_psa_result

pytestmark = pytest.mark.django_db


def _psa(case) -> dict:
    report = evaluate_readiness(case, action="approve")
    return next(r for r in report["requirements"] if r["key"] == "psa")


@pytest.fixture
def seeded(hta_user, kft_member_user) -> Case:
    call_command("seed_uat_cases", stdout=StringIO())
    return Case.objects.get(case_id="UAT_LENGKAP")


def test_a_psa_from_before_recorded_inputs_is_rerun(seeded, hta_user):
    make_psa_result(seeded, hta_user, record_inputs=False)
    assert _psa(seeded)["satisfied"] is False

    call_command("seed_uat_cases", stdout=StringIO())

    assert _psa(seeded)["satisfied"] is True
    assert evaluate_readiness(seeded, action="approve")["is_ready"] is True


def test_a_psa_made_stale_by_an_edit_is_left_for_the_user(seeded):
    model = EconomicModel.objects.get(case=seeded)
    model.wtp_threshold = Decimal("100000000")
    model.save()
    runs = seeded.econ_psa_results.count()

    call_command("seed_uat_cases", stdout=StringIO())

    assert seeded.econ_psa_results.count() == runs
    assert _psa(seeded)["satisfied"] is False
