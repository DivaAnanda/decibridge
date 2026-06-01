# DeciBridge — Brief Extraction (Indonesian)

Plain-text extraction of `../../Brief/11052026_Workflow and Steps kerja untuk IT.docx`.
Regenerate by re-running unpack + this script if the docx changes.

---

A. Konsep besar workflow DeciBridge

DeciBridge bekerja per kasus. Satu kasus misalnya:

ARNI vs ACEI pada pasien HFrEF untuk keputusan masuk formularium RS

Setiap kasus akan memiliki:

case metadata: identitas kasus

case pack/evidence layer: bukti klinis dan ekonomi

local input layer: harga obat, biaya RS, LOS, volume pasien, uptake

CEA quick dan BIA: perhitungan ekonomi

EtD appraisal: penilaian KFT per domain

recommendation engine: rekomendasi awal

criteria-based access/CBA: syarat penggunaan bila obat disetujui bersyarat

policy brief: dokumen keputusan otomatis

audit trail dan versioning: jejak keputusan dan perubahan data

Dalam dokumen teknis, sistem harus menjaga pemisahan antara evidence layer dan local input layer, sehingga perubahan harga obat, biaya layanan, volume pasien, atau pola terapi tidak mengubah bukti klinis, tetapi hanya membuat versi input baru dan memperbarui output CEA/BIA.

B. Flowchart utama DeciBridge untuk tim IT

Berikut flowchart dalam bentuk Mermaid. Tim IT bisa menyalin kode ini ke tools yang mendukung Mermaid untuk dijadikan diagram visual.

C. Workflow detail per step untuk diberikan ke tim IT

Saya sarankan memberi tabel ini ke IT, karena lebih jelas untuk diterjemahkan menjadi modul, database, dan API.

Step 1 — User login sesuai role

Komponen

Isi

Tujuan

Memastikan hanya user berwenang yang bisa masuk dan fitur yang tampil sesuai role

Aktor

Admin IT, HTA analyst, Farmasi RS/Sekretaris KFT, KFT member, Ketua KFT/Approver

Input

Username/email, password, role

Proses sistem

Autentikasi user, cek role, tampilkan menu sesuai hak akses

Output

User masuk ke dashboard sesuai role

Database

users, roles, audit_logs

Audit trail

Mencatat user_id, waktu login, status berhasil/gagal, IP/perangkat bila diperlukan

Catatan untuk IT

Admin IT tidak boleh mengubah judgement klinis/EtD; HTA analyst tidak boleh lock keputusan; Ketua KFT/Approver yang boleh approve dan lock decision

Role pengguna dalam dokumen dibagi menjadi Admin IT, HTA Analyst/Farmakoekonomi, Farmasi RS/Sekretaris KFT, KFT Member, dan Ketua KFT/Approver, dengan hak akses berbeda.

Step 2 — Sekretaris KFT/analis HTA membuat atau memilih kasus

Komponen

Isi

Tujuan

Membuat kasus keputusan baru atau membuka kasus yang sudah ada

Aktor

Sekretaris KFT atau HTA analyst

Input

case_id, case_title, technology, comparator, indication, population, setting, perspective, status

Proses sistem

Membuat case baru atau menampilkan case dashboard

Output

Halaman ringkasan kasus/formularium

Database

cases, decision_questions, version_history

Status kasus

Draft, in review, approved, locked, archived

Audit trail

Mencatat siapa membuat/mengubah kasus, field lama, field baru, timestamp

Tampilan UI

Card ringkasan kasus: judul, intervensi, comparator, indikasi, populasi, outcome, status, versi

Contoh isi untuk kasus pilot:

Field

Contoh

case_id

HF_ARNI_ACEI_001

case_title

ARNI vs ACEI pada pasien HFrEF

technology

Sacubitril/valsartan

comparator

ACE inhibitor

indication

Heart failure with reduced ejection fraction

population

Pasien HFrEF rawat jalan/rawat inap sesuai kriteria RS

setting

KFT Rumah Sakit

perspective

Hospital payer/BPJS/rumah sakit

status

Draft

Step 3 — Analis HTA mengunggah workbook Excel atau mengisi data manual

Analis HTA mengunggah file case pack Excel, yaitu DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx, atau mengisi data kasus secara manual melalui form dashboard. File database dictionary tidak diunggah sebagai case, tetapi digunakan oleh tim IT sebagai panduan struktur database dan validasi.

Komponen

Isi

Tujuan

Memasukkan data kasus ke sistem

Aktor

HTA analyst, Farmasi RS/Sekretaris KFT

Input

Workbook Excel standar atau form manual

Proses sistem

Upload wizard: pilih file → preview sheet → validasi → konfirmasi import

Output

Data masuk ke staging untuk divalidasi

Database awal

upload_logs, patient_data_staging, version_history

Artefak audit

File Excel asli disimpan sebagai bukti

Audit trail

Mencatat nama file, hash file, upload_id, version_id, user, waktu upload

Sheet Excel yang dipetakan ke modul DeciBridge meliputi 00_README, 01_case_meta, 02_patient_data_min, 03_variable_dictionary, 04_effect_estimates, 05_cost_inputs, 06_CEA_quick, 07_BIA_inputs, 08_EtD_appraisal, 09_CBA_criteria, 10_references, dan 99_changelog.

Penjelasan detail:

Isi file case pack yang diunggah

File case pack yang diunggah harus berisi data yang akan dibaca sistem, misalnya:

Sheet/komponen

Fungsi

01_case_meta

Identitas kasus: case_id, judul, intervensi, comparator, indikasi, populasi

02_patient_data_min

Data pasien de-identified atau agregat untuk analisis lokal

03_variable_dictionary

Definisi variabel, unit, format, rentang valid

04_effect_estimates

Effect estimate seperti RR/OR/HR, event, outcome

05_cost_inputs

Harga obat dan biaya layanan

06_CEA_quick

Perhitungan cost-effectiveness cepat

07_BIA_inputs

Input budget impact analysis

08_EtD_appraisal

Domain EtD dan judgement

09_CBA_criteria

Criteria-based access

10_references

Sumber bukti dan referensi

99_changelog

Riwayat perubahan workbook

Dokumen teknis juga menegaskan bahwa setiap sheet perlu diterjemahkan menjadi tabel database atau halaman modul, dan setiap upload workbook menghasilkan versi data baru sehingga data lama tidak ditimpa.

Cara kerja real di aplikasi

Pada aplikasi DeciBridge nanti, Step 3 berjalan seperti ini:

Analis HTA login.

Analis membuka case ARNI vs ACEI.

Klik tombol Upload Case Pack Excel.

Upload file DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx.

Sistem membaca sheet di dalam file.

Sistem memvalidasi:

apakah sheet wajib ada,

apakah case_id konsisten,

apakah field wajib kosong atau tidak,

apakah angka ditulis sebagai angka,

apakah proporsi 0–1,

apakah event tidak lebih besar dari total pasien.

Bila valid, data masuk ke database utama.

Bila tidak valid, sistem menampilkan error report.

Dalam dokumen teknis, modul import Excel harus menggunakan upload wizard, menampilkan preview sheet, validasi, konfirmasi import, menyimpan file asli sebagai artefak audit, memberi upload_id dan version_id, serta menaruh data valid ke tabel utama dan data tidak valid ke staging.

Untuk IT, instruksi praktisnya

Kalimat yang bisa Ibu kirim ke IT:

Pada Step 3, yang dimaksud workbook Excel yang diunggah oleh Analis HTA adalah file case pack Excel, yaitu DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx. File ini harus dibaca oleh sistem sebagai input case ARNI vs ACEI. Sistem perlu melakukan import, validasi sheet/field/tipe data/konsistensi, lalu menyimpan data valid ke database dengan case_id = HF_ARNI_ACEI_001 dan version_id baru.

File DeciBridge_Database_Dictionary_MVP_ARNI_vs_ACEI_IT_READY.xlsx tidak diunggah sebagai case; file tersebut digunakan tim IT sebagai blueprint untuk membuat database, tabel, validasi, mapping field, CEA/BIA, EtD appraisal, recommendation rules, CBA, policy brief, versioning, dan audit trail.

Step 4 — Sistem melakukan validasi template, tipe data, rentang nilai, dan konsistensi internal

Step 4 berarti tim IT harus membuat “validation engine”, yaitu mesin pemeriksa otomatis yang mengecek apakah file case pack Excel yang diunggah oleh Analis HTA sudah sesuai template dan aman dimasukkan ke database DeciBridge.

Dalam dokumen “Langkah pembuatan EtD DeciBridge”, aturan import Excel menyebut bahwa sistem harus menerima workbook sesuai template standar, setiap sheet wajib memiliki nama sesuai template, kolom wajib harus divalidasi, data gagal validasi masuk ke status rejected/staging, dan setiap upload menghasilkan versi data baru sehingga data lama tidak ditimpa.

Setelah Analis HTA mengunggah file DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx, sistem harus membaca semua sheet, memeriksa apakah struktur dan isinya benar, lalu menentukan apakah data boleh masuk ke database utama atau harus dikembalikan sebagai error report.

Komponen

Isi

Tujuan

Memastikan data yang diupload tidak salah sebelum masuk database utama

Aktor

Sistem

Input

Workbook Excel atau data manual dari Step 3

Proses sistem

Cek kelengkapan sheet, kolom wajib, tipe data, range, consistency check, referential integrity

Output jika valid

Data siap masuk database utama

Output jika invalid

Error report

Database

validation_logs, patient_data_staging, audit_logs

Audit trail

Mencatat jenis error, lokasi error, user, timestamp

Catatan untuk IT

Data invalid jangan langsung dibuang; simpan di staging/rejected agar bisa diperbaiki

Jenis validasi yang perlu dibuat:

Validasi

Contoh aturan

Pesan error

Kelengkapan sheet

Sheet wajib harus tersedia

“Sheet wajib tidak ditemukan. Harap gunakan template resmi DeciBridge.”

Kelengkapan field

case_id, technology, comparator, outcome utama tidak boleh kosong

“Field case_id kosong pada sheet 01_case_meta.”

Tipe data numerik

Estimate, cost, volume, uptake harus numerik

“Nilai cost_inputs bukan angka.”

Rentang proporsi

Uptake/probabilitas harus 0–1

“Uptake melebihi 1. Gunakan format 0.30.”

Consistency check

events tidak boleh lebih besar dari n

“events_treated lebih besar dari n_treated.”

Referential integrity

case_id harus konsisten antar-sheet

“case_id tidak konsisten antar sheet.”

Aturan import Excel dalam dokumen menyebut bahwa setiap sheet wajib memiliki nama sesuai template, kolom wajib divalidasi, data gagal validasi masuk staging/rejected, dan setiap upload workbook menghasilkan versi data baru tanpa menimpa data lama.

A. Urutan kerja tim IT pada Step 4

1. Sistem menerima file Excel

Tim IT harus membuat fitur upload, misalnya tombol:

Upload Case Pack Excel

Setelah file diunggah, sistem harus mencatat:

Data yang dicatat

Contoh

Nama file

DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx

User uploader

hta_analyst_01

Waktu upload

2026-05-11 10:30

Upload ID

UPLOAD_20260511_001

Case ID

HF_ARNI_ACEI_001

Version ID sementara

v0.1_upload

Status awal

pending_validation

File asli sebaiknya disimpan sebagai artefak audit, sehingga nanti bisa ditelusuri kembali file mana yang menjadi sumber data.

2. Sistem mengecek format file

Validasi paling awal adalah memastikan file benar-benar bisa dibaca.

Validasi

Aturan

Jika gagal

Ekstensi file

Harus .xlsx

Tampilkan error: “Format file tidak didukung. Gunakan file .xlsx.”

File tidak rusak

File bisa dibuka oleh sistem

“File tidak dapat dibaca.”

Ukuran file

Tidak melebihi batas, misalnya 20 MB

“Ukuran file terlalu besar.”

Workbook tidak kosong

Minimal berisi sheet wajib

“Workbook tidak memiliki sheet yang dibutuhkan.”

B. Validasi template workbook

Ini bagian paling penting. Sistem harus memeriksa apakah file Excel yang diupload mengikuti template resmi DeciBridge.

1. Cek nama sheet wajib

Untuk MVP ARNI vs ACEI, sistem minimal perlu mencari sheet berikut:

Sheet

Fungsi

Wajib?

00_SCOPE_FOR_IT

Catatan scope MVP untuk IT

Opsional, tetapi disarankan

01_case_meta

Identitas kasus

Wajib

03_variable_dictionary

Definisi variabel

Wajib

04_effect_estimates

Data effect estimate

Wajib

05_cost_inputs

Harga obat dan biaya layanan

Wajib

06_CEA_quick

Perhitungan CEA cepat

Wajib

07_BIA_inputs

Input BIA

Wajib

08_EtD_appraisal atau etd_session

Domain EtD dan judgement

Wajib untuk tahap EtD

09_CBA_criteria

Criteria-based access

Wajib bila rekomendasi bersyarat

10_references

Referensi

Wajib

99_changelog

Riwayat perubahan

Opsional, tetapi disarankan

Jika sheet wajib tidak ada, sistem harus menolak import.

Contoh error:

Error

Pesan yang muncul

Sheet 01_case_meta tidak ada

“Sheet wajib 01_case_meta tidak ditemukan. Harap gunakan template resmi DeciBridge.”

Sheet 04_effect_estimates tidak ada

“Sheet effect estimates tidak ditemukan. Data evidence tidak dapat diproses.”

Sheet 05_cost_inputs tidak ada

“Sheet cost inputs tidak ditemukan. CEA/BIA tidak dapat dihitung.”

Dokumen teknis menyebut bahwa sheet Excel seperti 01_case_meta, 04_effect_estimates, 05_cost_inputs, 06_CEA_quick, 07_BIA_inputs, 08_EtD_appraisal, 09_CBA_criteria, 10_references, dan 99_changelog perlu diterjemahkan menjadi tabel database atau modul aplikasi.

2. Cek kolom wajib pada setiap sheet

Setelah nama sheet benar, sistem harus memeriksa kolom.

Sheet 01_case_meta

Kolom minimal:

Kolom

Wajib?

Contoh

case_id

Ya

HF_ARNI_ACEI_001

case_title

Ya

ARNI vs ACEI pada pasien HFrEF

technology atau intervention

Ya

Sacubitril/valsartan

comparator

Ya

ACE inhibitor

indication

Ya

HFrEF

population

Ya

Pasien HFrEF

setting

Ya

KFT RS Unud

perspective

Ya

Hospital payer/BPJS

Jika case_id kosong, sistem tidak boleh melanjutkan.

Pesan error:

“Field case_id kosong pada sheet 01_case_meta.”

Sheet 04_effect_estimates

Kolom minimal:

Kolom

Wajib?

Contoh

case_id

Ya

HF_ARNI_ACEI_001

comparison

Ya

ARNI vs ACEI

outcome

Ya

Rehospitalisation within 12 months

metric atau effect_measure

Ya

RR

estimate

Ya

0.6359

lcl_95

Jika ada

0.4363

ucl_95

Jika ada

0.9266

n_treated

Ya

40

n_control

Ya

65

events_treated

Ya

18

events_control

Ya

46

source

Ya

Local RWE / literature

Validasi penting:

n_treated harus angka.

n_control harus angka.

events_treated tidak boleh lebih besar dari n_treated.

events_control tidak boleh lebih besar dari n_control.

estimate harus angka positif.

lcl_95 tidak boleh lebih besar dari ucl_95.

Sheet 05_cost_inputs

Kolom minimal:

Kolom

Wajib?

Contoh

case_id

Ya

HF_ARNI_ACEI_001

parameter_name atau item_name

Ya

Drug cost - ARNI per month

value atau unit_cost

Ya, boleh kosong sementara jika status draft

850000

unit

Ya

IDR/month

source_type atau source

Ya

e-catalog / contract / billing

price_year atau effective_date

Ya

2026

version_id

Ya

v0.1

notes

Opsional

harga masih perlu validasi RS Unud

Untuk tahap MVP, jika harga obat belum tersedia, sistem boleh memberi status:

missing_required_for_final_calculation

Artinya data masih bisa masuk untuk membangun dashboard, tetapi CEA/BIA final belum bisa dihitung.

Sheet 07_BIA_inputs

Kolom minimal:

Kolom

Wajib?

Contoh

case_id

Ya

HF_ARNI_ACEI_001

eligible_population

Ya untuk BIA final

120

uptake

Ya

0.10, 0.30, 0.50

time_horizon

Ya

1 year

scenario_name

Ya

Conservative, Moderate, Aggressive

source

Ya

SIMRS RS Unud / assumption KFT

Validasi penting:

eligible_population harus integer ≥ 0.

uptake harus antara 0 dan 1.

Jika user menulis 30, sistem harus memberi pesan:

“Uptake harus proporsi 0–1. Untuk 30%, isi 0.30.”

Sheet etd_session atau 08_EtD_appraisal

Kolom minimal:

Kolom

Wajib?

Contoh

session_id

Ya

KFT_2026_ARNI_001

meeting_date

Ya

2026-03-05

user_id

Ya

KFT_member1

case_id

Ya

HF_ARNI_ACEI_001

domain

Ya

benefits

rating

Ya

Green

rationale

Ya, terutama untuk Yellow/Red

Manfaat klinis mendukung tetapi biaya masih tinggi

Validasi penting:

Domain harus berasal dari daftar domain resmi.

Rating harus sesuai opsi yang diizinkan.

Rationale tidak boleh kosong untuk rating Yellow atau Red.

C. Validasi tipe data

Tim IT harus membuat sistem yang mengenali tipe data.

Jenis data

Contoh field

Aturan validasi

Text

case_title, population, notes

Tidak boleh kosong jika wajib

Integer

n_treated, n_control, events_treated, eligible_population

Harus bilangan bulat ≥ 0

Decimal

estimate, risk, uptake, probability

Harus angka

Currency

unit_cost, value

Harus angka ≥ 0

Date

meeting_date, effective_date, valid_from

Format tanggal valid

Enum/dropdown

status, rating, recommendation

Harus sesuai pilihan yang ditentukan

Boolean

adjusted, is_final

Ya/tidak atau true/false

Contoh error tipe data:

Kesalahan

Pesan error

unit_cost berisi “belum ada”

“Nilai unit_cost harus berupa angka. Jika data belum tersedia, kosongkan nilai dan isi notes.”

uptake berisi “30%”

“Uptake harus dalam format proporsi, misalnya 0.30.”

meeting_date berisi “minggu depan”

“Tanggal harus dalam format YYYY-MM-DD.”

D. Validasi rentang nilai

Rentang nilai perlu dibuat agar data tidak masuk secara tidak logis.

Field

Rentang valid

Contoh error

uptake

0–1

1.5 tidak valid

probability

0–1

-0.2 tidak valid

risk

0–1

120 tidak valid

n_patients

≥0

-5 tidak valid

n_events

≥0 dan ≤ n_patients

50 event dari 40 pasien tidak valid

unit_cost

≥0

biaya negatif tidak valid

time_horizon_months

>0

0 bulan tidak valid

estimate RR/OR/HR

>0

RR = -0.5 tidak valid

CI lower

>0 dan ≤ CI upper

CI lower lebih besar dari CI upper tidak valid

Contoh pesan:

“Nilai events_treated tidak boleh lebih besar dari n_treated.”

“Nilai uptake melebihi 1. Gunakan proporsi, misalnya 0.30 untuk 30%.”

E. Validasi konsistensi internal

Ini adalah validasi antar-sheet. Tujuannya memastikan data di satu sheet tersambung dengan sheet lain.

1. Konsistensi case_id

Semua sheet harus memakai:

HF_ARNI_ACEI_001

Jika ada sheet yang masih memakai HF_ARNI_vs_ACEI_RWE_ID_2026 atau HF_ARNI_ARB_001, sistem harus menandai error.

Pesan error:

“case_id tidak konsisten. Sheet 04_effect_estimates menggunakan HF_ARNI_vs_ACEI_RWE_ID_2026, sedangkan sheet 01_case_meta menggunakan HF_ARNI_ACEI_001.”

2. Konsistensi intervensi dan comparator

Jika di 01_case_meta tertulis:

Field

Isi

intervention

ARNI

comparator

ACEI

Maka di sheet lain tidak boleh tiba-tiba tertulis comparator ARB untuk case yang sama.

Pesan error:

“Comparator tidak konsisten. Case metadata menyebut ACEI, tetapi sheet effect estimates menyebut ARB.”

3. Konsistensi outcome

Jika outcome utama adalah:

Rehospitalisation within 12 months

Maka outcome ini harus muncul konsisten di:

04_effect_estimates

06_CEA_quick

policy brief mapping

EtD benefits rationale

Jika outcome tidak ditemukan, sistem memberi warning:

“Outcome utama tidak ditemukan pada sheet effect_estimates.”

4. Konsistensi event dan risk

Jika data:

Data

Nilai

n_treated

40

events_treated

18

Maka sistem dapat menghitung:

risk intervention = 18 / 40 = 0.45

Jika di sheet lain risk intervention ditulis 0.70, sistem perlu memberi warning:

“Risk intervention hasil perhitungan berbeda dari nilai yang tercantum. Mohon cek kembali.”

5. Konsistensi CEA/BIA

Sistem harus membandingkan:

hasil hitung Excel,

hasil hitung aplikasi.

Dalam dokumen teknis, verifikasi hasil aplikasi terhadap Excel pembanding harus dilakukan untuk risk comparator, risk intervention, RR, absolute benefit, ICER, dan BIA.

Contoh validasi:

Item

Rumus

Toleransi

Risk comparator

events_control / n_control

selisih < 0.0001

Risk intervention

events_treated / n_treated

selisih < 0.0001

RR

risk_intervention / risk_comparator

selisih < 0.0001

Absolute benefit

risk_comparator - risk_intervention

selisih < 0.0001

ICER

incremental total cost / benefit

sesuai pembulatan rupiah

BIA

population × uptake × incremental cost

sesuai pembulatan rupiah

F. Klasifikasi error: fatal error vs warning

Tim IT sebaiknya membedakan error menjadi dua.

1. Fatal error

Fatal error berarti data tidak boleh masuk ke database utama.

Contoh:

Fatal error

Tindakan sistem

Sheet wajib tidak ada

Tolak import

case_id kosong

Tolak import

case_id tidak konsisten

Tolak import

events > n_patients

Tolak import

Tipe data numerik salah pada field wajib

Tolak import

uptake > 1

Tolak import untuk BIA

Status data:

rejected atau validation_failed

2. Warning

Warning berarti data boleh masuk, tetapi diberi catatan belum final.

Contoh:

Warning

Tindakan sistem

Harga ARNI belum diisi

Data masuk, tetapi CEA/BIA final belum bisa dihitung

Referensi belum lengkap

Data masuk, tetapi evidence summary diberi flag

Rationale EtD belum ada

Data masuk sebagai draft

Approved_by kosong

Belum bisa lock decision

CBA kosong padahal rekomendasi restrict

Belum bisa final policy brief

Status data:

valid_with_warning atau draft_incomplete

G. Error report yang harus dibuat IT

Jika validasi gagal, sistem harus menampilkan error report yang jelas, bukan hanya “file error”.

Format error report minimal:

Kolom error report

Contoh

upload_id

UPLOAD_20260511_001

sheet_name

05_cost_inputs

row_number

7

column_name

unit_cost

error_type

invalid_numeric

current_value

belum ada

expected_format

number, IDR

severity

fatal atau warning

message

unit_cost harus berupa angka

suggested_fix

Isi angka biaya, misalnya 850000, atau kosongkan dan beri notes jika belum tersedia

Sistem juga perlu menyediakan tombol:

Download Error Report Excel

Re-upload Corrected File

View Validation Summary

H. Status setelah validasi

Setelah validasi, sistem harus memberi status.

Kondisi

Status

Semua valid

validation_passed

Valid tetapi ada data belum lengkap

valid_with_warning

Ada kesalahan fatal

validation_failed

Data disimpan sementara

staging

Data ditolak

rejected

Data masuk database utama

imported_to_main_database

Alur teknisnya:

I. Tabel database yang diperlukan untuk Step 4

Minimal IT perlu membuat tabel berikut:

Tabel

Fungsi

upload_logs

Mencatat upload file

validation_logs

Mencatat hasil validasi

staging_case_meta

Menyimpan data sementara sebelum valid

staging_effect_estimates

Menyimpan effect estimate sementara

staging_cost_inputs

Menyimpan input biaya sementara

staging_bia_inputs

Menyimpan input BIA sementara

cases

Database utama identitas kasus

effect_estimates

Database utama effect estimate

cost_inputs

Database utama biaya

bia_inputs

Database utama BIA

version_history

Menyimpan riwayat versi

audit_logs

Mencatat aktivitas user

J. Acceptance criteria untuk tim IT

Step 4 dianggap selesai bila sistem sudah bisa melakukan hal berikut:

Acceptance criteria

Harus bisa?

Upload file .xlsx

Ya

Membaca semua sheet workbook

Ya

Mengecek sheet wajib

Ya

Mengecek kolom wajib

Ya

Mengecek tipe data

Ya

Mengecek rentang nilai

Ya

Mengecek konsistensi case_id antar-sheet

Ya

Mengecek events <= n_patients

Ya

Mengecek uptake antara 0–1

Ya

Menampilkan error report per sheet/baris/kolom

Ya

Membedakan fatal error dan warning

Ya

Menyimpan data invalid ke staging/rejected

Ya

Menyimpan file asli sebagai audit artifact

Ya

Membuat upload_id dan version_id

Ya

Mengizinkan re-upload setelah perbaikan

Ya

Memindahkan data valid ke database utama

Ya

Tidak menimpa data lama

Ya

K. Pesan untuk tim IT

Pada Step 4, sistem DeciBridge harus memiliki validation engine untuk memeriksa workbook case pack Excel sebelum data masuk ke database utama. Validasi meliputi: format file, kelengkapan sheet wajib, kelengkapan kolom wajib, tipe data, rentang nilai, dan konsistensi internal antar-sheet. Sistem harus memeriksa bahwa case_id konsisten di semua sheet, field wajib tidak kosong, nilai numerik benar, uptake/probabilitas berada pada rentang 0–1, event tidak lebih besar dari jumlah pasien, serta outcome/intervention/comparator konsisten dengan case metadata.

Bila terjadi fatal error, data tidak boleh masuk ke database utama dan harus disimpan di staging/rejected dengan error report yang menunjukkan sheet, baris, kolom, jenis kesalahan, nilai saat ini, format yang diharapkan, dan saran perbaikan. Bila hanya ada warning, misalnya harga obat belum tersedia atau approved_by belum diisi, data boleh masuk sebagai draft/valid_with_warning tetapi belum bisa dipakai untuk CEA/BIA final atau lock decision. Setiap upload harus menghasilkan upload_id dan version_id, file asli harus disimpan sebagai artefak audit, dan data lama tidak boleh ditimpa.

Kesimpulan sederhana

Pada Step 4, tugas tim IT adalah membuat sistem yang bisa menjawab:

Apakah file Excel yang diupload adalah template DeciBridge yang benar?

Apakah semua sheet wajib ada?

Apakah semua kolom wajib ada?

Apakah angka, tanggal, teks, dan pilihan dropdown sudah benar?

Apakah nilai masuk akal, misalnya uptake 0–1 dan event tidak melebihi jumlah pasien?

Apakah case_id sama di semua sheet?

Apakah data boleh masuk database utama atau harus diperbaiki dulu?

Jika salah, di bagian mana salahnya dan bagaimana memperbaikinya?

Jadi Step 4 adalah gerbang keamanan data sebelum DeciBridge menghitung CEA/BIA, menampilkan EtD, membuat rekomendasi, dan menghasilkan policy brief.

Step 5 — Sistem menyimpan data ke staging, lalu ke database utama jika valid

Pada tahap ini, sistem DeciBridge tidak langsung memasukkan semua data Excel ke database utama. Sistem harus memakai mekanisme staging dulu, lalu hanya data yang valid yang dipindahkan ke database utama.

Setelah file case pack Excel diupload dan divalidasi pada Step 4, sistem menyimpan data sementara di area staging. Jika data lolos validasi, sistem memindahkan data ke database utama dan memberi version_id. Jika tidak lolos, data tetap di staging/rejected dan user mendapat error report.

Dalam dokumen teknis DeciBridge, data valid harus masuk ke tabel utama, sedangkan data tidak valid tetap berada di staging untuk diperbaiki. Setiap import juga harus diberi upload_id dan version_id, serta file asli disimpan sebagai artefak audit.

Komponen

Isi

Tujuan

Memisahkan data mentah, data valid, dan data final

Aktor

Sistem

Input

Data valid dari validation engine

Proses sistem

Data masuk staging → validasi final → masuk database utama

Output

Case version baru, misalnya v0.1, v0.2, v1.0

Database

cases, clinical_outcomes, effect_estimates, cost_inputs, bia_inputs, references, version_history

Audit trail

Mencatat versi input, user, waktu, sumber data

Catatan untuk IT

Jangan pernah overwrite data lama; setiap perubahan harus menghasilkan version_id baru

Contoh struktur versioning:

Perubahan

Versi

Upload pertama case pack

v0.1

Perbaikan effect estimate

v0.2

Update harga obat

local_input_v0.3

Setelah disetujui KFT

v1.0 locked

A. Apa itu staging?

Staging adalah tempat penyimpanan sementara.

Analogi sederhananya:

Staging itu seperti “meja pemeriksaan dokumen”. File Excel diletakkan dulu di meja ini. Setelah dicek dan dinyatakan benar, baru dimasukkan ke lemari arsip utama/database utama.

Jadi, data dari Excel tidak boleh langsung masuk ke database utama karena bisa saja:

ada sheet kurang,

case_id tidak konsisten,

angka salah format,

harga obat belum tersedia,

events lebih besar dari jumlah pasien,

uptake ditulis 30 bukan 0.30,

field wajib kosong.

Dengan staging, data yang salah tidak merusak database utama.

B. Tujuan Step 5

Step 5 punya 6 tujuan utama:

Tujuan

Penjelasan

Menjaga database utama tetap bersih

Hanya data valid yang boleh masuk

Menyimpan riwayat upload

Setiap file yang diupload punya jejak

Memudahkan koreksi

Data salah bisa dikembalikan ke user dengan error report

Mendukung audit trail

Bisa diketahui siapa upload, kapan, file apa, versi berapa

Mendukung versioning

Setiap upload/update tidak menimpa data lama

Menjamin reproducibility

Keputusan bisa direkonstruksi berdasarkan versi data tertentu

C. Alur teknis Step 5

Berikut flowchart untuk tim IT:

D. Urutan kerja detail untuk tim IT

1. Simpan file asli yang diupload

Begitu file Excel diupload, sistem harus menyimpan file aslinya.

Yang disimpan:

Data

Contoh

Original filename

DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx

File path/storage location

/uploads/casepacks/2026/UPLOAD_001.xlsx

Uploaded by

hta_analyst_01

Uploaded at

2026-05-11 10:30:00

File hash

hash unik untuk memastikan file tidak berubah

Upload status

pending_validation

Kenapa file asli perlu disimpan?

Karena nanti saat audit, sistem bisa membuktikan:

“Keputusan KFT ini dibuat berdasarkan file Excel versi apa?”

2. Buat upload_id

Setiap upload harus punya ID unik.

Contoh:

UPLOAD_20260511_001

Fungsinya:

melacak file upload,

menghubungkan file dengan error report,

menghubungkan file dengan staging data,

menghubungkan file dengan version history.

Contoh tabel upload_logs:

Field

Contoh

upload_id

UPLOAD_20260511_001

case_id

HF_ARNI_ACEI_001

filename

DeciBridge_casepack_MVP_ARNI_vs_ACEI_IT_READY.xlsx

uploaded_by

hta_analyst_01

uploaded_at

2026-05-11 10:30

validation_status

validation_passed / valid_with_warning / validation_failed

file_hash

abc123...

notes

Initial MVP upload

3. Simpan data mentah ke staging tables

Sebelum masuk database utama, data dari setiap sheet disimpan dulu ke tabel staging.

Contoh staging tables:

Sheet Excel

Tabel staging

01_case_meta

staging_case_meta

04_effect_estimates

staging_effect_estimates

05_cost_inputs

staging_cost_inputs

07_BIA_inputs

staging_bia_inputs

08_EtD_appraisal / etd_session

staging_etd_appraisals

09_CBA_criteria

staging_access_criteria

10_references

staging_references

Setiap baris staging sebaiknya punya field tambahan:

Field tambahan

Fungsi

staging_id

ID unik baris staging

upload_id

Menghubungkan ke file upload

case_id

Menghubungkan ke kasus

sheet_name

Asal sheet Excel

row_number

Baris asal di Excel

validation_status

valid/warning/error

error_message

Pesan error jika ada

created_at

Waktu masuk staging

4. Tentukan status validasi

Setelah Step 4 selesai, sistem harus menentukan status data.

Ada tiga kemungkinan:

A. validation_failed

Ini terjadi bila ada fatal error.

Contoh fatal error:

sheet wajib tidak ada,

case_id kosong,

case_id tidak konsisten,

events_treated > n_treated,

uptake > 1,

field numerik wajib berisi teks.

Tindakan sistem:

Tindakan

Keterangan

Data tidak masuk database utama

Tetap di staging/rejected

Error report dibuat

User tahu salahnya di mana

Case status tidak berubah ke in review

Tetap draft/upload failed

User diminta upload ulang

Setelah file diperbaiki

Status:

validation_failed

B. valid_with_warning

Ini terjadi bila data struktur utamanya benar, tetapi ada hal yang belum lengkap untuk finalisasi.

Contoh warning:

harga ARNI belum diisi,

harga ACEI belum diisi,

jumlah pasien eligible belum ada,

approved_by masih kosong,

EtD rationale belum lengkap,

rekomendasi final belum ada.

Tindakan sistem:

Tindakan

Keterangan

Data boleh masuk database utama

Tetapi status case tetap draft/incomplete

Sistem memberi warning

CEA/BIA final atau lock decision belum bisa jalan

User bisa melengkapi nanti

Melalui local input layer atau form EtD

Version tetap dibuat

Misalnya v0.1-draft

Status:

valid_with_warning

C. validation_passed

Ini terjadi bila semua struktur dan isi wajib valid.

Tindakan sistem:

Tindakan

Keterangan

Data masuk database utama

Ya

Version resmi dibuat

Misalnya v0.1

Case dashboard aktif

Ya

Data siap dipakai

Evidence summary, CEA/BIA, EtD

Status:

validation_passed

E. Pindahkan data valid ke database utama

Setelah data valid, sistem memindahkan data dari staging ke tabel utama.

Contoh mapping:

Staging table

Main database table

staging_case_meta

cases

staging_effect_estimates

effect_estimates

staging_cost_inputs

cost_inputs

staging_bia_inputs

bia_inputs

staging_etd_appraisals

etd_appraisals / etd_scores

staging_access_criteria

access_criteria

staging_references

references

Dalam dokumen teknis, database utama perlu menyimpan data evidence, input lokal, judgement EtD, dokumen output, dan audit trail secara terpisah tetapi tetap terhubung melalui case_id dan version_id.

F. Buat version_id

Ini bagian sangat penting.

Setiap data yang masuk database utama harus punya version_id.

Contoh:

Situasi

version_id

Upload awal case pack

v0.1

Revisi data evidence

v0.2

Update harga obat

local_input_v0.3

EtD meeting pertama

etd_session_v0.1

Policy brief final

brief_v1.0

Keputusan terkunci

decision_v1.0_locked

Untuk MVP, boleh dibuat sederhana:

CASE-HF_ARNI_ACEI_001-v0.1

atau:

HF_ARNI_ACEI_001_v0.1

Yang penting:

data lama tidak ditimpa,

perubahan baru selalu jadi versi baru,

setiap output dapat ditelusuri ke versi inputnya.

G. Jangan menimpa data lama

Prinsip penting untuk IT:

Never overwrite locked or previous version data.

Jika ada update harga, sistem jangan mengganti harga lama. Sistem harus membuat record baru.

Contoh:

case_id

parameter

value

version_id

valid_from

status

HF_ARNI_ACEI_001

ARNI monthly cost

850000

v0.1

2026-03-01

archived

HF_ARNI_ACEI_001

ARNI monthly cost

800000

v0.2

2026-05-01

active

Dengan begitu, kalau keputusan KFT dibuat pada Maret, sistem tahu bahwa keputusan itu memakai harga Rp850.000, bukan harga baru Rp800.000.

H. Update status case

Setelah data masuk database utama, sistem harus mengubah status case.

Contoh status case:

Status

Makna

draft

Case baru dibuat, data belum lengkap

uploaded

File berhasil diupload

validation_failed

Ada fatal error

valid_with_warning

Data masuk tetapi belum lengkap

in_review

Case siap ditinjau analis/KFT

ready_for_etd

Evidence dan input lokal cukup untuk EtD

approved

Rekomendasi sudah disetujui

locked

Keputusan final dikunci

archived

Versi lama disimpan

Untuk kondisi sekarang, karena harga obat RS Unud dan BIA final mungkin belum lengkap, status realistis setelah upload adalah:

valid_with_warning atau draft_incomplete

Bukan langsung ready_for_etd.

I. Apa yang harus terjadi jika data tidak valid?

Jika data tidak valid, jangan hapus data. Simpan di staging dan tampilkan error.

Contoh:

Kondisi

Tindakan sistem

case_id kosong

Import gagal, data tetap staging

Sheet 05_cost_inputs hilang

Import gagal

Harga obat kosong

Warning, boleh masuk sebagai draft

uptake = 30

Error, harus 0.30

events = 70, n = 40

Error fatal

approved_by kosong

Warning, belum bisa lock decision

Tampilan ke user:

“Upload berhasil dibaca tetapi belum dapat diproses ke database utama karena terdapat 3 fatal errors dan 5 warnings. Silakan download error report.”

Atau:

“Upload berhasil. Data valid dengan warning: harga ARNI, harga ACEI, dan eligible population belum tersedia. Case disimpan sebagai draft dan dapat dilengkapi melalui local input layer.”

J. Contoh struktur tabel untuk Step 5

1. Tabel upload_logs

Field

Tipe

Contoh

upload_id

text/UUID

UPLOAD_20260511_001

case_id

text

HF_ARNI_ACEI_001

filename

text

casepack.xlsx

uploaded_by

user_id

hta_analyst_01

uploaded_at

datetime

2026-05-11 10:30

file_hash

text

hashvalue123

validation_status

enum

validation_passed

version_id

text

v0.1

2. Tabel validation_logs

Field

Tipe

Contoh

validation_id

text/UUID

VAL_001

upload_id

text

UPLOAD_20260511_001

sheet_name

text

05_cost_inputs

row_number

integer

7

column_name

text

unit_cost

severity

enum

warning

message

text

Harga ARNI belum tersedia

suggested_fix

text

Isi harga ARNI dari e-catalog/kontrak RS Unud

3. Tabel version_history

Field

Tipe

Contoh

version_id

text

HF_ARNI_ACEI_001_v0.1

case_id

text

HF_ARNI_ACEI_001

version_type

enum

case_pack_upload

created_by

user_id

hta_analyst_01

created_at

datetime

2026-05-11 10:35

source_upload_id

text

UPLOAD_20260511_001

status

enum

active_draft

notes

text

Initial MVP case pack import

4. Tabel utama cases

Field

Contoh

case_id

HF_ARNI_ACEI_001

case_title

ARNI vs ACEI pada pasien HFrEF

technology

Sacubitril/valsartan

comparator

ACE inhibitor

indication

HFrEF

population

Pasien HFrEF

status

draft_incomplete

active_version_id

HF_ARNI_ACEI_001_v0.1

K. Pseudocode sederhana untuk IT

Tim IT bisa memahami Step 5 seperti ini:

1. Receive uploaded Excel file.2. Save original file in secure storage.3. Create upload_id.4. Parse workbook sheets.5. Store parsed rows into staging tables.6. Run validation rules.7. If fatal errors exist:      - mark upload as validation_failed      - keep data in staging/rejected      - generate error report      - do not update main tables8. If only warnings exist:      - mark upload as valid_with_warning      - create version_id      - move valid rows to main tables      - mark case as draft_incomplete      - display warning summary9. If no errors/warnings:      - mark upload as validation_passed      - create version_id      - move valid rows to main tables      - mark case as in_review or ready_for_etd10. Write audit log and version history.11. Never overwrite old version; create a new version for each upload/update.

L. Acceptance criteria Step 5

Step 5 dianggap selesai jika sistem sudah mampu:

Acceptance criteria

Harus bisa

Menyimpan file Excel asli

Ya

Membuat upload_id

Ya

Menyimpan data mentah ke staging

Ya

Membedakan validation_failed, valid_with_warning, dan validation_passed

Ya

Menahan data invalid di staging/rejected

Ya

Membuat error report

Ya

Memindahkan hanya data valid ke database utama

Ya

Membuat version_id untuk setiap import

Ya

Tidak menimpa data lama

Ya

Mengubah status case sesuai hasil validasi

Ya

Mencatat aktivitas ke audit log

Ya

Menghubungkan data dengan case_id dan version_id

Ya

M. Pesan untuk tim IT

Pada Step 5, setelah workbook case pack selesai divalidasi, sistem tidak boleh langsung memasukkan semua data ke database utama. Sistem harus menyimpan file asli sebagai audit artifact, membuat upload_id, lalu menyimpan hasil parsing ke staging tables. Jika terdapat fatal error, data tetap berada di staging/rejected, status upload menjadi validation_failed, dan sistem menghasilkan error report. Jika hanya terdapat warning, data dapat dipindahkan ke database utama sebagai draft dengan status valid_with_warning atau draft_incomplete. Jika semua valid, data dipindahkan ke database utama dengan status validation_passed.

Setiap import harus membuat version_id, misalnya HF_ARNI_ACEI_001_v0.1. Data lama tidak boleh ditimpa. Jika ada upload ulang, update harga, atau update evidence, sistem harus membuat versi baru. Semua aktivitas harus dicatat di upload_logs, validation_logs, version_history, dan audit_logs. Data utama harus terhubung melalui case_id dan version_id agar policy brief dan decision record dapat direkonstruksi untuk audit.

Kesimpulan sederhana

Step 5 adalah tahap penyimpanan aman.

Tim IT harus membuat sistem yang:

menyimpan file Excel asli,

menyimpan data sementara di staging,

memindahkan hanya data yang valid ke database utama,

memberi status jika data masih belum lengkap,

membuat upload_id dan version_id,

tidak menimpa data lama,

mencatat semua aktivitas ke audit trail.

Dengan Step 5 ini, DeciBridge menjadi sistem yang rapi, aman, bisa diaudit, dan bisa ditelusuri kembali.

Step 6 — Analis meninjau case pack dan evidence summary, maksudnya: Analis HTA meninjau tampilan case pack digital dan evidence summary di dashboard DeciBridge untuk memastikan PICO, outcome klinis, effect estimate, certainty evidence, asumsi, dan referensi sudah benar sebelum kasus dilanjutkan ke local input layer, CEA/BIA, dan EtD appraisal.

Step 6 adalah tahap ketika Analis HTA memeriksa apakah case pack dan evidence summary yang sudah masuk ke sistem sudah benar, lengkap, dan siap ditampilkan untuk rapat KFT. Jadi ini bukan tahap menghitung biaya dulu; ini tahap review isi bukti klinis/evidence layer sebelum Farmasi RS memperbarui local input layer dan sebelum sistem menjalankan CEA/BIA.

Dalam workflow DeciBridge, Step 6 muncul setelah data selesai di-upload, divalidasi, dan disimpan ke database utama. Setelah itu, Analis HTA meninjau case pack dan evidence summary. Dokumen teknis menyebut isi modul evidence layer/case pack meliputi PICO, clinical evidence, effect estimates, certainty, assumption register, dan references.

Komponen

Isi

Tujuan

Memastikan bukti klinis siap dibahas dalam rapat KFT

Aktor

HTA analyst

Input

PICO, evidence clinical, effect estimates, certainty, assumption register, references

Proses sistem

Tampilkan ringkasan evidence di dashboard

Output

Case pack digital/dashboard-ready

Database

case_pack, evidence_summary, effect_estimates, references, assumptions

Audit trail

Mencatat review evidence, perubahan evidence, dan user

Tampilan UI

Evidence summary card, tabel outcome, certainty rating, daftar referensi

Isi minimal case pack:

Subkomponen

Isi

PICO

Population, intervention, comparator, outcome

Evidence clinical

Guideline, RCT, meta-analysis, local RWE

Effect estimates

RR/OR/HR, absolute risk, event rate

Certainty

High, moderate, low, very low

Assumption register

Asumsi klinis dan ekonomi

References

Guideline/artikel/sumber data

Dokumen menyebut evidence layer/case pack harus berisi PICO, bukti klinis, effect estimates, certainty, assumption register, dan references.

Penjelasan detail:

A. Tujuan Step 6

Tujuan Step 6 adalah memastikan bahwa bukti klinis yang akan dibahas KFT sudah benar.

Pada tahap ini, Analis HTA mengecek:

Apakah kasusnya benar?

Apakah populasi, intervensi, comparator, dan outcome sudah sesuai?

Apakah outcome utama sudah jelas?

Apakah data event dan jumlah pasien benar?

Apakah effect estimate benar?

Apakah ringkasan manfaat dan risiko sudah sesuai bukti?

Apakah certainty evidence sudah diisi?

Apakah asumsi sudah dicatat?

Apakah referensi/sumber bukti sudah jelas?

Apakah case pack sudah layak dibahas di rapat KFT?

B. Siapa yang melakukan Step 6?

Role

Peran

Analis HTA / Farmakoekonomi

Pemeriksa utama case pack dan evidence summary

PI/Ketua Peneliti

Dapat memberi approval akademik/HTA jika diperlukan

Klinisi/Reviewer klinis

Opsional, membantu validasi outcome dan relevansi klinis

Farmasi RS/Sekretaris KFT

Belum fokus di Step 6, tetapi bisa melihat ringkasan kasus

Tim IT

Membuat tampilan dashboard, tombol review, status kelengkapan, dan audit log

Dalam dokumen teknis, role HTA Analyst/Farmakoekonomi memiliki hak akses untuk input case pack, effect estimate, CEA, BIA, dan referensi, tetapi tidak mengunci keputusan final. Keputusan final tetap kewenangan Ketua KFT/Approver.

C. Apa yang harus dibuat tim IT pada Step 6?

Tim IT harus membuat halaman Evidence Review / Case Pack Review di dashboard.

Halaman ini bukan sekadar menampilkan data mentah dari Excel, tetapi harus menampilkan data dalam bentuk yang mudah dibaca oleh Analis HTA dan KFT.

1. Halaman ringkasan kasus

Tampilan awal harus berisi:

Elemen tampilan

Isi

Case ID

HF_ARNI_ACEI_001

Judul kasus

ARNI vs ACEI pada pasien HFrEF

Disease area

Heart failure

Intervensi

ARNI / sacubitril-valsartan

Comparator

ACEI

Indikasi

HFrEF

Populasi target

Pasien HFrEF sesuai kriteria case pack

Setting

KFT RS Unud / rumah sakit

Perspektif

RS/BPJS/payer, sesuai input

Outcome utama

Rehospitalisasi 12 bulan, LOS, dll

Status case

Draft / in review / ready for local input

Version ID

Misalnya HF_ARNI_ACEI_001_v0.1

Dalam dokumen teknis, case dashboard minimal menampilkan ringkasan kasus, status kasus, versi analisis, kelengkapan data, dan aksi utama seperti import Excel, edit case, run CEA/BIA, open EtD, dan generate brief.

2. Tab PICO / Decision Question

Tim IT perlu membuat tab PICO atau Decision Question.

Isi yang harus ditampilkan:

Komponen

Contoh

Population

Pasien HFrEF

Intervention

ARNI

Comparator

ACEI

Outcome

Rehospitalisasi, mortalitas, LOS, efek samping, biaya

Time horizon

12 bulan / 1 tahun

Decision question

Apakah ARNI perlu diadopsi/masuk formularium untuk pasien HFrEF dibanding ACEI di RS Unud?

Output dari tab ini:

Decision question sheet atau ringkasan pertanyaan keputusan.

Dokumen database yang disiapkan untuk EtD menyebut bahwa case pack perlu memuat PICO, sumber evidence, ringkasan manfaat, risiko, certainty evidence, dan catatan asumsi; komponen ini akan menjadi tabel case_pack, evidence_summary, dan references.

3. Tab Evidence Summary

Tim IT perlu membuat tab Evidence Summary.

Tab ini menampilkan ringkasan bukti, bukan seluruh artikel.

Isi minimal:

Komponen

Isi

Sumber evidence

Local RWE, guideline, RCT, meta-analysis

Outcome utama

Rehospitalisasi 12 bulan

Outcome tambahan

LOS, mortalitas, adverse events bila tersedia

Ringkasan manfaat

Misalnya ARNI menurunkan risiko rehospitalisasi dibanding ACEI

Ringkasan risiko

Hipotensi, hiperkalemia, gangguan ginjal

Notes

Catatan keterbatasan data

Evidence source

Referensi/sumber data

Dalam dokumen MVP, fungsi aplikasi harus dapat menampilkan evidence berupa baseline summary, outcomes, rates, effect size/CI bila ada, serta notes/citations.

4. Tab Clinical Outcomes

Tim IT perlu membuat tabel outcome klinis.

Contoh tampilan:

Outcome

Time horizon

ARNI

ACEI

Effect measure

Effect value

Source

Notes

Rehospitalisasi

12 bulan

18/40

46/65

RR

0.636

Local RWE

Data belum disesuaikan confounding

LOS

episode rawat inap

median/mean ARNI

median/mean ACEI

Difference

sesuai data

Local RWE

Dari tanggal masuk-keluar

Data yang harus ditampilkan bisa berasal dari:

clinical_outcomes

effect_estimates

patient_data_min jika ada data agregat/de-identified

references

Untuk tahap awal, data pasien sebaiknya agregat atau de-identified, bukan identitas pasien. Dokumen database menyebut minimal data klinis agregat meliputi case_id, treatment_group, n_patients, n_events, outcome_name, follow_up_period, data_source, dan analysis_type.

5. Tab Effect Estimates

Tim IT perlu menampilkan effect estimate secara jelas.

Isi tabel:

Field

Contoh

comparison

ARNI vs ACEI

outcome

Rehospitalisation within 12 months

metric

RR

estimate

0.6359

lower 95% CI

0.4363

upper 95% CI

0.9266

n_treated

40

n_control

65

events_treated

18

events_control

46

adjusted

No/Yes

source

Local RWE / literature

Dokumen teknis memberikan contoh tabel effect_estimates dengan field comparison, outcome, metric, estimate, confidence interval, jumlah pasien, jumlah event, adjusted, dan source.

Selain tabel, sistem sebaiknya menampilkan ringkasan otomatis:

“Pada outcome rehospitalisasi 12 bulan, kelompok ARNI memiliki 18 event dari 40 pasien, sedangkan kelompok ACEI memiliki 46 event dari 65 pasien. Estimasi efek menunjukkan RR 0,6359, yang menunjukkan risiko rehospitalisasi lebih rendah pada ARNI dibanding ACEI.”

Kalimat otomatis ini bisa menjadi draft evidence summary yang bisa diedit Analis HTA.

6. Tab Certainty Evidence

Tim IT perlu menyediakan field untuk certainty evidence.

Isi minimal:

Outcome

Source

Certainty

Alasan

Rehospitalisasi

Local RWE + literatur pendukung

Low/Moderate

Data observasional, potensi confounding

LOS

Local RWE

Low

Bergantung pada kelengkapan tanggal masuk-keluar

Pilihan certainty:

High

Moderate

Low

Very low

Dokumen teknis menyebut certainty dalam case pack dapat berupa penilaian GRADE-like dengan kategori high, moderate, low, very low.

Untuk IT, field yang diperlukan:

Field

Fungsi

certainty_id

ID unik

case_id

menghubungkan ke kasus

outcome_id

menghubungkan ke outcome

certainty_level

high/moderate/low/very low

certainty_reason

alasan penilaian

reviewed_by

Analis HTA

reviewed_at

tanggal review

7. Tab Assumption Register

Ini penting untuk audit.

Analis HTA harus bisa melihat dan mengedit daftar asumsi.

Contoh:

Asumsi

Keterangan

Sumber

Dampak

Time horizon

Outcome dihitung 12 bulan

case pack

memengaruhi interpretasi outcome

Comparator

ACEI sebagai terapi pembanding utama

formularium/praktik RS

memengaruhi CEA

HF admission cost

menggunakan proxy biaya rawat inap

billing/proxy data

memengaruhi cost offset

Data source

outcome berasal dari local RWE

RM/SIMRS

potensi bias/confounding

Dokumen teknis menyebut assumption register sebagai bagian dari evidence layer/case pack, dengan output daftar asumsi yang bisa diaudit.

8. Tab References

Tim IT perlu membuat tab referensi.

Isi minimal:

Reference ID

Jenis sumber

Judul/sumber

Tahun

Link/DOI/file

Digunakan untuk

REF001

Guideline

Heart failure guideline

2022/2023

DOI/link

rekomendasi klinis

REF002

Local data

Data RS Sanglah/Tabanan/Unud

2026

file/internal

outcome lokal

REF003

RCT/meta-analysis

Studi ARNI

tahun

DOI

effect estimate pendukung

References dibutuhkan agar policy brief dan audit trail tidak hanya menampilkan angka, tetapi juga sumber bukti. Dalam pemetaan workbook, sheet 10_references berfungsi sebagai sumber bukti dan referensi, lalu masuk ke tabel references.

D. Apa yang dilakukan Analis HTA di Step 6?

Analis HTA bukan hanya melihat tampilan. Ia harus melakukan review dan sign-off awal.

Checklist review Analis HTA

Yang dicek

Pertanyaan review

Status

Case metadata

Apakah judul, intervensi, comparator, dan populasi sudah benar?

Pass/revise

PICO

Apakah PICO sesuai pertanyaan keputusan KFT?

Pass/revise

Outcome utama

Apakah outcome utama sudah relevan untuk KFT?

Pass/revise

Clinical outcomes

Apakah angka event dan jumlah pasien benar?

Pass/revise

Effect estimate

Apakah RR/OR/HR/risk difference sudah benar?

Pass/revise

Certainty

Apakah tingkat kepastian bukti sudah diisi?

Pass/revise

Benefits

Apakah ringkasan manfaat sesuai data?

Pass/revise

Harms/safety

Apakah risiko utama sudah disebutkan?

Pass/revise

Assumptions

Apakah asumsi penting sudah dicatat?

Pass/revise

References

Apakah sumber bukti sudah dicantumkan?

Pass/revise

Dashboard readiness

Apakah case pack siap dibahas di KFT?

Ready / not ready

E. Status yang harus tersedia di sistem

Setelah review, Analis HTA harus bisa memberi status:

Status

Makna

evidence_draft

Evidence masih awal

needs_revision

Ada bagian yang perlu diperbaiki

evidence_reviewed

Evidence sudah ditinjau Analis HTA

clinically_reviewed

Sudah ditinjau reviewer klinis, jika ada

ready_for_local_input

Evidence siap dilanjutkan ke input harga/biaya RS

ready_for_etd

Evidence dan local input cukup untuk masuk ke EtD appraisal

Untuk kondisi Ibu saat ini, status setelah Step 6 kemungkinan:

evidence_reviewed atau ready_for_local_input

Bukan langsung ready_for_etd, karena data biaya lokal RS Unud, eligible population, dan uptake masih sedang dilengkapi.

F. Apa yang harus ditampilkan dalam UI Step 6?

Tim IT perlu membuat halaman dengan struktur seperti ini:

Case Pack Review Page[Header]Case ID: HF_ARNI_ACEI_001Case title: ARNI vs ACEI pada pasien HFrEFStatus: Draft / Evidence reviewedVersion: v0.1Last updated: tanggal[Checklist Kelengkapan]✓ Case metadata✓ PICO✓ Clinical outcomes✓ Effect estimates✓ Certainty✓ Assumption register✓ References⚠ Cost inputs incomplete⚠ BIA inputs incomplete[Tabs]1. Overview2. PICO / Decision question3. Evidence summary4. Clinical outcomes5. Effect estimates6. Certainty evidence7. Assumption register8. References9. Reviewer comments[Actions]- Edit evidence summary- Add reviewer comment- Mark as needs revision- Mark evidence reviewed- Send to local input layer- View version history

G. Tombol/aksi yang harus dibuat IT

Tombol

Fungsi

Role yang boleh

View case pack

Melihat case pack digital

HTA analyst, Farmasi RS, KFT member

Edit evidence summary

Mengedit ringkasan bukti

HTA analyst

Edit certainty

Mengedit certainty evidence

HTA analyst

Add reference

Menambah referensi

HTA analyst

Add reviewer comment

Memberi catatan review

HTA analyst/reviewer klinis

Mark needs revision

Menandai perlu revisi

HTA analyst

Mark evidence reviewed

Menandai evidence sudah ditinjau

HTA analyst/PI

Send to local input layer

Melanjutkan ke Step 7

HTA analyst

View audit trail

Melihat riwayat perubahan

sesuai role

Export case pack PDF/Word

Export ringkasan evidence

HTA analyst/sekretariat

H. Database/tabel yang dibutuhkan untuk Step 6

Minimal tabel yang digunakan:

Tabel

Fungsi

cases

Identitas kasus

case_pack

Ringkasan PICO dan evidence summary

clinical_outcomes

Outcome klinis

effect_estimates

RR/OR/HR/risk difference

certainty_assessments

Kepastian bukti per outcome

assumption_register

Daftar asumsi

references

Sumber bukti

review_comments

Komentar Analis HTA/reviewer

review_status

Status review case pack

version_history

Riwayat versi

audit_logs

Jejak aktivitas

Dokumen database yang disiapkan untuk IT juga menyebut struktur minimal database DeciBridge meliputi cases, case_pack, clinical_outcomes, effect_estimates, cost_inputs, cea_results, bia_inputs, bia_results, etd_domains, etd_rubrics, etd_appraisals, recommendation_rules, recommendations, access_criteria, policy_briefs, references, version_history, dan audit_logs.

I. Audit trail pada Step 6

Setiap perubahan evidence harus tercatat.

Aktivitas yang dicatat:

Aktivitas

Data yang dicatat

Membuka case pack

user_id, case_id, timestamp

Mengedit evidence summary

field lama, field baru, user, timestamp

Mengubah certainty

certainty lama, certainty baru, alasan, user

Menambah referensi

reference_id, sumber, user

Menambah asumsi

assumption_id, user

Mark evidence reviewed

reviewer, tanggal, status

Send to local input layer

user, case_id, version_id, timestamp

Ini penting karena case pack adalah bagian dari evidence layer. Jika evidence berubah, sistem harus dapat menunjukkan:

“Apa yang berubah, siapa yang mengubah, kapan, dan versi mana yang digunakan saat keputusan KFT dibuat?”

J. Hubungan Step 6 dengan Step berikutnya

Step 6 menghasilkan case pack yang sudah direview.

Baru setelah itu:

Step berikutnya

Apa yang menggunakan hasil Step 6

Step 7 local input layer

Menggunakan case_id dan outcome dari case pack

Step 8 CEA/BIA

Menggunakan effect estimate dan outcome klinis

Step 9 EtD appraisal

Domain benefits, harms, certainty mengambil ringkasan dari Step 6

Step 12 policy brief

Ringkasan bukti klinis, manfaat-risiko, dan certainty otomatis masuk policy brief

Dalam struktur policy brief otomatis, bagian “Pertanyaan keputusan” mengambil PICO, “Ringkasan bukti klinis” mengambil effect estimate, outcome utama, dan certainty, sedangkan “Ringkasan manfaat-risiko” mengambil benefits, harms, dan safety monitoring.

K. Contoh output Step 6 untuk kasus ARNI vs ACEI

Contoh tampilan evidence summary yang diharapkan:

Bagian

Isi contoh

Case ID

HF_ARNI_ACEI_001

Decision question

Apakah ARNI perlu diadopsi untuk pasien HFrEF dibanding ACEI di RS Unud?

Population

Pasien HFrEF

Intervention

ARNI

Comparator

ACEI

Main outcome

Rehospitalisasi dalam 12 bulan

Evidence source

Local RWE dari RS dan/atau literatur pendukung

Effect estimate

RR 0,6359

Clinical interpretation

ARNI menunjukkan risiko rehospitalisasi lebih rendah dibanding ACEI

Certainty

Low/Moderate, sesuai penilaian Analis HTA

Key harms

Hipotensi, hiperkalemia, gangguan ginjal

Assumptions

Outcome dihitung 12 bulan; biaya lokal akan diperbarui dari RS Unud

Review status

Evidence reviewed / ready for local input

L. Acceptance criteria Step 6 untuk IT

Step 6 dianggap selesai jika sistem sudah bisa:

Acceptance criteria

Harus bisa

Menampilkan case metadata

Ya

Menampilkan PICO/decision question

Ya

Menampilkan clinical outcomes

Ya

Menampilkan effect estimates

Ya

Menampilkan certainty evidence

Ya

Menampilkan assumption register

Ya

Menampilkan references

Ya

Memberi checklist kelengkapan evidence

Ya

Mengizinkan Analis HTA memberi komentar review

Ya

Mengizinkan Analis HTA mengubah status menjadi evidence_reviewed

Ya

Mengizinkan status needs_revision bila ada masalah

Ya

Menyimpan semua perubahan ke audit log

Ya

Menghubungkan case pack dengan case_id dan version_id

Ya

Menandai case siap masuk local input layer

Ya

Menyediakan data evidence untuk EtD dan policy brief

Ya

M. Pseudocode sederhana untuk tim IT

1. User opens case HF_ARNI_ACEI_001.2. System checks user role.3. If role = HTA Analyst or authorized reviewer:      show Case Pack Review page.4. System loads:      - case metadata from cases      - PICO from case_pack      - clinical outcomes from clinical_outcomes      - effect estimates from effect_estimates      - certainty from certainty_assessments      - assumptions from assumption_register      - references from references5. System displays evidence completeness checklist.6. Analyst reviews each section.7. Analyst may:      - edit evidence summary      - edit certainty      - add assumption      - add reference      - add reviewer comment8. System saves each edit with case_id, version_id, user_id, timestamp.9. Analyst selects:      - needs_revision, or      - evidence_reviewed, or      - ready_for_local_input10. System updates case status and writes audit log.11. If ready_for_local_input:      enable Step 7 local input layer.

N. Pesan untuk tim IT

Pada Step 6, sistem harus menyediakan halaman Case Pack Review / Evidence Summary untuk Analis HTA. Halaman ini digunakan setelah workbook case pack lolos validasi dan data masuk ke database utama. Sistem harus menampilkan case metadata, PICO/decision question, clinical outcomes, effect estimates, certainty evidence, assumption register, dan references berdasarkan case_id dan version_id.

Analis HTA harus dapat meninjau apakah evidence sudah lengkap dan benar, memberi komentar, memperbaiki ringkasan evidence bila diperlukan, mengubah certainty evidence, menambah asumsi atau referensi, lalu memberi status needs_revision, evidence_reviewed, atau ready_for_local_input. Semua perubahan harus tercatat di audit log dan version history. Output Step 6 adalah case pack digital yang sudah direview dan siap digunakan untuk Step 7 local input layer, Step 8 CEA/BIA, Step 9 EtD appraisal, dan Step 12 policy brief.

Kesimpulan sederhana

Step 6 adalah tahap review evidence oleh Analis HTA.

Untuk tim IT, yang harus dibuat adalah:

halaman Case Pack Review;

tampilan PICO/decision question;

tampilan clinical outcomes;

tampilan effect estimates;

tampilan certainty evidence;

tampilan assumption register;

tampilan references;

checklist kelengkapan evidence;

fitur komentar dan status review;

audit log setiap perubahan.

Setelah Step 6 selesai, case belum langsung menjadi keputusan KFT. Case baru dianggap siap masuk Step 7, yaitu pengisian local input layer oleh Farmasi RS, seperti harga obat, biaya rawat inap, volume pasien eligible, dan uptake.

Step 7 — Farmasi RS mengisi atau memperbarui local input layer, maksudnya: Farmasi RS/Sekretariat KFT mengisi atau memperbarui parameter lokal RS, seperti harga obat, biaya layanan, biaya rawat inap, biaya monitoring, volume pasien eligible, pola terapi, dan skenario uptake. Sistem harus menyimpan setiap perubahan sebagai versi baru, tanpa mengubah evidence layer/case pack.

Prinsip utamanya: evidence layer dan local input layer harus dipisahkan. Bukti klinis seperti PICO, outcome, effect estimate, dan certainty tidak berubah ketika harga obat atau biaya RS berubah. Perubahan harga/biaya hanya membuat versi input lokal baru dan memperbarui output CEA/BIA. Dokumen DeciBridge memang menegaskan bahwa perubahan harga obat, biaya layanan, volume pasien, atau pola terapi tidak boleh mengubah struktur bukti, tetapi harus menghasilkan versi input baru dan memperbarui biaya/BIA secara transparan.

Komponen

Isi

Tujuan

Memasukkan data lokal RS yang bisa berubah dari waktu ke waktu

Aktor

Farmasi RS/Sekretaris KFT

Input

Harga obat, biaya event, biaya monitoring, volume pasien eligible, uptake

Proses sistem

User input/edit local parameters; sistem menyimpan sumber, tanggal berlaku, dan versi

Output

Local input layer versi baru

Database

cost_inputs, bia_inputs, version_history, audit_logs

Audit trail

Mencatat nilai lama, nilai baru, sumber, tanggal berlaku, user, timestamp

Catatan penting

Perubahan harga tidak boleh mengubah evidence layer

Isi local input layer:

Input lokal

Sumber

Validasi

Harga obat ARNI per bulan

e-catalog/kontrak RS/pengadaan

Numerik, IDR/month, tahun harga

Harga obat comparator per bulan

e-catalog/kontrak RS/pengadaan

Numerik, IDR/month

Biaya rawat inap HF per event

Billing/unit cost RS

Numerik, IDR/event

Biaya rawat jalan/monitoring

Tarif RS/BPJS/laboratorium

Numerik, IDR/visit atau IDR/test

Volume pasien eligible

SIMRS/HIS/klinik

Integer, periode jelas

Uptake intervensi

Skenario KFT

Proporsi 0–1 atau persen dikonversi

A. Apa yang dimaksud local input layer?

Local input layer adalah bagian aplikasi tempat pengguna RS memasukkan data yang bersifat lokal dan bisa berubah dari waktu ke waktu.

Contohnya:

harga ARNI di RS Unud,

harga ACEI di RS Unud,

biaya rawat inap gagal jantung di RS Unud,

biaya kontrol rawat jalan,

biaya lab monitoring,

jumlah pasien HFrEF eligible per tahun,

pola terapi saat ini,

skenario uptake jika ARNI masuk formularium.

Jadi, local input layer bukan data bukti klinis, tetapi data lokal RS yang dipakai untuk menghitung dampak biaya dan budget impact.

Dalam dokumen teknis, local input layer disebut sebagai modul yang memuat harga obat, biaya layanan, LOS, volume eligible, dan uptake.

B. Siapa yang mengisi Step 7?

Role

Tugas

Farmasi RS / Sekretariat KFT

Mengisi harga obat, sumber harga, tanggal harga, pola terapi, data pengadaan/formularium

Unit Keuangan/Billing RS

Memberikan biaya layanan, biaya rawat inap, biaya rawat jalan, biaya monitoring

SIMRS/HIS/Rekam Medis

Memberikan volume pasien eligible, LOS, pola terapi agregat

Analis HTA/Farmakoekonomi

Membantu memeriksa apakah input lokal masuk akal dan siap dipakai untuk CEA/BIA

Tim IT

Membuat form input, validasi, versioning, audit log, dan koneksi ke CEA/BIA engine

Dalam proposal, sumber data lokal memang diarahkan ke RS Universitas Udayana: Instalasi Farmasi untuk harga obat dan perubahan harga, Unit Keuangan/Billing untuk unit cost dan biaya rawat inap, SIMRS/HIS untuk LOS, volume pasien, dan pola terapi agregat.

C. Apa yang harus dibuat tim IT pada Step 7?

Tim IT harus membuat halaman Local Input Layer di dashboard DeciBridge.

Halaman ini sebaiknya memiliki beberapa tab:

Local Input Layer Page[Header]Case ID: HF_ARNI_ACEI_001Case title: ARNI vs ACEI pada pasien HFrEFEvidence version: evidence_v0.1Local input version: local_input_v0.1Status: draft / complete / active[Tabs]1. Drug price inputs2. Event/service cost inputs3. Monitoring cost inputs4. Eligible population & uptake5. Current treatment pattern6. Sensitivity scenario7. Source & notes8. Version history[Actions]- Add input- Edit input- Save as draft- Validate local inputs- Create new local input version- Set as active version- Run CEA/BIA- View audit trail

D. Data yang harus diinput dalam local input layer

1. Harga obat

Ini bagian paling penting untuk ARNI vs ACEI.

Field

Contoh isi

Wajib?

Catatan validasi

case_id

HF_ARNI_ACEI_001

Ya

Harus sama dengan case

input_category

drug_price

Ya

Dropdown

item_name

Sacubitril/valsartan

Ya

Nama obat/intervensi

item_role

intervention

Ya

intervention/comparator

unit_cost

850000

Ya untuk final

Harus numerik ≥0

unit

IDR/month

Ya

IDR/tablet, IDR/month, IDR/year

dose_assumption

sesuai dosis praktik RS

Ya

teks/asumsi

annual_cost

otomatis

Sistem

monthly_cost × 12

source_type

e-catalog / contract / procurement

Ya

Dropdown

source_detail

e-catalog 2026 / kontrak RS Unud

Ya

teks

effective_date

2026-05-01

Ya

tanggal valid

price_year

2026

Ya

tahun

notes

harga perlu validasi instalasi farmasi

Opsional

teks

Untuk ARNI vs ACEI, minimal harus ada:

Obat

Role

ARNI / sacubitril-valsartan

Intervention

ACEI, misalnya ramipril/enalapril/lisinopril sesuai formularium RS

Comparator

Dalam dokumen teknis MVP, cost inputs harus editable dan mencatat drug unit price intervensi, drug unit price comparator, dosis atau cost per month, price source, dan price date.

2. Biaya event klinis

Biaya event adalah biaya yang berhubungan dengan outcome klinis, misalnya rawat inap gagal jantung.

Field

Contoh isi

Wajib?

case_id

HF_ARNI_ACEI_001

Ya

input_category

event_cost

Ya

event_cost_name

HF admission

Ya

unit_cost

6889093

Ya untuk model saat ini

unit

IDR/admission

Ya

cost_type

mean / median / tariff / INA-CBG / billing

Ya

source_type

billing / unit cost / INA-CBG / proxy

Ya

source_detail

Billing RS Unud 2026

Ya

cost_year

2026

Ya

notes

digunakan untuk cost-offset rehospitalisasi

Opsional

Untuk kasus ARNI vs ACEI, biaya ini dipakai untuk menghitung hospitalisation cost offset, yaitu potensi biaya rawat inap yang dapat dihindari jika rehospitalisasi berkurang.

3. Biaya monitoring

ARNI biasanya membutuhkan monitoring tekanan darah, fungsi ginjal, dan kalium. Biaya ini bisa dibuat opsional untuk MVP, tetapi sebaiknya disediakan form-nya.

Field

Contoh

monitoring_item

Kreatinin/eGFR

unit_cost

tarif lab RS

unit

IDR/test

frequency

1–2 kali setelah inisiasi/titrasi

source

Tarif lab RS Unud

notes

dipakai untuk CBA/monitoring plan

Contoh monitoring:

Monitoring

Unit

Kreatinin/eGFR

IDR/test

Kalium

IDR/test

Tekanan darah

IDR/visit atau bagian dari kunjungan

Kunjungan rawat jalan

IDR/visit

4. Volume pasien eligible

Ini dipakai untuk BIA.

Field

Contoh isi

Wajib?

case_id

HF_ARNI_ACEI_001

Ya

input_category

eligible_population

Ya

eligible_population

120

Ya untuk BIA

period

per year

Ya

data_year

2026

Ya

source_type

SIMRS / HIS / registry / estimate

Ya

source_detail

SIMRS RS Unud, pasien HFrEF 2025

Ya

inclusion_definition

HFrEF sesuai kriteria case pack

Ya

notes

data agregat, tanpa identitas pasien

Opsional

Dokumen database menyebut bahwa data biaya lokal dapat disiapkan dari Instalasi Farmasi, Keuangan/Billing, SIMRS, atau tarif RS; sedangkan local input penting karena menjadi dasar modul biaya.

5. Uptake intervensi

Uptake adalah perkiraan persentase pasien eligible yang akan memakai ARNI jika masuk formularium.

Field

Contoh

scenario_name

Conservative

uptake_proportion

0.10

description

10% pasien eligible menggunakan ARNI

source

Asumsi KFT

notes

skenario awal untuk BIA

Minimal buat 3 skenario:

Skenario

Uptake

Conservative

0.10

Moderate

0.30

Aggressive

0.50

Dalam dokumen teknis, BIA menggunakan target population dan uptake proportion, dengan skenario conservative/moderate/aggressive atau 10/30/50%.

6. Pola terapi saat ini

Ini tidak selalu wajib untuk CEA quick, tetapi sangat membantu untuk BIA dan policy brief.

Field

Contoh

current_treatment

ACEI

n_current_users

jumlah pasien

proportion_current_users

proporsi pasien

source

SIMRS/Farmasi

period

2025/2026

notes

pola terapi sebelum ARNI diadopsi

Contoh:

Terapi

Jumlah pasien/tahun

Sumber

ACEI

80

Farmasi/SIMRS

ARB

35

Farmasi/SIMRS

ARNI

5

Farmasi/SIMRS

E. Validasi yang harus dibuat IT pada Step 7

Tim IT harus membuat validasi khusus untuk local input.

Field

Aturan validasi

unit_cost

harus numerik ≥0

eligible_population

integer ≥0

uptake_proportion

harus 0–1

effective_date

format tanggal valid

source_type

harus dipilih

unit

harus sesuai kategori, misalnya IDR/month untuk obat

case_id

harus sama dengan case aktif

version_id

wajib dibuat otomatis

annual_cost

dihitung otomatis jika monthly cost tersedia

valid_from

tidak boleh kosong untuk harga final

notes

wajib jika data berupa proxy/asumsi

Contoh error/warning:

Kondisi

Jenis

Pesan

Harga ARNI kosong

Warning

“Harga ARNI belum tersedia; CEA/BIA final belum dapat dihitung.”

unit_cost = -5000

Fatal error

“Biaya tidak boleh bernilai negatif.”

uptake = 30

Fatal error

“Uptake harus dalam format proporsi 0–1. Gunakan 0.30 untuk 30%.”

Sumber harga kosong

Warning/fatal untuk final

“Sumber harga wajib diisi sebelum local input dikunci.”

Tanggal harga kosong

Warning/fatal untuk final

“Effective date wajib diisi untuk versioning.”

Unit salah

Fatal error

“Unit untuk harga obat bulanan harus IDR/month.”

F. Versioning pada Step 7

Ini sangat penting.

Harga obat dan biaya RS bisa berubah. Sistem tidak boleh menimpa data lama. Setiap perubahan harus menjadi versi baru.

Contoh:

local_input_version

Parameter

Nilai

Status

local_input_v0.1

ARNI monthly cost

850000

archived

local_input_v0.2

ARNI monthly cost

800000

active

local_input_v0.3

HF admission cost

7000000

draft

Jika harga ARNI berubah, sistem harus:

menyimpan nilai lama,

membuat record baru,

memberi version_id baru,

mencatat siapa mengubah,

mencatat alasan/sumber perubahan,

menjalankan ulang CEA/BIA bila diminta.

Proposal DeciBridge juga menekankan adanya parameter versioning untuk menjaga keterlacakan perubahan input lokal.

G. Audit trail pada Step 7

Setiap perubahan local input harus tercatat.

Aktivitas

Data yang dicatat

Tambah harga obat

user, case_id, item, nilai, sumber, tanggal

Ubah harga obat

nilai lama, nilai baru, user, timestamp

Ubah biaya rawat inap

nilai lama, nilai baru, sumber

Ubah eligible population

nilai lama, nilai baru, periode data

Ubah uptake

skenario lama, skenario baru

Set active version

version lama, version baru, user

Run CEA/BIA setelah update

input version yang dipakai, waktu run

Dalam dokumen teknis, audit trail wajib mencatat perubahan harga/biaya berupa nilai lama, nilai baru, sumber, dan tanggal berlaku.

H. Database/tabel yang dibutuhkan untuk Step 7

Minimal IT perlu membuat tabel ini:

Tabel

Fungsi

local_input_versions

Menyimpan versi local input

cost_inputs

Harga obat, biaya layanan, biaya event

drug_price_inputs

Bisa dipisah jika ingin lebih rapi

event_cost_inputs

Biaya rawat inap/event klinis

monitoring_cost_inputs

Biaya lab/monitoring

bia_inputs

Eligible population, uptake, horizon

current_treatment_patterns

Pola terapi saat ini

input_sources

Sumber data harga/biaya/volume

audit_logs

Jejak perubahan

version_history

Riwayat versi input

Dalam dokumen teknis, tabel cost_inputs memuat parameter_name, value, unit, source_type, price_year, version_id, valid_from, dan notes.

Flowchart Step 7

J. Status local input yang perlu dibuat

Status

Makna

draft

Data sedang diisi

incomplete

Ada input wajib belum lengkap

valid_with_warning

Bisa dipakai sementara, tetapi belum final

validated

Sudah dicek dan lengkap

active

Versi ini dipakai untuk CEA/BIA

archived

Versi lama disimpan

locked_with_decision

Versi ini dipakai dalam keputusan final KFT

Untuk kondisi sekarang, karena Ibu masih mencari data hari 3–14, status awal bisa dibuat:

local_input_v0.1_draft atau valid_with_warning

Setelah harga RS Unud, biaya rawat inap, eligible population, dan uptake lengkap, status bisa menjadi:

active_for_analysis

K. Output Step 7

Output Step 7 adalah local input version yang siap dipakai untuk CEA/BIA.

Minimal output:

Output

Isi

local_input_version_id

HF_ARNI_ACEI_001_local_v0.1

Drug price table

harga ARNI dan ACEI

Event cost table

biaya rawat inap HF

Monitoring cost table

biaya lab/kontrol jika tersedia

BIA input table

eligible population dan uptake

Source log

sumber dan tanggal data

Validation result

valid / warning / error

Audit log

siapa mengubah apa dan kapan

L. Hubungan Step 7 dengan Step 8

Step 7 harus menghasilkan input yang akan dipakai Step 8.

Input dari Step 7

Dipakai untuk Step 8

Harga ARNI per tahun

Incremental drug cost

Harga ACEI per tahun

Incremental drug cost

Biaya rawat inap HF

Hospitalisation cost offset

Eligible population

BIA

Uptake

BIA scenario

Monitoring cost

Bisa ditambahkan ke total cost

Version ID

Audit dan reproducibility

Rumus yang akan digunakan Step 8:

Komponen

Rumus

Incremental drug cost

annual drug cost ARNI − annual drug cost ACEI

Hospitalisation cost offset

rehospitalisation avoided × hospitalisation cost per event

Incremental total cost

incremental drug cost − hospitalisation cost offset

Budget impact

target population × uptake × incremental total cost per patient-year

CEA quick dan BIA dalam dokumen teknis memang menggunakan harga obat, biaya rawat inap, eligible population, dan uptake dari local input layer.

M. Contoh tampilan form untuk IT

LOCAL INPUT LAYER: HF_ARNI_ACEI_001Section 1. Drug Price Inputs- ARNI monthly cost: [________] IDR/month- ACEI monthly cost: [________] IDR/month- Source: [e-catalog / contract / RS procurement / other]- Effective date: [YYYY-MM-DD]- Notes: [________]Section 2. Event Cost Inputs- HF admission cost: [________] IDR/admission- Source: [billing / INA-CBG / unit cost / proxy]- Cost year: [YYYY]- Notes: [________]Section 3. Monitoring Cost Inputs- Creatinine/eGFR cost: [________] IDR/test- Potassium cost: [________] IDR/test- Outpatient visit cost: [________] IDR/visitSection 4. Eligible Population & Uptake- Eligible HFrEF patients/year: [________]- Conservative uptake: [0.10]- Moderate uptake: [0.30]- Aggressive uptake: [0.50]Section 5. Versioning- Current local input version: local_v0.1- Save as new version: [Yes/No]- Set as active for CEA/BIA: [Yes/No]Buttons:[Save Draft] [Validate Inputs] [Create New Version] [Run CEA/BIA] [View Audit Trail]

N. Acceptance criteria Step 7 untuk tim IT

Step 7 dianggap selesai jika sistem sudah bisa:

Acceptance criteria

Harus bisa

Menampilkan halaman local input layer per case

Ya

Menginput harga ARNI dan ACEI

Ya

Menginput biaya rawat inap HF

Ya

Menginput biaya monitoring

Ya, minimal opsional

Menginput eligible population

Ya

Menginput uptake 10/30/50%

Ya

Menyimpan sumber data dan effective date

Ya

Memvalidasi angka, tanggal, unit, dan proporsi

Ya

Membuat local input version baru

Ya

Menyimpan nilai lama dan nilai baru

Ya

Tidak mengubah evidence layer

Ya

Menetapkan active local input version

Ya

Menghubungkan local input dengan case_id dan version_id

Ya

Mencatat audit trail

Ya

Memberi warning bila data belum lengkap

Ya

Mengirim data valid ke Step 8 CEA/BIA

Ya

O. Pseudocode sederhana untuk tim IT

1. User opens case HF_ARNI_ACEI_001.2. System checks role:      if role is Farmasi RS, Sekretariat KFT, or HTA Analyst:          allow local input edit      else:          view only3. System displays current active local_input_version.4. User enters or updates:      - drug price intervention      - drug price comparator      - event cost      - monitoring cost      - eligible population      - uptake scenarios      - source and effective date5. System validates:      - numeric values      - date format      - uptake 0-1      - required source      - unit consistency6. If validation fails:      show error and keep as draft.7. If valid or valid_with_warning:      create new local_input_version.8. Save data to cost_inputs and bia_inputs.9. Record audit log:      old value, new value, user, timestamp, source.10. If user sets version as active:      mark previous active version as archived.11. Enable Run CEA/BIA button for Step 8.

P. Pesan untuk tim IT

Pada Step 7, sistem harus menyediakan halaman Local Input Layer untuk Farmasi RS/Sekretariat KFT. Halaman ini digunakan untuk mengisi atau memperbarui parameter lokal RS, yaitu harga obat ARNI dan comparator ACEI, biaya rawat inap HF, biaya rawat jalan/monitoring, volume pasien eligible, pola terapi saat ini, dan skenario uptake. Setiap input wajib memiliki sumber data, tanggal berlaku/effective date, unit, dan catatan bila menggunakan proxy/asumsi.

Sistem harus memvalidasi input lokal: nilai biaya harus numerik dan ≥0, eligible population harus integer, uptake harus 0–1, tanggal harus valid, dan sumber data wajib diisi. Setiap perubahan harga/biaya/volume tidak boleh menimpa data lama dan tidak boleh mengubah evidence layer. Sistem harus membuat local_input_version_id baru, menyimpan nilai lama dan nilai baru, mencatat user, timestamp, sumber, dan tanggal berlaku ke audit log. Versi input lokal yang aktif akan dipakai pada Step 8 untuk menjalankan CEA quick dan BIA.

Kesimpulan sederhana

Step 7 adalah tahap input data lokal RS. Untuk tim IT, yang harus dibuat adalah:

form harga obat;

form biaya rawat inap/event;

form biaya monitoring;

form eligible population;

form uptake scenario;

sumber data dan tanggal berlaku;

validasi angka/unit/tanggal/proporsi;

versioning local input;

audit trail perubahan;

tombol untuk melanjutkan ke CEA/BIA.

Jadi, Step 7 adalah jembatan antara bukti klinis dan perhitungan ekonomi lokal rumah sakit. Tanpa Step 7, sistem bisa menampilkan evidence, tetapi belum bisa menghitung ICER dan budget impact yang relevan untuk RS Unud.

Step 8 — Sistem menjalankan CEA quick dan BIA

Komponen

Isi

Tujuan

Menghitung ringkasan ekonomi untuk bahan keputusan KFT

Aktor

Sistem

Input

Effect estimates, event rate, harga obat, biaya rawat inap, volume eligible, uptake

Proses sistem

Hitung CEA quick dan BIA

Output CEA

Risk comparator, risk intervention, RR, absolute benefit, incremental cost, ICER

Output BIA

Budget impact tahunan, skenario uptake, sensitivitas harga/volume

Database

cea_results, bia_results, audit_logs

Validasi

Hasil harus sama dengan Excel pembanding dalam toleransi yang disepakati

Rumus CEA quick yang perlu dimasukkan IT:

Output

Formula

Risk comparator

events_control / n_control

Risk intervention

events_treated / n_treated

Relative risk

risk_intervention / risk_comparator

Absolute benefit

risk_comparator - risk_intervention

Incremental drug cost

annual drug cost intervention - annual drug cost comparator

Hospitalisation cost offset

rehospitalisation avoided × hospitalisation cost per event

Incremental total cost

incremental drug cost - hospitalisation cost offset

ICER

incremental total cost / rehospitalisation avoided

Rumus BIA:

Output

Formula

Jumlah pengguna intervensi

target population × uptake proportion

Budget impact tahunan

number of users × incremental total cost per patient-year

Skenario uptake

10%, 30%, 50% atau conservative/moderate/aggressive

Sensitivitas harga

harga -20%, base, +20%

Sensitivitas volume

eligible population -20%, base, +20%

Dokumen menyebut bahwa CEA quick menghitung biaya tambahan per outcome klinis yang dihindari, sedangkan BIA menghitung konsekuensi anggaran bila obat/teknologi diadopsi dalam formularium.

Penjelasan:

Step 8 adalah tahap ketika sistem DeciBridge menghitung analisis ekonomi otomatis, yaitu:

CEA quick = analisis cost-effectiveness sederhana.

BIA = Budget Impact Analysis atau analisis dampak anggaran.

Kalimat workflow:

Step 8 — Sistem menjalankan CEA quick dan BIA.

Sebaiknya ditulis lebih jelas untuk tim IT menjadi:

Setelah local input layer lengkap/aktif, sistem menggunakan data evidence layer dan local input layer untuk menghitung CEA quick dan BIA secara otomatis. Hasil perhitungan harus disimpan dengan case_id, evidence_version_id, local_input_version_id, dan calculation_run_id, sehingga dapat diverifikasi, diaudit, dan direproduksi.

Dalam dokumen teknis, CEA quick menghitung biaya tambahan per outcome klinis yang dihindari, misalnya biaya tambahan per rehospitalisasi yang dihindari, sedangkan BIA menghitung konsekuensi anggaran bila obat/teknologi diadopsi dalam formularium dengan skenario uptake seperti 10%, 30%, dan 50%.

A. Tujuan Step 8

Tujuan Step 8 adalah menjawab dua pertanyaan utama untuk KFT:

1. Pertanyaan CEA quick

“Jika ARNI digunakan dibanding ACEI, berapa tambahan biaya untuk mendapatkan tambahan manfaat klinis, misalnya rehospitalisasi yang dapat dihindari?”

Outputnya:

risk ARNI,

risk ACEI,

relative risk/RR,

absolute benefit,

incremental drug cost,

hospitalisation cost offset,

incremental total cost,

ICER.

2. Pertanyaan BIA

“Jika ARNI masuk formularium RS Unud dan digunakan oleh sebagian pasien eligible, berapa dampak anggaran RS dalam 1 tahun?”

Outputnya:

jumlah pasien yang menggunakan ARNI,

budget impact per skenario uptake,

skenario konservatif/moderat/agresif,

sensitivitas harga dan volume.

B. Data yang digunakan sistem pada Step 8

Step 8 mengambil data dari dua sumber besar:

Sumber data

Isi

Berasal dari step

Evidence layer

event rate, jumlah pasien, outcome, effect estimate, rehospitalisasi yang dihindari

Step 6

Local input layer

harga ARNI, harga ACEI, biaya rawat inap HF, eligible population, uptake

Step 7

Jadi, sistem tidak hanya mengambil data dari satu sheet. Sistem harus menggabungkan:

Komponen

Sumber tabel/sheet

case_id

cases / 01_case_meta

jumlah pasien ARNI dan ACEI

clinical_outcomes / effect_estimates

jumlah event ARNI dan ACEI

clinical_outcomes / effect_estimates

harga ARNI per bulan

cost_inputs

harga ACEI per bulan

cost_inputs

biaya rawat inap HF per event

cost_inputs

eligible population

bia_inputs

uptake 10/30/50%

bia_inputs

evidence version

version_history

local input version

local_input_versions

Dalam dokumen teknis, CEA quick menggunakan risk comparator, risk intervention, RR, absolute benefit, incremental drug cost, cost offset, incremental total cost, dan ICER. BIA menggunakan target population, uptake proportion, dan incremental total cost per patient-year.

C. Apa yang harus dibuat tim IT pada Step 8?

Tim IT harus membuat Calculation Engine yang terdiri dari dua modul:

Modul

Fungsi

CEA Quick Engine

Menghitung cost-effectiveness sederhana

BIA Engine

Menghitung dampak anggaran berdasarkan jumlah pasien dan uptake

Di dashboard, sebaiknya dibuat halaman:

CEA/BIA Calculation Page[Header]Case ID: HF_ARNI_ACEI_001Case title: ARNI vs ACEI pada pasien HFrEFEvidence version: evidence_v0.1Local input version: local_input_v0.1Calculation status: draft / calculated / needs update[Sections]1. Input summary2. CEA quick result3. BIA result4. Sensitivity scenarios5. Verification vs Excel6. Calculation log[Actions]- Run CEA- Run BIA- Run all calculations- Export result- View calculation formula- View audit trail

D. CEA quick: rumus yang harus dibuat IT

Untuk kasus ARNI vs ACEI, outcome utama yang digunakan adalah rehospitalisasi dalam 12 bulan.

1. Hitung risiko pada comparator

Comparator = ACEI.

Risk_ACEI = events_control / n_control

Contoh bila data:

events_control = 46n_control = 65

Maka:

Risk_ACEI = 46 / 65 = 0.7077

Artinya, sekitar 70,77% pasien pada kelompok ACEI mengalami rehospitalisasi dalam periode follow-up.

2. Hitung risiko pada intervensi

Intervensi = ARNI.

Risk_ARNI = events_treated / n_treated

Contoh bila data:

events_treated = 18n_treated = 40

Maka:

Risk_ARNI = 18 / 40 = 0.4500

Artinya, sekitar 45% pasien pada kelompok ARNI mengalami rehospitalisasi.

3. Hitung relative risk/RR

RR = Risk_ARNI / Risk_ACEI

Contoh:

RR = 0.4500 / 0.7077 = 0.6359

Interpretasi:

Risiko rehospitalisasi pada kelompok ARNI sekitar 0,636 kali dibanding kelompok ACEI.

4. Hitung absolute benefit

Dalam model ini, manfaat klinis dihitung sebagai rehospitalisasi yang dihindari.

Rehospitalisation avoided = Risk_ACEI - Risk_ARNI

Contoh:

Rehospitalisation avoided = 0.7077 - 0.4500 = 0.2577

Artinya:

ARNI berpotensi menghindari sekitar 0,2577 rehospitalisasi per pasien dibanding ACEI dalam 12 bulan.

Atau lebih mudah:

Sekitar 25,77 rehospitalisasi dapat dihindari per 100 pasien.

5. Hitung annual drug cost

Sistem mengambil harga obat per bulan dari local input layer.

Annual drug cost ARNI = monthly cost ARNI × 12Annual drug cost ACEI = monthly cost ACEI × 12

Contoh:

Annual drug cost ARNI = 850.000 × 12 = 10.200.000Annual drug cost ACEI = 25.000 × 12 = 300.000

6. Hitung incremental drug cost

Incremental drug cost = annual drug cost ARNI - annual drug cost ACEI

Contoh:

Incremental drug cost = 10.200.000 - 300.000 = 9.900.000

Artinya:

Penggunaan ARNI menambah biaya obat sekitar Rp9.900.000 per pasien per tahun dibanding ACEI.

7. Hitung hospitalisation cost offset

Cost offset adalah penghematan biaya rawat inap karena rehospitalisasi berkurang.

Hospitalisation cost offset = rehospitalisation avoided × hospitalisation cost per event

Contoh bila biaya rawat inap HF per admission = Rp6.889.093:

Cost offset = 0.2577 × 6.889.093 = 1.775.000-an

Artinya:

Karena ARNI mengurangi rehospitalisasi, ada potensi penghematan biaya rawat inap sekitar Rp1,78 juta per pasien per tahun.

8. Hitung incremental total cost

Incremental total cost = incremental drug cost - hospitalisation cost offset

Contoh:

Incremental total cost = 9.900.000 - 1.775.000 = 8.125.000

Artinya:

Setelah memperhitungkan penghematan rawat inap, ARNI masih menambah biaya sekitar Rp8,13 juta per pasien per tahun.

9. Hitung ICER

ICER = incremental total cost / rehospitalisation avoided

Contoh:

ICER = 8.125.000 / 0.2577 = 31.529.000

Interpretasi:

Biaya tambahan ARNI sekitar Rp31,5 juta untuk mencegah satu kejadian rehospitalisasi dibanding ACEI.

Dalam dokumen teknis, rumus CEA quick memang meliputi risk comparator, risk intervention, RR, rehospitalisation avoided, incremental drug cost, hospitalisation cost offset, incremental total cost, dan ICER.

E. Formula CEA quick yang harus diprogram

Tim IT bisa menggunakan tabel ini sebagai rumus resmi MVP:

Output

Formula

risk_comparator

events_control / n_control

risk_intervention

events_treated / n_treated

relative_risk

risk_intervention / risk_comparator

absolute_benefit

risk_comparator - risk_intervention

annual_cost_intervention

monthly_cost_intervention × 12

annual_cost_comparator

monthly_cost_comparator × 12

incremental_drug_cost

annual_cost_intervention - annual_cost_comparator

hospitalisation_cost_offset

absolute_benefit × hospitalisation_cost_per_event

incremental_total_cost

incremental_drug_cost - hospitalisation_cost_offset

ICER

incremental_total_cost / absolute_benefit

F. BIA: rumus yang harus dibuat IT

BIA menghitung dampak anggaran jika ARNI digunakan pada sejumlah pasien eligible.

1. Hitung jumlah pengguna intervensi

Number of users = eligible population × uptake proportion

Contoh:

Skenario

Eligible population

Uptake

Number of users

Conservative

120

0.10

12 pasien

Moderate

120

0.30

36 pasien

Aggressive

120

0.50

60 pasien

2. Hitung budget impact tahunan

Budget impact = number of users × incremental total cost per patient-year

Contoh jika incremental total cost = Rp8.125.000:

Skenario

Number of users

Incremental total cost

Budget impact

Conservative 10%

12

Rp8.125.000

Rp97.500.000

Moderate 30%

36

Rp8.125.000

Rp292.500.000

Aggressive 50%

60

Rp8.125.000

Rp487.500.000

3. Sensitivity harga

Sistem perlu menyediakan skenario jika harga ARNI turun/naik.

Contoh:

Skenario harga

Nilai

Lower price

-20%

Base case

0%

Higher price

+20%

Tujuan:

KFT bisa melihat apakah ARNI menjadi lebih layak jika ada negosiasi harga.

4. Sensitivity volume pasien

Sistem juga perlu menyediakan variasi jumlah pasien eligible.

Skenario volume

Nilai

Low volume

-20%

Base volume

0%

High volume

+20%

Tujuan:

KFT bisa melihat bagaimana budget impact berubah jika jumlah pasien eligible lebih sedikit atau lebih banyak.

Dalam dokumen teknis, BIA menggunakan jumlah pengguna = target population × uptake proportion, dan budget impact = number of users × incremental total cost per patient-year. Skenario sensitivitas dapat mencakup harga dan volume, misalnya -20%, base, +20%.

G. Output CEA/BIA yang harus tampil di dashboard

1. Tampilan CEA quick

Komponen

Nilai yang ditampilkan

Risk ARNI

otomatis

Risk ACEI

otomatis

RR

otomatis

Rehospitalisation avoided

otomatis

Annual cost ARNI

otomatis

Annual cost ACEI

otomatis

Incremental drug cost

otomatis

Hospitalisation cost offset

otomatis

Incremental total cost

otomatis

ICER

otomatis

Sistem juga sebaiknya menampilkan interpretasi otomatis:

“ARNI memiliki risiko rehospitalisasi lebih rendah dibanding ACEI. Dengan harga dan biaya lokal versi ini, incremental total cost per pasien per tahun adalah Rp…, dan ICER adalah Rp… per rehospitalisasi yang dihindari.”

2. Tampilan BIA

Skenario

Uptake

Jumlah pengguna

Budget impact 1 tahun

Conservative

10%

otomatis

otomatis

Moderate

30%

otomatis

otomatis

Aggressive

50%

otomatis

otomatis

Sistem juga sebaiknya menampilkan interpretasi otomatis:

“Jika ARNI digunakan pada 30% pasien eligible, estimasi dampak anggaran 1 tahun adalah Rp….”

3. Status hasil

Sistem harus memberi status hasil:

Status

Makna

calculation_not_ready

Input penting belum lengkap

calculated_with_warning

Bisa dihitung, tetapi ada data proxy/asumsi

calculated

Semua input lengkap dan hasil valid

needs_update

Ada input baru sehingga kalkulasi lama tidak lagi aktif

locked_with_decision

Hasil digunakan dalam keputusan final KFT

H. Validasi sebelum menjalankan CEA/BIA

Sebelum kalkulasi, sistem harus memeriksa apakah input wajib tersedia.

1. Minimal input untuk CEA quick

Input

Wajib?

events_treated

Ya

n_treated

Ya

events_control

Ya

n_control

Ya

monthly_cost_intervention

Ya

monthly_cost_comparator

Ya

hospitalisation_cost_per_event

Ya

time_horizon

Ya

Jika harga ARNI belum ada, sistem harus menampilkan:

“CEA quick belum dapat dijalankan karena harga ARNI belum tersedia pada local input layer.”

2. Minimal input untuk BIA

Input

Wajib?

eligible_population

Ya

uptake_proportion

Ya

incremental_total_cost

Ya, dari CEA

time_horizon

Ya

Jika eligible population belum ada:

“BIA belum dapat dijalankan karena jumlah pasien eligible belum tersedia.”

I. Error dan warning yang harus dibuat IT

Kondisi

Jenis

Pesan

n_control = 0

Fatal

“n_control tidak boleh 0 karena akan menyebabkan pembagian dengan nol.”

n_treated = 0

Fatal

“n_treated tidak boleh 0.”

events_control > n_control

Fatal

“Jumlah event comparator tidak boleh lebih besar dari jumlah pasien comparator.”

events_treated > n_treated

Fatal

“Jumlah event intervensi tidak boleh lebih besar dari jumlah pasien intervensi.”

harga ARNI kosong

Fatal untuk CEA final

“Harga ARNI belum tersedia.”

harga ACEI kosong

Fatal untuk CEA final

“Harga ACEI belum tersedia.”

biaya rawat inap kosong

Warning/fatal tergantung setting

“Biaya rawat inap belum tersedia; cost-offset tidak dapat dihitung.”

eligible population kosong

Fatal untuk BIA

“Eligible population belum tersedia.”

uptake > 1

Fatal

“Uptake harus 0–1.”

absolute benefit = 0

Warning/fatal untuk ICER

“Tidak ada perbedaan efektivitas; ICER tidak dapat dihitung.”

incremental total cost negatif

Warning interpretasi

“Intervensi berpotensi cost-saving.”

J. Bagaimana sistem menangani hasil khusus?

1. Jika ARNI lebih efektif dan lebih mahal

Kondisi:

absolute_benefit > 0incremental_total_cost > 0

Interpretasi:

Hitung ICER. KFT perlu mempertimbangkan apakah tambahan biaya layak dibanding manfaat.

2. Jika ARNI lebih efektif dan lebih murah

Kondisi:

absolute_benefit > 0incremental_total_cost < 0

Interpretasi:

ARNI bersifat dominant/cost-saving. Sistem dapat memberi label: “dominant”.

3. Jika ARNI kurang efektif dan lebih mahal

Kondisi:

absolute_benefit < 0incremental_total_cost > 0

Interpretasi:

ARNI bersifat dominated. Sistem dapat memberi label: “dominated”.

4. Jika tidak ada manfaat tambahan

Kondisi:

absolute_benefit = 0

Interpretasi:

ICER tidak dapat dihitung karena pembagi nol. Sistem harus menampilkan warning.

K. Database/tabel yang dibutuhkan Step 8

Minimal IT perlu membuat tabel berikut:

Tabel

Fungsi

calculation_runs

Menyimpan setiap proses perhitungan

cea_results

Menyimpan hasil CEA quick

bia_results

Menyimpan hasil BIA

bia_scenarios

Menyimpan skenario uptake

sensitivity_results

Menyimpan hasil sensitivitas

audit_logs

Mencatat siapa menjalankan kalkulasi

version_history

Menghubungkan hasil dengan versi evidence dan local input

Contoh tabel calculation_runs

Field

Contoh

calculation_run_id

CALC_20260511_001

case_id

HF_ARNI_ACEI_001

evidence_version_id

evidence_v0.1

local_input_version_id

local_input_v0.1

run_by

hta_analyst_01

run_at

2026-05-11 14:00

calculation_status

calculated_with_warning

notes

Harga menggunakan input RS Unud versi awal

Contoh tabel cea_results

Field

Contoh

calculation_run_id

CALC_20260511_001

case_id

HF_ARNI_ACEI_001

risk_intervention

0.45

risk_comparator

0.7077

relative_risk

0.6359

absolute_benefit

0.2577

annual_cost_intervention

10200000

annual_cost_comparator

300000

incremental_drug_cost

9900000

hospitalisation_cost_offset

1775000

incremental_total_cost

8125000

icer

31529000

interpretation

More effective and more costly

Contoh tabel bia_results

Field

Contoh

calculation_run_id

CALC_20260511_001

case_id

HF_ARNI_ACEI_001

scenario_name

Moderate

eligible_population

120

uptake

0.30

number_of_users

36

incremental_cost_per_patient_year

8125000

budget_impact_year1

292500000

L. Flowchart Step 8

M. Hubungan Step 8 dengan Step 9 dan policy brief

Hasil Step 8 akan dipakai untuk:

Step berikutnya

Data yang digunakan

Step 9 EtD appraisal

Domain cost-effectiveness dan budget impact

Step 10 recommendation engine

Rule biaya dan budget impact

Step 12 policy brief

Ringkasan ekonomi, ICER, BIA, sensitivitas

Step 13 approval

Ketua KFT melihat hasil ekonomi sebelum lock decision

Dalam struktur policy brief otomatis, bagian ringkasan ekonomi harus memuat incremental cost, ICER, BIA, dan skenario sensitivitas.

N. Pseudocode sederhana untuk IT

1. User clicks "Run CEA/BIA".2. System loads:      case_id      active evidence_version_id      active local_input_version_id3. System validates CEA inputs:      n_treated, events_treated,      n_control, events_control,      monthly_cost_intervention,      monthly_cost_comparator,      hospitalisation_cost_per_event.4. If required CEA input missing:      stop calculation and show error.5. Calculate:      risk_intervention      risk_comparator      relative_risk      absolute_benefit      annual drug costs      incremental drug cost      hospitalisation cost offset      incremental total cost      ICER.6. Save results to cea_results.7. Validate BIA inputs:      eligible_population      uptake_scenarios.8. If BIA inputs exist:      calculate number_of_users and budget impact for each scenario.9. Run sensitivity analysis:      price -20%, base, +20%      volume -20%, base, +20%.10. Save results to bia_results and sensitivity_results.11. Create calculation_run_id.12. Save audit log:      who ran calculation,      when,      which evidence version,      which local input version,      formulas used.13. Display results in dashboard.

O. Acceptance criteria Step 8 untuk tim IT

Step 8 dianggap selesai jika sistem sudah bisa:

Acceptance criteria

Harus bisa

Mengambil data dari evidence layer dan local input layer

Ya

Menggunakan case_id, evidence_version_id, dan local_input_version_id

Ya

Memvalidasi input sebelum kalkulasi

Ya

Menghitung risk intervention dan risk comparator

Ya

Menghitung RR

Ya

Menghitung absolute benefit/rehospitalisasi dihindari

Ya

Menghitung annual drug cost

Ya

Menghitung incremental drug cost

Ya

Menghitung hospitalisation cost offset

Ya

Menghitung incremental total cost

Ya

Menghitung ICER

Ya

Menghitung number of users per uptake scenario

Ya

Menghitung budget impact per skenario

Ya

Menjalankan sensitivitas harga dan volume

Ya

Menyimpan hasil ke cea_results dan bia_results

Ya

Membuat calculation_run_id

Ya

Mencatat audit log

Ya

Menampilkan warning bila data belum lengkap

Ya

Menyediakan hasil untuk EtD dan policy brief

Ya

Bisa diverifikasi dengan Excel pembanding

Ya

Dokumen teknis juga menyebut bahwa hasil CEA quick dan BIA harus diverifikasi terhadap Excel pembanding, dengan kriteria seperti selisih risk/RR/absolute benefit <0,0001 dan ICER/BIA sesuai pembulatan rupiah.

P. Pesan untuk tim IT

Pada Step 8, sistem DeciBridge harus menjalankan CEA quick dan Budget Impact Analysis/BIA secara otomatis setelah evidence layer dan local input layer tersedia. Sistem harus mengambil data outcome klinis dari evidence layer, seperti events_treated, n_treated, events_control, n_control, lalu mengambil data lokal dari local input layer, seperti harga ARNI per bulan, harga ACEI per bulan, biaya rawat inap HF per event, jumlah pasien eligible, dan skenario uptake.

CEA quick menghitung risk_intervention, risk_comparator, relative_risk, absolute_benefit, incremental_drug_cost, hospitalisation_cost_offset, incremental_total_cost, dan ICER. BIA menghitung number_of_users = eligible_population × uptake dan budget_impact = number_of_users × incremental_total_cost_per_patient_year. Sistem juga perlu menjalankan sensitivitas sederhana untuk harga dan volume, misalnya -20%, base, +20%.

Setiap kalkulasi harus menghasilkan calculation_run_id dan disimpan bersama case_id, evidence_version_id, dan local_input_version_id. Hasil harus masuk ke tabel cea_results, bia_results, dan sensitivity_results. Sistem harus mencatat siapa yang menjalankan kalkulasi, kapan, versi evidence dan versi local input mana yang dipakai, serta formula yang digunakan. Jika input belum lengkap, sistem harus memberi error/warning dan tidak menghitung hasil final. Hasil kalkulasi harus dapat diverifikasi dengan Excel pembanding dan kemudian digunakan untuk EtD appraisal serta policy brief.

Kesimpulan sederhana

Step 8 adalah mesin hitung ekonomi DeciBridge.

Tim IT harus membuat sistem yang bisa:

mengambil data klinis dari evidence layer;

mengambil harga, biaya, eligible population, dan uptake dari local input layer;

menghitung CEA quick;

menghitung BIA;

menjalankan sensitivitas sederhana;

menyimpan hasil dengan calculation_run_id;

mencatat versi data yang dipakai;

menampilkan hasil di dashboard;

mengirim hasil ke EtD dan policy brief;

memverifikasi hasil dengan Excel pembanding.

Dengan Step 8 ini, KFT dapat melihat bukan hanya apakah ARNI bermanfaat secara klinis, tetapi juga berapa tambahan biaya dan dampak anggaran jika ARNI masuk formularium RS Unud.

Step 9 — Anggota KFT mengisi judgement EtD dan rationale, maksudnya: Anggota KFT mengisi penilaian EtD per domain melalui form dashboard, misalnya manfaat klinis, risiko, kepastian bukti, cost-effectiveness, budget impact, feasibility, acceptability, dan equity. Untuk setiap domain, anggota KFT memilih judgement/rating dan menuliskan rationale atau alasan singkat. Sistem menyimpan setiap judgement, rationale, user, waktu pengisian, session_id, case_id, dan version_id ke database dan audit trail.

Step 9 adalah tahap ketika anggota KFT menilai setiap domain Evidence-to-Decision/EtD dan menuliskan alasan penilaiannya. Tahap ini penting karena DeciBridge bukan hanya menghitung angka CEA/BIA, tetapi juga merekam pertimbangan keputusan KFT secara transparan dan bisa diaudit.

Dalam dokumen teknis, EtD appraisal memang menjadi modul yang menyimpan judgement per domain, rationale, dan traffic-light; anggota KFT memberi judgement dan rationale, sedangkan sistem kemudian menampilkan traffic-light serta rekomendasi awal.

Komponen

Isi

Tujuan

Merekam penilaian KFT secara terstruktur per domain keputusan

Aktor

KFT member

Input

Judgement per domain dan rationale/alasan

Proses sistem

User memilih dropdown judgement dan menulis alasan singkat

Output

EtD appraisal lengkap

Database

etd_domains, etd_scores, etd_rationales, etd_appraisals

Audit trail

Mencatat domain, nilai lama, nilai baru, rationale, user, timestamp

Catatan IT

Rationale sebaiknya wajib untuk domain kuning/merah

Domain EtD yang digunakan:

Domain

Input utama

Pilihan judgement

Problem priority

Beban penyakit, unmet need, frekuensi rehospitalisasi

High / moderate / low

Benefits

Effect estimate, absolute benefit, outcome penting

Favorable / uncertain / unfavorable

Harms

Hipotensi, hiperkalemia, gangguan ginjal, adverse event lain

Acceptable / concern / unacceptable

Certainty of evidence

Jenis studi, risk of bias, konsistensi, presisi

High / moderate / low / very low

Cost-effectiveness

ICER dan interpretasi lokal

Favorable / uncertain / unfavorable

Budget impact

Dampak anggaran tahunan dan skenario uptake

Low / moderate / high

Equity

Dampak pada akses dan keadilan layanan

Improve / neutral / worsen

Feasibility

Ketersediaan obat, monitoring, SDM, SOP

Feasible / feasible with constraints / not feasible

Acceptability

Penerimaan klinisi, farmasi, manajemen, pasien

High / mixed / low

A. Tujuan Step 9

Tujuan Step 9 adalah membuat keputusan KFT tidak hanya berbasis “pendapat umum”, tetapi terdokumentasi berdasarkan domain yang jelas.

Step 9 menjawab pertanyaan:

Domain

Pertanyaan utama

Problem priority

Apakah masalah klinis ini penting untuk RS?

Benefits

Apakah obat memberi manfaat klinis bermakna?

Harms

Apakah risiko/efek samping dapat diterima?

Certainty

Seberapa kuat bukti ilmiahnya?

Cost-effectiveness

Apakah tambahan biaya sebanding dengan manfaat?

Budget impact

Apakah dampak anggaran masih dapat diterima RS?

Equity

Apakah keputusan ini memperbaiki atau memperburuk akses pasien?

Feasibility

Apakah obat dapat diterapkan di RS?

Acceptability

Apakah dapat diterima klinisi, farmasi, manajemen, dan pasien?

Output Step 9 adalah:

Tabel EtD judgement + rationale per domain yang nanti dipakai sistem untuk membuat traffic-light, rekomendasi awal, dan policy brief.

B. Siapa yang mengisi Step 9?

Role

Hak akses pada Step 9

KFT Member

Mengisi judgement dan rationale per domain

Ketua KFT / Approver

Dapat melihat semua judgement, memberi keputusan final, dan mengunci keputusan

Sekretaris KFT / Farmasi RS

Dapat membantu membuka sesi rapat dan mencatat consensus judgement

Analis HTA

Menyediakan evidence summary dan hasil CEA/BIA sebagai bahan penilaian, tetapi tidak mengunci keputusan final

Admin IT

Tidak boleh mengubah judgement klinis/EtD

Dalam dokumen teknis, KFT member berhak memberikan judgement EtD, rationale, dan komentar rapat, tetapi tidak mengubah data evidence yang sudah divalidasi. Ketua KFT/Approver berhak approve rekomendasi, lock decision, dan finalisasi policy brief.

C. Kapan Step 9 dilakukan?

Step 9 dilakukan setelah:

Case pack sudah direview oleh Analis HTA.

Evidence summary sudah siap.

Local input layer sudah diisi atau minimal tersedia sebagai draft.

CEA quick dan BIA sudah dijalankan atau diberi status “belum final” jika data ekonomi belum lengkap.

Rapat/simulasi KFT dimulai.

Jadi anggota KFT tidak mengisi EtD dalam keadaan kosong. Sistem harus menampilkan bahan keputusan terlebih dahulu.

D. Apa yang harus dibuat tim IT?

Tim IT perlu membuat halaman:

EtD Appraisal Form

Struktur halaman sebaiknya seperti ini:

EtD Appraisal Page[Header]Case ID: HF_ARNI_ACEI_001Case title: ARNI vs ACEI pada pasien HFrEFMeeting/session ID: KFT_2026_ARNI_001Evidence version: evidence_v0.1Local input version: local_input_v0.1Calculation run: CALC_2026_001Status: open / submitted / consensus / locked[Ringkasan singkat]- Intervention: ARNI- Comparator: ACEI- Main outcome: rehospitalisasi 12 bulan- Clinical effect: RR, absolute benefit- CEA result: incremental cost, ICER- BIA result: budget impact skenario 10/30/50%[Domain EtD]1. Problem priority2. Benefits3. Harms4. Certainty of evidence5. Cost-effectiveness6. Budget impact7. Equity8. Feasibility9. Acceptability[Untuk tiap domain]- Evidence cue / ringkasan data pendukung- Dropdown judgement- Traffic-light preview- Rationale text box- Comment box- Save draft- Submit domain[Actions]- Save all as draft- Submit EtD judgement- View other member responses- Generate consensus summary- Send to recommendation engine

E. Konsep penting: session EtD

Setiap rapat atau simulasi KFT harus punya session_id.

Contoh:

KFT_2026_ARNI_001

Session ini menghubungkan:

case yang dibahas,

tanggal rapat,

anggota KFT yang menilai,

domain EtD,

rating,

rationale,

rekomendasi final.

Tanpa session_id, sistem sulit membedakan apakah penilaian dibuat pada rapat pertama, revisi rapat, atau simulasi ulang.

F. Field database minimal untuk Step 9

Minimal tabel yang dibutuhkan:

1. Tabel etd_sessions

Field

Contoh

Fungsi

session_id

KFT_2026_ARNI_001

ID sesi rapat

case_id

HF_ARNI_ACEI_001

ID kasus

meeting_date

2026-05-20

Tanggal rapat

session_type

pilot / real_meeting / simulation

Jenis sesi

status

open / submitted / consensus / locked

Status sesi

created_by

sekretaris_kft_01

Pembuat sesi

created_at

timestamp

Waktu dibuat

2. Tabel etd_appraisals atau etd_scores

Field

Contoh

Fungsi

appraisal_id

ETDAPP_001

ID unik penilaian

session_id

KFT_2026_ARNI_001

Sesi rapat

case_id

HF_ARNI_ACEI_001

Kasus

user_id

KFT_member1

Penilai

domain

benefits

Domain EtD

judgement

Favorable

Penilaian

rating

Green

Warna/traffic-light

rationale

“ARNI menurunkan rehospitalisasi dibanding ACEI.”

Alasan

evidence_version_id

evidence_v0.1

Versi evidence yang dipakai

local_input_version_id

local_input_v0.1

Versi input lokal

calculation_run_id

CALC_2026_001

Hasil CEA/BIA yang dipakai

submitted_at

timestamp

Waktu submit

3. Tabel etd_domains

Field

Contoh

domain_id

benefits

domain_name

Benefits

definition

Besarnya manfaat klinis intervensi dibanding comparator

display_order

2

is_required

true

4. Tabel etd_rationales

Boleh digabung dengan etd_appraisals, tetapi lebih rapi jika dipisah.

Field

Contoh

rationale_id

RAT_001

appraisal_id

ETDAPP_001

rationale_text

“Manfaat klinis terlihat dari penurunan rehospitalisasi.”

created_by

KFT_member1

created_at

timestamp

G. Domain EtD yang harus tampil

Untuk MVP DeciBridge, saya sarankan pakai 9 domain ini.

No

Domain

Data pendukung yang harus ditampilkan sistem

Pilihan judgement

1

Problem priority

Beban penyakit, unmet need, frekuensi rehospitalisasi

High / moderate / low

2

Benefits

Effect estimate, RR, absolute benefit, outcome penting

Favorable / uncertain / unfavorable

3

Harms

Hipotensi, hiperkalemia, gangguan ginjal, adverse event lain

Acceptable / concern / unacceptable

4

Certainty of evidence

Jenis studi, risk of bias, konsistensi, presisi

High / moderate / low / very low

5

Cost-effectiveness

ICER dan interpretasi lokal

Favorable / uncertain / unfavorable

6

Budget impact

Dampak anggaran tahunan dan skenario uptake

Low / moderate / high

7

Equity

Dampak pada akses pasien dan keadilan layanan

Improve / neutral / worsen

8

Feasibility

Ketersediaan obat, monitoring, SDM, SOP

Feasible / feasible with constraints / not feasible

9

Acceptability

Penerimaan klinisi, farmasi, manajemen, pasien

High / mixed / low

Daftar domain dan judgement ini sesuai dengan bagian EtD scoring dalam dokumen teknis DeciBridge.

H. Contoh tampilan tiap domain di dashboard

Contoh domain: Benefits

Domain: BenefitsEvidence cue:- Outcome utama: rehospitalisasi 12 bulan- Risk ARNI: 0.45- Risk ACEI: 0.7077- RR: 0.6359- Absolute benefit: 0.2577 rehospitalisasi dihindari per pasienJudgement:[Dropdown]- Favorable- Uncertain- UnfavorableTraffic-light:Favorable = GreenUncertain = YellowUnfavorable = RedRationale:[Text box]Contoh: ARNI menunjukkan penurunan risiko rehospitalisasi dibanding ACEI berdasarkan data lokal, sehingga manfaat klinis dinilai mendukung adopsi.[Save draft] [Submit]

Contoh domain: Budget impact

Domain: Budget impactEvidence cue:- Eligible population: 120 pasien/tahun- Uptake scenario:  Conservative 10% = Rp...  Moderate 30% = Rp...  Aggressive 50% = Rp...- Data menggunakan local_input_v0.1Judgement:[Dropdown]- Low- Moderate- HighTraffic-light:Low = GreenModerate = YellowHigh = Red atau Yellow, sesuai rule KFTRationale:[Text box]Contoh: Dampak anggaran pada skenario 30% masih memerlukan diskusi manajemen dan kemungkinan pembatasan pasien eligible.[Save draft] [Submit]

Contoh domain: Feasibility

Domain: FeasibilityEvidence cue:- Obat tersedia/tidak tersedia di formularium- Monitoring tekanan darah, kreatinin/eGFR, dan kalium tersedia di RS- Prescriber dapat dibatasi pada dokter jantung/penyakit dalamJudgement:[Dropdown]- Feasible- Feasible with constraints- Not feasibleTraffic-light:Feasible = GreenFeasible with constraints = YellowNot feasible = RedRationale:[Text box]Contoh: Implementasi feasible karena monitoring laboratorium tersedia, tetapi perlu SOP pembatasan prescriber dan monitoring awal.

I. Mapping judgement ke traffic-light

Tim IT harus membuat aturan mapping.

Contoh sederhana:

Domain

Judgement

Traffic-light

Benefits

Favorable

Green

Benefits

Uncertain

Yellow

Benefits

Unfavorable

Red

Harms

Acceptable

Green

Harms

Concern

Yellow

Harms

Unacceptable

Red

Certainty

High/Moderate

Green

Certainty

Low

Yellow

Certainty

Very low

Red

Cost-effectiveness

Favorable

Green

Cost-effectiveness

Uncertain

Yellow

Cost-effectiveness

Unfavorable

Red

Budget impact

Low

Green

Budget impact

Moderate

Yellow

Budget impact

High

Red atau Yellow sesuai aturan KFT

Equity

Improve

Green

Equity

Neutral

Yellow

Equity

Worsen

Red

Feasibility

Feasible

Green

Feasibility

Feasible with constraints

Yellow

Feasibility

Not feasible

Red

Acceptability

High

Green

Acceptability

Mixed

Yellow

Acceptability

Low

Red

Dalam dokumen teknis, warna hijau berarti mendukung adopsi, kuning berarti masih ada ketidakpastian atau perlu pembatasan, dan merah berarti tidak mendukung adopsi.

J. Rationale wajib diisi

Tim IT perlu membuat aturan:

Setiap domain harus memiliki rationale.

Minimal 1–2 kalimat. Untuk rating Yellow dan Red, rationale harus wajib.

Contoh aturan validasi:

Kondisi

Aturan

Rating Green

rationale disarankan/wajib singkat

Rating Yellow

rationale wajib

Rating Red

rationale wajib

Rationale kosong

tidak bisa submit

Rationale terlalu pendek

beri warning, misalnya minimal 20 karakter

Rationale terlalu panjang

batasi, misalnya maksimal 1.000 karakter

Contoh pesan error:

“Rationale wajib diisi untuk domain Budget impact karena rating yang dipilih adalah Yellow.”

K. Apakah tiap anggota KFT mengisi sendiri-sendiri atau satu consensus judgement?

Untuk MVP, ada dua opsi teknis.

Opsi 1 — Individual judgement

Setiap anggota KFT mengisi sendiri.

Kelebihan:

lebih transparan,

bisa melihat variasi pendapat,

cocok untuk audit.

Kekurangan:

lebih kompleks,

perlu fitur agregasi.

Opsi 2 — Consensus judgement

Sekretaris KFT atau Ketua KFT mengisi satu penilaian final per domain berdasarkan hasil diskusi.

Kelebihan:

lebih sederhana untuk MVP,

lebih cepat dibuat IT,

cocok untuk simulasi awal.

Kekurangan:

variasi pendapat individu tidak terekam detail.

Saran untuk MVP

Saya sarankan untuk MVP awal:

Gunakan consensus judgement sebagai data utama, tetapi sistem tetap menyediakan field user_id agar nanti bisa dikembangkan menjadi individual judgement.

Dengan begitu, Step 9 dapat berjalan cepat untuk pilot KFT.

Formatnya:

session_id

user_id

role

domain

judgement

rating

rationale

KFT_2026_ARNI_001

sekretaris_kft

consensus_recorder

benefits

Favorable

Green

Berdasarkan diskusi, manfaat klinis mendukung adopsi.

KFT_2026_ARNI_001

sekretaris_kft

consensus_recorder

budget_impact

Moderate

Yellow

Dampak anggaran memerlukan pembatasan pasien eligible.

L. Validasi Step 9

Sebelum EtD bisa disubmit, sistem harus memvalidasi:

Validasi

Aturan

session_id

tidak boleh kosong

case_id

harus sama dengan case aktif

domain

harus dari daftar domain resmi

judgement

harus sesuai pilihan domain

rating

harus sesuai mapping judgement

rationale

wajib, terutama untuk Yellow/Red

semua domain wajib

harus terisi sebelum submit final

user role

hanya KFT Member/Sekretariat/Approver yang boleh submit

case status

case belum boleh locked

version linkage

evidence_version dan local_input_version harus tercatat

Jika data ekonomi belum final, sistem tetap boleh mengizinkan EtD, tetapi domain cost-effectiveness dan budget impact diberi warning:

“CEA/BIA belum final. Judgement ekonomi dapat disimpan sebagai draft, tetapi belum dapat dipakai untuk lock decision final.”

M. Status EtD session

Tim IT perlu membuat status:

Status

Makna

not_started

EtD belum diisi

in_progress

Sebagian domain sudah diisi

submitted

Semua domain sudah diisi

needs_revision

Ada domain yang perlu revisi

consensus_done

Penilaian konsensus selesai

ready_for_recommendation

Bisa lanjut ke recommendation engine

locked

Sudah masuk keputusan final dan tidak bisa diubah

N. Output Step 9

Output Step 9 adalah tabel EtD appraisal.

Contoh:

Domain

Judgement

Traffic-light

Rationale

Problem priority

High

Green

HFrEF memiliki beban klinis tinggi dan rehospitalisasi berdampak pada biaya RS.

Benefits

Favorable

Green

ARNI menunjukkan penurunan rehospitalisasi dibanding ACEI.

Harms

Concern

Yellow

ARNI memerlukan monitoring hipotensi, kalium, dan fungsi ginjal.

Certainty

Low/Moderate

Yellow

Data lokal bersifat observasional dan perlu didukung literatur.

Cost-effectiveness

Uncertain

Yellow

ICER bergantung pada harga ARNI dan biaya rawat inap yang digunakan.

Budget impact

Moderate/High

Yellow/Red

Dampak anggaran bergantung pada uptake dan jumlah pasien eligible.

Equity

Neutral/Improve

Yellow/Green

Pembatasan akses dapat membantu penggunaan lebih adil pada pasien yang paling membutuhkan.

Feasibility

Feasible with constraints

Yellow

Monitoring tersedia, tetapi perlu SOP dan kriteria prescriber.

Acceptability

Mixed/High

Yellow/Green

Perlu kesepakatan klinisi, farmasi, dan manajemen.

O. Hubungan Step 9 dengan Step 10

Hasil Step 9 akan dipakai sistem untuk membuat:

Traffic-light summary

Draft recommendation

Policy brief

Audit trail keputusan

Contoh rule Step 10:

Kondisi dari Step 9

Rekomendasi awal

Benefits Green, harms Green/Yellow, feasibility Green, budget impact Green/Yellow

Adopt atau Adopt with criteria

Benefits Green tetapi budget impact Red

Adopt with criteria-based access

Benefits Yellow dan cost-effectiveness Red

Defer

Harms Red atau feasibility Red

Do not adopt

Dokumen teknis menjelaskan bahwa recommendation engine menggunakan kondisi rule seperti benefit favorable, harms acceptable, feasibility feasible, budget impact acceptable untuk menghasilkan rekomendasi awal.

P. Audit trail pada Step 9

Setiap pengisian EtD harus tercatat.

Aktivitas

Data yang dicatat

User membuka form EtD

user_id, case_id, session_id, timestamp

User mengisi judgement

domain, judgement, rating, timestamp

User mengubah judgement

nilai lama, nilai baru, user, timestamp

User mengisi rationale

rationale text, user, timestamp

Submit EtD

semua domain, user, timestamp

Consensus final

recorder/approver, timestamp

Revisi setelah submit

alasan revisi, user, timestamp

Dalam dokumen teknis, audit trail harus mencatat perubahan judgement EtD berupa domain, nilai lama, nilai baru, dan rationale.

Q. Flowchart Step 9

R. Pseudocode sederhana untuk IT

1. User opens EtD Appraisal page for case HF_ARNI_ACEI_001.2. System checks user role.3. If role is KFT Member, Sekretariat KFT, or Approver:      allow filling EtD form.   Else:      view only.4. System loads:      case metadata      evidence summary      CEA/BIA result      EtD domain list      rating options      traffic-light mapping.5. User selects judgement for each domain.6. User writes rationale for each domain.7. System maps judgement to traffic-light.8. System validates:      all required domains filled,      rationale not empty,      rating valid,      case/session not locked.9. If incomplete:      save as draft and show missing domain.10. If complete:      save to etd_appraisals.11. Create or update session status:      submitted / consensus_done / ready_for_recommendation.12. Write audit log:      user, domain, judgement, rationale, timestamp.13. Send EtD summary to recommendation engine.

S. Acceptance criteria Step 9 untuk tim IT

Step 9 dianggap selesai jika sistem sudah bisa:

Acceptance criteria

Harus bisa

Membuat EtD session per case

Ya

Menampilkan semua domain EtD

Ya

Menampilkan evidence cue per domain

Ya

Menampilkan hasil CEA/BIA pada domain ekonomi

Ya

Menyediakan dropdown judgement per domain

Ya

Memetakan judgement ke traffic-light

Ya

Menyediakan text box rationale

Ya

Menyimpan draft bila belum lengkap

Ya

Memvalidasi semua domain wajib

Ya

Mewajibkan rationale untuk domain tertentu

Ya

Menyimpan user_id, session_id, case_id, domain, rating, rationale

Ya

Mendukung consensus judgement untuk MVP

Ya

Menyimpan audit trail perubahan judgement

Ya

Mengunci EtD setelah decision locked

Ya

Mengirim hasil EtD ke recommendation engine

Ya

Mengirim hasil EtD ke policy brief generator

Ya

T. Pesan untuk tim IT

Pada Step 9, sistem harus menyediakan halaman EtD Appraisal Form untuk anggota KFT. Setiap sesi rapat KFT harus memiliki session_id, misalnya KFT_2026_ARNI_001, dan terhubung dengan case_id = HF_ARNI_ACEI_001. Sistem menampilkan ringkasan evidence, hasil CEA/BIA, dan seluruh domain EtD. Anggota KFT atau sekretaris KFT sebagai consensus recorder memilih judgement per domain dan menuliskan rationale singkat.

Domain minimal yang digunakan adalah problem priority, benefits, harms, certainty of evidence, cost-effectiveness, budget impact, equity, feasibility, dan acceptability. Setiap domain memiliki pilihan judgement tertentu, lalu sistem memetakan judgement tersebut menjadi traffic-light Green/Yellow/Red. Rationale harus wajib diisi, terutama jika rating Yellow atau Red.

Sistem harus menyimpan session_id, case_id, user_id, domain, judgement, traffic_light, rationale, evidence_version_id, local_input_version_id, calculation_run_id, dan submitted_at. Semua perubahan judgement harus masuk audit log, termasuk nilai lama, nilai baru, user, timestamp, dan rationale. Output Step 9 adalah EtD summary yang siap digunakan oleh recommendation engine dan policy brief generator.

Kesimpulan sederhana

Step 9 adalah tahap penilaian KFT.Tim IT harus membuat form yang memungkinkan anggota KFT atau sekretaris KFT sebagai pencatat konsensus untuk:

memilih domain EtD;

melihat data pendukung tiap domain;

memilih judgement;

menuliskan rationale;

menyimpan draft;

submit penilaian;

menghasilkan traffic-light;

menyimpan audit trail.

Step ini adalah inti dari Evidence-to-Decision, karena di sinilah angka klinis dan ekonomi diterjemahkan menjadi pertimbangan keputusan KFT yang eksplisit, transparan, dan terdokumentasi.

Step 10 — Sistem menampilkan traffic-light dan rekomendasi awal, maksudnya: Setelah EtD judgement dan rationale diisi, sistem memetakan setiap judgement domain EtD ke warna Green/Yellow/Red, menampilkan ringkasan traffic-light per domain, lalu menjalankan rule-based recommendation engine untuk menghasilkan rekomendasi awal: Adopt, Adopt with criteria-based access, Defer, Do not adopt, atau Reassess after price negotiation. Rekomendasi ini masih bersifat draft dan harus dapat direview, diedit, dan disetujui oleh Ketua KFT/Approver.

Step 10 adalah tahap ketika sistem DeciBridge mengubah hasil penilaian EtD menjadi tampilan warna/traffic-light dan rekomendasi awal otomatis. Jadi setelah anggota KFT mengisi judgement dan rationale pada Step 9, sistem membaca semua judgement tersebut, memberi warna hijau/kuning/merah, lalu menghasilkan draft rekomendasi seperti:

Adopt

Adopt with criteria-based access

Defer pending additional evidence

Do not adopt

Reassess after price negotiation

Dalam dokumen teknis, traffic-light digunakan untuk menunjukkan apakah suatu domain mendukung adopsi, masih perlu diskusi/pembatasan, atau tidak mendukung adopsi. Recommendation engine kemudian memberi rekomendasi awal berbasis rule, tetapi keputusan final tetap dapat diedit/disetujui oleh KFT/Ketua KFT.

Komponen

Isi

Tujuan

Membantu KFT melihat ringkasan penilaian secara cepat

Aktor

Sistem

Input

EtD judgement dan rules rekomendasi

Proses sistem

Mapping judgement ke warna dan rekomendasi awal

Output

Traffic-light summary dan draft recommendation

Database

recommendation_rules, recommendations, etd_scores

Audit trail

Mencatat rekomendasi awal yang dihasilkan sistem

Catatan IT

Rekomendasi awal harus bisa diedit oleh KFT/approver

Arti traffic-light:

Warna

Makna

Implikasi

Hijau

Mendukung adopsi

Domain ini memberi argumen positif

Kuning

Ada ketidakpastian/perlu pembatasan

Perlu diskusi, monitoring, negosiasi harga, atau kriteria akses

Merah

Tidak mendukung adopsi

Risiko/biaya/ketidaklayakan besar atau bukti tidak cukup

Rules rekomendasi awal:

Kondisi

Rekomendasi awal

Benefit favorable, harms acceptable, feasibility feasible, budget impact acceptable

Adopt

Benefit favorable, tetapi budget impact tinggi atau certainty rendah

Adopt with criteria-based access

Benefit uncertain dan cost-effectiveness unfavorable

Defer pending additional evidence

Harms unacceptable atau feasibility not feasible

Do not adopt

Benefit baik tetapi ICER sensitif pada harga obat

Reassess after price negotiation

A. Tujuan Step 10

Step 10 bertujuan membantu KFT melihat hasil penilaian secara cepat dan konsisten.

Tanpa Step 10, KFT hanya punya banyak isian EtD. Dengan Step 10, sistem dapat merangkum:

Pertanyaan

Dijawab oleh Step 10

Domain mana yang mendukung adopsi?

Ditampilkan sebagai hijau

Domain mana yang masih meragukan/perlu pembatasan?

Ditampilkan sebagai kuning

Domain mana yang tidak mendukung adopsi?

Ditampilkan sebagai merah

Berdasarkan pola warna, apa rekomendasi awalnya?

Sistem memberi draft recommendation

Apakah perlu CBA/restriksi?

Sistem memberi sinyal bila rekomendasi bersyarat

Apakah perlu negosiasi harga?

Sistem memberi rekomendasi reassess after price negotiation

Apakah keputusan perlu ditunda?

Sistem memberi rekomendasi defer

B. Input yang digunakan sistem pada Step 10

Step 10 menggunakan hasil dari Step 9 dan Step 8.

Input

Sumber

Contoh

EtD judgement per domain

etd_appraisals / etd_scores

benefits = favorable

Rationale per domain

etd_rationales

manfaat klinis mendukung

Traffic-light mapping

etd_rubrics atau traffic_light_rules

favorable = green

Hasil CEA

cea_results

ICER, incremental cost

Hasil BIA

bia_results

budget impact skenario 10/30/50%

Evidence version

version_history

evidence_v0.1

Local input version

local_input_versions

local_input_v0.1

Calculation run

calculation_runs

CALC_2026_001

Recommendation rules

recommendation_rules

if benefits green and budget red → restrict

C. Output Step 10

Output Step 10 terdiri dari dua bagian besar.

1. Traffic-light summary

Contoh:

Domain EtD

Judgement

Traffic-light

Rationale ringkas

Problem priority

High

Green

HFrEF memiliki beban klinis dan biaya tinggi

Benefits

Favorable

Green

ARNI menurunkan rehospitalisasi dibanding ACEI

Harms

Concern

Yellow

Perlu monitoring hipotensi, kalium, fungsi ginjal

Certainty

Low/Moderate

Yellow

Data lokal observasional, perlu dukungan literatur

Cost-effectiveness

Uncertain

Yellow

ICER bergantung pada harga obat

Budget impact

High

Red/Yellow

Dampak anggaran tinggi jika uptake besar

Equity

Neutral/Improve

Yellow/Green

Akses perlu dibatasi pada pasien eligible

Feasibility

Feasible with constraints

Yellow

Perlu SOP monitoring dan prescriber

Acceptability

Mixed/High

Yellow/Green

Perlu persetujuan klinisi dan manajemen

2. Draft recommendation

Contoh:

Adopt with criteria-based access

Dengan draft narasi:

Berdasarkan manfaat klinis yang mendukung, risiko yang masih dapat dikelola dengan monitoring, tetapi adanya ketidakpastian pada biaya dan dampak anggaran, sistem merekomendasikan ARNI untuk dipertimbangkan masuk formularium dengan criteria-based access.

D. Arti warna traffic-light

Tim IT perlu membuat definisi warna yang konsisten.

Warna

Makna

Implikasi keputusan

Green

Mendukung adopsi

Domain ini memberi argumen positif untuk masuk formularium

Yellow

Ada ketidakpastian atau perlu pembatasan

Perlu diskusi, monitoring, negosiasi harga, atau criteria-based access

Red

Tidak mendukung adopsi

Risiko, biaya, ketidakpastian, atau ketidaklayakan terlalu besar

Dokumen teknis menjelaskan bahwa hijau berarti mendukung adopsi, kuning berarti masih ada ketidakpastian atau perlu pembatasan, sedangkan merah berarti tidak mendukung adopsi.

E. Mapping judgement ke traffic-light

Tim IT harus membuat tabel mapping. Mapping ini sebaiknya disimpan di database, bukan di-hardcode, agar nanti bisa diubah tanpa mengubah source code.

1. Mapping umum

Domain

Judgement

Traffic-light

Problem priority

High

Green

Problem priority

Moderate

Yellow

Problem priority

Low

Red

Benefits

Favorable

Green

Benefits

Uncertain

Yellow

Benefits

Unfavorable

Red

Harms

Acceptable

Green

Harms

Concern

Yellow

Harms

Unacceptable

Red

Certainty

High

Green

Certainty

Moderate

Green/Yellow, sesuai kebijakan

Certainty

Low

Yellow

Certainty

Very low

Red

Cost-effectiveness

Favorable

Green

Cost-effectiveness

Uncertain

Yellow

Cost-effectiveness

Unfavorable

Red

Budget impact

Low

Green

Budget impact

Moderate

Yellow

Budget impact

High

Red atau Yellow, sesuai rule KFT

Equity

Improve

Green

Equity

Neutral

Yellow

Equity

Worsen

Red

Feasibility

Feasible

Green

Feasibility

Feasible with constraints

Yellow

Feasibility

Not feasible

Red

Acceptability

High

Green

Acceptability

Mixed

Yellow

Acceptability

Low

Red

Untuk MVP, saya sarankan Budget impact = High diberi Yellow atau Red tergantung konteks. Bila obat tetap bermanfaat klinis tetapi budget impact tinggi, rekomendasi biasanya bukan langsung “Do not adopt”, tetapi “Adopt with criteria-based access” atau “Reassess after price negotiation”.

F. Recommendation engine: aturan rekomendasi awal

Sistem harus membuat rekomendasi awal berdasarkan pola traffic-light.

1. Rekomendasi: Adopt

Dipakai bila mayoritas domain mendukung.

Kondisi

Rekomendasi

Benefits = Green

Harms = Green atau Yellow ringan

Certainty = Green atau Yellow

Cost-effectiveness = Green

Budget impact = Green atau Yellow

Feasibility = Green

Acceptability = Green atau Yellow

Tidak ada Red pada domain kritis

Output:

Adopt

Contoh narasi:

Sistem merekomendasikan adopsi karena manfaat klinis mendukung, risiko dapat diterima, kelayakan implementasi baik, dan dampak anggaran masih dapat dikelola.

2. Rekomendasi: Adopt with criteria-based access

Ini kemungkinan paling realistis untuk obat berbiaya tinggi seperti ARNI.

Kondisi

Rekomendasi

Benefits = Green

Harms = Green/Yellow

Feasibility = Green/Yellow

Budget impact = Yellow/Red

Cost-effectiveness = Yellow/Uncertain

Certainty = Yellow/Low

Perlu pembatasan pasien eligible atau monitoring

Output:

Adopt with criteria-based access

Contoh narasi:

Sistem merekomendasikan adopsi bersyarat karena manfaat klinis mendukung, tetapi terdapat ketidakpastian pada biaya dan dampak anggaran. Penggunaan perlu dibatasi pada pasien HFrEF yang memenuhi kriteria klinis dan monitoring.

Dokumen teknis juga menyebut bahwa bila benefit favorable tetapi budget impact tinggi atau certainty rendah, rekomendasi awal adalah Adopt with criteria-based access.

3. Rekomendasi: Defer pending additional evidence

Dipakai bila bukti belum cukup.

Kondisi

Rekomendasi

Benefits = Yellow/Uncertain

Certainty = Red atau Very low

Cost-effectiveness = Yellow/Uncertain

Data biaya lokal belum lengkap

Evidence utama belum cukup

Output:

Defer pending additional evidence

Contoh narasi:

Sistem merekomendasikan penundaan keputusan sampai tersedia data tambahan terkait efektivitas, keamanan, biaya lokal, atau dampak anggaran.

4. Rekomendasi: Do not adopt

Dipakai bila ada masalah besar pada manfaat, risiko, atau feasibility.

Kondisi

Rekomendasi

Benefits = Red / Unfavorable

Harms = Red / Unacceptable

Feasibility = Red / Not feasible

Cost-effectiveness = Red dan Budget impact = Red

Tidak ada cara realistis untuk restriksi/monitoring

Output:

Do not adopt

Contoh narasi:

Sistem tidak merekomendasikan adopsi karena manfaat klinis tidak jelas, risiko tidak dapat diterima, atau implementasi tidak feasible pada kondisi RS saat ini.

Dokumen teknis menyebut bahwa bila harms unacceptable atau feasibility not feasible, rekomendasi awal adalah Do not adopt.

5. Rekomendasi: Reassess after price negotiation

Dipakai bila manfaat klinis baik, tetapi harga/ICER/BIA terlalu tinggi.

Kondisi

Rekomendasi

Benefits = Green

Harms = Green/Yellow

Feasibility = Green/Yellow

Cost-effectiveness = Red atau Yellow karena harga

Budget impact = Red

Sensitivity harga menunjukkan hasil membaik bila harga turun

Output:

Reassess after price negotiation

Contoh narasi:

Sistem merekomendasikan penilaian ulang setelah negosiasi harga karena manfaat klinis mendukung, tetapi ICER dan budget impact saat ini terlalu tinggi.

Dokumen teknis juga menyebut bahwa bila benefit baik tetapi ICER sensitif pada harga obat, rekomendasi awal dapat berupa Reassess after price negotiation.

G. Domain kritis yang harus diperhatikan

Tidak semua domain memiliki bobot yang sama secara praktis. Untuk MVP, tim IT dapat menggunakan aturan sederhana:

Domain kritis

Domain

Mengapa kritis?

Benefits

Jika tidak ada manfaat, sulit diadopsi

Harms

Jika risiko tidak dapat diterima, tidak boleh diadopsi

Certainty

Jika bukti sangat rendah, perlu hati-hati

Cost-effectiveness

Penting untuk obat mahal

Budget impact

Penting untuk formularium RS

Feasibility

Jika tidak bisa diterapkan, keputusan tidak realistis

Domain pendukung

Domain

Fungsi

Equity

Menilai akses dan keadilan

Acceptability

Menilai penerimaan klinisi/manajemen/pasien

Problem priority

Menilai pentingnya masalah

Untuk MVP, aturan sederhana:

Jika Benefits Red, Harms Red, atau Feasibility Red, sistem sebaiknya tidak memberi rekomendasi “Adopt”.Jika Benefits Green tetapi Budget Impact Red, sistem sebaiknya memberi rekomendasi “Adopt with criteria-based access” atau “Reassess after price negotiation”.

H. Contoh rule engine sederhana untuk MVP

Tim IT bisa mulai dengan if-then rule seperti ini.

IF benefits = GreenAND harms != RedAND feasibility != RedAND budget_impact != RedTHEN recommendation = AdoptIF benefits = GreenAND harms != RedAND feasibility != RedAND (budget_impact = Red OR cost_effectiveness = Yellow OR certainty = Yellow)THEN recommendation = Adopt with criteria-based accessIF benefits = YellowAND certainty = RedTHEN recommendation = Defer pending additional evidenceIF benefits = RedOR harms = RedOR feasibility = RedTHEN recommendation = Do not adoptIF benefits = GreenAND budget_impact = RedAND cost_effectiveness = RedAND price_sensitivity = improves_with_price_reductionTHEN recommendation = Reassess after price negotiation

I. Bagaimana jika ada konflik antar-domain?

Contoh:

Benefits = Green

Harms = Yellow

Certainty = Yellow

Budget impact = Red

Feasibility = Green

Sistem jangan langsung “Do not adopt”. Untuk kasus seperti ini, rekomendasi lebih tepat:

Adopt with criteria-based access atau Reassess after price negotiation

Contoh logika:

Pola konflik

Rekomendasi

Manfaat baik, biaya tinggi

Restrict atau price negotiation

Manfaat baik, bukti rendah

Restrict/defer dengan monitoring

Manfaat baik, feasibility terbatas

Restrict dengan SOP implementasi

Manfaat tidak jelas, biaya tinggi

Defer atau do not adopt

Risiko tinggi

Do not adopt atau defer

Feasibility tidak ada

Do not adopt

J. Tampilan UI yang perlu dibuat IT

Tim IT perlu membuat halaman EtD Summary & Draft Recommendation.

Contoh tampilan:

EtD Summary & RecommendationCase ID: HF_ARNI_ACEI_001Session ID: KFT_2026_ARNI_001Evidence version: evidence_v0.1Local input version: local_input_v0.1Calculation run: CALC_2026_001Traffic-light Summary:[Problem priority] Green[Benefits] Green[Harms] Yellow[Certainty] Yellow[Cost-effectiveness] Yellow[Budget impact] Red[Equity] Yellow[Feasibility] Yellow[Acceptability] YellowSystem-generated draft recommendation:Adopt with criteria-based accessSystem rationale:Benefits are favorable, harms are manageable with monitoring, but budget impact is high and cost-effectiveness is uncertain. Use should be restricted to eligible HFrEF patients with monitoring criteria.Recommended next action:Complete Criteria-Based Access form.Buttons:[Accept draft][Edit recommendation][Send to CBA form][Return to EtD appraisal][Generate policy brief draft][View audit trail]

K. Data yang harus disimpan pada Step 10

Minimal database untuk Step 10:

1. Tabel traffic_light_summary

Field

Contoh

summary_id

TLS_001

session_id

KFT_2026_ARNI_001

case_id

HF_ARNI_ACEI_001

domain

benefits

judgement

Favorable

traffic_light

Green

rationale

“ARNI menurunkan rehospitalisasi.”

created_at

timestamp

2. Tabel recommendation_drafts

Field

Contoh

recommendation_draft_id

REC_DRAFT_001

session_id

KFT_2026_ARNI_001

case_id

HF_ARNI_ACEI_001

draft_recommendation

Adopt with criteria-based access

draft_rationale

manfaat mendukung, BIA tinggi

generated_by

system

generated_at

timestamp

rule_triggered

benefit_green_budget_red

status

draft

3. Tabel recommendation_rules

Field

Contoh

rule_id

RULE_002

rule_name

benefit favorable but budget high

conditions_json

{benefits: green, budget_impact: red}

recommendation_output

Adopt with criteria-based access

priority_order

2

active

true

L. Rekomendasi awal tidak boleh langsung menjadi keputusan final

Ini penting untuk IT.

Sistem boleh menghasilkan:

draft recommendation

Tetapi keputusan final tetap oleh Ketua KFT/Approver pada Step 13.

Jadi status rekomendasi harus dibedakan:

Status

Makna

system_draft

Rekomendasi awal dari sistem

edited_by_kft

Rekomendasi sudah diedit KFT

pending_approval

Menunggu Ketua KFT

approved

Disetujui

locked

Dikunci sebagai keputusan final

Pada Step 10, status maksimal adalah:

system_draft atau pending_kft_review

Belum locked.

M. Kapan sistem mengarahkan ke CBA form?

Jika rekomendasi awal adalah:

Adopt with criteria-based access

maka sistem harus otomatis menampilkan pesan:

“Recommendation requires criteria-based access. Please complete CBA form.”

Lalu tombol:

Go to Criteria-Based Access

CBA akan diisi pada Step 11.

Contoh rule:

IF recommendation = "Adopt with criteria-based access"THEN cba_required = trueAND next_step = "Complete CBA form"

N. Validasi Step 10

Sebelum sistem menampilkan rekomendasi awal, sistem harus memastikan:

Validasi

Aturan

Semua domain wajib sudah diisi

Jika belum, jangan generate rekomendasi final

Rationale domain wajib ada

Jika kosong, tampilkan warning

Traffic-light mapping tersedia

Jika tidak, tampilkan error konfigurasi

Recommendation rules aktif

Minimal satu rule aktif

Case belum locked

Jika sudah locked, hanya view-only

Session ID tersedia

Harus ada

Evidence/local input/calculation version tercatat

Untuk audit

Jika belum semua domain terisi, sistem menampilkan:

“EtD appraisal belum lengkap. Rekomendasi awal belum dapat dibuat.”

O. Audit trail Step 10

Setiap proses generate rekomendasi harus dicatat.

Aktivitas

Data yang dicatat

Generate traffic-light

domain, judgement, warna, rule mapping

Generate recommendation

rule yang aktif, output rekomendasi

Edit recommendation draft

teks lama, teks baru, user

Accept draft

user, timestamp

Send to CBA

user, timestamp

Regenerate recommendation

alasan, perubahan input, versi

Dokumen teknis menyebut audit trail harus mencatat perubahan judgement EtD, rekomendasi, template, input version, output file, dan approval/lock decision.

P. Flowchart Step 10

Q. Pseudocode untuk tim IT

1. User opens EtD Summary page.2. System loads:      session_id      case_id      etd_appraisals      etd_rationales      evidence_version_id      local_input_version_id      calculation_run_id.3. Check whether all required EtD domains are completed.4. If incomplete:      show missing domains and stop recommendation generation.5. For each domain:      map judgement to traffic_light using traffic_light_rules.6. Save traffic_light_summary.7. Load active recommendation_rules.8. Evaluate rules in priority order:      a. Do not adopt rules      b. Adopt with CBA rules      c. Reassess after price negotiation rules      d. Defer rules      e. Adopt rules9. Select first matched rule or mark manual_review_required.10. Generate draft recommendation and draft rationale.11. If recommendation requires CBA:      set cba_required = true.12. Save to recommendation_drafts.13. Write audit log:      rule_triggered,      input domains,      output recommendation,      user/system,      timestamp.14. Display EtD traffic-light summary and draft recommendation.

R. Rule priority yang disarankan

Agar aman, tim IT perlu mengevaluasi rule dengan urutan prioritas. Jangan langsung menghitung mayoritas warna, karena satu domain merah seperti harms bisa sangat penting.

Urutan prioritas yang disarankan:

Prioritas

Rule

1

Jika harms Red atau feasibility Red → Do not adopt

2

Jika benefits Red → Do not adopt atau Defer

3

Jika benefits Green tetapi budget/cost Red → Adopt with CBA atau Reassess after price negotiation

4

Jika certainty Red dan benefits tidak kuat → Defer

5

Jika benefits Green, harms tidak Red, feasibility tidak Red → Adopt atau Adopt with CBA

6

Jika tidak ada rule cocok → Manual review required

S. Acceptance criteria Step 10 untuk tim IT

Step 10 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Membaca hasil EtD appraisal per session

Ya

Mengecek semua domain wajib sudah terisi

Ya

Memetakan judgement ke Green/Yellow/Red

Ya

Menampilkan traffic-light summary per domain

Ya

Menampilkan rationale ringkas per domain

Ya

Menjalankan recommendation rules

Ya

Menghasilkan draft recommendation

Ya

Menghasilkan draft rationale otomatis

Ya

Menandai apakah CBA diperlukan

Ya

Mengarahkan user ke CBA form bila perlu

Ya

Mengizinkan KFT/Approver mengedit draft recommendation

Ya

Menyimpan recommendation draft ke database

Ya

Mencatat rule yang memicu rekomendasi

Ya

Mencatat audit trail

Ya

Membedakan rekomendasi sistem dan keputusan final

Ya

Mengirim hasil ke policy brief generator

Ya

T. Pesan untuk tim IT

Pada Step 10, sistem DeciBridge harus membaca hasil EtD appraisal dari Step 9 berdasarkan session_id dan case_id. Sistem kemudian memetakan judgement setiap domain ke traffic-light Green/Yellow/Red menggunakan tabel mapping yang dapat dikonfigurasi. Setelah itu sistem menampilkan ringkasan traffic-light per domain beserta rationale ringkas.

Sistem juga harus menjalankan rule-based recommendation engine untuk menghasilkan rekomendasi awal. Pilihan rekomendasi awal minimal adalah Adopt, Adopt with criteria-based access, Defer pending additional evidence, Do not adopt, dan Reassess after price negotiation. Rekomendasi awal ini harus disimpan sebagai system_draft, bukan keputusan final. Jika rekomendasi adalah Adopt with criteria-based access, sistem harus menandai cba_required = true dan mengarahkan user ke form CBA pada Step 11.

Sistem harus mencatat session_id, case_id, judgement domain, traffic-light, rule yang terpicu, draft recommendation, draft rationale, evidence_version_id, local_input_version_id, calculation_run_id, dan timestamp. Semua proses generate atau edit rekomendasi harus masuk audit trail. Keputusan final tetap dilakukan oleh Ketua KFT/Approver pada tahap review, approve, dan lock decision.

Kesimpulan sederhana

Step 10 adalah tahap ringkasan keputusan awal.

Tim IT harus membuat sistem yang dapat:

membaca EtD judgement;

mengubah judgement menjadi warna hijau/kuning/merah;

menampilkan traffic-light summary;

menjalankan recommendation rules;

membuat draft rekomendasi otomatis;

memberi tanda bila perlu criteria-based access;

menyimpan draft rekomendasi;

mencatat semua proses ke audit trail.

Yang penting: rekomendasi dari sistem bukan keputusan final, tetapi draft awal untuk membantu KFT mengambil keputusan secara lebih cepat, transparan, dan terdokumentasi.

Step 11 — Jika rekomendasi bersyarat, KFT mengisi criteria-based access, maksudnya: Jika sistem menghasilkan rekomendasi awal “Adopt with criteria-based access”, maka sistem harus membuka form Criteria-Based Access/CBA. KFT mengisi kriteria pasien yang boleh menerima obat, kriteria klinis, pembatasan prescriber, monitoring, durasi evaluasi, stop rule, dan rencana review. CBA ini akan masuk ke recommendation record dan policy brief.

Step 11 adalah tahap ketika KFT mengisi kriteria pembatasan penggunaan obat, jika rekomendasi awal dari sistem adalah “Adopt with criteria-based access” atau “diadopsi bersyarat.”

Komponen

Isi

Tujuan

Membatasi penggunaan obat agar tepat pasien, aman, dan terkendali biaya

Aktor

KFT member, Farmasi RS, Ketua KFT

Input

Kriteria diagnosis, klinis, prescriber, monitoring, stop rule

Proses sistem

Form CBA diisi jika rekomendasi = adopt with criteria-based access

Output

Structured CBA criteria

Database

access_criteria, recommendations

Audit trail

Mencatat perubahan CBA, user, timestamp

Catatan IT

Form CBA hanya wajib jika rekomendasi bersyarat

Contoh CBA untuk ARNI pada HFrEF:

Jenis kriteria

Contoh isi

Diagnosis

HFrEF confirmed

EF

EF ≤40% atau sesuai definisi lokal RS

Clinical status

NYHA II–IV atau risiko rehospitalisasi tinggi

Prior therapy

Sudah mendapat GDMT optimal bila tidak ada kontraindikasi

Renal function

eGFR ≥30 mL/min/1,73 m²

Potassium

K+ tidak tinggi, misalnya ≤5,2 mmol/L sesuai SOP lokal

Prescriber

Dokter jantung/penyakit dalam sesuai kebijakan RS

Monitoring

Tekanan darah, kreatinin/eGFR, kalium 1–2 minggu setelah mulai/titrasi

Stop rule

Hipotensi simptomatik, AKI, hiperkalemia, atau intoleransi

A. Apa itu Criteria-Based Access/CBA?

Criteria-Based Access adalah aturan yang menentukan:

“Pasien seperti apa yang boleh mendapat obat ini, siapa yang boleh meresepkan, apa yang harus dimonitor, dan kapan obat harus dihentikan.”

Untuk obat mahal seperti ARNI, KFT mungkin tidak langsung berkata:

“Semua pasien gagal jantung boleh memakai ARNI.”

Tetapi lebih realistis:

“ARNI boleh masuk formularium, tetapi hanya untuk pasien HFrEF tertentu yang memenuhi kriteria klinis, dengan monitoring tekanan darah, fungsi ginjal, dan kalium.”

Jadi, CBA adalah cara agar keputusan KFT menjadi:

lebih aman, karena ada monitoring;

lebih hemat, karena obat mahal dibatasi pada pasien yang paling membutuhkan;

lebih adil, karena kriteria akses jelas;

lebih mudah diaudit, karena alasan penggunaan obat terdokumentasi.

B. Kapan Step 11 muncul?

Step 11 tidak selalu muncul. Step ini hanya aktif jika rekomendasi awal atau rekomendasi KFT adalah:

Adopt with criteria-based access

atau

Restrict

Flow sederhananya:

C. Siapa yang mengisi CBA?

Role

Peran pada Step 11

KFT Member

Memberi masukan kriteria klinis dan monitoring

Ketua KFT / Approver

Menyetujui CBA final

Sekretaris KFT / Farmasi RS

Menginput hasil konsensus CBA ke sistem

Klinisi terkait

Memberi masukan kriteria diagnosis, EF, NYHA, monitoring, stop rule

Analis HTA

Membantu memastikan CBA konsisten dengan evidence, CEA/BIA, dan EtD

Tim IT

Membuat form CBA, validasi, database, versioning, dan audit trail

Untuk MVP, yang paling praktis:

Sekretaris KFT atau Analis HTA mengisi CBA sebagai “consensus recorder” berdasarkan hasil diskusi KFT. Ketua KFT kemudian menyetujui CBA saat approve/lock decision.

D. Apa yang harus dibuat tim IT?

Tim IT perlu membuat halaman:

Criteria-Based Access Form

Contoh struktur halaman:

Criteria-Based Access FormCase ID: HF_ARNI_ACEI_001Session ID: KFT_2026_ARNI_001Recommendation draft: Adopt with criteria-based accessStatus: draft / complete / approved / lockedSections:1. Eligibility criteria2. Clinical criteria3. Prior therapy requirement4. Contraindication/exclusion criteria5. Prescriber restriction6. Monitoring plan7. Stop rule8. Review timeline9. Implementation notesActions:- Save draft- Validate CBA- Mark CBA complete- Send to policy brief- View audit trail

E. Isi form CBA yang perlu dibuat

1. Eligibility criteria

Bagian ini menentukan pasien mana yang boleh menerima obat.

Contoh untuk ARNI:

Field

Contoh isi

diagnosis_required

HFrEF confirmed

ef_threshold

EF ≤40%

nyha_class

NYHA II–IV

clinical_status

Pasien simptomatik atau risiko rehospitalisasi

age_group

Dewasa, bila diperlukan

setting

Rawat jalan/rawat inap sesuai kebijakan RS

Contoh narasi:

ARNI hanya diberikan pada pasien HFrEF terkonfirmasi dengan EF ≤40%, NYHA II–IV, dan masih simptomatik meskipun telah mendapat terapi standar.

Dokumen teknis memberi contoh CBA ARNI pada HFrEF: diagnosis HFrEF confirmed, EF ≤40%, NYHA II–IV, prior therapy, renal function, potassium, prescriber, monitoring, dan stop rule.

2. Prior therapy requirement

Bagian ini menjelaskan terapi sebelumnya yang harus sudah diberikan sebelum ARNI digunakan.

Field

Contoh isi

prior_therapy_required

Ya

prior_therapy_detail

Sudah mendapat GDMT optimal bila tidak ada kontraindikasi

acei_arb_requirement

Sudah menggunakan/tidak toleran ACEI/ARB sesuai kebijakan klinis

washout_requirement

Jika berpindah dari ACEI, perlu memperhatikan washout sesuai guideline/SOP

Contoh narasi:

Pasien telah mendapat terapi standar gagal jantung sesuai praktik klinis RS, dan penggunaan ARNI dipertimbangkan bila pasien tetap simptomatik atau memiliki risiko rehospitalisasi.

3. Exclusion criteria / kontraindikasi

Bagian ini menentukan pasien yang tidak boleh menerima obat.

Field

Contoh isi

exclusion_hypotension

Hipotensi simptomatik

exclusion_hyperkalemia

Kalium tinggi, misalnya >5,2 atau >5,5 mmol/L sesuai SOP

exclusion_renal

eGFR <30 mL/min/1,73 m² atau sesuai kebijakan RS

exclusion_aki

Acute kidney injury aktif

exclusion_intolerance

Riwayat intoleransi/angioedema, bila relevan

Contoh narasi:

ARNI tidak diberikan pada pasien dengan hipotensi simptomatik, hiperkalemia bermakna, gangguan ginjal berat, AKI aktif, atau riwayat intoleransi terhadap obat terkait.

4. Prescriber restriction

Bagian ini menentukan siapa yang boleh meresepkan.

Field

Contoh isi

prescriber_allowed

Dokter jantung / penyakit dalam

approval_required

Ya/tidak

approval_by

KFT / DPJP / Farmasi klinik

dispensing_restriction

Sesuai formularium dan persetujuan internal

Contoh narasi:

ARNI diresepkan oleh dokter jantung atau dokter penyakit dalam sesuai kebijakan RS, dengan dokumentasi indikasi dan monitoring awal.

5. Monitoring plan

Bagian ini menjelaskan apa yang harus dipantau setelah obat diberikan.

Parameter monitoring

Waktu monitoring

Catatan

Tekanan darah

Awal terapi dan saat titrasi

untuk mendeteksi hipotensi

Kreatinin/eGFR

1–2 minggu setelah mulai/titrasi

untuk fungsi ginjal

Kalium

1–2 minggu setelah mulai/titrasi

untuk hiperkalemia

Gejala klinis

setiap kontrol

sesak, edema, toleransi

Rehospitalisasi

selama follow-up

outcome implementasi

Adverse event

selama terapi

hipotensi, AKI, hiperkalemia

Contoh narasi:

Monitoring meliputi tekanan darah, kreatinin/eGFR, dan kalium pada awal terapi dan 1–2 minggu setelah inisiasi atau titrasi, serta evaluasi gejala klinis dan kejadian rehospitalisasi.

6. Stop rule

Stop rule adalah aturan kapan obat harus dihentikan atau dievaluasi ulang.

Field

Contoh isi

stop_hypotension

Hipotensi simptomatik persisten

stop_hyperkalemia

Kalium meningkat bermakna sesuai SOP

stop_renal

Penurunan eGFR signifikan atau AKI

stop_intolerance

Intoleransi obat

stop_no_benefit

Tidak ada perbaikan klinis setelah periode evaluasi

review_period

3 bulan / 6 bulan sesuai KFT

Contoh narasi:

Obat dihentikan atau dievaluasi ulang bila terjadi hipotensi simptomatik persisten, AKI, hiperkalemia, intoleransi obat, atau tidak ada manfaat klinis setelah periode evaluasi.

7. Review timeline

Bagian ini menentukan kapan keputusan formularium ditinjau ulang.

Field

Contoh isi

initial_review

3 bulan

routine_review

6–12 bulan

trigger_review

Jika harga berubah, BIA meningkat, atau ada sinyal safety

review_by

KFT / Instalasi Farmasi / Tim HTA

Contoh narasi:

Keputusan penggunaan ARNI ditinjau ulang setiap 6–12 bulan atau lebih cepat bila terjadi perubahan harga, peningkatan budget impact, atau laporan masalah keamanan.

F. Struktur database Step 11

Tim IT minimal perlu membuat tabel access_criteria.

Tabel access_criteria

Field

Contoh

access_criteria_id

CBA_001

case_id

HF_ARNI_ACEI_001

session_id

KFT_2026_ARNI_001

recommendation_draft_id

REC_DRAFT_001

criteria_type

eligibility / exclusion / monitoring / stop_rule

criteria_name

EF threshold

criteria_value

EF ≤40%

criteria_text

Pasien HFrEF dengan EF ≤40%

is_required

true

created_by

sekretaris_kft_01

created_at

timestamp

updated_by

user_id

updated_at

timestamp

status

draft / complete / approved / locked

Alternatif struktur lebih praktis untuk MVP

Untuk MVP, IT bisa menyimpan CBA sebagai satu record besar dalam tabel recommendations:

Field

Contoh

case_id

HF_ARNI_ACEI_001

session_id

KFT_2026_ARNI_001

recommendation

Adopt with criteria-based access

eligibility_criteria

teks

exclusion_criteria

teks

monitoring_plan

teks

stop_rule

teks

prescriber_restriction

teks

review_timeline

teks

Namun untuk jangka panjang, lebih baik CBA dibuat terstruktur per kriteria agar bisa ditampilkan, dicari, dan diaudit.

G. Validasi yang harus dibuat IT

Sebelum CBA dinyatakan lengkap, sistem perlu memvalidasi field wajib.

Field

Validasi

Diagnosis

tidak boleh kosong

Population/eligibility

tidak boleh kosong

Prescriber

tidak boleh kosong jika obat restriksi

Monitoring

wajib untuk obat dengan risiko klinis

Stop rule

wajib

Review timeline

wajib untuk keputusan bersyarat

Rationale CBA

wajib

Status recommendation

harus Adopt with criteria-based access atau restrict

Contoh error:

Kondisi

Pesan

Monitoring kosong

“Monitoring plan wajib diisi untuk rekomendasi bersyarat.”

Stop rule kosong

“Stop rule wajib diisi sebelum CBA dapat diselesaikan.”

Prescriber kosong

“Prescriber restriction perlu diisi untuk obat dengan criteria-based access.”

CBA belum lengkap

“Policy brief belum dapat difinalisasi karena CBA belum lengkap.”

H. Status CBA

Tim IT perlu membuat status CBA:

Status

Makna

not_required

Rekomendasi tidak bersyarat

required

Rekomendasi membutuhkan CBA

draft

CBA sedang diisi

incomplete

CBA belum lengkap

complete

CBA lengkap dan siap masuk policy brief

approved

Disetujui Ketua KFT

locked

Terkunci bersama keputusan final

Untuk Step 11, status maksimal sebaiknya:

complete

Sedangkan approved dan locked terjadi pada Step 13 saat Ketua KFT menyetujui keputusan.

I. Hubungan Step 11 dengan policy brief

CBA harus otomatis masuk ke policy brief.

Bagian policy brief yang diisi dari CBA:

Bagian policy brief

Isi dari CBA

Recommendation

Adopt with criteria-based access

Key conditions

ringkasan eligibility dan restriction

Criteria-based access

diagnosis, EF, NYHA, prior therapy

Monitoring plan

tekanan darah, kreatinin/eGFR, kalium

Stop rule

hipotensi, AKI, hiperkalemia, intoleransi

Implementation notes

prescriber, review timeline, dokumentasi

Audit info

session_id, version_id, approver

Dokumen teknis menyebut policy brief otomatis harus memuat rekomendasi KFT, syarat implementasi, criteria-based access, prescriber, monitoring, stop rule, dan rencana monitoring.

J. Contoh output CBA untuk kasus ARNI vs ACEI

Contoh yang bisa dijadikan default template di sistem:

Komponen

Isi contoh

Diagnosis

HFrEF terkonfirmasi

EF

EF ≤40% atau sesuai definisi lokal RS

Clinical status

NYHA II–IV atau pasien dengan risiko rehospitalisasi

Prior therapy

Sudah mendapat terapi standar/GDMT optimal bila tidak ada kontraindikasi

Renal function

eGFR ≥30 mL/min/1,73 m²

Potassium

K+ tidak tinggi, misalnya ≤5,2 mmol/L sesuai SOP lokal

Blood pressure

Tidak terdapat hipotensi simptomatik

Prescriber

Dokter jantung atau penyakit dalam sesuai kebijakan RS

Monitoring

Tekanan darah, kreatinin/eGFR, kalium 1–2 minggu setelah mulai/titrasi

Stop rule

Hipotensi simptomatik, AKI, hiperkalemia, intoleransi

Review timeline

Evaluasi 3–6 bulan, review formulary 6–12 bulan

K. Flowchart Step 11

L. Pseudocode sederhana untuk tim IT

1. System checks draft recommendation for session_id and case_id.2. If recommendation != "Adopt with criteria-based access":      set cba_required = false      skip CBA form      proceed to policy brief.3. If recommendation == "Adopt with criteria-based access":      set cba_required = true      open CBA form.4. User inputs:      eligibility criteria,      exclusion criteria,      prior therapy requirement,      prescriber restriction,      monitoring plan,      stop rule,      review timeline,      implementation notes.5. System validates required fields.6. If required fields missing:      show warning and keep CBA as draft/incomplete.7. If complete:      save CBA to access_criteria table.8. Link CBA with:      case_id,      session_id,      recommendation_draft_id,      evidence_version_id,      local_input_version_id.9. Write audit log:      user,      timestamp,      old value,      new value,      criteria changed.10. Send CBA data to policy brief generator.

M. Audit trail Step 11

Setiap perubahan CBA harus tercatat.

Aktivitas

Data yang dicatat

CBA form dibuka

user_id, case_id, session_id, timestamp

Eligibility diisi

nilai, user, timestamp

Monitoring diubah

nilai lama, nilai baru, user

Stop rule diubah

nilai lama, nilai baru, user

CBA dinyatakan complete

user, timestamp

CBA dikirim ke policy brief

user, timestamp

CBA direvisi

alasan revisi, user, timestamp

Audit ini penting karena pembatasan akses adalah bagian dari keputusan formal KFT.

N. Hubungan Step 11 dengan Step 12 dan Step 13

Step

Hubungan dengan CBA

Step 12 — Policy brief generator

CBA masuk otomatis ke bagian “Key conditions”, “Implementation”, “Monitoring”, dan “Stop rule”

Step 13 — Approve and lock

Ketua KFT menyetujui rekomendasi final dan CBA final

Step 14 — Decision record

CBA disimpan sebagai bagian dari decision record

Step 15 — Versioning

Jika CBA direvisi, sistem membuat versi baru tanpa menimpa CBA lama

O. Acceptance criteria Step 11 untuk tim IT

Step 11 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Mendeteksi rekomendasi bersyarat

Ya

Membuka CBA form hanya jika diperlukan

Ya

Mengisi eligibility criteria

Ya

Mengisi exclusion criteria

Ya

Mengisi prior therapy requirement

Ya

Mengisi prescriber restriction

Ya

Mengisi monitoring plan

Ya

Mengisi stop rule

Ya

Mengisi review timeline

Ya

Memvalidasi field wajib

Ya

Menyimpan CBA ke database

Ya

Menghubungkan CBA dengan case_id dan session_id

Ya

Menghubungkan CBA dengan recommendation draft

Ya

Mencatat audit trail

Ya

Mengirim CBA ke policy brief generator

Ya

Membedakan status draft, complete, approved, locked

Ya

Mencegah perubahan CBA setelah decision locked

Ya

P. Pesan untuk tim IT

Pada Step 11, sistem harus membuka Criteria-Based Access/CBA form jika rekomendasi awal adalah Adopt with criteria-based access atau restrict. Form CBA digunakan KFT untuk menentukan pasien yang boleh menerima obat, kriteria klinis, kriteria eksklusi, terapi sebelumnya, pembatasan prescriber, monitoring, stop rule, dan jadwal review.

Untuk kasus ARNI vs ACEI, contoh CBA meliputi HFrEF terkonfirmasi, EF ≤40%, NYHA II–IV, sudah mendapat terapi standar/GDMT optimal bila tidak ada kontraindikasi, eGFR memenuhi syarat, kalium tidak tinggi, tidak hipotensi simptomatik, prescriber dibatasi pada dokter jantung/penyakit dalam, monitoring tekanan darah, kreatinin/eGFR, dan kalium, serta stop rule untuk hipotensi simptomatik, AKI, hiperkalemia, atau intoleransi.

Sistem harus menyimpan CBA dengan case_id, session_id, recommendation_draft_id, criteria_type, criteria_name, criteria_value, criteria_text, status CBA, user, dan timestamp. Field monitoring, stop rule, eligibility, dan prescriber restriction harus wajib diisi sebelum CBA dianggap complete. Semua perubahan CBA harus masuk audit trail. CBA yang lengkap harus otomatis masuk ke policy brief dan decision record. Setelah keputusan di-lock oleh Ketua KFT, CBA tidak boleh diedit langsung; revisi harus dibuat sebagai versi baru.

Kesimpulan sederhana

Step 11 adalah tahap membuat aturan penggunaan obat bila rekomendasi bersyarat.

Untuk tim IT, yang harus dibuat adalah:

sistem mendeteksi rekomendasi bersyarat;

membuka form CBA;

menyediakan field eligibility, exclusion, prior therapy, prescriber, monitoring, stop rule, review timeline;

memvalidasi field wajib;

menyimpan CBA ke database;

menghubungkan CBA dengan case, session, dan recommendation;

memasukkan CBA ke policy brief;

mencatat audit trail;

mengunci CBA setelah keputusan final.

Dengan Step 11, DeciBridge tidak hanya berkata “obat diterima”, tetapi juga menjelaskan “diterima untuk pasien siapa, dengan syarat apa, dipantau bagaimana, dan kapan harus dievaluasi ulang.”

Step 12 — Sistem menghasilkan policy brief otomatis, maksudnya: Sistem mengambil data final/draft dari database berdasarkan case_id dan session_id, lalu mengisi template policy brief Word/DOCX secara otomatis. Policy brief harus dapat dipreview sebelum diekspor, dapat diekspor ke Word/PDF, dan versi final hanya dapat dikunci oleh Ketua KFT/Approver.

Step 12 ini juga disebut Policy Brief Generator: sistem membuat draft policy brief otomatis dari case metadata, evidence summary, hasil CEA/BIA, EtD traffic-light, rekomendasi, CBA, monitoring plan, dan audit/version information.

Step 12 adalah tahap ketika sistem DeciBridge membuat dokumen policy brief otomatis dari semua data yang sudah masuk sebelumnya: case metadata, evidence summary, CEA/BIA, EtD appraisal, rekomendasi, criteria-based access/CBA, dan audit information.

Dalam dokumen teknis, policy brief generator memang disebut sebagai dokumen otomatis 1–2 halaman untuk arsip dan keputusan KFT, dengan output minimal Word/PDF policy brief. Sistem juga harus mengisi template DOCX dari database dan hasil EtD, menyediakan preview sebelum export, dan menyimpan versi final bersama input_version_id dan audit trail.

Komponen

Isi

Tujuan

Membuat dokumen keputusan otomatis untuk arsip KFT/manajemen

Aktor

Sistem, HTA analyst, Sekretaris KFT

Input

Case metadata, evidence, CEA/BIA, EtD, recommendation, CBA, audit info

Proses sistem

Render template DOCX/PDF dari placeholder

Output

Policy brief 1–2 halaman

Database

policy_briefs, recommendations, audit_logs

Audit trail

Mencatat template version, input version, output file, user, timestamp

Catatan IT

Policy brief harus bisa preview sebelum export final

Isi policy brief otomatis:

Bagian policy brief

Isi otomatis dari sistem

Judul kasus

case_title, technology, comparator, indication

Pertanyaan keputusan

PICO dan tujuan penilaian

Ringkasan bukti klinis

effect estimate, outcome utama, certainty

Ringkasan manfaat-risiko

benefits, harms, safety monitoring

Ringkasan ekonomi

incremental cost, ICER, BIA, skenario sensitivitas

Pertimbangan EtD

traffic-light per domain dan rationale ringkas

Rekomendasi KFT

adopt/adopt with criteria/defer/do not adopt

Syarat implementasi

CBA, prescriber, monitoring, stop rule

Rencana monitoring

indikator outcome, penggunaan, biaya, review berkala

Audit information

version_id, tanggal rapat, approver, status locked

Dokumen teknis menyebut policy brief harus ringkas, siap dibaca dalam rapat manajemen/KFT, dapat menjadi arsip keputusan, dan detail bukti dapat diletakkan pada case pack/lampiran.

Penjelasan:

A. Tujuan Step 12

Tujuan Step 12 adalah membuat dokumen ringkas yang siap dibaca KFT/manajemen RS tanpa harus mengetik ulang semua hasil analisis secara manual.

Policy brief ini berfungsi sebagai:

Fungsi

Penjelasan

Bahan rapat KFT

Ringkasan keputusan obat dalam format singkat

Lampiran notulen

Bisa disimpan sebagai dokumen resmi rapat

Arsip keputusan formularium

Menjelaskan mengapa obat diterima/ditolak/ditunda

Bukti audit

Menunjukkan data, versi input, rationale, dan approver

Dokumen implementasi

Memuat kriteria akses, monitoring, dan stop rule jika obat diterima bersyarat

Jadi, policy brief bukan laporan panjang, tetapi dokumen ringkas 1–2 halaman yang menjawab:

“Obat ini dinilai untuk apa, buktinya apa, biayanya bagaimana, keputusan KFT apa, syarat implementasinya apa, dan data versi mana yang digunakan?”

B. Kapan Step 12 dilakukan?

Step 12 dilakukan setelah:

case pack sudah tersedia,

evidence summary sudah direview,

local input layer sudah diisi,

CEA/BIA sudah dijalankan,

EtD judgement dan rationale sudah diisi,

sistem sudah menampilkan traffic-light dan rekomendasi awal,

jika rekomendasi bersyarat, CBA sudah diisi.

Namun, sistem tetap boleh membuat draft policy brief walaupun sebagian data belum final. Bedanya, statusnya harus jelas:

Kondisi data

Status policy brief

Semua data lengkap

ready_for_approval

Harga/BIA belum lengkap

draft_with_warning

EtD belum lengkap

incomplete

CBA belum lengkap padahal rekomendasi bersyarat

cannot_finalize

Sudah disetujui Ketua KFT

approved

Sudah dikunci

locked_final

C. Data apa saja yang diambil sistem?

Policy brief generator harus mengambil data dari beberapa tabel/modul.

Bagian policy brief

Sumber data

Judul kasus

cases / case_meta

Pertanyaan keputusan

case_pack / PICO

Populasi, intervensi, comparator

cases, case_pack

Ringkasan bukti klinis

evidence_summary, clinical_outcomes, effect_estimates

Certainty evidence

certainty_assessments

Ringkasan manfaat-risiko

etd_appraisals, evidence_summary, safety notes

Ringkasan ekonomi

cea_results, bia_results, sensitivity_results

EtD traffic-light

traffic_light_summary, etd_scores

Rationale EtD

etd_rationales

Rekomendasi awal/final

recommendation_drafts, recommendations

Criteria-based access

access_criteria

Monitoring plan

access_criteria, monitoring_plan

Audit information

version_history, audit_logs, calculation_runs, approver

Dalam dokumen teknis, struktur policy brief otomatis memuat judul kasus, pertanyaan keputusan, ringkasan bukti klinis, ringkasan manfaat-risiko, ringkasan ekonomi, pertimbangan EtD, rekomendasi KFT, syarat implementasi, rencana monitoring, dan audit information.

D. Isi policy brief yang harus dibuat sistem

1. Document control

Bagian paling atas harus berisi identitas dokumen.

Field

Contoh

Brief ID

PB_HF_ARNI_ACEI_001_KFT_2026_001

Case ID

HF_ARNI_ACEI_001

Session ID

KFT_2026_ARNI_001

Meeting date

tanggal rapat KFT

Prepared by

Analis HTA/Sekretaris KFT

Approved by

Ketua KFT

Approved at

tanggal approval

Status

draft / approved / locked

Policy brief version

brief_v0.1 / brief_v1.0_locked

Tujuannya agar dokumen bisa diaudit.

2. Decision question

Bagian ini menjelaskan pertanyaan keputusan.

Contoh:

Apakah sacubitril/valsartan/ARNI perlu diadopsi dalam formularium RS untuk pasien HFrEF dibandingkan ACEI?

Field yang ditarik:

Field

Sumber

population

case pack

intervention

case metadata

comparator

case metadata

outcome

evidence summary

setting

case metadata

hospital_name

konfigurasi sistem

3. Executive summary

Bagian ini harus singkat.

Isi minimal:

Komponen

Contoh

Recommendation

Adopt with criteria-based access

Summary rationale

Manfaat klinis mendukung, tetapi biaya dan budget impact memerlukan pembatasan

Key conditions

Hanya untuk pasien HFrEF eligible dengan monitoring

Status

draft / pending approval / locked

Contoh narasi otomatis:

Berdasarkan ringkasan bukti klinis, hasil CEA/BIA, dan EtD appraisal, sistem menghasilkan rekomendasi awal Adopt with criteria-based access. ARNI menunjukkan manfaat klinis terhadap penurunan rehospitalisasi, tetapi dampak biaya perlu dikendalikan melalui pembatasan kriteria pasien dan monitoring.

4. Local inputs used

Bagian ini menjelaskan input lokal yang dipakai.

Parameter

Value

Source

Effective date

ARNI monthly cost

Rp…

e-catalog/kontrak RS Unud

tanggal

ACEI monthly cost

Rp…

e-catalog/kontrak RS Unud

tanggal

HF admission cost

Rp…

billing/unit cost/INA-CBG/proxy

tanggal

Eligible population

… pasien/tahun

SIMRS/rekam medis

tahun

Uptake

10%, 30%, 50%

asumsi KFT

tanggal

Bagian ini penting karena harga obat dan biaya bisa berubah. Bila data masih proxy, sistem harus menampilkan catatan:

“Input biaya menggunakan data proxy dan perlu diperbarui dengan data lokal RS Unud sebelum keputusan implementasi final.”

5. Evidence snapshot

Bagian ini menampilkan ringkasan bukti klinis.

Outcome

Time horizon

Intervention

Comparator

Effect

Notes

Rehospitalisasi

12 bulan

ARNI

ACEI

RR …

Local RWE/literatur

LOS

episode rawat inap

ARNI

ACEI

difference/summary

jika tersedia

Field yang ditarik:

outcome_name

time_horizon

events_treated

n_treated

events_control

n_control

effect_measure

effect_value

CI

certainty

source_note

6. Clinical interpretation

Sistem sebaiknya membuat interpretasi otomatis, misalnya:

Pada outcome rehospitalisasi 12 bulan, ARNI menunjukkan risiko rehospitalisasi lebih rendah dibanding ACEI berdasarkan data yang tersedia. Namun, interpretasi perlu mempertimbangkan sumber data, ukuran sampel, dan potensi keterbatasan bukti.

Bagian ini bisa dibuat otomatis, tetapi sebaiknya dapat diedit oleh Analis HTA sebelum export.

7. Economic summary

Bagian ini menampilkan hasil Step 8.

Komponen

Nilai

Incremental drug cost

Rp…

Hospitalisation cost offset

Rp…

Incremental total cost

Rp…

ICER

Rp… per rehospitalisasi dihindari

Budget impact 10% uptake

Rp…

Budget impact 30% uptake

Rp…

Budget impact 50% uptake

Rp…

Sensitivity result

harga -20%, base, +20%

Contoh narasi:

Dengan input lokal versi local_input_v0.1, ARNI menghasilkan incremental total cost sebesar Rp… per pasien per tahun dan ICER sebesar Rp… per rehospitalisasi yang dihindari. Pada skenario uptake 30%, estimasi dampak anggaran satu tahun adalah Rp….

Jika data belum lengkap:

“CEA/BIA belum final karena harga obat atau eligible population belum lengkap.”

8. EtD assessment

Bagian ini menampilkan domain EtD, traffic-light, dan rationale.

Domain

Rating

Rationale

Benefits

Green

ARNI menurunkan rehospitalisasi

Harms

Yellow

Perlu monitoring hipotensi, kalium, ginjal

Certainty

Yellow

Data lokal observasional

Cost-effectiveness

Yellow

ICER bergantung pada harga ARNI

Budget impact

Red/Yellow

Dampak anggaran perlu pembatasan

Feasibility

Yellow

Perlu SOP dan monitoring

Acceptability

Yellow

Perlu persetujuan klinisi/manajemen

Equity

Yellow/Green

CBA membantu akses lebih tepat sasaran

Dokumen teknis menyebut bagian pertimbangan EtD pada policy brief memuat traffic-light per domain dan rationale ringkas.

9. Recommendation and CBA

Bagian ini menarik data dari Step 10 dan Step 11.

Contoh:

Final recommendation/draft recommendation: Adopt with criteria-based access.

CBA yang ditampilkan:

Komponen

Isi

Diagnosis

HFrEF terkonfirmasi

EF

EF ≤40% atau sesuai definisi lokal RS

Clinical status

NYHA II–IV atau risiko rehospitalisasi

Prior therapy

sudah mendapat terapi standar/GDMT optimal

Renal function

eGFR sesuai batas SOP

Potassium

K+ tidak tinggi

Prescriber

dokter jantung/penyakit dalam

Monitoring

tekanan darah, kreatinin/eGFR, kalium

Stop rule

hipotensi simptomatik, AKI, hiperkalemia, intoleransi

Bagian ini wajib ada jika rekomendasi adalah Adopt with criteria-based access.

10. Implementation and monitoring plan

Bagian ini menjelaskan apa yang harus dilakukan setelah keputusan.

Komponen

Contoh isi

Implementation steps

sosialisasi formularium, pembatasan prescriber, form persetujuan

Monitoring indicators

jumlah pasien memakai ARNI, biaya aktual, rehospitalisasi, adverse event

Review timeline

3–6 bulan awal, lalu 6–12 bulan

Trigger review

harga berubah, BIA meningkat, safety signal

11. Audit information

Bagian ini sangat penting untuk DeciBridge.

Field

Contoh

Evidence version

evidence_v0.1

Local input version

local_input_v0.1

Calculation run ID

CALC_2026_001

EtD session ID

KFT_2026_ARNI_001

Recommendation draft ID

REC_DRAFT_001

CBA version

CBA_v0.1

Policy brief version

brief_v0.1

Generated by

user/system

Generated at

timestamp

Approved by

Ketua KFT

Locked at

timestamp

Dokumen teknis menyebut audit information pada policy brief harus memuat version_id, tanggal rapat, approver, dan status locked.

E. Apa yang harus dibuat tim IT?

Tim IT perlu membuat Policy Brief Generator Module.

Modul ini minimal terdiri dari:

Komponen teknis

Fungsi

Template manager

Menyimpan template DOCX policy brief

Placeholder mapping

Menghubungkan field template dengan database

Data fetcher

Mengambil data berdasarkan case_id dan session_id

Renderer

Mengisi template dengan data

Preview page

Menampilkan draft sebelum export

Export engine

Export ke DOCX dan/atau PDF

Versioning

Membuat versi policy brief

Audit log

Mencatat generate, preview, export, approval

Validation checker

Cek apakah data wajib lengkap sebelum final

Dokumen teknis menyarankan export engine menggunakan DOCX template + PDF converter untuk mendukung policy brief siap arsip dan penandatanganan.

F. Template dan placeholder

Tim IT perlu menggunakan file template Word, misalnya:

DeciBridge_PolicyBrief_Template.docx

Template ini harus berisi placeholder.

Contoh placeholder:

{{brief_id}}{{meeting_date}}{{case_id}}{{case_title}}{{intervention}}{{comparator}}{{population_definition}}{{setting}}{{clinical_summary}}{{economic_summary}}{{etd_table}}{{recommendation}}{{final_text}}{{cba_criteria}}{{monitoring_plan}}{{analysis_version}}{{inputs_version}}{{approved_by}}{{approved_at}}

Sistem harus mengganti placeholder tersebut dengan data dari database.

G. Mapping placeholder ke database

Placeholder

Sumber data

{{case_id}}

cases.case_id

{{case_title}}

cases.case_title

{{intervention}}

cases.technology

{{comparator}}

cases.comparator

{{population_definition}}

cases.population / case_pack.population

{{clinical_summary}}

evidence_summary

{{effect_value}}

effect_estimates.estimate

{{certainty}}

certainty_assessments.certainty_level

{{economic_summary}}

cea_results, bia_results

{{etd_table}}

traffic_light_summary, etd_rationales

{{recommendation}}

recommendation_drafts / recommendations

{{cba_criteria}}

access_criteria

{{monitoring_plan}}

access_criteria.monitoring

{{review_timeline}}

access_criteria.review_timeline

{{analysis_version}}

version_history

{{inputs_version}}

local_input_versions

{{approved_by}}

recommendations.approved_by

{{approved_at}}

recommendations.approved_at

H. Alur kerja teknis Step 12

I. Validasi sebelum policy brief dibuat

Sebelum export, sistem harus mengecek kelengkapan data.

1. Field wajib untuk draft policy brief

Data

Wajib untuk draft?

case_id

Ya

case_title

Ya

intervention

Ya

comparator

Ya

population

Ya

evidence summary

Ya

EtD traffic-light

Ya

recommendation draft

Ya

version_id

Ya

2. Field wajib untuk final policy brief

Data

Wajib untuk final?

semua field draft

Ya

CEA/BIA final atau catatan jelas

Ya

CBA jika rekomendasi bersyarat

Ya

approved_by

Ya

approved_at

Ya

lock status

Ya

audit/version information

Ya

Jika ada yang kurang, sistem harus menampilkan warning:

Kekurangan

Pesan

CEA/BIA belum final

“Policy brief dapat dibuat sebagai draft, tetapi belum dapat difinalisasi.”

CBA belum lengkap

“CBA wajib dilengkapi sebelum policy brief final.”

approved_by kosong

“Policy brief belum dapat dikunci karena belum ada approver.”

EtD belum lengkap

“EtD appraisal belum lengkap, policy brief belum dapat dibuat final.”

Ada placeholder kosong

“Masih ada placeholder yang belum terisi.”

J. Status policy brief

Tim IT perlu membuat status policy brief:

Status

Makna

not_generated

Belum dibuat

draft_generated

Draft berhasil dibuat

draft_with_warning

Draft dibuat tetapi ada data belum lengkap

ready_for_review

Siap direview Ketua KFT

approved

Disetujui

locked_final

Final dan tidak bisa diedit

superseded

Digantikan oleh versi baru

Pada Step 12, status biasanya:

draft_generated, draft_with_warning, atau ready_for_review.

Status approved dan locked_final terjadi pada Step 13.

K. Preview sebelum export

Tim IT harus membuat preview.

Tujuannya:

Analis HTA/Sekretaris KFT bisa melihat apakah isi sudah benar.

Placeholder kosong bisa terlihat.

Rekomendasi dan CBA bisa dicek.

Policy brief tidak langsung menjadi final.

Tombol yang disarankan:

Tombol

Fungsi

Generate Draft

Membuat draft policy brief

Preview

Melihat isi sebelum export

Edit draft text

Mengedit narasi tertentu jika diizinkan

Export DOCX

Export Word

Export PDF

Export PDF

Send to Approver

Kirim ke Ketua KFT

Regenerate from latest data

Membuat ulang dari data terbaru

View audit trail

Melihat riwayat

L. Apakah isi policy brief boleh diedit manual?

Untuk MVP, sebaiknya ada dua jenis field:

1. Field otomatis dan terkunci

Contoh:

case_id

effect estimate

ICER

BIA

version_id

calculation_run_id

Field ini tidak boleh diedit manual di policy brief, karena harus konsisten dengan database.

2. Field narasi yang boleh diedit terbatas

Contoh:

ringkasan narasi manfaat,

ringkasan rationale,

final recommendation text,

implementation notes.

Namun, jika diedit, sistem harus mencatat audit trail:

teks lama, teks baru, siapa mengubah, kapan, dan alasannya.

M. Versioning policy brief

Setiap generate/export harus punya versi.

Contoh:

Versi

Kondisi

brief_v0.1

draft pertama

brief_v0.2

revisi setelah CBA

brief_v0.3

revisi setelah Ketua KFT

brief_v1.0_locked

final setelah approval

brief_v1.1

versi baru jika harga/bukti berubah

Sistem tidak boleh menimpa policy brief lama.

Contoh tabel:

brief_id

case_id

session_id

version

status

generated_at

PB001

HF_ARNI_ACEI_001

KFT_2026_ARNI_001

v0.1

draft

tanggal

PB002

HF_ARNI_ACEI_001

KFT_2026_ARNI_001

v1.0

locked_final

tanggal

N. Database/tabel yang dibutuhkan

Minimal tabel:

Tabel

Fungsi

policy_brief_templates

Menyimpan template DOCX dan versinya

policy_briefs

Menyimpan metadata policy brief

policy_brief_versions

Menyimpan riwayat versi

policy_brief_exports

Menyimpan file DOCX/PDF yang diekspor

policy_brief_placeholders

Mapping placeholder ke field database

audit_logs

Mencatat generate/export/edit

version_history

Menghubungkan brief dengan evidence/local input/calculation/session

Contoh tabel policy_briefs

Field

Contoh

policy_brief_id

PB_001

case_id

HF_ARNI_ACEI_001

session_id

KFT_2026_ARNI_001

recommendation_id

REC_001

template_id

TPL_POLICY_001

brief_version

v0.1

status

draft_generated

generated_by

hta_analyst_01

generated_at

timestamp

file_docx_path

path file

file_pdf_path

path file

evidence_version_id

evidence_v0.1

local_input_version_id

local_input_v0.1

calculation_run_id

CALC_001

O. Audit trail Step 12

Setiap aktivitas harus dicatat.

Aktivitas

Data yang dicatat

Generate draft

user, case_id, session_id, template version, timestamp

Preview

user, timestamp

Export DOCX/PDF

user, file path, timestamp

Edit narasi

teks lama, teks baru, user, timestamp

Regenerate brief

alasan regenerate, versi input lama/baru

Send to approver

user, approver, timestamp

Final lock nanti di Step 13

approver, timestamp, final version

Dokumen teknis menyebut audit trail untuk generate policy brief harus mencatat template version, input version, dan output file.

P. Error handling

Tim IT harus menangani kondisi berikut:

Kondisi

Tindakan sistem

Template DOCX tidak ditemukan

tampilkan error “template tidak tersedia”

Placeholder tidak cocok

tampilkan daftar placeholder yang gagal

Data CEA/BIA kosong

buat draft dengan warning atau hentikan finalisasi

CBA kosong padahal wajib

tidak boleh final

Export PDF gagal

simpan DOCX, tampilkan pesan PDF gagal

Data berubah setelah brief dibuat

status brief menjadi outdated_needs_regeneration

Case sudah locked

policy brief hanya view/download, tidak bisa regenerate kecuali versi baru

Q. Pseudocode sederhana untuk IT

1. User clicks "Generate Policy Brief".2. System checks role:      HTA Analyst / Sekretariat KFT can generate draft.      Approver can approve/lock in Step 13.3. Load case_id and session_id.4. Fetch:      case metadata,      PICO,      evidence summary,      effect estimates,      certainty,      CEA results,      BIA results,      EtD traffic-light,      rationales,      recommendation,      CBA if required,      monitoring plan,      audit/version data.5. Validate required fields.6. If missing critical fields:      mark brief as draft_with_warning or cannot_finalize.7. Load active DOCX template.8. Replace placeholders with database values.9. Generate DOCX file.10. Optionally convert DOCX to PDF.11. Save file path and metadata to policy_briefs table.12. Create policy_brief_version.13. Write audit log.14. Show preview and export buttons.15. Send to approver if user chooses.

R. Acceptance criteria Step 12 untuk tim IT

Step 12 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Mengambil data berdasarkan case_id dan session_id

Ya

Mengisi template DOCX otomatis

Ya

Menghasilkan draft policy brief

Ya

Menampilkan preview sebelum export

Ya

Export ke DOCX

Ya

Export ke PDF

Idealnya ya, minimal DOCX untuk MVP

Mengisi bagian case, PICO, evidence, ekonomi, EtD, rekomendasi, CBA, monitoring, audit

Ya

Mendeteksi placeholder kosong

Ya

Memberi warning jika data belum final

Ya

Menyimpan versi policy brief

Ya

Mencatat template version dan input version

Ya

Menghubungkan policy brief dengan evidence/local input/calculation/session

Ya

Mengirim policy brief ke approver

Ya

Mencegah finalisasi jika CBA/approval belum lengkap

Ya

Tidak menimpa policy brief lama

Ya

S. Pesan untuk tim IT

Pada Step 12, sistem DeciBridge harus memiliki Policy Brief Generator. Modul ini mengambil data berdasarkan case_id dan session_id, lalu mengisi template policy brief DOCX secara otomatis. Data yang harus ditarik meliputi case metadata, PICO/decision question, evidence summary, effect estimates, certainty evidence, hasil CEA/BIA, traffic-light EtD, rationale per domain, rekomendasi, CBA jika ada, monitoring plan, serta audit/version information.

Sistem harus menggunakan template DOCX dengan placeholder, misalnya {{case_id}}, {{case_title}}, {{intervention}}, {{comparator}}, {{clinical_summary}}, {{economic_summary}}, {{etd_table}}, {{recommendation}}, {{cba_criteria}}, {{monitoring_plan}}, {{analysis_version}}, dan {{inputs_version}}. Sistem mengganti placeholder tersebut dengan data dari database, lalu menghasilkan policy brief dalam format DOCX dan bila memungkinkan PDF.

Policy brief harus dapat dipreview sebelum export. Jika ada data penting yang belum lengkap, sistem harus memberi status draft_with_warning atau cannot_finalize. Jika rekomendasi adalah Adopt with criteria-based access, maka CBA harus terisi sebelum policy brief bisa difinalisasi. Setiap generate, preview, edit, export, dan regenerate harus masuk audit trail. Policy brief final hanya dapat dikunci oleh Ketua KFT/Approver pada Step 13, dan versi final harus tersimpan bersama evidence version, local input version, calculation run, EtD session, dan audit trail.

Kesimpulan sederhana

Step 12 adalah tahap membuat dokumen output otomatis.

Untuk tim IT, yang harus dibuat adalah:

template DOCX dengan placeholder;

sistem mapping placeholder ke database;

fitur generate draft policy brief;

fitur preview;

export DOCX/PDF;

validasi data sebelum final;

versioning policy brief;

audit trail;

integrasi dengan approval/lock decision.

Jadi, Step 12 membuat DeciBridge menghasilkan dokumen keputusan yang siap dibaca, disimpan, diaudit, dan digunakan sebagai lampiran rapat KFT.

Step 13 — Ketua KFT melakukan review, approve, dan lock decision, maksudnya: Ketua KFT/Approver meninjau seluruh hasil DeciBridge, yaitu evidence summary, hasil CEA/BIA, EtD traffic-light, rationale, rekomendasi, CBA jika ada, dan draft policy brief. Jika sudah sesuai, Ketua KFT menyetujui rekomendasi final dan mengunci keputusan. Setelah decision locked, data keputusan final tidak boleh diedit langsung; setiap perubahan harus dibuat sebagai versi baru.

Step 13 adalah tahap pengesahan keputusan final oleh Ketua KFT/Approver. Pada tahap ini, sistem tidak lagi hanya menampilkan draft rekomendasi, tetapi meminta Ketua KFT melakukan review, memberi approval, lalu melakukan lock decision agar keputusan tidak dapat diubah sembarangan.

Dalam dokumen teknis DeciBridge, role Ketua KFT/Approver memang diberi hak untuk approve rekomendasi, lock decision, dan finalisasi policy brief, sedangkan perubahan setelah lock harus dibuat sebagai versi baru.

Komponen

Isi

Tujuan

Menetapkan keputusan final dan mencegah perubahan langsung setelah disetujui

Aktor

Ketua KFT/Approver

Input

Draft policy brief, rekomendasi final, CBA, EtD rationale

Proses sistem

Review → approve → lock decision

Output

Decision record terkunci

Database

recommendations, policy_briefs, version_history, audit_logs

Audit trail

Mencatat approver, timestamp, rekomendasi final

Catatan IT

Setelah locked, data final tidak bisa diedit langsung; perubahan harus menjadi versi baru

Status setelah lock:

Status

Makna

locked

Keputusan final sudah disahkan

archived

Keputusan lama disimpan sebagai arsip

new version created

Ada revisi karena bukti/harga baru

A. Tujuan Step 13

Tujuan Step 13 adalah memastikan bahwa keputusan KFT menjadi resmi, final, terdokumentasi, dan dapat diaudit.

Pada tahap ini sistem harus menjawab:

Siapa yang menyetujui keputusan?

Kapan keputusan disetujui?

Rekomendasi finalnya apa?

Data versi mana yang dipakai?

Hasil EtD mana yang dipakai?

Hasil CEA/BIA mana yang dipakai?

Apakah CBA sudah lengkap jika rekomendasi bersyarat?

Policy brief versi mana yang menjadi dokumen final?

Apakah keputusan sudah dikunci?

Jika nanti ada perubahan harga/bukti, apakah keputusan lama tetap tersimpan?

B. Bedakan “approve” dan “lock decision”

Untuk tim IT, ini penting.

Istilah

Makna

Review

Ketua KFT membaca dan mengecek semua komponen sebelum disahkan

Approve

Ketua KFT menyetujui rekomendasi final

Lock decision

Sistem mengunci seluruh data keputusan final agar tidak bisa diedit langsung

New version

Jika ada perubahan setelah lock, sistem membuat versi baru tanpa menimpa keputusan lama

Jadi, alurnya bukan langsung lock. Alur yang benar:

Review → jika ada revisi, kembalikan ke tim → jika sudah benar, approve → lock decision → simpan final record.

C. Kapan Step 13 bisa dilakukan?

Step 13 hanya boleh dilakukan jika syarat minimum terpenuhi.

Syarat sebelum approve/lock

Wajib?

Case metadata sudah lengkap

Ya

Evidence summary sudah direview

Ya

Local input version aktif tersedia

Ya

CEA/BIA sudah dijalankan atau ada catatan jika belum final

Ya

EtD judgement semua domain wajib sudah terisi

Ya

Rationale EtD sudah terisi

Ya

Traffic-light summary sudah dibuat

Ya

Draft rekomendasi sudah tersedia

Ya

CBA sudah lengkap jika rekomendasi bersyarat

Ya

Policy brief draft sudah dibuat

Ya

Audit/version information tersedia

Ya

Approver login dengan role Ketua KFT/Approver

Ya

Kalau ada syarat belum terpenuhi, sistem tidak boleh mengizinkan lock decision.

D. Siapa yang boleh melakukan Step 13?

Role

Hak akses

Ketua KFT / Approver

Bisa review, approve, finalisasi policy brief, dan lock decision

Sekretaris KFT

Bisa menyiapkan draft, tetapi tidak boleh lock final jika bukan approver

Analis HTA

Bisa membantu revisi evidence, CEA/BIA, rekomendasi, policy brief, tetapi tidak boleh lock final

KFT Member

Bisa melihat hasil dan memberi judgement, tetapi tidak boleh lock final

Admin IT

Tidak boleh approve keputusan klinis/EtD; hanya mengelola sistem

Dalam dokumen teknis, Admin IT tidak mengubah judgement klinis/EtD, HTA analyst tidak mengunci keputusan final, sedangkan Ketua KFT/Approver berwenang approve rekomendasi, lock decision, dan finalisasi policy brief.

E. Apa yang harus dibuat tim IT pada Step 13?

Tim IT perlu membuat halaman:

Approval & Lock Decision Page

Struktur halaman disarankan seperti ini:

Approval & Lock Decision PageCase ID: HF_ARNI_ACEI_001Session ID: KFT_2026_ARNI_001Case title: ARNI vs ACEI pada pasien HFrEFCurrent status: pending_approvalSections:1. Case summary2. Evidence summary3. CEA/BIA result summary4. EtD traffic-light summary5. Recommendation final/draft6. Criteria-Based Access, if required7. Policy brief preview8. Version and audit information9. Approval notesActions:- Request revision- Approve recommendation- Lock decision- Download final policy brief- View audit trail

F. Isi yang harus direview Ketua KFT

1. Review case summary

Ketua KFT harus melihat ringkasan kasus:

Field

Contoh

Case ID

HF_ARNI_ACEI_001

Intervensi

ARNI / sacubitril-valsartan

Comparator

ACEI

Indikasi

HFrEF

Populasi

Pasien HFrEF sesuai kriteria

Setting

KFT RS Unud

Outcome utama

Rehospitalisasi 12 bulan

Status

pending approval

2. Review evidence summary

Sistem menampilkan:

Komponen

Isi

PICO

population, intervention, comparator, outcome

Effect estimate

RR, risk difference, absolute benefit

Outcome klinis

rehospitalisasi, LOS, safety bila ada

Certainty evidence

high/moderate/low/very low

Keterbatasan bukti

misalnya data observasional, single/multi-center, confounding

Referensi

guideline, RCT, meta-analysis, local RWE

Tujuannya agar Ketua KFT tahu basis bukti klinis sebelum keputusan dikunci.

3. Review hasil CEA/BIA

Sistem menampilkan ringkasan ekonomi:

Komponen

Isi

Incremental drug cost

biaya tambahan obat ARNI vs ACEI

Cost offset

potensi penghematan rawat inap

Incremental total cost

biaya tambahan total per pasien/tahun

ICER

biaya per rehospitalisasi yang dihindari

Budget impact

skenario 10%, 30%, 50% uptake

Sensitivity

variasi harga dan volume

Status data biaya

final/proxy/draft

Jika data biaya belum final, sistem harus menampilkan warning, misalnya:

“Hasil ekonomi menggunakan data proxy atau input lokal sementara. Keputusan dapat dikunci sebagai keputusan simulasi/pilot, tetapi perlu update data RS Unud sebelum implementasi final.”

4. Review EtD traffic-light

Ketua KFT melihat ringkasan:

Domain

Traffic-light

Rationale

Benefits

Green

manfaat klinis mendukung

Harms

Yellow

perlu monitoring

Certainty

Yellow

bukti masih terbatas

Cost-effectiveness

Yellow

bergantung harga

Budget impact

Yellow/Red

perlu pembatasan

Feasibility

Yellow

perlu SOP

Acceptability

Yellow/Green

perlu kesepakatan

Equity

Yellow/Green

perlu kriteria akses

5. Review rekomendasi final

Sistem menampilkan rekomendasi yang akan disahkan.

Pilihan minimal:

Adopt

Adopt with criteria-based access

Defer pending additional evidence

Do not adopt

Reassess after price negotiation

Contoh rekomendasi final:

Adopt with criteria-based access.KFT merekomendasikan ARNI dipertimbangkan masuk formularium untuk pasien HFrEF yang memenuhi kriteria klinis, dengan pembatasan prescriber dan monitoring tekanan darah, kreatinin/eGFR, serta kalium.

Ketua KFT harus bisa:

menerima rekomendasi,

mengedit teks final,

meminta revisi,

menolak rekomendasi,

menyetujui dan lock.

6. Review Criteria-Based Access jika ada

Jika rekomendasi adalah Adopt with criteria-based access, sistem harus memastikan CBA sudah lengkap.

CBA yang direview:

Komponen

Contoh

Diagnosis

HFrEF terkonfirmasi

EF

EF ≤40% atau sesuai SOP lokal

NYHA

II–IV

Prior therapy

sudah mendapat terapi standar/GDMT

Renal function

eGFR sesuai batas SOP

Potassium

tidak hiperkalemia

Prescriber

dokter jantung/penyakit dalam

Monitoring

tekanan darah, kreatinin/eGFR, kalium

Stop rule

hipotensi, AKI, hiperkalemia, intoleransi

Review timeline

3–6 bulan awal, lalu 6–12 bulan

Jika CBA belum lengkap, sistem tidak boleh lock decision.

7. Review policy brief

Ketua KFT harus melihat preview policy brief sebelum lock.

Yang dicek:

Bagian policy brief

Harus ada?

Judul kasus

Ya

Decision question

Ya

Evidence summary

Ya

Economic summary

Ya

EtD table

Ya

Recommendation

Ya

CBA jika perlu

Ya

Monitoring plan

Ya

Audit/version information

Ya

Prepared by

Ya

Approved by

Ya

Approved date

Ya

Dalam dokumen teknis, policy brief final hanya dapat dikunci oleh approver dan tersimpan bersama input version serta audit trail.

G. Status keputusan yang perlu dibuat IT

Tim IT perlu membuat status workflow.

Status

Makna

draft

Case masih awal

in_review

Sedang ditinjau

ready_for_approval

Semua komponen siap untuk Ketua KFT

revision_requested

Ketua KFT meminta revisi

approved

Rekomendasi disetujui, tetapi belum dikunci

locked

Keputusan final terkunci

archived

Versi lama disimpan

superseded

Digantikan oleh versi baru

Alur status:

draft → in_review → ready_for_approval → approved → locked                         ↓                  revision_requested

H. Apa yang terjadi saat “approve”?

Ketika Ketua KFT menekan tombol Approve Recommendation, sistem harus menyimpan:

Field

Contoh

approved_by

user Ketua KFT

approved_at

timestamp

approval_status

approved

final_recommendation

adopt with criteria-based access

approval_notes

catatan Ketua KFT

approved_policy_brief_version

brief_v0.3

approved_cba_version

cba_v0.1

Approve berarti:

Ketua KFT setuju dengan isi rekomendasi dan policy brief, tetapi sistem masih dapat memberi satu tahap konfirmasi terakhir sebelum lock.

I. Apa yang terjadi saat “lock decision”?

Ketika Ketua KFT menekan tombol Lock Decision, sistem harus:

Mengunci rekomendasi final.

Mengunci policy brief final.

Mengunci EtD summary yang dipakai.

Mengunci CBA jika ada.

Mengunci evidence version yang dipakai.

Mengunci local input version yang dipakai.

Mengunci calculation run yang dipakai.

Membuat final decision record.

Menyimpan final policy brief Word/PDF.

Mencatat audit trail.

Mengubah status case menjadi locked.

Lock decision berarti:

Data keputusan final tidak bisa diedit langsung lagi.

Jika ada revisi setelah lock, sistem harus membuat versi baru, misalnya decision_v1.1, tanpa menimpa decision_v1.0_locked.

Dokumen teknis DeciBridge menyebut bahwa setelah locked, perubahan tidak mengubah keputusan lama; sistem harus membuat versi baru.

J. Data yang harus dikunci saat lock decision

Saat lock, sistem harus menyimpan snapshot final.

Komponen

Yang dikunci

Case

case_id, case_title, intervention, comparator, population

Evidence

evidence_version_id, effect estimate, certainty

Local input

local_input_version_id, harga, biaya, volume, uptake

Calculation

calculation_run_id, CEA/BIA results

EtD

session_id, domain rating, rationale

Recommendation

final recommendation dan final_text

CBA

eligibility, monitoring, stop rule

Policy brief

final DOCX/PDF version

Approval

approved_by, approved_at

Audit

locked_by, locked_at, lock_reason

K. Database/tabel yang dibutuhkan Step 13

Minimal tabel:

Tabel

Fungsi

approval_records

Menyimpan approval Ketua KFT

decision_records

Menyimpan keputusan final

recommendations

Menyimpan rekomendasi final

policy_briefs

Menyimpan policy brief final

decision_locks

Menyimpan informasi lock decision

version_history

Riwayat versi

audit_logs

Jejak aktivitas

access_criteria

CBA final jika ada

calculation_runs

CEA/BIA yang dipakai

Contoh tabel decision_records

Field

Contoh

decision_id

DEC_HF_ARNI_ACEI_001_v1.0

case_id

HF_ARNI_ACEI_001

session_id

KFT_2026_ARNI_001

final_recommendation

Adopt with criteria-based access

final_text

teks rekomendasi final

evidence_version_id

evidence_v0.1

local_input_version_id

local_input_v0.1

calculation_run_id

CALC_2026_001

etd_session_id

KFT_2026_ARNI_001

policy_brief_id

PB_001_v1.0

cba_id

CBA_001

approved_by

ketua_kft_01

approved_at

timestamp

locked_by

ketua_kft_01

locked_at

timestamp

status

locked

L. Validasi sebelum approve dan lock

1. Validasi sebelum approve

Validasi

Aturan

User role

harus Ketua KFT/Approver

Rekomendasi

tidak boleh kosong

EtD

semua domain wajib sudah terisi

Rationale

tidak boleh kosong

Policy brief

minimal draft tersedia

CBA

wajib lengkap jika rekomendasi bersyarat

Version ID

evidence, local input, calculation harus tercatat

Approval notes

disarankan/wajib sesuai SOP

2. Validasi sebelum lock

Validasi

Aturan

Approval status

harus approved

Final policy brief

harus ada

Final recommendation

harus ada

CBA jika perlu

harus complete

Audit info

harus lengkap

Data belum berubah setelah approve

sistem harus cek apakah ada update baru

Lock confirmation

user harus konfirmasi

Jika data berubah setelah policy brief dibuat, sistem harus memberi warning:

“Data local input atau calculation run berubah setelah policy brief dibuat. Silakan regenerate policy brief sebelum lock decision.”

M. Jika Ketua KFT meminta revisi

Sistem harus menyediakan tombol:

Request Revision

Jika tombol ini dipilih, Ketua KFT harus menulis alasan revisi.

Contoh alasan:

Revisi diminta

Tujuan

Tambahkan CBA lebih spesifik

agar restriksi pasien jelas

Perbarui harga obat

agar BIA lebih akurat

Revisi final_text

agar narasi rekomendasi lebih tepat

Tambahkan monitoring

agar implementasi lebih aman

Tunda approval

menunggu data biaya RS Unud

Status berubah menjadi:

revision_requested

Data kembali ke step terkait:

Jenis revisi

Kembali ke step

Evidence kurang

Step 6

Data biaya kurang

Step 7

CEA/BIA perlu ulang

Step 8

EtD perlu revisi

Step 9

Recommendation perlu ubah

Step 10

CBA perlu ubah

Step 11

Policy brief perlu regenerate

Step 12

N. Jika data berubah setelah lock

Setelah lock, data lama tidak boleh diubah.

Jika ada:

harga obat berubah,

guideline baru,

evidence baru,

volume pasien berubah,

safety issue baru,

revisi CBA,

maka sistem harus membuat:

new decision version

Contoh:

Versi

Status

decision_v1.0_locked

keputusan lama, tetap tersimpan

decision_v1.1_draft

versi revisi karena harga berubah

decision_v2.0_locked

keputusan baru setelah rapat ulang

Sistem harus menampilkan hubungan:

decision_v2.0 supersedes decision_v1.0

O. Audit trail Step 13

Audit trail wajib sangat detail.

Aktivitas

Data yang dicatat

Ketua KFT membuka halaman approval

user_id, case_id, timestamp

Review policy brief

user_id, policy_brief_id, timestamp

Request revision

alasan revisi, user, timestamp

Approve recommendation

approver, timestamp, final recommendation

Edit final_text

teks lama, teks baru, user

Lock decision

locked_by, locked_at, decision_id

Download final brief

user, timestamp

Attempt edit after lock

user, timestamp, blocked action

Create new version

old decision_id, new decision_id, reason

Dalam dokumen teknis, audit trail harus mencatat approve/lock decision berupa approver, timestamp, dan rekomendasi final.

P. UI tombol dan hak akses

Tombol

Role yang boleh

Fungsi

Review

Ketua KFT/Approver

melihat semua ringkasan

Request Revision

Ketua KFT/Approver

mengembalikan ke tim

Approve Recommendation

Ketua KFT/Approver

menyetujui rekomendasi

Lock Decision

Ketua KFT/Approver

mengunci keputusan final

Download Final Brief

sesuai hak akses

mengunduh dokumen final

Create New Version

Approver/Admin/HTA sesuai SOP

membuat versi baru setelah lock

View Audit Trail

sesuai hak akses

melihat riwayat

Tombol Lock Decision sebaiknya memiliki konfirmasi ganda:

Are you sure you want to lock this decision?After locking, this decision cannot be edited directly.Any future changes must be made as a new version.[Cancel] [Yes, Lock Decision]

Q. Flowchart Step 13

R. Endpoint/API yang dibutuhkan

Tim IT dapat membuat endpoint seperti ini:

Endpoint

Method

Fungsi

/cases/{case_id}/approval

GET

menampilkan halaman approval

/cases/{case_id}/approve

POST

menyetujui rekomendasi

/cases/{case_id}/request-revision

POST

meminta revisi

/cases/{case_id}/lock

POST

lock decision

/cases/{case_id}/decision-record

GET

melihat decision record

/cases/{case_id}/audit-trail

GET

melihat audit trail

/cases/{case_id}/new-version

POST

membuat versi baru setelah lock

Dokumen teknis DeciBridge juga mencantumkan endpoint /cases/{case_id}/lock untuk approve dan lock decision.

S. Pseudocode untuk tim IT

1. Approver opens approval page for case_id.2. System checks role:      if role != Ketua KFT / Approver:          deny access.3. System loads:      case metadata,      evidence summary,      CEA/BIA results,      EtD appraisal,      traffic-light summary,      recommendation draft/final,      CBA if required,      policy brief draft,      version and audit info.4. System validates completeness.5. If missing critical components:      show missing checklist;      disable Lock Decision button.6. Approver reviews all sections.7. If revision needed:      approver clicks Request Revision;      system records revision note;      status = revision_requested.8. If approved:      approver clicks Approve Recommendation;      system saves approval record.9. System asks lock confirmation.10. If confirmed:      create decision_id;      save final decision record;      lock recommendation, CBA, EtD summary, policy brief, input versions, and calculation run;      status = locked.11. Write audit log:      approved_by,      approved_at,      locked_by,      locked_at,      final recommendation,      versions used.12. If future change needed:      system creates new version; old locked decision remains unchanged.

T. Acceptance criteria Step 13 untuk tim IT

Step 13 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Membatasi approval hanya untuk role Ketua KFT/Approver

Ya

Menampilkan semua ringkasan keputusan sebelum approval

Ya

Mengecek kelengkapan evidence, CEA/BIA, EtD, recommendation, CBA, policy brief

Ya

Menampilkan checklist komponen yang belum lengkap

Ya

Menyediakan tombol Request Revision

Ya

Menyimpan alasan revisi

Ya

Menyediakan tombol Approve Recommendation

Ya

Menyimpan approved_by dan approved_at

Ya

Menyediakan konfirmasi sebelum Lock Decision

Ya

Membuat final decision_id

Ya

Mengunci decision record

Ya

Mengunci policy brief final

Ya

Mengunci versi evidence, local input, calculation run, EtD, dan CBA

Ya

Mencegah edit langsung setelah locked

Ya

Membuat versi baru jika ada perubahan setelah lock

Ya

Mencatat audit trail lengkap

Ya

Menyediakan final policy brief untuk download

Ya

U. Pesan untuk tim IT

Pada Step 13, sistem harus menyediakan halaman Approval & Lock Decision yang hanya dapat diakses oleh role Ketua KFT/Approver. Pada halaman ini, Ketua KFT harus dapat meninjau case summary, evidence summary, hasil CEA/BIA, EtD traffic-light, rationale, rekomendasi, CBA jika ada, policy brief preview, dan audit/version information.

Sistem harus melakukan completeness check sebelum approval dan lock. Komponen wajib meliputi case metadata, evidence summary, active local input version, calculation run, EtD judgement dan rationale, recommendation, CBA jika rekomendasi bersyarat, policy brief draft, serta evidence/local input/calculation/session version ID. Jika ada komponen wajib yang belum lengkap, tombol Lock Decision harus disabled dan sistem menampilkan daftar item yang perlu diperbaiki.

Ketua KFT harus dapat memilih Request Revision, Approve Recommendation, atau Lock Decision. Jika Request Revision, sistem menyimpan catatan revisi dan mengembalikan status ke tahap terkait. Jika Approve Recommendation, sistem menyimpan approved_by, approved_at, final_recommendation, dan approval_notes. Jika Lock Decision, sistem membuat final decision_id, mengunci rekomendasi, policy brief, EtD summary, CBA, evidence version, local input version, dan calculation run yang digunakan. Setelah locked, data tidak boleh diedit langsung. Jika ada perubahan setelah lock, sistem harus membuat versi baru tanpa menimpa keputusan lama. Semua aktivitas approval dan lock harus masuk audit trail.

Kesimpulan sederhana

Step 13 adalah tahap pengesahan keputusan final.

Untuk tim IT, yang harus dibuat adalah:

halaman review final untuk Ketua KFT;

validasi kelengkapan sebelum approve/lock;

tombol request revision;

tombol approve recommendation;

tombol lock decision dengan konfirmasi;

decision record final;

penguncian policy brief, recommendation, CBA, EtD, calculation, dan version;

audit trail lengkap;

mekanisme new version jika ada perubahan setelah lock.

Dengan Step 13, DeciBridge tidak hanya menghasilkan rekomendasi, tetapi menghasilkan keputusan KFT yang resmi, terkunci, terdokumentasi, dan dapat diaudit.

Step 14 — Sistem menyimpan decision record, audit trail, dan versi final dokumen, maksudnya: Setelah Ketua KFT melakukan approve dan lock decision, sistem harus membuat final decision record yang bersifat read-only/immutable, menyimpan seluruh versi input yang digunakan, menyimpan policy brief final, mencatat audit trail lengkap, dan memastikan keputusan lama tidak bisa ditimpa. Jika nanti ada perubahan harga atau bukti baru, sistem harus membuat versi baru tanpa mengubah decision record yang sudah locked.

Step 14 adalah tahap backend/system finalization, yaitu setelah Ketua KFT menekan Lock Decision pada Step 13, maka sistem harus otomatis menyimpan seluruh bukti keputusan dalam bentuk:

decision record, yaitu catatan keputusan final;

audit trail, yaitu jejak semua aktivitas penting;

versi final dokumen, yaitu policy brief final Word/PDF dan snapshot data yang dipakai

Dalam dokumen teknis DeciBridge, output utama sistem adalah policy brief, decision record terkunci, dan audit trail yang dapat ditelusuri. Sistem juga harus menjaga versioning, karena perubahan harga/biaya atau bukti tidak boleh menimpa keputusan lama.

Komponen

Isi

Tujuan

Menjamin keputusan bisa ditelusuri kembali dan diaudit

Aktor

Sistem

Input

Semua data final: evidence version, local input version, EtD score, recommendation, policy brief

Proses sistem

Simpan final document, audit log, decision record

Output

Dokumen final Word/PDF, decision record, audit trail

Database

decision_records, audit_logs, version_history, policy_briefs

Audit trail

Semua aktivitas penting tersimpan

Catatan IT

Harus ada tombol “View audit trail” di dashboard kasus

Aktivitas yang wajib tercatat:

Aktivitas

Data yang dicatat

Login

user_id, waktu, IP/perangkat bila diperlukan

Edit case

field lama, field baru, user, timestamp

Upload Excel

nama file, hash file, upload_id, version_id, user

Ubah harga/biaya

nilai lama, nilai baru, sumber, tanggal berlaku

Ubah judgement EtD

domain, nilai lama, nilai baru, rationale

Generate policy brief

template version, input version, output file

Approve/lock decision

approver, timestamp, rekomendasi final

Penjelasan:

A. Perbedaan Step 13 dan Step 14

Step

Aktor utama

Makna

Step 13

Ketua KFT/Approver

Ketua KFT melakukan review, approve, dan menekan lock decision

Step 14

Sistem/backend

Sistem menyimpan keputusan final, audit trail, dan dokumen final secara permanen

Jadi Step 13 adalah aksi manusia, sedangkan Step 14 adalah proses otomatis sistem setelah keputusan dikunci.

B. Tujuan Step 14

Step 14 bertujuan agar keputusan KFT bisa dijawab kembali kapan pun:

“Keputusan ini dibuat berdasarkan data apa, oleh siapa, kapan, menggunakan harga versi mana, evidence versi mana, hasil CEA/BIA mana, EtD session mana, rekomendasi apa, dan policy brief versi mana?”

Dengan Step 14, sistem tidak hanya menyimpan file Word/PDF, tetapi menyimpan paket bukti keputusan yang lengkap.

C. Apa yang harus disimpan pada Step 14?

1. Decision record

Decision record adalah catatan final keputusan KFT.

Untuk kasus ARNI vs ACEI, decision record harus menyimpan:

Field

Contoh

decision_id

DEC_HF_ARNI_ACEI_001_v1.0

case_id

HF_ARNI_ACEI_001

session_id

KFT_2026_ARNI_001

case_title

ARNI vs ACEI pada pasien HFrEF

final_recommendation

Adopt with criteria-based access

final_text

Teks rekomendasi final KFT

cba_required

true

cba_id

CBA_HF_ARNI_ACEI_001_v1.0

policy_brief_id

PB_HF_ARNI_ACEI_001_v1.0

approved_by

Ketua KFT

approved_at

tanggal/jam approval

locked_by

Ketua KFT

locked_at

tanggal/jam lock

decision_status

locked

decision_version

v1.0

notes

catatan final, bila ada

Decision record ini harus menjadi read-only setelah locked.

2. Snapshot versi data yang digunakan

Ini sangat penting. Sistem harus menyimpan bukan hanya hasil akhir, tetapi juga versi data yang dipakai.

Komponen

Yang harus disimpan

Evidence layer

evidence_version_id

Case pack

case_pack_version_id

Local input layer

local_input_version_id

Harga obat

versi harga ARNI dan ACEI

Biaya event

versi biaya rawat inap HF

BIA input

versi eligible population dan uptake

CEA/BIA result

calculation_run_id

EtD appraisal

etd_session_id

Traffic-light summary

traffic_light_summary_id

Recommendation

recommendation_id

CBA

cba_version_id

Policy brief

policy_brief_version_id

Kenapa perlu snapshot? Karena harga obat bisa berubah bulan depan. Jika keputusan lama tidak menyimpan versi harga yang dipakai, maka audit akan kacau.

Contoh:

Komponen

Versi yang dikunci

Evidence

evidence_v0.1

Local input

local_input_v0.3

Calculation

CALC_2026_001

EtD session

KFT_2026_ARNI_001

Policy brief

brief_v1.0_locked

3. Audit trail

Audit trail adalah catatan aktivitas yang terjadi dari awal sampai keputusan final.

Minimal aktivitas yang harus tercatat:

Aktivitas

Data yang dicatat

Login

user_id, waktu, IP/perangkat jika diperlukan

Upload Excel

nama file, hash file, upload_id, version_id, user

Validasi workbook

status validasi, error/warning

Edit case

field lama, field baru, user, timestamp

Update harga/biaya

nilai lama, nilai baru, sumber, tanggal berlaku

Run CEA/BIA

calculation_run_id, input version, hasil

Isi EtD

domain, judgement, rationale, user

Generate traffic-light

domain, warna, rule mapping

Generate recommendation

rule yang terpicu, rekomendasi draft

Isi CBA

criteria lama/baru, user

Generate policy brief

template version, input version, output file

Approve/lock decision

approver, timestamp, rekomendasi final

Dokumen teknis secara eksplisit menyebut aktivitas audit trail seperti login, edit case, upload Excel, perubahan harga/biaya, perubahan judgement EtD, generate policy brief, dan approve/lock decision.

4. Versi final dokumen

Setelah locked, sistem harus menyimpan dokumen final.

Dokumen yang disimpan:

Dokumen

Format

Status

Policy brief final

DOCX

locked

Policy brief final

PDF

locked, bila PDF generator tersedia

Decision summary

bisa HTML/PDF

locked

Audit trail export

CSV/PDF, opsional

locked/exportable

Case pack snapshot

Excel/PDF, opsional

archived

Dalam template policy brief, bagian audit/versioning memang memuat case pack version, local inputs version, dan catatan deviasi; sistem mengambil data dari case metadata, clinical outcomes, cost inputs, EtD session, dan recommendation untuk dirender ke DOCX.

D. Alur teknis Step 14

E. Status setelah Step 14

Setelah Step 14 selesai, status case harus berubah menjadi:

locked

Contoh status:

Komponen

Status setelah Step 14

Case

locked

Decision record

locked

Recommendation

final_locked

EtD session

locked

CBA

locked, bila ada

Policy brief

locked_final

Local input version

locked_with_decision

CEA/BIA calculation

locked_with_decision

Evidence version

locked_with_decision

Artinya, user tidak bisa lagi mengedit langsung keputusan lama.

F. Apa yang boleh dan tidak boleh setelah locked?

Boleh

Aksi

Boleh?

Melihat decision record

Ya

Mengunduh policy brief final

Ya

Melihat audit trail

Ya

Membuat versi baru

Ya

Membandingkan versi lama dan baru

Ya

Export audit trail

Ya

Tidak boleh

Aksi

Boleh?

Edit rekomendasi final langsung

Tidak

Edit policy brief final langsung

Tidak

Mengganti harga pada versi locked

Tidak

Mengubah EtD judgement yang sudah locked

Tidak

Menghapus decision record

Tidak

Menimpa file policy brief final

Tidak

Jika user mencoba mengedit, sistem harus menampilkan pesan:

“Decision has been locked. To make changes, please create a new version.”

G. Database/tabel yang dibutuhkan

Minimal tabel untuk Step 14:

Tabel

Fungsi

decision_records

Menyimpan keputusan final

decision_record_versions

Menyimpan riwayat versi keputusan

decision_locks

Menyimpan data lock decision

policy_briefs

Menyimpan metadata policy brief

policy_brief_files

Menyimpan path file DOCX/PDF

audit_logs

Menyimpan semua aktivitas

version_history

Menyimpan versi evidence, local input, calculation, EtD, CBA

case_snapshots

Menyimpan snapshot data final, opsional

file_artifacts

Menyimpan file Excel, policy brief, export audit

approval_records

Menyimpan approval Ketua KFT

Contoh tabel decision_records

Field

Tipe

Contoh

decision_id

text/UUID

DEC_HF_ARNI_ACEI_001_v1.0

case_id

text

HF_ARNI_ACEI_001

session_id

text

KFT_2026_ARNI_001

decision_version

text

v1.0

final_recommendation

enum/text

Adopt with criteria-based access

final_text

text

teks rekomendasi final

recommendation_id

text

REC_001

cba_id

text

CBA_001

policy_brief_id

text

PB_001

evidence_version_id

text

evidence_v0.1

local_input_version_id

text

local_input_v0.3

calculation_run_id

text

CALC_001

etd_session_id

text

KFT_2026_ARNI_001

approved_by

user_id

ketua_kft_01

approved_at

datetime

timestamp

locked_by

user_id

ketua_kft_01

locked_at

datetime

timestamp

status

enum

locked

Contoh tabel audit_logs

Field

Tipe

Contoh

audit_id

UUID

AUD_001

case_id

text

HF_ARNI_ACEI_001

session_id

text

KFT_2026_ARNI_001

user_id

text

ketua_kft_01

user_role

text

approver

action_type

text

LOCK_DECISION

entity_type

text

decision_record

entity_id

text

DEC_HF_ARNI_ACEI_001_v1.0

old_value

JSON/text

status sebelum

new_value

JSON/text

status locked

timestamp

datetime

waktu aksi

ip_address

text

opsional

notes

text

catatan

Contoh tabel policy_brief_files

Field

Contoh

file_id

FILE_PB_001

policy_brief_id

PB_HF_ARNI_ACEI_001_v1.0

case_id

HF_ARNI_ACEI_001

file_type

DOCX / PDF

file_path

/storage/policy_briefs/PB_001_v1.0.pdf

file_hash

hash dokumen

generated_at

timestamp

generated_by

user/system

status

locked_final

H. File hash wajib disimpan

Untuk dokumen final, sistem sebaiknya menyimpan file hash.

Fungsinya:

memastikan file final tidak berubah setelah locked.

Contoh:

Dokumen

Hash

Policy brief PDF

sha256:abc123...

Policy brief DOCX

sha256:def456...

Jika suatu saat file berubah, hash akan berbeda, sehingga sistem bisa mendeteksi ketidaksesuaian.

I. Snapshot final: mengapa penting?

Selain menyimpan link ke tabel, sistem sebaiknya menyimpan snapshot final dalam bentuk JSON atau tabel snapshot.

Contoh snapshot:

{  "case_id": "HF_ARNI_ACEI_001",  "decision_version": "v1.0",  "final_recommendation": "Adopt with criteria-based access",  "evidence_version_id": "evidence_v0.1",  "local_input_version_id": "local_input_v0.3",  "calculation_run_id": "CALC_001",  "etd_session_id": "KFT_2026_ARNI_001",  "policy_brief_id": "PB_001_v1.0",  "locked_by": "ketua_kft_01",  "locked_at": "2026-05-20 14:35"}

Tujuannya agar keputusan tetap bisa direkonstruksi meskipun data aktif di dashboard nanti berubah.

J. Validasi sebelum sistem menyimpan final

Sebelum membuat decision record final, sistem harus mengecek:

Validasi

Aturan

Case status

harus approved atau siap locked

User role

harus Ketua KFT/Approver

Policy brief

harus ada versi final/draft siap final

EtD session

harus lengkap

Recommendation

final recommendation tidak boleh kosong

CBA

wajib lengkap jika rekomendasi bersyarat

Version ID

evidence, local input, calculation harus ada

Audit info

approved_by dan approved_at harus ada

File export

DOCX atau PDF harus berhasil dibuat

Tidak ada perubahan baru

sistem harus cek apakah input berubah setelah policy brief dibuat

Jika ada yang kurang, sistem tidak boleh menyimpan final.

Contoh pesan:

“Decision record tidak dapat dikunci karena CBA belum lengkap.”

atau:

“Policy brief dibuat sebelum update harga terakhir. Silakan regenerate policy brief sebelum lock.”

K. Apa yang dilakukan sistem setelah decision record disimpan?

Setelah decision record berhasil dibuat, sistem melakukan beberapa hal otomatis:

Update status cases.status = locked.

Update recommendations.status = final_locked.

Update policy_briefs.status = locked_final.

Update etd_sessions.status = locked.

Update access_criteria.status = locked, jika ada.

Update local_input_versions.status = locked_with_decision.

Update calculation_runs.status = locked_with_decision.

Simpan final policy brief DOCX/PDF.

Simpan audit trail lock decision.

Tampilkan halaman final decision summary.

L. Tampilan halaman setelah Step 14

IT perlu membuat halaman:

Final Decision Record Page

Isi halaman:

FINAL DECISION RECORDDecision ID: DEC_HF_ARNI_ACEI_001_v1.0Case ID: HF_ARNI_ACEI_001Session ID: KFT_2026_ARNI_001Status: LOCKEDFinal recommendation:Adopt with criteria-based accessApproved by:Ketua KFT, tanggal/jamLocked by:Ketua KFT, tanggal/jamVersions used:- Evidence version: evidence_v0.1- Local input version: local_input_v0.3- Calculation run: CALC_001- EtD session: KFT_2026_ARNI_001- Policy brief: PB_001_v1.0Available actions:[Download Policy Brief DOCX][Download Policy Brief PDF][View Audit Trail][Create New Version][View Snapshot]

M. Jika ada perubahan setelah Step 14

Jika setelah keputusan locked ada:

harga ARNI berubah,

biaya rawat inap berubah,

jumlah pasien eligible berubah,

guideline baru,

evidence baru,

safety signal,

CBA perlu revisi,

maka sistem tidak boleh mengubah decision record lama.

Sistem harus membuat:

new version

Contoh:

Kejadian

Tindakan sistem

Harga ARNI turun

buat local_input_v0.4, lalu calculation run baru

Guideline baru

buat evidence_v0.2

KFT ingin review ulang

buat decision_v1.1_draft

Keputusan baru disahkan

buat decision_v2.0_locked

Keputusan lama

tetap decision_v1.0_locked

Dalam checklist MVP, lock decision dinyatakan berhasil bila setelah locked, perubahan tidak mengubah keputusan lama dan sistem membuat versi baru.

N. Backup dan keamanan data

Karena Step 14 menyimpan keputusan final, sistem perlu mendukung:

Komponen

Kebutuhan

Database backup

harian

File backup

minimal mingguan atau setiap ada final brief

Access control

hanya role tertentu bisa melihat/mengunduh

Immutable record

decision locked tidak bisa diedit

File hash

memastikan file final tidak berubah

Restore procedure

prosedur pemulihan bila terjadi error

Export audit

audit trail bisa diekspor bila diminta

Dokumen teknis menyarankan database PostgreSQL karena kuat untuk versioning, audit trail, dan query relasional; file storage digunakan untuk menyimpan case pack, policy brief, dan export Word/PDF.

O. Endpoint/API yang dibutuhkan

Endpoint

Method

Fungsi

/cases/{case_id}/decision-record

POST

membuat decision record final

/cases/{case_id}/decision-record

GET

melihat decision record

/cases/{case_id}/audit-trail

GET

melihat audit trail

/cases/{case_id}/final-documents

GET

melihat dokumen final

/policy-briefs/{brief_id}/download

GET

unduh DOCX/PDF

/cases/{case_id}/new-version

POST

membuat versi baru setelah locked

/cases/{case_id}/snapshot

GET

melihat snapshot final

/cases/{case_id}/audit-export

GET

export audit trail

P. Pseudocode untuk tim IT

1. Receive lock confirmation from Step 13.2. Verify user role = Ketua KFT / Approver.3. Verify case status = approved or ready_to_lock.4. Validate required components:      - final recommendation      - EtD session      - CEA/BIA calculation run      - local input version      - evidence version      - CBA if required      - policy brief final/draft ready for final.5. Generate decision_id.6. Create immutable decision record.7. Save snapshot of all linked versions.8. Mark linked records as locked_with_decision:      - recommendation      - policy brief      - EtD session      - CBA      - calculation run      - local input version      - evidence version.9. Generate/store final DOCX/PDF if not already final.10. Save file path and file hash.11. Write audit log:      - who locked      - when locked      - final recommendation      - versions used      - policy brief file ID.12. Update case status = locked.13. Disable edit actions for locked data.14. Enable view/download/audit/new-version actions only.

Q. Acceptance criteria Step 14 untuk tim IT

Step 14 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Membuat decision_id final

Ya

Menyimpan final decision record

Ya

Menghubungkan decision record dengan case_id dan session_id

Ya

Menyimpan evidence version yang dipakai

Ya

Menyimpan local input version yang dipakai

Ya

Menyimpan calculation run yang dipakai

Ya

Menyimpan EtD session yang dipakai

Ya

Menyimpan recommendation final

Ya

Menyimpan CBA final jika ada

Ya

Menyimpan policy brief final DOCX/PDF

Ya

Menyimpan file path dan file hash

Ya

Mencatat audit trail lengkap

Ya

Mengubah status case menjadi locked

Ya

Mencegah edit langsung setelah locked

Ya

Menyediakan fitur download dokumen final

Ya

Menyediakan fitur view audit trail

Ya

Menyediakan fitur create new version

Ya

Tidak menimpa keputusan lama saat ada update

Ya

R. Pesan untuk tim IT

Pada Step 14, setelah Ketua KFT melakukan approve dan lock decision, sistem harus otomatis menyimpan final decision record, audit trail, dan versi final dokumen. Sistem harus membuat decision_id final, menyimpan case_id, session_id, final recommendation, final_text, approved_by, approved_at, locked_by, locked_at, serta seluruh versi data yang digunakan: evidence_version_id, local_input_version_id, calculation_run_id, etd_session_id, cba_id bila ada, dan policy_brief_id.

Decision record harus bersifat read-only/immutable setelah locked. Sistem juga harus menyimpan policy brief final dalam DOCX dan/atau PDF, menyimpan file path dan file hash, serta mencatat seluruh aktivitas ke audit log. Audit trail minimal mencakup upload Excel, validasi, perubahan harga/biaya, run CEA/BIA, pengisian EtD, generate recommendation, pengisian CBA, generate policy brief, approval, dan lock decision.

Setelah Step 14 selesai, status case menjadi locked, policy brief menjadi locked_final, recommendation menjadi final_locked, dan semua versi input yang dipakai diberi status locked_with_decision. Data yang sudah locked tidak boleh diedit langsung. Jika ada perubahan harga, bukti, CBA, atau rekomendasi setelah lock, sistem harus membuat versi baru tanpa menimpa decision record lama.

Kesimpulan sederhana

Step 14 adalah tahap penyimpanan final dan audit.

Untuk tim IT, inti pekerjaannya adalah:

membuat final decision record;

menyimpan semua versi data yang dipakai;

menyimpan policy brief final;

mencatat audit trail lengkap;

mengunci data agar tidak bisa diedit;

menyediakan download dokumen final;

menyediakan view audit trail;

menyediakan create new version bila ada perubahan.

Dengan Step 14, DeciBridge menjadi sistem yang bukan hanya menghasilkan rekomendasi, tetapi menghasilkan arsip keputusan KFT yang resmi, terkunci, transparan, dan dapat diaudit kembali.

Step 15 — Jika ada perubahan harga atau bukti baru, sistem membuat versi baru tanpa menimpa keputusan lama, maksudnya: Jika setelah keputusan locked terdapat perubahan pada harga obat, biaya layanan, volume pasien, evidence klinis, guideline, hasil CEA/BIA, EtD judgement, CBA, atau rekomendasi, maka sistem harus membuat versi baru dari case/decision. Decision record lama tetap read-only dan tersimpan sebagai arsip. Versi baru diproses ulang melalui workflow DeciBridge mulai dari bagian yang berubah.

Step 15 adalah mekanisme versioning/revision control setelah keputusan KFT sudah dikunci. Intinya: jika setelah keputusan final ada harga obat berubah, biaya RS berubah, jumlah pasien eligible berubah, evidence/guideline baru, atau CBA perlu direvisi, maka sistem tidak boleh mengubah keputusan lama. Sistem harus membuat versi baru.

Prinsip ini sesuai dengan dokumen teknis DeciBridge: setelah decision locked, perubahan tidak boleh mengubah keputusan lama; sistem harus membuat versi baru. Dokumen juga menekankan bahwa perubahan harga obat, biaya layanan, volume pasien, atau pola terapi tidak boleh mengubah evidence layer, tetapi harus menghasilkan versi input baru dan memperbarui output CEA/BIA secara transparan.

Komponen

Isi

Tujuan

Menjaga keputusan lama tetap aman, tetapi memungkinkan update

Aktor

Farmasi RS, HTA analyst, Ketua KFT

Pemicu

Harga obat berubah, biaya RS berubah, guideline baru, evidence baru, volume pasien berubah

Proses sistem

Buat versi baru dari case lama

Output

Case baru versi lanjutan, misalnya dari v1.0 locked menjadi v1.1 draft

Database

version_history, cases, cost_inputs, effect_estimates, audit_logs

Catatan IT

Keputusan lama tetap locked dan tidak ditimpa

Contoh:

Kondisi

Sistem harus melakukan

Harga ARNI berubah

Buat local_input_v1.1, jalankan ulang CEA/BIA

Guideline baru keluar

Buat evidence_v1.1, minta HTA analyst review ulang

Safety issue baru

Buat versi baru dan tandai perlu rapat ulang

Budget impact naik signifikan

Trigger “review required”

A. Tujuan Step 15

Tujuan Step 15 adalah menjaga agar keputusan KFT tetap:

aman secara audit, karena keputusan lama tidak hilang;

reproducible, karena dapat diketahui keputusan dibuat berdasarkan data versi mana;

fleksibel, karena sistem tetap bisa diperbarui jika ada data baru;

transparan, karena terlihat apa yang berubah dan mengapa;

tidak membingungkan, karena data lama dan data baru tidak tercampur.

Contoh sederhana:

Pada Mei 2026, KFT memutuskan:

ARNI masuk formularium dengan criteria-based access berdasarkan harga ARNI Rp850.000/bulan.

Pada Agustus 2026, harga ARNI turun menjadi Rp650.000/bulan.

Sistem tidak boleh mengganti harga lama pada keputusan Mei 2026. Sistem harus membuat:

versi baru local input, menjalankan ulang CEA/BIA, lalu bila perlu membuat decision version baru.

B. Apa yang dapat memicu Step 15?

Step 15 bisa dipicu oleh perubahan data berikut:

Jenis perubahan

Contoh

Dampak workflow

Harga obat berubah

Harga ARNI turun/naik

Update local input layer, run ulang CEA/BIA

Biaya rawat inap berubah

Unit cost HF admission berubah

Update local input, run ulang CEA/BIA

Volume pasien berubah

Pasien HFrEF eligible meningkat

Update BIA input, run ulang BIA

Uptake berubah

KFT ingin skenario 20/40/60%

Update BIA scenario

Evidence baru

RCT/meta-analysis/guideline baru

Update evidence layer, review ulang case pack

Safety signal baru

Ada laporan hiperkalemia/AKI

Update harms domain dan EtD

CBA berubah

EF threshold atau monitoring berubah

Update access criteria

Rekomendasi perlu revisi

Dari restrict menjadi adopt/defer

Buat decision version baru

Policy brief perlu update

Narasi atau data berubah

Generate policy brief versi baru

C. Prinsip utama: tidak boleh overwrite

Untuk IT, prinsip paling penting:

Never overwrite locked decision. Create a new version.

Artinya:

Data lama

Perlakuan

Decision record lama

tetap locked/read-only

Policy brief lama

tetap tersimpan

Harga lama

tetap tersimpan sebagai versi lama

CEA/BIA lama

tetap tersimpan

EtD lama

tetap tersimpan

CBA lama

tetap tersimpan

Audit trail lama

tetap tersimpan

Data baru masuk sebagai:

Data baru

Contoh version

Local input baru

local_input_v1.1

Evidence baru

evidence_v1.1

Calculation baru

CALC_v1.1

EtD session baru

KFT_2026_ARNI_REVIEW_002

Policy brief baru

brief_v1.1

Decision baru

decision_v1.1_draft atau decision_v2.0_locked

D. Contoh versioning yang benar

Misalnya keputusan awal sudah locked:

Komponen

Versi awal

Case

HF_ARNI_ACEI_001

Decision

decision_v1.0_locked

Evidence

evidence_v1.0

Local input

local_input_v1.0

Calculation

CALC_v1.0

Policy brief

brief_v1.0_locked

Kemudian harga ARNI berubah.

Sistem membuat:

Komponen

Versi baru

Local input baru

local_input_v1.1

Calculation baru

CALC_v1.1

Policy brief draft baru

brief_v1.1_draft

Decision baru

decision_v1.1_draft

Jika KFT kemudian rapat ulang dan mengesahkan:

Komponen

Versi final baru

Decision baru

decision_v2.0_locked

Policy brief baru

brief_v2.0_locked

Decision lama

tetap decision_v1.0_locked

E. Alur teknis Step 15

F. Jenis versi baru yang harus didukung sistem

1. New local input version

Dipakai jika yang berubah hanya data lokal RS.

Contoh perubahan:

harga ARNI berubah,

harga ACEI berubah,

biaya rawat inap berubah,

eligible population berubah,

uptake berubah.

Sistem harus melakukan:

buat local_input_version_id baru;

simpan nilai lama dan baru;

jalankan ulang CEA/BIA;

tandai hasil lama sebagai archived, bukan dihapus;

tampilkan perbandingan hasil lama vs baru.

Contoh:

Parameter

Versi lama

Versi baru

Harga ARNI/bulan

Rp850.000

Rp650.000

Incremental total cost

Rp8.125.000

Rp5.725.000

ICER

Rp31.500.000

Rp22.200.000

Budget impact 30%

Rp292.500.000

Rp206.100.000

2. New evidence version

Dipakai jika ada bukti klinis baru.

Contoh:

guideline gagal jantung baru,

meta-analysis baru,

data lokal RS Unud sudah tersedia,

safety signal baru,

effect estimate berubah.

Sistem harus melakukan:

buat evidence_version_id baru;

update case pack/evidence summary;

minta Analis HTA review ulang;

jika effect estimate berubah, CEA/BIA harus dihitung ulang;

EtD domain benefits, harms, dan certainty mungkin perlu diisi ulang.

3. New EtD session version

Dipakai jika KFT perlu rapat ulang.

Contoh:

hasil BIA berubah signifikan,

ada evidence baru,

CBA perlu direvisi,

rekomendasi final perlu ditinjau ulang.

Sistem harus membuat:

Komponen

Contoh

session_id baru

KFT_2026_ARNI_REVIEW_002

etd_session_version

etd_v1.1

status

in_review

linked_previous_session

KFT_2026_ARNI_001

4. New policy brief version

Dipakai jika dokumen perlu di-generate ulang.

Contoh:

Versi

Status

brief_v1.0_locked

policy brief final lama

brief_v1.1_draft

draft update karena harga baru

brief_v2.0_locked

final baru setelah review KFT

5. New decision version

Dipakai jika rekomendasi resmi berubah atau perlu disahkan ulang.

Contoh:

Decision version

Rekomendasi

Status

decision_v1.0_locked

Adopt with criteria-based access

keputusan lama

decision_v1.1_draft

Draft setelah harga baru

belum final

decision_v2.0_locked

Adopt with revised CBA

keputusan baru

G. Kapan perlu approval ulang?

Tidak semua perubahan memerlukan approval ulang. Tim IT perlu menyediakan logic atau minimal status.

Perubahan

Perlu approval ulang?

Koreksi typo di draft sebelum locked

Tidak, jika belum final

Update harga setelah locked

Ya, jika memengaruhi CEA/BIA dan policy brief

Evidence baru yang mengubah benefit/harms

Ya

Perubahan CBA

Ya

Perubahan rekomendasi final

Ya

Generate ulang policy brief karena format

Tidak selalu, jika isi keputusan tidak berubah

Update eligible population untuk monitoring internal

Tergantung SOP, tetapi sebaiknya review

Untuk MVP, saran paling aman:

Jika case sudah locked dan ada perubahan pada harga, evidence, CEA/BIA, EtD, recommendation, atau CBA, sistem harus membuat versi baru dan menandai requires review.

H. Status versi baru

Tim IT perlu membuat status versioning.

Status

Makna

locked

keputusan lama final, tidak bisa diedit

archived

versi lama tersimpan

superseded

versi lama digantikan oleh versi baru

draft_revision

versi baru sedang disiapkan

in_review

versi baru sedang direview

ready_for_approval

versi baru siap disahkan

locked_new_version

versi baru sudah final

active

versi yang berlaku saat ini

Contoh:

Decision

Status

decision_v1.0_locked

superseded

decision_v2.0_locked

active

Tetapi meskipun decision_v1.0 menjadi superseded, datanya tetap harus bisa dibuka.

I. Apa yang harus dibuat tim IT pada UI?

Tim IT perlu membuat tombol:

Create New Version

Tombol ini muncul pada case yang sudah locked.

Saat diklik, sistem menampilkan pilihan:

Create New VersionReason for new version:[ ] Price/cost update[ ] New evidence/guideline[ ] Safety update[ ] Eligible population/update BIA[ ] CBA revision[ ] Recommendation revision[ ] Policy brief correction[ ] OtherDescription of change:[Text box]Which component to update?[ ] Local input only[ ] Evidence layer[ ] CEA/BIA calculation[ ] EtD appraisal[ ] CBA[ ] Policy brief[ ] Full decision review[Cancel] [Create version]

Setelah itu sistem membuat versi baru dengan status draft_revision.

J. Tampilan version history

Sistem harus punya halaman:

Version History

Contoh tampilan:

Version

Type

Change reason

Created by

Created at

Status

Linked decision

v1.0

Decision

Initial KFT decision

Ketua KFT

2026-05-20

locked

DEC_v1.0

v1.1

Local input

ARNI price update

Farmasi RS

2026-08-01

draft

linked to DEC_v1.0

v1.2

Calculation

CEA/BIA rerun

HTA analyst

2026-08-02

calculated

CALC_v1.2

v2.0

Decision

Revised KFT decision

Ketua KFT

2026-08-15

locked

DEC_v2.0

K. Database/tabel yang dibutuhkan

Minimal tabel untuk Step 15:

Tabel

Fungsi

version_history

Menyimpan semua versi

decision_records

Menyimpan keputusan lama dan baru

case_versions

Menyimpan versi case

local_input_versions

Menyimpan versi harga/biaya/volume

evidence_versions

Menyimpan versi evidence/case pack

calculation_runs

Menyimpan hasil CEA/BIA tiap versi

policy_brief_versions

Menyimpan versi policy brief

revision_requests

Menyimpan alasan revisi

audit_logs

Mencatat semua perubahan

supersession_links

Menghubungkan decision lama dan decision baru

Contoh tabel version_history

Field

Contoh

version_id

HF_ARNI_ACEI_001_v1.1

case_id

HF_ARNI_ACEI_001

version_type

local_input_update

parent_version_id

HF_ARNI_ACEI_001_v1.0

parent_decision_id

DEC_HF_ARNI_ACEI_001_v1.0

change_reason

Price update

change_description

Harga ARNI diperbarui dari data RS Unud Agustus 2026

created_by

farmasi_rs_01

created_at

timestamp

status

draft_revision

Contoh tabel supersession_links

Field

Contoh

old_decision_id

DEC_HF_ARNI_ACEI_001_v1.0

new_decision_id

DEC_HF_ARNI_ACEI_001_v2.0

reason

Price update and revised BIA

superseded_at

timestamp

superseded_by

ketua_kft_01

L. Aturan edit setelah locked

Tim IT harus membuat permission rule:

Kondisi

Hak edit

Case belum locked

boleh edit sesuai role

Case locked

hanya view/download

Case locked dan perlu update

harus create new version

Versi baru masih draft

boleh edit sesuai role

Versi baru locked

tidak boleh edit langsung

Contoh pesan sistem:

“This decision is locked. Please create a new version to make changes.”

atau dalam Bahasa Indonesia:

“Keputusan ini sudah dikunci. Untuk melakukan perubahan, buat versi baru.”

M. Audit trail Step 15

Setiap pembuatan versi baru harus tercatat.

Aktivitas

Data yang dicatat

User klik create new version

user, case_id, old_decision_id, timestamp

Alasan versi baru

price/evidence/safety/CBA/recommendation

Data lama yang dirujuk

parent_version_id

Data baru yang dibuat

new_version_id

Update harga

nilai lama, nilai baru, sumber

Update evidence

evidence lama, evidence baru

Run ulang CEA/BIA

calculation_run_id lama dan baru

Generate policy brief baru

brief lama dan baru

Lock decision baru

decision lama dan baru

Supersede decision lama

old_decision_id, new_decision_id

Audit ini harus memungkinkan reviewer melihat:

“Mengapa keputusan lama direvisi?”

N. Hubungan Step 15 dengan step lain

Step 15 tidak selalu mengulang semua step. Sistem harus mengarahkan ke step yang relevan.

Jenis update

Workflow yang perlu diulang

Harga obat berubah

Step 7 → Step 8 → Step 12/13 bila perlu

Biaya rawat inap berubah

Step 7 → Step 8

Eligible population berubah

Step 7 → Step 8

Evidence baru

Step 6 → Step 8 → Step 9 → Step 10

Safety issue

Step 6 → Step 9 → Step 10

CBA berubah

Step 11 → Step 12 → Step 13

Recommendation berubah

Step 10 → Step 12 → Step 13

Policy brief format berubah

Step 12 saja

Keputusan final berubah

Step 13 → Step 14

O. Contoh skenario untuk ARNI vs ACEI

Skenario 1 — Harga ARNI turun

Keputusan lama: decision_v1.0_locked.

Farmasi RS input harga ARNI baru.

Sistem membuat local_input_v1.1.

Sistem menjalankan ulang CEA/BIA: CALC_v1.1.

Sistem menampilkan perbandingan ICER dan BIA lama vs baru.

Jika hasil berubah signifikan, sistem menandai requires KFT review.

KFT bisa membuat policy brief baru.

Jika disetujui, Ketua KFT lock decision_v2.0.

Skenario 2 — Guideline baru keluar

Analis HTA klik create new version: reason = new evidence/guideline.

Sistem membuat evidence_v1.1.

Analis memperbarui evidence summary dan certainty.

Jika benefit/harms berubah, EtD perlu diperbarui.

Sistem membuat EtD session baru.

Rekomendasi bisa tetap sama atau berubah.

Policy brief versi baru dibuat.

Ketua KFT approve/lock bila keputusan berubah.

Skenario 3 — CBA perlu diperketat

Keputusan lama sudah locked.

KFT ingin menambahkan kriteria monitoring lebih ketat.

Sistem membuat cba_v1.1.

Policy brief baru dibuat.

Ketua KFT approve CBA baru.

Jika hanya CBA berubah tanpa mengubah rekomendasi utama, bisa menjadi decision_v1.1_locked.

P. Error handling

Tim IT perlu menangani error berikut:

Kondisi

Tindakan sistem

User mencoba edit decision locked

Blokir, minta create new version

User membuat versi baru tanpa alasan

Tampilkan error “reason required”

Harga baru diinput tanpa sumber

Warning/fatal sesuai aturan

Evidence baru tanpa referensi

Warning

Versi baru dibuat tetapi tidak lengkap

Status draft_revision

Policy brief lama dibuka setelah ada versi baru

Tampilkan label superseded jika sudah diganti

Dua user mengedit versi baru bersamaan

Gunakan locking/edit history

Q. Endpoint/API yang dibutuhkan

Endpoint

Method

Fungsi

/cases/{case_id}/versions

GET

melihat riwayat versi

/cases/{case_id}/new-version

POST

membuat versi baru

/versions/{version_id}

GET

melihat detail versi

/versions/{version_id}/compare

GET

membandingkan versi lama dan baru

/cases/{case_id}/local-inputs/new-version

POST

update harga/biaya

/cases/{case_id}/evidence/new-version

POST

update evidence

/cases/{case_id}/calculations/rerun

POST

menjalankan ulang CEA/BIA

/cases/{case_id}/policy-brief/regenerate

POST

membuat policy brief baru

/decisions/{decision_id}/supersede

POST

menandai keputusan lama digantikan

/cases/{case_id}/audit-trail

GET

melihat audit trail

R. Pseudocode untuk tim IT

1. User opens locked case.2. System shows case as read-only.3. User clicks "Create New Version".4. System asks reason for new version.5. User selects reason:      price/cost update,      new evidence,      safety update,      CBA revision,      recommendation revision,      policy brief update,      other.6. System creates new version_id and links it to parent decision_id.7. System copies relevant locked data into new draft version.8. User edits only the selected component.9. System saves changes as draft_revision.10. If local input changed:      run new CEA/BIA.11. If evidence changed:      require evidence review.12. If EtD/recommendation/CBA changed:      require KFT review.13. Generate new policy brief if needed.14. If new decision requires approval:      send to approver.15. If approver locks new decision:      create new decision_id.16. Mark old decision as superseded if appropriate.17. Keep old decision read-only and downloadable.18. Write all actions to audit log.

S. Acceptance criteria Step 15 untuk IT

Step 15 dianggap selesai jika sistem bisa:

Acceptance criteria

Harus bisa

Menampilkan case locked sebagai read-only

Ya

Mencegah edit langsung pada data locked

Ya

Menyediakan tombol Create New Version

Ya

Mewajibkan alasan pembuatan versi baru

Ya

Membuat new_version_id

Ya

Menghubungkan versi baru dengan parent decision

Ya

Membuat versi baru untuk local input

Ya

Membuat versi baru untuk evidence

Ya

Membuat calculation run baru bila input berubah

Ya

Membuat policy brief baru bila data berubah

Ya

Menyimpan decision lama tetap locked

Ya

Menyediakan version history

Ya

Menyediakan compare old vs new version

Ideal, minimal version history

Menandai decision lama sebagai superseded bila ada decision baru

Ya

Mencatat semua perubahan ke audit trail

Ya

Tidak menimpa file/dokumen lama

Ya

Mengizinkan approval/lock untuk versi baru

Ya

T. Pesan untuk tim IT

Pada Step 15, sistem harus mendukung mekanisme versioning setelah decision locked. Jika ada perubahan harga obat, biaya layanan, volume pasien, uptake, evidence/guideline baru, safety update, CBA revision, atau perubahan rekomendasi, sistem tidak boleh mengubah decision record lama. Keputusan lama harus tetap read-only dan tersimpan sebagai arsip.

Sistem harus menyediakan tombol Create New Version pada case yang sudah locked. Saat tombol ini diklik, user wajib memilih alasan perubahan, misalnya price/cost update, new evidence, safety update, BIA update, CBA revision, recommendation revision, atau policy brief correction. Sistem kemudian membuat new_version_id yang terhubung dengan parent_decision_id.

Jika perubahan adalah harga/biaya/volume, sistem membuat local_input_version_id baru dan menjalankan ulang CEA/BIA. Jika perubahan adalah evidence/guideline, sistem membuat evidence_version_id baru dan meminta review ulang oleh Analis HTA. Jika perubahan memengaruhi rekomendasi atau CBA, sistem harus meminta review/approval ulang oleh KFT/Ketua KFT. Semua versi lama tetap tersimpan, policy brief lama tetap dapat diunduh, dan semua perubahan harus tercatat di audit trail. Jika versi baru disetujui dan dikunci, sistem membuat decision_id baru dan dapat menandai decision lama sebagai superseded, bukan menghapusnya.

Kesimpulan sederhana

Step 15 adalah mekanisme pembaruan setelah keputusan final.

Untuk tim IT, inti pekerjaannya adalah:

keputusan locked harus read-only;

perubahan tidak boleh overwrite;

sistem harus membuat versi baru;

alasan perubahan wajib dicatat;

versi baru harus terhubung dengan keputusan lama;

data yang berubah menentukan step mana yang diulang;

CEA/BIA harus dihitung ulang jika local input berubah;

EtD/rekomendasi harus direview ulang jika evidence/CBA berubah;

policy brief baru dibuat jika data berubah;

audit trail harus lengkap.

Dengan Step 15, DeciBridge menjadi sistem yang hidup dan bisa diperbarui, tetapi tetap menjaga keputusan lama sebagai arsip resmi yang tidak berubah.

D. Flowchart dalam bentuk swimlane berdasarkan aktor

Ini versi yang lebih mudah dipahami tim IT karena terlihat siapa melakukan apa.

E. Output yang harus dihasilkan pada setiap tahap

Step

Output minimal

Login

Session aktif dan hak akses sesuai role

Buat/pilih case

Case dashboard dengan status dan version_id

Upload/input data

File tersimpan dan siap validasi

Validasi

Error report atau valid import report

Simpan database

Data tersimpan dengan version_id

Review case pack

Evidence summary siap rapat

Local input layer

Harga/biaya/volume/uptake versi terbaru

CEA/BIA

Incremental cost, ICER, budget impact, sensitivitas

EtD appraisal

Judgement dan rationale per domain

Traffic-light

Warna hijau/kuning/merah per domain

Recommendation

Draft rekomendasi: adopt/restrict/defer/do not adopt/reassess

CBA

Eligibility, prescriber, monitoring, stop rule

Policy brief

Word/PDF draft

Approve/lock

Final decision record

Audit/versioning

Log perubahan dan dokumen final yang dapat ditelusuri

F. Rekomendasi struktur modul aplikasi untuk tim IT

Agar IT mudah mengerjakan, workflow di atas dapat diterjemahkan menjadi modul berikut:

Modul

Fungsi

Step terkait

M1 Auth & Role Management

Login dan role-based access

Step 1

M2 Case Dashboard

Membuat/memilih/memantau kasus

Step 2

M3 Excel Import & Validation Engine

Upload, validasi, staging

Step 3–5

M4 Evidence Layer / Case Pack

Menampilkan PICO, evidence, effect estimate, certainty

Step 6

M5 Local Input Layer

Input harga, biaya, LOS, volume, uptake

Step 7

M6 CEA Quick Engine

Hitung risk, benefit, incremental cost, ICER

Step 8

M7 BIA Engine

Hitung budget impact dan skenario

Step 8

M8 EtD Appraisal

Judgement dan rationale

Step 9

M9 Traffic-light & Recommendation Engine

Warna dan rekomendasi awal

Step 10

M10 CBA Builder

Kriteria akses bila rekomendasi bersyarat

Step 11

M11 Policy Brief Generator

Export Word/PDF

Step 12

M12 Approval & Lock Decision

Review, approve, lock

Step 13

M13 Audit Trail & Versioning

Log, riwayat versi, rekonstruksi keputusan

Step 14–15

G. Endpoint/API yang dapat diminta ke tim IT

Berdasarkan workflow tersebut, IT dapat membuat endpoint minimal berikut:

Endpoint

Method

Fungsi

/auth/login

POST

Login pengguna

/cases

GET/POST

Melihat daftar kasus dan membuat kasus baru

/cases/{case_id}

GET/PUT

Melihat/mengedit identitas kasus

/cases/{case_id}/upload-excel

POST

Upload workbook dan validasi

/cases/{case_id}/evidence

GET/PUT

Kelola evidence layer/case pack

/cases/{case_id}/local-inputs

GET/POST

Kelola input lokal dan versioning

/cases/{case_id}/cea/run

POST

Jalankan CEA quick

/cases/{case_id}/bia/run

POST

Jalankan BIA

/cases/{case_id}/etd

GET/POST

Kelola EtD appraisal dan rationale

/cases/{case_id}/recommendation

GET/PUT

Buat/edit rekomendasi

/cases/{case_id}/policy-brief

POST

Generate policy brief Word/PDF

/cases/{case_id}/lock

POST

Approve dan lock decision

/cases/{case_id}/audit-trail

GET

Lihat audit trail

Daftar endpoint ini sesuai dengan lampiran teknis MVP dalam dokumen DeciBridge.

H. Pesan untuk tim IT

DeciBridge perlu dibangun sebagai sistem case-based. Setiap case dimulai dari login sesuai role, kemudian sekretariat/analis membuat atau memilih kasus. Analis mengupload workbook Excel standar atau mengisi data manual. Sistem harus memvalidasi template, sheet, field wajib, tipe data, rentang nilai, dan konsistensi internal. Data valid disimpan ke database utama dengan version_id, sedangkan data tidak valid masuk staging/rejected dan menghasilkan error report. Setelah itu analis meninjau case pack/evidence summary, farmasi RS mengisi local input layer berupa harga obat, biaya layanan, LOS, volume pasien eligible, dan uptake. Sistem kemudian menjalankan CEA quick dan BIA. Anggota KFT mengisi EtD judgement dan rationale, lalu sistem menampilkan traffic-light dan rekomendasi awal. Jika rekomendasi bersyarat, KFT mengisi criteria-based access. Sistem kemudian menghasilkan policy brief otomatis. Ketua KFT melakukan review, approve, dan lock decision. Setelah keputusan terkunci, sistem menyimpan decision record, audit trail, dan dokumen final. Bila ada perubahan harga atau bukti baru, sistem harus membuat versi baru tanpa menimpa keputusan lama.

I. Kesimpulan untuk tim IT

Workflow yang perlu dibuat bukan hanya “upload Excel lalu keluar laporan”, tetapi alur keputusan lengkap KFT. Poin teknis paling penting adalah:

Semua berjalan per case.

Evidence layer dan local input layer harus dipisahkan.

Setiap upload dan perubahan input harus punya version_id.

Data invalid masuk staging, bukan langsung database final.

CEA/BIA harus bisa diverifikasi dengan Excel pembanding.

EtD harus menyimpan judgement dan rationale.

Recommendation engine hanya memberi rekomendasi awal, keputusan final tetap oleh Ketua KFT.

Jika rekomendasi bersyarat, sistem wajib menyediakan CBA form.

Policy brief harus bisa dibuat otomatis dari database.

Setelah lock decision, data final tidak boleh diedit langsung; revisi harus menjadi versi baru.

