"""Re-hash archived documents and report any that no longer match.

Round 4 item 7. Run with no arguments to check every locked/archived case, or
--case-id to check one.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.archive.verification import verify_case_documents
from apps.cases.models import Case, CaseStatus


class Command(BaseCommand):
    help = "Verify that archived policy brief files still match their recorded hashes."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--case-id", default=None, help="Check a single case.")

    def handle(self, *args, **options) -> None:
        cases = Case.objects.filter(
            status__in=(CaseStatus.LOCKED, CaseStatus.ARCHIVED)
        ).order_by("case_id")
        if options["case_id"]:
            cases = cases.filter(case_id=options["case_id"])

        checked = 0
        tampered = 0

        for case in cases:
            report = verify_case_documents(case)
            if not report.checks:
                continue
            checked += 1
            if report.is_intact:
                self.stdout.write(
                    self.style.SUCCESS(f"{case.case_id}: {len(report.checks)} berkas utuh")
                )
                continue
            tampered += 1
            for failure in report.failures:
                self.stdout.write(
                    self.style.ERROR(
                        f"{case.case_id}: {failure.label} - {failure.status}"
                    )
                )

        self.stdout.write(f"Diperiksa {checked} kasus; {tampered} bermasalah.")
