"""Round 4 item 7: a changed document must be detectable after the fact."""

from __future__ import annotations

import pytest

from apps.archive.verification import (
    STATUS_MISSING,
    STATUS_MODIFIED,
    STATUS_OK,
    sha256_of,
    verify_case_documents,
)
from apps.policy_brief.service import absolute_path

pytestmark = pytest.mark.django_db


class TestDocumentVerification:
    def test_untouched_documents_verify_clean(self, archived_case_with_brief):
        case, _ = archived_case_with_brief

        report = verify_case_documents(case)

        assert report.checks
        assert report.is_intact is True
        assert all(c.status == STATUS_OK for c in report.checks)

    def test_a_tampered_docx_is_detected(self, archived_case_with_brief):
        """'pemeriksaan hash dapat mendeteksi perubahan pada salinan dokumen uji.'"""
        case, brief = archived_case_with_brief
        path = absolute_path(brief.docx_path)
        original = path.read_bytes()
        path.write_bytes(original + b"\n<!-- diubah setelah dikunci -->")

        report = verify_case_documents(case)

        assert report.is_intact is False
        failure = next(c for c in report.failures if "DOCX" in c.label)
        assert failure.status == STATUS_MODIFIED
        assert failure.actual_sha256 != failure.expected_sha256

    def test_a_deleted_document_is_detected(self, archived_case_with_brief):
        case, brief = archived_case_with_brief
        absolute_path(brief.docx_path).unlink()

        report = verify_case_documents(case)

        assert report.is_intact is False
        assert any(c.status == STATUS_MISSING for c in report.failures)

    def test_recorded_hash_matches_the_file_as_generated(self, archived_case_with_brief):
        _, brief = archived_case_with_brief

        assert sha256_of(absolute_path(brief.docx_path)) == brief.docx_sha256
