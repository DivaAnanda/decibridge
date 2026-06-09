# DeciBridge — Railway Deployment Guide

Step-by-step guide to deploy DeciBridge to Railway as **one service** (Django serves both API and the React build) backed by Railway's managed Postgres.

Estimated time: **~30 minutes** for first deploy. Re-deploys after pushes: ~3-5 minutes.

## What you get

- Single URL like `https://decibridge.up.railway.app` serving:
  - `/` → landing page
  - `/login` → login
  - `/dashboard`, `/cases/*` → React app (auth required)
  - `/api/v1/*` → DRF endpoints
  - `/admin/` → Django admin
  - `/static/*`, `/media/*` → static assets + policy briefs + manifests
- Managed Postgres (Railway add-on)
- Persistent volume for `media/` so policy briefs + archive manifests survive redeploys
- LibreOffice baked into the image so DOCX → PDF works on Linux without MS Word

---

## Prerequisites

- Railway account with **$5/month Hobby plan** active (or Trial credit)
- Project pushed to GitHub (or GitLab) — Railway pulls from a repo
- Local docker login optional (Railway builds remotely)

---

## Step 1 — Push to GitHub

If your repo isn't on GitHub yet:

```powershell
cd "E:\Kuliah\Kuliah Semester 6\Project Dosen\DeciBridge\Project"
git remote -v   # check if origin exists

# If empty, create a new GitHub repo at https://github.com/new
# Then:
git remote add origin https://github.com/<your-username>/decibridge.git
git push -u origin main
```

If origin exists, just push the latest commits:

```powershell
git push
```

---

## Step 2 — Create the Railway project

1. Open **https://railway.com/dashboard** and click **New Project**.
2. Choose **Deploy from GitHub repo**.
3. Authorize Railway if prompted, then pick the `decibridge` repo.
4. Railway will read `railway.json` from the repo root and start a Docker build immediately. **Let it run** — but expect the first build to fail because Postgres isn't connected yet.

The build itself takes ~5-10 minutes (Node deps + Python deps + LibreOffice install).

---

## Step 3 — Add Postgres

1. In the project view, click **+ Create → Database → Add PostgreSQL**.
2. Railway provisions a managed Postgres in ~30 seconds.
3. Click the Postgres service → **Variables** tab → confirm `DATABASE_URL` is generated.
4. Click your **decibridge web service** → **Variables** tab → click **+ New Variable** → **Add Reference** → pick the Postgres service's `DATABASE_URL`. This injects the DB connection string into the web service env.

---

## Step 4 — Add environment variables

Still in the web service's **Variables** tab, add the following:

| Variable | Value | Notes |
|---|---|---|
| `DJANGO_DEBUG` | `False` | Wajib production |
| `DJANGO_SECRET_KEY` | (paste a random 64-char string) | Generate locally: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | `decibridge.up.railway.app,*.up.railway.app` | Your Railway domain — adjust after you know the actual URL |
| `CSRF_TRUSTED_ORIGINS` | `https://decibridge.up.railway.app` | Same domain, with `https://` prefix |
| `CORS_ALLOWED_ORIGINS` | `` (empty) | Same-origin deploy → no CORS needed |
| `JWT_ACCESS_LIFETIME_MINUTES` | `30` | |
| `JWT_REFRESH_LIFETIME_DAYS` | `7` | |
| `MEDIA_ROOT` | `/app/media` | Matches the Docker volume below |
| `GUNICORN_WORKERS` | `3` | Default; bump if traffic justifies |

> **Tip:** Click **Raw Editor** in Variables to paste all of the above as `.env` lines instead of clicking 9 times.

---

## Step 5 — Attach a persistent volume

`media/` holds generated policy briefs (DOCX + PDF) and archive manifests. These must survive container restarts.

1. In the web service, go to **Settings** tab.
2. Scroll to **Volumes** section → **+ New Volume**.
3. **Mount path**: `/app/media`
4. **Size**: 1 GB (more than enough for the demo; brief sizes are ~50-100 KB).
5. Save.

---

## Step 6 — Trigger a redeploy

Either:

- Click **Deploy** in the top-right, or
- Push a new commit to GitHub (Railway auto-deploys on push)

The deploy will:

1. Build the Docker image (~5-10 min on first build, ~2-3 min after cache warms up)
2. Apply migrations against the Railway Postgres
3. Run `create_test_users` to seed the 6 demo accounts
4. Start gunicorn on the port Railway assigned

Watch the **Deploy Logs** tab. You should see:

```
==> Applying migrations
Operations to perform: ...
==> Provisioning demo test users (idempotent)
  · ensured  hta@test.local [hta_analyst]
  · ensured  sekre@test.local [farmasi_sekretaris]
  ... etc
==> Starting gunicorn on port XXXX
[INFO] Starting gunicorn ...
```

---

## Step 7 — Find your URL & verify

1. In the web service → **Settings** tab → **Networking** section → click **Generate Domain**.
2. Railway gives you something like `decibridge-production.up.railway.app`.
3. **Update env vars** with the real domain:
   - `DJANGO_ALLOWED_HOSTS` → add the exact host (e.g. `decibridge-production.up.railway.app`)
   - `CSRF_TRUSTED_ORIGINS` → `https://decibridge-production.up.railway.app`
4. Railway will redeploy automatically when you save the env var changes.

Open the URL — you should see the landing page.

Smoke tests:
- `https://your-url.up.railway.app/` → landing page renders
- `https://your-url.up.railway.app/api/v1/health/` → `{"status":"ok","checks":{...}}`
- `https://your-url.up.railway.app/login` → login form
- Log in as `hta@test.local` / `TestPass123!` → redirects to `/dashboard`
- `https://your-url.up.railway.app/admin/` → Django admin (needs superuser; see step 8)

---

## Step 8 — Create a superuser (optional)

To access `/admin/`:

1. Web service → **Settings** → scroll to bottom → click **Open Shell**.
2. In the Railway shell:
   ```bash
   cd /app/backend
   python manage.py createsuperuser
   ```
3. Use whatever email + password you'll remember. This account is for managing user records, viewing audit logs, browsing archive manifests.

---

## Step 9 — Test the full workflow end-to-end

Run through the lecturer demo script (`docs/demo/demo-script.md`) on the live URL:

1. Log in as HTA → create `HF_ARNI_ACEI_RAILWAY_001` → CEA → BIA → EtD → Recommendation
2. Submit for review
3. Log in as Ketua → Sign-Off → lock
4. Generate Policy Brief → verify the PDF downloads and opens cleanly (this is the LibreOffice path — if it works, the production swap from `docx2pdf` succeeded)
5. Tindakan → Arsipkan → manifest JSON download works

If anything fails, check **Deploy Logs** + **Runtime Logs** in the Railway dashboard.

---

## Common gotchas

### Build fails on `npm ci`

You may need to delete `frontend/package-lock.json` and re-run `npm install` locally, commit the new lockfile, push. `npm ci` is strict — any version mismatch with `package.json` makes it bail.

### Build succeeds but the app shows "DisallowedHost" in logs

`DJANGO_ALLOWED_HOSTS` doesn't include Railway's auto-generated host. Add the exact domain (no `https://` prefix, no trailing slash) and redeploy.

### POST requests get 403 with "CSRF verification failed"

`CSRF_TRUSTED_ORIGINS` is missing your Railway URL. Add it with the `https://` prefix.

### Generating a policy brief throws "soffice not found"

The Dockerfile installs `libreoffice-writer` + `libreoffice-core`. If you customized the Dockerfile, ensure those packages stayed in the apt install. Verify in shell:
```bash
soffice --version
```

### Generated PDF looks different from local

Local uses MS Word (pixel-perfect Office rendering). Linux uses LibreOffice (~95% identical, fonts/margins may shift slightly). For the demo, the difference is invisible; for production, install **Microsoft Core Fonts** in the Dockerfile if you need higher fidelity.

### Persistent volume not mounted → media files vanish after redeploy

Check **Settings → Volumes** → ensure mount path is exactly `/app/media`. The MEDIA_ROOT env var must match.

---

## Cost projection

For a portfolio demo with light traffic:

| Item | Monthly cost (Hobby plan) |
|---|---|
| Web service (~512 MB / shared CPU) | $0 - $3 (idle cost based on actual usage, billed per minute) |
| Postgres (managed, 1 GB) | ~$5 |
| Egress (light traffic) | < $1 |
| **Total** | **~$5-9/month** |

Hobby plan ($5 credit/month) covers most of it. If you exceed, Railway prompts upgrade.

---

## Updating the live deployment

Any push to `main` (or whichever branch Railway tracks) triggers an auto-deploy.

```powershell
# Local dev → commit → push
git add .
git commit -m "fix: ..."
git push
# Railway picks it up in ~30 seconds and starts a new build
```

To force-redeploy without code changes (e.g. after env var changes):
- **Deployments** tab → latest deploy → **Redeploy** button

---

## Rollback

- **Deployments** tab → pick a previous successful deploy → **Redeploy this version**

Railway keeps the last ~10 builds available.

---

## Demo URL to share with the lecturer

Once verified, send the lecturer:

```
URL:      https://your-url.up.railway.app
Login:    hta@test.local      / TestPass123!  (HTA Analyst)
          sekre@test.local    / TestPass123!  (Sekretaris KFT)
          kft1@test.local     / TestPass123!  (Anggota KFT)
          kft2@test.local     / TestPass123!  (Anggota KFT)
          ketua@test.local    / TestPass123!  (Ketua KFT — sign-off authority)
          adminit@test.local  / TestPass123!  (Admin IT — archive authority)

Suggested flow: log in as Ketua → open the locked _006 case → tab Versi →
see the archived manifest, then tab Brief → download a DOCX policy brief.
For the full pipeline demo, see docs/demo/demo-script.md.
```
