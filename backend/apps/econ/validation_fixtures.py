"""Authoritative parameter set from the lecturer's validation workbook.

Source: `../Brief/DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx`
(sheet `01_INPUTS`), supplied after the first acceptance test. These REPLACE the
reverse-engineered placeholders used before the workbook arrived — the totals
were already correct, but the decomposition is now the real one.

Verified against sheet `02_DETERMINISTIC`:
    ARNI cost = 15,399,360 + 0.45   x 6,889,093 = 18,499,451.85
    ACEI cost =    324,000 + 0.7077 x 6,889,093 =  5,199,411.1161
    ARNI QALY = 0.7 - 0.45   x 0.1 = 0.655
    ACEI QALY = 0.7 - 0.7077 x 0.1 = 0.62923
    ICER = 516,105,577.5669 · INB @ WTP 85,000,000 = -11,109,590.7339

Per the lecturer these remain illustrative/proxy where marked and MUST stay
editable — nothing here is hardcoded into the engines.
"""

from __future__ import annotations

from decimal import Decimal

from .models import Alternative, DataStatus, ParamKey, ParamType

VALIDATION_CASE_ID = "HF_ARNI_ACEI_001"

# Sheet 01_INPUTS: horizon 1 year, both discount rates 3% (year 1 undiscounted),
# WTP 85M IDR/QALY, annual pharmacy budget baseline for % impact.
MODEL_SCALARS = dict(
    horizon_years=1,
    cost_discount_rate=Decimal("0.03"),
    outcome_discount_rate=Decimal("0.03"),
    wtp_threshold=Decimal("85000000.0000"),
    annual_budget_baseline=Decimal("50000000000.0000"),
)

# PSA run configuration (sheet 01_INPUTS / 04_PSA_INPUTS).
PSA_SIMULATIONS = 1000
PSA_SEED = 20260724

# Uptake scenarios for the budget-impact table (sheet 03_BIA).
UPTAKE_SCENARIOS = [
    ("low", Decimal("0.1000000000")),
    ("medium", Decimal("0.3000000000")),
    ("high", Decimal("0.5000000000")),
]

_OBS = DataStatus.OBSERVED
_PROXY = DataStatus.PROXY
_ASSUME = DataStatus.ASSUMPTION

VALIDATION_PARAMETERS: list[dict] = [
    # ── Shared clinical / cost parameters ────────────────────────────────
    dict(key=ParamKey.EVENT_COST, alternative=Alternative.SHARED,
         value=Decimal("6889093.0000"), param_type=ParamType.COST,
         unit="IDR/admission", data_status=_PROXY,
         source_reference="Casepack: Biaya Tabanan.xlsx — median proxy, bukan biaya final RS Unud",
         source_year=2023,
         distribution="gamma", dist_param1=Decimal("25"), dist_param2=Decimal("275563.72")),
    dict(key=ParamKey.BASELINE_UTILITY, alternative=Alternative.SHARED,
         value=Decimal("0.7000000000"), param_type=ParamType.UTILITY,
         unit="utility weight", data_status=_ASSUME,
         source_reference="Illustrative — stable HFrEF utility (belum bersumber dari file)",
         distribution="beta", dist_param1=Decimal("162.63333333"), dist_param2=Decimal("69.7")),
    dict(key=ParamKey.EVENT_DISUTILITY, alternative=Alternative.SHARED,
         value=Decimal("0.1000000000"), param_type=ParamType.DISUTILITY,
         unit="QALY/admission", data_status=_ASSUME,
         source_reference="Illustrative — QALY loss per HF admission",
         distribution="beta", dist_param1=Decimal("22.4"), dist_param2=Decimal("201.6")),
    # ── Intervention: ARNI (sacubitril/valsartan) ────────────────────────
    dict(key=ParamKey.DRUG_COST, alternative=Alternative.INTERVENTION,
         value=Decimal("15399360.0000"), param_type=ParamType.COST,
         unit="IDR/patient-year", data_status=_PROXY,
         source_reference="Template 01_Harga_Obat: Rp21.388/tablet x 60/bulan x 12",
         distribution="gamma", dist_param1=Decimal("100"), dist_param2=Decimal("153993.6")),
    dict(key=ParamKey.EVENT_PROBABILITY, alternative=Alternative.INTERVENTION,
         value=Decimal("0.4500000000"), param_type=ParamType.PROBABILITY,
         unit="annual proportion", data_status=_OBS,
         source_reference="Observed RWE — Casepack 18/40, rehospitalisasi 12 bulan",
         distribution="beta", dist_param1=Decimal("19"), dist_param2=Decimal("23")),
    dict(key=ParamKey.OTHER_COST, alternative=Alternative.INTERVENTION,
         value=Decimal("0.0000"), param_type=ParamType.COST,
         unit="IDR/patient-year", data_status=_ASSUME,
         source_reference="Biaya monitoring ARNI — dikecualikan secara default"),
    # ── Comparator: ACEI (enalapril) ─────────────────────────────────────
    dict(key=ParamKey.DRUG_COST, alternative=Alternative.COMPARATOR,
         value=Decimal("324000.0000"), param_type=ParamType.COST,
         unit="IDR/patient-year", data_status=_PROXY,
         source_reference="Template 01_Harga_Obat: Rp450/tablet x 60/bulan x 12",
         distribution="gamma", dist_param1=Decimal("100"), dist_param2=Decimal("3240")),
    dict(key=ParamKey.EVENT_PROBABILITY, alternative=Alternative.COMPARATOR,
         value=Decimal("0.7077000000"), param_type=ParamType.PROBABILITY,
         unit="annual proportion", data_status=_OBS,
         source_reference="Observed RWE — Casepack 46/65, rehospitalisasi 12 bulan",
         distribution="beta", dist_param1=Decimal("47.0005"), dist_param2=Decimal("19.9995")),
    dict(key=ParamKey.OTHER_COST, alternative=Alternative.COMPARATOR,
         value=Decimal("0.0000"), param_type=ParamType.COST,
         unit="IDR/patient-year", data_status=_ASSUME,
         source_reference="Biaya monitoring ACEI — dikecualikan secara default"),
    # ── Budget-impact scenario parameters (sheet 03_BIA) ─────────────────
    # NOTE: the lecturer's BIA uses patients = eligible x uptake ONLY.
    # market_share is intentionally absent (defaults to 1.0) to avoid the
    # double counting he flagged in the first revision.
    dict(key=ParamKey.ELIGIBLE_POPULATION, alternative=Alternative.SHARED,
         value=Decimal("100"), param_type=ParamType.COUNT,
         unit="patients/year", data_status=_ASSUME,
         source_reference="Populasi uji ilustratif — ganti dengan denominator RS Unud tervalidasi"),
    dict(key=ParamKey.UPTAKE, alternative=Alternative.SHARED,
         value=Decimal("0.3000000000"), param_type=ParamType.RATE,
         unit="proportion eligible", data_status=_ASSUME,
         source_reference="Skenario medium (30%)"),
    dict(key=ParamKey.UPTAKE_LOW, alternative=Alternative.SHARED,
         value=Decimal("0.1000000000"), param_type=ParamType.RATE,
         unit="proportion eligible", data_status=_ASSUME,
         source_reference="Skenario uptake rendah (10%)"),
    dict(key=ParamKey.UPTAKE_MEDIUM, alternative=Alternative.SHARED,
         value=Decimal("0.3000000000"), param_type=ParamType.RATE,
         unit="proportion eligible", data_status=_ASSUME,
         source_reference="Skenario uptake menengah (30%)"),
    dict(key=ParamKey.UPTAKE_HIGH, alternative=Alternative.SHARED,
         value=Decimal("0.5000000000"), param_type=ParamType.RATE,
         unit="proportion eligible", data_status=_ASSUME,
         source_reference="Skenario uptake tinggi (50%)"),
    # ── Secondary clinical validation (sheet 02_DETERMINISTIC) ───────────
    dict(key=ParamKey.MEDIAN_LOS, alternative=Alternative.INTERVENTION,
         value=Decimal("4"), param_type=ParamType.COUNT,
         unit="days/admission", data_status=_OBS,
         source_reference="Observed RWE — Casepack"),
    dict(key=ParamKey.MEDIAN_LOS, alternative=Alternative.COMPARATOR,
         value=Decimal("5"), param_type=ParamType.COUNT,
         unit="days/admission", data_status=_OBS,
         source_reference="Observed RWE — Casepack"),
]

# Expected results from sheet 09_DATA_MAP_QC (QC01-QC12): metric, expected, tolerance.
QC_EXPECTATIONS = [
    ("total_cost_intervention", Decimal("18499451.85"), Decimal("1")),
    ("total_cost_comparator", Decimal("5199411.1161"), Decimal("1")),
    ("total_qaly_intervention", Decimal("0.655"), Decimal("0.000001")),
    ("total_qaly_comparator", Decimal("0.62923"), Decimal("0.000001")),
    ("incremental_cost", Decimal("13300040.7339"), Decimal("1")),
    ("incremental_qaly", Decimal("0.02577"), Decimal("0.000001")),
    ("icer", Decimal("516105577.5669392"), Decimal("10")),
    ("inb", Decimal("-11109590.7339"), Decimal("10")),
    ("bia_net_low", Decimal("133000407.339"), Decimal("1")),
    ("bia_net_medium", Decimal("399001222.017"), Decimal("1")),
    ("bia_net_high", Decimal("665002036.695"), Decimal("1")),
]
