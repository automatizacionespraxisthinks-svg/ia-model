# Ejemplos de uso — Praxis IA Model API

## Variables para los ejemplos

```bash
API_URL="http://tu-vps-ip"          # o http://localhost en local
ADMIN_SECRET="change-this-admin-secret"   # del .env
API_KEY="sk-xxxx"                         # obtenida al crear una key
```

---

## 1. Health check

```bash
curl "$API_URL/health"
```

Respuesta esperada:
```json
{
  "status": "ok",
  "api": "ok",
  "ollama": {
    "status": "ok",
    "models": ["mistral:latest", "llama3:latest", "phi3:latest"]
  }
}
```

---

## 2. Crear primera API key (requiere ADMIN_SECRET del .env)

```bash
curl -X POST "$API_URL/v1/keys" \
  -H "Authorization: Bearer $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "mi-primera-key", "is_admin": true}'
```

Respuesta:
```json
{
  "id": 1,
  "name": "mi-primera-key",
  "key": "sk-AbCdEf...",        <-- guarda esto
  "key_prefix": "sk-AbCdEf",
  "is_admin": true,
  "created_at": "2024-01-01T00:00:00"
}
```

---

## 3. Crear una key normal (con key de admin)

```bash
curl -X POST "$API_URL/v1/keys" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "n8n-workflow", "is_admin": false}'
```

---

## 4. Listar keys

```bash
curl "$API_URL/v1/keys" \
  -H "Authorization: Bearer $API_KEY"
```

---

## 5. Chat completion — modelo explícito

```bash
curl -X POST "$API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [
      {"role": "system", "content": "Eres un asistente útil y conciso."},
      {"role": "user", "content": "¿Cuál es la capital de Francia?"}
    ],
    "temperature": 0.7,
    "max_tokens": 200
  }'
```

Respuesta:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "mistral",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "La capital de Francia es París."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

---

## 6. Chat usando alias de OpenAI (auto-mapeo)

```bash
curl -X POST "$API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hola!"}]
  }'
```
> `gpt-3.5-turbo` se mapea automáticamente a `mistral`.

---

## 7. Chat con selección automática de modelo

```bash
curl -X POST "$API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hola"}]
  }'
```
> Prompt corto → elige `phi3` automáticamente.

---

## 8. Listar modelos disponibles

```bash
curl "$API_URL/v1/models" \
  -H "Authorization: Bearer $API_KEY"
```

---

## 9. Métricas

```bash
curl "$API_URL/metrics"
```

---

## 10. Revocar una key

```bash
curl -X DELETE "$API_URL/v1/keys/2" \
  -H "Authorization: Bearer $API_KEY"
```

---

## Configuración en n8n

En n8n, cuando agregues una credencial de **OpenAI**:

| Campo | Valor |
|-------|-------|
| API Key | `sk-tu-key-generada` |
| Base URL | `http://tu-vps-ip/v1` |

Selecciona cualquier modelo listado en `/v1/models` o usa `gpt-3.5-turbo` (se mapea a mistral).
