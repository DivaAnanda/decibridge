# Panduan Admin IT

**Akun demo**: `adminit@test.local` / `TestPass123!`

## Tanggung Jawab Anda

- Mengelola user dan peran (via Django admin).
- Mengarsipkan kasus terkunci untuk retensi 7 tahun.
- Memverifikasi integritas arsip menggunakan SHA-256 manifest.
- Menjalankan pre-flight check sebelum demo / acara penting.

## Yang **Tidak** Boleh Anda Lakukan

> Per brief, Admin IT **tidak boleh menyentuh keputusan klinis**.

- ❌ Mengubah CEA, BIA, EtD, Rekomendasi, atau Approval — itu domain klinis.
- ❌ Tanda tangan sign-off (Ketua KFT only).
- ❌ Edit kasus secara langsung (use the proper roles).

## Yang Boleh Anda Lakukan

- ✅ Lihat semua kasus (read access semua peran).
- ✅ Arsipkan kasus berstatus `locked`.
- ✅ Unduh manifest arsip dan verifikasi hash.
- ✅ Manage user account & role assignment via `http://127.0.0.1:8000/admin/`.
- ✅ Reset password user (jika lupa).
- ✅ Jalankan management commands.

## Tugas Operasional Rutin

### 1. Provisioning user demo

```powershell
cd Project/backend
.\.venv\Scripts\Activate.ps1
python manage.py create_test_users
```

Idempotent. Aman dijalankan kapan saja. Membuat / memverifikasi 6 akun demo dengan password `TestPass123!`.

Untuk reset password:

```powershell
python manage.py create_test_users --reset-password
```

### 2. Pre-flight sebelum demo

Selalu jalankan ini ~5 menit sebelum lecturer demo:

```powershell
python manage.py demo_preflight
```

Akan memverifikasi:
- Database reachable.
- Semua migrasi sudah diterapkan.
- 5 role rows ter-seed.
- 6 test user ada dengan role yang benar.
- Direktori `media/` writable.
- `docx2pdf` importable (MS Word ada).

Exit 0 = ready. Exit 1 = ada masalah yang harus diperbaiki.

### 3. Manage user via Django admin

Buka `http://127.0.0.1:8000/admin/` dan login dengan superuser.

- **Users** → tambah / hapus / edit akun.
- **Groups** → assign user ke role group (`hta_analyst`, `ketua_kft`, dst).
- **Roles** → daftar 5 role yang tersedia.

### 4. Arsipkan kasus

Setelah Ketua KFT mengunci kasus:

1. Login sebagai Admin IT.
2. Buka kasus → klik **Tindakan → Arsipkan**.
3. Sistem akan:
   - Membuat manifest JSON di `media/archives/{case_id}/manifest.json`.
   - Menghitung SHA-256 dari manifest tersebut.
   - Membuat `ArchiveRecord` dengan retensi 7 tahun.
4. Tab Versi akan menampilkan panel **TERARSIPKAN** dengan:
   - Tanggal arsip.
   - Tanggal retensi berakhir (~7 tahun ke depan).
   - SHA-256 hash manifest.
   - Jumlah artefak per kategori.
   - Tombol **Unduh Manifest JSON**.

### 5. Verifikasi integritas arsip

Untuk membuktikan tidak ada tampering setelah arsip:

1. Unduh manifest JSON.
2. Hitung SHA-256 dari file:
   ```powershell
   certutil -hashfile manifest.json SHA256
   ```
3. Bandingkan dengan field `manifest_sha256` di ArchiveRecord (tab Versi atau Django admin).
4. Jika cocok → tidak ada perubahan sejak arsip dibuat.
5. Per-row hashes di dalam manifest juga dapat di-recomputed untuk verifikasi granular.

## Catatan Keamanan

- **Audit log adalah sakral** — jangan pernah hapus baris dari tabel `audit_log`. Migration yang drop tabel ini adalah bug.
- **Append-only model** — CEA, BIA, Rekomendasi, Approval, PolicyBriefDocument, ArchiveRecord — semua tidak bisa diupdate atau dihapus, bahkan oleh superuser via Django admin form.
- **JWT lifetime** — default 30 menit access token, 7 hari refresh. Configurable via env var `JWT_ACCESS_LIFETIME_MINUTES`.
- **Session timeout** — saat token kedaluwarsa, frontend otomatis refresh sekali; jika gagal user di-logout.

## Troubleshooting

### "CoInitialize has not been called" saat Generate Brief

Bug COM threading di Windows. Sudah di-fix di Sprint 9 hotfix (`pythoncom.CoInitialize`). Jika muncul lagi setelah upgrade, periksa `apps/policy_brief/service.py::_convert_docx_to_pdf`.

### "docx2pdf returned without writing"

MS Word sedang membuka dokumen lain. Tutup semua dokumen Word, lalu retry "Buat Versi Baru".

### Database tidak terkoneksi

Pastikan Docker Compose `db` dan `redis` services running:
```powershell
docker compose ps db redis
```
Postgres ada di port host **5433** (bukan 5432 — Laragon konflik di mesin developer).
