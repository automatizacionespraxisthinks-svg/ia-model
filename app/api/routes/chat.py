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
    Message,
    ModelInfo,
    ModelListResponse,
    ResponseOutputContentItem,
    ResponseOutputItem,
    ResponsesRequest,
    ResponsesResponse,
    ResponsesUsage,
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


@router.post("/responses", response_model=ResponsesResponse)
async def responses(
    request: ResponsesRequest,
    current_key: Annotated[APIKey, Depends(get_current_key)],
) -> ResponsesResponse:
    """
    Responses API — formato usado por n8n ≥ 2.6 / LangChain JS openai >= 0.4.
    Convierte internamente a ChatCompletion y llama a Ollama.
    """
    # Normalizar input a lista de mensajes
    if isinstance(request.input, str):
        messages = [Message(role="user", content=request.input)]
    else:
        messages = [
            Message(role=m.get("role", "user"), content=m.get("content", ""))
            for m in request.input
        ]

    # Reutilizar la misma lógica de chat
    chat_request = ChatCompletionRequest(
        model=request.model,
        messages=messages,
        temperature=request.temperature,
        max_tokens=request.max_output_tokens,
    )
    model = resolve_model(chat_request)

    logger.info(
        "Responses API | key=%s | model_req=%s | model_used=%s | messages=%d",
        current_key.key_prefix, request.model, model, len(messages),
    )

    try:
        result = await call_ollama(chat_request, model)
    except OllamaError as exc:
        metrics.record_request(model, 0, error=True)
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    metrics.record_request(model, result["duration_seconds"])

    return ResponsesResponse(
        id=f"resp_{uuid.uuid4().hex[:24]}",
        object="response",
        created_at=int(time.time()),
        model=model,
        output=[
            ResponseOutputItem(
                id=f"msg_{uuid.uuid4().hex[:24]}",
                type="message",
                role="assistant",
                content=[ResponseOutputContentItem(type="output_text", text=result["content"])],
            )
        ],
        usage=ResponsesUsage(
            input_tokens=result["prompt_tokens"],
            output_tokens=result["completion_tokens"],
            total_tokens=result["prompt_tokens"] + result["completion_tokens"],
        ),
    )


@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(
    model_id: str,
    current_key: Annotated[APIKey, Depends(get_current_key)],
) -> ModelInfo:
    """
    Devuelve info de un modelo específico.
    n8n/LangChain llama este endpoint para validar que el modelo existe.
    Los alias externos (gpt-3.5-turbo, gpt-4, etc.) también se resuelven aquí.
    """
    from app.services.model_router import MODEL_ALIASES

    # Resolver alias externos al modelo local equivalente
    resolved = MODEL_ALIASES.get(model_id.lower(), model_id)

    # Verificar que el modelo (o su alias resuelto) existe
    if resolved not in settings.available_models_list:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found. Available: {settings.available_models_list}",
        )

    return ModelInfo(id=model_id, created=int(time.time()), owned_by="praxis-ia")
