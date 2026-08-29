"""Isi awal database: master cabang dan akun. Aman dijalankan berulang kali."""
import os
from app.models import *
from app.auth import hash_pw

PW = os.environ.get("SEED_PASSWORD", "password123")

# Setel ulang password akun bawaan. Isi RESET_AKUN=1 di Environment Variables
# bila password admin terlupa, lalu Redeploy. Hapus lagi setelah berhasil masuk.
RESET = os.environ.get("RESET_AKUN") == "1"

# (nama, kota untuk tanggal surat, alamat lengkap)
CABANG = [
    ("Klender", "Jakarta",
     "Jl. Raya Bekasi No.KM.17, RT.2/RW.3, Jatinegara, Kec. Cakung, Kota Jakarta Timur, "
     "Daerah Khusus Ibukota Jakarta 13930"),
    ("Ceger", "Tangerang Selatan",
     "Jl. Ceger Raya No.1b, Jurang Manggu Tim., Aren, Kota Tangerang Selatan, Banten 15225"),
    ("Bintara", "Bekasi",
     "Jl. Bintara No.31, RT.013/RW.010, Bintara, Kec. Bekasi Bar., Kota Bks, Jawa Barat 17134"),
    ("Radjiman", "Jakarta",
     "Jl. Dr. KRT Radjiman Widyodiningrat No.20, RT.1/RW.13, Jatinegara, Kec. Cakung, "
     "Kota Jakarta Timur, Daerah Khusus Ibukota Jakarta 13930"),
    ("Jatimulya", "Bekasi",
     "Jl. HM. Joyo Martono No.9-4, RW.006, Jatimulya, Kec. Tambun Sel., Kabupaten Bekasi, "
     "Jawa Barat 17620"),
    ("Dramaga", "Bogor",
     "Jl. Raya Tanjakan Cinangneng, Bojong Jengkol, Kec. Ciampea, Kabupaten Bogor, "
     "Jawa Barat 16620"),
    ("Condet", "Jakarta",
     "Jl. Raya Condet, RT.5/RW.3, Batu Ampar, Kec. Kramat Jati, Kota Jakarta Timur, "
     "Daerah Khusus Ibukota Jakarta 13520"),
    ("Jatibening", "Bekasi",
     "Jl. Caman Raya 11E dan 11F, Service Center, RT.004/RW.003, Jatibening Baru, "
     "Kec. Pd. Gede, Kota Bks, Jawa Barat 17412"),
    ("Sawangan", "Depok",
     "Jl. Raya Sawangan, Mampang, Kec. Pancoran Mas, Kota Depok, Jawa Barat 16433"),
    ("Warbong", "Bekasi",
     "Warung Bongkok, Jl. Raya Imam Bonjol, Sukadanau, Kec. Cikarang Bar., "
     "Kabupaten Bekasi, Jawa Barat 17530"),
    ("Cinere", "Depok",
     "Jl. Cinere Raya No.11, RT.02, Cinere, Kec. Cinere, Kota Depok, Jawa Barat 16514"),
    ("Cibinong", "Bogor",
     "Jl. Raya Cikaret No.16916 Blk D no. 9, Pabuaran, Kec. Cibinong, Kabupaten Bogor, "
     "Jawa Barat 16915"),
    ("Karawang", "Karawang",
     "Jl. Raya Teluk Jambe No.15, Telukjambe, Telukjambe Timur, Karawang, "
     "Jawa Barat 41361"),
    ("Jatiwaringin", "Bekasi",
     "Jl. Raya Jatiwaringin No.6, RT.1/RW.9, Jaticempaka, Kec. Pd. Gede, Kota Bks, "
     "Jawa Barat 17411"),
    ("Cikampek", "Karawang",
     "Jl. Ir. Haji Juanda, Jomin Bar., Kec. Kota Baru, Karawang, Jawa Barat 41374"),
    ("Cilangkap", "Jakarta",
     "Jl. Raya Cilangkap No.6, RT.7/RW.1, Cilangkap, Kec. Cipayung, Kota Jakarta Timur, "
     "Daerah Khusus Ibukota Jakarta 13870"),
    ("Pejaten", "Jakarta",
     "Pejaten Office Park, Jl. Buncit Raya No.E79, RT.1/RW.7, Pejaten Bar., Ps. Minggu, "
     "Kota Jakarta Selatan, Daerah Khusus Ibukota Jakarta 12510"),
    ("Cibubur", "Bogor",
     "Jl. Alternatif Cibubur, Cileungsi, KM 1 No. 1-2, Cileungsi, Kec. Cileungsi, "
     "Kabupaten Bogor, Jawa Barat 16820"),
]

# Kantor pusat: dipakai sebagai kop surat pengajuan Insentif Profit ARM.
PUSAT = ("Pusat", "MFlash Pusat", "Jakarta",
         "Pejaten Office Park, Jl. Buncit Raya No.E79, RT.1/RW.7, Pejaten Bar., "
         "Ps. Minggu, Kota Jakarta Selatan, Daerah Khusus Ibukota Jakarta 12510")

# Cabang yang tidak ikut menambah total laba bersih pada Insentif Profit ARM
TIDAK_HITUNG_ARM = {"Pejaten", "Pusat"}

# Store Leader per cabang. Password awal sama untuk semua; setiap orang
# menggantinya sendiri lewat menu Ganti Password saat pertama masuk.
PW_SL = "12345678"
STORE_LEADER = [
    ("Bintara",      "Tatang Saputra"),
    ("Radjiman",     "Rinaldy Alamsyah"),
    ("Jatimulya",    "Rizqi Fadhillah"),
    ("Dramaga",      "Tony Nugroho"),
    ("Condet",       "Yusup Ismail"),
    ("Jatibening",   "Chandra Kurniawan"),
    ("Sawangan",     "Muhammad Waldi"),
    ("Warbong",      "Saiful Bahmi"),
    ("Cinere",       "Ery Suryo"),
    ("Cibinong",     "Feri Irawan"),
    ("Karawang",     "Busyra Kirawa"),
    ("Jatiwaringin", "Buyung Widagdo"),
    ("Cikampek",     "Ikbal Sabari"),
    ("Cilangkap",    "Rusmindar"),
    ("Pejaten",      "Harris Januar"),
    ("Cibubur",      "Vicky Faldhy"),
]

AKUN = [
    ("sl.klender", "Vicky Faldhy Agita", "Store Leader MFlash Klender", ROLE_SL, "Klender"),
    ("arm",     "Budiarja Ibrahim", "Store Area Manager",    ROLE_ARM,     None),
    ("ceo",     "Zaskanul Tibalky", "CEO MFlash",            ROLE_CEO,     None),
    ("finance", "Galih Permana",    "Chief Finance Officer", ROLE_FINANCE, None),
    ("admin",   "Administrator",    "IT",                    ROLE_ADMIN,   None),
]


def jalankan():
    init_db()
    db = SessionLocal()
    baru = diperbarui = 0
    for nama, kota, alamat in CABANG:
        b = db.query(Branch).filter_by(name=nama).first()
        if not b:
            db.add(Branch(name=nama, display_name=f"MFlash – {nama}",
                          address=alamat, city=kota, active=True,
                          hitung_arm=nama not in TIDAK_HITUNG_ARM))
            baru += 1
        elif not (b.address or "").strip() or b.address.strip() == "-":
            b.address, b.city = alamat, kota   # lengkapi yang masih kosong
            diperbarui += 1

    nm, tampil, kota_p, alamat_p = PUSAT
    if not db.query(Branch).filter_by(name=nm).first():
        db.add(Branch(name=nm, display_name=tampil, address=alamat_p,
                      city=kota_p, active=True, hitung_arm=False))
        baru += 1
    db.commit()

    if RESET and db.query(User).count():
        diubah = 0
        for un, _fn, _pos, _role, _cabang in AKUN:
            u = db.query(User).filter_by(username=un).first()
            if u:
                u.password_hash = hash_pw(PW)
                u.active = True
                diubah += 1
        db.commit()
        print(f"RESET_AKUN aktif: password {diubah} akun bawaan disetel ulang. "
              f"Hapus RESET_AKUN dari Environment Variables setelah berhasil masuk.")

    if not db.query(User).count():
        for un, fn, pos, role, cabang in AKUN:
            bid = None
            if cabang:
                b = db.query(Branch).filter_by(name=cabang).first()
                bid = b.id if b else None
            db.add(User(username=un, password_hash=hash_pw(PW), full_name=fn,
                        position=pos, role=role, branch_id=bid))
        db.commit()
        print(f"akun awal dibuat ({len(AKUN)})")
    # Store Leader per cabang — hanya ditambahkan bila belum ada
    sl_baru, sl_lewat = 0, []
    for cabang, nama in STORE_LEADER:
        username = "sl." + cabang.lower()
        if db.query(User).filter_by(username=username).first():
            continue
        b = db.query(Branch).filter_by(name=cabang).first()
        if not b:
            sl_lewat.append(cabang)
            continue
        db.add(User(username=username, password_hash=hash_pw(PW_SL), full_name=nama,
                    position=f"Store Leader {cabang}", role=ROLE_SL,
                    branch_id=b.id, active=True))
        sl_baru += 1
    db.commit()
    if sl_baru:
        print(f"store leader: {sl_baru} akun baru dibuat (password awal {PW_SL})")
    if sl_lewat:
        print("cabang tidak ditemukan, SL dilewati: " + ", ".join(sl_lewat))

    print(f"cabang: {baru} baru, {diperbarui} dilengkapi, "
          f"{db.query(Branch).count()} total")
    db.close()


jalankan()
