from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.api_keys import validate_api_key
from app.core.config import get_settings
from app.core.database import get_db
from app.models.api_key import APIKey

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="API key inválida o ausente",
    headers={"WWW-Authenticate": "Bearer"},
)

_FORBIDDEN = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Se requieren permisos de administrador",
)


def _extract_raw_key(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise _UNAUTHORIZED
    return credentials.credentials


def get_current_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> APIKey:
    """Dependencia: cualquier key válida."""
    raw_key = _extract_raw_key(credentials)
    record = validate_api_key(db, raw_key)
    if record is None:
        raise _UNAUTHORIZED
    return record


def get_admin_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> APIKey:
    """Dependencia: key válida con permisos de admin."""
    raw_key = _extract_raw_key(credentials)

    # Permitir también el ADMIN_SECRET del .env (bootstrap sin DB)
    if raw_key == settings.admin_secret:
        # Devolvemos un objeto simulado con is_admin=True
        return APIKey(id=0, name="env-admin", key_prefix="env", is_admin=True, is_active=True)

    record = validate_api_key(db, raw_key)
    if record is None:
        raise _UNAUTHORIZED
    if not record.is_admin:
        raise _FORBIDDEN
    return record
