from django.apps import AppConfig


class ETDConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.etd"
    verbose_name = "EtD — Evidence to Decision"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import EtDAppraisal, ReferenceCitation

        register_auditable(EtDAppraisal)
        register_auditable(ReferenceCitation)
