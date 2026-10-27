# Persyaratan Kelengkapan per Tahap

Menjawab Round 4 item 4: *"Mohon buat daftar persyaratan untuk submit, hitung
rekomendasi, sign-off, lock, penerbitan brief final, dan archive. Persyaratannya
disesuaikan dengan fungsi masing-masing tahap."*

Seluruh aturan di bawah ditegakkan di **backend**. Tombol yang dinonaktifkan di
layar hanya cerminan; permintaan yang dikirim langsung ke API tetap ditolak.
Bukti pengujiannya ada di `backend/apps/cases/tests/test_stage_gates_api.py` --
setiap pengujian memakai role yang **berwenang**, sehingga yang menghentikannya
murni kelengkapan dossier, bukan perizinan.

## Ringkasan

| Tahap | Role | Persyaratan | Kode penolakan |
|---|---|---|---|
| Submit (draft to in_review) | HTA Analyst, Sekretaris KFT | PICO lengkap | 422 |
| Hitung rekomendasi | HTA Analyst, Sekretaris KFT | EtD 9/9, CEA, BIA | 422 |
| Sign-off Ketua | Ketua KFT | PICO, CEA, BIA, PSA pada input terbaru, EtD 9/9, rekomendasi yang masih sesuai input, Keputusan Final KFT atas rekomendasi itu | 422 |
| Lock keputusan | Ketua KFT | seluruh syarat sign-off + tanda tangan persetujuan atas rekomendasi dan Keputusan Final KFT yang berlaku (setelah revisi: tanda tangan baru) | 422 |
| Penerbitan brief final | Ketua KFT, HTA Analyst | status approved/locked + rekomendasi + PICO, CEA, BIA, EtD 9/9 | 400 / 422 |
| Archive | Ketua KFT | PICO, CEA, BIA, EtD 9/9, rekomendasi, tanda tangan + snapshot keputusan + alasan | 422 |

## Mengapa berbeda per tahap

**Submit hanya menuntut PICO.** Analisis CEA/BIA/EtD justru dihasilkan *selama*
tinjauan; mewajibkannya di tahap submit akan membuat tahap ini mustahil dicapai.
Yang wajib ada hanyalah pertanyaan keputusan yang nyata -- keempat bagian P, I, C
dan O harus terisi, bukan sekadar satu baris judul.

**Sign-off menuntut dossier penuh.** Inilah titik ketika keputusan klinis diambil.

**Sign-off dan lock menuntut PSA dan rekomendasi yang masih berlaku (Round 5 item 1).**
*"Kalau PSA belum dikerjakan atau sudah tidak sesuai input terbaru -> belum boleh
sign-off/lock."* Setiap hasil PSA mencatat input yang dipakainya; PSA dianggap
berlaku hanya bila input itu sama dengan input sekarang. PSA yang dijalankan sebelum
13 Oktober 2026 belum mencatat inputnya, sehingga harus dijalankan ulang sekali.
Rekomendasi yang dihitung sebelum CEA, BIA, EtD, bobot, atau CBA terakhir berubah juga
menahan sign-off sampai dihitung ulang.

**Sign-off dan lock menuntut Keputusan Final KFT (Round 5 item 3).** Warna dan skor
sistem tetap ditampilkan, tetapi keputusan diambil manusia: Anggota KFT atau Ketua KFT
memilih salah satu dari lima jenis keputusan (Adopt, Adopt with criteria-based access,
Defer pending additional evidence, Do not adopt, Reassess after price negotiation) dan
wajib menulis alasannya. Setiap keputusan disimpan sebagai riwayat dan mencatat
rekomendasi yang menjadi dasarnya; bila rekomendasi dihitung ulang, keputusan harus
dikonfirmasi ulang. Tanda tangan Ketua mencatat keputusan mana yang ditandatangani.

**Brief dan archive tidak menuntut PSA maupun Keputusan Final KFT.** Keduanya hanya berlaku untuk kasus yang
sudah disetujui atau dikunci, yang telah lolos aturan yang berlaku saat ditandatangani.
Kasus yang dikunci sebelum Round 5 tidak dapat menjalankan ulang PSA, dan pemeriksaan
integritas yang berjalan pada setiap deploy tidak boleh mengubahnya menjadi kasus
"perlu perbaikan".

**Lock menambahkan tanda tangan tercatat.** Baris `Approval` hanya ditulis oleh
endpoint sign-off. Sebelum perbaikan ini, transisi `approve` mentah tidak menulis
baris tersebut, sehingga kasus dapat mencapai `locked` **tanpa tanda tangan sama
sekali** -- persis skenario yang dikhawatirkan pada laporan Ketua KFT.

**Archive menambahkan snapshot.** Pengarsipan menjadikan kasus sebagai rekam
keputusan resmi rumah sakit, sehingga snapshot tak-berubah harus sudah ada.
Pengarsipan juga mewajibkan alasan tertulis.

## Aturan data kosong

*"Data kosong tidak boleh otomatis dianggap nol atau mendapat skor menguntungkan."*

| Situasi | Perilaku |
|---|---|
| EtD, CEA, atau BIA belum ada | Rekomendasi berstatus `incomplete`; **tidak ada** lampu lalu lintas, bukan MERAH dan bukan angka |
| EtD baru sebagian (mis. 4/9) | Ditolak, dengan rasio sebenarnya disebutkan; skor parsial diberi label "Sementara" dan tidak boleh masuk rekomendasi |
| CBA belum didefinisikan | Dianggap "belum dinilai", dikeluarkan dari komposit, bobot dinormalisasi ulang -- bukan otomatis 100 |
| BIA tanpa anggaran baseline | `budget_score` bernilai null (`not_assessed`), bukan angka |

## Bentuk pesan penolakan

Setiap penolakan menyebutkan komponen yang kurang, bukan hanya "tidak lengkap":

```json
{
  "detail": "Dossier belum lengkap: Analisis ekonomi deterministik (CEA); Penilaian EtD lengkap (9 domain)",
  "missing": [
    "Analisis ekonomi deterministik (CEA)",
    "Penilaian EtD lengkap (9 domain)"
  ]
}
```

Untuk archive, kode penolakannya `integrity_check_failed` dan daftar `missing`
mencakup snapshot serta tanda tangan.

## Rujukan kode

| Bagian | Berkas |
|---|---|
| Daftar syarat per tahap | `backend/apps/cases/completeness.py` (`STAGE_REQUIREMENTS`) |
| Pemeriksaan integritas arsip | `backend/apps/cases/integrity.py` |
| Penegakan pada transisi | `backend/apps/cases/state_machine.py` (`enforce_completeness`) |
| Penegakan pada sign-off | `backend/apps/approval/views.py` |
| Penegakan pada brief | `backend/apps/policy_brief/views.py` |
| Bukti penolakan langsung | `backend/apps/cases/tests/test_stage_gates_api.py` |
