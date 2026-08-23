"""Write the economic-validation workbook (.xlsx) to disk.

    python manage.py export_validation_workbook [path]

Default path: DeciBridge_Economic_Validation_Model.xlsx in the current directory.
Doubles as the template the lecturer's real workbook can be diffed against.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.econ.validation_workbook import build_workbook


class Command(BaseCommand):
    help = "Export the economic-validation workbook to an .xlsx file."

    def add_arguments(self, parser):
        parser.add_argument(
            "path", nargs="?", default="DeciBridge_Economic_Validation_Model.xlsx"
        )

    def handle(self, *args, **options):
        path = options["path"]
        build_workbook().save(path)
        self.stdout.write(self.style.SUCCESS(f"Wrote validation workbook to {path}"))
