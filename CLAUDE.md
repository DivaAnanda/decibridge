# DeciBridge — Project Context for Claude Code

Auto-loaded into every Claude Code session in this repo. Keep short, keep current.

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
| 10 | Versioning + audit reconstruction UI (auto-snapshot on lock + timeline + diff) | ✅ shipped + tests green — **awaiting your manual verification** |
| **11** | **Long-term archive (read-only retention)** | **NEXT** |
| 11 | Long-term archive (read-only retention) | pending |
| 12 | Hardening + E2E Playwright + docs | pending |

**Test suite: 229 tests, all passing.** Coverage target 80% (well above).

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
`apps/core` (health) · `apps/accounts` (User + Role) · `apps/audit` (AuditLog) · `apps/cases` (Case + state machine + CaseVersion auto-snapshot on lock) · `apps/cea` (ICER) · `apps/bia` (budget impact) · `apps/etd` (9 domains + references + appraisals) · `apps/recommendation` (weights + CBA + traffic-light) · `apps/approval` (sign-off) · `apps/policy_brief` (DOCX/PDF generation, append-only PolicyBriefDocument with SHA-256) · `apps/versioning` (read-only version list + timeline + state reconstruction + diff)

### Frontend modules shipped
`src/auth/` · `src/cases/` · `src/cea/` · `src/bia/` · `src/etd/` · `src/recommendation/` · `src/approval/` · `src/policy_brief/` · `src/pages/` (Login, Dashboard, Cases, CaseDetail with **8 tabs**: Ringkasan / CEA / BIA / EtD / Rekomendasi / Sign-Off / Brief / Versi) · `src/api/` (client + per-app modules)

### Test users that exist (set up via Django admin)
- `hta@test.local` — `TestPass123!` — **HTA Analyst / Pharmacoeconomist** group
- `sekre@test.local` — `TestPass123!` — **Hospital Pharmacy / KFT Secretariat** group
- `ketua@test.local` — `TestPass123!` — **KFT Chair / Approver** group
- `kft1@test.local` — `TestPass123!` — **KFT Member** group
- `kft2@test.local` — `TestPass123!` — **KFT Member** group
- *(optional, not yet created)* `adminit@test.local` — IT Administrator group, needed only for Sprint 11

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
