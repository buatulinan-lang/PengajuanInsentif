"""
Insentif Purchasing.

Masukan: ekspor Accurate "Rincian Pembelian for RnD" satu bulan penuh
(kolom Tanggal, Pemasok, Total Harga, dan lainnya apa adanya).

Mekanisme (mengikuti tools Excel yang selama ini dipakai):
  1. Tiap pemasok dikategorikan TERTARGET / NON TERTARGET dari Master Supplier.
     Pemasok yang belum terdaftar dikeluarkan dari perhitungan dan dilaporkan.
  2. % Tertarget  = pembelian tertarget / total pembelian terkategori.
  3. Tier insentif dari % tertarget: >=50% -> 0,2% ; >=35% -> 0,15% ; >=20% -> 0,1%.
  4. Nominal insentif = total pembelian terkategori x tier.
  5. Pencapaian goal = % tertarget / Goal Performate.
  6. Insentif final  = nominal x pengali: <85% -> 25% ; <100% -> 80% ; >=100% -> 100%.
Angka-angkanya ada di data/rules.json bagian "purchasing".
"""
import json
from collections import defaultdict

from app.calc import RULES_PATH, CalcError, _num
from app.calc_sales import _baca_tabel, _bulan, _k

TERTARGET = "TERTARGET"


def hitung_purchasing(path, bulan, tahun=None, master_supplier=None,
                      goal_pct=None):
    rules = json.load(open(RULES_PATH))["purchasing"]
    if goal_pct is None:
        goal_pct = rules["goal_performate_pct"]

    master = {_k(n): (k or "").strip().upper()
              for n, k in (master_supplier or {}).items()}
    if not master:
        raise CalcError("Master Supplier masih kosong. Impor dulu daftar "
                        "kategori supplier lewat menu Master Supplier.")

    baris = _baca_tabel(path, ["Tanggal", "Pemasok", "Total Harga"])

    per_supplier = defaultdict(float)
    per_kategori = defaultdict(float)
    tak_terdaftar = defaultdict(float)
    dipakai = 0

    for b in baris:
        if _bulan(b.get("tanggal")) != bulan:
            continue
        if tahun:
            th = getattr(b.get("tanggal"), "year", None)
            if th and th != tahun:
                continue
        nilai = _num(b.get("totalharga"))
        if not nilai:
            continue
        dipakai += 1
        pemasok = str(b.get("pemasok") or "").strip()
        kat = master.get(_k(pemasok))
        if kat is None:
            tak_terdaftar[pemasok] += nilai
            continue
        per_supplier[(pemasok, kat)] += nilai
        per_kategori[kat] += nilai

    total = sum(per_kategori.values())
    if total <= 0:
        raise CalcError(f"Tidak ada pembelian dari supplier terdaftar pada bulan "
                        f"yang dipilih. Periksa file atau bulan pengajuan.")

    nilai_tertarget = per_kategori.get(TERTARGET, 0.0)
    pct_tertarget = nilai_tertarget / total * 100

    tier_pct = 0.0
    for t in rules["tier"]:
        if pct_tertarget >= t["pct_tertarget_min"]:
            tier_pct = t["insentif_pct"]
            break

    nominal = total * tier_pct / 100
    pencapaian = pct_tertarget / goal_pct * 100 if goal_pct else 0
    pengali = rules["pengali"][-1]["pengali_pct"]
    for p in rules["pengali"]:
        if pencapaian >= p["pencapaian_min"]:
            pengali = p["pengali_pct"]
            break

    rincian = sorted(
        ({"pemasok": n, "kategori": k, "nilai": v,
          "pct": v / total * 100} for (n, k), v in per_supplier.items()),
        key=lambda x: -x["nilai"])

    return {
        "jenis": "purchasing", "bulan": bulan, "tahun": tahun,
        "total_pembelian": round(total),
        "nilai_tertarget": round(nilai_tertarget),
        "nilai_non_tertarget": round(per_kategori.get("NON TERTARGET", 0.0)),
        "pct_tertarget": round(pct_tertarget, 2),
        "goal_pct": goal_pct,
        "tier_pct": tier_pct,
        "nominal_insentif": round(nominal, 2),
        "pencapaian_goal": round(pencapaian, 2),
        "pengali_pct": pengali,
        "total": round(nominal * pengali / 100, 2),
        "rincian": rincian[:40],
        "jumlah_baris": dipakai,
        "supplier_tak_terdaftar": sorted(
            ({"pemasok": n, "nilai": round(v)} for n, v in tak_terdaftar.items()),
            key=lambda x: -x["nilai"]),
        "nilai_tak_terdaftar": round(sum(tak_terdaftar.values())),
    }
