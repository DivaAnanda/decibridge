"""Manifest engine tests — pure functions, no Django."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from apps.archive import engine


class TestCanonicalDumps:
    def test_sorts_keys(self):
        a = {"b": 1, "a": 2}
        b = {"a": 2, "b": 1}
        assert engine.canonical_dumps(a) == engine.canonical_dumps(b)

    def test_decimal_serializable(self):
        out = engine.canonical_dumps({"price": Decimal("10.50")})
        assert "10.50" in out

    def test_datetime_serializable(self):
        ts = datetime(2026, 6, 8, 14, 30, tzinfo=timezone.utc)
        out = engine.canonical_dumps({"ts": ts})
        assert "2026-06-08T14:30:00" in out


class TestSha256:
    def test_stable_across_equivalent_dicts(self):
        a = {"x": 1, "y": [1, 2, 3]}
        b = {"y": [1, 2, 3], "x": 1}
        assert engine.sha256_of(a) == engine.sha256_of(b)

    def test_changes_when_data_changes(self):
        a = {"x": 1}
        b = {"x": 2}
        assert engine.sha256_of(a) != engine.sha256_of(b)


class TestRowSummary:
    def test_includes_hash_and_fields(self):
        row = {"id": 1, "value": "test"}
        summary = engine.row_summary(row)
        assert summary["id"] == 1
        assert summary["sha256"] == engine.sha256_of(row)
        assert summary["fields"] == row


class TestBuildManifest:
    def _minimal_args(self):
        return dict(
            case_meta={"case_id": "TEST_001", "case_title": "Test"},
            archived_at=datetime(2026, 6, 8, 14, 30, tzinfo=timezone.utc),
            archived_by={"email": "ketua@test.local", "name": "Dr. Test"},
            retention_until=datetime(2033, 6, 8, 14, 30, tzinfo=timezone.utc),
            cea_results=[],
            bia_results=[],
            etd_appraisals=[],
            references=[],
            recommendations=[],
            approvals=[],
            case_versions=[],
            policy_briefs=[],
            audit_log=[],
        )

    def test_empty_manifest_has_schema_version(self):
        m = engine.build_manifest(**self._minimal_args())
        assert m["schema_version"] == engine.MANIFEST_SCHEMA_VERSION
        assert m["case_id"] == "TEST_001"

    def test_manifest_includes_all_artifact_categories(self):
        m = engine.build_manifest(**self._minimal_args())
        for key in (
            "cea_results",
            "bia_results",
            "etd_appraisals",
            "references",
            "recommendations",
            "approvals",
            "case_versions",
            "policy_briefs",
        ):
            assert key in m["artifacts"]

    def test_artifacts_get_per_row_hashes(self):
        args = self._minimal_args()
        args["recommendations"] = [
            {"id": 1, "traffic_light": "green", "composite_score": "90.00"},
            {"id": 2, "traffic_light": "yellow", "composite_score": "65.00"},
        ]
        m = engine.build_manifest(**args)
        recs = m["artifacts"]["recommendations"]
        assert len(recs) == 2
        assert recs[0]["sha256"] != recs[1]["sha256"]
        # Hash of identical input → identical output
        recomputed = engine.sha256_of(args["recommendations"][0])
        assert recs[0]["sha256"] == recomputed


class TestManifestSha256:
    def test_hash_changes_when_any_row_changes(self):
        base_args = dict(
            case_meta={"case_id": "TEST_001"},
            archived_at=datetime(2026, 6, 8, tzinfo=timezone.utc),
            archived_by={"email": "x@test.local", "name": "X"},
            retention_until=datetime(2033, 6, 8, tzinfo=timezone.utc),
            cea_results=[],
            bia_results=[],
            etd_appraisals=[],
            references=[],
            recommendations=[{"id": 1, "traffic_light": "green"}],
            approvals=[],
            case_versions=[],
            policy_briefs=[],
            audit_log=[],
        )
        m1 = engine.build_manifest(**base_args)
        sha1 = engine.manifest_sha256(m1)

        tampered = {**base_args, "recommendations": [{"id": 1, "traffic_light": "red"}]}
        m2 = engine.build_manifest(**tampered)
        sha2 = engine.manifest_sha256(m2)

        assert sha1 != sha2
