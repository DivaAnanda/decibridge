"""What the walkthrough produced, the instructor key, and Indonesian number formatting."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SHOTS = HERE / "screenshots"
OUT_DOCX = HERE / "Buku_Panduan_DeciBridge_Kasus_Latihan.docx"
PRINTER = HERE.parents[1] / "frontend" / "e2e" / "print-pdf.mjs"
OUT_PDF = OUT_DOCX.with_suffix(".pdf")

RESULTS = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
INPUTS = RESULTS["inputs"]
INITIAL = RESULTS["initial"]
REVISED = RESULTS["revised"]
CASE_ID = RESULTS["case_id"]
BUILD = RESULTS["build"]

PACKAGE = "DeciBridge_Demo_Training_Package.xlsx"
FOOTER = f"DeciBridge - Buku Panduan Kasus Latihan {CASE_ID} - data sintetis"

BULAN = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
    "Agustus", "September", "Oktober", "November", "Desember",
]


# ── Indonesian number formatting ───────────────────────────────────────────


def _swap(text: str) -> str:
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def num(value, decimals: int = 0) -> str:
    return _swap(f"{Decimal(str(value)):,.{decimals}f}")


def rp(value, decimals: int = 0) -> str:
    return f"Rp{num(value, decimals)}"


def pct(value, decimals: int = 2) -> str:
    return f"{num(value, decimals)}%"


# ── The instructor key (package sheet 11, and sheet 10 for the revision) ────

KEY = {
    "total_cost_intervention": Decimal("16500000"),
    "total_cost_comparator": Decimal("4100000"),
    "incremental_cost": Decimal("12400000"),
    "total_qaly_intervention": Decimal("0.75"),
    "total_qaly_comparator": Decimal("0.695"),
    "incremental_qaly": Decimal("0.055"),
    "icer": Decimal("225454545.45"),
    "nmb_intervention": Decimal("208500000"),
    "nmb_comparator": Decimal("204400000"),
    "inb": Decimal("4100000"),
    "bia_net": [Decimal("496000000"), Decimal("954800000"), Decimal("1488000000")],
    "bia_patients": [Decimal("40"), Decimal("77"), Decimal("120")],
    "bia_pct": [Decimal("2.48"), Decimal("4.774"), Decimal("7.44")],
    "bia_cumulative": Decimal("2938800000"),
    "psa_prob": Decimal("0.5634"),
    "psa_mean_cost": Decimal("12407194.25"),
    "psa_mean_qaly": Decimal("0.0546"),
    "revised_incremental_cost": Decimal("11200000"),
    "revised_icer": Decimal("203636363.64"),
    "revised_inb": Decimal("5300000"),
}

MISMATCHES: list[str] = []


def exact(label: str, actual, expected: Decimal, tolerance: str = "0.01") -> str:
    """Status text for a figure that must reproduce the key."""
    if abs(Decimal(str(actual)) - expected) <= Decimal(tolerance):
        return "Sesuai"
    MISMATCHES.append(f"{label}: dashboard {actual}, kunci {expected}")
    return "TIDAK SESUAI"


def approximate(label: str, actual, expected: Decimal, relative: str) -> str:
    """Status text for a Monte-Carlo figure, which the key allows to differ."""
    gap = abs(Decimal(str(actual)) - expected) / expected
    if gap <= Decimal(relative):
        return "Dalam toleransi"
    MISMATCHES.append(f"{label}: dashboard {actual}, kunci {expected} (di luar toleransi)")
    return "DI LUAR TOLERANSI"
