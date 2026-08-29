"""
Mesin perhitungan Insentif Profit Store Leader.

Sumber data: file Laporan Laba/Rugi cabang (mis. KLENDER.xlsx).
Tiap bulan menempati 3 kolom: [rincian] [total] [prosentase].
JANUARI = C/D/E, FEBRUARI = F/G/H, ... DESEMBER = AJ/AK/AL.

Alur:
  Laba Bersih  = Total Laba Bersih Setelah Prepaid - Laba Ditahan
  Persentase   = Laba Bersih / Jumlah Omzet   (penentu kolom matriks)
  Insentif     = matriks[baris laba terdekat ke bawah][kolom GP%]
Aturan angkanya ada di data/rules.json agar bisa diubah tanpa menyentuh kode.
"""
import json, os, re
from openpyxl import load_workbook

RULES_PATH = "data/rules.json"

BULAN_XLS = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
             "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]

# Label baris yang dicari di kolom B (dicocokkan longgar, tanpa spasi/huruf besar)
BARIS = {
    "omzet":            "jumlah omzet madinah flash",
    "laba_kotor":       "laba kotor sesudah fee teknisi",
    "fee_teknisi":      "total biaya fee teknisi",
    "biaya_operasional": "total biaya operasional",
    "laba_setelah_pajak": "total laba bersih setelah pajak",
    "laba_setelah_prepaid": "total laba bersih setelah prepaid",
}


class CalcError(Exception):
    pass


def load_rules():
    with open(RULES_PATH) as f:
        return json.load(f)


def _key(s):
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def _num(v):
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _cari_kolom_bulan(ws, bulan):
    """Kembalikan (kolom_rincian, kolom_total, kolom_persen) untuk bulan ke-n."""
    target = BULAN_XLS[bulan - 1]
    for r in range(1, 40):
        for c in range(1, ws.max_column + 1):
            if _key(ws.cell(r, c).value) == _key(target):
                return c, c + 1, c + 2
    raise CalcError(f"Kolom bulan {target} tidak ditemukan di file Excel.")


def _cari_baris(ws):
    """Peta nama internal -> nomor baris, dari label di kolom B."""
    hasil, dicari = {}, {k: _key(v) for k, v in BARIS.items()}
    for r in range(1, ws.max_row + 1):
        k = _key(ws.cell(r, 2).value)
        if not k:
            continue
        for nama, pola in dicari.items():
            if nama not in hasil and k == pola:
                hasil[nama] = r
    kurang = [BARIS[n] for n in BARIS if n not in hasil]
    if kurang:
        raise CalcError("Baris berikut tidak ditemukan di Excel: " + "; ".join(kurang))
    return hasil


def hitung_profit_sl(path, bulan, laba_ditahan_pct=None, sheet=None):
    rules = load_rules()["profit_sl"]
    if laba_ditahan_pct is None:
        laba_ditahan_pct = rules.get("laba_ditahan_pct_default", 7)

    wb = load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb[wb.sheetnames[0]]
    c_rinci, c_total, _ = _cari_kolom_bulan(ws, bulan)
    baris = _cari_baris(ws)

    def total(nama):
        return _num(ws.cell(baris[nama], c_total).value)

    omzet          = total("omzet")
    laba_kotor     = total("laba_kotor")          # sesudah fee teknisi
    fee_teknisi    = total("fee_teknisi")
    biaya_ops      = total("biaya_operasional")
    setelah_pajak  = total("laba_setelah_pajak")
    setelah_prepaid = total("laba_setelah_prepaid")

    if omzet == 0:
        raise CalcError(f"Data bulan {BULAN_XLS[bulan-1].title()} masih kosong "
                        f"(omzet 0). Pilih bulan lain atau lengkapi Excel-nya.")

    prepaid = setelah_pajak - setelah_prepaid       # total PRE PAID EXPENSE
    laba_kotor_sebelum_fee = laba_kotor + fee_teknisi

    laba_ditahan = round(setelah_prepaid * laba_ditahan_pct / 100)
    laba_bersih = setelah_prepaid - laba_ditahan

    # penentu kolom matriks: laba bersih berbanding jumlah omzet
    gp_pct = laba_bersih / omzet * 100 if omzet else 0

    # kolom matriks: ambang tertinggi yang masih terpenuhi
    kolom = rules["kolom_gp"]
    idx_kolom, label_kolom = 0, kolom[0]["label"]
    for i, k in enumerate(kolom):
        if gp_pct >= k["min_pct"]:
            idx_kolom, label_kolom = i, k["label"]

    # baris matriks: turun ke ambang terdekat di bawah laba bersih
    insentif, baris_matriks = 0, None
    for m in rules["matriks"]:
        if laba_bersih >= m["laba_min"]:
            insentif, baris_matriks = m["insentif"][idx_kolom], m["laba_min"]

    return {
        "jenis": "profit_sl",
        "bulan": bulan,
        "bulan_nama": BULAN_XLS[bulan - 1].title(),
        "omzet": omzet,
        "laba_kotor_sesudah_fee": laba_kotor,
        "fee_teknisi": fee_teknisi,
        "laba_kotor_sebelum_fee": laba_kotor_sebelum_fee,
        "biaya_operasional": biaya_ops,
        "prepaid": prepaid,
        "laba_setelah_prepaid": setelah_prepaid,
        "laba_ditahan_pct": laba_ditahan_pct,
        "laba_ditahan": laba_ditahan,
        "laba_bersih": laba_bersih,
        "gp_pct": round(gp_pct, 2),
        "kolom_matriks": label_kolom,
        "baris_matriks": baris_matriks,
        "total": insentif,
    }


def compute(jenis, path, bulan=None, laba_ditahan_pct=None):
    if jenis == "profit_sl":
        return hitung_profit_sl(path, bulan, laba_ditahan_pct)
    raise CalcError(f"Perhitungan otomatis untuk '{jenis}' belum tersedia. "
                    f"Isi nilainya secara manual.")


# ---------------------------------------------------------------- rotasi
def pengali_rotasi(offset, tujuan_ge_asal):
    """Proporsi pengali (asal, tujuan) pada bulan ke-`offset` sejak mutasi."""
    rot = load_rules()["profit_sl"]["rotasi"]
    tabel = rot["tujuan_lebih_besar_atau_sama"] if tujuan_ge_asal else rot["tujuan_lebih_kecil"]
    if offset < 0:                      # bulan sebelum mutasi efektif
        return 100.0, 0.0
    i = min(offset, len(tabel["asal"]) - 1)
    return float(tabel["asal"][i]), float(tabel["tujuan"][i])


def label_bulan_rotasi(offset):
    if offset < 0:
        return "sebelum mutasi"
    return "Bulan H" if offset == 0 else f"Bulan H+{offset}"


def hitung_blok(blok, bulan, tahun, laba_ditahan_pct):
    """
    blok = {
      "tipe": "tunggal" | "rotasi",
      "asal":   {"cabang": str, "path": str},
      "tujuan": {"cabang": str, "path": str},   # hanya untuk rotasi
      "mutasi_bulan": int, "mutasi_tahun": int  # hanya untuk rotasi
    }
    """
    hasil_asal = hitung_profit_sl(blok["asal"]["path"], bulan, laba_ditahan_pct)

    if blok["tipe"] != "rotasi":
        return {
            "tipe": "tunggal",
            "asal": {"cabang": blok["asal"]["cabang"], "hasil": hasil_asal,
                     "pengali": 100.0, "insentif": hasil_asal["total"]},
            "total": hasil_asal["total"],
        }

    hasil_tujuan = hitung_profit_sl(blok["tujuan"]["path"], bulan, laba_ditahan_pct)
    offset = ((tahun * 12 + bulan) -
              (blok["mutasi_tahun"] * 12 + blok["mutasi_bulan"]))
    tujuan_ge = hasil_tujuan["laba_bersih"] >= hasil_asal["laba_bersih"]
    p_asal, p_tujuan = pengali_rotasi(offset, tujuan_ge)

    ins_asal = round(hasil_asal["total"] * p_asal / 100)
    ins_tujuan = round(hasil_tujuan["total"] * p_tujuan / 100)
    return {
        "tipe": "rotasi",
        "offset": offset,
        "offset_label": label_bulan_rotasi(offset),
        "kasus": ("Net Profit cabang tujuan lebih besar atau sama"
                  if tujuan_ge else "Net Profit cabang tujuan lebih kecil"),
        "mutasi": f"{BULAN_XLS[blok['mutasi_bulan']-1].title()} {blok['mutasi_tahun']}",
        "asal": {"cabang": blok["asal"]["cabang"], "hasil": hasil_asal,
                 "pengali": p_asal, "insentif": ins_asal},
        "tujuan": {"cabang": blok["tujuan"]["cabang"], "hasil": hasil_tujuan,
                   "pengali": p_tujuan, "insentif": ins_tujuan},
        "total": ins_asal + ins_tujuan,
    }


def hitung_pengajuan(blok_list, bulan, tahun, laba_ditahan_pct=None):
    """Hitung seluruh blok cabang pada satu pengajuan."""
    hasil, catatan = [], []
    for i, blok in enumerate(blok_list, 1):
        try:
            hasil.append(hitung_blok(blok, bulan, tahun, laba_ditahan_pct))
        except CalcError as e:
            catatan.append(f"Blok {i}: {e}")
    return {"blok": hasil, "total": sum(b["total"] for b in hasil),
            "catatan": catatan}
