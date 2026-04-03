import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.auth.middleware import get_current_key
from app.models.api_key import APIKey
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    ChoiceMessage,
    ModelInfo,
    ModelListResponse,
    UsageInfo,
)
from app.services.metrics import metrics
from app.services.model_router import resolve_model
from app.services.ollama import OllamaError, call_ollama
from app.core.config import get_settings
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    current_key: Annotated[APIKey, Depends(get_current_key)],
) -> ChatCompletionResponse:
    model = resolve_model(request)
    logger.info(
        "Request | key=%s | model_req=%s | model_used=%s | messages=%d",
        current_key.key_prefix,
        request.model,
        model,
        len(request.messages),
    )

    try:
        result = await call_ollama(request, model)
    except OllamaError as exc:
        metrics.record_request(model, 0, error=True)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    metrics.record_request(model, result["duration_seconds"])

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
        object="chat.completion",
        created=int(time.time()),
        model=model,
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content=result["content"]),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
            total_tokens=result["prompt_tokens"] + result["completion_tokens"],
        ),
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    current_key: Annotated[APIKey, Depends(get_current_key)],
) -> ModelListResponse:
    """Lista los modelos disponibles (compatible con OpenAI /v1/models)."""
    created = int(time.time())
    return ModelListResponse(
        data=[
            ModelInfo(id=m, created=created, owned_by="praxis-ia")
            for m in settings.available_models_list
        ]
    )
