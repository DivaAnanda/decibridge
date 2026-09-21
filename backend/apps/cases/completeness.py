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

from dataclasses import asdict, dataclass, replace

# Transitions that require a complete dossier.
GATED_TRANSITIONS = frozenset({"submit", "approve", "lock"})

# Round 4 item 4: "Persyaratannya disesuaikan dengan fungsi masing-masing tahap."
# Which requirements are mandatory depends on the stage. Submitting for review
# only needs a real decision question -- the analysis is what the review is for.
# Approval needs the full dossier. Locking additionally needs a recorded
# signature, which cannot exist any earlier.
STAGE_REQUIREMENTS: dict[str, frozenset[str]] = {
    "submit": frozenset({"pico"}),
    "approve": frozenset(
        {"pico", "economic_analysis", "budget_impact", "etd_domains", "recommendation"}
    ),
    "lock": frozenset(
        {
            "pico",
            "economic_analysis",
            "budget_impact",
            "etd_domains",
            "recommendation",
            "signoff",
        }
    ),
}
# The Sign-Off checklist renders without naming an action; show the approve set.
DEFAULT_STAGE = "approve"

# Transitions gated on the stricter archival integrity check (Round 3), which
# additionally requires an immutable snapshot and a recorded sign-off.
INTEGRITY_GATED_TRANSITIONS = frozenset({"archive"})


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


def _pico_requirement(case) -> Requirement:
    """Round 3 item 1 names PICO as a lock precondition alongside CEA/BIA/EtD.

    A decision question with an empty P, I, C or O is not a formulary question
    anyone can audit later, so all four parts must be filled.
    """
    questions = list(case.decision_questions.all())
    complete = [
        q
        for q in questions
        if q.pico_population.strip()
        and q.pico_intervention.strip()
        and q.pico_comparator.strip()
        and q.pico_outcome.strip()
    ]
    return Requirement(
        key="pico",
        label="Pertanyaan keputusan (PICO) lengkap",
        satisfied=bool(complete),
        detail=(
            f"{len(complete)}/{len(questions)} pertanyaan lengkap" if questions
            else "Belum ada pertanyaan keputusan"
        ),
    )


def _signoff_requirement(case, *, mandatory: bool) -> Requirement:
    """Round 3 item 1 also names sign-off as a lock precondition.

    An Approval row is only written by the sign-off endpoint, so the raw
    `approve` transition could otherwise reach `locked` with no signature on
    file -- the "backend pernah memungkinkan penguncian tidak sah" case.
    """
    count = case.approvals.count()
    return Requirement(
        key="signoff",
        label="Sign-off Ketua KFT tercatat",
        satisfied=count > 0,
        mandatory=mandatory,
        detail=f"{count} tanda tangan tercatat" if count else "Belum ada tanda tangan",
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


def evaluate_readiness(case, *, action: str | None = None) -> dict:
    """Return the full checklist plus whether `action` may proceed.

    Every requirement is always reported so the UI can show the whole picture;
    `mandatory` says which ones actually block this particular stage.
    """
    required = STAGE_REQUIREMENTS.get(action or DEFAULT_STAGE, STAGE_REQUIREMENTS[DEFAULT_STAGE])

    requirements = [
        _pico_requirement(case),
        *_econ_requirements(case),
        _etd_requirement(case),
        _recommendation_requirement(case),
        _signoff_requirement(case, mandatory=True),
        _cba_requirement(case),
    ]
    requirements = [
        replace(r, mandatory=r.mandatory and r.key in required) for r in requirements
    ]
    missing = [r for r in requirements if r.mandatory and not r.satisfied]
    return {
        "is_ready": not missing,
        "requirements": [r.as_dict() for r in requirements],
        "missing": [r.label for r in missing],
    }


def assert_ready_for(case, action: str) -> None:
    """Raise ValidationError if `action` is gated and the dossier is incomplete."""
    from django.core.exceptions import ValidationError

    if action in INTEGRITY_GATED_TRANSITIONS:
        from .integrity import evaluate_integrity

        report = evaluate_integrity(case)
        if not report["is_valid"]:
            raise ValidationError(
                "Integritas kasus gagal diverifikasi: " + "; ".join(report["failures"]),
                code="integrity_check_failed",
                params={"missing": report["failures"]},
            )
        return

    if action not in GATED_TRANSITIONS:
        return

    readiness = evaluate_readiness(case, action=action)
    if not readiness["is_ready"]:
        raise ValidationError(
            "Dossier belum lengkap: " + "; ".join(readiness["missing"]),
            code="incomplete_dossier",
            params={"missing": readiness["missing"]},
        )
