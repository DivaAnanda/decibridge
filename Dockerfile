# syntax=docker/dockerfile:1.7
#
# DeciBridge — single-image deploy for Railway.
#
# Stage 1 (node): builds the React app with Vite into /app/dist
# Stage 2 (python): installs backend deps + LibreOffice, copies the React
#                   dist into FRONTEND_DIST so Django's WhiteNoise + SPA
#                   fallback view serve it.
#
# The final image runs: migrate → create_test_users → gunicorn (see entrypoint.sh).

# ---------------------------------------------------------------------------
# Stage 1: build the React frontend
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend

WORKDIR /build

# Cache deps separately from source so changes to .tsx don't blow the layer.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./

# Production API base URL — Railway injects DECIBRIDGE_PUBLIC_URL at deploy
# time (we set it in railway env), or fall back to relative paths so the same
# domain serves both frontend and API.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ---------------------------------------------------------------------------
# Stage 2: Python + Django + LibreOffice runtime
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=decibridge.settings

# System deps:
#   libreoffice-writer  → soffice headless for DOCX→PDF (replaces docx2pdf)
#   libpq5              → psycopg runtime
#   curl                → Railway healthcheck convenience
#   fonts-dejavu-core   → fallback fonts so LibreOffice doesn't render boxes
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-core \
        libpq5 \
        curl \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend dependencies first (cache layer).
COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --upgrade pip && \
    pip install -e /app/backend && \
    pip install gunicorn

# Backend source.
COPY backend/ /app/backend/

# Frontend build output goes here — settings.FRONTEND_DIST points at it.
COPY --from=frontend /build/dist /app/frontend_dist

ENV FRONTEND_DIST=/app/frontend_dist \
    MEDIA_ROOT=/app/media \
    PATH="/usr/local/bin:$PATH"

WORKDIR /app/backend

# collectstatic baked into the image so first-request latency is low.
# Run with a fake SECRET_KEY since DJANGO_SECRET_KEY is set at runtime.
RUN DJANGO_SECRET_KEY=build-time-placeholder \
    DJANGO_DEBUG=False \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=sqlite:///tmp/build.sqlite3 \
    JWT_ACCESS_LIFETIME_MINUTES=30 \
    JWT_REFRESH_LIFETIME_DAYS=7 \
    CORS_ALLOWED_ORIGINS= \
    python manage.py collectstatic --noinput --clear

# Make media/ writable by gunicorn worker.
RUN mkdir -p /app/media && chmod -R 755 /app/media

COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Railway sets PORT — entrypoint reads it and passes to gunicorn.
ENTRYPOINT ["/app/entrypoint.sh"]
