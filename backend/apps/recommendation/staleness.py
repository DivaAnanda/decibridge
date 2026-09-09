"""Detect a stored recommendation whose inputs have since changed.

Round 3: `HF_ARNI_ACEI_001` carried a recommendation whose justification read
"BIA belum dijalankan" while a BIA result of Rp399.001.222 already existed. The
recommendation was correct when computed and never revisited, so the case
displayed a confident verdict built on inputs that no longer applied.

Staleness is derived at read time rather than stored, so it cannot itself go
stale: every input that feeds `compute_recommendation` is compared against the
recommendation's own `computed_at`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

REASON_ECON = "Analisis ekonomi (CEA) telah dihitung ulang setelah rekomendasi ini dibuat."
REASON_BIA = "Analisis dampak anggaran (BIA) telah dihitung ulang setelah rekomendasi ini dibuat."
REASON_ETD = "Penilaian EtD telah berubah setelah rekomendasi ini dibuat."
REASON_WEIGHTS = "Bobot domain telah berubah setelah rekomendasi ini dibuat."
REASON_CBA = "Kriteria CBA telah berubah setelah rekomendasi ini dibuat."


@dataclass(frozen=True)
class StalenessReport:
    is_stale: bool
    reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {"is_stale": self.is_stale, "stale_reasons": self.reasons}


def _latest(queryset, field: str) -> datetime | None:
    return queryset.order_by(f"-{field}").values_list(field, flat=True).first()


def evaluate_staleness(case, recommendation) -> StalenessReport:
    """Compare every recommendation input against `recommendation.computed_at`."""
    from apps.etd.models import EtDAppraisal
    from apps.recommendation.models import CBACriterion, DomainWeightVote

    computed_at = recommendation.computed_at
    reasons: list[str] = []

    checks = (
        (_latest(case.econ_deterministic_results.all(), "computed_at"), REASON_ECON),
        (_latest(case.econ_bia_results.all(), "computed_at"), REASON_BIA),
        (_latest(EtDAppraisal.objects.filter(case=case), "updated_at"), REASON_ETD),
        (_latest(DomainWeightVote.objects.filter(case=case), "updated_at"), REASON_WEIGHTS),
        (_latest(CBACriterion.objects.filter(case=case), "updated_at"), REASON_CBA),
    )

    for changed_at, reason in checks:
        if changed_at is not None and changed_at > computed_at:
            reasons.append(reason)

    return StalenessReport(is_stale=bool(reasons), reasons=reasons)
