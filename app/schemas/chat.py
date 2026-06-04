from typing import Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="qwen3.5", description="Modelo a usar")
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
    model: str = Field(default="qwen3.5")
    input: str | list[dict] = Field(..., description="Texto o lista de mensajes")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=512, ge=1, le=32768)

    model_config = {"extra": "ignore"}


class ResponseOutputContentItem(BaseModel):
    type: str = "output_text"
    text: str
    annotations: list = []


class ResponseOutputItem(BaseModel):
    type: str = "message"
    id: str
    status: str = "completed"
    role: str = "assistant"
    content: list[ResponseOutputContentItem]


class ResponsesUsageDetails(BaseModel):
    cached_tokens: int = 0


class ResponsesUsageOutputDetails(BaseModel):
    reasoning_tokens: int = 0


class ResponsesUsage(BaseModel):
    input_tokens: int
    input_tokens_details: ResponsesUsageDetails = ResponsesUsageDetails()
    output_tokens: int
    output_tokens_details: ResponsesUsageOutputDetails = ResponsesUsageOutputDetails()
    total_tokens: int


class ResponsesReasoning(BaseModel):
    effort: str | None = None
    summary: str | None = None


class ResponsesTextFormat(BaseModel):
    type: str = "text"


class ResponsesTextConfig(BaseModel):
    format: ResponsesTextFormat = ResponsesTextFormat()


class ResponsesResponse(BaseModel):
    """
    Alineado al spec de OpenAI Responses API.
    Los campos null/default existen para que el cliente openai-node y LangChain JS
    pasen la validación de schema; sin ellos algunos parsers devuelven {}.
    """
    id: str
    object: str = "response"
    created_at: int
    status: str = "completed"
    error: None = None
    incomplete_details: None = None
    instructions: None = None
    max_output_tokens: int | None = None
    model: str
    output: list[ResponseOutputItem]
    parallel_tool_calls: bool = True
    previous_response_id: None = None
    reasoning: ResponsesReasoning = ResponsesReasoning()
    store: bool = True
    temperature: float = 1.0
    text: ResponsesTextConfig = ResponsesTextConfig()
    tool_choice: str = "auto"
    tools: list = []
    top_p: float = 1.0
    truncation: str = "disabled"
    usage: ResponsesUsage
    user: None = None
    metadata: dict = {}
