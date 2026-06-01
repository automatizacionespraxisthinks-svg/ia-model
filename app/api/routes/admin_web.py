import secrets
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=1, max_length=200)


class LoginResponse(BaseModel):
    token: str


@router.get("/admin", include_in_schema=False)
@router.get("/admin/", include_in_schema=False)
def admin_dashboard():
    return FileResponse(WEB_DIR / "dashboard.html")


@router.get("/admin/login", include_in_schema=False)
def admin_login_page():
    return FileResponse(WEB_DIR / "login.html")


@router.post(
    "/admin/api/login",
    response_model=LoginResponse,
    include_in_schema=False,
)
def admin_login(body: LoginRequest) -> LoginResponse:
    user_ok = secrets.compare_digest(body.username, settings.admin_username)
    pass_ok = secrets.compare_digest(body.password, settings.admin_password)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña inválidos",
        )
    return LoginResponse(token=settings.admin_secret)
