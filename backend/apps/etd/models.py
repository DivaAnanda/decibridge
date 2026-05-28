"""Evidence-to-Decision (EtD) data model.

Three tables:

- `EtDDomain`: the 9 GRADE EtD domains, seeded via data migration. Stable
  slugs are referenced by aggregation code, so changes must be migration-
  compatible.

- `ReferenceCitation`: bibliography per case. Each appraisal can link to
  zero or more references. Created and curated by HTA Analysts /
  Sekretaris KFT; readable by all viewers.

- `EtDAppraisal`: one row per (case, domain, KFT member). Each member
  submits a 5-point GRADE judgement, a 4-level certainty rating, a
  narrative, and citations. Aggregation across members happens in
  `aggregation.py`.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from apps.cases.models import Case


class EtDDomainSlug(models.TextChoices):
    """Stable slugs for the 9 GRADE EtD domains. Do not rename without migration."""

    PROBLEM = "problem", _("Masalah (Problem)")
    DESIRABLE_EFFECTS = "desirable_effects", _("Efek yang Diinginkan")
    UNDESIRABLE_EFFECTS = "undesirable_effects", _("Efek yang Tidak Diinginkan")
    CERTAINTY = "certainty_of_evidence", _("Kepastian Bukti")
    VALUES_PREFERENCES = "values_preferences", _("Nilai & Preferensi")
    RESOURCE_USE = "resource_use", _("Penggunaan Sumber Daya")
    EQUITY = "equity", _("Ekuitas")
    FEASIBILITY = "feasibility", _("Kelayakan Implementasi")
    ACCEPTABILITY = "acceptability", _("Penerimaan oleh Pemangku Kepentingan")


class EtDDomain(models.Model):
    """One of the 9 GRADE domains. Seeded once; never user-created."""

    slug = models.CharField(max_length=32, unique=True, choices=EtDDomainSlug.choices)
    display_name_id = models.CharField(max_length=120)
    display_name_en = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    prompt_text_id = models.TextField(
        help_text=_("Pertanyaan panduan yang ditampilkan kepada anggota KFT"),
        blank=True,
        default="",
    )
    order = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["order"]
        verbose_name = _("EtD Domain")
        verbose_name_plural = _("EtD Domains")

    def __str__(self) -> str:
        return self.display_name_id


class Judgement(models.IntegerChoices):
    """5-point GRADE EtD scale, mapped to 0-100 for aggregation."""

    NO = 0, _("Tidak")
    PROBABLY_NO = 25, _("Mungkin tidak")
    UNCERTAIN = 50, _("Tidak pasti")
    PROBABLY_YES = 75, _("Mungkin ya")
    YES = 100, _("Ya")


class Certainty(models.TextChoices):
    """GRADE certainty-of-evidence rating."""

    HIGH = "high", _("Tinggi")
    MODERATE = "moderate", _("Sedang")
    LOW = "low", _("Rendah")
    VERY_LOW = "very_low", _("Sangat rendah")


CERTAINTY_NUMERIC: dict[str, int] = {
    Certainty.HIGH.value: 100,
    Certainty.MODERATE.value: 75,
    Certainty.LOW.value: 50,
    Certainty.VERY_LOW.value: 25,
}


class ReferenceType(models.TextChoices):
    JOURNAL = "journal_article", _("Artikel jurnal")
    GUIDELINE = "clinical_guideline", _("Pedoman klinis")
    PROTOCOL = "institutional_protocol", _("Protokol institusi")
    EXPERT = "expert_opinion", _("Pendapat ahli")
    MODEL = "pharmacoeconomic_model", _("Model farmakoekonomi")


class ReferenceCitation(models.Model):
    """Bibliography entry tied to a case. M2M linked to appraisals."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="references")
    reference_type = models.CharField(
        max_length=32, choices=ReferenceType.choices, default=ReferenceType.JOURNAL
    )
    citation_text = models.CharField(
        max_length=500,
        help_text=_("Sitasi terformat — author year. title. journal."),
    )
    authors = models.CharField(max_length=300, blank=True, default="")
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    title = models.CharField(max_length=500, blank=True, default="")
    journal_name = models.CharField(max_length=200, blank=True, default="")
    doi_pmid = models.CharField(max_length=120, blank=True, default="")
    url = models.URLField(max_length=500, blank=True, default="")
    evidence_summary = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="references_created",
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ["case", "-publication_year", "authors"]
        verbose_name = _("Reference Citation")
        verbose_name_plural = _("Reference Citations")

    def __str__(self) -> str:
        return self.citation_text[:80]


class EtDAppraisal(models.Model):
    """One KFT member's judgement on one domain of one case.

    Uniqueness: (case, domain, member). A member can update their own row;
    other members cannot.
    """

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="etd_appraisals")
    domain = models.ForeignKey(EtDDomain, on_delete=models.PROTECT, related_name="appraisals")
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="etd_appraisals",
    )

    judgement = models.PositiveSmallIntegerField(choices=Judgement.choices)
    certainty = models.CharField(max_length=16, choices=Certainty.choices, default=Certainty.MODERATE)
    narrative = models.TextField(
        blank=True,
        default="",
        help_text=_("Pertimbangan singkat anggota KFT untuk domain ini"),
    )
    references = models.ManyToManyField(
        ReferenceCitation, blank=True, related_name="appraisals"
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(m2m_fields=[references])

    class Meta:
        unique_together = [("case", "domain", "member")]
        ordering = ["case", "domain__order", "member__email"]
        verbose_name = _("EtD Appraisal")
        verbose_name_plural = _("EtD Appraisals")
        indexes = [
            models.Index(fields=["case", "domain"]),
            models.Index(fields=["case", "member"]),
        ]

    def __str__(self) -> str:
        return f"{self.case.case_id} / {self.domain.slug} / {self.member.email}"
