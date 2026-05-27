from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Case, CaseVersion, DecisionQuestion, validate_case_id
from .state_machine import allowed_transitions_for


class DecisionQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionQuestion
        fields = [
            "id",
            "order",
            "question_text",
            "pico_population",
            "pico_intervention",
            "pico_comparator",
            "pico_outcome",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CaseVersionSerializer(serializers.ModelSerializer):
    locked_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = CaseVersion
        fields = [
            "id",
            "version_number",
            "status",
            "locked_at",
            "locked_by",
            "lock_reason",
            "diff",
            "created_at",
            "created_by",
        ]
        read_only_fields = fields


class CaseListSerializer(serializers.ModelSerializer):
    """Slim payload for the dashboard list view."""

    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "case_id",
            "case_title",
            "technology",
            "comparator",
            "indication",
            "status",
            "perspective",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CaseDetailSerializer(serializers.ModelSerializer):
    decision_questions = DecisionQuestionSerializer(many=True, read_only=True)
    versions = CaseVersionSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    allowed_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "case_id",
            "case_title",
            "technology",
            "comparator",
            "indication",
            "population",
            "setting",
            "perspective",
            "status",
            "is_editable",
            "is_locked",
            "decision_questions",
            "versions",
            "created_by",
            "created_at",
            "updated_at",
            "allowed_transitions",
        ]
        read_only_fields = [
            "id",
            "status",
            "is_editable",
            "is_locked",
            "decision_questions",
            "versions",
            "created_by",
            "created_at",
            "updated_at",
            "allowed_transitions",
        ]

    def get_allowed_transitions(self, obj: Case) -> list[dict]:
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return []
        return [
            {
                "name": t.name,
                "target": t.target,
                "requires_reason": t.requires_reason,
            }
            for t in allowed_transitions_for(obj, request.user)
        ]


class CaseCreateSerializer(serializers.ModelSerializer):
    """Create-only serializer with PICO question optional in same request."""

    decision_question = DecisionQuestionSerializer(required=False, write_only=True)

    class Meta:
        model = Case
        fields = [
            "case_id",
            "case_title",
            "technology",
            "comparator",
            "indication",
            "population",
            "setting",
            "perspective",
            "decision_question",
        ]

    def validate_case_id(self, value: str) -> str:
        validate_case_id(value)
        return value

    def create(self, validated_data: dict) -> Case:
        question_data = validated_data.pop("decision_question", None)
        case = Case.objects.create(
            created_by=self.context["request"].user,
            **validated_data,
        )
        CaseVersion.objects.create(
            case=case,
            version_number="0.1.0",
            created_by=self.context["request"].user,
        )
        if question_data:
            DecisionQuestion.objects.create(case=case, order=1, **question_data)
        return case


class TransitionSerializer(serializers.Serializer):
    action = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")
