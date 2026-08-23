"""Derive the 0-100 cost-effectiveness sub-score for the traffic-light synthesis.

The recommendation engine expects a 0-100 CE sub-score. Post-R2 the source of
truth is the deterministic econ result (INB / ICER vs WTP), not the legacy
CEA-Quick banding. This pure helper maps a persisted `EconDeterministicResult`
onto the same 0-100 scale the synthesis weights expect.

Bands mirror the original CEA logic so the composite calibration is preserved:
    dominant / cost-saving        → 100
    dominated                     → 0
    ICER <= 0.8 * WTP             → 100
    0.8*WTP < ICER <= WTP         → 80
    WTP < ICER <= 1.5 * WTP       → 50
    ICER > 1.5 * WTP              → 0
    ICER undefined (Δqaly = 0)    → 50 (ambiguous; decided by other domains)
"""

from __future__ import annotations

from decimal import Decimal


def ce_score_from_result(result) -> Decimal:
    """Map an EconDeterministicResult onto a 0-100 cost-effectiveness sub-score."""
    if result.is_dominant:
        return Decimal("100")
    if result.is_dominated:
        return Decimal("0")

    icer = result.icer
    if icer is None:
        return Decimal("50")

    wtp = result.wtp_threshold_used
    if icer <= Decimal("0.8") * wtp:
        return Decimal("100")
    if icer <= wtp:
        return Decimal("80")
    if icer <= Decimal("1.5") * wtp:
        return Decimal("50")
    return Decimal("0")
