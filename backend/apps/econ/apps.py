from django.apps import AppConfig


class EconConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.econ"
    verbose_name = "Economic Model (HTA)"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import (
            EconBIAResult,
            EconDeterministicResult,
            EconomicModel,
            EconomicParameter,
            EconPSAResult,
        )

        register_auditable(EconomicModel)
        register_auditable(EconomicParameter)
        register_auditable(EconDeterministicResult)
        register_auditable(EconBIAResult)
        register_auditable(EconPSAResult)
