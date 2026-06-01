"""Pure synthesis engine — turns CEA + BIA + EtD + CBA into a traffic-light.

Per the brief's §5 traffic-light formula:
    Score = 0.40 · Evidence + 0.30 · CE + 0.20 · Budget + 0.10 · CBA
Where each sub-score is 0-100 and weights are normalised.

Traffic-light assignment:
    Score >= 75 AND CBA fully satisfied  → GREEN  (adopt unconditionally)
    Score >= 60 OR CBA partially satisfied → YELLOW (conditional adoption)
    Otherwise → RED (do not adopt)

Special overrides (from the brief's §6):
    - If evidence_tier = Low Quality but ICER cost-saving → escalate Red→Yellow
    - If unmet clinical need and only option exists → escalate Red→Yellow
    These are NOT automated here — they're captured in justification_text
    when applicable; Ketua KFT can override in Sprint 8 approval.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

ALGORITHM_VERSION = "1.0.0"

# Sub-score weights (from the brief's §6 — sum to 1.00).
W_EVIDENCE = Decimal("0.40")
W_CE = Decimal("0.30")
W_BUDGET = Decimal("0.20")
W_CBA = Decimal("0.10")

GREEN_THRESHOLD = Decimal("75")
YELLOW_THRESHOLD = Decimal("60")


@dataclass(frozen=True)
class SynthesisInput:
    evidence_strength_score: Decimal | None  # from EtD aggregate (0-100)
    ce_score: Decimal | None  # from latest CEA result (0-100)
    budget_score: Decimal | None  # from latest BIA result (0-100)
    cba_criteria_count: int
    cba_satisfied_count: int

    def snapshot(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in d.items()}


@dataclass(frozen=True)
class SynthesisResult:
    evidence_strength_score: Decimal | None
    ce_score: Decimal | None
    budget_score: Decimal | None
    cba_score: Decimal
    composite_score: Decimal
    traffic_light: str
    justification_text: str
    cba_criteria_count: int
    cba_satisfied_count: int
    algorithm_version: str = ALGORITHM_VERSION


def _cba_score(criteria_count: int, satisfied_count: int) -> Decimal:
    """CBA contribution to the composite.

    - No criteria defined: 100 (no restrictions to fail)
    - All satisfied: 100
    - Some satisfied: 50
    - None satisfied: 0
    """
    if criteria_count == 0:
        return Decimal("100")
    if satisfied_count >= criteria_count:
        return Decimal("100")
    if satisfied_count > 0:
        return Decimal("50")
    return Decimal("0")


def compute_recommendation(inp: SynthesisInput) -> SynthesisResult:
    cba = _cba_score(inp.cba_criteria_count, inp.cba_satisfied_count)

    # Treat missing sub-scores as 0 for composite (and call it out in narrative)
    evidence = inp.evidence_strength_score if inp.evidence_strength_score is not None else Decimal("0")
    ce = inp.ce_score if inp.ce_score is not None else Decimal("0")
    budget = inp.budget_score if inp.budget_score is not None else Decimal("0")

    composite = (
        evidence * W_EVIDENCE
        + ce * W_CE
        + budget * W_BUDGET
        + cba * W_CBA
    ).quantize(Decimal("0.01"))

    cba_fully = inp.cba_criteria_count > 0 and inp.cba_satisfied_count == inp.cba_criteria_count
    cba_partial = inp.cba_criteria_count > 0 and 0 < inp.cba_satisfied_count < inp.cba_criteria_count

    if composite >= GREEN_THRESHOLD and (inp.cba_criteria_count == 0 or cba_fully):
        light = "green"
    elif composite >= YELLOW_THRESHOLD or cba_partial:
        light = "yellow"
    else:
        light = "red"

    return SynthesisResult(
        evidence_strength_score=inp.evidence_strength_score,
        ce_score=inp.ce_score,
        budget_score=inp.budget_score,
        cba_score=cba,
        composite_score=composite,
        traffic_light=light,
        justification_text=_build_narrative(inp, composite, cba, light, cba_fully, cba_partial),
        cba_criteria_count=inp.cba_criteria_count,
        cba_satisfied_count=inp.cba_satisfied_count,
    )


def _build_narrative(
    inp: SynthesisInput,
    composite: Decimal,
    cba: Decimal,
    light: str,
    cba_fully: bool,
    cba_partial: bool,
) -> str:
    pieces: list[str] = []
    pieces.append(f"Skor komposit: {composite} / 100.")

    if inp.evidence_strength_score is None:
        pieces.append("Kekuatan bukti EtD belum dihitung — perlu input domain dari anggota KFT.")
    else:
        pieces.append(f"Bukti EtD: {inp.evidence_strength_score} (bobot 40%).")

    if inp.ce_score is None:
        pieces.append("CEA belum dijalankan untuk kasus ini.")
    else:
        pieces.append(f"CEA: {inp.ce_score} (bobot 30%).")

    if inp.budget_score is None:
        pieces.append("BIA belum dijalankan untuk kasus ini.")
    else:
        pieces.append(f"Anggaran (BIA): {inp.budget_score} (bobot 20%).")

    if inp.cba_criteria_count == 0:
        pieces.append("Tidak ada kriteria CBA (skor CBA otomatis 100, bobot 10%).")
    elif cba_fully:
        pieces.append(
            f"Semua {inp.cba_criteria_count} kriteria CBA terpenuhi (skor 100, bobot 10%)."
        )
    elif cba_partial:
        pieces.append(
            f"Hanya {inp.cba_satisfied_count} dari {inp.cba_criteria_count} kriteria CBA terpenuhi "
            f"(skor 50, bobot 10%)."
        )
    else:
        pieces.append(
            f"Tidak ada dari {inp.cba_criteria_count} kriteria CBA terpenuhi (skor 0, bobot 10%)."
        )

    if light == "green":
        pieces.append(
            "REKOMENDASI: HIJAU — adopsi tanpa syarat. Bukti, cost-effectiveness, dampak anggaran, "
            "dan kriteria akses lokal semua mendukung."
        )
    elif light == "yellow":
        pieces.append(
            "REKOMENDASI: KUNING — adopsi bersyarat. Perlu pemenuhan kriteria CBA atau "
            "pertimbangan domain tambahan sebelum implementasi penuh."
        )
    else:
        pieces.append(
            "REKOMENDASI: MERAH — tidak direkomendasikan untuk diadopsi pada konteks saat ini. "
            "Bukti, biaya, atau kelayakan tidak mendukung."
        )

    return " ".join(pieces)
