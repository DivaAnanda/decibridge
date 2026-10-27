"""Policy-brief DOCX builder. Pure functions, no Django imports.

Trivially testable: feed in a `BriefContext` dataclass, get bytes out.

Sections (in order):
    Cover                — case_id, title, drugs, target population, setting, perspective
    1. Executive summary — the KFT final decision, then the system's traffic light
    2. Decision question — each PICO question and the target population
    3. CEA               — ICER, dominance, sensitivity table
    4. BIA               — per-year + cumulative table, % budget
    5. PSA               — iterations, seed, P(cost-effective), mean increments, CEAC points
    6. EtD               — per-domain table with mean judgement + dominant certainty
    7. CBA               — table, satisfaction status
    8. References        — numbered bibliography
    9. Audit summary     — signature timestamp + IP + approver name

Round 5 item 2 added the decision question, target population and PSA; item 3
added the KFT final decision.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor


# ----------------------------------------------------------------------------
# Data shapes — populated by the service layer from Django models.
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseInfo:
    case_id: str
    title: str
    intervention: str
    comparator: str
    indication: str
    population: str
    setting: str
    perspective: str
    created_by_name: str
    status: str  # localized label, e.g. "Disetujui"


@dataclass(frozen=True)
class CEABlock:
    icer: Decimal | None
    dominance_label: str  # localized
    cost_drug: Decimal
    cost_comparator: Decimal
    efficacy_drug: Decimal
    efficacy_comparator: Decimal
    wtop_threshold: Decimal
    ce_score: Decimal  # 0-100
    sensitivity_low_icer: Decimal | None = None
    sensitivity_high_icer: Decimal | None = None


@dataclass(frozen=True)
class BIAYearRow:
    year: int
    patients: int
    cost_impact: Decimal
    pct_of_budget: Decimal


@dataclass(frozen=True)
class BIABlock:
    rows: list[BIAYearRow]
    cumulative_impact: Decimal
    cumulative_pct_of_budget: Decimal
    severity_label: str  # localized


@dataclass(frozen=True)
class EtDDomainRow:
    code: str
    label: str  # localized
    mean_judgement: Decimal | None  # 0-100
    judgement_label: str  # localized
    dominant_certainty: str  # localized, e.g. "Tinggi"
    member_count: int


@dataclass(frozen=True)
class EtDBlock:
    rows: list[EtDDomainRow]
    aggregated_evidence_score: Decimal
    domains_filled: int
    domains_total: int


@dataclass(frozen=True)
class CBACriterionRow:
    label: str
    operator: str
    value: str
    satisfied: bool
    notes: str


@dataclass(frozen=True)
class CBABlock:
    rows: list[CBACriterionRow]
    cba_score: Decimal
    satisfied_count: int
    total_count: int


@dataclass(frozen=True)
class RecommendationBlock:
    traffic_light: str  # "green" | "yellow" | "red"
    traffic_light_label: str  # localized
    composite_score: Decimal
    evidence_score: Decimal
    ce_score: Decimal
    budget_score: Decimal
    cba_score: Decimal
    justification_text: str
    computed_at: datetime
    algorithm_version: str


@dataclass(frozen=True)
class ReferenceRow:
    number: int
    citation: str
    authors: str
    year: int | None
    journal: str
    doi_or_url: str


@dataclass(frozen=True)
class ApprovalRow:
    decision: str  # "approved" | "rejected" | "revision_requested"
    decision_label: str  # localized
    approver_name: str
    approver_email: str
    signed_at: datetime
    reason: str
    ip_address: str


@dataclass(frozen=True)
class DecisionQuestionRow:
    number: int
    question: str
    population: str
    intervention: str
    comparator: str
    outcome: str


@dataclass(frozen=True)
class CEACPoint:
    wtp: Decimal
    probability: float  # 0-1


@dataclass(frozen=True)
class PSABlock:
    n_simulations: int
    seed: int
    wtp_base: Decimal
    prob_cost_effective: Decimal  # 0-1
    mean_incremental_cost: Decimal
    mean_incremental_qaly: Decimal
    base_case_incremental_cost: Decimal
    base_case_incremental_qaly: Decimal
    interpretation_text: str
    computed_at: datetime
    # False: an input changed after the run. None: the run predates recorded
    # inputs (2026-10-13), so it cannot be checked.
    is_current: bool | None
    ceac: list[CEACPoint] = field(default_factory=list)


@dataclass(frozen=True)
class FinalDecisionBlock:
    decision_label: str
    reason: str
    decided_by: str
    decided_at: datetime
    on_latest_recommendation: bool


@dataclass(frozen=True)
class BriefContext:
    case: CaseInfo
    cea: CEABlock | None
    bia: BIABlock | None
    etd: EtDBlock | None
    cba: CBABlock | None
    recommendation: RecommendationBlock | None
    references: list[ReferenceRow] = field(default_factory=list)
    approvals: list[ApprovalRow] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    decision_questions: list[DecisionQuestionRow] = field(default_factory=list)
    psa: PSABlock | None = None
    final_decision: FinalDecisionBlock | None = None


# ----------------------------------------------------------------------------
# Formatting helpers
# ----------------------------------------------------------------------------


def _idr(value: Decimal | int | float | None) -> str:
    if value is None:
        return "—"
    return f"Rp {value:,.0f}".replace(",", ".")


def _count(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _probability(value: Decimal | float) -> str:
    return f"{float(value) * 100:.1f}%"


def _pct(value: Decimal | float | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f}%"


def _num(value: Decimal | float | int | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{decimals}f}"


def _date_id(value: datetime) -> str:
    bulan = [
        "",
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]
    return f"{value.day} {bulan[value.month]} {value.year}"


_WIB = ZoneInfo("Asia/Jakarta")


def _datetime_id(value: datetime) -> str:
    # Timestamps read from the database are UTC; printing them as they came
    # put "12:38 WIB" next to an issue time of "19:38 WIB" on the same page.
    local = value.astimezone(_WIB) if value.tzinfo else value
    return f"{_date_id(local)}, {local.strftime('%H:%M')} WIB"


TRAFFIC_LIGHT_COLORS = {
    "green": RGBColor(0x2F, 0x9E, 0x44),
    "yellow": RGBColor(0xF0, 0x8C, 0x00),
    "red": RGBColor(0xE0, 0x39, 0x31),
}


# ----------------------------------------------------------------------------
# Document construction
# ----------------------------------------------------------------------------


def _add_heading(doc, text: str, level: int = 1) -> None:
    heading = doc.add_heading(text, level=level)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1C, 0x4E, 0x80)


def _add_table(doc, headers: list[str], rows: list[list[str]]):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    head_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        head_cells[i].text = h
        for paragraph in head_cells[i].paragraphs:
            for run in paragraph.runs:
                run.bold = True
        head_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for r, row in enumerate(rows, start=1):
        cells = table.rows[r].cells
        for i, val in enumerate(row):
            cells[i].text = val
    return table


def _add_traffic_light_box(doc, recommendation: RecommendationBlock) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    cell = table.rows[0].cells[0]
    cell.width = Cm(16)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(recommendation.traffic_light_label.upper())
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    bg_hex = {
        "green": "2F9E44",
        "yellow": "F08C00",
        "red": "E03131",
    }.get(recommendation.traffic_light, "808080")
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), bg_hex)
    cell._tc.get_or_add_tcPr().append(shading)


# ----------------------------------------------------------------------------
# Section builders
# ----------------------------------------------------------------------------


def _build_cover(doc, ctx: BriefContext) -> None:
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run("RINGKASAN KEBIJAKAN FORMULARIUM")
    title_run.bold = True
    title_run.font.size = Pt(20)
    title_run.font.color.rgb = RGBColor(0x1C, 0x4E, 0x80)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run("Komite Farmasi dan Terapi (KFT)")
    sub_run.italic = True
    sub_run.font.size = Pt(12)

    doc.add_paragraph()

    info = [
        ("ID Kasus", ctx.case.case_id),
        ("Judul", ctx.case.title),
        ("Intervensi", ctx.case.intervention),
        ("Komparator", ctx.case.comparator),
        ("Indikasi", ctx.case.indication),
        ("Populasi target", ctx.case.population or "—"),
        ("Setting", ctx.case.setting or "—"),
        ("Perspektif", ctx.case.perspective or "—"),
        ("Status saat ini", ctx.case.status),
        ("Versi dokumen", f"v{ctx.version}"),
        ("Tanggal terbit", _date_id(ctx.generated_at)),
    ]
    info_table = doc.add_table(rows=len(info), cols=2)
    info_table.style = "Light List Accent 1"
    for i, (k, v) in enumerate(info):
        cells = info_table.rows[i].cells
        cells[0].text = k
        cells[1].text = v
        for paragraph in cells[0].paragraphs:
            for run in paragraph.runs:
                run.bold = True

    doc.add_paragraph()


def _score(value, *, suffix: str = "") -> str:
    """Render a sub-score, or say so when it was never assessed.

    Sub-scores are nullable by design: an absent CBA is "not assessed" rather
    than zero, and a BIA without a budget baseline scores null. Formatting those
    with :.2f raised TypeError and failed the whole document.
    """
    if value is None:
        return "Belum dinilai"
    return f"{value:.2f}{suffix}"


def _build_final_decision(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "Keputusan Final KFT", level=2)
    decision = ctx.final_decision
    if decision is None:
        doc.add_paragraph("Keputusan Final KFT belum dicatat untuk kasus ini.")
        return

    label = doc.add_paragraph().add_run(decision.decision_label)
    label.bold = True
    label.font.size = Pt(14)
    reason = doc.add_paragraph()
    reason.add_run("Alasan: ").bold = True
    reason.add_run(decision.reason)
    doc.add_paragraph(f"Dicatat oleh {decision.decided_by}, {_datetime_id(decision.decided_at)}.")
    if not decision.on_latest_recommendation:
        doc.add_paragraph(
            "Catatan: keputusan ini dicatat atas rekomendasi sistem yang kemudian dihitung ulang."
        )


def _build_executive_summary(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "1. Ringkasan Eksekutif", level=1)
    _build_final_decision(doc, ctx)

    _add_heading(doc, "Rekomendasi Sistem", level=2)
    if not ctx.recommendation:
        doc.add_paragraph("Rekomendasi belum tersedia untuk kasus ini.")
        return
    doc.add_paragraph(
        "Warna dan skor berikut dihitung otomatis oleh sistem sebagai bahan pertimbangan. "
        "Keputusan di atas adalah keputusan KFT."
    )

    _add_traffic_light_box(doc, ctx.recommendation)
    doc.add_paragraph()

    summary_rows = [
        ["Skor Komposit", _score(ctx.recommendation.composite_score, suffix=" / 100")],
        ["Bukti EtD (bobot 40%)", _score(ctx.recommendation.evidence_score)],
        ["Cost-effectiveness (bobot 30%)", _score(ctx.recommendation.ce_score)],
        ["Dampak Anggaran (bobot 20%)", _score(ctx.recommendation.budget_score)],
        ["Kriteria CBA (bobot 10%)", _score(ctx.recommendation.cba_score)],
        ["Algoritma", ctx.recommendation.algorithm_version],
        ["Waktu komputasi", _datetime_id(ctx.recommendation.computed_at)],
    ]
    _add_table(doc, ["Komponen", "Nilai"], summary_rows)

    doc.add_paragraph()
    just_h = doc.add_paragraph()
    just_h.add_run("Justifikasi: ").bold = True
    doc.add_paragraph(ctx.recommendation.justification_text or "—")


def _build_decision_questions(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "2. Pertanyaan Keputusan dan Populasi Target", level=1)
    target = doc.add_paragraph()
    target.add_run("Populasi target: ").bold = True
    target.add_run(ctx.case.population or "—")

    if not ctx.decision_questions:
        doc.add_paragraph("Belum ada pertanyaan keputusan untuk kasus ini.")
        return
    for q in ctx.decision_questions:
        question = doc.add_paragraph()
        question.add_run(f"Q{q.number}: ").bold = True
        question.add_run(q.question)
        _add_table(
            doc,
            ["Unsur PICO", "Isi"],
            [
                ["Populasi (P)", q.population or "—"],
                ["Intervensi (I)", q.intervention or "—"],
                ["Komparator (C)", q.comparator or "—"],
                ["Outcome (O)", q.outcome or "—"],
            ],
        )
        doc.add_paragraph()


def _build_cea(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "3. Analisis Efektivitas Biaya (CEA)", level=1)
    if not ctx.cea:
        doc.add_paragraph("Tidak ada hasil CEA untuk kasus ini.")
        return

    rows = [
        ["ICER", _idr(ctx.cea.icer) + " per unit efektivitas"],
        ["Klasifikasi dominansi", ctx.cea.dominance_label],
        ["Biaya intervensi", _idr(ctx.cea.cost_drug)],
        ["Biaya komparator", _idr(ctx.cea.cost_comparator)],
        # Four places: at two, a QALY of 0.695 printed as 0.70 and no longer
        # matched the Analisis Ekonomi tab.
        ["Efektivitas intervensi (QALY)", _num(ctx.cea.efficacy_drug, 4)],
        ["Efektivitas komparator (QALY)", _num(ctx.cea.efficacy_comparator, 4)],
        ["Ambang WTOP", _idr(ctx.cea.wtop_threshold) + " / QALY"],
        ["Skor CE", f"{ctx.cea.ce_score:.2f} / 100"],
    ]
    _add_table(doc, ["Komponen", "Nilai"], rows)

    if ctx.cea.sensitivity_low_icer is not None and ctx.cea.sensitivity_high_icer is not None:
        doc.add_paragraph()
        sens_p = doc.add_paragraph()
        sens_p.add_run("Analisis sensitivitas ±20%: ").bold = True
        sens_p.add_run(
            f"ICER batas bawah {_idr(ctx.cea.sensitivity_low_icer)} – "
            f"batas atas {_idr(ctx.cea.sensitivity_high_icer)}."
        )


def _build_bia(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "4. Analisis Dampak Anggaran (BIA)", level=1)
    if not ctx.bia:
        doc.add_paragraph("Tidak ada hasil BIA untuk kasus ini.")
        return

    rows: list[list[str]] = []
    for r in ctx.bia.rows:
        rows.append(
            [
                f"Tahun {r.year}",
                f"{r.patients:,}".replace(",", "."),
                _idr(r.cost_impact),
                _pct(r.pct_of_budget),
            ]
        )
    rows.append(
        [
            "Kumulatif",
            "—",
            _idr(ctx.bia.cumulative_impact),
            _pct(ctx.bia.cumulative_pct_of_budget),
        ]
    )
    _add_table(doc, ["Periode", "Pasien", "Dampak Biaya", "% Anggaran"], rows)

    doc.add_paragraph()
    sev_p = doc.add_paragraph()
    sev_p.add_run("Klasifikasi severity: ").bold = True
    sev_p.add_run(ctx.bia.severity_label)


_PSA_NOTE = {
    False: (
        "Catatan: input berubah setelah PSA ini dijalankan, sehingga angka di atas tidak "
        "mencerminkan input akhir."
    ),
    None: (
        "Catatan: PSA ini dijalankan sebelum input PSA dicatat (sebelum 13 Oktober 2026), "
        "sehingga kesesuaiannya dengan input akhir tidak dapat diperiksa."
    ),
}


def _build_psa(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "5. Analisis Sensitivitas Probabilistik (PSA)", level=1)
    psa = ctx.psa
    if not psa:
        doc.add_paragraph("PSA belum dijalankan untuk kasus ini.")
        return

    rows = [
        ["Jumlah iterasi", _count(psa.n_simulations)],
        ["Seed acak", str(psa.seed)],
        ["WTP dasar", _idr(psa.wtp_base) + " / QALY"],
        ["Peluang cost-effective pada WTP dasar", _probability(psa.prob_cost_effective)],
        ["Rerata selisih biaya", _idr(psa.mean_incremental_cost)],
        ["Rerata selisih QALY", _num(psa.mean_incremental_qaly, 4)],
        ["Selisih biaya base case", _idr(psa.base_case_incremental_cost)],
        ["Selisih QALY base case", _num(psa.base_case_incremental_qaly, 4)],
        ["Waktu komputasi", _datetime_id(psa.computed_at)],
    ]
    _add_table(doc, ["Komponen", "Nilai"], rows)

    if psa.ceac:
        doc.add_paragraph()
        doc.add_paragraph().add_run("Kurva penerimaan biaya-efektivitas (CEAC):").bold = True
        _add_table(
            doc,
            ["WTP per QALY", "Peluang cost-effective"],
            [[_idr(pt.wtp), _probability(pt.probability)] for pt in psa.ceac],
        )

    if psa.interpretation_text:
        doc.add_paragraph()
        doc.add_paragraph(psa.interpretation_text)
    if psa.is_current is not True:
        doc.add_paragraph(_PSA_NOTE[psa.is_current])


def _build_etd(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "6. Evidence-to-Decision (EtD) — 9 Domain GRADE", level=1)
    if not ctx.etd:
        doc.add_paragraph("Belum ada appraisal EtD untuk kasus ini.")
        return

    rows = []
    for r in ctx.etd.rows:
        rows.append(
            [
                r.label,
                _num(r.mean_judgement, decimals=2),
                r.judgement_label,
                r.dominant_certainty,
                str(r.member_count),
            ]
        )
    _add_table(
        doc,
        ["Domain", "Skor rata-rata", "Judgement", "Certainty dominan", "Voter"],
        rows,
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run(
        f"Domain terisi: {ctx.etd.domains_filled} / {ctx.etd.domains_total} · "
        f"Skor kekuatan bukti agregat: {ctx.etd.aggregated_evidence_score:.2f} / 100"
    )


def _build_cba(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "7. Kriteria Akses (CBA)", level=1)
    if not ctx.cba or not ctx.cba.rows:
        doc.add_paragraph("Tidak ada kriteria CBA yang didefinisikan.")
        return

    rows = []
    for r in ctx.cba.rows:
        rows.append(
            [
                r.label,
                r.operator,
                r.value,
                "Ya" if r.satisfied else "Belum",
                r.notes or "—",
            ]
        )
    _add_table(doc, ["Kriteria", "Operator", "Nilai", "Terpenuhi", "Catatan"], rows)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run(
        f"Status keseluruhan: {ctx.cba.satisfied_count} / {ctx.cba.total_count} kriteria terpenuhi · "
        f"Skor CBA: {_score(ctx.cba.cba_score, suffix=' / 100')}"
    )


def _build_references(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "8. Daftar Referensi", level=1)
    if not ctx.references:
        doc.add_paragraph("Tidak ada referensi terdaftar.")
        return

    for ref in ctx.references:
        parts = []
        if ref.authors:
            parts.append(ref.authors)
        if ref.year:
            parts.append(f"({ref.year})")
        if ref.citation:
            parts.append(ref.citation)
        if ref.journal:
            parts.append(f"<i>{ref.journal}</i>")
        if ref.doi_or_url:
            parts.append(ref.doi_or_url)
        text = f"[{ref.number}] " + ". ".join(p for p in parts if p)
        # Strip <i> placeholder — we add the journal as plain text.
        text = text.replace("<i>", "").replace("</i>", "")
        doc.add_paragraph(text, style="List Number")


def _build_audit_summary(doc, ctx: BriefContext) -> None:
    _add_heading(doc, "9. Ringkasan Audit & Tanda Tangan", level=1)
    if not ctx.approvals:
        doc.add_paragraph("Belum ada tanda tangan tercatat untuk kasus ini.")
        return

    rows = []
    for a in ctx.approvals:
        rows.append(
            [
                _datetime_id(a.signed_at),
                a.decision_label,
                f"{a.approver_name}\n<{a.approver_email}>",
                a.reason or "—",
                a.ip_address or "—",
            ]
        )
    _add_table(doc, ["Waktu", "Keputusan", "Penandatangan", "Alasan", "IP"], rows)

    doc.add_paragraph()
    doc.add_paragraph(
        "Dokumen ini diterbitkan oleh sistem DeciBridge dan tercatat dalam audit log "
        "yang bersifat append-only. Setiap perubahan setelah penerbitan akan tercatat "
        "sebagai versi baru dengan hash SHA-256 berbeda."
    )


def _build_footer(doc, ctx: BriefContext) -> None:
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        f"— Dokumen DeciBridge v{ctx.version} · "
        f"diterbitkan {_datetime_id(ctx.generated_at)} —"
    )
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x6C, 0x75, 0x7D)


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------


def build_docx_bytes(ctx: BriefContext) -> bytes:
    """Render the policy brief to a DOCX byte string. Pure — no IO."""
    doc = Document()

    # Page setup — A4 portrait, 2.5 cm margins.
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

    _build_cover(doc, ctx)
    doc.add_page_break()
    _build_executive_summary(doc, ctx)
    _build_decision_questions(doc, ctx)
    _build_cea(doc, ctx)
    _build_bia(doc, ctx)
    _build_psa(doc, ctx)
    _build_etd(doc, ctx)
    _build_cba(doc, ctx)
    _build_references(doc, ctx)
    _build_audit_summary(doc, ctx)
    _build_footer(doc, ctx)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


__all__ = [
    "ApprovalRow",
    "BIABlock",
    "BIAYearRow",
    "BriefContext",
    "CBABlock",
    "CBACriterionRow",
    "CEACPoint",
    "CaseInfo",
    "CEABlock",
    "DecisionQuestionRow",
    "EtDBlock",
    "EtDDomainRow",
    "FinalDecisionBlock",
    "PSABlock",
    "RecommendationBlock",
    "ReferenceRow",
    "build_docx_bytes",
]
