from datetime import datetime
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Nombre descriptivo de la key")
    is_admin: bool = Field(False, description="Si True, la key puede gestionar otras keys")


class APIKeyCreated(BaseModel):
    """Respuesta al crear una key — la única vez que se devuelve la clave completa."""
    id: int
    name: str
    key: str = Field(..., description="Guárdala en lugar seguro, no se volverá a mostrar")
    key_prefix: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyPublic(BaseModel):
    """Vista pública de una key (sin el secreto)."""
    id: int
    name: str
    key_prefix: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_used_at: datetime | None
    request_count: int

    model_config = {"from_attributes": True}


class APIKeyListResponse(BaseModel):
    keys: list[APIKeyPublic]
    total: int


class APIKeyRevokeResponse(BaseModel):
    message: str
    id: int
