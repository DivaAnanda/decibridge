# DeciBridge — Project Context for Claude Code

Auto-loaded into every Claude Code session in this repo. Keep short, keep current.

## CURRENT STATE - read this first (2026-10-26)

**Rounds 1-4, the PSA distribution editor, the manual book and the fixes it exposed are shipped
and deployed (pushed 2026-10-13; see `git log` for the head). 520 backend tests passing (~14 min
full run).**

- **Live:** https://decibridge-production.up.railway.app (still on Railway; migration not started).
- **Production now holds other people's work.** Students and the lecturer create cases there
  (`HF_ARNI_ACEI_DWIKA`, `HF_ARNI_ACEI_TANIA`, `NN_DEMO_HF_001`, `TRN_HF_ARNI_001_1`,
  `HF_ARNI_ACEI_0510`, ...). Never reset, reseed or overwrite a case you did not create. Every
  seeder in the entrypoint is create-only for this reason.
- Reference cases: `DB_DEMO_HF_001` (synthetic training case, matches the instructor key),
  `UAT_*` (five gate fixtures), `HF_ARNI_ACEI_001` (old validation-workbook values, 11/11 QC),
  `HF_ARNI_ACEI_004` (locked, flagged `requires_remediation`, NEVER DELETE).

### ROUND 5 (WhatsApp from Pak Anom, 2026-10-26) - ALL FIVE ITEMS BUILT (uncommitted); next: regenerate the manual, review, commit when asked

**Item 5 as built (2026-10-26):** `apps/cases/permissions.VIEWER_ROLES` now means "may read case
content" and no longer holds ADMIN_IT; every analysis app imports it, so econ/CEA/BIA/EtD/
recommendation/approval reads are closed to Admin IT. `METADATA_ROLES` (+ADMIN_IT) and
`sees_metadata_only(user)` let Admin IT list/retrieve cases through `CaseMetadataListSerializer` /
`CaseMetadataSerializer` (ID, title, status, dates, integrity) and nothing else (no readiness,
PATCH, transition). Versioning and policy-brief reads/generation drop ADMIN_IT. Archive: the
record (seal, retention, counts) stays readable; the manifest download (a full case export) does
not (`ArchiveManifestPermission`). Four views that only checked login (EtD summary, weights
summary, recommendation list/latest) now use `CanReadCaseContent`. Full-IP tests for approvals
and version state moved to a superuser; Admin IT still sees full IPs in user admin. Frontend
follows the payload shape (`hasCaseContent`, `hasListContent`): `cases/CaseMetadataView.tsx`
replaces the tabs for Admin IT; the list hides Intervensi/Komparator. Tests:
`apps/cases/tests/test_admin_it_scope.py`. A user holding Admin IT plus a content role keeps
content.

**Item 1 as built (2026-10-26):** `completeness.py` adds requirements `psa` (latest PSA's
recorded inputs equal `psa_input_state(model)` now; unrecorded = must re-run;
`econ/psa_distributions.psa_result_is_stale` is the one implementation, the serializer uses it)
and `recommendation_current` (`recommendation/staleness.evaluate_staleness`). Both are in the
`approve` and `lock` stages, which cover the sign-off endpoint and both transitions. New stage
keys keep older decisions on their old rules: `brief` (policy_brief/views) and `integrity`
(`integrity.evaluate_integrity`, used by archive and the deploy-time `audit_case_integrity`).
`seed_uat_cases._psa` re-runs a UAT PSA only when the latest has no recorded inputs, so
UAT_LENGKAP stays signable after the deploy; a PSA made stale by an edit is left alone. Frontend:
checklist refetches on every visit and wraps long details; "Setujui dengan Sign-Off" is disabled
until ready; the PSA tab warns about pre-2026-10-13 runs. Tests: `test_psa_signoff_gate.py`,
`test_uat_seed_psa.py`; `econ/tests/factories.make_psa_result` builds PSA rows without Monte
Carlo. Rules documented in `docs/stage-requirements.md`.

**Item 3 as built (2026-10-26):** `recommendation.FinalDecision` (append-only; latest row is
current; FK to the recommendation it was decided against; `FinalDecisionType` = the five brief
decision types, labelled "Indonesian (English)"). `GET/POST /cases/{id}/final-decisions/`
(`recommendation/final_decision_views.py`): Anggota/Ketua KFT write, only while `is_editable`
and after a recommendation exists; reason required; audited with `metadata.case_id`. Readiness
requirement `final_decision` in `approve`/`lock` only ("konfirmasi ulang" when the
recommendation was recomputed). `Approval.final_decision` (nullable FK) binds the decision at
sign time. Included in the lock snapshot (`final_decision` block), Versi state, and the archive
manifest (`final_decisions`). UAT seeder adds a synthetic decision to UAT_LENGKAP and
UAT_TANPA_TANDA_TANGAN only when they have none. Frontend: `recommendation/FinalDecisionCard.tsx`
on the Rekomendasi tab (needs `caseIsEditable`), decision on the Sign-Off dossier and signature
history, Versi block. Factory: `recommendation/tests/factories.make_final_decision`. Migrations
`recommendation/0003`, `approval/0002`.

**Item 2 as built (2026-10-27):** the brief (`policy_brief/engine.py`, pure; filled by
`service.build_context`) now has: cover rows Populasi target (case.population, falling back to the
first PICO P), Setting, Perspektif; section 1 opens with the Keputusan Final KFT, then
"Rekomendasi Sistem" (colour/score); new section 2 Pertanyaan Keputusan dan Populasi Target (each
PICO question as a table); new section 5 PSA (iterations, seed, P(CE) at base WTP, mean and
base-case increments, CEAC at 0/0.5/1/1.5/2 x WTP, interpretation, a note when the PSA is stale or
predates recorded inputs). Sections renumbered 1-9; the manual's brief chapter
(`docs/panduan/manual/chapters_decision.py` ~line 294) lists the old numbering - update it when
regenerating. Fixed in passing: `_build_cba` formatted a null CBA score (UAT_LENGKAP's seeded
recommendation) and failed the whole brief. Tests: `policy_brief/tests/test_round5_content.py`,
new cases in `test_engine.py`.

**Item 4 as built (2026-10-27):** transition `revise` (locked -> draft; HTA Analyst or Ketua KFT;
reason required; archived cases excluded). `state_machine._record_revision` writes an append-only
CaseVersion `{next}-draft` (e.g. `1.1-draft`), status draft, trigger `revision_requested`, the
reason in `lock_reason`, `diff = {revises_version, revises_version_id}`. The locked v1.0 row and
its snapshot are never touched; the next lock is v1.1 (existing `_next_lock_version_number`).
`transition()` now runs its writes in `transaction.atomic()`. `completeness._revision_start`
makes the signature and the Keputusan Final KFT count only if recorded after the latest revision
began, so v1.0's signature cannot lock v1.1. `CaseVersionSerializer` exposes `trigger`; the case
page shows a "Revisi dari vX sedang berjalan" banner and the reason dialog explains the action.
Tests: `apps/cases/tests/test_revision.py`.

**Round 5 code review fixes (2026-10-27):** sign-off (`approval/views._approval_refusal`) runs
inside one `select_for_update` on the case, refuses a `recommendation_id` that is not the latest
(409) and an optional `final_decision_id` that is no longer current (409); recording a decision
takes the same row lock. The lock stage's `signoff` requirement is strict: an APPROVED approval,
since the latest revision, on the latest recommendation and the current decision (integrity and
archive keep the old count). Lock snapshots and their approval/brief pointers ignore rows from
before the revision. `transition()` re-reads the status under `select_for_update`. `revise` is
refused for integrity-flagged cases (HF_ARNI_ACEI_004 stays a locked fixture). Recommendation
compute is refused once approved. Admin IT case search covers ID and title only. `/readiness/`
on locked/archived cases uses the `integrity` stage. `FinalDecisionSerializer.is_current` is the
gate's notion of current. Version diff compares `final_decision`.

His words: "5 tambahan fungsi kecil pada menu yang sudah ada, tidak perlu buat menu baru ...
tidak perlu ubah struktur dashboard. Hanya menyempurnakan fungsi yang sudah ada."

1. Sign-Off: tambah cek PSA. Kalau PSA belum dikerjakan atau sudah tidak sesuai input terbaru ->
   belum boleh sign-off/lock.
2. Brief: tambahkan hasil PSA + pertanyaan keputusan + populasi target ke PDF/DOCX.
3. Rekomendasi: hasil warna/skor sistem tetap ada, tetapi tambahkan kolom Keputusan Final KFT +
   alasan yang diisi manusia.
4. Versi: kalau kasus sudah locked dan perlu revisi, buat versi/revisi baru, jangan mengubah versi
   yang lama.
5. Admin IT: batasi hanya urusan user/system/backup. Tidak boleh mengubah isi analisis atau
   menerbitkan keputusan.

These are the gaps the manual's Lampiran B listed; he is NOT asking for the 23092026 rebuild
(seven roles, new lifecycle). Do not add new menus or restructure the dashboard.

**Decisions confirmed by the user on 2026-10-26 ("defaults are fine")** - taken from the 23092026
Panduan, not invented:
- Build order: **5 -> 1 -> 3 -> 2 -> 4**, then regenerate the manual (chapters 7-10, Lampiran B rows
  50-59 change) with `bash docs/panduan/regenerate.sh`.
- Item 1 also blocks sign-off/lock when the RECOMMENDATION is stale (today only a warning:
  `StaleRecommendationAlert`). Justification: Panduan section 15 "version gate".
- Item 3: Keputusan Final KFT is filled by **Anggota KFT and Ketua KFT**; options are the original
  brief's five: Adopt / Adopt with criteria-based access / Defer pending additional evidence / Do
  not adopt / Reassess after price negotiation. Reason always required. Keep history (append-only
  rows; latest is current). Sign-Off requires it and the signature binds it; it should reference the
  recommendation row it was decided against (re-confirm if the recommendation is recomputed). Show
  it in the Sign-Off dossier, the lock snapshot (`cases/decision_snapshot.py`) and the brief.
- Item 4: **Analis HTA or Ketua KFT** may start a revision of a LOCKED case (not archived), reason
  required. Same case reopens as Draft; v1.0 snapshot stays frozen; next lock becomes v1.1
  (`state_machine._next_lock_version_number` already bumps minor; `CaseVersionTrigger.
  REVISION_REQUESTED` exists but is unused - write a version row with the reason). Earlier
  approvals/briefs/results stay (append-only). Versi diff v1.0 vs v1.1 already reads snapshots.
- Item 5: Admin IT keeps user admin (`/administrasi/pengguna`), health/build, archive
  verification. Remove brief generation (`policy_brief/permissions.py` GENERATOR_ROLES has
  ADMIN_IT; `frontend/src/policy_brief/PolicyBriefTab.tsx` `mayGenerate` includes 'admin_it' -
  I added that on 2026-10-13 to match the backend; item 5 reverses both). Admin IT sees **case
  list metadata only** (ID, title, status, dates, archive integrity), NOT the analysis tabs or
  their APIs - the Panduan's least-privilege rule says Admin IT must not see detailed
  clinical/economic content. Admin IT is in VIEWER_ROLES of cases, versioning, archive and
  policy_brief permissions today; econ/etd/recommendation/approval views inherit viewer access
  through cases. No backup feature exists in-app; do not build one (no new menus).

**Production cautions for round 5:**
- `audit_case_integrity` runs on every deploy and uses `evaluate_readiness(action="lock")`. Adding
  PSA to the lock requirements naively would flag every old locked case without PSA (including
  `HF_ARNI_ACEI_004`) as requires_remediation and hide it from the dashboard. Apply the PSA rule
  to transitions from now on only, not to the retroactive integrity audit.
- Cases now in_review/approved whose PSA ran before 2026-10-13 have no recorded inputs
  (`is_stale` is null); the new gate will require one PSA re-run. Tell the user.
- The manual is now `docs/panduan/Buku_Panduan_DeciBridge.{docx,pdf}` (user's choice,
  2026-10-27; `manual/data.py` OUT_DOCX). The old `_Kasus_Latihan` files are deleted in the
  working tree; commit the rename with the regenerated manual.

### Documents in `../Brief/`, oldest to newest - LATER ONES SUPERSEDE EARLIER ONES

| File | What it is |
|---|---|
| `11052026_Workflow and Steps kerja untuk IT.docx` | The ORIGINAL brief. Do not treat as current where a later document disagrees. |
| `Hasil Checking DeciBridge.docx` | Round 1 revision (econ engine). Done. |
| *(WhatsApp, pasted in chat)* | Round 3: five role-based acceptance reports. Done. |
| `revisi final.docx` | Round 4: eight items. Done except what the new spec below replaces. |
| `23092026_DeciBridge_Panduan_Detail_Role_Workflow_dan_Kasus_End_to_End.docx` | **NEW SPEC, not yet implemented.** See below. |
| `DeciBridge_Demo_Training_Package.xlsx` | Synthetic training case + instructor key. Loaded as `DB_DEMO_HF_001`. |

### What the lecturer asked for last (WhatsApp, early Oct) - manual book BUILT 2026-10-13

"Diva coba dimasukkan pakai data real ini. Kemudian screenshot, sekalian nanti jadi manual book /
panduan." He then sent the training package when told the docx held no data. So the deliverable is
a **manual book with screenshots** of the training case being worked through all nine menus.
The manual is `docs/panduan/Buku_Panduan_DeciBridge.{docx,pdf}` (42 pages, 47
screenshots). See "Manual book" below for how it is produced. The fixes found while writing it
were deployed with it. Whether the manual has been sent to him is for the user to say: ask.

"Data real" has NOT been loaded. The package is labelled synthetic. The only real numbers we have
are in the Panduan section 3 (ARNI Rp1.175.000/month, ramipril Rp90.000/month, HF hospitalisation
Rp6.500.000/event, HR hospitalisation ~0,80, HR mortality ~0,84) and it marks eligible population,
uptake and utility as not yet available, so a CUA on them must show INCOMPLETE/BLOCK. The engine
takes event probabilities, not hazard ratios. `HF_ARNI_ACEI_001` still holds the older values.

### The 23092026 Panduan - next big round, plan with the user before building

- **Seven roles** (we have five): adds Pembimbing/Peneliti (methodology review gate) and
  Klinisi/Clinical Expert; Farmasi becomes Data Owner; KFT splits Reviewer / Approver.
- **Status lifecycle:** Draft -> Methodology Review -> Revision Required -> Submitted for KFT ->
  Rejected / Approved-Frozen -> Archived-Verified.
- **EtD:** per-domain judgement in its own vocabulary + score -1/0/+1 + rationale + evidence used.
  "Tanpa automatic weighted decision." Values & Preferences must not auto-count as favourable.
- **Recommendation is a human decision:** decision type, target population, access criteria,
  rationale, implementation plan, monitoring plan. This retires the 40/30/20/10 composite, the
  GREEN/YELLOW/RED verdict and the (inert) domain-weight voting. Do not "fix" those; replace them.
- **Admin IT is metadata-only:** must not see detailed clinical/economic case content. Today it can.
- **Per-parameter fields:** adds source_detail, model_status (Included / Not used / Scenario only),
  validation status "Missing".
- **Version gate:** CEA, BIA, PSA, EtD, recommendation must share one parameter/model version.
- **Role dashboards:** four blocks (MY TASK / DATA I NEED / ACTION REQUIRED / OUTPUT-HANDOFF) and a
  header with versions, completeness %, blocking issues.
- "FINAL LOCKED FOR STUDENT RESEARCH" needs identical builds: pin dependencies (see gotcha 9).

### Open items, in suggested order

1. ~~PSA distribution editor~~ - built 2026-10-13 (see "PSA set-up" below).
2. ~~Manual book~~ - built 2026-10-13 (see "Manual book" below). Gaps it exposed, not yet built:
   a locked case cannot be reopened for a v1.1; the brief has no PSA summary or decision
   question; Rekomendasi has no decision-type / target-population / rationale inputs; the
   Sign-Off checklist does not include PSA; a stale recommendation is warned about but can
   still be signed. Most of these are what the 23092026 spec replaces - plan them there.
3. Plan and build the 23092026 spec as its own round.
4. Pin `djangorestframework` (pyproject says `>=3.15`; local venv 3.17, Docker image 3.18).
5. Leave Railway: Supabase Postgres + Render (paid) or Fly.io (free, volumes). Backup taken
   2026-09-11 at `../decibridge-railway.dump` is now stale; take a fresh `pg_dump` first.
6. `recommendation/engine.py` docstring claims the composite is "per the brief's section 5". It is
   not in any brief. Moot once item 3 replaces the engine.
7. Still unwritten from round 2 item 9: functional / edge-case / security test documentation, SUS,
   KFT meeting simulation.

### Manual book (`docs/panduan/`)

- One command rebuilds it from nothing: `bash docs/panduan/regenerate.sh`. It creates an empty
  database `decibridge_manual`, points the Docker backend at it
  (`docs/panduan/docker-compose.manual.yml`), runs `frontend/e2e/capture-manual.mjs` (Playwright
  works the training case through all nine menus in four roles and saves the screenshots and
  `results.json`), copies out the generated briefs, then runs `docs/panduan/build_manual.py`.
  Return to the normal stack afterwards with `docker compose up -d backend frontend`.
- Every number in the manual comes from `results.json` and is checked against the instructor key
  in `docs/panduan/manual/data.py`; the build stops if CEA or BIA disagree. Input tables are
  printed from the capture script's own constants. Do not retype figures into the chapters.
- The screenshots show the build badge of `MANUAL_BUILD_COMMIT` (HEAD when the script ran), so
  regenerate AFTER committing app changes, then commit the manual separately.
- **The verdict depends on the CBA "terpenuhi" tick.** With the four access criteria unticked
  the training case scores 69.44 KUNING (adopsi bersyarat), which matches the package's "Adopt
  with criteria-based access". With all four ticked it scores 79.44 HIJAU (tanpa syarat). The
  manual leaves them unticked and says why (package sheet 06 lists monitoring and workflow as
  still to be defined). This was the author's judgement; the user was told.
- EtD judgements are mapped from the package's per-domain vocabulary to the five-point scale in
  the capture script (`APPRAISALS`). Also a judgement, tabulated in chapter 6 of the manual.

### PSA set-up (package steps 37-39)

- Edited on the PSA tab (`frontend/src/econ/PSADistributionCard.tsx`), saved by its own endpoint
  `PUT /cases/{id}/econ/psa/distributions/` with rows `{id, distribution, dist_param1, dist_param2}`.
  It never writes a value (`save(update_fields=...)`), and the table endpoint cannot write
  distributions: they are read-only in `EconomicParameterSerializer`. Keep it that way; two
  screens echoing each other's cached fields is how the PSA set-up got wiped before.
- Only the rows the engine samples are editable: six keys, `year_index` null
  (`apps/econ/psa_distributions.py::SAMPLED_KEYS`).
- Users may type SE/SD as a number or as a share of the base value (`10%`); the two stored
  parameters are derived by method of moments in `frontend/src/econ/psaDistribution.ts`. Drug cost
  is stored per year while the package quotes per month, so `10%` is the safe way to enter it.
  The dot is the decimal point (`600.000` = 600), so the screen reads the parsed SE back.
- A workbook import stores `distribution` as typed (e.g. `Beta`), outside the choices. The
  validator reports it and the editor still renders the row so it can be re-picked.
- Beta only for probability/utility/disutility; Gamma and Log-normal only for costs. The same
  validator (`distribution_errors`) runs at save and at `run_psa`, which now returns 422 with the
  reason instead of silently holding a half-filled distribution fixed.
- Each PSA result records its inputs in `input_snapshot["inputs"]`; `is_stale` on the result
  compares them with the present state (`null` for results older than 2026-10-13).
- Known and left alone: a `shared` parameter (e.g. event cost) is drawn separately for each arm
  rather than once for both. Changing it would move every PSA number; ask the lecturer first.

### Operational quick-reference

| Need | Command |
|---|---|
| Run tests | `cd backend && ./.venv/Scripts/python.exe -m pytest -q --no-cov` (~12 min; one run at a time, they share the test DB) |
| Start DB | `docker compose up -d db redis` (Postgres on **5433**; Docker Desktop must be running) |
| Local app | `docker compose up -d backend frontend` -> http://localhost:5173 (API :8000) |
| Deploy | `git push origin main` - Railway builds in ~2 min |
| Check prod | Log in through the API as `hta@test.local` and read JSON; `railway ssh` needs `railway login` again (session expired) |

Entrypoint on every deploy: `migrate`, `create_test_users`, `backfill_decision_snapshots`,
`seed_uat_cases`, `seed_demo_training_case`, `audit_case_integrity`. All create-only or idempotent.

### Hard-won gotchas (each one cost real time - do not relearn these)

1. **The SPA catch-all returns HTTP 200 + `index.html` for unmatched API paths.** Always assert on
   the response body. Also: Django admin owns `/admin/*`, so no React route may start with `/admin`.
2. The version state endpoint takes the version *id*: `/cases/{case_id}/versions/{version_id}/state/`.
3. **Never add `seed_econ_validation_case` to the entrypoint** - it overwrites parameters.
4. **Never put business gates inside `state_machine.transition()`**; use `enforce_completeness=True`
   at API entry points, evaluated after the role check (403 before 422).
5. Lazy translation proxies are not JSON-serializable (`decision_snapshot._s()` coerces them).
6. Railway has no dashboard shell; billing lapses take the site down with an edge 404
   "Application not found". Check billing before debugging.
7. **A bulk parameter save must only write fields the client sent.** Defaulting missing fields reset
   every PSA distribution to `fixed` on each table save (fixed in `b6277ed`, tests guard it).
8. **Tests passing locally does not prove the container.** Check changed UI flows in the browser
   against the Docker stack before pushing.
9. **DRF version drift:** bulk-serializer errors are a list in 3.17 and a dict keyed by row in 3.18.
   Local venv and Docker image differ. `econ/views._row_errors` handles both.
10. Vite inside Docker on Windows does not hot-reload from the bind mount: `docker compose restart
    frontend` after frontend edits.
11. Nullable sub-scores (`cba_score`, `budget_score`) must never be formatted with `:.2f` unguarded.
12. Bash heredocs break on non-ASCII (em-dash) and turn `\n` inside Python strings into real
    newlines; use the Write/Edit tools for such content.
13. `compose` builds with `context: ./backend` and `./frontend`, so each needs its own
    `.dockerignore`; the repo-root one does not apply.
14. `npx vitest run` in `frontend/` shows two failures that predate round 4: Vitest collects the
    Playwright spec `e2e/smoke.spec.ts`, and `App.test.tsx` needs a `window.matchMedia` stub.
    `src/econ/psaDistribution.test.ts` is the frontend suite that is expected to pass.
15. Case tabs use `keepMounted={false}`: leaving a tab unmounts it, so unsaved edits in it are lost
    and its queries refetch on return only if older than the 30 s `staleTime` or invalidated.
16. **Never automate Microsoft Word on this machine** (`docx2pdf`, `win32com`). It attaches to
    the Word window the user already has open, opens files in it, and `docx2pdf` calls
    `Quit()` on it afterwards. PDFs for docs are printed with Playwright's Chromium
    (`frontend/e2e/print-pdf.mjs`); briefs are converted by LibreOffice inside Docker. The app's
    own `policy_brief.service._convert_docx_to_pdf` still uses docx2pdf when run outside Docker
    on Windows - generate briefs through the Docker stack.
17. A case built through the ORM (seeders, tests) has no `v0.1.0` version row; only the API
    creates it. The Versi tab reads economic figures from the lock snapshot
    (`versioning/views._state_blocks`), legacy CEA/BIA pointer rows are only a fallback.
18. Git Bash heredocs and `sed` on this machine: a quoted heredoc still fails on box-drawing or
    other non-ASCII characters, and Python strings in heredocs lose escapes. Write a patch
    script with the Write tool and run it.

### Standing constraints from the lecturer

- Never delete `HF_ARNI_ACEI_004`.
- Every economic parameter must be editable in the UI, never hardcoded.
- Missing/blank/null must never silently become 0 or a favourable judgement.
- Synthetic test data must be labelled and kept apart from research cases.

## What this is

**DeciBridge** is a hospital formulary committee (KFT — *Komite Farmasi dan Terapi*) decision-support web app for Indonesian hospitals. It guides KFT teams through an evidence-based, auditable workflow for deciding whether to admit a drug to the formulary. Pilot case throughout: **ARNI vs ACEI** for HFrEF patients.

The system is **case-based** — one "case" = one formulary decision — and enforces a strict **separation between evidence layer (immutable once locked) and local input layer (editable per-institution)**.

## Authoritative sources

| Document | Purpose |
|---|---|
| `../Brief/11052026_Workflow and Steps kerja untuk IT.docx` | Lecturer's full spec (Indonesian, ~110K tokens). **Source of truth — do not paraphrase from memory; re-read it for questions about schema, validation, or business rules.** |
| `docs/brief_extraction_id.md` | UTF-8 markdown extraction of the brief (~14k lines, durable, lives in the repo). Regenerate via the docx-skill `unpack.py` + a small XML-to-MD script if the source docx changes. |
| `C:\Users\gedes\.claude\plans\hello-okay-so-i-playful-puddle.md` | Sprint plan + roadmap (Sprint 0 → Sprint 12) |
| `README.md` | Setup & layout |
| *(still pending from lecturer)* `DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx` | Sample case data |
| *(still pending from lecturer)* `DeciBridge_Database_Dictionary_MVP_ARNI_vs_ACEI_IT_READY.xlsx` | Authoritative schema blueprint |

## Stack

Django 5.2 + DRF + SimpleJWT + Celery 5.6 · PostgreSQL 16 (Docker host port **5433**, NOT 5432) · Redis 7 · React 18 + Vite + TypeScript + Mantine 7 + TanStack Query · @mantine/charts + Recharts (BIA trajectory) · django-simple-history + django-crum (audit) · pytest + Vitest + Playwright (Sprint 12 only).

## Sprint status (as of last session)

| # | Sprint | Status |
|---|---|---|
| 0 | Repo scaffold (Django + React + Docker + CI) | ✅ shipped + verified + committed |
| 1 | Auth, 5 roles, append-only audit | ✅ shipped + verified + committed |
| 2 | Case lifecycle (state machine: draft→in_review→approved→locked→archived) | ✅ shipped + verified + committed |
| **3** | **Excel intake** | ⏸ **deferred — lecturer hasn't supplied case-pack / dictionary XLSX yet** |
| 4 | CEA Quick (ICER engine, 6 dominance bands, ±20% sensitivity) | ✅ shipped + verified + committed |
| 5 | BIA (1-year + 3-year impact, severity classes, trajectory chart) | ✅ shipped + verified + committed |
| 6 | EtD (9 GRADE domains, references, 5-point judgement, certainty, aggregation) | ✅ shipped + verified + committed |
| 7 | Recommendation synthesis (weights, CBA, traffic-light: GREEN/YELLOW/RED) | ✅ shipped + verified + committed |
| 8 | Approval + Sign-Off (Ketua KFT signs with checkbox + password re-verify) | ✅ shipped + verified + committed + role-gate hotfix landed (commit 455c4f7) |
| 9 | Policy brief DOCX/PDF export (python-docx + docx2pdf, MS Word required) | ✅ shipped + verified + committed |
| 10 | Versioning + audit reconstruction UI (auto-snapshot on lock + timeline + diff) | ✅ shipped + verified + committed |
| 11 | Long-term archive (SHA-256 manifest + 7-year retention + Admin IT user) | ✅ shipped + verified + committed |
| 12 | Hardening + Playwright smoke + user manuals + demo script + deployment notes + dashboard redesign + version bump to v1.0.0 | ✅ shipped + verified + committed |
| 13 | Public marketing landing page (Mantine port of Accenprove style) + routing rewire (`/` = landing, `/dashboard` = authed home) | ✅ shipped + verified + committed |
| 14 | Production deployment to Railway (Dockerfile + LibreOffice swap + SPA fallback + Whitenoise compressed static) | ✅ **LIVE at https://decibridge-production.up.railway.app** |

**🎉 12-sprint roadmap complete + bonus deploy.** All sprints except Sprint 3 (Excel intake — deferred pending dosen XLSX) are shipped, verified, and committed.

**Test suite: 520 tests, all passing.** Coverage target 80%.

## Post-demo revision (lecturer feedback — `../Brief/Hasil Checking DeciBridge.docx`)

After the first lecturer demo we received a substantial revision request turning the
"CEA Quick" MVP into a proper HTA-grade cost-utility engine. Full plan + phase tracking:
**`docs/revision-plan.md`**. Phases R0–R6; status so far:

- **R0 ✅** — CEA/BIA "Hitung" button now enables immediately after "Simpan" (`setQueryData`, no refetch race).
- **R1 ✅** — new additive **`apps/econ`**: `EconomicModel` + `EconomicParameter` registry. High precision (`DECIMAL(20,4)` cost, `DECIMAL(18,10)` rate/utility, `DECIMAL(28,10)` value), per-parameter provenance metadata (source, year, observed/proxy/assumption), auto-versioning, `value_of()` resolver with alternative + per-year fallback. Never round in the calc layer.
- **R2 ✅** — deterministic engine `apps/econ/engine_deterministic.py` (multi-year cost+QALY, discounting, ICER, NMB, INB, decision rules, full precision, no premature rounding) + append-only `EconDeterministicResult` + `service.py` + DRF API (`/cases/{id}/econ/model|parameters|compute|results`). Frontend **CEA tab replaced by `src/econ/EconTab.tsx`** (label "Analisis Ekonomi"). Reproduces the lecturer's acceptance table EXACTLY (ICER 516,105,577.57 / INB −11,109,590.73), verified in-browser.
- **R3 ✅** — safe missing-data handling. `recommendation/engine.py` returns `status "incomplete"` + `missing_components` (no fabricated RED) when EtD/CE/BIA missing; empty CBA → `cba_score None` ("not assessed"), composite re-normalised (never auto-100/0). **CE sub-score now comes from the econ deterministic result** (`apps/econ/scoring.py`), not legacy `CEAResult`. Compute returns HTTP 422 + missing list when incomplete; `Recommendation.cba_score` nullable. Frontend shows the missing-inputs alert.
- **R4 ✅** — cost-offset BIA, **econ-backed** (not a standalone rework). Pure `apps/econ/engine_bia.py` (event cost-offset: `net = incremental_drug − event_cost_offset + incremental_other`, per-year table, severity/budget-score), append-only `EconBIAResult`, `service.run_bia`, DRF `/econ/bia/compute|results`. `annual_budget_baseline` added to `EconomicModel`. **Recommendation `budget_score` now reads the econ BIA result** (legacy `apps/bia` orphaned from UI/recommendation, still has its own tests). Frontend BIA tab replaced by `src/econ/EconBIATab.tsx`. `patients_int = eligible × uptake × market_share`.
- **R5 ✅** — PSA + CEAC + CE-plane (#6-8). Pure `apps/econ/engine_psa.py` (**numpy**): Monte-Carlo, seedable/reproducible, Beta/Gamma/Log-normal/Normal distributions. `EconomicParameter` gained `distribution/dist_param1/dist_param2`; append-only `EconPSAResult`; `service.run_psa`; DRF `/econ/psa/compute|results`. New **9th tab** `src/econ/EconPSATab.tsx` (recharts CE-plane scatter + CEAC curve). numpy added to pyproject. Verified: P(cost-effective) 4.8% @ WTP 85M.
- **R6 ✅** — Excel validation import (#12). We own the workbook format (`apps/econ/validation_workbook.py` build+parse). `validation_service.import_and_validate` maps a workbook onto a case, validates ranges/duplicates/consistency, runs the engines, and produces a PASS/FAIL report (expected/actual/diff/tolerance per metric). DRF `POST /econ/validate/` + `GET /econ/validate/template/`. `export_validation_workbook` command; generated `docs/DeciBridge_Economic_Validation_Model.xlsx`. Frontend `ValidationImportCard` in the Analisis Ekonomi tab. openpyxl added.

**🎉 All post-demo revision items (R0–R6) complete.** The lecturer's 12 feedback points are addressed. See `docs/revision-plan.md`.

## Round 2 — acceptance testing + real validation workbook (V1–V3)

Source: Pak Anom's acceptance test of `HF_ARNI_ACEI_004` + the real
`DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx` (tracked at `backend/apps/econ/tests/fixtures/`).

- **V1 ✅** — adopted his REAL parameters (prob 0.45/0.7077, drug 15,399,360/324,000, admission 6,889,093, utility 0.7, QALY loss 0.1, discounts 0.03, PSA seed **20260724**). The engine formula was already correct — only my decomposition was invented. **BIA aligned**: `market_share` defaults to 1.0 (his model = `eligible × uptake` alone — the double-count he flagged) + low/medium/high scenario table. Clinical outputs (ARR/RR/RRR/NNT/LOS). `annual_budget_baseline` now **optional** → severity `not_assessed`, `budget_score` null. **`lecturer_workbook.py` parses his file as-is** → QC01–QC11 report. All QC values match exactly.
- **V2 ✅** — **`CaseVersion.snapshot`** JSON stores the full immutable VALUE snapshot on lock (econ model+params, deterministic, BIA, PSA, EtD per-domain, CBA, recommendation, approval, **+ legacy CEA/BIA**). Built by `apps/cases/decision_snapshot.py`; backfill: `python manage.py backfill_decision_snapshots`.
- **V3 ✅** — `apps/cases/completeness.py` gates approve/lock: **all 9 EtD domains mandatory** (user decision), + CEA + BIA + recommendation. CBA advisory. Blocked → **HTTP 422 + missing list**; `GET /cases/{id}/readiness/` drives the "Kelengkapan Dossier" checklist on Sign-Off.

- **V4 ✅** — finished the migration. **Policy Brief** (`policy_brief/service.py`) now builds its CEA/BIA blocks from the econ results with a legacy fallback for pre-migration cases; **Versi** state endpoint returns the full `snapshot` (+ `has_snapshot`); **Archive manifest** now inventories `econ_deterministic_results`, `econ_bia_results`, `econ_psa_results`. Frontend surfaces BIA uptake scenarios and the clinical validation block (ARR/RR/NNT/admission saving).

**Root cause of his report (own-goal to remember):** R2/R4 migrated the compute tabs to `apps/econ` but left **Sign-Off, Brief, Versi, Archive and the lock snapshot** on the legacy `apps/cea`/`apps/bia` tables. All are now migrated (econ-first, legacy fallback). `apps/cea`/`apps/bia` remain only as fallback readers for cases locked before the migration.

### Deploy notes (round 2)

- `entrypoint.sh` now runs **`backfill_decision_snapshots`** on every container boot. It
  only fills versions whose `snapshot` is NULL, so it is a no-op after the first boot —
  this removes the need for Railway shell access to populate pre-V2 locked cases.
- **`seed_econ_validation_case` is deliberately NOT in the entrypoint**: it overwrites the
  economic parameters for `HF_ARNI_ACEI_001` and would silently wipe lecturer edits on
  every deploy. Run it manually via the Railway shell when you want the workbook values.
- **Verification gotcha:** the SPA catch-all serves `index.html` with **HTTP 200** for any
  unmatched path, so a missing API route looks identical to a working one if you only
  check the status code. Always assert on the response **body** (JSON vs `<!doctype html>`)
  when probing whether a deploy is live.
- The versioning state endpoint takes the **version id** (int), not the version number:
  `/cases/{case_id}/versions/{version_id}/state/`.

**Never delete `HF_ARNI_ACEI_004`** — it is his regression case for locked-snapshot + cross-module consistency.

**Key revision facts:**
- **No workbook.** Lecturer's `DeciBridge_Economic_Validation_Model_ACEI_Dual.xlsx` was never provided. We build engines correct-by-formula and seed our own verified default params (`apps/econ/validation_fixtures.py`) that reproduce the acceptance numbers. `python manage.py seed_econ_validation_case` populates HF_ARNI_ACEI_001.
- The traffic-light recommendation now consumes the econ deterministic result (`apps/econ/scoring.py::ce_score_from_result`) — done in R3.
- The legacy `apps/cea` ("CEA Quick") and `apps/bia` backends still exist but are orphaned from the UI + recommendation (used only by their own tests). Both the CEA and BIA tabs and the recommendation's CE + budget sub-scores now come from the econ model. Old frontend `src/cea/CEATab.tsx` + `src/bia/BIATab.tsx` are unused.
- `vite.config.ts` `base` is now gated on build mode (prod `/static/`, dev `/`). Local dev serves at `/` again; deep-link refreshes work.

## Live deployment

| | |
|---|---|
| URL | https://decibridge-production.up.railway.app |
| Platform | Railway (single service: Django serves both API + React build) |
| DB | Railway managed Postgres |
| Persistent storage | Railway volume mounted at `/app/media` |
| DOCX→PDF on Linux | LibreOffice headless via `soffice` (replaces docx2pdf which needs Word) |
| Test users | All 6 from `create_test_users`, password `TestPass123!` |
| Demo creds intentionally public | Acceptable for portfolio (fake data) |

Deploy guide: `docs/railway-deploy.md` (covers GH push, Postgres add-on, env vars, volume, domain, smoke tests).

### Deploy gotchas chain (every one of these bit us — don't repeat)

1. `vite.config.ts` imported `defineConfig` from `'vite'` but used Vitest's `test` key → tsc -b bailed → frontend stage failed. Fix: import from `'vitest/config'`.
2. Railway healthcheck probes hit container with Host `healthcheck.railway.app` → `DisallowedHost`. Fix: settings auto-appends `healthcheck.railway.app` + `RAILWAY_PUBLIC_DOMAIN` to ALLOWED_HOSTS.
3. `SECURE_SSL_REDIRECT=True` (Sprint 0 hardening) → healthcheck probes (bypass edge proxy, no X-Forwarded-Proto) got 301. Fix: removed SECURE_SSL_REDIRECT on managed-edge platforms.
4. Vite's default `base: '/'` made index.html reference `/assets/...` which SPA fallback re-served as HTML → blank white page. Fix: `base: '/static/'` + `%BASE_URL%` placeholder on favicon.
5. WhiteNoise `CompressedManifestStaticFilesStorage` would re-hash Vite's already-hashed asset filenames → 404. Fix: use plain `CompressedStaticFilesStorage`.

### Operational quick-refs

- Force a redeploy: push any commit, or in Railway UI: Deployments → Redeploy this version
- Roll back: Deployments → pick previous successful → Redeploy this version
- Shell into the running container: **`railway ssh`** (CLI). There is no "Open Shell" button in the dashboard — that note was wrong. Full flow: `railway login` (interactive browser) → `railway link` → `railway ssh bash -lc "cd /app/backend && <cmd>"`. `railway ssh` also accepts a command directly instead of an interactive shell.
- View live logs: Deployments → latest → Runtime Logs tab
- Add an env var: Variables tab → Raw Editor for bulk paste

## Test-user provisioning

Idempotent management command — re-runnable any time, safe across sessions:
```powershell
python manage.py create_test_users [--reset-password]
```
Creates all 6 demo accounts with password `TestPass123!` (see Test users below).

## Sprint 9 verification crib

Before Sprint 10 starts, verify the policy brief works end-to-end on the live app:

1. Log in as HTA (`hta@test.local`). Open an `approved` or `locked` case (e.g. `_006_2`).
2. Click the new **Brief** tab (8th tab, between Sign-Off and Versi).
3. Click **Terbitkan Ringkasan**. ~10-30 second wait (MS Word opens in background — do not interrupt).
4. Version 1 row appears with green "Selesai" badge + DOCX/PDF download buttons.
5. Download DOCX → opens in Word, 7 sections visible (cover, exec summary with green/yellow/red box, CEA, BIA, EtD 9-domain table, CBA, references, audit signatures).
6. Download PDF → opens in PDF reader, looks pixel-identical to DOCX.
7. Click **Buat Versi Baru** → v2 row appears with different SHA-256 hashes.
8. Log in as KFT Member (`kft1`) → same case → Brief tab → can list + download, but cannot see Terbitkan button.
9. Try generating on a `draft` case → button disabled with tooltip explaining why.

Known platform caveats:
- **MS Word must be installed AND not in mid-task** when generation fires. `docx2pdf` shells out to Word; if Word is busy on another doc, the conversion may hang or fail. Failures land with status=`failed` and the error in `error_message`; the user sees a red alert in the Brief tab.
- Sprint 12 hardening will swap `docx2pdf` for LibreOffice headless (`soffice --convert-to pdf`) so the cloud deploy works on Linux without Office. Engine + service split keeps this swap to ~10 LOC in `service._convert_docx_to_pdf`.

## Project state cheatsheet

### Backend apps shipped
`apps/core` (health) · `apps/accounts` (User + Role) · `apps/audit` (AuditLog) · `apps/cases` (Case + state machine + CaseVersion auto-snapshot on lock + ArchiveRecord hook on archive) · `apps/cea` (ICER) · `apps/bia` (budget impact) · `apps/etd` (9 domains + references + appraisals) · `apps/recommendation` (weights + CBA + traffic-light) · `apps/approval` (sign-off) · `apps/policy_brief` (DOCX/PDF generation, append-only PolicyBriefDocument with SHA-256) · `apps/versioning` (read-only version list + timeline + state reconstruction + diff) · `apps/archive` (SHA-256 manifest, 7-year retention, append-only)

### Frontend modules shipped
`src/auth/` · `src/cases/` · `src/cea/` · `src/bia/` · `src/etd/` · `src/recommendation/` · `src/approval/` · `src/policy_brief/` · `src/pages/` (Login, Dashboard, Cases, CaseDetail with **8 tabs**: Ringkasan / CEA / BIA / EtD / Rekomendasi / Sign-Off / Brief / Versi) · `src/api/` (client + per-app modules)

### Test users that exist (set up via Django admin)
- `hta@test.local` — `TestPass123!` — **HTA Analyst / Pharmacoeconomist** group
- `sekre@test.local` — `TestPass123!` — **Hospital Pharmacy / KFT Secretariat** group
- `ketua@test.local` — `TestPass123!` — **KFT Chair / Approver** group
- `kft1@test.local` — `TestPass123!` — **KFT Member** group
- `kft2@test.local` — `TestPass123!` — **KFT Member** group
- `adminit@test.local` — `TestPass123!` — **IT Administrator** group (Sprint 11+)

### Case IDs created during verification (all `HF_ARNI_ACEI_NNN`)
- `_001` — pilot from Sprint 2 verification (locked)
- `_002` — Sprint 4/5 CEA+BIA verification (locked)
- `_003` — Sprint 6 EtD verification (likely locked)
- `_004` — Sprint 7 Recommendation verification (likely approved/locked)
- `_005` — Sprint 8 Sign-Off verification (use a fresh ID like `_006` for Sprint 9 testing)

### Git commits so far (branch `main`)
```
feat(sprint-7): weights + CBA + traffic-light synthesis  ← Sprint 8 NOT committed yet
feat(sprint-6): 9-domain EtD appraisal + reference manager
feat(sprint-5): BIA projection engine + trajectory chart
feat(sprint-4): CEA Quick computation engine
feat(sprint-2): case lifecycle with state machine
feat(sprint-1): auth, 5-role RBAC, append-only audit log
feat(sprint-0): repo scaffold for DeciBridge
```
**Sprint 8 needs committing once the failing test is fixed.**

## Conventions

### Backend
- Append-only models: every `*Result` and `Approval` model overrides `save()` to raise `PermissionError` on update; `delete()` always raises. Re-compute = new row.
- Every model that holds clinical/financial data is paired with `register_auditable()` + `HistoricalRecords()`.
- Pure-function engines (`engine.py`) live alongside their app models. No Django imports in engines → trivially testable.
- DRF permission classes per app (`apps/X/permissions.py`) following the brief's 5-role matrix.
- Role-aware fixtures live in `backend/conftest.py` (project-root). App-local conftests only add app-specific fixtures.
- **Pytest fixture gotcha:** each authed-client fixture (`hta_client`, `ketua_client`, etc.) builds its OWN `APIClient` instance — they don't share, so tests can use multiple authed clients in the same body without auth bleed.

### Frontend
- TanStack Query for server state; no global server-state stores.
- One API client module per backend app under `src/api/`.
- One Mantine tab per major workflow stage on `CaseDetailPage`. Read-only-vs-editable rendered via `caseIsLocked` prop + role check.
- All UI strings in **Indonesian**. Code, identifiers, commit messages in **English**.

### Migration ordering gotcha
Apps with data migrations (`accounts.0002_seed_roles`, `etd.0002_seed_domains`) ship the seed file before `0001_initial` exists. `makemigrations` errors. Workaround:
```powershell
Move-Item apps\<app>\migrations\0002_seed_*.py .\_seed.bak
python manage.py makemigrations <app>
Move-Item .\_seed.bak apps\<app>\migrations\
python manage.py migrate
```

## Sprint 9 design notes (next sprint)

**Goal:** generate a Word DOCX policy brief from a locked case, plus a PDF export.

**Library choices:**
- `python-docx` for DOCX (already in Sprint 0 pyproject implicitly — confirm if installed)
- LibreOffice headless or `weasyprint` for PDF export
- Celery task for generation so it doesn't block the HTTP request

**Sections of the brief:**
1. Cover (case_id, title, drugs, decision date, signing Ketua KFT name)
2. Executive summary (traffic-light box, composite score, 1-paragraph justification)
3. CEA results (ICER, dominance, sensitivity table)
4. BIA results (per-year + cumulative, trajectory chart embedded as image)
5. EtD appraisal (per-domain table with mean judgement + dominant certainty)
6. CBA criteria (table, satisfaction status)
7. References (numbered bibliography from ReferenceCitation)
8. Audit summary (signature timestamp + IP + approver name)

**Permission gate:** generation allowed for HTA Analyst / Sekretaris KFT once case is `approved` or `locked`. Document download allowed for all viewers.

**Storage:** generated files land in `media/policy_briefs/{case_id}/v{version}.docx` + `.pdf`. SHA-256 hash recorded on a new `PolicyBriefDocument` model.

## Working with this codebase

- **Sprint plan is non-negotiable scope** — don't add features outside the current sprint without checking the plan file at `C:\Users\gedes\.claude\plans\hello-okay-so-i-playful-puddle.md`.
- **Audit log is sacred** — never DELETE from `audit_log`. Migration that drops it = bug.
- **Append-only invariant** — CEA/BIA/Recommendation/Approval results never update; re-compute always creates a new row.
- **Lock enforcement** — once a case is `locked`, all writes 403 at the API layer. Schema-level enforcement still pending (Sprint 11 candidate).
- **Test before commit** — 80% coverage floor, currently at 90%+.
- **No emojis in code or commits** — user's global rule.
- **Two PowerShell terminals** — backend (`runserver`) + frontend (`npm run dev`). Postgres on Docker port **5433**.

## Open dependencies

- Lecturer must provide `DeciBridge_casepack_*.xlsx` and `DeciBridge_Database_Dictionary_*.xlsx` before Sprint 3 can ship. User has asked twice; no response yet.
- Lecturer must confirm deployment target before Sprint 12 (local-only demo or institutional hosting).
- Demo is upcoming — Sprint 9 (DOCX export) is the highest visual-impact item still to build.
