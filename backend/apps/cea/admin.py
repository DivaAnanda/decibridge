from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import CEAInput, CEAResult


@admin.register(CEAInput)
class CEAInputAdmin(SimpleHistoryAdmin):
    list_display = (
        "case",
        "drug_cost_per_unit",
        "comparator_cost_per_unit",
        "drug_efficacy_value",
        "comparator_efficacy_value",
        "wtop_threshold",
        "updated_at",
    )
    search_fields = ("case__case_id", "case__case_title")
    readonly_fields = ("created_at", "updated_at", "created_by", "last_edited_by")


@admin.register(CEAResult)
class CEAResultAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "icer_value",
        "dominance",
        "ce_score",
        "threshold_sensitivity_flag",
        "computed_at",
        "computed_by",
    )
    list_filter = ("dominance", "threshold_sensitivity_flag", "computed_at")
    search_fields = ("case__case_id",)
    readonly_fields = tuple(f.name for f in CEAResult._meta.get_fields() if not f.is_relation or f.many_to_one)

    def has_add_permission(self, request) -> bool:
        return False  # results only created via the compute endpoint

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
