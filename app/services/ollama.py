"""
Cliente async para Ollama con reintentos y timeout configurable.
Usa /api/chat (soporta messages nativamente desde Ollama 0.1.14+).
"""
import asyncio
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.schemas.chat import ChatCompletionRequest

logger = get_logger(__name__)
settings = get_settings()


class OllamaError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


async def call_ollama(request: ChatCompletionRequest, model: str) -> dict[str, Any]:
    """
    Llama a Ollama /api/chat y devuelve un dict con:
    {content, prompt_tokens, completion_tokens, duration_seconds}
    """
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens,
        },
    }

    last_error: Exception | None = None

    for attempt in range(1, settings.ollama_max_retries + 1):
        try:
            result = await _do_request(payload, attempt)
            return result
        except OllamaError as exc:
            last_error = exc
            if attempt < settings.ollama_max_retries:
                wait = 2 ** (attempt - 1)  # backoff: 1s, 2s, 4s…
                logger.warning(
                    "Ollama intento %d/%d fallido: %s — esperando %ds",
                    attempt, settings.ollama_max_retries, exc, wait,
                )
                await asyncio.sleep(wait)
            else:
                logger.error("Ollama falló tras %d intentos: %s", attempt, exc)

    raise last_error  # type: ignore[misc]


async def _do_request(payload: dict, attempt: int) -> dict[str, Any]:
    url = f"{settings.ollama_base_url}/api/chat"
    t0 = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout) as client:
            response = await client.post(url, json=payload)
    except httpx.TimeoutException:
        raise OllamaError(f"Timeout al contactar Ollama ({settings.ollama_timeout}s)", 504)
    except httpx.ConnectError:
        raise OllamaError("No se pudo conectar a Ollama. ¿Está corriendo?", 502)

    duration = time.perf_counter() - t0

    if response.status_code != 200:
        raise OllamaError(
            f"Ollama respondió {response.status_code}: {response.text[:300]}",
            502,
        )

    data = response.json()
    message = data.get("message", {})
    content = message.get("content", "")

    # Ollama devuelve estadísticas de tokens si están disponibles
    prompt_tokens = data.get("prompt_eval_count", _estimate_tokens(payload["messages"]))
    completion_tokens = data.get("eval_count", _estimate_tokens_str(content))

    logger.info(
        "Ollama OK | modelo=%s | intento=%d | tokens=%d+%d | %.2fs",
        payload["model"], attempt, prompt_tokens, completion_tokens, duration,
    )

    return {
        "content": content,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "duration_seconds": duration,
    }


def _estimate_tokens(messages: list[dict]) -> int:
    """Estimación burda: ~1 token ≈ 4 chars."""
    total_chars = sum(len(m.get("content", "")) for m in messages)
    return max(1, total_chars // 4)


def _estimate_tokens_str(text: str) -> int:
    return max(1, len(text) // 4)


async def check_ollama_health() -> dict[str, Any]:
    """Verifica conectividad con Ollama y lista los modelos disponibles."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            return {"status": "ok", "models": models}
        return {"status": "error", "detail": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"status": "unreachable", "detail": str(exc)}
