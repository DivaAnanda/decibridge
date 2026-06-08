# DeciBridge — Deployment Notes

Catatan praktis untuk siapa pun yang men-deploy DeciBridge ke environment produksi (rumah sakit atau cloud). MVP saat ini dirancang untuk **demo lokal di Windows + MS Word**. Berikut yang perlu disesuaikan untuk produksi.

## Quick Reference

| Aspek | Dev (sekarang) | Produksi (rekomendasi) |
|---|---|---|
| OS | Windows (laptop dev) | Linux (Ubuntu LTS) |
| DEBUG | `True` | **`False`** — wajib |
| Database | Postgres 16 via Docker port 5433 | Postgres 16 managed (RDS, Cloud SQL, atau on-prem) |
| Redis | Docker | Managed (Elasticache, Memorystore) atau systemd unit |
| Web server | `manage.py runserver` | Gunicorn + Nginx reverse proxy |
| DOCX→PDF | `docx2pdf` + MS Word | `soffice --convert-to pdf` (LibreOffice headless) |
| Static files | Vite dev server | Build dengan `npm run build` + CDN/Nginx |
| HTTPS | Tidak (localhost) | **Wajib** — Let's Encrypt via Nginx atau load balancer |
| Secret management | `.env` file | Vault, AWS Secrets Manager, atau env vars dari orchestrator |
| Backup | Tidak diatur | pg_dump harian + media/ rsync |

## Pre-Deploy Checklist

### Backend (`backend/.env`)

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<random-256-bit-string>          # generate dengan: python -c "import secrets; print(secrets.token_urlsafe(64))"
DJANGO_ALLOWED_HOSTS=decibridge.rs-anda.go.id,localhost
DATABASE_URL=postgres://decibridge:STRONG_PWD@db-host:5432/decibridge
REDIS_URL=redis://redis-host:6379/0
JWT_ACCESS_LIFETIME_MINUTES=15                     # tighter daripada dev (default 30)
JWT_REFRESH_LIFETIME_DAYS=1                        # tighter daripada dev (default 7)
CORS_ALLOWED_ORIGINS=https://decibridge.rs-anda.go.id
```

### Frontend (`frontend/.env.production`)

```env
VITE_API_BASE_URL=https://decibridge.rs-anda.go.id/api/v1
```

Build & deploy:

```bash
npm run build
# Hasil di frontend/dist/ — serve via Nginx
```

## Nginx Config (Reference)

```nginx
server {
    listen 443 ssl http2;
    server_name decibridge.rs-anda.go.id;

    ssl_certificate     /etc/letsencrypt/live/decibridge.rs-anda.go.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/decibridge.rs-anda.go.id/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'" always;

    client_max_body_size 50M;  # untuk upload Excel case-pack di Sprint 3

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /var/www/decibridge/static/;
        expires 30d;
    }

    location /media/ {
        # Dokumen brief & archive manifest — protect dengan auth!
        # Tidak boleh diakses publik tanpa JWT.
        internal;
    }

    location / {
        root /var/www/decibridge/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

## Gunicorn Service

```bash
# /etc/systemd/system/decibridge.service
[Unit]
Description=DeciBridge Backend
After=network.target

[Service]
User=decibridge
WorkingDirectory=/opt/decibridge/backend
Environment="PATH=/opt/decibridge/backend/.venv/bin"
EnvironmentFile=/opt/decibridge/backend/.env
ExecStart=/opt/decibridge/backend/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/decibridge/access.log \
    --error-logfile /var/log/decibridge/error.log \
    decibridge.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

## DOCX → PDF di Linux

Ganti `apps/policy_brief/service.py::_convert_docx_to_pdf` dengan:

```python
import subprocess

def _convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> None:
    result = subprocess.run(
        [
            "soffice", "--headless",
            "--convert-to", "pdf",
            "--outdir", str(pdf_path.parent),
            str(docx_path),
        ],
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice convert gagal: {result.stderr.decode()}")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF tidak ditulis ke {pdf_path}")
```

Install:
```bash
sudo apt install libreoffice
```

Hapus `pythoncom.CoInitialize` calls dan dependensi `docx2pdf` + `pywin32`.

## Celery untuk Async

Saat ini Sprint 9 & 11 sinkronous (HTTP request menunggu generation). Untuk produksi:

1. Aktifkan worker:
   ```bash
   celery -A decibridge worker --loglevel=info --concurrency=2
   ```
2. Pindahkan `service.generate_brief()` dan `service.archive_case()` ke task:
   ```python
   @shared_task
   def generate_brief_task(case_id, user_id):
       ...
   ```
3. View hanya enqueue task → balas 202 Accepted + brief_id placeholder.
4. Frontend poll endpoint detail untuk update status.

## Backup Plan

```bash
# /etc/cron.daily/decibridge-backup
#!/bin/bash
set -e
TS=$(date +%Y%m%d_%H%M%S)
DEST=/backup/decibridge

# DB
pg_dump -U decibridge decibridge | gzip > $DEST/db_$TS.sql.gz

# Media (briefs + manifests)
rsync -a --delete /opt/decibridge/media/ $DEST/media/

# Rotate (keep 30 days)
find $DEST/db_*.sql.gz -mtime +30 -delete
```

## Security Posture

Sudah ada di Sprint 0–11:
- JWT auth via SimpleJWT (Bearer token).
- Per-role permission classes pada setiap endpoint.
- Per-transition role gate di state machine (Sprint 8 hotfix).
- Append-only invariants di model layer.
- Audit log untuk setiap mutasi.
- Password validators default Django (8+ chars).
- Constant-time password verification via `authenticate()`.

Sebelum produksi, **tambahkan**:
- HTTPS (Nginx + Let's Encrypt).
- CSP header (sudah ada di config Nginx di atas).
- Rate limiting (`django-ratelimit` atau Nginx `limit_req`).
- OWASP Top-10 audit (`bandit` untuk Python, `npm audit` untuk JS).
- Penetration test internal sebelum go-live.

## Load Testing (Pre-Launch)

Belum dijalankan. Untuk pra-produksi:

```bash
# locust
pip install locust
locust -f locustfile.py --host=https://staging.decibridge
```

Target: 100 concurrent users, 95% p99 < 2s untuk endpoint read-only, < 30s untuk policy brief generation.

## Retention & Compliance

- Default retention: 7 tahun (configurable di `apps/archive/models.py::DEFAULT_RETENTION_YEARS`).
- Audit log tidak boleh di-purge — itu evidence regulator.
- ArchiveRecord tidak boleh dihapus — append-only enforced di model.
- Media files (`media/policy_briefs/`, `media/archives/`) harus include di backup harian.

## Sprint 3 (Excel Intake) — Belum Ada

Sprint 3 ditunda karena dosen belum supply file dictionary. Saat file tersedia:
- Tambahkan `apps/intake/` dengan validation engine.
- Tambah `apps.intake.tasks.parse_excel_upload` (Celery task).
- Tambah upload wizard di frontend dengan preview per sheet.
- Validation matrix harus match column types & ranges di dictionary file.
