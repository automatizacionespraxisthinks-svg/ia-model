"""
Router de modelos: selecciona el modelo adecuado según el request.
"""
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.schemas.chat import ChatCompletionRequest

logger = get_logger(__name__)

# Mapeo de modelos externos a modelos locales
MODEL_ALIASES: dict[str, str] = {
    # OpenAI
    "gpt-4": "llama3",
    "gpt-4-turbo": "llama3",
    "gpt-4o": "llama3",
    "gpt-3.5-turbo": "mistral",
    "gpt-3.5-turbo-16k": "mistral",
    # Google
    "gemini-pro": "mistral",
    "gemini-1.5-pro": "llama3",
    # Anthropic
    "claude-3-opus": "llama3",
    "claude-3-sonnet": "mistral",
    "claude-3-haiku": "phi3",
}


def resolve_model(request: ChatCompletionRequest) -> str:
    """
    Determina el modelo local a usar:
    1. Si el modelo pedido es un alias conocido → mapearlo.
    2. Si el modelo pedido está en la lista de disponibles → usarlo.
    3. Si el modelo es 'auto' o vacío → elegir automáticamente por longitud.
    4. Fallback al modelo por defecto.
    """
    settings = get_settings()
    available = settings.available_models_list
    requested = request.model.strip().lower()

    # 1. Alias de API externas
    if requested in MODEL_ALIASES:
        resolved = MODEL_ALIASES[requested]
        logger.info("Alias '%s' → modelo local '%s'", requested, resolved)
        return resolved

    # 2. Modelo local explícito
    if requested in available:
        return requested

    # 3. Selección automática por complejidad del prompt
    if requested in ("auto", ""):
        return _auto_select(request, settings)

    # 4. Fallback
    logger.warning("Modelo '%s' no encontrado, usando default '%s'", requested, settings.default_model)
    return settings.default_model


def _auto_select(request: ChatCompletionRequest, settings) -> str:
    """Elige modelo según longitud total del prompt (proxy de complejidad)."""
    total_chars = sum(len(m.content) for m in request.messages)

    if total_chars < settings.router_light_threshold:
        model = settings.router_light_model
        tier = "light"
    elif total_chars < settings.router_medium_threshold:
        model = settings.router_medium_model
        tier = "medium"
    else:
        model = settings.router_heavy_model
        tier = "heavy"

    logger.info(
        "Auto-router: %d chars → tier=%s → modelo='%s'", total_chars, tier, model
    )
    return model
