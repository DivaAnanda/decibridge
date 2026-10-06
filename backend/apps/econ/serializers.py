from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import (
    EconBIAResult,
    EconDeterministicResult,
    EconomicModel,
    EconomicParameter,
    EconPSAResult,
    ParamType,
)

# Uptake and market share are stored as `rate` and are proportions too; they were
# missing here, so a market share of 11 (1100%) saved without complaint.
_UNIT_INTERVAL_TYPES = {
    ParamType.PROBABILITY,
    ParamType.UTILITY,
    ParamType.DISUTILITY,
    ParamType.RATE,
}

_UNIT_INTERVAL_NOUN = {
    ParamType.PROBABILITY: "Probabilitas",
    ParamType.UTILITY: "Utility",
    ParamType.DISUTILITY: "Disutility",
    ParamType.RATE: "Uptake/market share",
}


def _plain(value: Decimal) -> str:
    return format(value.normalize(), "f")


def unit_interval_message(param_type: str, value: Decimal) -> str:
    """Say what to type, not only that the value is wrong.

    The usual mistake is a percentage (70 for 70%), so name the conversion.
    """
    noun = _UNIT_INTERVAL_NOUN.get(param_type, "Nilai")
    if Decimal("1") < value <= Decimal("100"):
        return (
            f"{noun} ditulis sebagai proporsi 0-1, bukan persen: "
            f"untuk {_plain(value)}% isi {_plain(value / Decimal('100'))}."
        )
    return f"{noun} harus berada pada rentang 0-1 (diisi {_plain(value)})."


class EconomicModelSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = EconomicModel
        fields = [
            "id",
            "horizon_years",
            "bia_horizon_years",
            "cost_discount_rate",
            "outcome_discount_rate",
            "wtp_threshold",
            "annual_budget_baseline",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "last_edited_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "last_edited_by"]

    def validate_bia_horizon_years(self, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise serializers.ValidationError("Horizon BIA minimal 1 tahun.")
        return value

    def validate_horizon_years(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Horizon minimal 1 tahun.")
        return value

    def validate_wtp_threshold(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("WTP harus > 0.")
        return value

    def validate(self, attrs: dict) -> dict:
        for field in ("cost_discount_rate", "outcome_discount_rate"):
            if attrs.get(field) is not None and attrs[field] < 0:
                raise serializers.ValidationError({field: "Discount rate tidak boleh negatif."})
        return attrs


class EconomicParameterSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = EconomicParameter
        fields = [
            "id",
            "key",
            "label",
            "display_label",
            "alternative",
            "year_index",
            "value",
            "unit",
            "param_type",
            "data_status",
            "source_reference",
            "source_year",
            "notes",
            "distribution",
            "dist_param1",
            "dist_param2",
            "version",
            "created_at",
            "updated_at",
            "created_by",
            "last_edited_by",
        ]
        read_only_fields = [
            "id",
            "display_label",
            "version",
            "created_at",
            "updated_at",
            "created_by",
            "last_edited_by",
        ]

    def validate(self, attrs: dict) -> dict:
        param_type = attrs.get("param_type", ParamType.COST)
        value = attrs.get("value")
        if value is not None:
            if param_type in _UNIT_INTERVAL_TYPES and not (Decimal("0") <= value <= Decimal("1")):
                raise serializers.ValidationError(
                    {"value": unit_interval_message(param_type, value)}
                )
            if param_type == ParamType.COST and value < 0:
                raise serializers.ValidationError({"value": "Biaya tidak boleh negatif."})
            if param_type == ParamType.COUNT and value < 0:
                raise serializers.ValidationError({"value": "Jumlah tidak boleh negatif."})
        return attrs


class EconBIAResultSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)

    class Meta:
        model = EconBIAResult
        fields = [
            "id",
            "input_snapshot",
            "cumulative_net_impact",
            "pct_of_total_baseline",
            "annual_budget_baseline",
            "severity",
            "budget_score",
            "per_year",
            "scenarios",
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields


class EconPSAResultSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)

    class Meta:
        model = EconPSAResult
        fields = [
            "id",
            "input_snapshot",
            "n_simulations",
            "random_seed",
            "wtp_base",
            "prob_cost_effective_base",
            "mean_incremental_cost",
            "mean_incremental_qaly",
            "ceac",
            "scatter",
            "base_case_incremental_cost",
            "base_case_incremental_qaly",
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields


class EconDeterministicResultSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)

    class Meta:
        model = EconDeterministicResult
        fields = [
            "id",
            "input_snapshot",
            "total_cost_intervention",
            "total_cost_comparator",
            "total_qaly_intervention",
            "total_qaly_comparator",
            "incremental_cost",
            "incremental_qaly",
            "icer",
            "nmb_intervention",
            "nmb_comparator",
            "inb",
            "wtp_threshold_used",
            "decision_code",
            "is_cost_effective",
            "is_dominant",
            "is_dominated",
            "per_year",
            "cost_breakdown",
            "clinical",
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields
