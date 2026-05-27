from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cases"
    verbose_name = "Cases"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import Case, CaseVersion, DecisionQuestion

        register_auditable(Case)
        register_auditable(CaseVersion)
        register_auditable(DecisionQuestion)
