# Panduan Deploy: Supabase + GitHub + Render

## 1. Ambil connection string dari Supabase

1. Buka project Supabase → tombol **Connect** di bagian atas dashboard.
2. Pilih tab **ORMs / Connection string**, lalu ambil **Session pooler**.
   Bentuknya:
   ```
   postgresql://postgres.[project-ref]:[PASSWORD]@aws-[region].pooler.supabase.com:5432/postgres
   ```
3. Ganti `[PASSWORD]` dengan password database Anda (bukan password login Supabase).
   Kalau lupa: Settings → Database → **Reset database password**.

> **Gunakan Session pooler (port 5432), bukan Direct connection.**
> Render berjalan di jaringan IPv4, sedangkan direct connection Supabase hanya IPv6 —
> ini penyebab error `Network is unreachable` yang paling sering terjadi.
> Kalau password mengandung karakter khusus (`@ : / #`), encode dulu
> (mis. `@` → `%40`).

Aplikasi ini juga sudah mendukung Transaction pooler (port 6543) secara otomatis,
tapi Session pooler lebih cocok untuk aplikasi seperti ini.

## 2. Push ke GitHub

```bash
cd insentif-app
git init
git add .
git commit -m "Aplikasi pengajuan insentif"
git branch -M main
git remote add origin https://github.com/<akun-anda>/insentif-app.git
git push -u origin main
```

`.gitignore` sudah mengecualikan database lokal dan file upload,
jadi tidak ada data yang ikut ter-upload.

## 3. Deploy di Render

1. Login ke Render → **New** → **Web Service** → hubungkan repo GitHub tadi.
2. Isi:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Buka tab **Environment**, tambahkan:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | connection string Supabase dari langkah 1 |
   | `SECRET` | teks acak panjang (untuk enkripsi sesi login) |
   | `BASE_URL` | `https://<nama-app>.onrender.com` |
   | `SEED_PASSWORD` | password awal akun contoh |
   | `PYTHON_VERSION` | `3.11.9` |

4. Deploy. Saat pertama kali jalan, tabel dan akun awal dibuat otomatis di Supabase.

> `BASE_URL` wajib diisi dengan domain asli. Isi QR pada dokumen Word
> mengambil alamat dari sini — kalau salah, QR akan mengarah ke `localhost`.

Alternatif: karena repo sudah berisi `render.yaml`, Anda bisa pakai
**New → Blueprint** dan Render akan membaca konfigurasinya sendiri;
Anda tinggal mengisi 3 nilai yang ditandai `sync: false`.

## 4. Setelah deploy

- Login dengan `admin` / nilai `SEED_PASSWORD`, lalu **ganti semua password akun**.
- Isi master cabang beserta alamat lengkapnya (dipakai untuk header dokumen Word).

## Catatan penting soal free tier Render

- **Aplikasi tidur setelah 15 menit tanpa akses.** Permintaan pertama setelah itu
  butuh ±30–60 detik untuk bangun. Jatah 750 jam per bulan.
- **Tidak ada disk permanen.** Karena itu database, file Excel, dan lampiran
  screenshot semuanya disimpan di Postgres Supabase — bukan di disk Render.
  Dokumen Word dibuat ulang setiap kali diunduh, jadi selalu memuat QR terbaru.
- Untuk pemakaian harian oleh tim, paket **Starter** ($7/bulan) menghilangkan
  masalah tidur dan lambat di akses pertama.
- Jangan pakai database gratis bawaan Render — masa berlakunya hanya 30 hari.
  Supabase yang Anda punya jauh lebih cocok.

---

# 5. Ping otomatis (wajib, dan gratis)

Tanpa ini: aplikasi Render tidur tiap 15 menit, dan project Supabase dijeda
setelah 7 hari tanpa aktivitas. Endpoint `/health` sudah tersedia di aplikasi —
ia menyentuh database, jadi satu ping menyelesaikan kedua masalah sekaligus.

Pilih **salah satu**:

### Opsi A — cron-job.org (paling andal, disarankan)
1. Daftar gratis di https://cron-job.org
2. Create cronjob → URL: `https://<nama-app>.onrender.com/health`
3. Jadwal: setiap 10 menit. Simpan.

### Opsi B — GitHub Actions (sudah disiapkan di repo)
File `.github/workflows/keepalive.yml` sudah ada. Tinggal:
1. Repo GitHub → Settings → Secrets and variables → Actions → **New repository secret**
2. Name: `APP_URL`, Value: `https://<nama-app>.onrender.com`

Catatan: jadwal GitHub Actions kadang meleset beberapa menit, dan workflow
otomatis dinonaktifkan bila repo tidak ada aktivitas selama 60 hari.
Karena itu Opsi A lebih aman untuk jangka panjang.

### Memastikan berjalan
Buka `https://<nama-app>.onrender.com/health` di browser — harus muncul
`{"status":"ok", ...}`. Setelah seminggu, cek dashboard Supabase: project harus
tetap berstatus aktif, tidak "Paused".

---

# Ringkasan biaya

| Komponen | Sekarang | Bila tim sudah bergantung penuh |
|---|---|---|
| Render | Free (750 jam/bln, cukup untuk nyala terus) | Starter $7/bln |
| Supabase | Free (yang sudah Anda punya) | tetap Free |
| Ping otomatis | Free | Free |
| **Total** | **Rp 0** | **± Rp 115rb/bln** |

Naik ke Render Starter kalau: instance free mulai sering direstart tanpa
pemberitahuan, memori 512 MB terasa kurang, atau proses approval sudah jadi
alur resmi yang tidak boleh terganggu.

---

# Keamanan sebelum dipakai sungguhan

1. **Ganti semua password akun contoh** setelah login pertama.
2. `SECRET` harus teks acak panjang dan tidak pernah masuk ke Git.
3. Password database Supabase jangan dipakai ulang di tempat lain.
4. Data insentif karyawan bersifat sensitif — jangan bagikan URL aplikasi ke
   luar tim yang berkepentingan.
