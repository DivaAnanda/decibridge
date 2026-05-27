"""CEA-only fixtures. Shared user/case fixtures come from project root + cases conftests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cea.models import CEAInput


@pytest.fixture
def cea_input_payload() -> dict:
    return {
        "drug_cost_per_unit": "10000000.00",
        "comparator_cost_per_unit": "5000000.00",
        "efficacy_metric": "qaly",
        "drug_efficacy_value": "2.5000",
        "comparator_efficacy_value": "2.0000",
        "patient_population_size": 150,
        "wtop_threshold": "250000000.00",
        "data_source": "literature",
        "evidence_year": 2024,
        "notes": "Pilot ARNI vs ACEI test inputs",
    }


@pytest.fixture
def cea_input(pilot_case, hta_user, cea_input_payload) -> CEAInput:
    return CEAInput.objects.create(
        case=pilot_case,
        drug_cost_per_unit=Decimal(cea_input_payload["drug_cost_per_unit"]),
        comparator_cost_per_unit=Decimal(cea_input_payload["comparator_cost_per_unit"]),
        efficacy_metric=cea_input_payload["efficacy_metric"],
        drug_efficacy_value=Decimal(cea_input_payload["drug_efficacy_value"]),
        comparator_efficacy_value=Decimal(cea_input_payload["comparator_efficacy_value"]),
        patient_population_size=cea_input_payload["patient_population_size"],
        wtop_threshold=Decimal(cea_input_payload["wtop_threshold"]),
        data_source=cea_input_payload["data_source"],
        evidence_year=cea_input_payload["evidence_year"],
        notes=cea_input_payload["notes"],
        created_by=hta_user,
        last_edited_by=hta_user,
    )
