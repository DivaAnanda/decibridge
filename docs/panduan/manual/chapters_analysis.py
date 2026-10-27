"""Cover, preparation, and the four analysis menus: Ringkasan, Analisis Ekonomi, BIA, PSA."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from .data import (
    BUILD, BULAN, CASE_ID, INITIAL, INPUTS, KEY, PACKAGE, approximate, exact, num, pct, rp,
)
from .document import Manual

# Package step numbers for the sixteen rows typed into the parameter registry.
PARAMETER_STEPS = ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
                   "26", "27", "28", "29", "30", "31"]


def cover(m: Manual) -> None:
    today = date.today()
    m.cover(
        "Buku Panduan DeciBridge",
        "Kasus latihan ARNI vs Ramipril pada HFrEF",
        "Langkah demi langkah dari menu Ringkasan sampai Versi, dengan tangkapan layar",
        [
            f"Kasus: `{CASE_ID}`",
            f"Sumber data: {PACKAGE}",
            f"Build aplikasi: v1.0.0 - {BUILD}",
            f"Disusun: {today.day} {BULAN[today.month]} {today.year}",
        ],
        "Data latihan sintetis",
        "Seluruh angka dalam panduan ini berasal dari paket latihan dan dibuat khusus untuk "
        "pembelajaran. Angka-angka itu bukan data pasien, bukan data rumah sakit, dan tidak "
        "boleh dipakai untuk keputusan klinis atau formularium yang sebenarnya.",
    )


def about(m: Manual) -> None:
    m.chapter("Tentang panduan ini")
    m.text(
        f"Panduan ini menunjukkan cara mengerjakan satu kasus lengkap di DeciBridge, mengikuti "
        f"Paket Data Demo ({PACKAGE}) dari menu Ringkasan sampai Versi. Setiap bab menyebut nomor "
        "langkah pada sheet 01_STEP_BY_STEP paket, nilai yang diketik, peran yang mengerjakan, dan "
        "hasil yang seharusnya muncul di layar."
    )
    m.text(
        f"Semua tangkapan layar diambil dari satu kali pengerjaan kasus `{CASE_ID}` pada database "
        f"kosong, dengan build {BUILD}. Angka pada tabel hasil dikutip langsung dari pengerjaan itu "
        "dan dicocokkan dengan 11_INSTRUCTOR_KEY pada Lampiran A."
    )
    m.section("Cara membaca panduan")
    m.bullets([
        "Teks **tebal** adalah nama tombol, tab, atau isian persis seperti di layar.",
        "Teks `seperti ini` adalah nilai yang diketik persis seperti tertulis. Desimal memakai "
        "titik, bukan koma: `0.30`.",
        "Kotak biru berisi catatan, kotak kuning berisi hal yang sering keliru, dan kotak hijau "
        "berisi angka untuk mencocokkan hasil.",
        "Tempat dashboard berbeda dari paket latihan dirangkum pada Lampiran B.",
    ])
    m.callout(
        "Bila berlatih di situs bersama",
        [
            f"Kasus `{CASE_ID}` sudah tersedia di sana sebagai rujukan, dan satu ID kasus hanya "
            "dapat dipakai sekali. Buat kasus dengan ID sendiri, misalnya `INISIAL_DEMO_HF_001`, "
            "lalu ikuti langkah yang sama. Jangan mengubah kasus milik orang lain.",
        ],
    )

    m.section("Isi panduan")
    m.table(
        ["Bab", "Menu", "Langkah paket", "Peran yang mengerjakan"],
        [
            ["1", "Persiapan: akun, peran, dan cara masuk", "-", "Semua"],
            ["2", "Ringkasan", "1-10", "Analis HTA"],
            ["3", "Analisis Ekonomi", "11-24", "Analis HTA"],
            ["4", "BIA", "25-34", "Analis HTA"],
            ["5", "PSA", "35-40", "Analis HTA"],
            ["6", "EtD", "41-49", "Analis HTA, lalu Anggota KFT"],
            ["7", "Rekomendasi", "50-53", "Sekretaris KFT, Analis HTA, lalu Anggota KFT"],
            ["8", "Sign-Off", "54-55", "Analis HTA, lalu Ketua KFT"],
            ["9", "Brief", "56", "Analis HTA"],
            ["10", "Versi", "55, 57-59", "Ketua KFT, Analis HTA dan Anggota KFT"],
            ["A", "Lampiran: kunci hasil", "", ""],
            ["B", "Lampiran: perbedaan paket latihan dan dashboard", "", ""],
            ["C", "Lampiran: masalah yang sering terjadi", "", ""],
        ],
        [1.2, 7.5, 2.8, 5.5],
    )


def preparation(m: Manual) -> None:
    m.chapter("1. Persiapan")
    m.section("1.1 Peran dan akun")
    m.text(
        "DeciBridge membagi pekerjaan menurut peran. Satu kasus baru selesai setelah keempat peran "
        "di bawah ini mengerjakan bagiannya. Orang yang berlatih sendiri perlu berganti akun pada "
        "setiap pergantian peran: klik nama di kanan atas, pilih **Keluar**, lalu masuk dengan akun "
        "berikutnya."
    )
    m.table(
        ["Peran", "Akun demo", "Yang dikerjakan dalam panduan ini"],
        [
            ["Analis HTA / Farmakoekonomi", "`hta@test.local`",
             "Membuat kasus; mengisi Analisis Ekonomi, BIA, PSA dan referensi; menghitung "
             "rekomendasi; mengajukan kasus; menerbitkan brief"],
            ["Sekretaris KFT / Farmasi RS", "`sekre@test.local`", "Mengisi kriteria akses (CBA)"],
            ["Anggota KFT", "`kft1@test.local`",
             "Menilai sembilan domain EtD; mencatat Keputusan Final KFT beserta alasannya"],
            ["Ketua KFT", "`ketua@test.local`",
             "Menandatangani sign-off, mengunci keputusan, membuat revisi sebagai versi baru"],
            ["Admin IT", "`adminit@test.local`",
             "Tidak membuka isi kasus; mengelola pengguna, memantau status dan integritas "
             "kasus, dan memeriksa segel arsip"],
        ],
        [4.2, 3.6, 9.2],
        caption="Peran, akun demo, dan pekerjaannya",
    )
    m.text("Kata sandi akun demo tertulis di halaman masuk, pada bagian **Akun demo**.")
    m.text(
        "Admin IT mengurus pengguna, sistem dan cadangan. Pada daftar kasus dan halaman kasus, "
        "Admin IT hanya melihat metadata: ID, judul, status, tanggal, integritas, dan segel arsip. "
        "Isi analisis tidak dapat dibuka, dan Admin IT tidak dapat mengubah analisis maupun "
        "menerbitkan keputusan."
    )
    m.figure("51-admin-it-kasus", "Kasus latihan dilihat Admin IT: metadata saja.",
             max_height_cm=8.5, crop_bottom_at=0.72)

    m.section("1.2 Masuk")
    m.steps([
        "Buka alamat aplikasi, lalu buka halaman masuk.",
        "Isi **Email** dan **Kata sandi**, lalu klik **Masuk**.",
        "Halaman **Beranda** terbuka. Nama dan peran akun tampil di bagian atas.",
    ])
    m.figure("01-login", "Halaman masuk. Daftar akun demo ada di bagian bawah kartu.",
             max_height_cm=9.5)
    m.figure("02-beranda", "Beranda Analis HTA sebelum ada kasus.", max_height_cm=10.5)

    m.section("1.3 Urutan kerja")
    m.text(
        "Sembilan menu kasus dikerjakan berurutan dari kiri ke kanan. Tiga menu pertama setelah "
        "Ringkasan menghitung bukti ekonomi, EtD dan Rekomendasi menimbangnya, lalu Sign-Off, "
        "Brief dan Versi mencatat keputusannya."
    )
    m.table(
        ["Status kasus", "Terjadi ketika", "Yang masih dapat diubah"],
        [
            ["Draft", "Kasus baru dibuat", "Semua isian"],
            ["Dalam Tinjauan", "Analis HTA memilih **Ajukan untuk Tinjauan**",
             "Semua isian; Ketua KFT dapat menandatangani"],
            ["Disetujui", "Ketua KFT menandatangani sign-off",
             "Brief dapat diterbitkan; Ketua KFT dapat meminta revisi"],
            ["Terkunci", "Ketua KFT memilih **Kunci Keputusan**",
             "Tidak ada. Untuk mengubah, Analis HTA atau Ketua KFT memilih **Buat Revisi (Versi "
             "Baru)**; kasus kembali ke Draft sebagai versi berikutnya dan versi terkunci tetap "
             "utuh"],
        ],
        [3.2, 6.6, 7.2],
        caption="Status kasus sepanjang alur",
    )


def ringkasan(m: Manual) -> None:
    m.chapter("2. Menu 1 - Ringkasan")
    m.role_line("Analis HTA", "1-10")
    m.text(
        "Menu Ringkasan memuat identitas kasus dan pertanyaan keputusannya (PICO). Isinya diketik "
        "satu kali ketika kasus dibuat, melalui tiga langkah."
    )
    m.steps([
        "Di **Beranda**, klik **Buat Kasus Baru**.",
        "Langkah **Identitas**: isi **ID Kasus** dan **Judul Kasus**, lalu klik **Lanjut**.",
        "Langkah **Klinis**: isi **Intervensi (Teknologi)**, **Komparator**, **Indikasi**, "
        "**Populasi** dan **Setting**. Biarkan **Perspektif** pada **Rumah Sakit**. Klik **Lanjut**.",
        "Langkah **PICO**: isi **Pertanyaan klinis** dan keempat unsur PICO, lalu klik **Lanjut**.",
        "Periksa ringkasan, lalu klik **Simpan Kasus**. Kasus terbuka pada tab **Ringkasan** "
        "dengan status **DRAFT**.",
    ])
    m.table(
        ["Isian", "Nilai yang diketik", "Langkah"],
        [
            ["ID Kasus", f"`{CASE_ID}`", "1"],
            ["Judul Kasus", "Demo ARNI vs Ramipril pada HFrEF", "2"],
            ["Indikasi", "Heart failure with reduced ejection fraction (HFrEF)", "3"],
            ["Populasi", "Dewasa >=18 tahun, HFrEF LVEF <=40%, NYHA II-IV, stabil", "4"],
            ["Intervensi (Teknologi)", "Sacubitril/valsartan (ARNI)", "5"],
            ["Komparator", "Ramipril (ACEI)", "6"],
            ["Setting", "Formularium rumah sakit; rawat jalan HFrEF", "7"],
            ["Perspektif", "Rumah Sakit", "8"],
            ["Pertanyaan klinis", "Apakah ARNI diadopsi dibanding ramipril untuk pasien HFrEF eligible?", "-"],
            ["Populasi (P), Intervensi (I), Komparator (C)", "Sama dengan isian di atas", "4-6"],
            ["Outcome (O)", "QALY; rehospitalisasi HF", "10"],
        ],
        [4.6, 10.6, 1.8],
        caption="Isian Ringkasan",
    )
    m.callout(
        "Dua isian paket yang letaknya berbeda",
        [
            "**Time horizon** (langkah 9) tidak diisi di sini. Isian itu ada di menu Analisis "
            "Ekonomi sebagai **Horizon CEA (tahun)**.",
            "**Outcome** (langkah 10) diisi pada **Outcome (O)** di langkah PICO.",
            "ID kasus hanya menerima huruf besar, angka dan garis bawah, dan tidak dapat diubah "
            "setelah kasus disimpan.",
        ],
    )
    m.figure("03-kasus-identitas", "Langkah Identitas pada pembuatan kasus.", max_height_cm=9.0)
    m.figure("04-kasus-klinis", "Langkah Klinis.", max_height_cm=10.0)
    m.figure("05-kasus-pico", "Langkah PICO.", max_height_cm=10.0)
    m.figure("06-ringkasan", "Tab Ringkasan setelah kasus disimpan. Status kasus masih DRAFT.",
             max_height_cm=10.5)


def ekonomi(m: Manual) -> None:
    det = INITIAL["deterministic"]
    m.chapter("3. Menu 2 - Analisis Ekonomi")
    m.role_line("Analis HTA", "11-24 (dan input BIA, langkah 25-33)")
    m.text(
        "Menu ini memuat model cost-utility: beberapa pengaturan model, lalu daftar parameter "
        "untuk tiap lengan. Semua input BIA juga diketik di sini; tab BIA hanya menghitung dan "
        "menampilkan hasilnya."
    )

    m.section("3.1 Parameter model")
    m.steps([
        "Buka tab **Analisis Ekonomi**.",
        "Isi kartu **Parameter Model Ekonomi** sesuai Tabel berikut.",
        "Klik **Simpan Model**. Model harus tersimpan sebelum parameter dapat disimpan.",
    ])
    m.table(
        ["Isian", "Nilai yang diketik", "Langkah", "Keterangan"],
        [
            ["Horizon CEA (tahun)", "`1`", "9", "Horizon analisis cost-utility"],
            ["Horizon BIA (tahun)", "`3`", "25", "Kosong berarti sama dengan horizon CEA"],
            ["Discount rate biaya", "`0`", "21", "Horizon hanya satu tahun"],
            ["Discount rate QALY", "`0`", "22", "Horizon hanya satu tahun"],
            ["WTP threshold (IDR/QALY)", "`300000000`", "23", "Rp300 juta per QALY"],
            ["Anggaran tahunan baseline (BIA)", "`20000000000`", "33", "Dasar persen dampak anggaran"],
            ["Catatan", "Keterangan bahwa data sintetis dan biaya obat diisi per tahun", "-", "Bebas"],
        ],
        [5.0, 4.6, 1.6, 5.8],
        caption="Parameter model",
    )
    m.figure("07-ekonomi-model", "Kartu Parameter Model Ekonomi sebelum disimpan.", max_height_cm=6.0)

    m.section("3.2 Registri parameter")
    m.text(
        "Setiap parameter ditambahkan sebagai satu baris. Pada bagian **Tambah parameter** di "
        "bawah tabel, pilih **Parameter**, **Alternatif** dan **Tahun**, lalu klik **Tambah**. "
        "Baris baru muncul di tabel; isi **Nilai**, **Satuan** dan **Sumber** pada baris itu."
    )
    rows = []
    for (parameter, alternative, year, value, unit, source), step in zip(
        INPUTS["parameters"], PARAMETER_STEPS
    ):
        rows.append([parameter, alternative, year or "Semua", f"`{value}`", unit, source, step])
    m.table(
        ["Parameter", "Alternatif", "Tahun", "Nilai", "Satuan", "Sumber", "Langkah"],
        rows,
        [3.9, 2.3, 1.6, 2.0, 2.6, 2.9, 1.7],
        caption="Enam belas baris parameter: sepuluh untuk analisis ekonomi, enam untuk BIA",
    )
    m.callout(
        "Empat hal yang sering keliru",
        [
            "**Biaya obat diisi per tahun.** Paket menulis biaya per bulan (Rp1.200.000 dan "
            "Rp100.000), sedangkan isian dashboard adalah biaya per pasien per tahun. Kalikan 12: "
            "`14400000` dan `1200000`.",
            "**Proporsi ditulis 0-1, bukan persen.** Probabilitas 30% diketik `0.30`, bukan `30`. "
            "Isian yang wajib 0-1 diberi tanda **0-1** di sisi kanan. Nilai seperti 30 ditolak saat "
            "disimpan dan barisnya ditandai merah.",
            "**Bersama** berarti satu nilai dipakai kedua lengan. Biaya per kejadian dan disutility "
            "diisi sekali dengan alternatif **Bersama**, tidak perlu diketik dua kali.",
            "**Market share tidak diisi.** Lihat kotak peringatan pada Bab 4.",
        ],
        kind="warn",
    )
    m.callout(
        "Status dan peringatan oranye",
        [
            "Kolom **Status** dibiarkan **Assumption** karena seluruh data paket adalah data "
            "sintetis. Dashboard lalu menampilkan peringatan bahwa parameter masih berstatus proxy "
            "atau asumsi. Untuk kasus latihan, peringatan itu memang seharusnya muncul.",
        ],
    )
    m.figure("08-ekonomi-tambah-parameter",
             "Baris pertama setelah klik Tambah, dengan nilai, satuan dan sumber terisi.",
             max_height_cm=8.5)
    m.figure("09-ekonomi-registri", "Registri Parameter lengkap, sebelum disimpan.", max_height_cm=19.5)

    m.section("3.3 Menyimpan dan menghitung")
    m.steps([
        "Klik **Simpan Parameter**. Bila ada baris yang ditolak, alasannya tampil di bawah isian "
        "**Nilai** baris tersebut dan tidak ada baris yang tersimpan sampai semuanya benar.",
        "Klik **Hitung**. Bila masih ada perubahan yang belum disimpan, tombol itu berbunyi "
        "**Simpan & Hitung** dan mengerjakan keduanya.",
        "Kartu **Hasil Deterministik (Cost-Utility)** muncul di bagian atas.",
    ])
    m.figure("10-ekonomi-hasil", "Hasil deterministik kasus latihan.", max_height_cm=9.5)
    m.callout(
        "Cocokkan dengan kunci (langkah 24)",
        [
            f"Total cost {rp(det['total_cost_intervention'])} vs {rp(det['total_cost_comparator'])}; "
            f"QALY {num(det['total_qaly_intervention'], 3)} vs {num(det['total_qaly_comparator'], 3)}.",
            f"Incremental cost {rp(det['incremental_cost'])}; incremental QALY "
            f"{num(det['incremental_qaly'], 3)}; ICER {rp(det['icer'], 2)} per QALY; "
            f"INB {rp(det['inb'])}.",
            "ICER berada di bawah WTP Rp300 juta dan INB positif, sehingga label hasilnya "
            "COST-EFFECTIVE. Paket menegaskan bahwa keputusan tidak berhenti di sini: lanjutkan "
            "ke BIA dan PSA.",
        ],
        kind="check",
    )


def bia(m: Manual) -> None:
    result = INITIAL["bia"]
    m.chapter("4. Menu 3 - BIA")
    m.role_line("Analis HTA", "25-34")
    m.text(
        "BIA menghitung tambahan beban anggaran rumah sakit per tahun, setelah dikurangi "
        "penghematan dari kejadian yang dicegah (cost offset). Inputnya sudah diketik di menu "
        "Analisis Ekonomi: **Horizon BIA** dan **Anggaran tahunan baseline** pada parameter model, "
        "serta **Jumlah populasi eligible** dan **Uptake** untuk Tahun 1 sampai Tahun 3 pada "
        "registri parameter."
    )
    m.callout(
        "Baris per tahun",
        [
            "Pilihan **Tahun 1**, **Tahun 2** dan **Tahun 3** pada **Tambah parameter** baru "
            "tersedia setelah **Horizon BIA** diisi 3. Baris per tahun diberi label TAHUN 1, "
            "TAHUN 2, TAHUN 3 di tabel.",
        ],
    )
    m.callout(
        "Market share baseline (langkah 32): jangan diisi",
        [
            "Paket menulis market share baseline ARNI = 0, artinya ARNI belum dipakai. Parameter "
            "**Market share** di dashboard bermakna lain: pengali jumlah pasien "
            "(pasien = eligible x uptake x market share) yang bernilai 1 bila tidak diisi. "
            "Mengisinya dengan 0 membuat jumlah pasien, dan seluruh BIA, menjadi nol.",
        ],
        kind="warn",
    )
    m.steps([
        "Buka tab **BIA**.",
        "Klik **Hitung BIA**.",
        "Kartu **Dampak Anggaran (dengan cost offset)** menampilkan rincian per tahun.",
    ])
    m.figure("12-bia-hasil", "Hasil BIA tiga tahun.", max_height_cm=8.0, crop_bottom_at=0.78)

    rows = []
    for index, year in enumerate(result["per_year"]):
        status = exact(f"BIA tahun {year['year']}", year["net_budget_impact"], KEY["bia_net"][index])
        exact(f"Pasien tahun {year['year']}", year["patients_intervention"], KEY["bia_patients"][index])
        rows.append([
            f"Tahun {year['year']}",
            num(year["patients_intervention"]),
            rp(year["net_budget_impact"]),
            pct(year["pct_of_annual_baseline"]),
            rp(KEY["bia_net"][index]),
            status,
        ])
    rows.append([
        "Kumulatif", "-", rp(result["cumulative_net_impact"]), pct(result["pct_of_total_baseline"]),
        rp(KEY["bia_cumulative"]),
        exact("BIA kumulatif", result["cumulative_net_impact"], KEY["bia_cumulative"]),
    ])
    m.table(
        ["Periode", "Pasien ARNI", "Dampak bersih", "% anggaran", "Kunci instruktur", "Status"],
        rows,
        [2.4, 2.4, 3.6, 2.4, 3.6, 2.6],
        caption="Hasil BIA dibanding kunci (langkah 34)",
    )
    m.text(
        "Persen anggaran pada baris kumulatif dihitung terhadap anggaran tiga tahun. Label "
        "**SIGNIFIKAN** dan **Skor anggaran** pada kartu dipakai lagi di menu Rekomendasi. Pesan "
        "paket untuk bagian ini: intervensi dapat tampak cost-effective tetapi tetap menambah "
        "anggaran, sehingga keterjangkauan harus dibahas tersendiri."
    )


def psa(m: Manual) -> None:
    result = INITIAL["psa"]
    m.chapter("5. Menu 4 - PSA")
    m.role_line("Analis HTA", "35-40")
    m.text(
        "PSA mengulang perhitungan ribuan kali dengan parameter yang diambil acak dari "
        "distribusinya, untuk melihat seberapa yakin hasil cost-effective itu. Ada dua bagian: "
        "mengatur distribusi tiap parameter, lalu menjalankan simulasinya."
    )

    m.section("5.1 Mengatur distribusi (langkah 37-39)")
    m.text(
        "Kartu **Distribusi Parameter PSA** memuat sepuluh parameter yang disampel. Pada kasus "
        "baru semuanya berstatus **Tetap (tidak disampel)**. Untuk tiap baris, pilih "
        "**Distribusi**, lalu isi salah satu: kolom **SE / SD**, atau **Parameter 1** dan "
        "**Parameter 2** secara langsung."
    )
    m.table(
        ["Baris", "Distribusi", "Yang diketik", "Terisi otomatis"],
        [
            ["Biaya obat (Intervensi, Komparator); Biaya per kejadian; Biaya tambahan lain "
             "(Intervensi, Komparator)", "Gamma", "SE / SD: `10%`",
             "shape 100; scale = nilai dasar / 100"],
            ["Probabilitas kejadian - Intervensi", "Beta", "Parameter 1: `60`; Parameter 2: `140`",
             "SE / SD 0.032323"],
            ["Probabilitas kejadian - Komparator", "Beta", "Parameter 1: `90`; Parameter 2: `110`",
             "SE / SD 0.0350905"],
            ["Utility dasar - Intervensi", "Beta", "SE / SD: `0,06`", "alpha 36.4; beta 10.2666666667"],
            ["Utility dasar - Komparator", "Beta", "SE / SD: `0,06`",
             "alpha 38.8088888889; beta 13.6355555556"],
            ["Disutility kejadian", "Beta", "SE / SD: `0,03`", "alpha 9.9; beta 89.1"],
        ],
        [6.2, 2.0, 4.6, 4.2],
        caption="Distribusi sesuai sheet 05_PSA paket",
    )
    m.steps([
        "Buka tab **PSA** dan gulir ke kartu **Distribusi Parameter PSA**.",
        "Isi kesepuluh baris sesuai Tabel di atas.",
        "Periksa kolom **Mean distribusi**: nilainya harus sama dengan **Nilai dasar**.",
        "Klik **Simpan Distribusi**.",
    ])
    m.callout(
        "Mengapa mengetik 10% dan bukan angka SE dari paket",
        [
            "Paket menulis SE biaya obat per bulan (120.000 untuk ARNI), sedangkan nilai dasar di "
            "dashboard per tahun. Mengetik 120000 berarti SE hanya 0,83% dari nilai dasar. "
            "Mengetik `10%` selalu benar karena dihitung dari nilai dasar yang tersimpan.",
            "Baris kecil di bawah isian SE / SD menampilkan nilai yang terbaca, misalnya "
            "\"= 1.440.000 (10% nilai dasar)\". Bacalah baris itu: titik adalah tanda desimal, "
            "sehingga `600.000` terbaca sebagai 600.",
            "Beta hanya tersedia untuk probabilitas, utility dan disutility. Gamma dan Log-normal "
            "hanya tersedia untuk biaya.",
        ],
        kind="warn",
    )
    m.figure("13-psa-awal", "Kartu distribusi pada kasus baru: semua parameter masih Tetap.",
             max_height_cm=11.0)
    m.figure("14-psa-distribusi", "Kesepuluh distribusi terisi, sebelum disimpan.", max_height_cm=19.5)

    m.section("5.2 Menjalankan PSA (langkah 35, 36 dan 40)")
    m.steps([
        "Pada kartu **Jalankan PSA**, isi **Iterasi** `5000` dan **Seed** `42`.",
        "Klik **Hitung PSA**. Tombol ini tidak aktif selama ada perubahan distribusi yang belum "
        "disimpan.",
        "Ringkasan hasil, bidang cost-effectiveness dan kurva CEAC tampil di bagian atas tab.",
    ])
    m.figure("15-psa-jalankan", "Pengaturan iterasi dan seed.", max_height_cm=3.2)
    m.figure("16-psa-hasil", "Hasil PSA: ringkasan, bidang cost-effectiveness, dan CEAC.",
             max_height_cm=10.5)
    m.table(
        ["Keluaran", "Dashboard", "Kunci instruktur", "Status"],
        [
            ["Probabilitas cost-effective pada WTP Rp300 juta",
             pct(Decimal(str(result["prob_cost_effective_base"])) * 100),
             pct(KEY["psa_prob"] * 100),
             approximate("PSA P(CE)", result["prob_cost_effective_base"], KEY["psa_prob"], "0.05")],
            ["Rata-rata incremental cost", rp(result["mean_incremental_cost"]),
             rp(KEY["psa_mean_cost"]),
             approximate("PSA mean cost", result["mean_incremental_cost"], KEY["psa_mean_cost"], "0.01")],
            ["Rata-rata incremental QALY", num(result["mean_incremental_qaly"], 4),
             num(KEY["psa_mean_qaly"], 4),
             approximate("PSA mean QALY", result["mean_incremental_qaly"], KEY["psa_mean_qaly"], "0.03")],
        ],
        [6.6, 3.4, 3.4, 3.6],
        caption="Hasil PSA dibanding kunci",
    )
    m.text(
        "Angka PSA tidak harus persis sama dengan kunci, karena pembangkit bilangan acak dashboard "
        "berbeda dari yang dipakai menyusun paket. Paket sendiri menyebut selisih beberapa poin "
        "masih wajar. Yang harus sama adalah input, arah dan tafsirannya: hasil deterministik "
        "tampak menguntungkan, tetapi peluang cost-effective hanya sekitar 56%. Dengan seed yang "
        "sama, dashboard selalu memberi angka yang sama."
    )
    m.callout(
        "Bila parameter diubah setelah PSA dijalankan",
        [
            "Tab PSA menampilkan peringatan **Hasil PSA ini tidak lagi sesuai input**. Jalankan "
            "ulang PSA. Contohnya ada pada latihan revisi di Bab 10.",
        ],
    )
