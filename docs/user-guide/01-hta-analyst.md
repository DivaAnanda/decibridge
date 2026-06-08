# Panduan HTA Analyst / Farmakoekonomi

**Akun demo**: `hta@test.local` / `TestPass123!`

## Tanggung Jawab Anda

- Membuat kasus baru di sistem.
- Mengisi data CEA Quick (biaya, efikasi).
- Mengisi data BIA (populasi, uptake, harga).
- Mengelola daftar referensi ilmiah.
- Membantu menghitung Rekomendasi.
- Membuat Policy Brief (DOCX/PDF) setelah kasus disetujui.

> Anda **tidak boleh** menandatangani sign-off atau mengunci keputusan. Itu hak Ketua KFT.

## Langkah Demi Langkah

### 1. Login & buat kasus

1. Buka aplikasi → login.
2. Klik **Buat Kasus Baru** dari Beranda atau menu Kasus.
3. Isi wizard:
   - **Case ID**: format `HF_ARNI_ACEI_001` (huruf besar, angka, underscore).
   - **Title**: deskripsi singkat (mis. "ARNI vs ACEI pada HFrEF").
   - **Intervensi**: nama obat baru (mis. `Sacubitril/Valsartan`).
   - **Komparator**: obat pembanding (mis. `Enalapril`).
   - **Indikasi**: kondisi klinis (mis. `HFrEF`).
4. Submit → masuk ke halaman detail dengan 8 tab.

### 2. CEA Quick — hitung ICER

Klik tab **CEA Quick**. Isi:

| Field | Contoh |
|---|---|
| Biaya intervensi per unit | `10000000` |
| Biaya komparator per unit | `5000000` |
| Efikasi intervensi (QALY) | `2.5` |
| Efikasi komparator (QALY) | `2.0` |
| Ambang WTOP | `250000000` |

Klik **Simpan Input** → **Hitung CEA**.

Hasil akan menampilkan:
- **ICER** (mis. `Rp 10.000.000 / QALY`).
- **Klasifikasi dominansi** (Cost-saving / Cost-effective / Dominated / dll).
- **Skor CE** 0–100 (kontribusi ke rekomendasi akhir).
- Analisis sensitivitas ±20%.

### 3. BIA — dampak anggaran

Klik tab **BIA**. Isi:

| Field | Contoh |
|---|---|
| Populasi pasien per tahun | `1000` |
| Horison proyeksi | `3 tahun` |
| Uptake Tahun 1 / Tahun 3 | `30%` / `60%` |
| Pangsa pasar Tahun 1 / Tahun 3 | `50%` / `70%` |
| Biaya intervensi per pasien per tahun | `10000000` |
| Biaya komparator per pasien per tahun | `500000` |
| Anggaran farmasi tahunan baseline | `10000000000` |

Klik **Simpan Input** → **Hitung BIA**.

Hasil:
- Tabel dampak per tahun (Tahun 1, 2, 3, kumulatif).
- Persentase dari anggaran tahunan.
- Trajectory chart.
- Klasifikasi severity.

### 4. Referensi — bangun daftar pustaka

Klik tab **EtD (9 domain)** → **Tambah Referensi**.

Isi minimal:
- Citation text (sitasi terformat).
- Authors.
- Year.
- Journal.
- DOI / URL.

Referensi ini akan masuk ke Policy Brief otomatis dan dapat dilampirkan oleh Anggota KFT ke domain EtD masing-masing.

### 5. CBA — definisikan kriteria akses

Klik tab **Rekomendasi** → kartu **Kriteria Akses (CBA)** → **Tambah Kriteria**.

Contoh:
- Label: `Diresepkan oleh kardiolog`
- Operator: `equals`
- Value: `kardiolog`
- Centang **Satisfied** bila kriteria terpenuhi.

### 6. Hitung Rekomendasi

Setelah CEA, BIA, EtD (terisi cukup), dan CBA siap:
- Tab **Rekomendasi** → **Hitung Rekomendasi**.
- Pilih metode agregasi bobot: Mean atau Median.

Sistem akan menghitung:
- Skor komposit = 0.40·Bukti + 0.30·CE + 0.20·Anggaran + 0.10·CBA.
- Traffic-light: HIJAU / KUNING / MERAH.
- Justifikasi otomatis dalam Bahasa Indonesia.

### 7. Submit untuk Tinjauan

Tab **Ringkasan** → klik **Tindakan → Submit untuk Tinjauan**.

Status flip: `draft` → `in_review`. Sekarang giliran Ketua KFT.

### 8. Generate Policy Brief

Setelah Ketua KFT menyetujui kasus (status `approved` atau `locked`):
- Tab **Brief** → **Terbitkan Ringkasan**.
- Tunggu ~10–30 detik (MS Word membuat PDF di background).
- Hasil: file DOCX + PDF dengan 7 bagian, hash SHA-256 tercatat.
- Klik **DOCX** atau **PDF** untuk mengunduh.
- Versi naik otomatis (`v1`, `v2`, `v3`...).

## Tips

- **Selalu simpan input dulu** sebelum klik "Hitung" — beberapa form memisahkan dua langkah ini.
- **Hindari karakter aneh** di Case ID — hanya `A-Z`, `0-9`, `_`.
- Jika perlu mengubah input setelah komputasi, **hitung ulang** — sistem akan membuat baris hasil baru, tidak menimpa yang lama.

## Apa yang Tidak Bisa Anda Lakukan

- ❌ Tanda tangan Sign-Off (Ketua only).
- ❌ Lock / Archive kasus (Ketua / Admin IT).
- ❌ Vote bobot domain (Anggota KFT).
- ❌ Hapus baris hasil CEA/BIA/Rekomendasi (append-only).
