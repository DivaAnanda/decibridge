"""R1 foundation tests: precision, provenance, resolution, versioning, audit."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.econ.models import (
    Alternative,
    DataStatus,
    EconomicModel,
    EconomicParameter,
    ParamKey,
    ParamType,
)


@pytest.fixture
def econ_model(pilot_case, hta_user) -> EconomicModel:
    return EconomicModel.objects.create(
        case=pilot_case,
        horizon_years=1,
        cost_discount_rate=Decimal("0.03"),
        outcome_discount_rate=Decimal("0.03"),
        wtp_threshold=Decimal("85000000.0000"),
        created_by=hta_user,
    )


def _param(econ_model, hta_user, **overrides) -> EconomicParameter:
    defaults = dict(
        economic_model=econ_model,
        key=ParamKey.DRUG_COST,
        alternative=Alternative.INTERVENTION,
        value=Decimal("18499451.85"),
        param_type=ParamType.COST,
        data_status=DataStatus.ASSUMPTION,
        created_by=hta_user,
    )
    defaults.update(overrides)
    return EconomicParameter.objects.create(**defaults)


@pytest.mark.django_db
class TestPrecision:
    def test_qaly_keeps_ten_decimal_places(self, econ_model, hta_user):
        # Arrange: a QALY value more precise than the old DECIMAL(_,4) allowed.
        precise = Decimal("0.6292312345")

        # Act
        p = _param(
            econ_model,
            hta_user,
            key=ParamKey.BASELINE_UTILITY,
            alternative=Alternative.COMPARATOR,
            value=precise,
            param_type=ParamType.UTILITY,
        )
        p.refresh_from_db()

        # Assert: stored and retrieved at full 10-dp precision.
        assert p.value == precise

    def test_cost_keeps_four_decimal_places(self, econ_model, hta_user):
        precise = Decimal("5199411.1161")
        p = _param(econ_model, hta_user, value=precise)
        p.refresh_from_db()
        assert p.value == precise


@pytest.mark.django_db
class TestValueResolution:
    def test_prefers_alternative_specific_then_shared(self, econ_model, hta_user):
        _param(econ_model, hta_user, key=ParamKey.EVENT_COST,
               alternative=Alternative.SHARED, value=Decimal("1000000"))
        _param(econ_model, hta_user, key=ParamKey.EVENT_COST,
               alternative=Alternative.INTERVENTION, value=Decimal("2000000"))

        assert econ_model.value_of(ParamKey.EVENT_COST, Alternative.INTERVENTION) == Decimal("2000000")
        # Comparator has no specific row → falls back to the shared value.
        assert econ_model.value_of(ParamKey.EVENT_COST, Alternative.COMPARATOR) == Decimal("1000000")

    def test_per_year_prefers_exact_year_then_year_agnostic(self, econ_model, hta_user):
        _param(econ_model, hta_user, key=ParamKey.UPTAKE, param_type=ParamType.RATE,
               alternative=Alternative.INTERVENTION, year_index=None, value=Decimal("0.30"))
        _param(econ_model, hta_user, key=ParamKey.UPTAKE, param_type=ParamType.RATE,
               alternative=Alternative.INTERVENTION, year_index=3, value=Decimal("0.60"))

        assert econ_model.value_of(ParamKey.UPTAKE, Alternative.INTERVENTION, year_index=3) == Decimal("0.60")
        # Year 2 has no exact row → falls back to the year-agnostic default.
        assert econ_model.value_of(ParamKey.UPTAKE, Alternative.INTERVENTION, year_index=2) == Decimal("0.30")

    def test_missing_returns_none(self, econ_model):
        assert econ_model.value_of(ParamKey.OTHER_COST, Alternative.INTERVENTION) is None


@pytest.mark.django_db
class TestConstraintsAndValidation:
    def test_duplicate_key_alt_year_rejected(self, econ_model, hta_user):
        _param(econ_model, hta_user, key=ParamKey.DRUG_COST, alternative=Alternative.INTERVENTION)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                _param(econ_model, hta_user, key=ParamKey.DRUG_COST,
                       alternative=Alternative.INTERVENTION)

    def test_probability_out_of_range_rejected(self, econ_model, hta_user):
        p = EconomicParameter(
            economic_model=econ_model,
            key=ParamKey.EVENT_PROBABILITY,
            alternative=Alternative.INTERVENTION,
            value=Decimal("1.5"),
            param_type=ParamType.PROBABILITY,
            created_by=hta_user,
        )
        with pytest.raises(ValidationError):
            p.clean()

    def test_negative_cost_rejected(self, econ_model, hta_user):
        p = EconomicParameter(
            economic_model=econ_model,
            key=ParamKey.DRUG_COST,
            alternative=Alternative.INTERVENTION,
            value=Decimal("-1"),
            param_type=ParamType.COST,
            created_by=hta_user,
        )
        with pytest.raises(ValidationError):
            p.clean()


@pytest.mark.django_db
class TestVersioningAndAudit:
    def test_version_increments_on_edit(self, econ_model, hta_user):
        p = _param(econ_model, hta_user, value=Decimal("100"))
        assert p.version == 1

        p.value = Decimal("200")
        p.save()
        p.refresh_from_db()
        assert p.version == 2

    def test_history_records_each_change(self, econ_model, hta_user):
        p = _param(econ_model, hta_user, value=Decimal("100"))
        p.value = Decimal("200")
        p.save()

        # simple_history keeps a row per create + per edit.
        assert p.history.count() == 2

    def test_display_label_falls_back_to_key_label(self, econ_model, hta_user):
        p = _param(econ_model, hta_user, key=ParamKey.DRUG_COST, label="")
        assert p.display_label == ParamKey.DRUG_COST.label

        p2 = _param(econ_model, hta_user, key=ParamKey.EVENT_COST, label="Biaya rawat inap ICU")
        assert p2.display_label == "Biaya rawat inap ICU"
