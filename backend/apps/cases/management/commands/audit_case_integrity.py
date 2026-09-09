"""Stamp locked/archived cases that fail the archival integrity check.

Round 3. `HF_ARNI_ACEI_004` was locked before the completeness gate existed and
presents a GREEN verdict with no CEA, no BIA and 4 of 9 EtD domains. The lecturer
asked for it to be kept as a regression fixture, so it is flagged rather than
removed:

    "mohon jangan hapus HF_ARNI_ACEI_004, karena kasus ini akan digunakan kembali
     sebagai regression test"

Safe to re-run: it recomputes the flag from current data every time, so a case
that is later remediated is cleared automatically.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.cases.integrity import evaluate_integrity
from apps.cases.models import Case, CaseStatus, IntegrityFlag

AUDITED_STATUSES = (CaseStatus.LOCKED, CaseStatus.ARCHIVED)


class Command(BaseCommand):
    help = "Run the archival integrity check over locked/archived cases and flag failures."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing.",
        )
        parser.add_argument(
            "--case-id",
            default=None,
            help="Audit a single case instead of every locked/archived one.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        case_id: str | None = options["case_id"]

        cases = Case.objects.filter(status__in=AUDITED_STATUSES).order_by("case_id")
        if case_id:
            cases = cases.filter(case_id=case_id)

        if not cases.exists():
            self.stdout.write("No locked or archived cases to audit.")
            return

        flagged = 0
        cleared = 0

        for case in cases:
            report = evaluate_integrity(case)
            new_flag = (
                IntegrityFlag.OK
                if report["is_valid"]
                else IntegrityFlag.REQUIRES_REMEDIATION
            )
            notes = "" if report["is_valid"] else "; ".join(report["failures"])

            if report["is_valid"]:
                if case.integrity_flag != IntegrityFlag.OK:
                    cleared += 1
                    self.stdout.write(self.style.SUCCESS(f"{case.case_id}: cleared"))
            else:
                flagged += 1
                self.stdout.write(
                    self.style.WARNING(f"{case.case_id}: {new_flag} — {notes}")
                )

            if dry_run:
                continue

            # `.update()` bypasses the model save path so the audit never counts
            # as a user edit to a locked case.
            with transaction.atomic():
                Case.objects.filter(pk=case.pk).update(
                    integrity_flag=new_flag,
                    integrity_notes=notes,
                    integrity_checked_at=timezone.now(),
                )

        suffix = " (dry run — nothing written)" if dry_run else ""
        self.stdout.write(
            f"Audited {cases.count()} case(s): {flagged} flagged, {cleared} cleared{suffix}."
        )
