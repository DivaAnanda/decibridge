"""Seed labelled UAT cases with synthetic data.

Round 4 item 3:

    "Mohon siapkan kasus baru berlabel 'UAT - bukan keputusan klinis'. Sediakan
     satu kasus lengkap untuk alur berhasil dan beberapa variasi kasus tidak
     lengkap untuk menguji penolakan sistem. Data kasus lama tetap dipertahankan."

Round 3's Ketua report also could not test the sign-off gate because no case sat
in `in_review`. Both needs are met here.

Cases created (all prefixed UAT_ and titled "UAT - bukan keputusan klinis"):

  UAT_LENGKAP            in_review, full dossier. The success path: PICO,
                         references, economic parameters with source and unit,
                         CEA, BIA, PSA, 9/9 EtD, CBA. Approval should be allowed.
  UAT_TANPA_PICO         draft, no decision question. Submit must be refused.
  UAT_TANPA_EKONOMI      in_review, PICO only. Approval must be refused.
  UAT_ETD_SEBAGIAN       in_review, PICO + CEA + BIA but only 4 of 9 EtD domains.
                         Approval must be refused and the partial evidence score
                         must not reach the recommendation.
  UAT_TANPA_TANDA_TANGAN approved, full dossier but no Approval row. Lock must be
                         refused for want of a recorded signature.

Existing cases are never touched. Idempotent: re-running resets each case to its
intended status.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import RoleSlug
from apps.cases.models import Case, CasePerspective, CaseStatus, DecisionQuestion

User = get_user_model()

UAT_TITLE = "UAT - bukan keputusan klinis"

LENGKAP = "UAT_LENGKAP"
TANPA_PICO = "UAT_TANPA_PICO"
TANPA_EKONOMI = "UAT_TANPA_EKONOMI"
ETD_SEBAGIAN = "UAT_ETD_SEBAGIAN"
TANPA_TANDA_TANGAN = "UAT_TANPA_TANDA_TANGAN"

ALL_UAT_CASE_IDS = (
    LENGKAP,
    TANPA_PICO,
    TANPA_EKONOMI,
    ETD_SEBAGIAN,
    TANPA_TANDA_TANGAN,
)


def _user_with_role(slug: str):
    return User.objects.filter(groups__role__slug=slug).order_by("pk").first()


class Command(BaseCommand):
    help = "Seed labelled UAT cases: one complete, several deliberately incomplete."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        author = _user_with_role(RoleSlug.HTA_ANALYST) or User.objects.order_by("pk").first()
        if author is None:
            self.stderr.write("No users exist. Run create_test_users first.")
            return
        member = _user_with_role(RoleSlug.KFT_MEMBER) or author

        complete = self._case(LENGKAP, author, with_pico=True)
        self._references(complete, author)
        self._economics(complete, author)
        self._etd(complete, member, domains=None)
        self._cba(complete, author)
        self._recommendation(complete, author)
        self._status(complete, CaseStatus.IN_REVIEW)
        self._ok(f"{LENGKAP}: in_review, dossier lengkap (alur berhasil)")

        no_pico = self._case(TANPA_PICO, author, with_pico=False)
        self._status(no_pico, CaseStatus.DRAFT)
        self._warn(f"{TANPA_PICO}: draft tanpa PICO (submit harus ditolak)")

        no_econ = self._case(TANPA_EKONOMI, author, with_pico=True)
        self._status(no_econ, CaseStatus.IN_REVIEW)
        self._warn(f"{TANPA_EKONOMI}: in_review tanpa CEA/BIA (approve harus ditolak)")

        partial = self._case(ETD_SEBAGIAN, author, with_pico=True)
        self._references(partial, author)
        self._economics(partial, author)
        self._etd(partial, member, domains=4)
        self._status(partial, CaseStatus.IN_REVIEW)
        self._warn(f"{ETD_SEBAGIAN}: in_review dengan EtD 4/9 (approve harus ditolak)")

        unsigned = self._case(TANPA_TANDA_TANGAN, author, with_pico=True)
        self._references(unsigned, author)
        self._economics(unsigned, author)
        self._etd(unsigned, member, domains=None)
        self._recommendation(unsigned, author)
        self._status(unsigned, CaseStatus.APPROVED)
        self._warn(
            f"{TANPA_TANDA_TANGAN}: approved tanpa tanda tangan (lock harus ditolak)"
        )

    # ── helpers ──────────────────────────────────────────────────────────

    def _ok(self, msg: str) -> None:
        self.stdout.write(self.style.SUCCESS(msg))

    def _warn(self, msg: str) -> None:
        self.stdout.write(self.style.WARNING(msg))

    def _case(self, case_id: str, author, *, with_pico: bool) -> Case:
        case, _ = Case.objects.get_or_create(
            case_id=case_id,
            defaults={
                "case_title": f"{UAT_TITLE} - {case_id}",
                "technology": "ARNI (sacubitril/valsartan)",
                "comparator": "ACEI (captopril)",
                "indication": "HFrEF",
                "population": "Data sintetis untuk pengujian penerimaan (UAT).",
                "perspective": CasePerspective.HOSPITAL,
                "created_by": author,
            },
        )
        if with_pico:
            DecisionQuestion.objects.get_or_create(
                case=case,
                order=1,
                defaults={
                    "question_text": (
                        "Apakah ARNI perlu dimasukkan ke formularium untuk pasien HFrEF? "
                        "(data sintetis UAT)"
                    ),
                    "pico_population": "Pasien HFrEF dewasa, EF <= 40%",
                    "pico_intervention": "ARNI (sacubitril/valsartan)",
                    "pico_comparator": "ACEI (captopril)",
                    "pico_outcome": "Rehospitalisasi gagal jantung 12 bulan",
                },
            )
        return case

    def _references(self, case: Case, author) -> None:
        from apps.etd.models import ReferenceCitation

        ReferenceCitation.objects.get_or_create(
            case=case,
            citation_text=(
                "Data sintetis UAT - rujukan contoh untuk pengujian, bukan sitasi nyata."
            ),
            defaults={"reference_type": "journal_article", "created_by": author},
        )

    def _economics(self, case: Case, author) -> None:
        """Build a real economic model and run the engines, so CEA/BIA/PSA are
        computed rather than written in by hand."""
        from apps.econ import service
        from apps.econ.models import EconomicModel, EconomicParameter
        from apps.econ.validation_fixtures import MODEL_SCALARS, VALIDATION_PARAMETERS

        model = EconomicModel.objects.filter(case=case).first()
        if model is None:
            model = EconomicModel.objects.create(case=case, created_by=author, **MODEL_SCALARS)

        for spec in VALIDATION_PARAMETERS:
            spec = dict(spec)
            EconomicParameter.objects.get_or_create(
                economic_model=model,
                key=spec.pop("key"),
                alternative=spec.pop("alternative"),
                year_index=spec.pop("year_index", None),
                defaults={**spec, "created_by": author},
            )

        if not case.econ_deterministic_results.exists():
            service.run_deterministic(model, computed_by=author)
        if not case.econ_bia_results.exists():
            service.run_bia(model, computed_by=author)
        if not case.econ_psa_results.exists():
            service.run_psa(model, computed_by=author)

    def _etd(self, case: Case, member, *, domains: int | None) -> None:
        from apps.etd.models import EtDAppraisal, EtDDomain

        queryset = EtDDomain.objects.all().order_by("order")
        if domains is not None:
            queryset = queryset[:domains]
        for domain in queryset:
            EtDAppraisal.objects.get_or_create(
                case=case,
                domain=domain,
                member=member,
                defaults={
                    "judgement": 75,
                    "certainty": "high",
                    "narrative": "Penilaian sintetis untuk UAT.",
                },
            )

    def _cba(self, case: Case, author) -> None:
        from apps.recommendation.models import CBACriterion

        CBACriterion.objects.get_or_create(
            case=case,
            order=1,
            defaults={
                "criterion_name": "Diresepkan oleh dokter spesialis jantung",
                "operator": "is_present",
                "is_satisfied": True,
                "created_by": author,
                "last_edited_by": author,
            },
        )

    def _recommendation(self, case: Case, author) -> None:
        from apps.recommendation.models import Recommendation

        if Recommendation.objects.filter(case=case).exists():
            return
        Recommendation.objects.create(
            case=case,
            input_snapshot={"uat": True},
            evidence_strength_score=Decimal("87.50"),
            ce_score=Decimal("40"),
            budget_score=Decimal("80"),
            composite_score=Decimal("70.36"),
            traffic_light="yellow",
            justification_text="Rekomendasi sintetis untuk UAT.",
            algorithm_version="2.0.0",
            computed_by=author,
        )

    def _status(self, case: Case, status: str) -> None:
        # `.update()` bypasses the model save path so seeding never counts as a
        # user edit, and skips the guards these fixtures exist to exercise.
        Case.objects.filter(pk=case.pk).update(status=status)
        case.refresh_from_db()
