"""Engine tests — pure functions, no Django, no Word."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from docx import Document

from apps.policy_brief import engine


def _minimal_ctx(**overrides) -> engine.BriefContext:
    base = dict(
        case=engine.CaseInfo(
            case_id="HF_TEST_001",
            title="ARNI vs ACEI test",
            intervention="Sacubitril/Valsartan",
            comparator="Enalapril",
            indication="HFrEF",
            population="Adults",
            setting="Hospital",
            perspective="Rumah Sakit",
            created_by_name="Dr. Test",
            status="Disetujui",
        ),
        cea=None,
        bia=None,
        etd=None,
        cba=None,
        recommendation=None,
        references=[],
        approvals=[],
        generated_at=datetime(2026, 6, 8, 14, 30),
        version=1,
    )
    base.update(overrides)
    return engine.BriefContext(**base)


def _read_docx(data: bytes) -> Document:
    return Document(io.BytesIO(data))


class TestMinimalDoc:
    def test_returns_nonempty_bytes(self):
        ctx = _minimal_ctx()
        out = engine.build_docx_bytes(ctx)
        assert isinstance(out, bytes)
        assert len(out) > 5_000  # DOCX zip overhead alone is >5 KB

    def test_cover_section_contains_case_id(self):
        ctx = _minimal_ctx()
        doc = _read_docx(engine.build_docx_bytes(ctx))
        text = "\n".join(p.text for p in doc.paragraphs)
        text += "\n".join(
            cell.text for table in doc.tables for row in table.rows for cell in row.cells
        )
        assert "HF_TEST_001" in text
        assert "ARNI vs ACEI test" in text
        assert "Sacubitril/Valsartan" in text

    def test_no_rec_falls_back_to_placeholder(self):
        ctx = _minimal_ctx()
        doc = _read_docx(engine.build_docx_bytes(ctx))
        body = "\n".join(p.text for p in doc.paragraphs)
        assert "Rekomendasi belum tersedia" in body


class TestRecommendationSection:
    def test_green_traffic_light_renders(self):
        ctx = _minimal_ctx(
            recommendation=engine.RecommendationBlock(
                traffic_light="green",
                traffic_light_label="HIJAU — Adopsi tanpa syarat",
                composite_score=Decimal("85.50"),
                evidence_score=Decimal("90.00"),
                ce_score=Decimal("100.00"),
                budget_score=Decimal("70.00"),
                cba_score=Decimal("100.00"),
                justification_text="Strong evidence + cost-saving.",
                computed_at=datetime(2026, 6, 8, 12, 0),
                algorithm_version="1.0.0",
            )
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        all_text = "\n".join(p.text for p in doc.paragraphs)
        all_text += "\n".join(
            cell.text for table in doc.tables for row in table.rows for cell in row.cells
        )
        assert "HIJAU" in all_text.upper()
        assert "85.50" in all_text
        assert "Strong evidence" in all_text


class TestCEASection:
    def test_cea_block_renders_values(self):
        ctx = _minimal_ctx(
            cea=engine.CEABlock(
                icer=Decimal("10000000"),
                dominance_label="Cost-effective (aman)",
                cost_drug=Decimal("10000000"),
                cost_comparator=Decimal("5000000"),
                efficacy_drug=Decimal("2.5"),
                efficacy_comparator=Decimal("2.0"),
                wtop_threshold=Decimal("250000000"),
                ce_score=Decimal("100"),
                sensitivity_low_icer=Decimal("8000000"),
                sensitivity_high_icer=Decimal("12000000"),
            )
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        all_text = "\n".join(
            cell.text for table in doc.tables for row in table.rows for cell in row.cells
        )
        body_text = "\n".join(p.text for p in doc.paragraphs)
        combined = all_text + "\n" + body_text
        assert "Cost-effective" in combined
        assert "Rp 10.000.000" in combined
        assert "sensitivitas" in combined.lower()

    def test_qaly_is_not_rounded_to_two_places(self):
        """The training case: 0.695 printed as 0.70, off from every other screen."""
        ctx = _minimal_ctx(
            cea=engine.CEABlock(
                icer=Decimal("225454545.45"),
                dominance_label="Cost-effective pada WTP terpilih",
                cost_drug=Decimal("16500000"),
                cost_comparator=Decimal("4100000"),
                efficacy_drug=Decimal("0.75"),
                efficacy_comparator=Decimal("0.695"),
                wtop_threshold=Decimal("300000000"),
                ce_score=Decimal("100"),
                sensitivity_low_icer=None,
                sensitivity_high_icer=None,
            )
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        cells = [c.text for t in doc.tables for r in t.rows for c in r.cells]

        assert "0.6950" in cells
        assert "0.7500" in cells
        assert "0.70" not in cells


class TestBIASection:
    def test_bia_three_year_table_has_four_rows(self):
        # Header + 3 years + cumulative = 5 rows
        ctx = _minimal_ctx(
            bia=engine.BIABlock(
                rows=[
                    engine.BIAYearRow(
                        year=1, patients=1000, cost_impact=Decimal("1_000_000_000"),
                        pct_of_budget=Decimal("10.0"),
                    ),
                    engine.BIAYearRow(
                        year=2, patients=1000, cost_impact=Decimal("2_000_000_000"),
                        pct_of_budget=Decimal("20.0"),
                    ),
                    engine.BIAYearRow(
                        year=3, patients=1000, cost_impact=Decimal("3_000_000_000"),
                        pct_of_budget=Decimal("30.0"),
                    ),
                ],
                cumulative_impact=Decimal("6_000_000_000"),
                cumulative_pct_of_budget=Decimal("60.0"),
                severity_label="Significant (10-50%)",
            )
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        bia_tables = [
            t for t in doc.tables
            if any("Periode" in cell.text for row in t.rows for cell in row.cells)
        ]
        assert len(bia_tables) == 1
        bia_table = bia_tables[0]
        assert len(bia_table.rows) == 5  # header + 3 years + cumulative

        body = "\n".join(
            cell.text for row in bia_table.rows for cell in row.cells
        )
        assert "Significant" in "\n".join(p.text for p in doc.paragraphs)
        assert "Rp 6.000.000.000" in body


class TestEtDSection:
    def test_etd_renders_9_domains(self):
        rows = [
            engine.EtDDomainRow(
                code=f"domain_{i}",
                label=f"Domain {i}",
                mean_judgement=Decimal("75"),
                judgement_label="Mungkin ya",
                dominant_certainty="Sedang",
                member_count=2,
            )
            for i in range(1, 10)
        ]
        ctx = _minimal_ctx(
            etd=engine.EtDBlock(
                rows=rows,
                aggregated_evidence_score=Decimal("82.50"),
                domains_filled=9,
                domains_total=9,
            )
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        etd_tables = [
            t for t in doc.tables
            if any("Domain" == cell.text or "Domain" in cell.text for row in t.rows for cell in row.cells[:1])
        ]
        assert any(
            len(t.rows) >= 10 for t in etd_tables  # header + 9 domains
        )


class TestReferences:
    def test_references_numbered(self):
        refs = [
            engine.ReferenceRow(
                number=1, citation="A et al.", authors="A et al.",
                year=2014, journal="NEJM", doi_or_url="10.1056/NEJMoa1409077",
            ),
            engine.ReferenceRow(
                number=2, citation="B et al.", authors="B et al.",
                year=2020, journal="Lancet", doi_or_url="",
            ),
        ]
        ctx = _minimal_ctx(references=refs)
        doc = _read_docx(engine.build_docx_bytes(ctx))
        all_paragraph_text = "\n".join(p.text for p in doc.paragraphs)
        assert "[1]" in all_paragraph_text
        assert "[2]" in all_paragraph_text
        assert "NEJM" in all_paragraph_text


class TestApprovalSection:
    def test_signature_row_appears(self):
        ctx = _minimal_ctx(
            approvals=[
                engine.ApprovalRow(
                    decision="approved",
                    decision_label="Disetujui",
                    approver_name="Dr. Ketua",
                    approver_email="ketua@test.local",
                    signed_at=datetime(2026, 6, 8, 14, 30),
                    reason="",
                    ip_address="127.0.0.1",
                )
            ]
        )
        doc = _read_docx(engine.build_docx_bytes(ctx))
        all_text = "\n".join(
            cell.text for table in doc.tables for row in table.rows for cell in row.cells
        )
        assert "Disetujui" in all_text
        assert "ketua@test.local" in all_text
        assert "127.0.0.1" in all_text


class TestFormatting:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (Decimal("1000"), "Rp 1.000"),
            (Decimal("10000000"), "Rp 10.000.000"),
            (None, "—"),
        ],
    )
    def test_idr_formatting(self, value, expected):
        assert engine._idr(value) == expected

    def test_date_id_formatting(self):
        d = datetime(2026, 6, 8)
        assert engine._date_id(d) == "8 Juni 2026"

    def test_utc_timestamp_is_converted_before_it_is_labelled_wib(self):
        """A database timestamp is UTC; 12:38 UTC is 19:38 in Jakarta."""
        stored = datetime(2026, 10, 13, 12, 38, tzinfo=UTC)

        assert engine._datetime_id(stored) == "13 Oktober 2026, 19:38 WIB"

    def test_conversion_can_move_the_date(self):
        stored = datetime(2026, 10, 13, 18, 5, tzinfo=UTC)

        assert engine._datetime_id(stored) == "14 Oktober 2026, 01:05 WIB"

    def test_naive_local_time_is_left_alone(self):
        assert engine._datetime_id(datetime(2026, 6, 8, 14, 30)) == "8 Juni 2026, 14:30 WIB"


class TestSignerAddress:
    def test_service_masks_the_address_before_it_reaches_the_document(self):
        """Every role can download a brief, so it follows the on-screen masking."""
        from types import SimpleNamespace
        from unittest.mock import patch

        from apps.policy_brief import service

        approval = SimpleNamespace(
            decision="approved",
            approver=SimpleNamespace(full_name="Ketua", email="ketua@example.com"),
            signed_at=datetime(2026, 10, 13, 12, 0, tzinfo=UTC),
            reason="",
            ip_address="203.0.113.77",
        )
        queryset = SimpleNamespace(
            select_related=lambda *a: SimpleNamespace(order_by=lambda *b: [approval])
        )
        with patch.object(service.Approval.objects, "filter", return_value=queryset):
            rows = service._build_approvals(case=None)

        assert rows[0].ip_address == "203.0.113.xxx"


def _all_text(data: bytes) -> str:
    doc = _read_docx(data)
    parts = [p.text for p in doc.paragraphs]
    parts += [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
    return "\n".join(parts)


def _psa(**overrides) -> engine.PSABlock:
    base = dict(
        n_simulations=5000,
        seed=42,
        wtp_base=Decimal("250000000"),
        prob_cost_effective=Decimal("0.5602"),
        mean_incremental_cost=Decimal("12400000"),
        mean_incremental_qaly=Decimal("0.05512"),
        base_case_incremental_cost=Decimal("12400000"),
        base_case_incremental_qaly=Decimal("0.055"),
        interpretation_text="Peluang ARNI cost-effective 56%.",
        computed_at=datetime(2026, 10, 26, 5, 0, tzinfo=UTC),
        is_current=True,
        ceac=[
            engine.CEACPoint(wtp=Decimal("0"), probability=0.0),
            engine.CEACPoint(wtp=Decimal("250000000"), probability=0.5602),
        ],
    )
    base.update(overrides)
    return engine.PSABlock(**base)


class TestRound5Content:
    """Round 5 item 2: "tambahkan hasil PSA + pertanyaan keputusan + populasi target"."""

    def test_decision_question_with_its_pico(self):
        ctx = _minimal_ctx(
            decision_questions=[
                engine.DecisionQuestionRow(
                    number=1,
                    question="Apakah ARNI perlu masuk formularium?",
                    population="Pasien HFrEF dewasa, EF <= 40%",
                    intervention="ARNI",
                    comparator="Ramipril",
                    outcome="Rehospitalisasi 12 bulan",
                )
            ]
        )

        text = _all_text(engine.build_docx_bytes(ctx))

        assert "Pertanyaan Keputusan dan Populasi Target" in text
        assert "Apakah ARNI perlu masuk formularium?" in text
        assert "Pasien HFrEF dewasa, EF <= 40%" in text
        assert "Rehospitalisasi 12 bulan" in text

    def test_target_population_is_on_the_cover(self):
        doc = _read_docx(engine.build_docx_bytes(_minimal_ctx()))
        cover = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}

        assert cover["Populasi target"] == "Adults"
        assert cover["Perspektif"] == "Rumah Sakit"

    def test_psa_results(self):
        text = _all_text(engine.build_docx_bytes(_minimal_ctx(psa=_psa())))

        assert "Analisis Sensitivitas Probabilistik (PSA)" in text
        assert "56.0%" in text
        assert "5.000" in text
        assert "Rp 12.400.000" in text
        assert "Peluang ARNI cost-effective 56%." in text

    def test_psa_curve_points_are_listed(self):
        text = _all_text(engine.build_docx_bytes(_minimal_ctx(psa=_psa())))

        assert "Rp 250.000.000" in text
        assert "0.0%" in text

    def test_missing_psa_is_stated(self):
        text = _all_text(engine.build_docx_bytes(_minimal_ctx()))

        assert "PSA belum dijalankan" in text

    @pytest.mark.parametrize(
        ("is_current", "note"),
        [(False, "input berubah setelah PSA ini dijalankan"), (None, "13 Oktober 2026")],
    )
    def test_outdated_psa_is_flagged(self, is_current, note):
        text = _all_text(engine.build_docx_bytes(_minimal_ctx(psa=_psa(is_current=is_current))))

        assert note in text

    def test_final_decision_leads_the_summary(self):
        ctx = _minimal_ctx(
            final_decision=engine.FinalDecisionBlock(
                decision_label="Adopsi dengan kriteria akses (Adopt with criteria-based access)",
                reason="ICER di bawah ambang; akses dibatasi EF <= 40%.",
                decided_by="Dr. Anggota",
                decided_at=datetime(2026, 10, 26, 5, 0, tzinfo=UTC),
                on_latest_recommendation=True,
            )
        )

        body = "\n".join(p.text for p in _read_docx(engine.build_docx_bytes(ctx)).paragraphs)

        assert body.index("Keputusan Final KFT") < body.index("Rekomendasi Sistem")
        assert "Adopt with criteria-based access" in body
        assert "ICER di bawah ambang; akses dibatasi EF <= 40%." in body
        assert "Dr. Anggota" in body

    def test_missing_final_decision_is_stated(self):
        body = "\n".join(p.text for p in _read_docx(engine.build_docx_bytes(_minimal_ctx())).paragraphs)

        assert "Keputusan Final KFT belum dicatat" in body


def test_criteria_without_a_cba_score_still_render():
    """UAT_LENGKAP has a criterion but its recommendation has no CBA score; the
    brief failed with a TypeError formatting None."""
    ctx = _minimal_ctx(
        cba=engine.CBABlock(
            rows=[
                engine.CBACriterionRow(
                    label="Diresepkan dokter spesialis jantung",
                    operator="Ada",
                    value="-",
                    satisfied=True,
                    notes="",
                )
            ],
            cba_score=None,
            satisfied_count=1,
            total_count=1,
        )
    )

    body = "\n".join(p.text for p in _read_docx(engine.build_docx_bytes(ctx)).paragraphs)

    assert "Skor CBA: Belum dinilai" in body
