"""Pre-demo sanity check. Run this 5 minutes before the lecturer demo.

Verifies that the live environment is in the state the demo script expects:
    * All 6 test users exist with their roles attached.
    * All 5 role rows are seeded.
    * Database is reachable.
    * media/ directory is writable.
    * docx2pdf can find MS Word (Windows only — soft warning on other OSs).
    * All migrations are applied — no pending migrations.

Exit code 0 = all green. Exit code 1 = something is off; output explains.

Usage:
    python manage.py demo_preflight
"""

from __future__ import annotations

import sys
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

from apps.accounts.models import Role, RoleSlug

User = get_user_model()


EXPECTED_USERS = {
    "hta@test.local": RoleSlug.HTA_ANALYST,
    "sekre@test.local": RoleSlug.FARMASI_SEKRETARIS,
    "ketua@test.local": RoleSlug.KETUA_KFT,
    "kft1@test.local": RoleSlug.KFT_MEMBER,
    "kft2@test.local": RoleSlug.KFT_MEMBER,
    "adminit@test.local": RoleSlug.ADMIN_IT,
}


class Command(BaseCommand):
    help = "Pre-demo readiness check. Exit 0 if everything is green."

    def handle(self, *args, **options):
        failures: list[str] = []
        warnings: list[str] = []

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== DeciBridge Pre-Demo Checklist ===\n"))

        # 1. Database reachability
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
            self._ok("Database reachable")
        except Exception as exc:
            failures.append(f"Database: {exc}")
            self._fail("Database not reachable")

        # 2. Pending migrations
        try:
            from io import StringIO

            buf = StringIO()
            call_command("showmigrations", "--plan", stdout=buf, no_color=True)
            output = buf.getvalue()
            pending = [line for line in output.splitlines() if line.startswith(" [ ]")]
            if pending:
                failures.append(f"Pending migrations: {len(pending)}")
                self._fail(f"Pending migrations: {len(pending)} (run `python manage.py migrate`)")
            else:
                self._ok("All migrations applied")
        except Exception as exc:
            warnings.append(f"Could not inspect migrations: {exc}")
            self._warn(f"Could not inspect migrations: {exc}")

        # 3. Roles seeded
        role_slugs_present = set(Role.objects.values_list("slug", flat=True))
        expected_slugs = {r.value for r in RoleSlug}
        missing_roles = expected_slugs - role_slugs_present
        if missing_roles:
            failures.append(f"Missing role rows: {sorted(missing_roles)}")
            self._fail(
                f"Missing role rows: {sorted(missing_roles)} (run `python manage.py migrate accounts`)"
            )
        else:
            self._ok(f"All {len(expected_slugs)} roles seeded")

        # 4. Test users exist + have right roles
        for email, expected_role in EXPECTED_USERS.items():
            try:
                u = User.objects.get(email=email)
            except User.DoesNotExist:
                failures.append(f"Missing user: {email}")
                self._fail(f"User missing: {email} (run `python manage.py create_test_users`)")
                continue
            if expected_role.value not in u.role_slugs:
                failures.append(f"{email} missing role {expected_role}")
                self._fail(f"User {email} missing role {expected_role.value}")
            else:
                self._ok(f"User OK: {email} [{expected_role.value}]")

        # 5. media/ writable
        media_root = Path(settings.MEDIA_ROOT)
        try:
            media_root.mkdir(parents=True, exist_ok=True)
            probe = media_root / ".preflight_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            self._ok(f"media/ writable at {media_root}")
        except Exception as exc:
            failures.append(f"media/ not writable: {exc}")
            self._fail(f"media/ not writable: {exc}")

        # 6. docx2pdf availability (Windows only — soft warning elsewhere)
        if sys.platform == "win32":
            try:
                import docx2pdf  # noqa: F401

                self._ok("docx2pdf importable (Word required at runtime for policy briefs)")
            except ImportError as exc:
                failures.append(f"docx2pdf import failed: {exc}")
                self._fail(f"docx2pdf not installed: {exc}")
        else:
            warnings.append("Not on Windows — policy-brief PDF generation will fail until Sprint 12 LibreOffice swap")
            self._warn(
                "Not on Windows — policy-brief PDF generation will need the LibreOffice swap"
            )

        # Summary
        self.stdout.write("")
        if failures:
            self.stdout.write(
                self.style.ERROR(f"FAIL — {len(failures)} issue(s) blocking the demo:")
            )
            for f in failures:
                self.stdout.write(self.style.ERROR(f"  • {f}"))
            sys.exit(1)
        if warnings:
            self.stdout.write(self.style.WARNING(f"WARNING — {len(warnings)} note(s):"))
            for w in warnings:
                self.stdout.write(self.style.WARNING(f"  • {w}"))
        self.stdout.write(self.style.SUCCESS("\nReady for demo."))

    # ── helpers ─────────────────────────────────────────────────────────
    def _ok(self, msg: str) -> None:
        self.stdout.write(self.style.SUCCESS(f"  [OK]   {msg}"))

    def _warn(self, msg: str) -> None:
        self.stdout.write(self.style.WARNING(f"  [WARN] {msg}"))

    def _fail(self, msg: str) -> None:
        self.stdout.write(self.style.ERROR(f"  [FAIL] {msg}"))
