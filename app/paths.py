"""Lokasi berkas, dihitung dari letak paket ini agar tetap benar di server
mana pun (Vercel menjalankan aplikasi dari direktori kerja yang berbeda)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(ROOT, "templates")
STATIC_DIR = os.path.join(ROOT, "static")
DATA_DIR = os.path.join(ROOT, "data")
RULES_PATH = os.path.join(DATA_DIR, "rules.json")
SQLITE_PATH = os.path.join(DATA_DIR, "insentif.db")
