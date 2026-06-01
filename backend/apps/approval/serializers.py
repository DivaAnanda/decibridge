from __future__ import annotations

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Approval, ApprovalDecision


class ApprovalReadSerializer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)
    decision_label = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = [
            "id",
            "case",
            "recommendation",
            "approver",
            "decision",
            "decision_label",
            "confirmation_acknowledged",
            "password_verified_at",
            "reason",
            "signed_at",
            "ip_address",
            "user_agent",
        ]
        read_only_fields = fields

    def get_decision_label(self, obj: Approval) -> str:
        return ApprovalDecision(obj.decision).label


class SignRequestSerializer(serializers.Serializer):
    """Payload for the sign endpoint. Server still has to validate the
    password against request.user via check_password()."""

    recommendation_id = serializers.IntegerField()
    decision = serializers.ChoiceField(choices=ApprovalDecision.choices)
    confirmation_acknowledged = serializers.BooleanField()
    password = serializers.CharField(write_only=True)
    reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_confirmation_acknowledged(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError(
                "Anda harus mencentang konfirmasi sebelum tanda tangan."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        decision = attrs["decision"]
        reason = attrs.get("reason", "").strip()
        if decision in {
            ApprovalDecision.REJECTED.value,
            ApprovalDecision.REVISION_REQUESTED.value,
        } and not reason:
            raise serializers.ValidationError(
                {"reason": "Alasan wajib diisi untuk penolakan atau permintaan revisi."}
            )
        return attrs
