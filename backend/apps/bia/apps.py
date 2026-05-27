from django.apps import AppConfig


class BIAConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bia"
    verbose_name = "BIA — Budget Impact Analysis"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import BIAInput, BIAResult

        register_auditable(BIAInput)
        register_auditable(BIAResult)
