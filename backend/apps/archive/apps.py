from django.apps import AppConfig


class ArchiveConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.archive"
    verbose_name = "Long-Term Archive"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import ArchiveRecord

        register_auditable(ArchiveRecord)
