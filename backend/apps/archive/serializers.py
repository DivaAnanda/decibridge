from __future__ import annotations

from rest_framework import serializers

from .models import ArchiveRecord


class ArchiveRecordSerializer(serializers.ModelSerializer):
    case_id = serializers.CharField(source="case.case_id", read_only=True)
    archived_by_name = serializers.SerializerMethodField()
    archived_by_email = serializers.CharField(
        source="archived_by.email", read_only=True
    )
    manifest_url = serializers.SerializerMethodField()

    class Meta:
        model = ArchiveRecord
        fields = (
            "id",
            "case_id",
            "archived_at",
            "archived_by_name",
            "archived_by_email",
            "manifest_path",
            "manifest_url",
            "manifest_sha256",
            "manifest_size_bytes",
            "retention_until",
            "notes",
            "artifact_counts",
        )
        read_only_fields = fields

    def get_archived_by_name(self, obj: ArchiveRecord) -> str:
        u = obj.archived_by
        return u.full_name or u.email

    def get_manifest_url(self, obj: ArchiveRecord) -> str:
        return f"/api/v1/cases/{obj.case.case_id}/archive/manifest/"
