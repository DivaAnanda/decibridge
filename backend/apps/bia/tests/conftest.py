"""BIA-only fixtures. Shared user/case/client fixtures live in backend/conftest.py."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.bia.models import BIAInput


@pytest.fixture
def bia_input_payload() -> dict:
    return {
        "eligible_population": 1000,
        "patient_uptake_year1": "0.3000",
        "patient_uptake_year3": "0.6000",
        "market_share_year1": "0.5000",
        "market_share_year3": "0.7000",
        "unit_cost_drug": "10000000.00",
        "unit_cost_comparator": "5000000.00",
        "budget_baseline": "10000000000.00",
        "projection_horizon": 3,
        "notes": "Pilot ARNI vs ACEI BIA inputs",
    }


@pytest.fixture
def bia_input(pilot_case, hta_user, bia_input_payload) -> BIAInput:
    return BIAInput.objects.create(
        case=pilot_case,
        eligible_population=bia_input_payload["eligible_population"],
        patient_uptake_year1=Decimal(bia_input_payload["patient_uptake_year1"]),
        patient_uptake_year3=Decimal(bia_input_payload["patient_uptake_year3"]),
        market_share_year1=Decimal(bia_input_payload["market_share_year1"]),
        market_share_year3=Decimal(bia_input_payload["market_share_year3"]),
        unit_cost_drug=Decimal(bia_input_payload["unit_cost_drug"]),
        unit_cost_comparator=Decimal(bia_input_payload["unit_cost_comparator"]),
        budget_baseline=Decimal(bia_input_payload["budget_baseline"]),
        projection_horizon=bia_input_payload["projection_horizon"],
        notes=bia_input_payload["notes"],
        created_by=hta_user,
        last_edited_by=hta_user,
    )
