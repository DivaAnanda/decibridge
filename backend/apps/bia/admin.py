from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import BIAInput, BIAResult


@admin.register(BIAInput)
class BIAInputAdmin(SimpleHistoryAdmin):
    list_display = (
        "case",
        "eligible_population",
        "projection_horizon",
        "unit_cost_drug",
        "unit_cost_comparator",
        "updated_at",
    )
    search_fields = ("case__case_id", "case__case_title")
    readonly_fields = ("created_at", "updated_at", "created_by", "last_edited_by")


@admin.register(BIAResult)
class BIAResultAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "severity",
        "direction",
        "cumulative_impact",
        "pct_of_annual_budget",
        "budget_score",
        "computed_at",
    )
    list_filter = ("severity", "direction", "computed_at")
    search_fields = ("case__case_id",)
    readonly_fields = tuple(
        f.name for f in BIAResult._meta.get_fields() if not f.is_relation or f.many_to_one
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
