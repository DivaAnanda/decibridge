"""Seed the economic model + parameters for the lecturer's validation case.

Idempotent: re-running updates values in place. Populates HF_ARNI_ACEI_001 with
the verified illustrative parameter set (see apps/econ/validation_fixtures.py)
that reproduces the acceptance table exactly.

    python manage.py seed_econ_validation_case
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import RoleSlug
from apps.cases.models import Case
from apps.econ.models import EconomicModel, EconomicParameter
from apps.econ.validation_fixtures import (
    MODEL_SCALARS,
    VALIDATION_CASE_ID,
    VALIDATION_PARAMETERS,
)

User = get_user_model()


def _seed_user() -> User:
    hta = User.objects.filter(groups__name=RoleSlug.HTA_ANALYST.value).first()
    return hta or User.objects.filter(is_superuser=True).first() or User.objects.first()


class Command(BaseCommand):
    help = "Seed the economic model + parameters for HF_ARNI_ACEI_001."

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            case = Case.objects.get(case_id=VALIDATION_CASE_ID)
        except Case.DoesNotExist as exc:
            raise CommandError(
                f"Case {VALIDATION_CASE_ID} not found. Create it first."
            ) from exc

        actor = _seed_user()
        if actor is None:
            raise CommandError("No users exist to attribute the seed to.")

        model = EconomicModel.objects.filter(case=case).first()
        created = model is None
        if created:
            model = EconomicModel.objects.create(case=case, created_by=actor, **MODEL_SCALARS)
        else:
            for key, value in MODEL_SCALARS.items():
                setattr(model, key, value)
            model.last_edited_by = actor
            model.save()

        count = 0
        for spec in VALIDATION_PARAMETERS:
            EconomicParameter.objects.update_or_create(
                economic_model=model,
                key=spec["key"],
                alternative=spec["alternative"],
                year_index=None,
                defaults={
                    "value": spec["value"],
                    "param_type": spec["param_type"],
                    "unit": spec.get("unit", ""),
                    "data_status": spec["data_status"],
                    "source_reference": spec.get("source_reference", ""),
                    "distribution": spec.get("distribution", "fixed"),
                    "dist_param1": spec.get("dist_param1"),
                    "dist_param2": spec.get("dist_param2"),
                    "last_edited_by": actor,
                    "created_by": actor,
                },
            )
            count += 1

        # Prune parameters that are no longer part of the validation set.
        # Without this a stale row (e.g. an old market_share=0.5) silently keeps
        # feeding the engines and halves the budget-impact scenarios.
        keep = {(str(s["key"]), str(s["alternative"]), None) for s in VALIDATION_PARAMETERS}
        removed = 0
        for param in list(model.parameters.all()):
            if (param.key, param.alternative, param.year_index) not in keep:
                param.delete()
                removed += 1

        verb = "Created" if created else "Updated"
        suffix = f" ({removed} parameter usang dihapus)" if removed else ""
        self.stdout.write(self.style.SUCCESS(
            f"{verb} economic model for {VALIDATION_CASE_ID} with {count} parameters{suffix}."
        ))
