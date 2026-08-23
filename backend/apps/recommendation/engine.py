"""Pure synthesis engine — turns CEA + BIA + EtD + CBA into a traffic-light.

Per the brief's §5 traffic-light formula:
    Score = 0.40 · Evidence + 0.30 · CE + 0.20 · Budget + 0.10 · CBA
Where each sub-score is 0-100 and weights are normalised.

Traffic-light assignment:
    Score >= 75 AND CBA satisfied/absent   → GREEN  (adopt)
    Score >= 60 OR CBA partially satisfied → YELLOW (conditional adoption)
    Otherwise → RED (do not adopt)

Phase R3 (post-demo lecturer revision — safe missing-data handling):
    * A recommendation is only computed when ALL mandatory components exist
      (EtD evidence, cost-effectiveness, budget impact). If any is missing the
      result is `status == "incomplete"` with a `missing_components` list and NO
      traffic light — the UI shows "Belum dapat dihitung", never a misleading RED.
    * An empty CBA is treated as **not assessed** (`cba_score = None`), NOT an
      automatic 100. The composite is re-normalised over the components that are
      actually present, so a missing component is never silently scored 0 or 100.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

ALGORITHM_VERSION = "2.0.0"

# Sub-score weights (from the brief's §6 — sum to 1.00).
W_EVIDENCE = Decimal("0.40")
W_CE = Decimal("0.30")
W_BUDGET = Decimal("0.20")
W_CBA = Decimal("0.10")

GREEN_THRESHOLD = Decimal("75")
YELLOW_THRESHOLD = Decimal("60")

STATUS_COMPLETE = "complete"
STATUS_INCOMPLETE = "incomplete"

# Human labels for the mandatory components (shown in the missing list).
LABEL_EVIDENCE = "Penilaian EtD (9 domain)"
LABEL_CE = "Analisis ekonomi (cost-effectiveness)"
LABEL_BUDGET = "Analisis dampak anggaran (BIA)"


@dataclass(frozen=True)
class SynthesisInput:
    evidence_strength_score: Decimal | None  # from EtD aggregate (0-100)
    ce_score: Decimal | None  # from latest deterministic econ result (0-100)
    budget_score: Decimal | None  # from latest BIA result (0-100)
    cba_criteria_count: int
    cba_satisfied_count: int

    def snapshot(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in d.items()}


@dataclass(frozen=True)
class SynthesisResult:
    status: str  # STATUS_COMPLETE | STATUS_INCOMPLETE
    missing_components: list[str]
    evidence_strength_score: Decimal | None
    ce_score: Decimal | None
    budget_score: Decimal | None
    cba_score: Decimal | None  # None = not assessed (no criteria defined)
    composite_score: Decimal | None  # None when incomplete
    traffic_light: str | None  # None when incomplete
    justification_text: str
    cba_criteria_count: int
    cba_satisfied_count: int
    algorithm_version: str = ALGORITHM_VERSION


def _cba_score(criteria_count: int, satisfied_count: int) -> Decimal:
    """CBA contribution when criteria ARE defined (0-100).

    - All satisfied: 100
    - Some satisfied: 50
    - None satisfied: 0
    (The no-criteria case is handled by the caller as "not assessed", not 100.)
    """
    if satisfied_count >= criteria_count:
        return Decimal("100")
    if satisfied_count > 0:
        return Decimal("50")
    return Decimal("0")


def compute_recommendation(inp: SynthesisInput) -> SynthesisResult:
    # ── Mandatory-component gate (R3) ────────────────────────────────────
    missing: list[str] = []
    if inp.evidence_strength_score is None:
        missing.append(LABEL_EVIDENCE)
    if inp.ce_score is None:
        missing.append(LABEL_CE)
    if inp.budget_score is None:
        missing.append(LABEL_BUDGET)

    if missing:
        return SynthesisResult(
            status=STATUS_INCOMPLETE,
            missing_components=missing,
            evidence_strength_score=inp.evidence_strength_score,
            ce_score=inp.ce_score,
            budget_score=inp.budget_score,
            cba_score=None,
            composite_score=None,
            traffic_light=None,
            justification_text=_incomplete_narrative(missing),
            cba_criteria_count=inp.cba_criteria_count,
            cba_satisfied_count=inp.cba_satisfied_count,
        )

    evidence = inp.evidence_strength_score
    ce = inp.ce_score
    budget = inp.budget_score

    cba_defined = inp.cba_criteria_count > 0
    if cba_defined:
        cba_score: Decimal | None = _cba_score(inp.cba_criteria_count, inp.cba_satisfied_count)
        composite = (
            evidence * W_EVIDENCE + ce * W_CE + budget * W_BUDGET + cba_score * W_CBA
        ).quantize(Decimal("0.01"))
    else:
        # CBA not assessed → exclude it and re-normalise over present components.
        cba_score = None
        present_weight = W_EVIDENCE + W_CE + W_BUDGET
        composite = (
            (evidence * W_EVIDENCE + ce * W_CE + budget * W_BUDGET) / present_weight
        ).quantize(Decimal("0.01"))

    cba_fully = cba_defined and inp.cba_satisfied_count == inp.cba_criteria_count
    cba_partial = cba_defined and 0 < inp.cba_satisfied_count < inp.cba_criteria_count

    if composite >= GREEN_THRESHOLD and (not cba_defined or cba_fully):
        light = "green"
    elif composite >= YELLOW_THRESHOLD or cba_partial:
        light = "yellow"
    else:
        light = "red"

    return SynthesisResult(
        status=STATUS_COMPLETE,
        missing_components=[],
        evidence_strength_score=evidence,
        ce_score=ce,
        budget_score=budget,
        cba_score=cba_score,
        composite_score=composite,
        traffic_light=light,
        justification_text=_complete_narrative(inp, composite, cba_score, light, cba_fully, cba_partial),
        cba_criteria_count=inp.cba_criteria_count,
        cba_satisfied_count=inp.cba_satisfied_count,
    )


def _incomplete_narrative(missing: list[str]) -> str:
    return (
        "Belum dapat dihitung — komponen wajib berikut belum tersedia: "
        + "; ".join(missing)
        + ". Rekomendasi akhir hanya dihitung setelah semua komponen wajib lengkap."
    )


def _complete_narrative(
    inp: SynthesisInput,
    composite: Decimal,
    cba_score: Decimal | None,
    light: str,
    cba_fully: bool,
    cba_partial: bool,
) -> str:
    pieces: list[str] = [f"Skor komposit: {composite} / 100."]
    pieces.append(f"Bukti EtD: {inp.evidence_strength_score} (bobot 40%).")
    pieces.append(f"CEA: {inp.ce_score} (bobot 30%).")
    pieces.append(f"Anggaran (BIA): {inp.budget_score} (bobot 20%).")

    if cba_score is None:
        pieces.append("CBA: belum dinilai (tidak ada kriteria) — dikeluarkan dari komposit, bobot dinormalisasi.")
    elif cba_fully:
        pieces.append(f"Semua {inp.cba_criteria_count} kriteria CBA terpenuhi (skor 100, bobot 10%).")
    elif cba_partial:
        pieces.append(
            f"Hanya {inp.cba_satisfied_count} dari {inp.cba_criteria_count} kriteria CBA terpenuhi "
            f"(skor 50, bobot 10%)."
        )
    else:
        pieces.append(f"Tidak ada dari {inp.cba_criteria_count} kriteria CBA terpenuhi (skor 0, bobot 10%).")

    if light == "green":
        pieces.append("REKOMENDASI: HIJAU — adopsi tanpa syarat.")
    elif light == "yellow":
        pieces.append("REKOMENDASI: KUNING — adopsi bersyarat.")
    else:
        pieces.append("REKOMENDASI: MERAH — tidak direkomendasikan untuk diadopsi saat ini.")

    return " ".join(pieces)
