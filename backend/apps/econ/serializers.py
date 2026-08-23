from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import (
    EconBIAResult,
    EconDeterministicResult,
    EconomicModel,
    EconomicParameter,
    ParamType,
)

_UNIT_INTERVAL_TYPES = {ParamType.PROBABILITY, ParamType.UTILITY, ParamType.DISUTILITY}


class EconomicModelSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = EconomicModel
        fields = [
            "id",
            "horizon_years",
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
                    {"value": "Probabilitas/utility harus berada pada rentang 0–1."}
                )
            if param_type == ParamType.COST and value < 0:
                raise serializers.ValidationError({"value": "Biaya tidak boleh negatif."})
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
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields
