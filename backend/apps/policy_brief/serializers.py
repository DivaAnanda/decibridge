from __future__ import annotations

from rest_framework import serializers

from .models import PolicyBriefDocument


class PolicyBriefDocumentSerializer(serializers.ModelSerializer):
    generated_by_email = serializers.CharField(source="generated_by.email", read_only=True)
    generated_by_name = serializers.SerializerMethodField()
    case_id = serializers.CharField(source="case.case_id", read_only=True)
    docx_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = PolicyBriefDocument
        fields = (
            "id",
            "case_id",
            "version",
            "status",
            "docx_path",
            "pdf_path",
            "docx_url",
            "pdf_url",
            "docx_sha256",
            "pdf_sha256",
            "docx_size_bytes",
            "pdf_size_bytes",
            "error_message",
            "generated_by_email",
            "generated_by_name",
            "generated_at",
            "completed_at",
            "source_recommendation_id",
        )
        read_only_fields = fields  # entire model is read-only via API

    def get_generated_by_name(self, obj: PolicyBriefDocument) -> str:
        user = obj.generated_by
        return user.full_name or user.email

    def get_docx_url(self, obj: PolicyBriefDocument) -> str | None:
        if not obj.docx_path:
            return None
        return f"/api/v1/cases/{obj.case.case_id}/policy-briefs/{obj.pk}/download/docx/"

    def get_pdf_url(self, obj: PolicyBriefDocument) -> str | None:
        if not obj.pdf_path:
            return None
        return f"/api/v1/cases/{obj.case.case_id}/policy-briefs/{obj.pk}/download/pdf/"
