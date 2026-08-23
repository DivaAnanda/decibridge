# DeciBridge — Lembar Isian Demo (Cheat Sheet)

Nilai **persis** untuk membangun kasus `HF_ARNI_ACEI_DEMO` live di depan dosen.
Setiap angka sudah diverifikasi terhadap engine (`cea/engine.py`, `bia/engine.py`,
`etd/aggregation.py`, `recommendation/engine.py`) — **hasil akhir dijamin HIJAU
dengan skor komposit 86.00**.

> Pegang lembar ini di HP / layar kedua. Jangan menghitung di kepala saat presentasi.

---

## Ringkasan hasil yang HARUS muncul (biar kamu tidak kaget)

| Tahap | Angka yang muncul di layar | Badge |
|---|---|---|
| CEA | ICER **10.000.000 IDR/QALY** | Cost-effective (aman) — skor 100 |
| BIA | Kumulatif **4.275.000.000 IDR** (2,85% dari anggaran 3-thn) | Manageable — skor 80 |
| EtD | Evidence strength **75** | Sedang |
| CBA | 1/1 kriteria terpenuhi | skor 100 |
| **Rekomendasi** | **Komposit 86,00 / 100** | **HIJAU** |

Rumus komposit: `0,40×75 + 0,30×100 + 0,20×80 + 0,10×100 = 86,00` → ≥75 & CBA penuh → **HIJAU**.

---

## 1. Buat Kasus Baru  *(login `hta@test.local` / `TestPass123!`)*

| Field | Isi |
|---|---|
| Case ID | `HF_ARNI_ACEI_DEMO` |
| Judul | `Demo Lecturer — ARNI vs ACEI HFrEF` |
| Obat intervensi | `Sacubitril/Valsartan` |
| Obat komparator | `Enalapril` |
| Indikasi / populasi | `HFrEF` |

---

## 2. Tab CEA Quick  →  Simpan  →  Hitung CEA

| Field | Isi |
|---|---|
| Biaya obat per unit | `10000000` |
| Biaya komparator per unit | `5000000` |
| Efikasi obat (QALY) | `2.5` |
| Efikasi komparator (QALY) | `2.0` |
| Ambang WTOP | `250000000` |

**Hasil:** ICER = **10.000.000 IDR/QALY** · dominansi **Cost-effective (aman)** ·
sensitivitas 6.666.667 – 15.000.000. Narasikan: *"jauh di bawah ambang 250 juta → sangat cost-effective."*

---

## 3. Tab BIA  →  Simpan  →  Hitung BIA

> ⚠️ Uptake & market share diisi sebagai **pecahan 0–1** (0.30 = 30%), **bukan** 30.

| Field | Isi |
|---|---|
| Populasi eligible | `1000` |
| Uptake Tahun 1 | `0.30` |
| Uptake Tahun 3 | `0.60` |
| Market share Tahun 1 | `0.50` |
| Market share Tahun 3 | `0.70` |
| Biaya unit obat | `10000000` |
| Biaya unit komparator | `5000000` |
| Anggaran obat tahunan RS | `50000000000` |
| Horizon proyeksi | `3 tahun` |

**Hasil:** Y1 = 750 jt · Y2 = 1,425 M · Y3 = 2,1 M · **kumulatif 4.275.000.000 IDR** ·
**2,85%** dari anggaran 3 tahun · severity **Manageable** (skor 80). Tunjukkan trajectory chart naik.

> Kenapa anggaran 50 M? Supaya dampak tetap "Manageable" (<10% anggaran tahunan). Kalau
> anggaran terlalu kecil, severity jadi "Prohibitive" (skor 0) dan lampu jatuh ke KUNING.

---

## 4. Tab EtD

1. **Tambah Referensi:** `PARADIGM-HF`, penulis `McMurray et al.`, sumber `NEJM 2014`.
2. Isi domain (minimal 3, boleh lebih) — **SEMUA dengan nilai sama:**

| Field per domain | Pilih |
|---|---|
| Judgement | **Mungkin ya** (= 75) |
| Certainty | **Sedang** (= 75) |

> 🔑 Kunci anti-gagal: selama setiap domain yang kamu isi bernilai 75/75, evidence
> strength = **75 persis** — tidak peduli berapa domain yang diisi atau bagaimana slider
> bobot digeser nanti. Ini yang menjaga lampu tetap HIJAU.

---

## 5. Tab Rekomendasi — Tambah Kriteria CBA

| Field | Isi |
|---|---|
| Nama kriteria | `Diresepkan oleh kardiolog` |
| Operator | `equals` / sama dengan |
| Nilai | `kardiolog` |
| **Terpenuhi (Satisfied)** | ✅ **WAJIB dicentang** |

> ⚠️ Kalau kotak **Terpenuhi** tidak dicentang → skor CBA jadi 0 → komposit turun ke 76
> → lampu **KUNING**, bukan HIJAU. Jangan lupa centang.

---

## 6. Anggota KFT (opsional, untuk tunjukkan multi-user)  *(login `kft1@test.local`)*

- Tab **EtD** → boleh vote 2–3 domain **(tetap Mungkin ya + Sedang)**.
- Tab **Rekomendasi** → kartu **Bobot Domain** → geser slider → **Simpan Bobot Saya**.
  Aman digeser: karena semua domain 75, rata-rata tertimbang tetap 75.

---

## 7. Hitung Rekomendasi  *(kembali login `hta@test.local`)*

Tab **Rekomendasi** → **Hitung Rekomendasi**.

**Hasil:** kartu besar **HIJAU**, **komposit 86,00 / 100**, justifikasi otomatis
menyebut bukti 75, CEA 100, anggaran 80, CBA 100.

Lalu tab **Ringkasan** → **Tindakan → Ajukan untuk Tinjauan** (status → `in_review`).

---

## 8. Sign-Off  *(login `ketua@test.local`)*

Buka `HF_ARNI_ACEI_DEMO` → tab **Sign-Off** → **Setujui dengan Sign-Off**.

**Tunjukkan jalur gagal dulu (nilai jual keamanan sistem):**

| Aksi | Hasil yang diharapkan |
|---|---|
| Submit tanpa centang pernyataan | Error **400** — pernyataan wajib |
| Centang + password **salah** | Error **401** — verifikasi identitas gagal |
| Centang + password **`TestPass123!`** | ✅ Sukses → status `approved` |

Lalu: **Tindakan → Kunci Keputusan** → status `locked` → tab **Versi** memunculkan **v1.0** otomatis.

---

## 9. Brief + Arsip

1. Tab **Brief** → **Terbitkan Ringkasan** → tunggu ± 15 dtk → unduh **PDF**.
   *(Di localhost pakai MS Word; di Railway pakai LibreOffice — dua-duanya jalan.)*
2. Tab **Ringkasan** → **Tindakan → Arsipkan** → status `archived` + manifest SHA-256 dibuat.

> Penutup: *"Dalam beberapa menit: dari kasus kosong → dihitung → dinilai komite →
> ditandatangani Ketua → dikunci → diterbitkan → diarsipkan permanen dengan hash."*

---

## Kalau lampu TIDAK hijau — diagnosa cepat

| Gejala | Penyebab | Perbaikan |
|---|---|---|
| Lampu KUNING, komposit 76 | Kotak CBA "Terpenuhi" belum dicentang | Edit kriteria → centang → hitung ulang |
| Lampu KUNING, budget skor 0 | Anggaran BIA terlalu kecil (severity Prohibitive) | Pastikan anggaran = `50000000000` |
| Evidence bukan 75 | Ada domain diisi ≠ Mungkin ya/Sedang | Samakan semua domain ke 75/75 |
| ICER negatif / "dominated" | Efikasi obat < komparator, atau biaya kebalik | obat 10jt/2.5 QALY, komparator 5jt/2.0 QALY |
