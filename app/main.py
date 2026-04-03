from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.routes import chat, health, keys
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging_config import get_logger, setup_logging

settings = get_settings()
setup_logging()
logger = get_logger(__name__)

# ─── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando %s [%s]", settings.app_name, settings.app_env)
    init_db()
    logger.info("Base de datos inicializada")
    yield
    logger.info("Apagando %s", settings.app_name)


# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Praxis IA Model API",
    description="API de inferencia LLM compatible con OpenAI. Powered by Ollama.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middlewares ───────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Error handlers ────────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validación fallida en %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error("Error inesperado en %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


# ─── Rutas ─────────────────────────────────────────────────────────────────────
app.include_router(health.router)                         # /health, /metrics
app.include_router(chat.router,   prefix="/v1", tags=["chat"])
app.include_router(keys.router,   prefix="/v1", tags=["api-keys"])


@app.get("/", tags=["system"])
def root():
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
