"""Generator dokumen Word: isi data, ganti header alamat cabang, sisipkan QR TTD."""
import io, os, re, qrcode

from app.paths import DOC_TEMPLATES_DIR
from docx import Document
from docx.shared import Cm

# Teks bawaan di template yang perlu ditukar dengan data cabang terpilih.
# Ditulis eksplisit agar template Word asli bisa dipakai apa adanya.
TEMPLATE_BRANCH_TEXT = {
    "profit_store_leader.docx": {
        "name": "MFlash – Klender",
        "address": "Jl. Raya Bekasi No.KM.17, RT.2/RW.3, Jatinegara, Kec. Cakung, "
                   "Kota Jakarta Timur, Daerah Khusus Ibukota Jakarta 13930",
    },
    "sales_team.docx": {
        "name": "MFlash Jatiwaringin",
        "address": "Jl. Raya Jatiwaringin No.6, RT.001/RW.9, Jaticempaka, "
                   "Kec. Pd. Gede, Bekasi 17411",
    },
    "purchasing.docx": {
        "name": "Jatiwaringin",
        "address": "Jl. Raya Jatiwaringin No.6, RT.001/RW.9, Jaticempaka, "
                   "Kec. Pd. Gede, Bekasi 17411",
    },
}

BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]


def rupiah(n):
    return "Rp {:,.0f}".format(float(n or 0)).replace(",", ".")


def make_qr(payload, px=6):
    qr = qrcode.QRCode(box_size=px, border=1)
    qr.add_data(payload)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    buf.seek(0)
    return buf


def _iter_paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p
                for it in cell.tables:
                    for r2 in it.rows:
                        for c2 in r2.cells:
                            for p in c2.paragraphs:
                                yield p
    for sec in doc.sections:
        for part in (sec.header, sec.footer, sec.first_page_header,
                     sec.first_page_footer, sec.even_page_header, sec.even_page_footer):
            if part is None:
                continue
            for p in part.paragraphs:
                yield p
            for t in part.tables:
                for row in t.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            yield p


def _replace_in_paragraph(p, mapping):
    """Gabungkan run agar pola yang terpecah tetap ketemu, lalu ganti."""
    full = "".join(r.text for r in p.runs)
    if not full:
        return
    new = full
    for src, dst in mapping.items():
        if src and src in new:
            new = new.replace(src, str(dst))
    if new != full:
        for i, r in enumerate(p.runs):
            r.text = new if i == 0 else ""


def _append_qr(doc, label, buf):
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_picture(buf, width=Cm(2.4))
    p.add_run("\n" + label)


def render(template_path, out_path, mapping, qr_items=None):
    """
    mapping : dict {teks_sumber_atau_{{PLACEHOLDER}} : nilai_baru}
    qr_items: list of (label, payload) -> QR disisipkan pada {{QR_<KEY>}}
              bila ada, jika tidak ditambahkan di akhir dokumen.
    """
    doc = Document(template_path)
    for p in _iter_paragraphs(doc):
        _replace_in_paragraph(p, mapping)

    for label, payload, key in (qr_items or []):
        buf = make_qr(payload)
        target = None
        for p in _iter_paragraphs(doc):
            if "{{QR_%s}}" % key in "".join(r.text for r in p.runs):
                target = p
                break
        if target is not None:
            for r in target.runs:
                r.text = ""
            target.runs[0].add_picture(buf, width=Cm(2.2))
        else:
            _append_qr(doc, label, buf)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    return out_path


def build_mapping(sub, branch, submitter, hasil, base_url):
    """Susun peta penggantian teks untuk satu pengajuan."""
    tpl = os.path.basename(sub_template(sub))
    src = TEMPLATE_BRANCH_TEXT.get(tpl, {})
    periode = f"{BULAN[sub.period_month]} {sub.period_year}"
    m = {}
    if src.get("name"):
        m[src["name"]] = branch.display_name or f"MFlash – {branch.name}"
    if src.get("address"):
        m[src["address"]] = branch.address or ""
    m.update({
        "{{NAMA}}": submitter.full_name,
        "{{JABATAN}}": submitter.position or "Store Leader",
        "{{CABANG}}": branch.name,
        "{{PERIODE}}": periode,
        "{{BULAN}}": BULAN[sub.period_month],
        "{{TAHUN}}": str(sub.period_year),
        "{{TOTAL}}": rupiah(hasil.get("total", sub.total_amount)),
        "{{KODE}}": sub.code,
        "{{KOTA_TANGGAL}}": f"{branch.city or 'Jakarta'}, "
                            f"{sub.created_at.day} {BULAN[sub.created_at.month]} "
                            f"{sub.created_at.year}",
    })
    return m


def sub_template(sub):
    from app.models import TYPES
    return os.path.join(DOC_TEMPLATES_DIR, TYPES[sub.type]["template"])
