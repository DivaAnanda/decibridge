from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import EconomicModel, EconomicParameter


class EconomicParameterInline(admin.TabularInline):
    model = EconomicParameter
    extra = 0
    fields = (
        "key",
        "alternative",
        "year_index",
        "value",
        "unit",
        "param_type",
        "data_status",
        "source_year",
        "version",
    )
    readonly_fields = ("version",)


@admin.register(EconomicModel)
class EconomicModelAdmin(SimpleHistoryAdmin):
    list_display = (
        "case",
        "horizon_years",
        "cost_discount_rate",
        "outcome_discount_rate",
        "wtp_threshold",
        "updated_at",
    )
    search_fields = ("case__case_id", "case__case_title")
    readonly_fields = ("created_at", "updated_at", "created_by", "last_edited_by")
    inlines = [EconomicParameterInline]


@admin.register(EconomicParameter)
class EconomicParameterAdmin(SimpleHistoryAdmin):
    list_display = (
        "economic_model",
        "key",
        "alternative",
        "year_index",
        "value",
        "param_type",
        "data_status",
        "version",
        "updated_at",
    )
    list_filter = ("param_type", "data_status", "alternative")
    search_fields = ("economic_model__case__case_id", "key", "label")
    readonly_fields = ("version", "created_at", "updated_at", "created_by", "last_edited_by")
