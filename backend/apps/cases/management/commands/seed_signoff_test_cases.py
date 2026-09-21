"""Seed two cases in `in_review` so the Ketua sign-off gate can be tested.

Round 3, Ketua report item 5:

    "Saat pengujian, tidak terdapat kasus berstatus in_review. Karena itu, saya
     belum dapat memastikan apakah tombol persetujuan Ketua benar-benar
     dinonaktifkan pada kasus in_review yang belum lengkap. Untuk mengetesnya
     dibutuhkan kasus uji khusus."

So this creates the fixture rather than asking the reviewer to mutate real data:

  SIGNOFF_TEST_INCOMPLETE - in_review with only PICO. Sign-off must be refused,
                            listing the missing components.
  SIGNOFF_TEST_COMPLETE   - in_review with PICO, CEA, BIA, 9/9 EtD and a
                            recommendation. Sign-off must be allowed.

The economic results on the complete case are written directly rather than
computed. The fixture exists to exercise the sign-off gate, not the econ engine,
which is covered by `seed_econ_validation_case` and its 11 QC checks.

Idempotent: re-running resets both cases to `in_review`.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import RoleSlug
from apps.cases.models import Case, CasePerspective, CaseStatus, DecisionQuestion

User = get_user_model()

INCOMPLETE_ID = "SIGNOFF_TEST_INCOMPLETE"
COMPLETE_ID = "SIGNOFF_TEST_COMPLETE"


def _user_with_role(slug: str) -> User | None:
    return User.objects.filter(groups__role__slug=slug).order_by("pk").first()


class Command(BaseCommand):
    help = "Seed in_review cases so the Ketua sign-off gate can be exercised."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        author = _user_with_role(RoleSlug.HTA_ANALYST) or User.objects.order_by("pk").first()
        if author is None:
            self.stderr.write("No users exist. Run create_test_users first.")
            return

        incomplete = self._base_case(
            INCOMPLETE_ID,
            "UJI GATE - dossier belum lengkap",
            author,
        )
        self._reset_to_in_review(incomplete)
        self.stdout.write(
            self.style.WARNING(f"{INCOMPLETE_ID}: in_review, sengaja tidak lengkap")
        )

        complete = self._base_case(
            COMPLETE_ID,
            "UJI GATE - dossier lengkap",
            author,
        )
        self._fill_dossier(complete, author)
        self._reset_to_in_review(complete)
        self.stdout.write(
            self.style.SUCCESS(f"{COMPLETE_ID}: in_review, dossier lengkap")
        )

    def _base_case(self, case_id: str, title: str, author) -> Case:
        case, _ = Case.objects.get_or_create(
            case_id=case_id,
            defaults={
                "case_title": title,
                "technology": "ARNI (sacubitril/valsartan)",
                "comparator": "ACEI (captopril)",
                "indication": "HFrEF",
                "perspective": CasePerspective.HOSPITAL,
                "created_by": author,
            },
        )
        DecisionQuestion.objects.get_or_create(
            case=case,
            order=1,
            defaults={
                "question_text": (
                    "Apakah ARNI perlu dimasukkan ke formularium untuk pasien HFrEF?"
                ),
                "pico_population": "Pasien HFrEF dewasa, EF <= 40%",
                "pico_intervention": "ARNI (sacubitril/valsartan)",
                "pico_comparator": "ACEI (captopril)",
                "pico_outcome": "Rehospitalisasi gagal jantung 12 bulan",
            },
        )
        return case

    def _fill_dossier(self, case: Case, author) -> None:
        from apps.econ.models import EconBIAResult, EconDeterministicResult
        from apps.etd.models import EtDAppraisal, EtDDomain
        from apps.recommendation.models import Recommendation

        if not EconDeterministicResult.objects.filter(case=case).exists():
            EconDeterministicResult.objects.create(
                case=case,
                input_snapshot={"seeded": True},
                total_cost_intervention=Decimal("18499451.85"),
                total_cost_comparator=Decimal("5199411.1161"),
                total_qaly_intervention=Decimal("0.655"),
                total_qaly_comparator=Decimal("0.62923"),
                incremental_cost=Decimal("13300040.7339"),
                incremental_qaly=Decimal("0.02577"),
                icer=Decimal("516110234.14"),
                nmb_intervention=Decimal("37175548.15"),
                nmb_comparator=Decimal("48285138.88"),
                inb=Decimal("-11109590.73"),
                wtp_threshold_used=Decimal("85000000"),
                decision_code="not_cost_effective",
                is_cost_effective=False,
                is_dominant=False,
                is_dominated=False,
                interpretation_text="Fixture sign-off gate.",
                algorithm_version="2.0.0",
                computed_by=author,
            )

        if not EconBIAResult.objects.filter(case=case).exists():
            EconBIAResult.objects.create(
                case=case,
                input_snapshot={"seeded": True},
                cumulative_net_impact=Decimal("1500000000"),
                pct_of_total_baseline=Decimal("3.0000"),
                annual_budget_baseline=Decimal("50000000000"),
                severity="manageable",
                budget_score=80,
                per_year=[],
                interpretation_text="Fixture sign-off gate.",
                algorithm_version="2.0.0",
                computed_by=author,
            )

        member = _user_with_role(RoleSlug.KFT_MEMBER) or author
        for domain in EtDDomain.objects.all():
            EtDAppraisal.objects.get_or_create(
                case=case,
                domain=domain,
                member=member,
                defaults={
                    "judgement": 75,
                    "certainty": "high",
                    "narrative": "Fixture sign-off gate.",
                },
            )

        if not Recommendation.objects.filter(case=case).exists():
            Recommendation.objects.create(
                case=case,
                input_snapshot={"seeded": True},
                evidence_strength_score=Decimal("87.50"),
                ce_score=Decimal("40"),
                budget_score=Decimal("80"),
                composite_score=Decimal("70.36"),
                traffic_light="yellow",
                justification_text="Fixture sign-off gate.",
                algorithm_version="2.0.0",
                computed_by=author,
            )

    def _reset_to_in_review(self, case: Case) -> None:
        # `.update()` bypasses the model save path so seeding never counts as a
        # user edit, and skips the transition guards this fixture exists to test.
        Case.objects.filter(pk=case.pk).update(status=CaseStatus.IN_REVIEW)
