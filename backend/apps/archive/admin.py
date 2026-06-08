from __future__ import annotations

from django.contrib import admin

from .models import ArchiveRecord


@admin.register(ArchiveRecord)
class ArchiveRecordAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "archived_at",
        "archived_by",
        "retention_until",
        "manifest_sha256_short",
    )
    list_filter = ("archived_at",)
    search_fields = ("case__case_id", "manifest_sha256")
    ordering = ("-archived_at",)
    readonly_fields = tuple(
        f.name for f in ArchiveRecord._meta.fields if f.name != "id"
    ) + ("manifest_sha256_short",)

    def manifest_sha256_short(self, obj: ArchiveRecord) -> str:
        return obj.manifest_sha256[:12] if obj.manifest_sha256 else "—"

    manifest_sha256_short.short_description = "Manifest SHA"  # type: ignore[attr-defined]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
