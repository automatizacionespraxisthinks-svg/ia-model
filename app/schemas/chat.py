from typing import Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="mistral", description="Modelo a usar")
    messages: list[Message] = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=32768)
    stream: bool = Field(default=False, description="Streaming no soportado aún")

    model_config = {"extra": "ignore"}


class ChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: UsageInfo


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "praxis-ia"


class ModelListResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


# ─── Responses API (OpenAI nueva generación — usada por n8n ≥ 2.6) ────────────

class ResponsesRequest(BaseModel):
    """Formato de la nueva Responses API de OpenAI."""
    model: str = Field(default="mistral")
    input: str | list[dict] = Field(..., description="Texto o lista de mensajes")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=512, ge=1, le=32768)

    model_config = {"extra": "ignore"}


class ResponseOutputContentItem(BaseModel):
    type: str = "output_text"
    text: str


class ResponseOutputItem(BaseModel):
    type: str = "message"
    id: str
    role: str = "assistant"
    content: list[ResponseOutputContentItem]


class ResponsesUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ResponsesResponse(BaseModel):
    id: str
    object: str = "response"
    created_at: int
    model: str
    output: list[ResponseOutputItem]
    usage: ResponsesUsage
