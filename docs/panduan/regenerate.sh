#!/usr/bin/env bash
# Rebuilds the manual book from nothing: an empty database, the full walkthrough
# of the training case in the browser, then the DOCX and PDF.
#
# Run from Git Bash with Docker Desktop running:   bash docs/panduan/regenerate.sh
# Afterwards, return to the normal stack with:      docker compose up -d backend frontend
set -euo pipefail
cd "$(dirname "$0")/../.."

COMPOSE="docker compose -f docker-compose.yml -f docs/panduan/docker-compose.manual.yml"
CASE_ID="DB_DEMO_HF_001"
OUT="docs/panduan"
export MANUAL_BUILD_COMMIT="$(git rev-parse --short HEAD)"

docker compose up -d db redis
docker compose stop backend
docker compose exec -T db psql -U decibridge -d postgres \
  -c "DROP DATABASE IF EXISTS decibridge_manual" -c "CREATE DATABASE decibridge_manual"
$COMPOSE up -d --force-recreate backend frontend

echo "Menunggu aplikasi siap..."
until curl -sf http://localhost:8000/api/v1/health/ >/dev/null; do sleep 3; done
until curl -sf http://localhost:5173/ >/dev/null; do sleep 3; done

rm -f "$OUT"/screenshots/*.png
(cd frontend && node e2e/capture-manual.mjs)

mkdir -p "$OUT/contoh-brief"
for version in 1 2; do
  for ext in docx pdf; do
    docker cp "decibridge-backend:/app/media/policy_briefs/$CASE_ID/v$version.$ext" \
      "$OUT/contoh-brief/${CASE_ID}_policy_brief_v$version.$ext"
  done
done

backend/.venv/Scripts/python.exe "$OUT/build_manual.py"
