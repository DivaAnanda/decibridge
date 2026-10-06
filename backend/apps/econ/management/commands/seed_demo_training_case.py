"""Load DB_DEMO_HF_001 from the lecturer's DeciBridge_Demo_Training_Package.xlsx.

The package is a synthetic training case (ARNI vs ramipril in HFrEF) with an
instructor key of expected results. It is explicitly not patient data, not
hospital data and not for clinical decisions, so the case title and every source
say so.

What is seeded, and why only this much:

  * Ringkasan: case identity and PICO.
  * Analisis Ekonomi / BIA / PSA: the model, every parameter with unit, source
    and PSA distribution, then CEA, BIA and PSA computed by the real engines.
    These are deterministic inputs from the package and can be checked
    against its 11_INSTRUCTOR_KEY.
  * References: the package's 12_SOURCE_REGISTER.

EtD, Rekomendasi, Sign-Off, Brief and Versi are judgement and governance steps
the package expects people to perform in their own role, so they are left for
the workflow rather than written in here.

Three translations from the package to this dashboard, recorded on the model's
notes so the manual can explain them:

  * Drug cost is given per month; the field is per year, so it is stored x12.
  * The package's "baseline market share = 0" means ARNI has no current share.
    Our `market_share` is a different multiplier (patients = eligible x uptake
    x share), so it is deliberately left unset; entering 0 would zero the BIA.
  * Utilities are given for PSA as mean + SD; beta alpha/beta are derived here.

Safe to re-run: existing rows are left alone unless --reset is given, so a
student's work on the case (e.g. the 10_VERSI price-revision exercise) is never
overwritten by a deploy.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import RoleSlug
from apps.cases.models import Case, CasePerspective, DecisionQuestion

User = get_user_model()

CASE_ID = "DB_DEMO_HF_001"
SYNTHETIC = "DATA LATIHAN SINTETIS - bukan data pasien/RS, bukan keputusan klinis"

PSA_ITERATIONS = 5000
PSA_SEED = 42

MODEL_NOTES = (
    "Paket Data Demo DeciBridge (latihan mahasiswa). " + SYNTHETIC + ". "
    "Biaya obat di paket dinyatakan per bulan; field dashboard per tahun, sehingga "
    "disimpan x12 (ARNI 1.200.000/bulan = 14.400.000/tahun; ramipril 100.000/bulan "
    "= 1.200.000/tahun). 'Market share baseline ARNI = 0' pada paket berarti ARNI "
    "belum dipakai; parameter market share dashboard adalah pengali lain dan "
    "sengaja tidak diisi (mengisi 0 akan membuat BIA menjadi nol). "
    "Horizon CEA 1 tahun, horizon BIA 3 tahun."
)

SRC_DRUG = "SRC-DEMO-01 Farmasi demo (sintetis, 2026)"
SRC_RWE = "SRC-DEMO-02 RWE demo (sintetis, 2026)"
SRC_BILLING = "SRC-DEMO-03 Billing demo (sintetis, 2026)"
SRC_UTILITY = "SRC-DEMO-04 Utility demo (sintetis, 2026)"
SRC_SIMRS = "SRC-DEMO-05 SIMRS demo (sintetis, 2026)"
SRC_PROTOCOL = "SRC-DEMO-06 Protokol latihan (asumsi, 2026)"
SRC_MONITORING = "Monitoring demo (paket latihan, sintetis, 2026)"

SOURCE_REGISTER = [
    (SRC_DRUG, "Harga ARNI dan ramipril. Harga latihan saja; bukan harga aktual RS/e-catalogue."),
    (SRC_RWE, "Probabilitas rehospitalisasi 0,30 vs 0,45 per tahun. Bukan data pasien nyata."),
    (SRC_BILLING, "Biaya rehospitalisasi Rp6.000.000/event. Bukan tarif aktual."),
    (SRC_UTILITY, "Utility 0,78 dan 0,74; disutility 0,10. Bukan EQ-5D aktual."),
    (SRC_SIMRS, "Eligible population 200/220/240 pasien/tahun. Bukan volume nyata RS."),
    (SRC_PROTOCOL, "Perspektif, horizon, WTP, uptake, seed. Ditentukan untuk pembelajaran."),
]


def _beta_from_mean_sd(mean: Decimal, sd: Decimal) -> tuple[Decimal, Decimal]:
    """Method-of-moments beta parameters, as the package's 05_PSA asks for."""
    k = mean * (1 - mean) / (sd * sd) - 1
    return (mean * k).quantize(Decimal("1E-10")), ((1 - mean) * k).quantize(Decimal("1E-10"))


def _parameters() -> list[dict]:
    u_i = _beta_from_mean_sd(Decimal("0.78"), Decimal("0.06"))
    u_c = _beta_from_mean_sd(Decimal("0.74"), Decimal("0.06"))
    dis = _beta_from_mean_sd(Decimal("0.10"), Decimal("0.03"))

    def p(key, alternative, value, unit, param_type, source, *, dist="fixed", d1=None,
          d2=None, notes="", year=None):
        return {
            "key": key,
            "alternative": alternative,
            "year_index": year,
            "value": Decimal(value),
            "unit": unit,
            "param_type": param_type,
            "data_status": "assumption",
            "source_reference": source,
            "source_year": 2026,
            "notes": notes,
            "distribution": dist,
            "dist_param1": None if d1 is None else Decimal(d1),
            "dist_param2": None if d2 is None else Decimal(d2),
        }

    rows = [
        p("drug_cost", "intervention", "14400000", "IDR/pasien/tahun", "cost", SRC_DRUG,
          dist="gamma", d1="100", d2="144000", notes="Paket: 1.200.000/bulan x 12. SE 10%."),
        p("drug_cost", "comparator", "1200000", "IDR/pasien/tahun", "cost", SRC_DRUG,
          dist="gamma", d1="100", d2="12000", notes="Paket: 100.000/bulan x 12. SE 10%."),
        p("event_probability", "intervention", "0.30", "proporsi/tahun", "probability", SRC_RWE,
          dist="beta", d1="60", d2="140"),
        p("event_probability", "comparator", "0.45", "proporsi/tahun", "probability", SRC_RWE,
          dist="beta", d1="90", d2="110"),
        p("event_cost", "shared", "6000000", "IDR/event", "cost", SRC_BILLING,
          dist="gamma", d1="100", d2="60000", notes="Unit cost sama untuk kedua lengan. SE 10%."),
        p("baseline_utility", "intervention", "0.78", "utility 0-1", "utility", SRC_UTILITY,
          dist="beta", d1=u_i[0], d2=u_i[1], notes="PSA: mean 0,78; SD 0,06."),
        p("baseline_utility", "comparator", "0.74", "utility 0-1", "utility", SRC_UTILITY,
          dist="beta", d1=u_c[0], d2=u_c[1], notes="PSA: mean 0,74; SD 0,06."),
        p("event_disutility", "shared", "0.10", "decrement/event", "disutility", SRC_UTILITY,
          dist="beta", d1=dis[0], d2=dis[1], notes="Decrement positif. PSA: mean 0,10; SD 0,03."),
        p("other_cost", "intervention", "300000", "IDR/pasien/tahun", "cost", SRC_MONITORING,
          dist="gamma", d1="100", d2="3000", notes="Monitoring tambahan. SE 10%."),
        p("other_cost", "comparator", "200000", "IDR/pasien/tahun", "cost", SRC_MONITORING,
          dist="gamma", d1="100", d2="2000", notes="Monitoring. SE 10%."),
    ]
    for year, eligible, uptake in ((1, "200", "0.20"), (2, "220", "0.35"), (3, "240", "0.50")):
        rows.append(p("eligible_population", "shared", eligible, "pasien/tahun", "count",
                      SRC_SIMRS, year=year))
        rows.append(p("uptake", "shared", uptake, "proporsi", "rate", SRC_PROTOCOL, year=year))
    return rows


def _author():
    return (
        User.objects.filter(groups__role__slug=RoleSlug.HTA_ANALYST).order_by("pk").first()
        or User.objects.order_by("pk").first()
    )


class Command(BaseCommand):
    help = "Load the synthetic training case DB_DEMO_HF_001 from the lecturer's package."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Overwrite parameters with the package values and recompute.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        reset: bool = options["reset"]
        author = _author()
        if author is None:
            self.stderr.write("No users exist. Run create_test_users first.")
            return

        case = self._case(author)
        self._references(case, author)
        model, changed = self._model(case, author, reset=reset)
        changed |= self._parameters(model, author, reset=reset)
        self._results(case, model, author, recompute=changed or reset)

        self.stdout.write(self.style.SUCCESS(f"{CASE_ID} siap ({case.status})."))

    def _case(self, author) -> Case:
        case, _ = Case.objects.get_or_create(
            case_id=CASE_ID,
            defaults={
                "case_title": "Demo ARNI vs Ramipril pada HFrEF (data latihan sintetis)",
                "technology": "Sacubitril/valsartan (ARNI)",
                "comparator": "Ramipril (ACEI)",
                "indication": "Heart failure with reduced ejection fraction (HFrEF)",
                "population": "Dewasa >=18 tahun, HFrEF LVEF <=40%, NYHA II-IV, stabil. " + SYNTHETIC,
                "setting": "Formularium rumah sakit; rawat jalan HFrEF",
                "perspective": CasePerspective.HOSPITAL,
                "created_by": author,
            },
        )
        DecisionQuestion.objects.get_or_create(
            case=case,
            order=1,
            defaults={
                "question_text": (
                    "Apakah ARNI diadopsi dibanding ramipril untuk pasien HFrEF eligible? "
                    "(kasus latihan sintetis)"
                ),
                "pico_population": "Dewasa >=18 tahun, HFrEF LVEF <=40%, NYHA II-IV, stabil",
                "pico_intervention": "Sacubitril/valsartan (ARNI)",
                "pico_comparator": "Ramipril (ACEI)",
                "pico_outcome": "QALY; rehospitalisasi HF",
            },
        )
        return case

    def _references(self, case: Case, author) -> None:
        from apps.etd.models import ReferenceCitation, ReferenceType

        for citation, summary in SOURCE_REGISTER:
            ReferenceCitation.objects.get_or_create(
                case=case,
                citation_text=citation,
                defaults={
                    "reference_type": ReferenceType.PROTOCOL,
                    "publication_year": 2026,
                    "evidence_summary": summary,
                    "created_by": author,
                },
            )

    def _model(self, case: Case, author, *, reset: bool):
        from apps.econ.models import EconomicModel

        scalars = {
            "horizon_years": 1,
            "bia_horizon_years": 3,
            "cost_discount_rate": Decimal("0"),
            "outcome_discount_rate": Decimal("0"),
            "wtp_threshold": Decimal("300000000"),
            "annual_budget_baseline": Decimal("20000000000"),
            "notes": MODEL_NOTES,
        }
        model = EconomicModel.objects.filter(case=case).first()
        if model is None:
            return EconomicModel.objects.create(case=case, created_by=author, **scalars), True
        if reset:
            for field, value in scalars.items():
                setattr(model, field, value)
            model.last_edited_by = author
            model.save()
            return model, True
        return model, False

    def _parameters(self, model, author, *, reset: bool) -> bool:
        from apps.econ.models import EconomicParameter

        changed = False
        for row in _parameters():
            lookup = {
                "economic_model": model,
                "key": row["key"],
                "alternative": row["alternative"],
                "year_index": row["year_index"],
            }
            values = {k: v for k, v in row.items() if k not in ("key", "alternative", "year_index")}
            existing = EconomicParameter.objects.filter(**lookup).first()
            if existing is None:
                EconomicParameter.objects.create(
                    **lookup, **values, created_by=author, last_edited_by=author
                )
                changed = True
            elif reset:
                for field, value in values.items():
                    setattr(existing, field, value)
                existing.last_edited_by = author
                existing.save()
                changed = True
        return changed

    def _results(self, case: Case, model, author, *, recompute: bool) -> None:
        from apps.econ import service

        if recompute or not case.econ_deterministic_results.exists():
            service.run_deterministic(model, computed_by=author)
        if recompute or not case.econ_bia_results.exists():
            service.run_bia(model, computed_by=author)
        if recompute or not case.econ_psa_results.exists():
            service.run_psa(model, computed_by=author, n_simulations=PSA_ITERATIONS, seed=PSA_SEED)
