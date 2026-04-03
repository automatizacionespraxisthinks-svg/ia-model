import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.api_key import APIKey


# ─── Generación ───────────────────────────────────────────────────────────────

def generate_api_key() -> tuple[str, str, str]:
    """
    Devuelve (full_key, key_prefix, key_hash).
    full_key tiene formato: sk-<48 chars aleatorios>
    """
    raw = secrets.token_urlsafe(36)  # 48 chars base64url
    full_key = f"sk-{raw}"
    key_prefix = full_key[:10]       # "sk-XXXXXXX" — suficiente para identificarla
    key_hash = _hash_key(full_key)
    return full_key, key_prefix, key_hash


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


# ─── Creación ─────────────────────────────────────────────────────────────────

def create_api_key(db: Session, name: str, is_admin: bool = False) -> tuple[APIKey, str]:
    """
    Crea y persiste una nueva API key.
    Devuelve (registro_db, full_key).
    """
    full_key, key_prefix, key_hash = generate_api_key()
    record = APIKey(
        name=name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_admin=is_admin,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, full_key


# ─── Validación ───────────────────────────────────────────────────────────────

def validate_api_key(db: Session, raw_key: str) -> APIKey | None:
    """
    Valida la key. Si es válida, actualiza el timestamp y contador.
    Devuelve el registro o None.
    """
    key_hash = _hash_key(raw_key)
    record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active.is_(True),
    ).first()

    if record:
        record.last_used_at = datetime.now(timezone.utc)
        record.request_count += 1
        db.commit()

    return record


# ─── Listado / revocación ─────────────────────────────────────────────────────

def list_api_keys(db: Session) -> list[APIKey]:
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()


def revoke_api_key(db: Session, key_id: int) -> APIKey | None:
    record = db.query(APIKey).filter(APIKey.id == key_id).first()
    if record:
        record.is_active = False
        db.commit()
        db.refresh(record)
    return record
