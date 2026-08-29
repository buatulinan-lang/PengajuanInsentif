# Panduan Deploy: Supabase + GitHub + Vercel

Tanpa kartu kredit. Vercel Hobby dan Supabase Free keduanya cukup mendaftar
dengan akun GitHub / email.

## 1. Ambil connection string dari Supabase

1. Buka project Supabase → tombol **Connect** di bagian atas dashboard.
2. Ambil **Transaction pooler** (port **6543**), bukan Session pooler dan bukan
   Direct connection. Bentuknya:
   ```
   postgresql://postgres.[project-ref]:[PASSWORD]@aws-[region].pooler.supabase.com:6543/postgres
   ```
3. Ganti `[PASSWORD]` dengan password database Anda (bukan password login Supabase).
   Lupa? Settings → Database → **Reset database password**.

> **Kenapa port 6543?** Vercel berjalan model serverless: tiap permintaan bisa
> memakai koneksi baru. Transaction pooler dirancang untuk pola ini. Aplikasi
> sudah mengenali port 6543 dan otomatis mematikan connection pool bawaannya.
> Kalau password mengandung `@ : / #`, encode dulu (mis. `@` → `%40`).

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

Repositorinya boleh privat. `.gitignore` sudah mengecualikan database lokal dan
file unggahan.

## 3. Deploy di Vercel

1. Buka https://vercel.com → **Sign up** dengan akun GitHub. Tidak diminta kartu.
2. **Add New → Project** → pilih repository tadi → **Import**.
3. Framework Preset biarkan **Other**. Build & output settings tidak perlu diubah —
   `vercel.json` di repo sudah mengaturnya.
4. Buka **Environment Variables**, isi:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | connection string Supabase dari langkah 1 |
   | `SECRET` | teks acak panjang (kunci sesi login) |
   | `BASE_URL` | `https://<nama-proyek>.vercel.app` |
   | `SEED_PASSWORD` | password awal akun contoh |

5. **Deploy**. Saat pertama diakses, tabel dan data awal (18 cabang) dibuat
   otomatis di Supabase.

> `BASE_URL` baru diketahui setelah deploy pertama. Isi seadanya dulu, lalu
> setelah alamatnya keluar, perbarui nilainya dan **Redeploy**. Isi QR pada
> dokumen Word mengambil alamat dari sini.

## 4. Menjaga Supabase tidak dijeda

Project Supabase gratis berhenti sendiri bila tidak ada aktivitas selama 7 hari.
`vercel.json` sudah memuat cron harian yang memanggil `/health` setiap pukul 03:00
UTC — cukup untuk menjaganya tetap aktif, dan tersedia di paket Hobby tanpa biaya.

Pastikan berjalan: buka **Project → Settings → Cron Jobs** di Vercel, dan setelah
seminggu periksa project Supabase masih berstatus aktif (bukan *Paused*).

## 5. Setelah deploy

- Buka `https://<nama-proyek>.vercel.app`, login `admin` dengan nilai `SEED_PASSWORD`.
- Periksa Master Cabang, isi Master Sales, dan impor Master Supplier.
- Uji dengan data yang hasilnya sudah diketahui (lihat README).

## Lupa password admin

Password tersimpan terenkripsi, jadi tidak bisa dibaca kembali &mdash; hanya bisa
disetel ulang:

1. Vercel &rarr; Settings &rarr; Environment Variables
2. Ubah `SEED_PASSWORD` menjadi password baru yang Anda inginkan
3. Tambahkan variabel baru: `RESET_AKUN` bernilai `1`
4. Deployments &rarr; titik tiga di deployment teratas &rarr; **Redeploy**
5. Buka aplikasi, login `admin` dengan password baru
6. **Hapus `RESET_AKUN`**, lalu Redeploy sekali lagi

Yang disetel ulang hanya password kelima akun bawaan (`admin`, `arm`, `ceo`,
`finance`, `sl.klender`). Data cabang, sales, supplier, dan seluruh riwayat
pengajuan tidak tersentuh.

> Langkah 6 penting. Selama `RESET_AKUN` masih ada, setiap deploy akan
> mengembalikan password ke nilai `SEED_PASSWORD` &mdash; termasuk menimpa
> password yang nanti diubah lewat menu kelola akun.

## Catatan tentang Vercel Hobby

- **Tidak ada tidur.** Berbeda dengan Render gratis, aplikasi tidak dimatikan
  setelah menganggur. Permintaan pertama setelah lama diam butuh 2–5 detik
  untuk *cold start*, setelah itu normal.
- **Batas waktu 60 detik per permintaan.** Cukup lapang: file faktur ~8.000 baris
  diproses dalam hitungan detik.
- **Sistem berkas hanya-baca**, kecuali `/tmp`. Karena itu database, file Excel,
  dan lampiran semuanya disimpan di Supabase — bukan di disk server.
- **Alamat tidak terdaftar publik**, tapi siapa pun yang tahu alamatnya bisa
  membuka halaman login. Pakai `SEED_PASSWORD` yang kuat.
- Paket Hobby untuk penggunaan non-komersial. Bila nanti dipakai sebagai
  perkakas kerja resmi perusahaan, Vercel meminta upgrade ke paket Pro.
  Alternatif tanpa kartu saat itu: jalankan di komputer kantor sendiri.

## Alternatif: Render

Repo juga berisi `render.yaml` bila suatu saat Anda ingin memakai Render
(perlu verifikasi kartu, dan aplikasi tidur setelah 15 menit menganggur).
Di Render gunakan **Session pooler port 5432**, bukan 6543.
