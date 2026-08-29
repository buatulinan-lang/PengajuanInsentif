from datetime import datetime
import os
from sqlalchemy import (create_engine, Column, Integer, String, Text, DateTime,
                        Float, ForeignKey, Boolean, LargeBinary)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

# Render menyediakan DATABASE_URL untuk Postgres. Tanpa itu, jatuh ke SQLite lokal.
from app.paths import SQLITE_PATH

DB_URL = os.environ.get("DATABASE_URL", f"sqlite:///{SQLITE_PATH}")
if DB_URL.startswith("postgres://"):          # format lama dari Render
    DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DB_URL.startswith("postgresql://"):
    DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

if DB_URL.startswith("sqlite"):
    _kw = {"connect_args": {"check_same_thread": False}}
elif ":6543/" in DB_URL:
    # Supabase transaction pooler: jangan pakai connection pool milik SQLAlchemy
    from sqlalchemy.pool import NullPool
    _kw = {"poolclass": NullPool}
else:
    # koneksi langsung / session pooler (port 5432)
    _kw = {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 5,
           "pool_recycle": 300}
ENGINE = create_engine(DB_URL, **_kw)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False)

# ---- Roles -------------------------------------------------------------
ROLE_SL      = "store_leader"
ROLE_ARM     = "arm"          # Area / Regional Manager
ROLE_CEO     = "ceo"
ROLE_FINANCE = "finance"
ROLE_ADMIN   = "admin"
ROLE_LABELS = {
    ROLE_SL: "Store Leader", ROLE_ARM: "Area Regional Manager",
    ROLE_CEO: "CEO", ROLE_FINANCE: "Finance", ROLE_ADMIN: "Administrator",
}

# ---- Workflow ----------------------------------------------------------
ST_DRAFT      = "draft"
ST_WAIT_ARM   = "menunggu_arm"
ST_WAIT_CEO   = "menunggu_ceo"
ST_WAIT_FIN   = "menunggu_finance"
ST_DONE       = "done"
ST_REJECTED   = "ditolak"
STATUS_FLOW = [ST_WAIT_ARM, ST_WAIT_CEO, ST_WAIT_FIN, ST_DONE]
STATUS_LABELS = {
    ST_DRAFT: "Draft", ST_WAIT_ARM: "Proses Approval ARM",
    ST_WAIT_CEO: "Proses Approval CEO", ST_WAIT_FIN: "Proses Pencairan Finance",
    ST_DONE: "Done", ST_REJECTED: "Ditolak",
}
# role yang berwenang bertindak pada tiap status
ACTOR_OF_STATUS = {ST_WAIT_ARM: ROLE_ARM, ST_WAIT_CEO: ROLE_CEO, ST_WAIT_FIN: ROLE_FINANCE}

# ---- Jenis pengajuan ---------------------------------------------------
TYPES = {
    "profit_sl":  {"label": "Insentif Profit Store Leader", "template": "profit_store_leader.docx"},
    "sales_team": {"label": "Insentif Sales & Team",        "template": "sales_team.docx"},
    "purchasing": {"label": "Insentif Purchasing",          "template": "purchasing.docx"},
}


class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # mis. "Klender"
    display_name = Column(String)                        # mis. "MFlash – Klender"
    address = Column(Text)                               # dipakai di header Word
    city = Column(String, default="Jakarta")             # untuk "Jakarta, 6 Agustus 2026"
    active = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    position = Column(String)                # jabatan yang tercetak di TTD
    role = Column(String, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    active = Column(Boolean, default=True)
    branch = relationship("Branch")


class Sales(Base):
    """Master anggota sales per cabang (untuk Insentif Sales & Team)."""
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)          # persis seperti di data faktur
    branch_id = Column(Integer, ForeignKey("branches.id"))
    status_karyawan = Column(String, default="TEAM INTI")
    aliases = Column(Text, default="")   # ejaan lain di data, dipisah koma
    active = Column(Boolean, default=True)
    branch = relationship("Branch")


class Supplier(Base):
    """Master kategori supplier (untuk Insentif Purchasing)."""
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    kategori = Column(String, default="NON TERTARGET")   # TERTARGET / NON TERTARGET


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)       # nomor dokumen
    type = Column(String, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"))
    submitter_id = Column(Integer, ForeignKey("users.id"))
    period_month = Column(Integer)
    period_year = Column(Integer)
    total_amount = Column(Float, default=0)
    status = Column(String, default=ST_DRAFT)
    data_json = Column(Text, default="{}")               # hasil perhitungan
    excel_name = Column(String)
    excel_blob = Column(LargeBinary)      # disimpan di DB, bukan disk (Render tanpa disk permanen)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch = relationship("Branch")
    submitter = relationship("User")
    approvals = relationship("Approval", back_populates="submission",
                             order_by="Approval.id", cascade="all, delete-orphan")
    attachments = relationship("Attachment", cascade="all, delete-orphan")


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    action = Column(String)          # approve / reject / submit / cair
    note = Column(Text)
    qr_token = Column(String, unique=True, index=True)   # untuk QR tanda tangan
    created_at = Column(DateTime, default=datetime.utcnow)
    submission = relationship("Submission", back_populates="approvals")
    user = relationship("User")


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    kind = Column(String)            # screenshot / excel / lain
    filename = Column(String)
    mime = Column(String, default="application/octet-stream")
    blob = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(ENGINE)
