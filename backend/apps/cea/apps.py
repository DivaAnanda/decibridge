from django.apps import AppConfig


class CEAConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cea"
    verbose_name = "CEA Quick"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import CEAInput, CEAResult

        register_auditable(CEAInput)
        register_auditable(CEAResult)
