from django.apps import AppConfig


class PolicyBriefConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.policy_brief"
    verbose_name = "Policy Brief — DOCX/PDF Export"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import PolicyBriefDocument

        register_auditable(PolicyBriefDocument)
