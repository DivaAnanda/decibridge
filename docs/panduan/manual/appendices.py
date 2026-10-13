"""Appendices: results against the key, differences from the package, common problems."""

from __future__ import annotations

from .data import CASE_ID, INITIAL, KEY, exact, num, rp
from .document import Manual


def appendix_key(m: Manual) -> None:
    det = INITIAL["deterministic"]
    m.chapter("Lampiran A - Kunci hasil")
    m.text(
        "Tabel berikut membandingkan hasil dashboard pada pengerjaan ini dengan 11_INSTRUCTOR_KEY. "
        "Hasil deterministik dan BIA harus sama persis; hasil BIA dan PSA ada pada Bab 4 dan Bab 5, "
        "dan hasil revisi pada Bab 10."
    )
    fields = [
        ("Total cost - intervensi", "total_cost_intervention", 0, True),
        ("Total cost - komparator", "total_cost_comparator", 0, True),
        ("Incremental cost", "incremental_cost", 0, True),
        ("QALY - intervensi", "total_qaly_intervention", 3, False),
        ("QALY - komparator", "total_qaly_comparator", 3, False),
        ("Incremental QALY", "incremental_qaly", 3, False),
        ("ICER per QALY", "icer", 2, True),
        ("NMB - intervensi", "nmb_intervention", 0, True),
        ("NMB - komparator", "nmb_comparator", 0, True),
        ("INB", "inb", 0, True),
    ]
    rows = []
    for label, key, decimals, money in fields:
        show = (lambda v: rp(v, decimals)) if money else (lambda v: num(v, decimals))
        tolerance = "0.01" if money else "0.0000001"
        rows.append([label, show(det[key]), show(KEY[key]), exact(label, det[key], KEY[key], tolerance)])
    m.table(
        ["Keluaran deterministik", "Dashboard", "Kunci instruktur", "Status"],
        rows,
        [5.6, 4.2, 4.2, 3.0],
        caption="Hasil deterministik dibanding kunci",
    )
    m.callout(
        "Kesimpulan belajar pada paket",
        [
            "Hasil deterministik tampak cost-effective pada WTP demo karena ICER sekitar Rp225,45 "
            "juta per QALY dan INB positif. Namun PSA hanya sekitar 56% cost-effective dan BIA naik "
            "sampai sekitar Rp1,488 miliar per tahun. Keputusan latihan yang koheren adalah adopsi "
            "dengan akses berbasis kriteria, bukan adopsi tanpa batas.",
        ],
        kind="check",
    )


def appendix_differences(m: Manual) -> None:
    m.chapter("Lampiran B - Perbedaan paket latihan dan dashboard")
    m.text(
        "Paket latihan ditulis untuk dashboard secara umum dan beberapa kali meminta pengguna "
        "memilih opsi terdekat. Tabel berikut mencatat setiap tempat build ini berbeda dari "
        "langkah paket, dan cara panduan ini menanganinya."
    )
    m.table(
        ["Langkah", "Pada paket", "Pada dashboard (build ini)"],
        [
            ["1", f"Case ID {CASE_ID}",
             "Di situs bersama ID itu sudah dipakai kasus rujukan. Gunakan ID sendiri."],
            ["9", "Time horizon diisi di Ringkasan", "Diisi di Analisis Ekonomi sebagai Horizon CEA."],
            ["10", "Outcome diisi di Ringkasan", "Diisi pada Outcome (O) di langkah PICO."],
            ["11-12", "Biaya obat per bulan", "Isian per pasien per tahun; nilai paket dikalikan 12."],
            ["25-33", "Input BIA di menu BIA",
             "Diisi di Analisis Ekonomi; tab BIA hanya menghitung dan menampilkan."],
            ["32", "Market share baseline ARNI = 0",
             "Tidak diisi. Market share di dashboard adalah pengali jumlah pasien; nilai 0 membuat BIA nol."],
            ["37-39", "Distribusi per kelompok parameter",
             "Diatur per parameter pada tab PSA. SE biaya diketik 10%; utility memakai SD."],
            ["41-49", "Judgement dengan istilah tiap domain",
             "Skala lima pilihan (Tidak sampai Ya) ditambah kepastian GRADE per domain. Padanannya pada Bab 6."],
            ["50", "Decision type dipilih pengguna",
             "Tidak ada isian. Sistem menghitung warna rekomendasi; KUNING sepadan dengan adopsi bersyarat."],
            ["51", "Target population diisi di Rekomendasi",
             "Tidak ada isian. Tercatat di Ringkasan dan pada kriteria akses pertama."],
            ["52", "Access criteria", "Diisi sebagai Kriteria Akses (CBA)."],
            ["53", "Rationale terintegrasi diisi pengguna",
             "Tidak ada isian. Sistem menulis Justifikasi; alasan per domain ada pada pertimbangan EtD."],
            ["54", "Checklist delapan butir, termasuk PSA",
             "Kelengkapan Dossier tidak memuat PSA; diperiksa sendiri di tab PSA."],
            ["55", "Approver memilih keputusan",
             "Ketua KFT menyetujui, meminta revisi, atau menolak rekomendasi yang dihitung sistem."],
            ["56", "Brief memuat ringkasan PSA dan pertanyaan keputusan",
             "Brief memuat CEA, BIA, EtD, CBA, referensi dan tanda tangan; tanpa ringkasan PSA."],
            ["57", "Versi awal disimpan sebagai v0.1", "v0.1.0 dibuat otomatis ketika kasus dibuat."],
            ["58-59", "Buat versi baru v0.2 dengan alasan",
             "Revisi dikerjakan sebelum penguncian melalui Minta Revisi dengan alasan. Tidak ada baris "
             "v0.2; penguncian menghasilkan v1.0. Kasus terkunci tidak dapat dibuka kembali."],
        ],
        [1.6, 5.4, 10.0],
        caption="Perbedaan langkah paket dan dashboard",
    )


def appendix_problems(m: Manual) -> None:
    m.chapter("Lampiran C - Masalah yang sering terjadi")
    m.table(
        ["Yang terlihat", "Penyebab", "Yang dilakukan"],
        [
            ["Pesan **Parameter belum tersimpan** dan ada baris bertanda merah",
             "Proporsi diketik sebagai persen, misalnya 30 untuk 30%",
             "Ketik 0.30. Tidak ada baris yang tersimpan sampai semua baris benar."],
            ["**Belum dapat dihitung - input wajib yang kurang**",
             "Parameter belum disimpan, atau ada parameter wajib yang belum ada",
             "Simpan parameter, lalu lengkapi yang disebut pada daftar."],
            ["Hasil BIA nol atau pasien nol", "Market share diisi 0", "Hapus baris market share, lalu hitung ulang."],
            ["Pilihan **Tahun 1** tidak ada saat menambah parameter",
             "Horizon BIA belum diisi",
             "Isi Horizon BIA 3 pada Parameter Model Ekonomi."],
            ["Tombol **Hitung PSA** tidak aktif", "Ada perubahan distribusi yang belum disimpan",
             "Klik Simpan Distribusi lebih dulu."],
            ["PSA **Belum dapat dihitung** dengan keterangan distribusi",
             "Sebuah distribusi dipilih tetapi parameternya belum lengkap",
             "Lengkapi baris yang disebut, atau kembalikan ke Tetap."],
            ["Peringatan **Hasil PSA ini tidak lagi sesuai input**",
             "Parameter atau distribusi berubah setelah PSA dijalankan", "Jalankan ulang PSA."],
            ["Peringatan **Rekomendasi ini tidak lagi sesuai input**",
             "Analisis ekonomi, BIA, EtD atau kriteria berubah setelah rekomendasi dihitung",
             "Klik Hitung Rekomendasi sebelum mengajukan atau menandatangani."],
            ["Rekomendasi **Belum dapat dihitung**",
             "Belum semua domain EtD terisi, atau analisis ekonomi atau BIA belum dihitung",
             "Lengkapi komponen yang disebut pada daftar."],
            ["**Dossier belum lengkap** saat mengajukan atau menyetujui",
             "Ada butir wajib pada Kelengkapan Dossier yang belum terpenuhi",
             "Buka tab Sign-Off dan lengkapi butir bertanda silang."],
            ["Tombol **Terbitkan Ringkasan** tidak aktif",
             "Kasus belum Disetujui, atau peran tidak berwenang",
             "Minta sign-off Ketua KFT; terbitkan sebagai Analis HTA, Ketua KFT atau Admin IT."],
            ["Tidak ada isian yang dapat diubah", "Kasus sudah Terkunci",
             "Kasus terkunci hanya dapat dibaca."],
        ],
        [5.4, 5.6, 6.0],
        caption="Masalah umum dan penyelesaiannya",
    )
