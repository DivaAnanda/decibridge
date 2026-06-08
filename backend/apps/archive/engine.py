"""Manifest builder — pure function, no Django imports at module level.

Produces a JSON-serializable manifest dict from queryset-like inputs. The
service layer (service.py) is responsible for fetching the rows from the
ORM; the engine only knows about dicts. Trivially testable.

Per-row SHA-256: hash of a canonical JSON dump of the row's fields. Any
tamper to the underlying row (which our append-only invariants already
forbid) would change the hash and break the manifest seal.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Iterable


MANIFEST_SCHEMA_VERSION = "1.0"


def _json_default(value: Any) -> Any:
    """JSON encoder for Decimal and datetime."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def canonical_dumps(obj: Any) -> str:
    """Stable, deterministic JSON serialization for hashing."""
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    )


def sha256_of(obj: Any) -> str:
    """SHA-256 hex digest of an object's canonical JSON form."""
    return hashlib.sha256(canonical_dumps(obj).encode("utf-8")).hexdigest()


def row_summary(row: dict) -> dict:
    """A summary suitable for embedding in the manifest: id + hash + key fields."""
    return {
        "id": row.get("id"),
        "sha256": sha256_of(row),
        "fields": row,
    }


def build_manifest(
    *,
    case_meta: dict,
    archived_at: datetime,
    archived_by: dict,
    retention_until: datetime,
    cea_results: Iterable[dict],
    bia_results: Iterable[dict],
    etd_appraisals: Iterable[dict],
    references: Iterable[dict],
    recommendations: Iterable[dict],
    approvals: Iterable[dict],
    case_versions: Iterable[dict],
    policy_briefs: Iterable[dict],
    audit_log: Iterable[dict],
) -> dict:
    """Assemble the manifest dict.

    Each artifact list is wrapped with per-row hashes so any single-row
    mutation in the source DB would break the seal.
    """
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "case_id": case_meta["case_id"],
        "archived_at": archived_at,
        "archived_by": archived_by,
        "retention_until": retention_until,
        "case": case_meta,
        "artifacts": {
            "cea_results": [row_summary(r) for r in cea_results],
            "bia_results": [row_summary(r) for r in bia_results],
            "etd_appraisals": [row_summary(r) for r in etd_appraisals],
            "references": [row_summary(r) for r in references],
            "recommendations": [row_summary(r) for r in recommendations],
            "approvals": [row_summary(r) for r in approvals],
            "case_versions": [row_summary(r) for r in case_versions],
            "policy_briefs": [row_summary(r) for r in policy_briefs],
        },
        "audit_log": [row_summary(r) for r in audit_log],
        "generated_at": datetime.now(tz=timezone.utc),
    }


def manifest_bytes(manifest: dict) -> bytes:
    """Serialize the manifest to bytes for writing to disk + hashing."""
    return canonical_dumps(manifest).encode("utf-8")


def manifest_sha256(manifest: dict) -> str:
    return hashlib.sha256(manifest_bytes(manifest)).hexdigest()


__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "build_manifest",
    "canonical_dumps",
    "manifest_bytes",
    "manifest_sha256",
    "row_summary",
    "sha256_of",
]
