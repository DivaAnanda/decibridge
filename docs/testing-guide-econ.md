# Panduan Uji Sistem Ekonomi Baru (R1–R6)

Cara menguji fitur revisi dosen di DeciBridge: model ekonomi parameterik,
CEA deterministik (ICER/NMB/INB), BIA cost-offset, PSA/CEAC/CE-plane, dan
import validasi Excel.

Live: https://decibridge-production.up.railway.app · Login `hta@test.local` / `TestPass123!`

---

## A. Menyiapkan data (seed) — 2 cara

### Cara 1 (paling mudah, tanpa shell) — Import Excel lewat UI
1. Login sebagai **HTA Analyst** (`hta@test.local`).
2. Buka kasus **draft** (mis. `HF_ARNI_ACEI_001`) → tab **Analisis Ekonomi**.
3. Gulir ke kartu **"Import & Validasi Excel"** paling bawah.
4. Klik **Unduh Template** → tersimpan `DeciBridge_Economic_Validation_Model.xlsx`.
5. Klik **Unggah & Validasi** → pilih file itu.
6. Muncul laporan **PASS (9/9 checks)** — dan semua parameter langsung terisi
   (termasuk distribusi PSA). Kasus kini siap dihitung.

> Catatan: `HF_ARNI_ACEI_001` di server live **sudah di-seed** dengan cara ini.

### Cara 2 — Railway shell / CLI (opsional)
Railway → service DeciBridge → buka shell, lalu:
```bash
python manage.py seed_econ_validation_case
```
Mengisi `HF_ARNI_ACEI_001` dengan parameter validasi (idempotent, aman diulang).

---

## B. Nilai input (kalau membangun kasus dari nol)

Tab **Analisis Ekonomi** → **Parameter Model Ekonomi** (skalar) dan **Registri Parameter**.

### Skalar model
| Field | Nilai |
|---|---|
| Horizon (tahun) | `1` |
| Discount rate biaya | `0` |
| Discount rate QALY | `0` |
| WTP threshold (IDR/QALY) | `85000000` |
| Anggaran tahunan baseline (BIA) | `50000000000` |

### Registri Parameter (klik "Tambah", pilih parameter + alternatif, isi Nilai)
| Parameter | Alternatif | Nilai | Tipe |
|---|---|---|---|
| Biaya obat per pasien per tahun | Intervensi | `14699451.85` | Biaya |
| Biaya obat per pasien per tahun | Komparator | `368611.1161` | Biaya |
| Probabilitas kejadian / rehospitalisasi | Intervensi | `0.19` | Probabilitas |
| Probabilitas kejadian / rehospitalisasi | Komparator | `0.24154` | Probabilitas |
| Biaya per kejadian / rawat inap | Bersama | `20000000` | Biaya |
| Utility dasar | Bersama | `0.75` | Utility |
| Disutility kejadian | Bersama | `0.5` | Disutility |
| Jumlah populasi eligible | Bersama | `1000` | Jumlah |
| Uptake | Bersama | `0.5` | Rasio |
| Market share | Bersama | `0.5` | Rasio |

Klik **Simpan Model** lalu **Simpan Parameter**.

> ⚠️ **PSA butuh distribusi.** Distribusi ketidakpastian (Beta/Gamma/Log-normal)
> belum bisa diedit di tabel registri — hanya terisi lewat **Import Excel** atau
> **seed command**. Kalau membangun manual, CEA deterministik & BIA tetap jalan
> penuh, tapi PSA akan degenerate (semua titik sama). Untuk demo PSA, pakai seed/import.

---

## C. Alur uji per-tab (pakai kasus yang sudah di-seed)

### 1. Tab Analisis Ekonomi — CEA deterministik
Klik **Hitung** → kartu **Hasil Deterministik** harus menampilkan:

| Metrik | Nilai yang benar |
|---|---|
| Total cost intervensi | Rp 18.499.451,85 |
| Total cost komparator | Rp 5.199.411,12 |
| Total QALY intervensi / komparator | 0.655000 / 0.629230 |
| Incremental cost | Rp 13.300.040,73 |
| Incremental QALY | 0.025770 |
| ICER | 516.105.577,57 |
| INB @ WTP 85 jt | Rp −11.109.590,73 |
| Keputusan | **TIDAK COST-EFFECTIVE** |

Plus tabel rincian per tahun (sebelum → sesudah discounting).

### 2. Tab BIA — dampak anggaran dengan cost offset
Klik **Hitung BIA** → harus tampil:
- Badge **DAPAT DIKELOLA**
- Dampak bersih kumulatif **Rp 3.325.010.183**
- **6,65%** dari anggaran (horizon)
- Skor anggaran **80 / 100**
- Tabel per tahun: pasien intervensi, Δ biaya obat, cost offset kejadian, dampak bersih, kumulatif.

### 3. Tab PSA — sensitivitas probabilistik
Isi **Iterasi** `2000`, **Seed** `42` → klik **Hitung PSA** → harus tampil:
- **P(cost-effective) ≈ 4,8%** pada WTP 85 jt (konsisten dgn hasil "tidak cost-effective")
- **CE-plane**: sebaran ~2000 titik biru + titik merah (base case deterministik)
- **CEAC**: kurva hijau naik dari ~0% ke ~22% seiring WTP naik
- Seed sama → hasil sama persis (dapat direproduksi).

### 4. Tab Rekomendasi — penanganan data hilang
- Pada kasus **belum lengkap** (mis. belum ada EtD): klik **Hitung Rekomendasi** →
  muncul **"Belum dapat dihitung"** + daftar komponen yang kurang (bukan lagi MERAH palsu).
- Setelah CEA + BIA + EtD lengkap: rekomendasi dihitung; **CBA kosong = "tidak dinilai"**,
  bukan otomatis 100.

### 5. Import & Validasi Excel (tab Analisis Ekonomi, kartu bawah)
- **Unduh Template** → **Unggah & Validasi** file yang sama → laporan **PASS** dengan
  tabel expected/actual/selisih/toleransi per metrik.
- Uji guard: ubah satu nilai `expected` di Excel → unggah → sebagian check **FAIL**.
- Uji konsistensi: unggah template `_001` ke kasus lain → **FAIL** karena case_id tidak konsisten.

---

## D. Ringkasan hasil acuan (untuk verifikasi cepat)
ICER **516.105.577,57** · INB **−11.109.590,73** · Keputusan **tidak cost-effective** ·
BIA kumulatif **3.325.010.183** (dapat dikelola, skor 80) · PSA P(CE) **≈4,8%** @ WTP 85 jt.

Semua angka ini cocok dengan tabel acuan di `../Brief/Hasil Checking DeciBridge.docx`.
