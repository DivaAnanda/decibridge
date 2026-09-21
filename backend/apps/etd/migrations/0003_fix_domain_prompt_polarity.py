"""Make every domain prompt point the same way as the score.

Round 4 item 6:

    "Periksa khusus arah penilaian domain 'Nilai & Preferensi': jawaban 'Ya'
     terhadap adanya ketidakpastian tidak boleh otomatis diperlakukan sebagai
     dukungan positif tanpa aturan yang jelas."

The judgement scale is directional -- Tidak=0 ... Ya=100 -- and the aggregate
treats a higher number as more favourable to adoption. Three prompts did not
match that convention:

* values_preferences asked whether important uncertainty EXISTS, so "Ya" (100)
  recorded a reason against adoption as maximum support. Straightforwardly
  inverted, and the one the lecturer spotted.
* equity asked whether the intervention would "increase, maintain, or decrease"
  equity -- a three-way question with no meaningful yes/no answer, so whatever
  the member picked scored arbitrarily.
* problem asked "how important", a magnitude question, on a yes/no scale.

Rewritten so "Ya" always means favourable. Existing appraisals are left alone:
they were recorded against the old wording and silently re-pointing them would
change what a member said. Re-appraisal is a human decision, and the case list
shows which cases predate this migration.
"""

from __future__ import annotations

from django.db import migrations

NEW_PROMPTS = {
    "problem": (
        "Apakah masalah klinis yang diatasi intervensi ini merupakan prioritas "
        "di rumah sakit Anda?"
    ),
    "values_preferences": (
        "Apakah pasien menilai outcome utama intervensi ini secara konsisten, "
        "tanpa ketidakpastian penting?"
    ),
    "equity": (
        "Apakah intervensi ini akan meningkatkan - atau setidaknya tidak "
        "menurunkan - ekuitas kesehatan di rumah sakit Anda?"
    ),
}

OLD_PROMPTS = {
    "problem": (
        "Seberapa penting masalah klinis yang diatasi oleh intervensi ini bagi pasien "
        "di rumah sakit Anda?"
    ),
    "values_preferences": (
        "Apakah ada ketidakpastian penting tentang bagaimana pasien menilai outcome "
        "utama dari intervensi ini?"
    ),
    "equity": (
        "Apakah intervensi ini akan meningkatkan, mempertahankan, atau menurunkan "
        "ekuitas kesehatan di RS Anda?"
    ),
}


def _apply(apps, prompts):
    EtDDomain = apps.get_model("etd", "EtDDomain")
    for slug, text in prompts.items():
        EtDDomain.objects.filter(slug=slug).update(prompt_text_id=text)


def forwards(apps, schema_editor):
    _apply(apps, NEW_PROMPTS)


def backwards(apps, schema_editor):
    _apply(apps, OLD_PROMPTS)


class Migration(migrations.Migration):
    dependencies = [("etd", "0002_seed_domains")]

    operations = [migrations.RunPython(forwards, backwards)]
