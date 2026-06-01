from django.contrib import admin

from .models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "decision",
        "approver",
        "recommendation",
        "signed_at",
        "ip_address",
    )
    list_filter = ("decision", "signed_at")
    search_fields = ("case__case_id", "approver__email", "reason")
    readonly_fields = tuple(
        f.name for f in Approval._meta.get_fields() if not f.is_relation or f.many_to_one
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
