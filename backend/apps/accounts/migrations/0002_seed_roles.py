"""Seed the 5 canonical roles (and their backing Django Groups).

Idempotent: safe to re-run. Permissions for each role are NOT assigned here
— they're assigned per-app as those apps come online (cases, intake, etc.).
"""

from django.db import migrations

ROLES = [
    {
        "slug": "admin_it",
        "display_name_id": "Admin IT",
        "display_name_en": "IT Administrator",
        "description": (
            "Manages users and system configuration. NOT permitted to alter "
            "clinical judgements or EtD appraisals."
        ),
    },
    {
        "slug": "hta_analyst",
        "display_name_id": "Analis HTA / Farmakoekonomi",
        "display_name_en": "HTA Analyst / Pharmacoeconomist",
        "description": (
            "Uploads cases, runs CEA/BIA, edits EtD appraisals. NOT permitted "
            "to lock final decisions."
        ),
    },
    {
        "slug": "farmasi_sekretaris",
        "display_name_id": "Farmasi RS / Sekretaris KFT",
        "display_name_en": "Hospital Pharmacy / KFT Secretariat",
        "description": "Manages case lifecycle, edits local inputs, defines CBA criteria.",
    },
    {
        "slug": "kft_member",
        "display_name_id": "Anggota KFT",
        "display_name_en": "KFT Member",
        "description": "Votes on EtD domains; assigns institutional weights.",
    },
    {
        "slug": "ketua_kft",
        "display_name_id": "Ketua KFT / Approver",
        "display_name_en": "KFT Chair / Approver",
        "description": "Sole authority to approve and lock final formulary decisions.",
    },
]


def seed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Role = apps.get_model("accounts", "Role")
    for entry in ROLES:
        group, _ = Group.objects.get_or_create(name=entry["display_name_en"])
        Role.objects.update_or_create(
            slug=entry["slug"],
            defaults={
                "display_name_id": entry["display_name_id"],
                "display_name_en": entry["display_name_en"],
                "description": entry["description"],
                "group": group,
            },
        )


def unseed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Group = apps.get_model("auth", "Group")
    slugs = [r["slug"] for r in ROLES]
    group_names = [r["display_name_en"] for r in ROLES]
    Role.objects.filter(slug__in=slugs).delete()
    Group.objects.filter(name__in=group_names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, reverse_code=unseed_roles),
    ]
