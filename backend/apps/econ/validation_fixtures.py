"""The verified illustrative parameter set for the lecturer's validation case.

These reproduce the acceptance table in `../Brief/Hasil Checking DeciBridge.docx`
for HF_ARNI_ACEI_001 exactly (total cost/QALY, incremental, ICER, INB).

Per the lecturer, these are illustrative assumptions and MUST stay editable —
they live in the DB as ordinary `EconomicParameter` rows, not hardcoded in the
engine. This module is the single source shared by the seed command and tests.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Alternative, DataStatus, ParamKey, ParamType

VALIDATION_CASE_ID = "HF_ARNI_ACEI_001"

MODEL_SCALARS = dict(
    horizon_years=1,
    cost_discount_rate=Decimal("0"),
    outcome_discount_rate=Decimal("0"),
    wtp_threshold=Decimal("85000000.0000"),
    annual_budget_baseline=Decimal("50000000000.0000"),
)

# Each entry becomes one EconomicParameter row (year-agnostic).
VALIDATION_PARAMETERS: list[dict] = [
    # ── Shared across both alternatives ──────────────────────────────────
    dict(key=ParamKey.EVENT_COST, alternative=Alternative.SHARED,
         value=Decimal("20000000.0000"), param_type=ParamType.COST,
         unit="IDR/kejadian", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (biaya rawat inap per rehospitalisasi)"),
    dict(key=ParamKey.BASELINE_UTILITY, alternative=Alternative.SHARED,
         value=Decimal("0.7500000000"), param_type=ParamType.UTILITY,
         unit="utility", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (utility dasar HFrEF)"),
    dict(key=ParamKey.EVENT_DISUTILITY, alternative=Alternative.SHARED,
         value=Decimal("0.5000000000"), param_type=ParamType.DISUTILITY,
         unit="utility", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (disutility per kejadian)"),
    # ── Intervention (ARNI / sacubitril-valsartan) ───────────────────────
    dict(key=ParamKey.DRUG_COST, alternative=Alternative.INTERVENTION,
         value=Decimal("14699451.8500"), param_type=ParamType.COST,
         unit="IDR/pasien/tahun", data_status=DataStatus.ASSUMPTION,
         source_reference="Diturunkan dari model validasi"),
    dict(key=ParamKey.EVENT_PROBABILITY, alternative=Alternative.INTERVENTION,
         value=Decimal("0.1900000000"), param_type=ParamType.PROBABILITY,
         unit="proporsi/tahun", data_status=DataStatus.ASSUMPTION,
         source_reference="Diturunkan dari model validasi"),
    # ── Comparator (ACEI / enalapril) ────────────────────────────────────
    dict(key=ParamKey.DRUG_COST, alternative=Alternative.COMPARATOR,
         value=Decimal("368611.1161"), param_type=ParamType.COST,
         unit="IDR/pasien/tahun", data_status=DataStatus.ASSUMPTION,
         source_reference="Diturunkan dari model validasi"),
    dict(key=ParamKey.EVENT_PROBABILITY, alternative=Alternative.COMPARATOR,
         value=Decimal("0.2415400000"), param_type=ParamType.PROBABILITY,
         unit="proporsi/tahun", data_status=DataStatus.ASSUMPTION,
         source_reference="Diturunkan dari model validasi"),
    # ── BIA scenario parameters (shared) — illustrative ──────────────────
    dict(key=ParamKey.ELIGIBLE_POPULATION, alternative=Alternative.SHARED,
         value=Decimal("1000"), param_type=ParamType.COUNT,
         unit="pasien/tahun", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (populasi eligible HFrEF)"),
    dict(key=ParamKey.UPTAKE, alternative=Alternative.SHARED,
         value=Decimal("0.5000000000"), param_type=ParamType.RATE,
         unit="proporsi", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (proporsi eligible yang diobati)"),
    dict(key=ParamKey.MARKET_SHARE, alternative=Alternative.SHARED,
         value=Decimal("0.5000000000"), param_type=ParamType.RATE,
         unit="proporsi", data_status=DataStatus.ASSUMPTION,
         source_reference="Asumsi ilustratif (pangsa intervensi di antara yang diobati)"),
]
