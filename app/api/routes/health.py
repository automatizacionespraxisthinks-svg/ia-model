from fastapi import APIRouter
from app.services.ollama import check_ollama_health
from app.services.metrics import metrics

router = APIRouter()


@router.get("/health", tags=["system"])
async def health_check() -> dict:
    ollama = await check_ollama_health()
    return {
        "status": "ok" if ollama["status"] == "ok" else "degraded",
        "api": "ok",
        "ollama": ollama,
    }


@router.get("/metrics", tags=["system"])
async def get_metrics() -> dict:
    return metrics.snapshot()
