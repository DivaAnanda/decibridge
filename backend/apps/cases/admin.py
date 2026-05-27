from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Case, CaseVersion, DecisionQuestion


class DecisionQuestionInline(admin.TabularInline):
    model = DecisionQuestion
    extra = 0
    fields = ("order", "question_text", "pico_population", "pico_intervention", "pico_comparator", "pico_outcome")


class CaseVersionInline(admin.TabularInline):
    model = CaseVersion
    extra = 0
    can_delete = False
    readonly_fields = ("version_number", "status", "locked_at", "locked_by", "created_at", "created_by")


@admin.register(Case)
class CaseAdmin(SimpleHistoryAdmin):
    list_display = ("case_id", "case_title", "technology", "comparator", "status", "created_by", "created_at")
    list_filter = ("status", "perspective", "created_at")
    search_fields = ("case_id", "case_title", "technology", "comparator", "indication")
    readonly_fields = ("created_by", "created_at", "updated_at")
    inlines = [DecisionQuestionInline, CaseVersionInline]


@admin.register(DecisionQuestion)
class DecisionQuestionAdmin(SimpleHistoryAdmin):
    list_display = ("case", "order", "pico_intervention", "pico_comparator", "pico_outcome")
    list_filter = ("case__status",)
    search_fields = ("case__case_id", "question_text")


@admin.register(CaseVersion)
class CaseVersionAdmin(admin.ModelAdmin):
    list_display = ("case", "version_number", "status", "locked_at", "locked_by", "created_at")
    list_filter = ("status",)
    search_fields = ("case__case_id", "version_number")
    readonly_fields = ("case", "version_number", "status", "locked_at", "locked_by", "lock_reason", "diff", "created_at", "created_by")
