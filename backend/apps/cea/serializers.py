from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import CEAInput, CEAResult


class CEAInputSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = CEAInput
        fields = [
            "id",
            "drug_cost_per_unit",
            "comparator_cost_per_unit",
            "efficacy_metric",
            "metric_label",
            "drug_efficacy_value",
            "comparator_efficacy_value",
            "patient_population_size",
            "wtop_threshold",
            "data_source",
            "evidence_year",
            "notes",
            "created_at",
            "updated_at",
            "created_by",
            "last_edited_by",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "last_edited_by"]

    def validate(self, attrs: dict) -> dict:
        # Defensive: keep computation engine happy.
        if attrs.get("drug_cost_per_unit") is not None and attrs["drug_cost_per_unit"] < 0:
            raise serializers.ValidationError({"drug_cost_per_unit": "Biaya tidak boleh negatif."})
        if attrs.get("comparator_cost_per_unit") is not None and attrs["comparator_cost_per_unit"] < 0:
            raise serializers.ValidationError(
                {"comparator_cost_per_unit": "Biaya tidak boleh negatif."}
            )
        if attrs.get("drug_efficacy_value") is not None and attrs["drug_efficacy_value"] < 0:
            raise serializers.ValidationError({"drug_efficacy_value": "Efikasi tidak boleh negatif."})
        if attrs.get("comparator_efficacy_value") is not None and attrs["comparator_efficacy_value"] < 0:
            raise serializers.ValidationError(
                {"comparator_efficacy_value": "Efikasi tidak boleh negatif."}
            )
        if attrs.get("wtop_threshold") is not None and attrs["wtop_threshold"] <= 0:
            raise serializers.ValidationError({"wtop_threshold": "Ambang WTOP harus > 0."})
        if attrs.get("efficacy_metric") == "other" and not (attrs.get("metric_label") or "").strip():
            raise serializers.ValidationError(
                {"metric_label": "Label metrik wajib diisi bila memilih 'Other'."}
            )
        return attrs


class CEAResultSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)

    class Meta:
        model = CEAResult
        fields = [
            "id",
            "input_snapshot",
            "incremental_cost",
            "incremental_effect",
            "icer_value",
            "wtop_threshold_used",
            "dominance",
            "ce_score",
            "sensitivity_low_icer",
            "sensitivity_high_icer",
            "threshold_sensitivity_flag",
            "interpretation_text",
            "algorithm_version",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields
