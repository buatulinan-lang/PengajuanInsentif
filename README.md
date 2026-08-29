# Aplikasi Pengajuan Insentif MFlash

Deploy ke Vercel + Supabase (gratis, tanpa kartu kredit): lihat **DEPLOY.md**.

## Menjalankan lokal
```
pip install -r requirements.txt
python seed.py            # buat database + akun contoh
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
### Variabel lingkungan
| Nama | Fungsi |
|---|---|
| `DATABASE_URL` | Postgres (Supabase). Kosong = SQLite lokal. |
| `SECRET` | Kunci enkripsi sesi login. Wajib diisi di produksi. |
| `BASE_URL` | Domain publik; dipakai sebagai isi QR verifikasi. |
| `SEED_PASSWORD` | Password awal akun contoh. |

## Akun contoh (password: password123)
| Username | Peran |
|---|---|
| sl.klender | Store Leader (mengajukan) |
| arm | Area Regional Manager (approval 1) |
| ceo | CEO (approval 2) |
| finance | Pencairan |
| admin | Administrator |

## Alur
Draft → Proses Approval ARM → Proses Approval CEO → Proses Pencairan Finance → Done.
Tiap approval menghasilkan QR unik yang disisipkan ke dokumen Word dan bisa
dicek publik di `/verify/<token>`.

## Uji cepat setelah deploy
Pakai berkas MFlash Klender periode Juli 2026 — hasilnya harus persis:

| Jenis | Hasil |
|---|---|
| Profit Store Leader | Rp 1.900.000 |
| Sales & Team | Rp 1.563.919 |
| Purchasing | Rp 754.347 |

## Yang perlu dilengkapi
1. **`data/rules.json`** — aturan perhitungan insentif (tier % net profit, pengali,
   pengurang goal). Saat ini berisi nilai sementara.
2. **`app/calc.py` → `COLUMN_ALIASES`** — sesuaikan nama kolom dengan file Excel asli.
3. **Master cabang** — isi alamat lengkap tiap cabang lewat `seed.py` atau tabel `branches`.
   Alamat ini yang otomatis mengganti header dokumen Word.
4. **Template Word** — ada di `data/doc_templates/`. Agar pengisian lebih rapi,
   ganti teks yang berubah-ubah dengan penanda `{{NAMA}}`, `{{CABANG}}`, `{{PERIODE}}`,
   `{{TOTAL}}`, `{{KOTA_TANGGAL}}`, dan `{{QR_ARM}}` / `{{QR_CEO}}` / `{{QR_FINANCE}}`
   di area tanda tangan. Tanpa penanda pun tetap jalan (QR ditambahkan di akhir dokumen).
