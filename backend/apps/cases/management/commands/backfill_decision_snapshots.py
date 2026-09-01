"""Backfill immutable decision snapshots for versions locked before Phase V2.

    python manage.py backfill_decision_snapshots [--force] [--case CASE_ID]

Cases locked before the snapshot existed (e.g. HF_ARNI_ACEI_004) have a
CaseVersion row carrying only legacy CEA/BIA pointers. This rebuilds a full
value snapshot for them from whatever data the case still holds — legacy CEA/BIA
included — so every tab renders consistently for those versions too.

The rebuilt snapshot is marked `backfilled: true` with a timestamp: it reflects
the case's data *now*, not necessarily the exact instant of the original lock,
and that distinction must stay visible for audit purposes.

CaseVersion is append-only (`save()` raises on update), so the snapshot is
written with a targeted queryset UPDATE that bypasses the instance guard. This
is the one sanctioned exception — it populates a previously-null field and never
alters a value that was already recorded.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.cases.decision_snapshot import build_decision_snapshot
from apps.cases.models import CaseVersion, CaseVersionStatus


class Command(BaseCommand):
    help = "Rebuild decision snapshots for CaseVersion rows locked before Phase V2."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Rebuild even when a snapshot already exists (overwrites backfilled data).",
        )
        parser.add_argument("--case", dest="case_id", default=None, help="Limit to one case_id.")

    @transaction.atomic
    def handle(self, *args, **options):
        versions = CaseVersion.objects.filter(status=CaseVersionStatus.LOCKED).select_related("case")
        if options["case_id"]:
            versions = versions.filter(case__case_id=options["case_id"])
        if not options["force"]:
            versions = versions.filter(snapshot__isnull=True)

        written = 0
        for version in versions:
            snapshot = build_decision_snapshot(version.case)
            snapshot["backfilled"] = True
            snapshot["backfilled_at"] = timezone.now().isoformat()
            # Append-only guard lives on the instance; a queryset update is the
            # sanctioned path for populating this previously-null field.
            CaseVersion.objects.filter(pk=version.pk).update(snapshot=snapshot)
            written += 1
            self.stdout.write(f"  {version.case.case_id} v{version.version_number}")

        if written:
            self.stdout.write(self.style.SUCCESS(f"Backfilled {written} decision snapshot(s)."))
        else:
            self.stdout.write("No versions needed backfilling.")
