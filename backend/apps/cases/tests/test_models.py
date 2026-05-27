from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.cases.models import Case, CasePerspective, validate_case_id


@pytest.mark.django_db
class TestCaseIdValidation:
    @pytest.mark.parametrize("value", ["HF_ARNI_ACEI_001", "ABC", "DM_METFORMIN_2024_Q1"])
    def test_valid_case_ids_accepted(self, value):
        validate_case_id(value)  # no exception

    @pytest.mark.parametrize(
        "value",
        [
            "lowercase_id",
            "1_starts_with_digit",
            "AB",  # too short
            "HAS SPACE",
            "HAS-HYPHEN",
            "",
        ],
    )
    def test_invalid_case_ids_rejected(self, value):
        with pytest.raises(ValidationError):
            validate_case_id(value)


@pytest.mark.django_db
class TestCaseModel:
    def test_default_status_is_draft(self, pilot_case):
        assert pilot_case.status == "draft"
        assert pilot_case.is_editable is True
        assert pilot_case.is_locked is False

    def test_str_contains_id_and_title(self, pilot_case):
        assert "HF_ARNI_ACEI_001" in str(pilot_case)
        assert "ARNI vs ACEI" in str(pilot_case)

    def test_perspective_default(self, pilot_case):
        assert pilot_case.perspective == CasePerspective.HOSPITAL
