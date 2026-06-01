from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import CBACriterion, DomainWeightVote, Recommendation


@admin.register(DomainWeightVote)
class DomainWeightVoteAdmin(SimpleHistoryAdmin):
    list_display = ("case", "domain", "member", "weight", "updated_at")
    list_filter = ("domain",)
    search_fields = ("case__case_id", "member__email")


@admin.register(CBACriterion)
class CBACriterionAdmin(SimpleHistoryAdmin):
    list_display = ("case", "order", "criterion_name", "operator", "is_satisfied", "updated_at")
    list_filter = ("operator", "is_satisfied")
    search_fields = ("case__case_id", "criterion_name")
    readonly_fields = ("created_at", "updated_at", "created_by", "last_edited_by")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "traffic_light",
        "composite_score",
        "cba_satisfied_count",
        "cba_criteria_count",
        "computed_at",
        "computed_by",
    )
    list_filter = ("traffic_light", "computed_at")
    search_fields = ("case__case_id",)
    readonly_fields = tuple(
        f.name for f in Recommendation._meta.get_fields() if not f.is_relation or f.many_to_one
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
