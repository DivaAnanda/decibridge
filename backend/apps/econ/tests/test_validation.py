"""Excel validation import + report tests (Phase R6)."""

from __future__ import annotations

from io import BytesIO

import pytest

from apps.econ.validation_service import import_and_validate
from apps.econ.validation_workbook import build_workbook, parse_workbook

BASE = "/api/v1/cases/HF_ARNI_ACEI_001/econ"


def _workbook_bytes() -> BytesIO:
    buf = BytesIO()
    build_workbook().save(buf)
    buf.seek(0)
    return buf


class TestWorkbookRoundtrip:
    def test_build_then_parse(self):
        parsed = parse_workbook(_workbook_bytes())
        assert parsed["missing_sheets"] == []
        assert parsed["case_meta"]["case_id"] == "HF_ARNI_ACEI_001"
        assert len(parsed["params"]) == 10
        assert len(parsed["expected_deterministic"]) == 8


@pytest.mark.django_db
class TestImportAndValidate:
    def test_generated_workbook_passes(self, pilot_case, hta_user):
        report = import_and_validate(pilot_case, _workbook_bytes(), hta_user)
        assert report["status"] == "PASS", report
        assert report["issues"] == []
        # every deterministic + PSA check within tolerance
        assert all(c["pass"] for c in report["checks"])

    def test_tampered_expected_fails(self, pilot_case, hta_user):
        wb = build_workbook()
        det = wb["expected_deterministic_results"]
        det["B2"] = "99999999"  # wrong total_cost_intervention
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        report = import_and_validate(pilot_case, buf, hta_user)
        assert report["status"] == "FAIL"
        assert any(not c["pass"] for c in report["checks"])

    def test_out_of_range_probability_flagged(self, pilot_case, hta_user):
        wb = build_workbook()
        params = wb["economic_model_params"]
        # Row 3 is event_probability intervention (value col D). Force > 1.
        for row in params.iter_rows(min_row=2):
            if row[0].value == "event_probability":
                row[3].value = "1.5"
                break
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        report = import_and_validate(pilot_case, buf, hta_user)
        assert report["status"] == "FAIL"
        assert any("0–1" in issue for issue in report["issues"])


@pytest.mark.django_db
class TestValidationApi:
    def test_template_download(self, hta_client, pilot_case):
        resp = hta_client.get(f"{BASE}/validate/template/")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp["Content-Type"]

    def test_upload_returns_pass_report(self, hta_client, pilot_case):
        buf = _workbook_bytes()
        resp = hta_client.post(
            f"{BASE}/validate/",
            {"file": buf},
            format="multipart",
        )
        assert resp.status_code == 200, resp.data
        assert resp.data["status"] == "PASS"

    def test_viewer_cannot_upload(self, kft_member_client, pilot_case):
        resp = kft_member_client.post(f"{BASE}/validate/", {"file": _workbook_bytes()}, format="multipart")
        assert resp.status_code == 403
