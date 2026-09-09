"""Archival integrity check (Round 3).

Requested after five-role acceptance testing:

    "Sistem perlu menjalankan integrity check sebelum pengarsipan: CEA tersedia;
     BIA tersedia; EtD 9/9; rekomendasi valid; sign-off sesuai urutan; snapshot
     dan hash tersedia. Kasus lama yang gagal pemeriksaan harus diberi status
     khusus seperti legacy_invalid atau requires_remediation."

Archiving is the point of no return: an archived case becomes the hospital's
formal decision record. `HF_ARNI_ACEI_004` was locked before the completeness
gate existed, so it carries a GREEN verdict with no CEA, no BIA and 4 of 9 EtD
domains — exactly the kind of record that must not enter the archive unexamined.

This extends `completeness.evaluate_readiness` with the artefacts that only a
properly locked decision can have: an immutable snapshot, and a sign-off.
"""

from __future__ import annotations

from .completeness import Requirement, evaluate_readiness

FLAG_OK = ""
FLAG_REQUIRES_REMEDIATION = "requires_remediation"
FLAG_LEGACY_INVALID = "legacy_invalid"


def _snapshot_requirement(case) -> Requirement:
    from .models import CaseVersion, CaseVersionStatus

    version = (
        CaseVersion.objects.filter(case=case, status=CaseVersionStatus.LOCKED)
        .order_by("-id")
        .first()
    )
    has_snapshot = version is not None and version.snapshot is not None
    return Requirement(
        key="decision_snapshot",
        label="Snapshot keputusan tersimpan dan tidak dapat diubah",
        satisfied=has_snapshot,
        detail=(
            f"Versi {version.version_number}" if has_snapshot
            else ("Versi terkunci tanpa snapshot" if version else "Belum ada versi terkunci")
        ),
    )


def _signoff_requirement(case) -> Requirement:
    count = case.approvals.count()
    return Requirement(
        key="signoff",
        label="Sign-off Ketua KFT tercatat",
        satisfied=count > 0,
        detail=f"{count} tanda tangan tercatat" if count else "Belum ada tanda tangan",
    )


def evaluate_integrity(case) -> dict:
    """Readiness plus the artefacts a locked decision must carry to be archived."""
    readiness = evaluate_readiness(case)
    extra = [_snapshot_requirement(case), _signoff_requirement(case)]

    requirements = readiness["requirements"] + [r.as_dict() for r in extra]
    failures = list(readiness["missing"]) + [
        r.label for r in extra if r.mandatory and not r.satisfied
    ]

    return {
        "is_valid": not failures,
        "requirements": requirements,
        "failures": failures,
        "suggested_flag": FLAG_OK if not failures else FLAG_REQUIRES_REMEDIATION,
    }
