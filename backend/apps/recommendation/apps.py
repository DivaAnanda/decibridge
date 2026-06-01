from django.apps import AppConfig


class RecommendationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recommendation"
    verbose_name = "Recommendation Synthesis"

    def ready(self) -> None:
        from apps.audit.signals import register_auditable

        from .models import CBACriterion, DomainWeightVote, Recommendation

        register_auditable(DomainWeightVote)
        register_auditable(CBACriterion)
        register_auditable(Recommendation)
