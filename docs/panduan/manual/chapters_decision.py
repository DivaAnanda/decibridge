"""The five decision menus: EtD, Rekomendasi, Sign-Off, Brief, Versi."""

from __future__ import annotations

from decimal import Decimal

from .data import INITIAL, INPUTS, KEY, MISMATCHES, REVISED, exact, num, pct, rp
from .document import Manual

# Package sheet 06: the judgement vocabulary the package uses for each domain,
# beside which the dashboard option chosen for it is printed.
PACKAGE_JUDGEMENTS = [
    ("Problem priority", "High"),
    ("Desirable effects", "Favorable"),
    ("Undesirable effects", "Acceptable with monitoring"),
    ("Certainty of evidence", "Moderate"),
    ("Values/preferences", "Probably important"),
    ("Resource use", "Moderate concern"),
    ("Equity", "Neutral / potential concern"),
    ("Feasibility", "Feasible with criteria"),
    ("Acceptability", "Mixed to favorable"),
]

TRAFFIC_LABEL = {
    "green": "HIJAU - Adopsi Tanpa Syarat",
    "yellow": "KUNING - Adopsi Bersyarat (CBA)",
    "red": "MERAH - Tidak Direkomendasikan",
}


def etd(m: Manual) -> None:
    m.chapter("6. Menu 5 - EtD")
    m.role_line("Analis HTA (referensi), lalu Anggota KFT (penilaian)", "41-49")
    m.text(
        "Evidence-to-Decision (EtD) menimbang bukti pada sembilan domain GRADE. Analis HTA "
        "menyiapkan daftar referensi; Anggota KFT memberi penilaian untuk tiap domain. Analis HTA "
        "dapat melihat penilaian tetapi tidak dapat mengisinya."
    )

    m.section("6.1 Referensi (Analis HTA)")
    m.steps([
        "Buka tab **EtD (9 domain)**. Pada kartu **Referensi Bukti**, klik **Tambah Referensi**.",
        "Pilih **Jenis**, isi **Sitasi (format bebas)**, **Tahun** dan **Ringkasan bukti**, lalu "
        "klik **Tambah**.",
        "Ulangi untuk keenam sumber pada sheet 12_SOURCE_REGISTER paket.",
    ])
    m.table(
        ["Sitasi", "Ringkasan bukti"],
        [[citation, summary] for citation, summary in INPUTS["references"]],
        [6.0, 11.0],
        caption="Enam referensi kasus latihan (jenis: Protokol institusi, tahun 2026)",
    )
    m.figure("17-etd-referensi-form", "Formulir Tambah Referensi.", max_height_cm=11.0)
    m.figure("18-etd-referensi", "Daftar referensi setelah keenam sumber ditambahkan.",
             max_height_cm=6.5)

    m.section("6.2 Penilaian sembilan domain (Anggota KFT)")
    m.text(
        "Keluar dari akun Analis HTA dan masuk sebagai Anggota KFT. Tiap domain berupa satu "
        "pertanyaan yang dijawab pada skala lima pilihan, dari **Tidak** sampai **Ya**, ditambah "
        "**Kepastian bukti (GRADE)**, referensi pendukung, dan pertimbangan tertulis. Penilaian "
        "baru dapat disimpan bila ada minimal satu referensi atau satu pertimbangan."
    )
    m.text(
        "Paket memberi judgement dengan istilah yang berbeda untuk tiap domain dan meminta "
        "pengguna memilih opsi dashboard yang paling dekat. Tabel berikut adalah padanan yang "
        "dipakai dalam panduan ini. Kepastian diisi **Sedang** pada semua domain, mengikuti "
        "satu-satunya penilaian kepastian pada paket (Certainty of evidence: Moderate)."
    )
    rows = []
    for (package_domain, package_judgement), (tab, choice, refs, narrative) in zip(
        PACKAGE_JUDGEMENTS, INPUTS["appraisals"]
    ):
        rows.append([
            tab, package_judgement, f"**{choice}**", ", ".join(refs) or "-", narrative,
        ])
    m.table(
        ["Domain di dashboard", "Judgement paket", "Pilihan", "Referensi", "Pertimbangan (narasi)"],
        rows,
        [3.8, 2.7, 2.3, 2.6, 5.6],
        caption="Padanan judgement paket (sheet 06_ETD) ke pilihan dashboard",
    )
    m.callout(
        "Padanan ini adalah pertimbangan, bukan kunci",
        [
            "Paket tidak menentukan pilihan mana pada skala lima pilihan yang setara dengan "
            "\"Favorable\" atau \"Moderate concern\". Kelompok yang menimbang berbeda boleh memilih "
            "berbeda, asal alasannya ditulis pada **Pertimbangan**. Pilihan yang berbeda mengubah "
            "Skor Kekuatan Bukti dan dapat mengubah rekomendasi.",
        ],
    )
    m.steps([
        "Buka tab **EtD (9 domain)** dan pilih domain pada daftar di sisi kiri.",
        "Pilih **Penilaian Anda**, lalu **Kepastian bukti (GRADE)**.",
        "Pilih **Referensi pendukung** bila ada, dan tulis **Pertimbangan (narasi)**.",
        "Klik **Simpan Penilaian Saya**. Angka kecil di samping nama domain menunjukkan jumlah "
        "suara yang sudah masuk.",
        "Ulangi sampai kesembilan domain terisi.",
    ])
    m.figure("19-etd-domain-1", "Penilaian domain 1, sebelum disimpan.", max_height_cm=9.0)
    m.figure("20-etd-domain-6", "Penilaian domain 6 (Penggunaan Sumber Daya).", max_height_cm=9.0)
    m.figure("21-etd-ringkasan", "Ringkasan EtD setelah kesembilan domain terisi.", max_height_cm=3.4)
    m.callout(
        "Cara skor dihitung",
        [
            "Skor satu domain adalah rata-rata nilai penilaian (Tidak 0, Mungkin tidak 25, Tidak "
            "pasti 50, Mungkin ya 75, Ya 100) dan nilai kepastian (Sangat rendah 25, Rendah 50, "
            "Sedang 75, Tinggi 100). **Skor Kekuatan Bukti** adalah rata-rata kesembilan domain.",
            f"Dengan penilaian pada Tabel di atas, skornya "
            f"{num(INITIAL['recommendation']['evidence_strength_score'], 2)} dari 100.",
            "Selama belum semua domain terisi, skor diberi tanda **Sementara** dan rekomendasi "
            "belum dapat dihitung.",
        ],
        kind="check",
    )


def rekomendasi(m: Manual) -> None:
    result = INITIAL["recommendation"]
    # With every criterion ticked the CBA component (weight 10%) scores 100
    # instead of 0; green needs a composite of at least 75.
    if_all_met = Decimal(result["composite_score"]) + Decimal("10")
    if result["cba_satisfied_count"] != 0 or if_all_met < Decimal("75"):
        MISMATCHES.append("Bab 7: penjelasan 'bila keempatnya dicentang' tidak lagi berlaku")
    m.chapter("7. Menu 6 - Rekomendasi")
    m.role_line("Sekretaris KFT (kriteria akses), lalu Analis HTA (menghitung)", "50-53")
    m.text(
        "Menu ini menggabungkan bukti EtD, cost-effectiveness, dampak anggaran dan kriteria akses "
        "menjadi satu rekomendasi berwarna. Rekomendasi dihitung oleh sistem; yang diisi pengguna "
        "adalah kriteria aksesnya."
    )

    m.section("7.1 Kriteria akses (langkah 52)")
    m.text(
        "Kriteria akses adalah syarat penggunaan obat bila disetujui. Sekretaris KFT, Analis HTA "
        "dan Ketua KFT dapat mengisinya."
    )
    m.steps([
        "Buka tab **Rekomendasi**. Pada kartu **Kriteria Akses (CBA)**, klik **Tambah Kriteria**.",
        "Isi **Nama kriteria** dan **Deskripsi**. Isian lain boleh dibiarkan.",
        "Biarkan kotak **Kriteria terpenuhi pada konteks RS saat ini** tidak dicentang, lalu klik "
        "**Tambah**.",
        "Ulangi untuk keempat kriteria pada sheet 07_REKOMENDASI paket.",
    ])
    m.table(
        ["Nama kriteria", "Deskripsi"],
        [[name, description] for name, description in INPUTS["criteria"]],
        [6.0, 11.0],
        caption="Empat kriteria akses kasus latihan",
    )
    m.figure("24-rekomendasi-kriteria-form", "Formulir Tambah Kriteria CBA.", max_height_cm=10.5)
    m.figure("25-rekomendasi-kriteria", "Empat kriteria, belum ada yang dicentang terpenuhi.",
             max_height_cm=6.0)
    m.callout(
        "Mengapa kotak \"terpenuhi\" tidak dicentang",
        [
            "Sistem membaca kriteria yang belum terpenuhi sebagai syarat yang masih harus dipenuhi, "
            "sehingga adopsinya bersyarat. Pada paket, pemantauan dan alur kerja masih harus "
            "ditetapkan (sheet 06_ETD, kolom Action needed: \"Specify monitoring\", \"Define "
            "workflow\"), jadi keempat kriteria ini adalah syarat adopsi, bukan hal yang sudah "
            "berjalan.",
            "Centang hanya syarat yang memang sudah berjalan di rumah sakit. Bila keempatnya "
            "dicentang pada kasus ini, sistem menganggap tidak ada syarat tersisa: skor komposit "
            f"menjadi {num(if_all_met, 2)} dan hasilnya HIJAU - Adopsi Tanpa Syarat.",
        ],
        kind="warn",
    )

    m.section("7.2 Menghitung rekomendasi (langkah 50)")
    m.steps([
        "Masuk sebagai Analis HTA dan buka tab **Rekomendasi**.",
        "Klik **Hitung Rekomendasi**.",
        "Kartu **Rekomendasi Akhir** menampilkan warna, skor komposit, keempat komponen, dan "
        "kalimat **Justifikasi**.",
    ])
    m.figure("26-rekomendasi-hasil", "Rekomendasi kasus latihan.", max_height_cm=8.0)
    m.table(
        ["Komponen", "Bobot", "Skor", "Berasal dari"],
        [
            ["Bukti EtD", "40%", num(result["evidence_strength_score"], 2), "Skor Kekuatan Bukti (Bab 6)"],
            ["Cost-effectiveness", "30%", num(result["ce_score"], 2), "Hasil deterministik (Bab 3)"],
            ["Dampak anggaran", "20%", num(result["budget_score"], 2), "Skor anggaran BIA (Bab 4)"],
            ["Kriteria akses (CBA)", "10%", num(result["cba_score"], 2),
             f"{result['cba_satisfied_count']} dari {result['cba_criteria_count']} kriteria terpenuhi"],
            ["**Skor komposit**", "", f"**{num(result['composite_score'], 2)}**",
             f"**{TRAFFIC_LABEL[result['traffic_light']]}**"],
        ],
        [4.6, 1.8, 2.2, 8.4],
        caption="Komponen rekomendasi",
    )
    m.text(
        "Hasil **KUNING - Adopsi Bersyarat (CBA)** sepadan dengan keputusan latihan pada paket, "
        "\"Adopt with criteria-based access\": manfaat dan cost-effectiveness mendukung, tetapi "
        "dampak anggaran bermakna dan penggunaannya dibatasi kriteria."
    )
    m.callout(
        "Yang belum ada pada build ini",
        [
            "**Decision type, target population dan rationale** (langkah 50, 51 dan 53) tidak "
            "memiliki isian tersendiri. Jenis keputusan adalah hasil hitung sistem. Target "
            "populasi tercatat pada Ringkasan dan pada kriteria pertama. Alasan per domain ada "
            "pada pertimbangan EtD, dan sistem menulis kalimat Justifikasi sendiri.",
            "**Hasil PSA tidak masuk ke skor komposit.** Skor cost-effectiveness hanya memakai "
            "hasil deterministik, sehingga ketidakpastian sekitar 56% harus dibahas KFT sendiri "
            "ketika menimbang rekomendasi ini.",
            "**Bobot Domain EtD** pada tab ini boleh diisi Anggota KFT, tetapi sesuai keterangan "
            "di layar hanya menjadi informasi dan tidak mengubah skor.",
        ],
    )


def signoff(m: Manual) -> None:
    m.chapter("8. Menu 7 - Sign-Off")
    m.role_line("Analis HTA (mengajukan), lalu Ketua KFT (menandatangani)", "54-55")
    m.text(
        "Sign-off adalah persetujuan resmi Ketua KFT atas rekomendasi. Sebelum itu, Analis HTA "
        "memeriksa kelengkapan dossier dan mengajukan kasus untuk ditinjau."
    )

    m.section("8.1 Memeriksa dan mengajukan (Analis HTA)")
    m.steps([
        "Buka tab **Sign-Off**. Kartu **Kelengkapan Dossier** harus bertanda **SIAP SIGN-OFF**, "
        "dengan semua butir wajib tercentang.",
        "Periksa kartu **Dossier Kasus untuk Tinjauan**: angkanya harus sama dengan tab asalnya.",
        "Klik **Tindakan** di kanan atas, lalu **Ajukan untuk Tinjauan**. Status kasus menjadi "
        "Dalam Tinjauan.",
    ])
    m.figure("27-signoff-kelengkapan", "Kelengkapan dossier dan ringkasannya, dilihat Analis HTA.",
             max_height_cm=17.0)
    m.figure("28-signoff-ajukan", "Menu Tindakan dengan pilihan Ajukan untuk Tinjauan.",
             max_height_cm=9.0, crop_bottom_at=0.62)
    m.callout(
        "Bandingkan dengan checklist paket (sheet 08_SIGN_OFF)",
        [
            "Kelengkapan Dossier memeriksa PICO, analisis ekonomi, BIA, sembilan domain EtD, "
            "rekomendasi, sign-off dan kriteria CBA.",
            "**PSA tidak ada dalam daftar itu.** Butir 4 checklist paket (PSA tersedia, dengan "
            "iterasi dan seed) harus diperiksa sendiri di tab PSA.",
            "Bila ada butir wajib yang kurang, pengajuan ditolak dengan pesan **Dossier belum "
            "lengkap** beserta daftar kekurangannya.",
        ],
    )

    m.section("8.2 Menandatangani (Ketua KFT)")
    m.steps([
        "Masuk sebagai Ketua KFT dan buka tab **Sign-Off** kasus tersebut.",
        "Tinjau dossier. Pada kartu **Tanda Tangan Ketua KFT**, klik **Setujui dengan Sign-Off**.",
        "Centang pernyataan konfirmasi, ketik **Sandi Anda**, lalu klik **Setujui & Tanda Tangan**.",
        "Status kasus menjadi Disetujui, dan tanda tangan tercatat pada **Riwayat Tanda Tangan**.",
    ])
    m.figure("29-signoff-ketua", "Tab Sign-Off dilihat Ketua KFT, dengan tiga pilihan keputusan.",
             max_height_cm=19.0)
    m.figure("30-signoff-tanda-tangan", "Konfirmasi dan sandi sebelum tanda tangan dicatat.",
             max_height_cm=8.5)
    m.figure("31-signoff-riwayat", "Riwayat tanda tangan. Alamat IP disamarkan.", max_height_cm=3.2)
    m.callout(
        "Wewenang",
        [
            "Hanya Ketua KFT yang melihat tombol tanda tangan. Peran lain dapat menyiapkan seluruh "
            "bukti dan draf, tetapi tidak dapat menyetujui.",
            "Ketua KFT menyetujui rekomendasi yang dihitung sistem; build ini tidak menyediakan "
            "pilihan jenis keputusan lain pada saat tanda tangan.",
            "**Minta Revisi** dan **Tolak** pada kartu ini wajib disertai alasan dan mengembalikan "
            "kasus ke Draft.",
        ],
    )


def brief(m: Manual) -> None:
    det = INITIAL["deterministic"]
    result = INITIAL["bia"]
    m.chapter("9. Menu 8 - Brief")
    m.role_line("Analis HTA (Ketua KFT dan Admin IT juga dapat)", "56")
    m.text(
        "Brief adalah ringkasan kebijakan dalam bentuk DOCX dan PDF. Brief baru dapat diterbitkan "
        "setelah kasus berstatus Disetujui atau Terkunci."
    )
    m.steps([
        "Buka tab **Brief** dan klik **Terbitkan Ringkasan**. Pembuatan dokumen memakan beberapa "
        "detik.",
        "Baris **v1** muncul pada **Riwayat Versi** dengan status **SELESAI**.",
        "Klik **DOCX** atau **PDF** untuk mengunduh. Kolom **SHA-256 DOCX** adalah sidik jari "
        "berkas, untuk membuktikan bahwa dokumen tidak diubah.",
    ])
    m.figure("33-brief-terbit", "Brief versi 1 selesai diterbitkan.", max_height_cm=8.0,
             crop_bottom_at=0.55)
    year_text = "; ".join(
        f"Tahun {y['year']} {rp(y['net_budget_impact'])}" for y in result["per_year"]
    )
    m.table(
        ["Bagian brief", "Isi pada kasus latihan"],
        [
            ["Sampul", "ID kasus, judul, intervensi, komparator, indikasi, status, versi, tanggal"],
            ["1. Ringkasan Eksekutif",
             f"{TRAFFIC_LABEL[INITIAL['recommendation']['traffic_light']]}; skor komposit "
             f"{num(INITIAL['recommendation']['composite_score'], 2)} dan keempat komponennya"],
            ["2. Analisis Efektivitas Biaya (CEA)",
             f"ICER {rp(det['icer'])}; biaya {rp(det['total_cost_intervention'])} vs "
             f"{rp(det['total_cost_comparator'])}; QALY {num(det['total_qaly_intervention'], 4)} vs "
             f"{num(det['total_qaly_comparator'], 4)}; ambang Rp300.000.000 per QALY"],
            ["3. Analisis Dampak Anggaran (BIA)",
             f"{year_text}; kumulatif {rp(result['cumulative_net_impact'])}"],
            ["4. Evidence-to-Decision (EtD)", "Tabel sembilan domain: skor, pilihan, kepastian, jumlah penilai"],
            ["5. Kriteria Akses (CBA)", "Empat kriteria dan status terpenuhinya"],
            ["6. Daftar Referensi", "Enam referensi"],
            ["7. Ringkasan Audit & Tanda Tangan", "Penanda tangan, keputusan, waktu"],
        ],
        [5.6, 11.4],
        caption="Isi brief versi 1, sudah dicocokkan dengan berkas yang dihasilkan",
    )
    m.callout(
        "Bandingkan dengan sheet 09_BRIEF paket",
        [
            "Angka CEA, BIA, EtD dan rekomendasi pada brief sama dengan tab asalnya.",
            "**Ringkasan PSA tidak tercantum pada brief** di build ini, begitu pula pertanyaan "
            "keputusan dan populasi. Untuk butir \"PSA summary\" pada paket, rujuk tab PSA.",
            "Berkas brief hasil pengerjaan ini disertakan pada folder `contoh-brief`.",
        ],
    )


def versi(m: Manual) -> None:
    det = REVISED["deterministic"]
    budget = REVISED["bia"]
    psa_result = REVISED["psa"]
    reco = REVISED["recommendation"]
    reason = INPUTS["revision_reason"]

    m.chapter("10. Menu 9 - Versi")
    m.role_line("Ketua KFT dan Analis HTA", "57-59")
    m.text(
        "Menu Versi mencatat riwayat kasus. Versi dibuat oleh sistem pada dua saat: ketika kasus "
        "dibuat (v0.1.0) dan ketika keputusan dikunci (v1.0). Hasil perhitungan tidak pernah "
        "ditimpa: setiap perhitungan ulang menambah catatan baru."
    )

    m.section("10.1 Versi awal (langkah 57)")
    m.text(
        "Buka tab **Versi**. Baris **v0.1.0** dengan pemicu **KASUS DIBUAT** sudah ada sejak kasus "
        "disimpan; tidak ada tombol untuk menyimpan versi secara manual."
    )
    m.figure("34-versi-awal", "Riwayat versi sebelum keputusan dikunci.", max_height_cm=8.5,
             crop_bottom_at=0.6)

    m.section("10.2 Latihan revisi (langkah 58-59)")
    m.text(
        "Paket meminta harga ARNI diturunkan dari Rp1.200.000 menjadi Rp1.100.000 per bulan, yaitu "
        "`13200000` per tahun, dengan alasan yang tercatat. Kasus sudah berstatus Disetujui, maka "
        "revisi dimulai oleh Ketua KFT."
    )
    m.steps([
        "**Ketua KFT:** klik **Tindakan**, lalu **Minta Revisi**. Ketik alasannya, "
        f"`{reason}`, dan klik **Lanjutkan**. Status kembali ke Dalam Tinjauan.",
        "**Analis HTA:** pada tab **Analisis Ekonomi**, ubah **Nilai** baris Biaya obat per pasien "
        "per tahun - Intervensi menjadi `13200000`, lalu klik **Simpan & Hitung**.",
        "**Analis HTA:** pada tab **BIA**, klik **Hitung BIA**.",
        "**Analis HTA:** pada tab **PSA**, dua peringatan muncul: hasil PSA tidak lagi sesuai "
        "input, dan mean distribusi biaya obat ARNI berbeda dari nilai dasarnya. Ketik ulang "
        "`10%` pada baris itu, klik **Simpan Distribusi**, lalu **Hitung PSA** dengan iterasi "
        "5000 dan seed 42.",
        "**Analis HTA:** pada tab **Rekomendasi**, peringatan **Rekomendasi ini tidak lagi sesuai "
        "input** muncul. Klik **Hitung Rekomendasi**.",
        "**Ketua KFT:** pada tab **Sign-Off**, tanda tangani lagi dengan **Setujui dengan "
        "Sign-Off**.",
        "**Analis HTA:** pada tab **Brief**, klik **Buat Versi Baru**. Brief v2 terbit; brief v1 "
        "tetap tersimpan dengan sidik jari yang berbeda.",
    ])
    m.figure("35-versi-minta-revisi", "Alasan wajib diisi ketika meminta revisi.", max_height_cm=6.5)
    m.figure("36-versi-harga-baru", "Nilai biaya obat ARNI diganti menjadi 13200000.",
             max_height_cm=2.2)
    m.figure("37-versi-hasil-baru", "Hasil deterministik setelah revisi harga.", max_height_cm=9.5)
    m.table(
        ["Keluaran", "Dashboard", "Kunci (sheet 10_VERSI, v0.2)", "Status"],
        [
            ["Incremental cost", rp(det["incremental_cost"]), rp(KEY["revised_incremental_cost"]),
             exact("Revisi incremental cost", det["incremental_cost"], KEY["revised_incremental_cost"])],
            ["ICER per QALY", rp(det["icer"], 2), rp(KEY["revised_icer"], 2),
             exact("Revisi ICER", det["icer"], KEY["revised_icer"])],
            ["INB", rp(det["inb"]), rp(KEY["revised_inb"]),
             exact("Revisi INB", det["inb"], KEY["revised_inb"])],
        ],
        [4.4, 4.2, 5.2, 3.2],
        caption="Hasil setelah revisi dibanding kunci",
    )
    m.figure("38-versi-bia-baru", "BIA setelah revisi harga.", max_height_cm=7.5)
    m.figure("39-versi-psa-peringatan",
             "Tab PSA setelah harga diubah: hasil lama ditandai tidak sesuai input, dan baris biaya "
             "obat ARNI ditandai berbeda dari nilai dasar.",
             max_height_cm=19.5, crop_bottom_at=0.62)
    m.figure("40-versi-psa-baru", "PSA setelah distribusi disesuaikan dan dijalankan ulang.",
             max_height_cm=4.2)
    m.figure("41-versi-rekomendasi-usang",
             "Tab Rekomendasi memberi tahu bahwa rekomendasi lama tidak lagi sesuai input.",
             max_height_cm=10.0, crop_bottom_at=0.75)
    m.figure("42-versi-rekomendasi-baru", "Rekomendasi setelah dihitung ulang.", max_height_cm=8.0)
    yearly = "; ".join(f"Tahun {y['year']} {rp(y['net_budget_impact'])}" for y in budget["per_year"])
    m.callout(
        "Angka setelah revisi",
        [
            f"BIA: {yearly}; kumulatif {rp(budget['cumulative_net_impact'])}.",
            f"PSA: probabilitas cost-effective "
            f"{pct(Decimal(str(psa_result['prob_cost_effective_base'])) * 100)} "
            f"(5000 iterasi, seed 42).",
            f"Rekomendasi: {TRAFFIC_LABEL[reco['traffic_light']]}, skor komposit "
            f"{num(reco['composite_score'], 2)}. Penurunan harga memperbaiki ICER dan BIA, tetapi "
            "tidak mengubah jenis rekomendasi.",
        ],
        kind="check",
    )
    m.figure("43-versi-tanda-tangan-ulang",
             "Riwayat tanda tangan memuat dua persetujuan: sebelum dan sesudah revisi.",
             max_height_cm=4.2)
    m.figure("44-versi-brief-v2", "Brief v2 terbit; v1 tetap dapat diunduh.", max_height_cm=5.0)

    m.section("10.3 Mengunci keputusan")
    m.steps([
        "**Ketua KFT:** klik **Tindakan**, lalu **Kunci Keputusan**. Status menjadi Terkunci.",
        "Buka tab **Versi**. Baris **v1.0** dengan pemicu **KEPUTUSAN DIKUNCI** muncul.",
        "Klik baris **v1.0**. Tab **Timeline Audit** memuat seluruh perubahan sampai saat itu, "
        "termasuk permintaan revisi beserta alasannya. Tab **Keadaan Data** memuat angka yang "
        "dibekukan pada versi itu.",
        "Pada **Bandingkan Versi**, pilih v0.1.0 dan v1.0, lalu klik **Tampilkan Diff** untuk "
        "melihat perbedaannya.",
    ])
    m.figure("45-versi-kunci", "Menu Tindakan Ketua KFT pada kasus yang sudah disetujui.",
             max_height_cm=8.5, crop_bottom_at=0.6)
    m.figure("46-versi-riwayat", "Riwayat versi setelah dikunci, dengan v0.1.0 dan v1.0.",
             max_height_cm=10.5)
    m.figure("47-versi-timeline",
             "Entri Timeline Audit untuk permintaan revisi, dengan alasannya.", max_height_cm=6.5)
    m.figure("48-versi-keadaan-data",
             "Keadaan Data versi 1.0: rekomendasi dan analisis ekonomi yang dibekukan.",
             max_height_cm=19.0, width_cm=11.5, crop_bottom_at=0.42)
    m.figure("48-versi-keadaan-data",
             "Keadaan Data versi 1.0 (lanjutan): BIA dan PSA. Tanda tangan dan brief ada di bawahnya.",
             max_height_cm=13.0, width_cm=11.5, crop_top_at=0.42, crop_bottom_at=0.69)
    m.figure("49-versi-diff", "Perbandingan v0.1.0 dan v1.0 (bagian atas).", max_height_cm=14.0,
             crop_bottom_at=0.3)
    m.figure("50-versi-terkunci",
             "Setelah dikunci, isian pada semua tab hanya dapat dibaca.", max_height_cm=6.0)
    m.callout(
        "Yang perlu diketahui tentang versi di build ini",
        [
            "Dashboard tidak membuat baris \"v0.2\" untuk revisi sebelum penguncian. Jejak revisi "
            "ada pada Timeline Audit, pada riwayat perhitungan tiap tab, pada dua tanda tangan, dan "
            "pada brief v1 dan v2.",
            "**Kasus yang sudah terkunci tidak dapat dibuka kembali.** Karena itu latihan revisi "
            "dikerjakan sebelum penguncian. Revisi setelah penguncian belum tersedia.",
            "Setelah terkunci, Ketua KFT dapat mengarsipkan kasus melalui **Tindakan**, "
            "**Arsipkan**. Pengarsipan tidak dibahas dalam panduan ini.",
        ],
        kind="warn",
    )
