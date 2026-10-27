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


def _probability(psa: dict) -> str:
    return pct(Decimal(str(psa["prob_cost_effective_base"])) * 100)


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
    m.role_line(
        "Sekretaris KFT (kriteria akses), Analis HTA (menghitung), lalu Anggota KFT "
        "(keputusan final)",
        "50-53",
    )
    m.text(
        "Menu ini menggabungkan bukti EtD, cost-effectiveness, dampak anggaran dan kriteria akses "
        "menjadi satu rekomendasi berwarna yang dihitung sistem. Di bawahnya, KFT mencatat "
        "keputusannya sendiri beserta alasan. Warna sistem adalah bahan pertimbangan; keputusan "
        "KFT yang ditandatangani."
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

    m.section("7.2 Menghitung rekomendasi sistem")
    m.steps([
        "Masuk sebagai Analis HTA dan buka tab **Rekomendasi**.",
        "Klik **Hitung Rekomendasi**.",
        "Kartu **Rekomendasi Akhir** menampilkan warna, skor komposit, keempat komponen, dan "
        "kalimat **Justifikasi**.",
    ])
    m.figure("26-rekomendasi-hasil", "Rekomendasi sistem untuk kasus latihan.", max_height_cm=8.0)
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
        caption="Komponen rekomendasi sistem",
    )

    m.section("7.3 Keputusan Final KFT (langkah 50, 51 dan 53)")
    m.text(
        "Paket meminta jenis keputusan dan alasan terintegrasi diisi manusia. Kartu **Keputusan "
        "Final KFT** di bawah rekomendasi sistem menampung keduanya. Kartu ini diisi oleh Anggota "
        "KFT atau Ketua KFT, wajib disertai alasan, dan menjadi syarat sign-off. Setiap perubahan "
        "disimpan sebagai riwayat; keputusan lama tidak pernah ditimpa."
    )
    m.steps([
        "Masuk sebagai Anggota KFT dan buka tab **Rekomendasi**.",
        "Pada kartu **Keputusan Final KFT**, pilih **Keputusan**: "
        f"`{INPUTS['final_decision']}`.",
        "Tulis **Alasan** yang memadukan seluruh menu, tidak hanya \"ICER di bawah WTP\".",
        "Klik **Simpan Keputusan Final**. Keputusan, alasan, nama pencatat, waktu, dan warna "
        "rekomendasi sistem yang menjadi dasarnya tampil pada kartu.",
    ])
    m.table(
        ["Isian", "Nilai pada kasus latihan"],
        [
            ["Keputusan", INPUTS["final_decision"]],
            ["Alasan", INPUTS["final_reason"]],
        ],
        [3.6, 13.4],
        caption="Keputusan Final KFT kasus latihan (paket langkah 50 dan 53)",
    )
    m.figure("26b-rekomendasi-keputusan-form", "Kartu Keputusan Final KFT sebelum disimpan.",
             max_height_cm=10.0)
    m.figure("26c-rekomendasi-keputusan-final",
             "Keputusan Final KFT tersimpan, di samping warna dan skor sistem.", max_height_cm=8.0)
    m.callout(
        "Warna sistem dan keputusan KFT",
        [
            "Lima jenis keputusan tersedia: Adopt, Adopt with criteria-based access, Defer pending "
            "additional evidence, Do not adopt, dan Reassess after price negotiation. KFT boleh "
            "memilih keputusan yang berbeda dari warna sistem, asal alasannya ditulis.",
            "Hasil **KUNING - Adopsi Bersyarat (CBA)** sepadan dengan keputusan latihan pada paket, "
            "\"Adopt with criteria-based access\": manfaat dan cost-effectiveness mendukung, tetapi "
            "dampak anggaran bermakna dan penggunaannya dibatasi kriteria.",
            "Bila rekomendasi dihitung ulang setelah keputusan dicatat, kartu meminta keputusan "
            "dicatat ulang atas rekomendasi terbaru sebelum sign-off.",
            "**Target populasi** (langkah 51) tidak diisi di sini: tercatat pada Ringkasan dan "
            "pertanyaan PICO, dan dicetak pada brief sebagai Populasi target.",
        ],
    )
    m.callout(
        "Yang perlu diketahui",
        [
            "**Hasil PSA tidak masuk ke skor komposit.** Skor cost-effectiveness hanya memakai "
            "hasil deterministik, sehingga ketidakpastian sekitar 56% ditimbang KFT dalam "
            "Keputusan Final KFT dan alasannya.",
            "**Bobot Domain EtD** pada tab ini boleh diisi Anggota KFT, tetapi sesuai keterangan "
            "di layar hanya menjadi informasi dan tidak mengubah skor.",
        ],
    )


def signoff(m: Manual) -> None:
    m.chapter("8. Menu 7 - Sign-Off")
    m.role_line("Analis HTA (mengajukan), lalu Ketua KFT (menandatangani)", "54-55")
    m.text(
        "Sign-off adalah persetujuan resmi Ketua KFT atas Keputusan Final KFT. Sebelum itu, "
        "Analis HTA memeriksa kelengkapan dossier dan mengajukan kasus untuk ditinjau."
    )

    m.section("8.1 Memeriksa dan mengajukan (Analis HTA)")
    m.steps([
        "Buka tab **Sign-Off**. Kartu **Kelengkapan Dossier** harus bertanda **SIAP SIGN-OFF**, "
        "dengan semua butir wajib tercentang.",
        "Periksa kartu **Dossier Kasus untuk Tinjauan**: angkanya harus sama dengan tab asalnya, "
        "dan Keputusan Final KFT tercantum.",
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
            "Kelengkapan Dossier memeriksa PICO, analisis ekonomi, BIA, **PSA yang dijalankan pada "
            "input terbaru**, sembilan domain EtD, rekomendasi, **rekomendasi yang masih sesuai "
            "input**, **Keputusan Final KFT**, sign-off dan kriteria CBA.",
            "PSA dianggap berlaku hanya bila inputnya sama dengan input sekarang. PSA yang "
            "dijalankan sebelum 13 Oktober 2026 belum mencatat inputnya dan harus dijalankan ulang "
            "sekali.",
            "Bila ada butir wajib yang kurang, pengajuan ditolak dengan pesan **Dossier belum "
            "lengkap** beserta daftar kekurangannya, dan tombol tanda tangan Ketua KFT tidak aktif.",
        ],
    )

    m.section("8.2 Menandatangani (Ketua KFT)")
    m.steps([
        "Masuk sebagai Ketua KFT dan buka tab **Sign-Off** kasus tersebut.",
        "Tinjau dossier. Pada kartu **Tanda Tangan Ketua KFT**, klik **Setujui dengan Sign-Off**.",
        "Centang pernyataan konfirmasi, ketik **Sandi Anda**, lalu klik **Setujui & Tanda Tangan**.",
        "Status kasus menjadi Disetujui, dan tanda tangan tercatat pada **Riwayat Tanda Tangan** "
        "bersama Keputusan Final KFT yang ditandatangani.",
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
            "Tanda tangan mengikat Keputusan Final KFT yang tercatat saat itu. Bila Ketua KFT "
            "berpendapat lain, ia mencatat keputusan baru di tab Rekomendasi lebih dulu.",
            "**Minta Revisi** dan **Tolak** pada kartu ini wajib disertai alasan dan mengembalikan "
            "kasus ke Draft.",
        ],
    )


def brief(m: Manual) -> None:
    det = INITIAL["deterministic"]
    result = INITIAL["bia"]
    psa = INITIAL["psa"]
    m.chapter("9. Menu 8 - Brief")
    m.role_line("Analis HTA (Ketua KFT juga dapat)", "56")
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
            ["Sampul", "ID kasus, judul, intervensi, komparator, indikasi, populasi target, "
             "setting, perspektif, status, versi, tanggal"],
            ["1. Ringkasan Eksekutif",
             f"Keputusan Final KFT ({INPUTS['final_decision']}) dan alasannya; lalu rekomendasi "
             f"sistem {TRAFFIC_LABEL[INITIAL['recommendation']['traffic_light']]}, skor komposit "
             f"{num(INITIAL['recommendation']['composite_score'], 2)} dan keempat komponennya"],
            ["2. Pertanyaan Keputusan dan Populasi Target",
             "Populasi target, pertanyaan keputusan, dan keempat unsur PICO"],
            ["3. Analisis Efektivitas Biaya (CEA)",
             f"ICER {rp(det['icer'])}; biaya {rp(det['total_cost_intervention'])} vs "
             f"{rp(det['total_cost_comparator'])}; QALY {num(det['total_qaly_intervention'], 4)} vs "
             f"{num(det['total_qaly_comparator'], 4)}; ambang Rp300.000.000 per QALY"],
            ["4. Analisis Dampak Anggaran (BIA)",
             f"{year_text}; kumulatif {rp(result['cumulative_net_impact'])}"],
            ["5. Analisis Sensitivitas Probabilistik (PSA)",
             f"{num(psa['n_simulations'], 0)} iterasi, seed {psa['random_seed']}; peluang "
             f"cost-effective {_probability(psa)}; rerata selisih biaya dan QALY; titik-titik CEAC"],
            ["6. Evidence-to-Decision (EtD)", "Tabel sembilan domain: skor, pilihan, kepastian, jumlah penilai"],
            ["7. Kriteria Akses (CBA)", "Empat kriteria dan status terpenuhinya"],
            ["8. Daftar Referensi", "Enam referensi"],
            ["9. Ringkasan Audit & Tanda Tangan", "Penanda tangan, keputusan, waktu"],
        ],
        [5.6, 11.4],
        caption="Isi brief versi 1, sudah dicocokkan dengan berkas yang dihasilkan",
    )
    m.callout(
        "Bandingkan dengan sheet 09_BRIEF paket",
        [
            "Angka CEA, BIA, PSA, EtD dan rekomendasi pada brief sama dengan tab asalnya.",
            "Brief memuat ringkasan PSA, pertanyaan keputusan, populasi target, dan Keputusan "
            "Final KFT yang ditandatangani.",
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
    m.role_line("Ketua KFT, Analis HTA, dan Anggota KFT", "55, 57-59")
    m.text(
        "Menu Versi mencatat riwayat kasus. Versi dibuat oleh sistem pada tiga saat: ketika kasus "
        "dibuat (v0.1.0), ketika keputusan dikunci (v1.0, v1.1, dan seterusnya), dan ketika kasus "
        "terkunci dibuka untuk revisi (misalnya v1.1-draft, beserta alasannya). Versi yang sudah "
        "terkunci tidak pernah diubah, dan hasil perhitungan tidak pernah ditimpa."
    )

    m.section("10.1 Versi awal (langkah 57)")
    m.text(
        "Buka tab **Versi**. Baris **v0.1.0** dengan pemicu **KASUS DIBUAT** sudah ada sejak kasus "
        "disimpan; tidak ada tombol untuk menyimpan versi secara manual."
    )
    m.figure("34-versi-awal", "Riwayat versi sebelum keputusan dikunci.", max_height_cm=8.5,
             crop_bottom_at=0.6)

    m.section("10.2 Mengunci keputusan sebagai v1.0 (langkah 55)")
    m.steps([
        "**Ketua KFT:** klik **Tindakan**, lalu **Kunci Keputusan**. Status menjadi Terkunci dan "
        "baris **v1.0** dengan pemicu **KEPUTUSAN DIKUNCI** muncul di tab Versi.",
        "Seluruh angka yang menjadi dasar keputusan dibekukan pada v1.0. Semua isian kini hanya "
        "dapat dibaca.",
    ])
    m.figure("45-versi-kunci", "Menu Tindakan Ketua KFT pada kasus yang sudah disetujui.",
             max_height_cm=8.5, crop_bottom_at=0.6)

    m.section("10.3 Latihan revisi sebagai versi baru (langkah 58-59)")
    m.text(
        "Paket meminta harga ARNI diturunkan dari Rp1.200.000 menjadi Rp1.100.000 per bulan, yaitu "
        "`13200000` per tahun, sebagai versi baru dengan alasan yang tercatat, tanpa mengubah "
        "versi lama. Analis HTA atau Ketua KFT dapat memulai revisi; di sini Ketua KFT."
    )
    m.steps([
        "**Ketua KFT:** klik **Tindakan**, lalu **Buat Revisi (Versi Baru)**. Ketik alasannya, "
        f"`{reason}`, dan klik **Lanjutkan**. Kasus kembali ke Draft dengan keterangan **Revisi "
        "dari v1.0 sedang berjalan**; v1.0 tetap tersimpan tanpa perubahan.",
        "**Analis HTA:** pada tab **Analisis Ekonomi**, ubah **Nilai** baris Biaya obat per pasien "
        "per tahun - Intervensi menjadi `13200000`, lalu klik **Simpan & Hitung**.",
        "**Analis HTA:** pada tab **BIA**, klik **Hitung BIA**.",
        "**Analis HTA:** pada tab **PSA**, dua peringatan muncul: hasil PSA tidak lagi sesuai "
        "input, dan mean distribusi biaya obat ARNI berbeda dari nilai dasarnya. Ketik ulang "
        "`10%` pada baris itu, klik **Simpan Distribusi**, lalu **Hitung PSA** dengan iterasi "
        "5000 dan seed 42.",
        "**Analis HTA:** pada tab **Rekomendasi**, peringatan **Rekomendasi ini tidak lagi sesuai "
        "input** muncul. Klik **Hitung Rekomendasi**.",
        "**Anggota KFT:** pada kartu **Keputusan Final KFT**, catat keputusan untuk versi baru "
        "dengan **Catat Keputusan Baru**. Keputusan untuk v1.0 tetap tercantum pada riwayat.",
        "**Analis HTA:** klik **Tindakan**, lalu **Ajukan untuk Tinjauan**.",
        "**Ketua KFT:** pada tab **Sign-Off**, tanda tangani lagi dengan **Setujui dengan "
        "Sign-Off**. Tanda tangan untuk v1.0 tidak berlaku untuk versi baru.",
        "**Analis HTA:** pada tab **Brief**, klik **Buat Versi Baru**. Brief v2 terbit; brief v1 "
        "tetap tersimpan dengan sidik jari yang berbeda.",
        "**Ketua KFT:** klik **Tindakan**, lalu **Kunci Keputusan**. Versi baru terkunci sebagai "
        "**v1.1**, beserta brief v2.",
    ])
    m.figure("35-versi-buat-revisi",
             "Membuat revisi: penjelasan dan alasan wajib sebelum kasus dibuka kembali.",
             max_height_cm=8.0)
    m.figure("35b-versi-revisi-berjalan",
             "Kasus kembali ke Draft dengan keterangan revisi dari v1.0.", max_height_cm=6.0,
             crop_bottom_at=0.37)
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
    m.figure("42b-versi-keputusan-ulang",
             "Keputusan Final KFT untuk versi baru; keputusan untuk v1.0 ada pada riwayat.",
             max_height_cm=11.0)
    yearly = "; ".join(f"Tahun {y['year']} {rp(y['net_budget_impact'])}" for y in budget["per_year"])
    m.callout(
        "Angka setelah revisi",
        [
            f"BIA: {yearly}; kumulatif {rp(budget['cumulative_net_impact'])}.",
            f"PSA: probabilitas cost-effective {_probability(psa_result)} (5000 iterasi, seed 42).",
            f"Rekomendasi sistem: {TRAFFIC_LABEL[reco['traffic_light']]}, skor komposit "
            f"{num(reco['composite_score'], 2)}. Penurunan harga memperbaiki ICER dan BIA, tetapi "
            "tidak mengubah jenis rekomendasi.",
            f"Keputusan Final KFT untuk versi baru: {INPUTS['final_decision']}, dengan alasan: "
            f"{INPUTS['final_reason_revised']}",
        ],
        kind="check",
    )
    m.figure("43-versi-tanda-tangan-ulang",
             "Riwayat tanda tangan memuat dua persetujuan: untuk v1.0 dan untuk versi baru.",
             max_height_cm=4.2)
    m.figure("44-versi-brief-v2", "Brief v2 terbit; v1 tetap dapat diunduh.", max_height_cm=5.0)

    m.section("10.4 Membaca riwayat versi")
    m.steps([
        "Buka tab **Versi**. Riwayat memuat **v0.1.0**, **v1.0**, baris **v1.1-draft** dengan "
        "pemicu **REVISI DIMINTA** dan alasannya, serta **v1.1**.",
        "Klik baris **v1.1**. Tab **Timeline Audit** memuat seluruh perubahan sampai saat itu, "
        "termasuk pembuatan revisi beserta alasannya. Tab **Keadaan Data** memuat angka yang "
        "dibekukan pada versi itu.",
        "Pada **Bandingkan Versi**, pilih v1.0 dan v1.1, lalu klik **Tampilkan Diff** untuk "
        "melihat angka yang berubah karena revisi harga.",
    ])
    m.figure("46-versi-riwayat",
             "Riwayat versi: v0.1.0, v1.0, revisi v1.1-draft beserta alasannya, dan v1.1.",
             max_height_cm=11.5)
    m.figure("47-versi-timeline",
             "Entri Timeline Audit untuk pembuatan revisi, dengan alasannya.", max_height_cm=6.5)
    m.figure("48-versi-keadaan-data",
             "Keadaan Data versi 1.1: rekomendasi, Keputusan Final KFT dan analisis ekonomi yang "
             "dibekukan.",
             max_height_cm=19.5, width_cm=11.5, crop_bottom_at=0.52)
    m.figure("48-versi-keadaan-data",
             "Keadaan Data versi 1.1 (lanjutan): BIA, PSA, tanda tangan dan brief v2.",
             max_height_cm=19.0, width_cm=11.5, crop_top_at=0.52, crop_bottom_at=0.995)
    m.figure("49-versi-diff",
             "Perbandingan v1.0 dan v1.1: angka yang berubah karena revisi harga.",
             max_height_cm=17.0, crop_bottom_at=0.5)
    m.figure("49-versi-diff",
             "Perbandingan v1.0 dan v1.1 (lanjutan): rekomendasi dan Keputusan Final KFT tiap versi.",
             max_height_cm=12.0, crop_top_at=0.505, crop_bottom_at=0.75)
    m.figure("50-versi-terkunci",
             "Setelah dikunci, isian pada semua tab hanya dapat dibaca.", max_height_cm=6.0)
    m.callout(
        "Yang perlu diketahui tentang versi",
        [
            "Penomoran paket v0.1 dan v0.2 sepadan dengan v1.0 dan v1.1 di dashboard: keduanya "
            "adalah keputusan yang sudah dikunci.",
            "Versi baru selalu memerlukan Keputusan Final KFT dan tanda tangan Ketua KFT yang "
            "baru; yang dicatat untuk versi sebelumnya tidak berlaku lagi.",
            "Kasus yang sudah diarsipkan adalah rekam keputusan resmi dan tidak dapat direvisi. "
            "Pengarsipan (Tindakan, **Arsipkan**, oleh Ketua KFT) tidak dibahas dalam panduan ini.",
        ],
        kind="warn",
    )
