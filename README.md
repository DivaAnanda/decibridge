# DeciBridge

Hospital formulary committee (KFT — *Komite Farmasi dan Terapi*) decision-support system for evidence-based drug-adoption decisions. Pilot case: **ARNI vs ACEI** for HFrEF.

> Status: **Sprint 0** — repo scaffold only. Auth, cases, Excel upload, CEA/BIA/EtD, and the rest of the 15-step workflow arrive in subsequent sprints. See `../Brief/` for the full Indonesian specification and `~/.claude/plans/hello-okay-so-i-playful-puddle.md` for the roadmap.

---

## Stack

| Layer | Choice |
|---|---|
| Backend | Django 5 + DRF + Celery + PostgreSQL 16 |
| Frontend | React 18 + Vite + TypeScript + Mantine UI + TanStack Query |
| Queue / cache | Redis 7 (Memurai on Windows) |
| Auth | JWT (SimpleJWT), role-based (5 roles) |
| Excel I/O | `openpyxl` (added Sprint 3) |
| Document gen | `python-docx` + LibreOffice headless (added Sprint 9) |
| Tests | pytest + Vitest + Playwright (Sprint 12) |

---

## Quickstart — Native dev (Laragon)

Requires the Laragon services that are already on this machine: PostgreSQL 18, Memurai (Redis), Python 3.11+, Node 20+.

### 1. PostgreSQL

In Laragon, start PostgreSQL. Then create the database:

```sh
psql -U postgres -c "CREATE DATABASE decibridge;"
```

### 2. Backend

```sh
cd backend
python -m venv .venv
.venv\Scripts\activate                       # PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e ".[dev]"
copy .env.example .env                       # adjust DATABASE_URL if needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend is now at <http://127.0.0.1:8000>. API root: <http://127.0.0.1:8000/api/v1/>. Swagger: <http://127.0.0.1:8000/api/schema/swagger/>.

### 3. Celery worker (separate terminal)

```sh
cd backend
.venv\Scripts\activate
celery -A decibridge worker --loglevel=info --pool=solo   # --pool=solo required on Windows
```

### 4. Frontend

```sh
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Frontend at <http://127.0.0.1:5173>. Should display a green "Backend health" badge once the API is up.

---

## Quickstart — Docker Compose

Alternative if Laragon services aren't running or you want full isolation.

```sh
cp .env.example .env
docker compose up -d db redis
docker compose up backend frontend worker beat
```

All services come up on the same ports as native dev. First boot installs Python and Node dependencies, so it takes a few minutes.

---

## Project layout

```
Project/
├── backend/                  Django + DRF + Celery
│   ├── decibridge/           Project package (settings, urls, celery)
│   ├── apps/
│   │   └── core/             Health check, shared utilities
│   │       ├── views.py      GET /api/v1/health/
│   │       └── tests.py
│   ├── manage.py
│   ├── pyproject.toml        Python deps + ruff/black/mypy/pytest config
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 React + Vite + TS
│   ├── src/
│   │   ├── api/client.ts     axios instance + JWT interceptor + getHealth()
│   │   ├── components/       Shared UI (HealthCheck for now)
│   │   ├── App.tsx           Mantine AppShell + routes
│   │   └── main.tsx          Provider tree (Mantine, QueryClient, Router)
│   ├── package.json          npm deps + Prettier config
│   ├── vite.config.ts        Dev server, /api proxy, Vitest setup
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── nginx.conf            Production reverse proxy to backend
├── docker-compose.yml
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml  Lint + test on push/PR
├── CLAUDE.md                 Project context for Claude Code sessions
└── README.md                 (this file)
```

Sprint 1 will add `apps/accounts/` and `apps/audit/`. Sprint 2: `apps/cases/`. Sprint 3: `apps/intake/`. Etc. — full breakdown in the plan file.

---

## ESLint setup (one-time)

Config-protection prevented committing `eslint.config.js` directly. After the first `npm install`:

```sh
cd frontend
npm init @eslint/config@latest
```

Choose: **To check syntax, find problems, and enforce code style** → **JavaScript modules (import/export)** → **React** → **Yes, using TypeScript** → **Browser** → **JSON** format. Then add the rules from `package.json`'s `prettier` block to integrate Prettier.

---

## Quality gates

| Tool | Command | Where |
|---|---|---|
| Format Python | `black .` and `ruff format .` | `backend/` |
| Lint Python | `ruff check .` | `backend/` |
| Type Python | `mypy decibridge apps` | `backend/` |
| Tests + coverage | `pytest` | `backend/` |
| Format JS/TS | `npm run format` | `frontend/` |
| Lint JS/TS | `npm run lint` | `frontend/` after ESLint init |
| Type JS/TS | `npm run typecheck` | `frontend/` |
| Tests + coverage | `npm run test:coverage` | `frontend/` |
| All-in-one | `pre-commit run --all-files` | repo root |

Coverage target: **80%** (enforced from Sprint 1 onward).

---

## Workflow & roles (Sprint roadmap)

The 15-step workflow and 5 user roles are documented in:
- `../Brief/11052026_Workflow and Steps kerja untuk IT.docx` — source of truth (Indonesian)
- `~/.claude/plans/hello-okay-so-i-playful-puddle.md` — sprint plan with acceptance criteria

| Role | Indonesian | Authority |
|---|---|---|
| Admin IT | Admin IT | System config only — no clinical edits |
| HTA Analyst | Analis HTA / Farmakoekonomi | Upload cases, run analyses, edit EtD |
| Pharmacy / Secretariat | Farmasi RS / Sekretaris KFT | Case lifecycle, local inputs, CBA |
| KFT Member | Anggota KFT | EtD voting, weight assignment |
| KFT Chair | Ketua KFT | **Sole authority** to approve & lock decisions |

---

## License

Academic project — university coursework. License TBD with lecturer.
