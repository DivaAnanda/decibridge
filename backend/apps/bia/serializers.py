from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import BIAInput, BIAResult


class BIAInputSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = BIAInput
        fields = [
            "id",
            "eligible_population",
            "patient_uptake_year1",
            "patient_uptake_year3",
            "market_share_year1",
            "market_share_year3",
            "unit_cost_drug",
            "unit_cost_comparator",
            "budget_baseline",
            "projection_horizon",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "last_edited_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "last_edited_by"]

    def validate(self, attrs: dict) -> dict:
        errors: dict[str, str] = {}

        def _in_unit(field: str) -> None:
            v = attrs.get(field)
            if v is not None and not (Decimal("0") <= v <= Decimal("1")):
                errors[field] = "Nilai harus berada di rentang 0-1."

        for f in (
            "patient_uptake_year1",
            "patient_uptake_year3",
            "market_share_year1",
            "market_share_year3",
        ):
            _in_unit(f)

        for f in ("unit_cost_drug", "unit_cost_comparator", "budget_baseline"):
            v = attrs.get(f)
            if v is not None and v < 0:
                errors[f] = "Nilai biaya tidak boleh negatif."

        if (pop := attrs.get("eligible_population")) is not None and pop <= 0:
            errors["eligible_population"] = "Populasi pasien harus > 0."

        if (b := attrs.get("budget_baseline")) is not None and b <= 0:
            errors["budget_baseline"] = "Anggaran baseline harus > 0."

        # Monotonic-ish sanity check — uptake should not collapse on year 3.
        up1, up3 = attrs.get("patient_uptake_year1"), attrs.get("patient_uptake_year3")
        if up1 is not None and up3 is not None and up3 < up1 * Decimal("0.5"):
            errors["patient_uptake_year3"] = (
                "Uptake tahun 3 turun lebih dari 50% dari tahun 1 — periksa kembali asumsi."
            )

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class BIAResultSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)

    class Meta:
        model = BIAResult
        fields = [
            "id",
            "input_snapshot",
            "year1_drug_cost",
            "year1_comparator_cost_displaced",
            "year1_net_impact",
            "year2_net_impact_interpolated",
            "year3_drug_cost",
            "year3_comparator_cost_displaced",
            "year3_net_impact",
            "cumulative_impact",
            "pct_of_annual_budget",
            "severity",
            "direction",
            "budget_score",
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields
