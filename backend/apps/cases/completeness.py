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
_DOSSIER = frozenset(
    {"pico", "economic_analysis", "budget_impact", "etd_domains", "recommendation"}
)
# Round 5 item 1: "Kalau PSA belum dikerjakan atau sudah tidak sesuai input terbaru
# -> belum boleh sign-off/lock." The recommendation must be current for the same
# reason (Panduan section 15: one version of the inputs behind every result).
_CURRENT = frozenset({"psa", "recommendation_current"})
# Round 5 item 3: the KFT's own decision on the current recommendation.
_HUMAN = frozenset({"final_decision"})

STAGE_REQUIREMENTS: dict[str, frozenset[str]] = {
    "submit": frozenset({"pico"}),
    "approve": _DOSSIER | _CURRENT | _HUMAN,
    "lock": _DOSSIER | _CURRENT | _HUMAN | {"signoff"},
    # A brief is only issued for an approved or locked case, which passed the gate
    # in force when it was signed. Cases signed before round 5 cannot re-run a PSA
    # once locked, so asking for one here would leave them without a brief.
    "brief": _DOSSIER,
    # The archive check, also run over every case on each deploy. It judges a
    # locked decision by the rules it was locked under, so round 5 does not turn
    # older locked cases into remediation cases.
    "integrity": _DOSSIER | {"signoff"},
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


def _revision_start(case):
    """When the current revision of a once-locked case began, or None (round 5 item 4).

    Signatures and KFT decisions from before it belong to the earlier version.
    """
    from .models import CaseVersion, CaseVersionTrigger

    return (
        CaseVersion.objects.filter(case=case, trigger=CaseVersionTrigger.REVISION_REQUESTED)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )


def _signoff_requirement(case, *, mandatory: bool, strict: bool = False) -> Requirement:
    """Round 3 item 1 also names sign-off as a lock precondition.

    An Approval row is only written by the sign-off endpoint, so the raw
    `approve` transition could otherwise reach `locked` with no signature on
    file -- the "backend pernah memungkinkan penguncian tidak sah" case.

    `strict` (the lock itself, round 5) counts only an approval of the
    recommendation and the KFT decision that are current now. The archive and
    deploy-time integrity checks keep the older count so earlier locks stand.
    """
    approvals = case.approvals.all()
    since = _revision_start(case)
    if since is not None:
        approvals = approvals.filter(signed_at__gte=since)
    if strict:
        from apps.approval.models import ApprovalDecision

        recorded = approvals.exists()
        latest = case.recommendations.order_by("-computed_at").first()
        approvals = approvals.filter(
            decision=ApprovalDecision.APPROVED,
            recommendation_id=latest.pk if latest else None,
        )
        current = case.final_decisions.first()
        if current is not None:
            approvals = approvals.filter(final_decision=current)
    count = approvals.count()
    if count:
        detail = f"{count} tanda tangan tercatat"
    elif strict and recorded:
        detail = "Tanda tangan tercatat untuk rekomendasi atau keputusan sebelumnya"
    else:
        detail = "Belum ada tanda tangan untuk versi ini" if since else "Belum ada tanda tangan"
    return Requirement(
        key="signoff",
        label="Sign-off Ketua KFT tercatat",
        satisfied=count > 0,
        mandatory=mandatory,
        detail=detail,
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


def _psa_requirement(case) -> Requirement:
    from apps.econ.models import EconPSAResult
    from apps.econ.psa_distributions import psa_result_is_stale

    psa = EconPSAResult.objects.filter(case=case).order_by("-computed_at", "-id").first()
    label = "PSA dijalankan pada input terbaru"
    if psa is None:
        return Requirement(key="psa", label=label, satisfied=False, detail="PSA belum dijalankan")

    stale = psa_result_is_stale(psa)
    if stale is None:
        detail = (
            "PSA ini dijalankan sebelum inputnya dicatat (sebelum 13 Oktober 2026); "
            "jalankan ulang PSA"
        )
    elif stale:
        detail = "Input berubah setelah PSA terakhir; jalankan ulang PSA"
    else:
        detail = (
            f"Peluang cost-effective {psa.prob_cost_effective_base:.1%}, "
            f"{psa.n_simulations:,} iterasi, seed {psa.random_seed}"
        )
    return Requirement(key="psa", label=label, satisfied=stale is False, detail=detail)


def _recommendation_current_requirement(case) -> Requirement:
    from apps.recommendation.staleness import evaluate_staleness

    label = "Rekomendasi sesuai input terbaru"
    rec = case.recommendations.order_by("-computed_at").first()
    if rec is None:
        return Requirement(
            key="recommendation_current", label=label, satisfied=False,
            detail="Belum ada rekomendasi",
        )
    report = evaluate_staleness(case, rec)
    return Requirement(
        key="recommendation_current",
        label=label,
        satisfied=not report.is_stale,
        detail=(
            " ".join(report.reasons) + " Hitung ulang rekomendasi." if report.is_stale
            else "Tidak ada input yang berubah sejak dihitung"
        ),
    )


def _final_decision_requirement(case) -> Requirement:
    label = "Keputusan Final KFT tercatat"
    decision = case.final_decisions.select_related("decided_by").first()
    if decision is None:
        return Requirement(
            key="final_decision", label=label, satisfied=False, detail="Belum ada keputusan final"
        )
    since = _revision_start(case)
    if since is not None and decision.decided_at < since:
        return Requirement(
            key="final_decision",
            label=label,
            satisfied=False,
            detail="Diputuskan untuk versi sebelumnya; konfirmasi ulang",
        )
    latest = case.recommendations.order_by("-computed_at").first()
    if latest is None or decision.recommendation_id != latest.pk:
        return Requirement(
            key="final_decision",
            label=label,
            satisfied=False,
            detail="Diputuskan atas rekomendasi sebelumnya; konfirmasi ulang",
        )
    who = decision.decided_by.full_name or decision.decided_by.email
    return Requirement(
        key="final_decision",
        label=label,
        satisfied=True,
        detail=f"{decision.get_decision_display()} oleh {who}",
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
        _psa_requirement(case),
        _etd_requirement(case),
        _recommendation_requirement(case),
        _recommendation_current_requirement(case),
        _final_decision_requirement(case),
        _signoff_requirement(case, mandatory=True, strict=action == "lock"),
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
        message = "Dossier belum lengkap: " + "; ".join(readiness["missing"])
        if action == "lock":
            # An approved case cannot record a decision or recompute; the way back
            # is Minta Revisi (approved -> in_review), then a new signature.
            message += (
                ". Pilih Minta Revisi untuk mengembalikan kasus ke Dalam Tinjauan, lengkapi "
                "butir di atas, lalu tanda tangani ulang."
            )
        raise ValidationError(
            message,
            code="incomplete_dossier",
            params={"missing": readiness["missing"]},
        )
