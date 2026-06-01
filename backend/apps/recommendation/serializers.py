from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import CBACriterion, DomainWeightVote, Recommendation, TrafficLight


class DomainWeightVoteReadSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    domain_slug = serializers.CharField(source="domain.slug", read_only=True)

    class Meta:
        model = DomainWeightVote
        fields = ["id", "case", "domain", "domain_slug", "member", "weight", "created_at", "updated_at"]
        read_only_fields = fields


class DomainWeightUpsertSerializer(serializers.Serializer):
    """Bulk upsert: caller submits {domain_slug: weight} for all 9 domains."""

    weights = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=100),
        help_text="{domain_slug: 0-100}",
    )


class CBACriterionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    last_edited_by = UserSerializer(read_only=True)

    class Meta:
        model = CBACriterion
        fields = [
            "id",
            "order",
            "criterion_name",
            "field_reference",
            "operator",
            "expected_value",
            "description",
            "is_satisfied",
            "created_by",
            "last_edited_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "last_edited_by", "created_at", "updated_at"]


class RecommendationSerializer(serializers.ModelSerializer):
    computed_by = UserSerializer(read_only=True)
    traffic_light_label = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "input_snapshot",
            "evidence_strength_score",
            "ce_score",
            "budget_score",
            "cba_score",
            "composite_score",
            "traffic_light",
            "traffic_light_label",
            "justification_text",
            "cba_criteria_count",
            "cba_satisfied_count",
            "algorithm_version",
            "weight_aggregation_method",
            "computed_at",
            "computed_by",
        ]
        read_only_fields = fields

    def get_traffic_light_label(self, obj: Recommendation) -> str:
        return TrafficLight(obj.traffic_light).label


class WeightAggregateSerializer(serializers.Serializer):
    domain_slug = serializers.CharField()
    vote_count = serializers.IntegerField()
    mean_weight = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    median_weight = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    chosen_weight = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    normalized_weight = serializers.DecimalField(max_digits=6, decimal_places=4, allow_null=True)


class WeightsSummarySerializer(serializers.Serializer):
    method = serializers.CharField()
    aggregates = WeightAggregateSerializer(many=True)
