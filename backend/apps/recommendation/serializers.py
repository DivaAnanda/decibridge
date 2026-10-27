from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import (
    CBACriterion,
    DomainWeightVote,
    FinalDecision,
    FinalDecisionType,
    Recommendation,
    TrafficLight,
)


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


class FinalDecisionSerializer(serializers.ModelSerializer):
    decision_label = serializers.CharField(source="get_decision_display", read_only=True)
    decided_by_name = serializers.SerializerMethodField()
    recommendation_id = serializers.IntegerField(read_only=True)
    recommendation_traffic_light = serializers.CharField(
        source="recommendation.traffic_light", read_only=True
    )
    recommendation_composite_score = serializers.DecimalField(
        source="recommendation.composite_score", max_digits=6, decimal_places=2, read_only=True
    )
    matches_latest_recommendation = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = FinalDecision
        fields = [
            "id",
            "decision",
            "decision_label",
            "reason",
            "decided_by_name",
            "decided_at",
            "recommendation_id",
            "recommendation_traffic_light",
            "recommendation_composite_score",
            "matches_latest_recommendation",
            "is_current",
        ]
        read_only_fields = fields

    def get_decided_by_name(self, obj: FinalDecision) -> str:
        return obj.decided_by.full_name or obj.decided_by.email

    def get_matches_latest_recommendation(self, obj: FinalDecision) -> bool:
        if "latest_recommendation_id" in self.context:
            latest_id = self.context["latest_recommendation_id"]
        else:
            latest = obj.case.recommendations.order_by("-computed_at").first()
            latest_id = latest.pk if latest else None
        return obj.recommendation_id == latest_id

    def get_is_current(self, obj: FinalDecision) -> bool:
        """What the sign-off gate accepts: on the latest recommendation, and recorded
        for the version now open (round 5 item 4)."""
        if "revision_start" in self.context:
            since = self.context["revision_start"]
        else:
            from apps.cases.completeness import _revision_start

            since = _revision_start(obj.case)
        recorded_for_this_version = since is None or obj.decided_at >= since
        return self.get_matches_latest_recommendation(obj) and recorded_for_this_version


class FinalDecisionCreateSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=FinalDecisionType.choices)
    reason = serializers.CharField(
        trim_whitespace=True,
        error_messages={"blank": "Alasan keputusan final wajib diisi."},
    )
