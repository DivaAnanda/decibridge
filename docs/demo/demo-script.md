# DeciBridge — Skrip Demo Lecturer (15 menit)

Skrip click-by-click untuk presentasi ke dosen. Estimasi: **15 menit**.

## T-5 menit — Persiapan

Sebelum lecturer datang, lakukan ini:

1. **Pastikan Docker Desktop running** (whale icon di taskbar = "Engine running").
2. Buka 3 PowerShell terminal:
   ```powershell
   # Terminal 1
   cd "E:\Kuliah\Kuliah Semester 6\Project Dosen\DeciBridge\Project"
   docker compose up -d db redis

   # Terminal 2
   cd "E:\Kuliah\Kuliah Semester 6\Project Dosen\DeciBridge\Project\backend"
   .\.venv\Scripts\Activate.ps1
   python manage.py demo_preflight
   # → harus "Ready for demo." Jika ada [FAIL], perbaiki sebelum lanjut.
   python manage.py runserver

   # Terminal 3
   cd "E:\Kuliah\Kuliah Semester 6\Project Dosen\DeciBridge\Project\frontend"
   npm run dev
   ```
3. **Tutup MS Word** kalau ada dokumen yang sedang dibuka (akan mengganggu generate brief).
4. **Buka browser** ke `http://localhost:5173/`.

---

## 0–2 menit — Konteks Singkat

> "DeciBridge adalah aplikasi pendukung keputusan untuk Komite Farmasi dan Terapi rumah sakit di Indonesia. Aplikasi ini memandu KFT melalui alur evidence-based dengan audit trail yang dapat diaudit selama 7 tahun. Studi kasus pilot kami adalah ARNI vs ACEI untuk pasien HFrEF."

Tunjukkan halaman login (UI Indonesia, badge **v1.0.0** di kanan atas).

---

## 2–4 menit — Tour Arsip (mulai dari hasil akhir)

Login sebagai Ketua KFT (`ketua@test.local` / `TestPass123!`).

> "Saya mulai dengan kasus yang sudah selesai sepenuhnya — diarsipkan permanen. Ini menunjukkan output sistem secara end-to-end."

1. **Beranda**: tunjukkan dashboard dengan stat boxes (Draft / In Review / Approved / Locked / Archived) dan quick links.
2. Klik **Kasus** → pilih `HF_ARNI_ACEI_006_2` (sudah archived).
3. Tunjukkan badge **DIARSIPKAN** di header kasus.
4. Klik tab **Versi**:
   - Tunjukkan panel besar **TERARSIPKAN** di atas dengan SHA-256 manifest.
   - Tunjukkan **retensi countdown** ("X tahun Y bulan lagi").
   - Tunjukkan **Inventaris Artefak** (CEA results: 3, BIA results: 2, ..., audit log entries: 25).
   - Klik **Unduh Manifest JSON** → buka file di Notepad → tunjukkan per-row SHA-256.
5. Klik **v1.0** di tabel Riwayat Versi → drawer terbuka.
   - Tab **Timeline Audit** → tunjukkan chronological event log (siapa, kapan, IP, diff).
   - Tab **Keadaan Data** → tunjukkan snapshot CEA + BIA + Rekomendasi + Approval + Brief.

> "Ini adalah bukti audit-grade. Manifest SHA-256 ini mendeteksi tampering pada level byte. Setiap baris klinis di-fingerprint."

---

## 4–6 menit — Tour Policy Brief

Tab **Brief** di kasus `_006_2`.

> "Dari kasus terkunci, kita bisa menerbitkan dokumen Word & PDF yang siap dipakai sebagai lampiran rapat KFT."

1. Tunjukkan **Riwayat Versi** (beberapa v1, v2, ...).
2. Klik **DOCX** pada v1 → buka di MS Word.
3. Tunjukkan 7 bagian:
   - Cover (case_id, judul, drugs).
   - Ringkasan Eksekutif dengan **box HIJAU** (traffic-light).
   - CEA (ICER + sensitivity).
   - BIA (per tahun + kumulatif).
   - EtD (9 domain table).
   - CBA (kriteria + status).
   - Referensi (numbered).
   - Audit signature (Ketua, IP, timestamp).
4. Bandingkan PDF (klik **PDF**) — harus pixel-identical.

---

## 6–12 menit — Build kasus baru live (HF_ARNI_ACEI_DEMO)

> "Sekarang saya akan membangun kasus baru dari nol untuk menunjukkan workflow penuh."

### Sebagai HTA Analyst

Logout → login `hta@test.local` / `TestPass123!`.

1. **Buat Kasus Baru** → ID `HF_ARNI_ACEI_DEMO`, judul "Demo Lecturer", Sacubitril/Valsartan vs Enalapril, HFrEF.
2. **Tab CEA Quick**: isi 10000000 / 5000000 / 2.5 / 2.0 / 250000000 → **Simpan** → **Hitung CEA**. Tunjukkan ICER + dominansi "Cost-effective".
3. **Tab BIA**: isi 1000 pasien, uptake 30%/60%, market share 50%/70%, biaya 10000000 / 500000, baseline 10000000000 → **Simpan** → **Hitung BIA**. Tunjukkan trajectory chart.
4. **Tab EtD**: **Tambah Referensi** PARADIGM-HF (NEJM 2014). Isi 3 domain pertama (Judgement = Mungkin ya, Certainty = Sedang).
5. **Tab Rekomendasi**: **Tambah Kriteria CBA** ("Diresepkan kardiolog", equals, kardiolog, **centang Satisfied**).

### Sebagai Anggota KFT 1

Logout → login `kft1@test.local`.

6. Tab **EtD** → vote 2-3 domain (atau biarkan apa yang HTA isi — itu juga bisa).
7. Tab **Rekomendasi** → kartu **Bobot Domain EtD** → geser 2-3 slider → **Simpan Bobot Saya**.

### Sebagai HTA Analyst (kembali)

Logout → login `hta@test.local`.

8. Tab **Rekomendasi** → **Hitung Rekomendasi** → tunjukkan kartu besar **HIJAU** dengan skor komposit + justifikasi otomatis.
9. Tab **Ringkasan** → **Tindakan → Ajukan untuk Tinjauan**.

### Sebagai Ketua KFT

Logout → login `ketua@test.local`.

10. Buka `HF_ARNI_ACEI_DEMO` → tab **Sign-Off**.
11. Klik **Setujui dengan Sign-Off** → modal.
12. **Demo negative path dulu**: kosongkan checkbox → submit → tunjukkan error 400.
13. Centang + password salah → 401.
14. Centang + password benar → sukses → status flip ke `approved`.
15. **Tindakan → Kunci Keputusan** → status `locked`. Tab Versi muncul **v1.0** otomatis.
16. Tab **Brief** → **Terbitkan Ringkasan** → tunggu 15 detik → unduh PDF baru.
17. **Tindakan → Arsipkan** → status `archived` + manifest dibuat.

> "Dalam 6 menit kita telah menjalankan pipeline penuh: dari kasus kosong sampai arsip permanen tertandatangani dan ter-hash."

---

## 12–14 menit — Tunjukkan integritas

1. Buka `http://127.0.0.1:8000/admin/`.
2. **Audit → Audit log** → tunjukkan ratusan entri dari demo barusan (login events, save events, sign-off, lock, archive).
3. **Approval → Approvals** → klik baris approval baru → tunjukkan **form read-only** (tidak ada Save button) → coba delete (tombol tidak tersedia).
4. **Long-Term Archive → Archive Records** → tunjukkan baris baru dengan manifest_sha256, retention_until 7 tahun ke depan.

> "Sistem ini bukan hanya tracker — ini adalah audit-grade evidence registry. Klinisi dapat mempercayai keputusan; auditor dapat memverifikasi."

---

## 14–15 menit — Wrap-up

Q&A. Beberapa pertanyaan yang mungkin muncul + jawaban:

| Pertanyaan | Jawaban singkat |
|---|---|
| Bagaimana deploy ke RS sesungguhnya? | Stack: Django + DRF + React + PostgreSQL. Docker Compose untuk dev. Production butuh HTTPS via reverse proxy + DEBUG=False + Celery untuk async. Notes di `docs/deployment-notes.md`. |
| Bagaimana kalau Word tidak tersedia di cloud Linux? | Swap `docx2pdf` ke `soffice --convert-to pdf` (LibreOffice headless). Engine sudah decoupled — ~10 LOC ganti. |
| Bagaimana sumber data Excel case-pack? | Sprint 3 (importer) ditunda — sedang menunggu file dictionary dari dosen. Forms-first adalah canonical intake sekarang. |
| Kapan retensi 7 tahun bisa diubah? | Hard-coded di `apps/archive/models.py::DEFAULT_RETENTION_YEARS`. Bisa jadi env var di Sprint 12 hardening. |
| Berapa banyak test? | 255 passing pytest, mencakup CEA engine, BIA engine, EtD aggregation, recommendation synthesis, traffic-light rules, approval append-only, versioning, archive manifest, role gates. |

---

## Setelah Demo

```powershell
# Optional: bersihkan kasus demo untuk demo berikutnya
# (Manual via Django admin atau biarkan — tetap tampil di history)
```

Jangan delete `_006_2` — itu adalah centerpiece untuk demo arsip masa depan.
