"""Idempotently provision the six demo accounts used in the verification scripts.

Usage:
    python manage.py create_test_users

Creates (or updates) the following accounts with password TestPass123!:
    hta@test.local       — HTA Analyst / Pharmacoeconomist
    sekre@test.local     — Hospital Pharmacy / KFT Secretariat
    ketua@test.local     — KFT Chair / Approver
    kft1@test.local      — KFT Member
    kft2@test.local      — KFT Member
    adminit@test.local   — IT Administrator

Re-running is safe — existing users get their role attached if missing, password
re-set if --reset-password is passed.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Role, RoleSlug


User = get_user_model()


TEST_USERS = [
    {
        "email": "hta@test.local",
        "full_name": "Dr. Andini Hartono",
        "role": RoleSlug.HTA_ANALYST,
    },
    {
        "email": "sekre@test.local",
        "full_name": "Apt. Rina Wibowo",
        "role": RoleSlug.FARMASI_SEKRETARIS,
    },
    {
        "email": "ketua@test.local",
        "full_name": "Dr. Bambang Sutrisno, Sp.JP",
        "role": RoleSlug.KETUA_KFT,
    },
    {
        "email": "kft1@test.local",
        "full_name": "dr. Indah Permata, Sp.JP",
        "role": RoleSlug.KFT_MEMBER,
    },
    {
        "email": "kft2@test.local",
        "full_name": "Dr. Joko Mahendra, Sp.PD",
        "role": RoleSlug.KFT_MEMBER,
    },
    {
        "email": "adminit@test.local",
        "full_name": "Putri Larasati (IT)",
        "role": RoleSlug.ADMIN_IT,
    },
]

PASSWORD = "TestPass123!"


class Command(BaseCommand):
    help = "Create or update the six demo test accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Force-reset the password on existing accounts.",
        )

    def handle(self, *args, **options):
        reset_password = options["reset_password"]
        roles_by_slug = {r.slug: r for r in Role.objects.select_related("group")}

        created_count = 0
        updated_count = 0

        for cfg in TEST_USERS:
            role = roles_by_slug.get(cfg["role"])
            if role is None:
                self.stderr.write(
                    self.style.WARNING(
                        f"Role '{cfg['role']}' not seeded. Run migrations first."
                    )
                )
                continue

            user, created = User.objects.get_or_create(
                email=cfg["email"],
                defaults={
                    "full_name": cfg["full_name"],
                    "is_active": True,
                },
            )

            if created or reset_password:
                user.set_password(PASSWORD)
                user.save(update_fields=["password"] if not created else None)

            # Attach the role group if missing.
            if not user.groups.filter(pk=role.group_id).exists():
                user.groups.add(role.group)

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  + created {cfg['email']} [{cfg['role']}]"))
            else:
                updated_count += 1
                self.stdout.write(f"  · ensured  {cfg['email']} [{cfg['role']}]")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. {created_count} created, {updated_count} verified. "
                f"All accounts use password: {PASSWORD}"
            )
        )
