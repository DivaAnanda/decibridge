# DeciBridge — Panduan Pengguna

DeciBridge adalah aplikasi pendukung keputusan untuk **Komite Farmasi dan Terapi (KFT)** rumah sakit di Indonesia. Aplikasi ini memandu tim KFT melalui alur evidence-based, terdokumentasi, dan dapat diaudit untuk memutuskan apakah suatu obat boleh masuk ke formularium rumah sakit.

## Apa yang DeciBridge lakukan

Untuk setiap usulan obat, DeciBridge mengikuti pipeline 15 langkah:

1. **Login** dengan peran sesuai.
2. **Buat kasus** dengan ID seperti `HF_ARNI_ACEI_001`.
3. *(Opsional, Sprint 3)* Upload Excel case-pack.
4. Validasi otomatis input.
5. **CEA Quick** — hitung ICER (Incremental Cost-Effectiveness Ratio).
6. **BIA** — hitung dampak anggaran 1 tahun & 3 tahun.
7. **EtD** — penilaian 9 domain GRADE oleh Anggota KFT.
8. **CBA** — kriteria akses bersyarat.
9. **Bobot domain** — bobot kepentingan per anggota.
10. **Sintesis rekomendasi** — Hijau / Kuning / Merah (traffic-light).
11. **Sign-off** Ketua KFT dengan password re-verification.
12. **Generate Policy Brief** (DOCX + PDF).
13. **Rekonstruksi audit** — lihat keadaan kasus pada versi mana pun.
14. **Versioning otomatis** (v0.x draft → v1.x locked → v1.x+1 revisi).
15. **Arsipkan** dengan manifest SHA-256, retensi 7 tahun.

## 5 Peran Pengguna

| Peran | Email demo | Boleh melakukan |
|---|---|---|
| Admin IT | `adminit@test.local` | Kelola user, arsipkan kasus terkunci. **Tidak boleh menyentuh keputusan klinis.** |
| HTA Analyst / Farmakoekonomi | `hta@test.local` | Buat kasus, jalankan CEA/BIA, isi EtD. **Tidak boleh mengunci keputusan.** |
| Sekretaris KFT / Farmasi RS | `sekre@test.local` | Kelola siklus kasus, definisikan CBA. |
| Anggota KFT | `kft1@test.local`, `kft2@test.local` | Vote 9 domain EtD, atur bobot domain. |
| **Ketua KFT / Approver** | `ketua@test.local` | **Otoritas tunggal** untuk menyetujui & mengunci keputusan. |

Password untuk semua akun demo: **`TestPass123!`**.

## Status Kasus

Kasus mengikuti state machine:

```
draft → in_review → approved → locked → archived
                 ↑          ↓
                  └ revisi ─┘
```

- **Draft**: kasus baru, data sedang diinput. Bisa diedit oleh HTA/Sekretaris.
- **In Review (Dalam Tinjauan)**: kasus dikirim ke KFT untuk dinilai dan disetujui.
- **Approved (Disetujui)**: Ketua KFT sudah tanda tangan. Belum final — masih bisa direvisi.
- **Locked (Terkunci)**: Ketua mengunci → evidence layer immutable. v1.0.
- **Archived (Diarsipkan)**: Admin IT arsipkan → manifest SHA-256 dibuat, retensi 7 tahun.

## Tab-tab di Halaman Kasus

Setiap kasus memiliki 8 tab:

| Tab | Tujuan | Aktor utama |
|---|---|---|
| **Ringkasan** | Identitas kasus + pertanyaan PICO | semua |
| **CEA Quick** | Input biaya + efikasi → ICER + dominansi | HTA |
| **BIA** | Input populasi/uptake → dampak per tahun + chart | HTA |
| **EtD (9 domain)** | 9 domain GRADE + referensi | Anggota KFT |
| **Rekomendasi** | Bobot + CBA → traffic-light final | HTA/Sekretaris hitung; KFT vote bobot |
| **Sign-Off** | Tanda tangan Ketua KFT (checkbox + password) | Ketua KFT |
| **Brief** | Generate DOCX & PDF | HTA/Sekretaris/Ketua |
| **Versi** | Riwayat versi + timeline audit + arsip | semua (read-only) |

## Prinsip Dasar

1. **Pemisahan evidence ↔ local input layer**: ubah harga obat lokal tidak mengubah bukti klinis.
2. **Append-only**: hasil CEA/BIA/Rekomendasi/Approval/Brief tidak pernah ditimpa — hitung ulang = baris baru.
3. **Audit log sakral**: setiap perubahan tercatat dengan user, IP, timestamp.
4. **Manifest SHA-256**: arsip permanen disegel dengan hash kriptografis.

## Selanjutnya

Buka panduan spesifik per peran Anda:

- [01 — HTA Analyst](./01-hta-analyst.md)
- [02 — Sekretaris KFT](./02-sekretaris-kft.md)
- [03 — Anggota KFT](./03-anggota-kft.md)
- [04 — Ketua KFT](./04-ketua-kft.md)
- [05 — Admin IT](./05-admin-it.md)
