import bcrypt
from fastapi import Request, HTTPException
from app.models import SessionLocal, User

def hash_pw(p):
    return bcrypt.hashpw(p.encode()[:72], bcrypt.gensalt()).decode()

def verify_pw(p, h):
    try:
        return bcrypt.checkpw(p.encode()[:72], h.encode())
    except Exception:
        return False

def current_user(request: Request):
    uid = request.session.get("uid")
    if not uid:
        return None
    db = SessionLocal()
    try:
        return db.query(User).get(uid)
    finally:
        db.close()

def require(request: Request, roles=None):
    u = current_user(request)
    if not u:
        raise HTTPException(status_code=401, detail="Silakan login")
    if roles and u.role not in roles:
        raise HTTPException(status_code=403, detail="Akses ditolak untuk role ini")
    return u
