"""Re-check stored hashes against the files actually on disk.

Round 4 item 7:

    "Uji juga bahwa DOCX/PDF sesuai dengan data versi terkunci dan pemeriksaan
     hash dapat mendeteksi perubahan pada salinan dokumen uji."

Recording a SHA-256 at generation time only helps if something later re-reads
the file and compares. This does that, so tampering with an archived document is
detectable rather than merely theoretically detectable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

STATUS_OK = "ok"
STATUS_MODIFIED = "modified"
STATUS_MISSING = "missing"
STATUS_NO_HASH = "no_hash_recorded"


@dataclass(frozen=True)
class FileCheck:
    label: str
    path: str
    status: str
    expected_sha256: str = ""
    actual_sha256: str = ""

    @property
    def is_ok(self) -> bool:
        return self.status == STATUS_OK

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path": self.path,
            "status": self.status,
            "expected_sha256": self.expected_sha256,
            "actual_sha256": self.actual_sha256,
        }


@dataclass
class VerificationReport:
    case_id: str
    checks: list[FileCheck] = field(default_factory=list)

    @property
    def is_intact(self) -> bool:
        return all(c.is_ok for c in self.checks)

    @property
    def failures(self) -> list[FileCheck]:
        return [c for c in self.checks if not c.is_ok]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "is_intact": self.is_intact,
            "checks": [c.as_dict() for c in self.checks],
        }


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(label: str, relative_path: str, expected: str) -> FileCheck:
    from apps.policy_brief.service import absolute_path

    if not expected:
        return FileCheck(label=label, path=relative_path, status=STATUS_NO_HASH)

    absolute = absolute_path(relative_path)
    if not absolute.exists():
        return FileCheck(
            label=label,
            path=relative_path,
            status=STATUS_MISSING,
            expected_sha256=expected,
        )

    actual = sha256_of(absolute)
    return FileCheck(
        label=label,
        path=relative_path,
        status=STATUS_OK if actual == expected else STATUS_MODIFIED,
        expected_sha256=expected,
        actual_sha256=actual,
    )


def verify_case_documents(case) -> VerificationReport:
    """Re-hash every policy brief file for a case and compare with what was stored."""
    from apps.policy_brief.models import PolicyBriefDocument

    report = VerificationReport(case_id=case.case_id)

    briefs = PolicyBriefDocument.objects.filter(case=case).order_by("version")
    for brief in briefs:
        if brief.docx_path:
            report.checks.append(
                _check(f"Policy brief v{brief.version} (DOCX)", brief.docx_path, brief.docx_sha256)
            )
        if brief.pdf_path:
            report.checks.append(
                _check(f"Policy brief v{brief.version} (PDF)", brief.pdf_path, brief.pdf_sha256)
            )

    return report
