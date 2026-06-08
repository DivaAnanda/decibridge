# Panduan Anggota KFT

**Akun demo**: `kft1@test.local` atau `kft2@test.local` / `TestPass123!`

## Tanggung Jawab Anda

- Memberi **judgement** pada 9 domain Evidence-to-Decision (EtD) GRADE.
- Memberi **bobot kepentingan** untuk masing-masing dari 9 domain.
- Membaca dossier yang disiapkan HTA Analyst sebelum vote.

## Apa yang Bisa Anda Lakukan

- ✅ Vote 9 domain EtD (judgement + certainty + catatan).
- ✅ Lampirkan referensi pada vote Anda.
- ✅ Edit vote Anda sendiri kapan saja (sebelum kasus terkunci).
- ✅ Set bobot 0–100 untuk masing-masing dari 9 domain.
- ✅ Lihat semua data kasus (read-only).
- ✅ Lihat rekomendasi & policy brief.

## Apa yang Tidak Bisa Anda Lakukan

- ❌ Edit input CEA / BIA / CBA.
- ❌ Edit vote anggota KFT lain.
- ❌ Submit kasus untuk tinjauan, approve, reject, lock, atau archive.
- ❌ Generate Policy Brief.
- ❌ Lihat / klik aksi state-transition (dropdown Tindakan akan kosong untuk Anda).

## Langkah Demi Langkah

### 1. Login & buka kasus yang menunggu vote Anda

- Login → Beranda → kartu "Aksi Cepat" akan mengarahkan Anda ke **Daftar Kasus**.
- Buka kasus dengan status `in_review` atau `draft` yang HTA Analyst minta dievaluasi.

### 2. Vote 9 domain EtD

Klik tab **EtD (9 domain)**. Anda akan melihat 9 kartu, masing-masing untuk satu domain GRADE:

1. **Masalah (Problem)** — Seberapa serius masalah klinis?
2. **Efek yang Diinginkan** — Seberapa besar manfaat?
3. **Efek yang Tidak Diinginkan** — Seberapa besar risiko?
4. **Kepastian Bukti** — Kualitas evidence?
5. **Nilai & Preferensi** — Apakah pasien akan menerima?
6. **Penggunaan Sumber Daya** — Efisien?
7. **Ekuitas** — Mempengaruhi ketimpangan?
8. **Kelayakan Implementasi** — Bisa dijalankan?
9. **Penerimaan oleh Stakeholder** — Diterima oleh tim?

Untuk masing-masing isi:

| Field | Pilihan |
|---|---|
| **Judgement** | Tidak (0) / Mungkin tidak (25) / Tidak pasti (50) / Mungkin ya (75) / Ya (100) |
| **Certainty** | Sangat rendah / Rendah / Sedang / Tinggi |
| **Catatan / Narrative** | Pertimbangan singkat Anda |
| **Referensi** | Centang referensi yang mendukung |

Vote Anda tersimpan otomatis. Anda dapat kembali dan mengubah jika ingin.

### 3. Set bobot domain

Klik tab **Rekomendasi** → kartu **Bobot Domain EtD**.

Anda akan melihat 9 slider, satu per domain. Geser ke nilai 0–100 yang mencerminkan **seberapa penting domain itu menurut Anda** untuk kasus ini.

Contoh: untuk obat dengan profil keamanan ketat seperti ARNI, Anda mungkin memberi:
- Efek yang Tidak Diinginkan: **90** (sangat penting)
- Kepastian Bukti: **85**
- Efek yang Diinginkan: **80**
- Ekuitas: **40** (kurang relevan untuk indikasi spesifik)

Klik **Simpan Bobot Saya**. Bobot Anda dirata-rata (atau median) dengan bobot anggota lain saat HTA/Sekretaris menjalankan "Hitung Rekomendasi".

### 4. Pantau hasil

Setelah cukup anggota vote + HTA menjalankan komputasi:
- Tab **Rekomendasi** akan menampilkan kartu besar dengan traffic-light HIJAU / KUNING / MERAH.
- Justifikasi otomatis menjelaskan sub-skor.
- Anda dapat melihat ini, tetapi tidak dapat mengubah keputusan akhir.

## Tips

- **Diskusikan dengan tim sebelum vote** — beberapa domain (seperti Ekuitas) bisa diperdebatkan.
- **Jangan biarkan domain kosong tanpa alasan** — sistem boleh menghitung dengan data parsial, tapi rekomendasi lebih kuat bila semua 9 terisi.
- **Tambahkan referensi pendukung** — vote tanpa referensi sah, tapi vote dengan rujukan lebih kredibel saat diaudit.
