"""Decision-readiness gate before approval / lock (Phase V3).

Requested by the lecturer after acceptance testing HF_ARNI_ACEI_004:

    "Mohon juga dicek completion gate sebelum Sign-Off. Pada kasus ini Sign-Off
     menunjukkan EtD baru 4/9 domain, tetapi kasus sudah dapat disetujui dan
     dikunci. Jika 9 domain diwajibkan, sistem seharusnya memblokir sign-off
     sampai lengkap. Jika tidak semuanya mandatory, mohon aturan tersebut dibuat
     eksplisit di UI."

Decision taken: **all 9 GRADE EtD domains are mandatory.** GRADE's Evidence-to-
Decision framework is designed to be completed in full; a partial appraisal
produces an evidence score that is not comparable across cases. The rule is
enforced here AND surfaced in the UI as an explicit checklist.

Requirements are returned as structured items so the API and the Sign-Off
checklist render exactly the same list — no duplicated rules in the frontend.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Transitions that require a complete dossier.
GATED_TRANSITIONS = frozenset({"approve", "lock"})


@dataclass(frozen=True)
class Requirement:
    key: str
    label: str
    satisfied: bool
    detail: str = ""
    mandatory: bool = True

    def as_dict(self) -> dict:
        return asdict(self)


def _econ_requirements(case) -> list[Requirement]:
    from apps.econ.models import EconBIAResult, EconDeterministicResult

    det = EconDeterministicResult.objects.filter(case=case).order_by("-computed_at").first()
    bia = EconBIAResult.objects.filter(case=case).order_by("-computed_at").first()

    return [
        Requirement(
            key="economic_analysis",
            label="Analisis ekonomi deterministik (CEA)",
            satisfied=det is not None,
            detail=(
                f"ICER {det.icer:,.0f} IDR/QALY" if det and det.icer is not None
                else ("Sudah dihitung" if det else "Belum dihitung")
            ),
        ),
        Requirement(
            key="budget_impact",
            label="Analisis dampak anggaran (BIA)",
            satisfied=bia is not None,
            detail=(
                f"Dampak bersih {bia.cumulative_net_impact:,.0f} IDR" if bia
                else "Belum dihitung"
            ),
        ),
    ]


def _etd_requirement(case) -> Requirement:
    from apps.etd.models import EtDAppraisal, EtDDomain

    total = EtDDomain.objects.count()
    completed = (
        EtDAppraisal.objects.filter(case=case)
        .values_list("domain_id", flat=True)
        .distinct()
        .count()
    )
    return Requirement(
        key="etd_domains",
        label=f"Penilaian EtD lengkap ({total} domain)",
        satisfied=total > 0 and completed >= total,
        detail=f"{completed}/{total} domain terisi",
    )


def _recommendation_requirement(case) -> Requirement:
    rec = case.recommendations.order_by("-computed_at").first()
    return Requirement(
        key="recommendation",
        label="Rekomendasi akhir (traffic-light) sudah dihitung",
        satisfied=rec is not None,
        detail=(f"{rec.traffic_light.upper()} — skor {rec.composite_score}" if rec
                else "Belum dihitung"),
    )


def _cba_requirement(case) -> Requirement:
    """Advisory only — an empty CBA is valid ('not assessed'), never auto-scored."""
    count = case.cba_criteria.count()
    satisfied_count = case.cba_criteria.filter(is_satisfied=True).count()
    return Requirement(
        key="cba_criteria",
        label="Kriteria CBA didefinisikan (opsional)",
        satisfied=True,
        mandatory=False,
        detail=(f"{satisfied_count}/{count} kriteria terpenuhi" if count
                else "Tidak ada kriteria — tidak dinilai"),
    )


def evaluate_readiness(case) -> dict:
    """Return the full checklist plus whether the case may be approved/locked."""
    requirements = [
        *_econ_requirements(case),
        _etd_requirement(case),
        _recommendation_requirement(case),
        _cba_requirement(case),
    ]
    missing = [r for r in requirements if r.mandatory and not r.satisfied]
    return {
        "is_ready": not missing,
        "requirements": [r.as_dict() for r in requirements],
        "missing": [r.label for r in missing],
    }


def assert_ready_for(case, action: str) -> None:
    """Raise ValidationError if `action` is gated and the dossier is incomplete."""
    if action not in GATED_TRANSITIONS:
        return
    from django.core.exceptions import ValidationError

    readiness = evaluate_readiness(case)
    if not readiness["is_ready"]:
        raise ValidationError(
            "Dossier belum lengkap: " + "; ".join(readiness["missing"]),
            code="incomplete_dossier",
            params={"missing": readiness["missing"]},
        )
