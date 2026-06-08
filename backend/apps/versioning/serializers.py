from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import AuditLog
from apps.cases.models import CaseVersion


class CaseVersionListSerializer(serializers.ModelSerializer):
    locked_by_name = serializers.SerializerMethodField()
    locked_by_email = serializers.CharField(source="locked_by.email", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    trigger_label = serializers.CharField(source="get_trigger_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CaseVersion
        fields = (
            "id",
            "version_number",
            "status",
            "status_label",
            "trigger",
            "trigger_label",
            "locked_at",
            "locked_by_name",
            "locked_by_email",
            "lock_reason",
            "created_at",
            "created_by_name",
            "cea_result_id",
            "bia_result_id",
            "recommendation_id",
            "approval_id",
            "policy_brief_document_id",
        )
        read_only_fields = fields

    def get_locked_by_name(self, obj: CaseVersion) -> str | None:
        if obj.locked_by is None:
            return None
        return obj.locked_by.full_name or obj.locked_by.email

    def get_created_by_name(self, obj: CaseVersion) -> str:
        u = obj.created_by
        return u.full_name or u.email


class AuditLogEntrySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.CharField(source="actor.email", read_only=True, default="")
    action_label = serializers.CharField(source="get_action_display", read_only=True)
    target_label = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "created_at",
            "action",
            "action_label",
            "actor_name",
            "actor_email",
            "target_label",
            "target_object_id",
            "diff",
            "metadata",
            "ip_address",
        )
        read_only_fields = fields

    def get_actor_name(self, obj: AuditLog) -> str:
        if obj.actor is None:
            return "(sistem)"
        return obj.actor.full_name or obj.actor.email

    def get_target_label(self, obj: AuditLog) -> str:
        if obj.target_content_type and obj.target_object_id:
            return f"{obj.target_content_type.model} #{obj.target_object_id}"
        return ""
