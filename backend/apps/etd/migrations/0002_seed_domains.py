"""Seed the 9 GRADE EtD domains. Idempotent."""

from django.db import migrations

DOMAINS = [
    {
        "slug": "problem",
        "order": 1,
        "display_name_id": "Masalah (Problem)",
        "display_name_en": "Problem",
        "description": (
            "Apakah masalah kesehatan yang dihadapi cukup penting bagi populasi RS? "
            "Mempertimbangkan prevalensi, beban penyakit, dan keparahan."
        ),
        "prompt_text_id": (
            "Seberapa penting masalah klinis yang diatasi oleh intervensi ini bagi pasien "
            "di rumah sakit Anda?"
        ),
    },
    {
        "slug": "desirable_effects",
        "order": 2,
        "display_name_id": "Efek yang Diinginkan",
        "display_name_en": "Desirable Effects",
        "description": "Seberapa besar manfaat klinis dari intervensi dibandingkan komparator?",
        "prompt_text_id": (
            "Apakah efek yang diinginkan (kemanjuran, peningkatan kualitas hidup, "
            "pengurangan mortalitas) cukup substansial?"
        ),
    },
    {
        "slug": "undesirable_effects",
        "order": 3,
        "display_name_id": "Efek yang Tidak Diinginkan",
        "display_name_en": "Undesirable Effects",
        "description": "Frekuensi dan keparahan efek samping atau dampak negatif intervensi.",
        "prompt_text_id": (
            "Apakah efek yang tidak diinginkan (efek samping, toksisitas) cukup kecil "
            "sehingga manfaat tetap dominan?"
        ),
    },
    {
        "slug": "certainty_of_evidence",
        "order": 4,
        "display_name_id": "Kepastian Bukti",
        "display_name_en": "Certainty of Evidence",
        "description": "Sejauh mana bukti dapat dipercaya — penilaian GRADE.",
        "prompt_text_id": (
            "Apakah Anda yakin bahwa estimasi efek mencerminkan kebenaran di populasi RS Anda?"
        ),
    },
    {
        "slug": "values_preferences",
        "order": 5,
        "display_name_id": "Nilai & Preferensi",
        "display_name_en": "Values and Preferences",
        "description": "Variabilitas nilai pasien terhadap outcome utama.",
        "prompt_text_id": (
            "Apakah ada ketidakpastian penting tentang bagaimana pasien menilai outcome "
            "utama dari intervensi ini?"
        ),
    },
    {
        "slug": "resource_use",
        "order": 6,
        "display_name_id": "Penggunaan Sumber Daya",
        "display_name_en": "Resource Use",
        "description": "Apakah penggunaan sumber daya sesuai — cost-effectiveness, opportunity cost.",
        "prompt_text_id": (
            "Apakah dampak sumber daya (biaya, anggaran, tenaga) sebanding dengan manfaat "
            "klinis yang diperoleh?"
        ),
    },
    {
        "slug": "equity",
        "order": 7,
        "display_name_id": "Ekuitas",
        "display_name_en": "Equity",
        "description": "Dampak terhadap kesetaraan akses dan outcome.",
        "prompt_text_id": (
            "Apakah intervensi ini akan meningkatkan, mempertahankan, atau menurunkan "
            "ekuitas kesehatan di RS Anda?"
        ),
    },
    {
        "slug": "feasibility",
        "order": 8,
        "display_name_id": "Kelayakan Implementasi",
        "display_name_en": "Feasibility",
        "description": "Kemampuan RS mengimplementasikan — pelatihan, supply chain, monitoring.",
        "prompt_text_id": (
            "Apakah intervensi ini layak diimplementasikan di RS Anda dengan sumber daya "
            "dan infrastruktur saat ini?"
        ),
    },
    {
        "slug": "acceptability",
        "order": 9,
        "display_name_id": "Penerimaan oleh Pemangku Kepentingan",
        "display_name_en": "Acceptability",
        "description": "Tingkat penerimaan oleh pasien, dokter, manajemen RS.",
        "prompt_text_id": (
            "Apakah intervensi ini dapat diterima oleh pemangku kepentingan utama "
            "(KFT, klinisi, pasien)?"
        ),
    },
]


def seed_domains(apps, schema_editor):
    EtDDomain = apps.get_model("etd", "EtDDomain")
    for d in DOMAINS:
        EtDDomain.objects.update_or_create(
            slug=d["slug"],
            defaults={
                "order": d["order"],
                "display_name_id": d["display_name_id"],
                "display_name_en": d["display_name_en"],
                "description": d["description"],
                "prompt_text_id": d["prompt_text_id"],
            },
        )


def unseed_domains(apps, schema_editor):
    EtDDomain = apps.get_model("etd", "EtDDomain")
    EtDDomain.objects.filter(slug__in=[d["slug"] for d in DOMAINS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("etd", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_domains, reverse_code=unseed_domains),
    ]
