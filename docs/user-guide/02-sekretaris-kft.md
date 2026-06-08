# Panduan Sekretaris KFT / Farmasi RS

**Akun demo**: `sekre@test.local` / `TestPass123!`

## Tanggung Jawab Anda

- Mengelola siklus hidup kasus (sama seperti HTA Analyst untuk inisiasi).
- Mendefinisikan **Criteria-Based Access (CBA)** — kondisi yang harus dipenuhi agar obat boleh diresepkan.
- Membantu jalankan komputasi CEA/BIA/Rekomendasi.
- Membuat Policy Brief setelah keputusan disetujui.

Peran Anda mirip HTA Analyst dalam hal kemampuan input, dengan tambahan tanggung jawab manajemen lifecycle dan CBA.

## Apa yang Bisa Anda Lakukan

- ✅ Buat kasus baru.
- ✅ Edit data CEA, BIA, EtD references.
- ✅ Tambah / edit / centang CBA criteria.
- ✅ Submit kasus untuk tinjauan (`draft → in_review`).
- ✅ Hitung rekomendasi.
- ✅ Generate Policy Brief.

## Apa yang Tidak Bisa Anda Lakukan

- ❌ Vote 9 domain EtD (itu hak Anggota KFT).
- ❌ Set bobot domain.
- ❌ Sign-off / approve / reject kasus (Ketua KFT).
- ❌ Lock / Archive (Ketua KFT / Admin IT).

## Langkah Demi Langkah (CBA Khusus)

Tab **Rekomendasi** → kartu **Kriteria Akses (CBA)** → **Tambah Kriteria**.

Contoh CBA untuk kasus ARNI vs ACEI:

| Label | Operator | Value | Catatan |
|---|---|---|---|
| HFrEF terkonfirmasi | is_present | — | Diagnosis utama |
| Diresepkan oleh kardiolog | equals | kardiolog | Spesialis penanggung jawab |
| EF ≤ 40% | less_than | 40 | Persen |
| Sudah pernah terapi GDMT optimal | is_present | — | Dokumentasi RM |
| Monitoring K+ tersedia | is_present | — | Lab cek kalium |

Centang **Satisfied** untuk kriteria yang dapat dipastikan terpenuhi di lingkungan RS Anda. Rekomendasi akhir akan terpengaruh:

- Jika semua CBA terpenuhi → skor CBA = 100 → rekomendasi cenderung **HIJAU**.
- Jika hanya sebagian terpenuhi → skor parsial → rekomendasi **dibatasi ke KUNING** (per aturan engine, partial CBA caps recommendation at YELLOW).

## Untuk Alur CEA/BIA/EtD Lihat

Buka [01 — HTA Analyst](./01-hta-analyst.md), karena alurnya sama persis dari sudut pandang teknis.
