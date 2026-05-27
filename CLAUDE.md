# DeciBridge — Project Context for Claude Code

This file is auto-loaded into every Claude Code session in this repo. Keep it short and current.

## What this is

**DeciBridge** is a hospital formulary committee (KFT — *Komite Farmasi dan Terapi*) decision-support web app. It guides Indonesian hospital teams through an evidence-based, auditable workflow for deciding whether to admit a drug to the formulary. Pilot case throughout: **ARNI vs ACEI** for HFrEF patients.

The system is **case-based** — one "case" = one formulary decision — and enforces a strict **separation between evidence layer (immutable once locked) and local input layer (editable per-institution)**.

## Authoritative sources

| Document | Purpose |
|---|---|
| `../Brief/11052026_Workflow and Steps kerja untuk IT.docx` | Lecturer's full spec (Indonesian, ~110K tokens). **Source of truth.** |
| `C:\Users\gedes\.claude\plans\hello-okay-so-i-playful-puddle.md` | Sprint plan + roadmap (Sprint 0 → Sprint 12) |
| `README.md` | Setup & layout |
| *(pending from lecturer)* `DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx` | Example case data |
| *(pending from lecturer)* `DeciBridge_Database_Dictionary_MVP_ARNI_vs_ACEI_IT_READY.xlsx` | Authoritative schema blueprint |

If a question about schema, validation, or business rules comes up, **read the brief first** — guessing leads to rework.

## Stack

Django 5 + DRF + SimpleJWT + Celery · PostgreSQL 16 · Redis 7 · React 18 + Vite + TypeScript + Mantine + TanStack Query · pytest + Vitest + Playwright (Sprint 12).

## Current sprint

**Sprint 0 — Infrastructure scaffold (complete).** Active development starts at Sprint 1 (auth, roles, audit foundation).

## Conventions

### Backend

- `apps/` holds Django apps; one app per workflow concern (`accounts`, `cases`, `intake`, `cea`, `bia`, `etd`, `recommendation`, `approval`, `policy_brief`, `versioning`, `archive`, `audit`).
- Settings live in `decibridge/settings.py` (single file for now; split if we add prod target).
- Every model that holds clinical/financial data must be paired with **append-only audit logging** — implemented in Sprint 1 via `django-simple-history` + custom `audit_log` signals.
- Excel inputs land in `patient_data_staging` first, then promote to main tables only after validation passes.
- **Never mutate evidence-layer rows post-lock.** Schema-level constraints will enforce this in Sprint 8.

### Frontend

- TanStack Query for all server state. No global stores for server data.
- Zustand for ephemeral UI state (modals, wizard steps).
- Mantine UI primitives — don't introduce another component library.
- API client at `src/api/client.ts`. Add one function per endpoint; reuse `apiClient` axios instance.

### Code style

- Python: ruff + black, 100-char lines, type hints required on exported APIs.
- TS: Prettier (config in `package.json`), strict TS, `noUncheckedIndexedAccess`.
- **No comments explaining *what* code does** — comments are for *why* (hidden constraints, workarounds, invariants). See user's global rules.
- **Immutability everywhere** — never mutate function arguments; spread to create new objects.
- Small files (<400 lines), small functions (<50 lines).

### Indonesian-vs-English

- **UI strings and policy-brief output: Indonesian** (the brief is Indonesian; users are Indonesian hospital staff).
- **Code, identifiers, comments, commit messages: English.**
- Keep role names in their Indonesian form (`Ketua KFT`, `Sekretaris KFT`, `Farmasi RS`) — they're proper job titles.

## Common commands

```sh
# Backend (run from backend/)
.venv\Scripts\activate
python manage.py runserver
python manage.py makemigrations && python manage.py migrate
pytest
ruff check . && black --check .

# Celery (separate terminal, Windows requires --pool=solo)
celery -A decibridge worker --loglevel=info --pool=solo

# Frontend (run from frontend/)
npm run dev
npm run test
npm run typecheck
npm run format

# Whole repo
pre-commit run --all-files
```

## Working with this codebase

- **Sprint plan is non-negotiable scope.** Don't add features outside the current sprint without checking the plan file.
- **Audit log is sacred.** Never `DELETE` from `audit_log`. Never write a migration that drops audit history.
- **Versioning rules.** `v0.x` = draft (everything editable). `v1.x` = approved/locked (evidence frozen). `v2.x+` = major revision with documented reason.
- **No skipping validation.** Excel inputs must run the full validation matrix before any data lands in main tables.
- **Test before commit.** 80% coverage is the floor, not the goal.
- **For UI changes:** check the `e2e-runner` agent and the `gan-design` skill if visual polish matters.

## Open dependencies

- Lecturer must provide `DeciBridge_casepack_*.xlsx` and `DeciBridge_Database_Dictionary_*.xlsx` before Sprint 3.
- Lecturer must confirm deployment target before Sprint 12.
