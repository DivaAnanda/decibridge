from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.approval"
    verbose_name = "Approval & Sign-Off"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import Approval

        register_auditable(Approval)
