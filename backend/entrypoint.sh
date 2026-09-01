#!/usr/bin/env bash
#
# Railway entrypoint — runs every time a new container boots.
#
# Order matters:
#   1. Apply any pending Django migrations against the managed Postgres.
#   2. Ensure the 6 demo test users exist (idempotent — safe to re-run).
#   3. Backfill decision snapshots for versions locked before Phase V2.
#   4. Launch gunicorn bound to the port Railway gave us.
#
# If migrate fails, we bail before gunicorn — better to crash visibly than to
# serve a half-migrated DB.

set -euo pipefail

cd /app/backend

echo "==> Applying migrations"
python manage.py migrate --noinput

echo "==> Provisioning demo test users (idempotent)"
# Don't crash on first deploy if role rows aren't seeded yet — the data
# migration runs as part of `migrate` above, but we still don't want a
# missing role to break the boot.
python manage.py create_test_users --reset-password || \
    echo "    (skipped — roles may not be seeded yet; re-run manually after deploy)"

echo "==> Backfilling decision snapshots (idempotent)"
# Only fills versions whose snapshot is NULL, so this is a no-op after the
# first boot following the Phase V2 deploy. Cases locked before the snapshot
# existed (e.g. HF_ARNI_ACEI_004) get one built from whatever data they hold,
# marked `backfilled: true`.
python manage.py backfill_decision_snapshots ||     echo "    (skipped — non-fatal; re-run manually if needed)"

echo "==> Starting gunicorn on port ${PORT:-8000}"
exec gunicorn decibridge.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
