# DeciBridge — Rencana Revisi Pasca-Demo (Lecturer Review)

Source: `../Brief/Hasil Checking DeciBridge.docx` (lecturer feedback, 2026-08-22).
Turns the "CEA Quick" MVP into a full HTA-grade cost-utility engine (deterministic +
probabilistic) with discounting, NMB/INB, PSA/CEAC/CE-plane, cost-offset BIA, safe
missing-data handling, and an Excel validation harness.

## Working constraint — no workbook

`DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx` was **not** provided. We proceed
anyway:

- Every engine is built **correct-by-formula** (formulas are fully specified in the doc)
  and unit-tested against hand-computed values.
- The lecturer stated all parameters are illustrative and **must be editable / not
  hardcoded** — so we ship a documented **default illustrative parameter set** for
  `HF_ARNI_ACEI_001` chosen to reproduce the acceptance totals.
- For the Excel validator we **generate our own** validation workbook fixture matching the
  documented sheet list, so the importer is testable end-to-end.
- When/if the lecturer's real workbook arrives: drop it in, run the validator, reconcile.
  No rework — just data.

## Acceptance reference (case `HF_ARNI_ACEI_001`)

| Metric | ARNI (intervensi) | ACEI (komparator) |
|---|---|---|
| Total cost | 18.499.451,85 | 5.199.411,1161 |
| Total QALY | 0,655 | 0,62923 |

Incremental cost **13.300.040,7339** · Incremental QALY **0,02577** ·
ICER **516.105.577,5669** · WTP **85.000.000** · INB **−11.109.590,7339** →
**NOT cost-effective**.

Tolerances: cost & INB ±Rp1 · QALY ±0,000001 · ICER ±Rp100 · PSA/CEAC prob ±0,005 (same seed).

Cross-cutting rules (apply to every phase):
- Param change auto-recomputes all dependent outputs.
- No rounding before the final result — round only at the presentation layer.
- Fixed-seed PSA is reproducible.
- Formula + algorithm version recorded in the audit trail.
- All parameters editable; nothing hardcoded.

---

## Phase sequencing (dependency-ordered)

```
R0 (independent quick win) ─┐
R1 precision + param model ─┼─► R2 deterministic engine ─► R3 missing-data gating
                            │           │
                            │           └─► R4 BIA cost-offset
                            │                    │
                            └────────────────────┴─► R5 PSA / CEAC / CE-plane ─► R6 Excel validator
```

R1 is the backbone — R2–R6 all sit on the parameter model and precision changes.

---

### R0 — Quick fix: enable "Hitung" button right after "Simpan Input"  *(Req #11)*  — ✅ DONE
**Independent — ship first as a warm-up.**
*Fixed by seeding the query cache from the PUT response (`setQueryData`) in `CEATab`/`BIATab`.*
- **Frontend only.** After the save mutation succeeds, invalidate/refetch the input query
  (TanStack Query) so `hasSavedInput` flips without a page reload; enable the compute button
  from mutation state.
- Add explicit loading state on Save + Compute, and surface API errors inline.
- **Files:** `frontend/src/cea/*`, `frontend/src/bia/*` (the save/compute hooks + panels).
- **Acceptance:** Save → button active immediately, no refresh; error shows a clear alert.

---

### R1 — Numeric precision + economic parameter model  *(Req #1, #2)* — FOUNDATION — ✅ DONE
**Backend-heavy. Everything downstream depends on this.**
*Shipped new additive `apps/econ`: `EconomicModel` + `EconomicParameter` registry with
`DECIMAL(20,4)` cost / `DECIMAL(18,10)` rate precision, per-param provenance metadata,
auto-versioning, `value_of()` resolver. 11 tests, 266 total passing, 86.6% coverage.*

Precision:
- Migrate decimal fields: **cost `DECIMAL(20,4)`**, **probability/utility/QALY `DECIMAL(18,10)`**.
- Remove all mid-calculation `.quantize(...)` from engines — carry full `Decimal` precision;
  round **only** in serializers/UI.

Parameter model (new `apps/econ` or extend `apps/cea`):
- New model `EconomicModel` (per case) + `EconomicParameter` rows. Parameters needed:
  horizon (years), cost discount rate, outcome discount rate, WTP threshold, drug cost per
  patient/year, event/rehospitalisation probability, cost per event, baseline utility, event
  disutility, other costs per alternative, eligible population, uptake per year, annual market share.
- Per-parameter metadata: `name, value, unit, data_source, source_year,
  data_status {observed|proxy|assumption}, notes, version, updated_at`.
- Held **per alternative** (intervention + comparator) where applicable.
- Append-only history via existing `register_auditable()` + `HistoricalRecords()`.
- **Acceptance:** can store a full ARNI-vs-ACEI parameter set with metadata; values round-trip
  at full precision; editing a param creates an audited new version.

---

### R2 — Deterministic engine: multi-year cost + QALY + discounting + NMB/INB  *(Req #3, #4, #5)*  — ✅ DONE
Backend: `engine_deterministic.py` (pure), `EconDeterministicResult` (append-only),
`service.py` (resolve→compute→persist + `IncompleteModelError`), `validation_fixtures.py`,
`seed_econ_validation_case` command. DRF `serializers/views/urls/permissions`.
Frontend: CEA tab replaced by `EconTab` (model scalars + editable parameter registry +
`EconResultCard` with per-year discounting table). Reproduces the acceptance table exactly —
verified in-browser (ICER 516,105,577.57 / INB −11,109,590.73). 18 new R2 tests (29 econ total),
all passing. Also fixed dev-only base-path bug: `vite.config.ts` now gates `base` on build mode
(prod `/static/`, dev `/`) so local deep-link refreshes stop 404-ing.
**R3 follow-up:** the traffic-light recommendation still reads the legacy `CEAResult.ce_score`;
rewire it to consume the econ deterministic result (or gate on it) during R3.

New pure engine `apps/econ/engine_deterministic.py` (no Django imports).

Per alternative, per year `t`:
```
annual_cost_t   = drug_cost + (event_prob × event_cost) + other_cost
disc_cost_t     = annual_cost_t / (1 + cost_discount_rate) ** (t-1)
total_cost      = Σ disc_cost_t
annual_qaly_t   = baseline_utility − (event_prob × event_disutility)
disc_qaly_t     = annual_qaly_t / (1 + outcome_discount_rate) ** (t-1)
total_qaly      = Σ disc_qaly_t
```
Then:
```
incremental_cost = total_cost_int − total_cost_comp
incremental_qaly = total_qaly_int − total_qaly_comp
ICER             = incremental_cost / incremental_qaly   (N/A if incremental_qaly == 0)
NMB_x            = WTP × total_qaly_x − total_cost_x
INB              = NMB_int − NMB_comp
```
Decision rules: INB>0 cost-effective; INB≤0 not; lower cost & higher QALY = dominant;
higher cost & lower QALY = dominated; incremental_qaly=0 → ICER "N/A" (no div error).

- UI: total cost/QALY per alternative, incremental, ICER, NMB, INB, decision badge, and a
  **per-year table before vs after discounting** with cost breakdown (drug/event/other).
- Derive the documented **illustrative default param set** that reproduces the acceptance totals.
- Audit: record formula id + `ALGORITHM_VERSION`.
- **Acceptance:** engine reproduces the reference table within tolerance given the default set;
  unit tests with hand-computed multi-year+discount cases.

---

### R3 — Safe missing-data handling + recommendation gating  *(Req #10)*
**Reverses current behaviour (missing→0, empty CBA→100).**
- Recommendation only computes when **all mandatory components exist**; otherwise status
  **"Belum dapat dihitung"** + a list of missing inputs.
- Empty CBA → `null` / "not assessed", **not 100**. Missing sub-score → not silently 0/100.
- `recommendation/engine.py`: introduce an explicit `incomplete` result type; callers render
  the missing-inputs checklist instead of a RED light.
- **Acceptance:** a case with no EtD/BIA shows "Belum dapat dihitung" (not RED); empty CBA is
  "not assessed"; filling all mandatory inputs unlocks the traffic light.

---

### R4 — BIA rework with event cost-offset  *(Req #9)*
New `bia/engine.py` logic:
```
incremental_drug_budget = patients_int × (drug_cost_int − drug_cost_comp)
event_cost_offset       = patients_int × (event_prob_comp − event_prob_int) × event_cost
net_budget_impact       = incremental_drug_budget − event_cost_offset + incremental_other
```
- Per-year table: eligible population, uptake, patients_int, patients_comp, incremental drug
  cost, event cost offset, net budget impact, cumulative, % of baseline annual budget.
- **Clarify uptake vs market share** to prevent double counting. Proposed definition (surfaced
  in the UI help text): `patients_on_intervention = eligible × uptake × market_share`, where
  **uptake** = proportion of eligible actually treated, **market share** = proportion of
  treated who receive the intervention. (Confirm with lecturer if possible.)
- **Acceptance:** cost-offset changes net impact vs the drug-only figure; per-year table matches
  hand calc; definitions visible in UI.

---

### R5 — PSA + CEAC + CE plane  *(Req #6, #7, #8)*
New `apps/econ/engine_psa.py` (numpy/scipy) — add deps.
- Monte Carlo: **≥1000 sims**, **settable seed** (reproducible), distributions: **Beta** for
  probabilities/utilities, **Gamma or Log-normal** for costs; inputs as mean+SE / alpha-beta /
  shape-scale; validate prob & utility stay in [0,1].
- Each iteration stores: total cost & QALY per alternative, incremental cost, incremental QALY,
  INB at chosen WTP, cost-effective status.
- **CEAC:** across a WTP range (min/max/step) → P(cost-effective)=share of iterations with INB>0;
  report value at base-case WTP.
- **CE plane:** scatter incremental QALY (x) vs incremental cost (y), 4 quadrants, plus the
  deterministic base-case point.
- Run via **Celery** (already in stack) since 1000+ sims; store results append-only.
- Frontend charts: CE-plane scatter + CEAC curve (Recharts/@mantine/charts).
- **Acceptance:** same seed → identical PSA output (±0,005 on probabilities); CE-plane and CEAC
  render; distributions respect [0,1] bounds.

---

### R6 — Excel validation import + validation report  *(Req #12)*  — partially self-served
Revives deferred Sprint 3, now concrete.
- **First: generate our own** `DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx` encoding
  `HF_ARNI_ACEI_001` with sheets: `case_meta`, `clinical_outcomes`, `cost_inputs`,
  `economic_model_params`, `expected_deterministic_results`, `expected_psa_summary`.
- Import endpoint / "Import Validation Case" menu: map sheets → models.
- Validation checks: case_id consistent, mandatory fields present, correct types, consistent
  units, prob/utility in [0,1], non-negative costs, no duplicate params, data source present,
  list empty params.
- **Validation report:** PASS/FAIL per metric with expected, actual, diff, tolerance.
- **Acceptance:** importing our fixture yields PASS within tolerance; a corrupted fixture yields
  FAIL with the offending rows. (Swap in lecturer's real file later — no code change.)

---

## Open decisions
1. **uptake vs market share** definition (R4) — proposed above; confirm with lecturer if reachable.
2. **Horizon & discount rates** (R1/R2) — unknown from the doc; ship editable defaults
   (e.g. horizon per validation model, cost/outcome discount 0–3%), reconcile when real data lands.
3. **PSA sync vs async** — plan is Celery async; acceptable for demo latency.

## Suggested order of execution
R0 (now) → R1 → R2 → R3 → R4 → R5 → R6. R1+R2 are the bulk of the value and unblock everything.
