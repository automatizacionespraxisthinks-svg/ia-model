# Praxis IA Model API

API de inferencia LLM autoalojada, compatible al 100% con el formato OpenAI.
Conecta herramientas como **n8n**, **LangChain** o cualquier cliente OpenAI a modelos locales corriendo en **Ollama**, sin depender de servicios externos ni pagar por token.

---

## Índice

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Inicio rápido](#inicio-rápido)
- [Variables de entorno](#variables-de-entorno)
- [API Reference](#api-reference)
- [Sistema de API Keys](#sistema-de-api-keys)
- [Router de modelos](#router-de-modelos)
- [Integración con n8n](#integración-con-n8n)
- [Seguridad](#seguridad)
- [Despliegue en VPS](#despliegue-en-vps)
- [Estructura del proyecto](#estructura-del-proyecto)

---

## Características

- **Compatible con OpenAI** — mismos endpoints y formato de respuesta; sin cambiar el cliente
- **API Keys propias** — generación, listado y revocación con formato `sk-...`
- **Router automático de modelos** — elige el modelo según longitud/complejidad del prompt
- **Alias de modelos externos** — `gpt-3.5-turbo`, `gpt-4`, `gemini-pro`, etc. se mapean automáticamente a modelos locales
- **Reintentos con backoff** — tolerancia a fallos de Ollama
- **Rate limiting** — doble capa: Nginx + SlowAPI
- **Métricas en tiempo real** — latencia, requests por modelo, tasa de error
- **Docker Compose** — despliegue en un solo comando
- **Listo para escalar** — reemplaza Ollama por vLLM cambiando una variable

---

## Arquitectura

```
                    ┌─────────────────────────────────────┐
  Clientes          │              VPS / Servidor           │
  ────────          │                                       │
  n8n               │   ┌─────────┐      ┌─────────────┐  │
  curl         ───► │   │  Nginx  │ ───► │  FastAPI    │  │
  LangChain         │   │ :80/443 │      │  :8000      │  │
  OpenAI SDK        │   └─────────┘      └──────┬──────┘  │
                    │    Rate limit             │          │
                    │    SSL termination        │ Auth     │
                    │    Reverse proxy          │ Routing  │
                    │                           │ Metrics  │
                    │                    ┌──────▼──────┐   │
                    │                    │   Ollama    │   │
                    │                    │   :11434    │   │
                    │                    │  (interno)  │   │
                    │                    ├─────────────┤   │
                    │                    │  mistral    │   │
                    │                    │  llama3     │   │
                    │                    │  phi3       │   │
                    │                    └─────────────┘   │
                    └─────────────────────────────────────┘
```

> **Ollama y la API nunca quedan expuestos directamente a internet.** Todo el tráfico entra por Nginx.

---

## Requisitos

### Para desarrollo local

- Docker Desktop
- Docker Compose v2

### Para producción (VPS)

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Disco | 40 GB | 80 GB SSD |
| OS | Ubuntu 22.04 | Ubuntu 22.04 |
| GPU | — | NVIDIA (inferencia más rápida) |

---

## Inicio rápido

### 1. Clonar y configurar

```bash
git clone https://github.com/tu-usuario/praxis-ia-model.git
cd praxis-ia-model

# Copiar y editar el archivo de entorno
cp .env.example .env
```

Editar `.env` — cambiar **obligatoriamente**:

```ini
SECRET_KEY=<genera con: openssl rand -hex 32>
ADMIN_SECRET=<tu-contrasena-segura-de-admin>
```

### 2. Levantar los servicios

```bash
docker compose up -d --build
```

### 3. Descargar los modelos (una sola vez)

```bash
docker compose exec ollama ollama pull mistral
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull phi3
```

> `mistral` pesa ~4 GB, `llama3` ~4.7 GB, `phi3` ~2.3 GB.
> Solo necesitas descargar los que vayas a usar.

### 4. Verificar

```bash
curl http://localhost/health
```

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

### 5. Crear tu primera API key

```bash
# Usa el ADMIN_SECRET de tu .env para el bootstrap inicial
curl -X POST http://localhost/v1/keys \
  -H "Authorization: Bearer TU_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "mi-primera-key", "is_admin": true}'
```

```json
{
  "id": 1,
  "name": "mi-primera-key",
  "key": "sk-AbCdEfGh...",
  "key_prefix": "sk-AbCdEf",
  "is_admin": true,
  "created_at": "2024-01-01T00:00:00"
}
```

> **Guarda la `key` en lugar seguro. No se vuelve a mostrar.**

### 6. Hacer tu primera llamada

```bash
curl -X POST http://localhost/v1/chat/completions \
  -H "Authorization: Bearer sk-AbCdEfGh..." \
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

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | *(requerida)* | Clave secreta de la app |
| `ADMIN_SECRET` | *(requerida)* | Contraseña de bootstrap para crear la primera key |
| `DATABASE_URL` | `sqlite:///./data/praxis.db` | URL de la base de datos |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL interna de Ollama |
| `OLLAMA_TIMEOUT` | `120` | Timeout en segundos por request a Ollama |
| `OLLAMA_MAX_RETRIES` | `3` | Intentos máximos ante fallo de Ollama |
| `AVAILABLE_MODELS` | `mistral,llama3,phi3` | Modelos habilitados (separados por coma) |
| `DEFAULT_MODEL` | `mistral` | Modelo por defecto |
| `ROUTER_LIGHT_THRESHOLD` | `500` | Chars para tier ligero (→ phi3) |
| `ROUTER_MEDIUM_THRESHOLD` | `2000` | Chars para tier medio (→ mistral) |
| `ROUTER_LIGHT_MODEL` | `phi3` | Modelo para prompts cortos |
| `ROUTER_MEDIUM_MODEL` | `mistral` | Modelo para prompts medianos |
| `ROUTER_HEAVY_MODEL` | `llama3` | Modelo para prompts largos |
| `RATE_LIMIT_PER_MINUTE` | `60` | Requests por minuto por IP |
| `DEBUG` | `false` | Activa logs detallados |

---

## API Reference

### Sistema

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `GET` | `/` | No | Info del servicio |
| `GET` | `/health` | No | Estado de API y Ollama |
| `GET` | `/metrics` | No | Métricas en tiempo real |
| `GET` | `/docs` | No | Swagger UI interactivo |

### Chat (compatible OpenAI)

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `POST` | `/v1/chat/completions` | Key válida | Generar respuesta del modelo |
| `GET` | `/v1/models` | Key válida | Listar modelos disponibles |

### API Keys

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| `POST` | `/v1/keys` | Admin | Crear nueva key |
| `GET` | `/v1/keys` | Admin | Listar todas las keys |
| `DELETE` | `/v1/keys/{id}` | Admin | Revocar una key |

---

### POST /v1/chat/completions

**Request:**

```json
{
  "model": "mistral",
  "messages": [
    {"role": "system", "content": "Eres un asistente útil."},
    {"role": "user", "content": "Explica qué es Docker en 2 líneas."}
  ],
  "temperature": 0.7,
  "max_tokens": 300
}
```

**Response:**

```json
{
  "id": "chatcmpl-a1b2c3d4e5f6",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "mistral",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Docker es una plataforma de contenedores que empaqueta aplicaciones con todas sus dependencias para garantizar su ejecución en cualquier entorno de forma consistente y aislada."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 42,
    "total_tokens": 70
  }
}
```

---

## Sistema de API Keys

Las keys se generan con criptografía segura y se almacenan **hasheadas con SHA-256**. El secreto original solo se devuelve una vez al momento de creación.

### Ciclo de vida

```
POST /v1/keys  →  se genera sk-xxxxx  →  se hashea y guarda en DB
                        │
                        └─ se devuelve la key completa (única vez)

Cada request  →  Bearer sk-xxxxx  →  SHA-256(key) → lookup en DB → ✓/✗
```

### Crear key normal (para usuarios o n8n)

```bash
curl -X POST http://localhost/v1/keys \
  -H "Authorization: Bearer $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "n8n-produccion", "is_admin": false}'
```

### Listar keys

```bash
curl http://localhost/v1/keys \
  -H "Authorization: Bearer $ADMIN_KEY"
```

### Revocar una key

```bash
curl -X DELETE http://localhost/v1/keys/3 \
  -H "Authorization: Bearer $ADMIN_KEY"
```

---

## Router de modelos

El router resuelve qué modelo local usar en este orden de prioridad:

```
1. ¿Es un alias de API externa? (gpt-4, gemini-pro…) → mapear al local equivalente
2. ¿Es el nombre exacto de un modelo local?           → usarlo directamente
3. ¿Es "auto" o vacío?                                → elegir por longitud de prompt
4. Fallback                                           → DEFAULT_MODEL
```

### Tabla de alias

| Modelo solicitado | Modelo local usado |
|-------------------|--------------------|
| `gpt-4`, `gpt-4-turbo`, `gpt-4o` | `llama3` |
| `gpt-3.5-turbo`, `gpt-3.5-turbo-16k` | `mistral` |
| `gemini-pro` | `mistral` |
| `gemini-1.5-pro` | `llama3` |
| `claude-3-opus` | `llama3` |
| `claude-3-sonnet` | `mistral` |
| `claude-3-haiku` | `phi3` |

### Selección automática (`"model": "auto"`)

| Longitud total del prompt | Modelo elegido |
|---------------------------|----------------|
| < 500 chars | `phi3` (rápido, ligero) |
| 500 – 2000 chars | `mistral` (equilibrado) |
| > 2000 chars | `llama3` (máxima capacidad) |

Los umbrales son configurables en `.env`.

---

## Integración con n8n

### Configurar credencial OpenAI en n8n

1. Ir a **Settings → Credentials → New Credential → OpenAI API**
2. Completar:

   | Campo | Valor |
   |-------|-------|
   | **API Key** | `sk-tu-key-generada` |
   | **Base URL** | `http://tu-vps-ip/v1` |

3. Guardar y usar en cualquier nodo **OpenAI Chat Model** o **OpenAI**

### Modelos recomendados en n8n

Usar cualquiera de los listados en `/v1/models`, o los alias de OpenAI — todos funcionan:

- `mistral` — mejor equilibrio velocidad/calidad
- `llama3` — mayor capacidad de razonamiento
- `phi3` — el más rápido, ideal para tareas simples
- `gpt-3.5-turbo` — se mapea a `mistral` automáticamente

---

## Seguridad

### Capas de protección

```
[Internet] → [Nginx: SSL + rate limit 30r/min] → [FastAPI: auth + rate limit 60r/min] → [Ollama: solo interno]
```

| Capa | Mecanismo |
|------|-----------|
| **Red** | Ollama y API no expuestos directamente (solo Nginx) |
| **Autenticación** | Bearer token (`sk-...`) validado en cada request |
| **Almacenamiento** | Keys guardadas como SHA-256, nunca en texto plano |
| **Rate limiting** | 30 req/min (Nginx) + 60 req/min por IP (SlowAPI) |
| **Validación** | Pydantic valida todos los inputs antes de procesarlos |
| **Headers** | `X-Content-Type-Options`, `X-Frame-Options`, `server_tokens off` |
| **Usuario** | La API corre como usuario no-root dentro del contenedor |

### Recomendaciones para producción

- Activar HTTPS en `nginx/nginx.conf` (bloque comentado listo para usar)
- Rotar `ADMIN_SECRET` y `SECRET_KEY` regularmente
- Monitorear `/metrics` para detectar anomalías de uso
- Usar un volumen externo para backups de la base de datos SQLite

---

## Despliegue en VPS

### Instalación de Docker (Ubuntu 22.04)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

### Despliegue completo

```bash
# 1. Subir el proyecto
git clone https://github.com/tu-usuario/praxis-ia-model.git
cd praxis-ia-model

# 2. Configurar entorno
cp .env.example .env
nano .env   # cambiar SECRET_KEY y ADMIN_SECRET

# 3. Levantar
docker compose up -d --build

# 4. Descargar modelos
docker compose exec ollama ollama pull mistral
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull phi3

# 5. Crear primera key
source .env
curl -X POST http://localhost/v1/keys \
  -H "Authorization: Bearer $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin", "is_admin": true}'
```

### Habilitar SSL con Let's Encrypt

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d ai.tu-dominio.com

mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/ai.tu-dominio.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/ai.tu-dominio.com/privkey.pem nginx/ssl/

# Descomentar bloque HTTPS en nginx/nginx.conf
docker compose restart nginx
```

### Comandos de mantenimiento

```bash
# Ver logs en vivo
docker compose logs -f api

# Reiniciar solo la API (sin afectar modelos descargados)
docker compose restart api

# Actualizar código
git pull && docker compose up -d --build api

# Ver métricas
curl http://localhost/metrics

# Backup de la base de datos
docker compose cp api:/app/data/praxis.db ./backup_$(date +%Y%m%d).db

# Ver modelos disponibles en Ollama
docker compose exec ollama ollama list
```

---

## Estructura del proyecto

```
praxis-ia-model/
│
├── app/
│   ├── main.py                    # Entry point: FastAPI, middlewares, rutas
│   │
│   ├── core/
│   │   ├── config.py              # Settings centralizados (pydantic-settings)
│   │   ├── database.py            # SQLAlchemy engine + sesiones + init_db
│   │   └── logging_config.py      # Logging estructurado a stdout
│   │
│   ├── models/
│   │   └── api_key.py             # Modelo ORM: tabla api_keys
│   │
│   ├── schemas/
│   │   ├── chat.py                # Request/Response compatible OpenAI
│   │   └── keys.py                # Schemas de gestión de API keys
│   │
│   ├── auth/
│   │   ├── api_keys.py            # Generación SHA-256, validación, CRUD
│   │   └── middleware.py          # FastAPI dependencies: get_current_key / get_admin_key
│   │
│   ├── services/
│   │   ├── ollama.py              # Cliente async con timeout y reintentos
│   │   ├── model_router.py        # Alias + selección automática de modelo
│   │   └── metrics.py             # Métricas en memoria (thread-safe)
│   │
│   └── api/routes/
│       ├── chat.py                # POST /v1/chat/completions, GET /v1/models
│       ├── keys.py                # POST/GET/DELETE /v1/keys
│       └── health.py              # GET /health, GET /metrics
│
├── nginx/
│   └── nginx.conf                 # Reverse proxy + rate limiting + SSL ready
│
├── scripts/
│   ├── pull_models.sh             # Descarga todos los modelos de Ollama
│   └── create_first_key.sh        # Script de bootstrap de la primera key
│
├── Dockerfile                     # Imagen Python 3.11 slim, usuario no-root
├── docker-compose.yml             # Servicios: api + ollama + nginx
├── requirements.txt               # Dependencias Python
├── .env.example                   # Plantilla de configuración
├── EXAMPLES.md                    # Ejemplos detallados de uso con curl
└── DEPLOY.md                      # Guía paso a paso de despliegue en VPS
```

---

## Stack tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Framework | FastAPI | 0.111 |
| Servidor ASGI | Uvicorn | 0.29 |
| Motor LLM | Ollama | latest |
| Base de datos | SQLite / SQLAlchemy | 2.0 |
| HTTP cliente | httpx (async) | 0.27 |
| Rate limiting | SlowAPI | 0.1.9 |
| Validación | Pydantic v2 | 2.7 |
| Reverse proxy | Nginx | 1.25 |
| Contenedores | Docker + Compose | v2 |

---

## Licencia

MIT — libre para uso personal y comercial.
