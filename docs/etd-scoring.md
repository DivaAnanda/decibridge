# Rumus Skor EtD dan Rekomendasi

Dokumen ini menjawab permintaan Round 4 item 6: *"Mohon jelaskan rumus skor EtD,
pengaruh certainty, bobot domain, serta bobot gabungan rekomendasi."*

Isinya menggambarkan perilaku sistem **apa adanya**, termasuk dua hal yang perlu
keputusan Pak Anom (bagian "Catatan terbuka" di bawah).

---

## 1. Skala penilaian per domain

Setiap anggota KFT menilai satu domain dengan skala GRADE 5 titik. Skala ini
**berarah**: makin tinggi angkanya, makin mendukung adopsi.

| Pilihan | Nilai |
|---|---|
| Tidak | 0 |
| Mungkin tidak | 25 |
| Tidak pasti | 50 |
| Mungkin ya | 75 |
| Ya | 100 |

Konsekuensinya, **setiap pertanyaan domain harus dirumuskan sehingga "Ya" berarti
menguntungkan adopsi.** Tiga pertanyaan sebelumnya melanggar aturan ini dan sudah
diperbaiki (migrasi `etd.0003_fix_domain_prompt_polarity`) — lihat bagian 6.

## 2. Pengaruh certainty

Certainty dinilai terpisah dari judgement, lalu dipetakan ke angka:

| Certainty | Nilai |
|---|---|
| Tinggi | 100 |
| Sedang | 75 |
| Rendah | 50 |
| Sangat rendah | 25 |

## 3. Skor per domain

Untuk satu domain dengan *n* penilaian anggota:

```
mean_judgement   = rata-rata judgement seluruh anggota
dominant_certainty = modus certainty (bila seri, dipilih yang LEBIH RENDAH)
certainty_score  = peta certainty di atas

combined_domain_score = (mean_judgement + certainty_score) / 2
```

Jika belum ada certainty sama sekali, `combined_domain_score = mean_judgement`.

Pemilihan modus yang konservatif saat seri disengaja: bila komite terbelah antara
"Tinggi" dan "Rendah", sistem memakai "Rendah".

## 4. Skor kekuatan bukti (agregat 9 domain)

```
evidence_strength_score = rata-rata combined_domain_score dari domain yang sudah dinilai
```

**Sejak Round 3, skor ini hanya boleh dipakai bila 9 dari 9 domain terisi.** Bila
baru sebagian, engine menolak menghitung rekomendasi dan antarmuka menandainya
"Skor sementara — x/9 domain". Sebelumnya, 4 dari 9 domain menghasilkan angka
87,50 yang tampak final.

## 5. Skor komposit dan lampu lalu lintas

```
composite = 0,40 x evidence + 0,30 x CE + 0,20 x budget + 0,10 x CBA
```

| Komponen | Bobot | Sumber |
|---|---|---|
| Bukti EtD | 40% | bagian 4 di atas |
| Cost-effectiveness | 30% | `econ/scoring.py` dari hasil deterministik |
| Dampak anggaran | 20% | `budget_score` dari hasil BIA |
| CBA | 10% | 100 bila semua kriteria terpenuhi, 50 bila sebagian, 0 bila tidak ada yang terpenuhi |

**Komponen yang belum tersedia tidak pernah diberi angka pengganti.** Bila
evidence, CE, atau budget belum ada, rekomendasi berstatus `incomplete` dan tidak
menghasilkan lampu sama sekali. Bila CBA belum didefinisikan, CBA dikeluarkan dari
rumus dan bobotnya dinormalisasi ulang atas tiga komponen sisanya:

```
composite = (0,40 x evidence + 0,30 x CE + 0,20 x budget) / 0,90
```

Lampu lalu lintas:

| Hasil | Syarat |
|---|---|
| HIJAU | composite >= 75 **dan** CBA terpenuhi seluruhnya atau tidak dinilai |
| KUNING | composite >= 60, **atau** CBA terpenuhi sebagian |
| MERAH | selain itu |

## 6. Perbaikan arah pertanyaan (Round 4 item 6)

Karena skala bersifat berarah, tiga pertanyaan tidak konsisten dengan skornya:

| Domain | Pertanyaan lama | Masalah |
|---|---|---|
| Nilai & Preferensi | "Apakah **ada ketidakpastian penting** tentang bagaimana pasien menilai outcome utama?" | "Ya" = ada ketidakpastian = alasan **menentang** adopsi, tetapi tercatat 100 (dukungan maksimum). Terbalik. |
| Ekuitas | "Apakah intervensi ini akan **meningkatkan, mempertahankan, atau menurunkan** ekuitas?" | Pertanyaan tiga arah dijawab pada skala ya/tidak. Jawaban apa pun memberi skor yang tidak bermakna. |
| Masalah | "**Seberapa penting** masalah klinis ini...?" | Pertanyaan besaran dijawab pada skala ya/tidak. |

Pertanyaan baru:

| Domain | Pertanyaan baru |
|---|---|
| Masalah | "Apakah masalah klinis yang diatasi intervensi ini merupakan prioritas di rumah sakit Anda?" |
| Nilai & Preferensi | "Apakah pasien menilai outcome utama intervensi ini secara konsisten, tanpa ketidakpastian penting?" |
| Ekuitas | "Apakah intervensi ini akan meningkatkan - atau setidaknya tidak menurunkan - ekuitas kesehatan di rumah sakit Anda?" |

**Penilaian lama tidak diubah.** Penilaian tersebut dibuat terhadap kalimat lama;
membalik angkanya secara diam-diam akan mengubah apa yang dinyatakan anggota KFT.
Penilaian ulang adalah keputusan manusia, bukan migrasi.

## 7. Catatan terbuka — perlu keputusan

### 7.1 Bobot domain belum berpengaruh

Anggota KFT dapat menetapkan bobot 0-100 untuk setiap domain, bobot itu
diagregasi (mean atau median) dan ditampilkan di tab Rekomendasi. **Namun bobot
tersebut tidak pernah dipakai dalam perhitungan.** `evidence_strength_score`
adalah rata-rata **tanpa bobot**; `aggregate_per_domain` hanya dipanggil oleh
endpoint ringkasan bobot, tidak oleh mesin rekomendasi.

Artinya saat ini sistem meminta masukan yang tidak berpengaruh pada hasil.

Tiga pilihan:

1. **Terapkan bobotnya** — `evidence = Σ(bobot_ternormalisasi_d x combined_d)`.
   Ini yang paling sesuai dengan harapan pengguna, tetapi **mengubah angka** pada
   kasus yang sudah dinilai.
2. **Tandai sebagai advisory** — bobot tetap dikumpulkan untuk bahan diskusi rapat,
   dengan label eksplisit bahwa bobot tidak masuk rumus.
3. **Hapus fiturnya** sampai aturannya disepakati.

Kami menunggu arahan karena Pak Anom menyatakan *"Rumus dan interpretasi HTA akan
saya tinjau bersama"*, dan opsi 1 mengubah skor yang sedang divalidasi.

### 7.2 Pembobotan judgement vs certainty

`combined_domain_score` memberi bobot **sama besar** (50/50) antara judgement dan
certainty. GRADE tidak menetapkan angka untuk ini; 50/50 adalah pilihan kami.
Mohon dikonfirmasi apakah proporsi ini sesuai.

---

## Rujukan kode

| Bagian | Berkas |
|---|---|
| Skala judgement + certainty | `backend/apps/etd/models.py` |
| Agregasi per domain dan keseluruhan | `backend/apps/etd/aggregation.py` |
| Agregasi bobot domain (belum dipakai) | `backend/apps/recommendation/aggregation.py` |
| Rumus komposit + lampu | `backend/apps/recommendation/engine.py` |
| Skor CE dari hasil ekonomi | `backend/apps/econ/scoring.py` |
