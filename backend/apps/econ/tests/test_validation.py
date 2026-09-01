"""Excel validation import + report tests (Phase R6)."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pytest

from apps.econ.lecturer_workbook import parse_lecturer_workbook
from apps.econ.validation_fixtures import VALIDATION_PARAMETERS
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
        assert len(parsed["params"]) == len(VALIDATION_PARAMETERS)
        # QC01-QC08 deterministic + QC09-QC11 BIA scenarios
        assert len(parsed["expected_deterministic"]) == 11


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


LECTURER_WORKBOOK = (
    Path(__file__).parent / "fixtures" / "DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx"
)


class TestLecturerWorkbookParsing:
    """The lecturer's own file must be accepted as-is (no reformatting)."""

    def test_detected_and_parsed(self):
        parsed = parse_lecturer_workbook(str(LECTURER_WORKBOOK))
        assert parsed["format"] == "lecturer"
        assert parsed["case_meta"]["case_id"] == "HF_ARNI_ACEI_001"
        assert parsed["model_scalars"]["horizon_years"] == "1"
        assert parsed["model_scalars"]["wtp_threshold"] == "85000000"
        assert parsed["psa_config"] == {"n_simulations": 1000, "seed": 20260724}
        # QC01-QC11 (QC12's expected cell is an uncomputed formula in his file).
        assert len(parsed["expected_deterministic"]) == 11

    def test_psa_distributions_extracted(self):
        params = {
            (p["key"], p["alternative"]): p
            for p in parse_lecturer_workbook(str(LECTURER_WORKBOOK))["params"]
        }
        arni_prob = params[("event_probability", "intervention")]
        assert arni_prob["distribution"] == "beta"
        assert arni_prob["value"] == Decimal("0.45")
        arni_drug = params[("drug_cost", "intervention")]
        assert arni_drug["distribution"] == "gamma"
        assert arni_drug["value"] == Decimal("15399360")


@pytest.mark.django_db
class TestLecturerWorkbookValidation:
    """End-to-end: import his real workbook and reproduce every QC check."""

    def test_all_qc_checks_pass(self, pilot_case, hta_user):
        report = import_and_validate(pilot_case, str(LECTURER_WORKBOOK), hta_user)
        failed = [c for c in report["checks"] if not c["pass"]]
        assert failed == [], failed
        assert report["issues"] == []
        assert report["status"] == "PASS"

    def test_covers_deterministic_and_bia(self, pilot_case, hta_user):
        report = import_and_validate(pilot_case, str(LECTURER_WORKBOOK), hta_user)
        metrics = {c["metric"] for c in report["checks"]}
        assert {"total_cost_intervention", "icer", "inb"} <= metrics
        assert {"bia_net_low", "bia_net_medium", "bia_net_high"} <= metrics


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
