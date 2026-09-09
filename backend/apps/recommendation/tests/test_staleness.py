"""Round 3: a stored recommendation must announce when its inputs moved on.

Reproduces the reported `HF_ARNI_ACEI_001` symptom — a BIA result exists, but the
recommendation still says "BIA belum dijalankan" because it predates the run.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.etd.models import EtDAppraisal
from apps.recommendation.models import Recommendation
from apps.recommendation.staleness import (
    REASON_BIA,
    REASON_ECON,
    REASON_ETD,
    evaluate_staleness,
)

pytestmark = pytest.mark.django_db


def _recommendation(case, user, *, age_minutes: int = 0) -> Recommendation:
    return Recommendation.objects.create(
        case=case,
        input_snapshot={},
        evidence_strength_score=Decimal("80"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        composite_score=Decimal("85.00"),
        traffic_light="green",
        justification_text="seed",
        algorithm_version="2.0.0",
        computed_by=user,
        computed_at=timezone.now() - timedelta(minutes=age_minutes),
    )


def test_recommendation_with_untouched_inputs_is_not_stale(pilot_case, hta_user):
    rec = _recommendation(pilot_case, hta_user)

    report = evaluate_staleness(pilot_case, rec)

    assert report.is_stale is False
    assert report.reasons == []


def test_bia_computed_after_the_recommendation_marks_it_stale(
    pilot_case, hta_user, seeded_bia_result
):
    """The exact _001 shape: BIA exists but the recommendation predates it."""
    rec = _recommendation(pilot_case, hta_user, age_minutes=60)

    report = evaluate_staleness(pilot_case, rec)

    assert report.is_stale is True
    assert REASON_BIA in report.reasons


def test_econ_recompute_after_the_recommendation_marks_it_stale(
    pilot_case, hta_user, seeded_econ_result
):
    rec = _recommendation(pilot_case, hta_user, age_minutes=60)

    report = evaluate_staleness(pilot_case, rec)

    assert report.is_stale is True
    assert REASON_ECON in report.reasons


def test_etd_appraisal_change_after_the_recommendation_marks_it_stale(
    pilot_case, hta_user, etd_domains, kft_member_user
):
    rec = _recommendation(pilot_case, hta_user, age_minutes=60)
    EtDAppraisal.objects.create(
        case=pilot_case,
        domain=etd_domains[0],
        member=kft_member_user,
        judgement=75,
        certainty="high",
    )

    report = evaluate_staleness(pilot_case, rec)

    assert report.is_stale is True
    assert REASON_ETD in report.reasons


def test_several_changed_inputs_are_all_reported(
    pilot_case, hta_user, seeded_econ_result, seeded_bia_result
):
    rec = _recommendation(pilot_case, hta_user, age_minutes=60)

    report = evaluate_staleness(pilot_case, rec)

    assert {REASON_ECON, REASON_BIA} <= set(report.reasons)


def test_latest_endpoint_exposes_staleness(
    hta_client, pilot_case, hta_user, seeded_bia_result
):
    _recommendation(pilot_case, hta_user, age_minutes=60)
    url = reverse("recommendation:result_latest", args=[pilot_case.case_id])

    response = hta_client.get(url)

    assert response.status_code == 200
    assert response.data["is_stale"] is True
    assert REASON_BIA in response.data["stale_reasons"]
