# Panduan Ketua KFT / Approver

**Akun demo**: `ketua@test.local` / `TestPass123!`

## Tanggung Jawab Anda

Anda adalah **otoritas tunggal** untuk keputusan formularium. Hanya Anda yang bisa:

- Menyetujui sebuah kasus.
- Menolak atau meminta revisi kasus.
- Mengunci keputusan (membuat versi v1.0 permanen).
- Mengarsipkan kasus terkunci untuk retensi jangka panjang.

## Alur Sign-Off

### 1. Buka kasus yang menunggu sign-off

Login → Beranda → kartu **Aksi Cepat** akan menampilkan **"Kasus Menunggu Tinjauan"** yang difilter ke status `in_review`. Klik kasus mana pun untuk membuka.

### 2. Tinjau dossier

Sebelum tanda tangan, tinjau semua tab:
- **Ringkasan** — identitas + PICO.
- **CEA Quick** — ICER dan dominansi.
- **BIA** — dampak per tahun.
- **EtD** — vote 9 domain dari semua Anggota KFT.
- **Rekomendasi** — traffic-light final + justifikasi.

Klik **Sign-Off** tab untuk masuk ke ringkasan dossier yang siap ditandatangani.

### 3. Tiga pilihan keputusan

Di tab Sign-Off Anda akan melihat tiga tombol:

| Tombol | Efek | Reason wajib? |
|---|---|---|
| **Setujui dengan Sign-Off** (hijau) | Status flip `in_review → approved`. Anda mengonfirmasi rekomendasi sistem. | Tidak |
| **Minta Revisi** (oranye) | Status flip `in_review → draft`. HTA Analyst perlu memperbaiki. | **Ya** |
| **Tolak** (merah) | Status flip `in_review → draft`. Kasus dihentikan dengan alasan. | **Ya** |

### 4. Modal Sign-Off (verifikasi 2-langkah)

Klik salah satu tombol → modal akan muncul. Anda **wajib**:

1. ✅ **Centang checkbox konfirmasi** ("Saya konfirmasi telah meninjau dossier ini...").
2. ✅ **Masukkan password Anda** (`TestPass123!` di demo).
3. Untuk Minta Revisi / Tolak: isi **Alasan** (textarea, wajib).

Klik **Tanda Tangan**. Sistem akan:
- Verifikasi password via `authenticate()` (constant-time check).
- Catat baris **Approval** immutable (append-only).
- Catat audit log dengan IP + timestamp.
- Flip status kasus.

### 5. Setelah disetujui — kunci atau revisi lagi

Setelah Anda menyetujui (`approved`), Anda masih punya pilihan:

- **Minta Revisi lagi** (Tindakan → Minta Revisi): jika Anda berubah pikiran sebelum lock.
- **Kunci Keputusan** (Tindakan → Kunci Keputusan): finalkan. Status flip `approved → locked`. Sistem otomatis membuat snapshot **v1.0** di tab Versi.

### 6. Setelah locked — arsipkan

Untuk menyegel kasus secara permanen dengan retensi 7 tahun:

- Tindakan → **Arsipkan**.
- Status flip `locked → archived`.
- Sistem membuat **manifest JSON** berisi SHA-256 dari setiap artefak (CEA, BIA, EtD, Rekomendasi, Approval, Versi, Brief, AuditLog).
- Manifest itu sendiri di-hash → segel kriptografis.
- Lihat panel **TERARSIPKAN** di tab Versi → unduh manifest JSON sebagai bukti.

## Aturan yang Wajib Anda Ketahui

1. **Password salah → 401**. Sistem tidak akan menandatangani bila password salah.
2. **Checkbox unchecked → 400**. Konfirmasi adalah komitmen, bukan formalitas.
3. **Alasan kosong untuk reject/revisi → 400**. Auditor butuh konteks.
4. **Tanda tangan bersifat permanen** — baris Approval tidak bisa diedit atau dihapus, bahkan oleh superuser Django.
5. **Kunci adalah satu arah** dalam state machine — `locked → archived` adalah transisi akhir. Untuk membuat keputusan baru, mulai kasus baru.

## Apa yang Tidak Bisa Anda Lakukan

- ❌ Mengedit input CEA / BIA / EtD (bukan peran Anda — itu untuk HTA/Anggota KFT).
- ❌ Mengubah baris Approval yang sudah ditandatangani — append-only.
- ❌ Vote sebagai Anggota KFT (kecuali Anda juga ditugaskan peran `kft_member`).

## Skenario Demo Cepat

Jika lecturer/auditor minta demo singkat:

1. Login sebagai Ketua → buka kasus `in_review` → tab Sign-Off.
2. Klik **Setujui dengan Sign-Off** → modal muncul.
3. Demo wrong-password → 401.
4. Centang + password benar + submit → sukses.
5. Tunjukkan tab Versi → snapshot v1.0 otomatis.
6. Tindakan → Arsipkan → tunjukkan manifest SHA-256.
7. Unduh manifest JSON → tunjukkan per-row hashes di file.
