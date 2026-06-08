from __future__ import annotations

from django.contrib import admin

from .models import PolicyBriefDocument


@admin.register(PolicyBriefDocument)
class PolicyBriefDocumentAdmin(admin.ModelAdmin):
    """Read-only admin — PolicyBriefDocument is append-only at the model layer.

    Listing is allowed (for audit visibility) but edit + delete actions are
    suppressed entirely so admins cannot tamper with the artifact registry.
    """

    list_display = (
        "case",
        "version",
        "status",
        "generated_by",
        "generated_at",
        "docx_sha256_short",
        "pdf_sha256_short",
    )
    list_filter = ("status", "case__case_id")
    search_fields = ("case__case_id", "docx_sha256", "pdf_sha256")
    ordering = ("-generated_at",)
    readonly_fields = tuple(
        f.name for f in PolicyBriefDocument._meta.fields if f.name != "id"
    ) + ("docx_sha256_short", "pdf_sha256_short")

    def docx_sha256_short(self, obj: PolicyBriefDocument) -> str:
        return obj.docx_sha256[:12] if obj.docx_sha256 else "—"

    docx_sha256_short.short_description = "DOCX SHA"  # type: ignore[attr-defined]

    def pdf_sha256_short(self, obj: PolicyBriefDocument) -> str:
        return obj.pdf_sha256[:12] if obj.pdf_sha256 else "—"

    pdf_sha256_short.short_description = "PDF SHA"  # type: ignore[attr-defined]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
