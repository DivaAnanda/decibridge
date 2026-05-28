from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import EtDAppraisal, EtDDomain, ReferenceCitation


@admin.register(EtDDomain)
class EtDDomainAdmin(admin.ModelAdmin):
    list_display = ("order", "slug", "display_name_id", "display_name_en")
    ordering = ("order",)
    readonly_fields = ("slug",)

    def has_add_permission(self, request) -> bool:
        return False  # seeded only

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(ReferenceCitation)
class ReferenceCitationAdmin(SimpleHistoryAdmin):
    list_display = ("case", "reference_type", "publication_year", "authors", "title")
    list_filter = ("reference_type", "publication_year")
    search_fields = ("case__case_id", "authors", "title", "doi_pmid")
    readonly_fields = ("created_at", "created_by")


@admin.register(EtDAppraisal)
class EtDAppraisalAdmin(SimpleHistoryAdmin):
    list_display = ("case", "domain", "member", "judgement", "certainty", "updated_at")
    list_filter = ("domain", "certainty")
    search_fields = ("case__case_id", "member__email", "narrative")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("case", "member", "references")
