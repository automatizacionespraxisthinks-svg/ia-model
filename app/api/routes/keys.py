from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.api_keys import create_api_key, list_api_keys, revoke_api_key
from app.auth.middleware import get_admin_key
from app.core.database import get_db
from app.models.api_key import APIKey
from app.schemas.keys import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyListResponse,
    APIKeyPublic,
    APIKeyRevokeResponse,
)

router = APIRouter()


@router.post(
    "/keys",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva API key",
)
def create_key(
    body: APIKeyCreate,
    db: Session = Depends(get_db),
    admin: Annotated[APIKey, Depends(get_admin_key)] = None,
) -> APIKeyCreated:
    record, full_key = create_api_key(db, name=body.name, is_admin=body.is_admin)
    return APIKeyCreated(
        id=record.id,
        name=record.name,
        key=full_key,
        key_prefix=record.key_prefix,
        is_admin=record.is_admin,
        created_at=record.created_at,
    )


@router.get(
    "/keys",
    response_model=APIKeyListResponse,
    summary="Listar todas las API keys",
)
def get_keys(
    db: Session = Depends(get_db),
    admin: Annotated[APIKey, Depends(get_admin_key)] = None,
) -> APIKeyListResponse:
    keys = list_api_keys(db)
    return APIKeyListResponse(
        keys=[APIKeyPublic.model_validate(k) for k in keys],
        total=len(keys),
    )


@router.delete(
    "/keys/{key_id}",
    response_model=APIKeyRevokeResponse,
    summary="Revocar una API key",
)
def delete_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin: Annotated[APIKey, Depends(get_admin_key)] = None,
) -> APIKeyRevokeResponse:
    record = revoke_api_key(db, key_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Key {key_id} no encontrada")
    return APIKeyRevokeResponse(message="Key revocada exitosamente", id=key_id)
