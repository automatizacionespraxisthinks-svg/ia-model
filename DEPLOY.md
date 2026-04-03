# Despliegue en VPS — Praxis IA Model

## Requisitos del VPS

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 vCPU | 8 vCPU |
| RAM | 8 GB | 16 GB |
| Disco | 40 GB | 80 GB SSD |
| OS | Ubuntu 22.04 | Ubuntu 22.04 |
| GPU | — | NVIDIA (para GPU inference) |

---

## Paso 1 — Preparar el servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
```

---

## Paso 2 — Clonar / subir el proyecto

```bash
# Opción A: Git
git clone https://github.com/tu-usuario/praxis-ia-model.git
cd praxis-ia-model

# Opción B: SCP desde tu máquina local
scp -r ./praxis-ia-model user@tu-vps-ip:~/
```

---

## Paso 3 — Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Cambiar obligatoriamente:
- `SECRET_KEY` → string aleatorio de 64 chars (`openssl rand -hex 32`)
- `ADMIN_SECRET` → contraseña segura para bootstrap de keys

```bash
# Generar valores seguros
openssl rand -hex 32   # para SECRET_KEY
openssl rand -hex 20   # para ADMIN_SECRET
```

---

## Paso 4 — Levantar los servicios

```bash
# Build y start
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f api

# Verificar que todo está corriendo
docker compose ps
```

---

## Paso 5 — Descargar modelos en Ollama

```bash
# Descargar modelos (tarda varios minutos por modelo)
docker compose exec ollama ollama pull mistral
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull phi3

# Verificar modelos disponibles
docker compose exec ollama ollama list
```

---

## Paso 6 — Verificar que la API responde

```bash
curl http://localhost/health
```

Debe devolver `"status": "ok"`.

---

## Paso 7 — Crear primera API key

```bash
# Usando el ADMIN_SECRET del .env
source .env
curl -X POST http://localhost/v1/keys \
  -H "Authorization: Bearer $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin-principal", "is_admin": true}'
```

**Guarda la `key` devuelta** — no se puede recuperar.

---

## Paso 8 — Configurar dominio + SSL (opcional pero recomendado)

```bash
# Instalar Certbot
sudo apt install -y certbot

# Obtener certificado (reemplaza con tu dominio)
sudo certbot certonly --standalone -d ai.tu-dominio.com

# Los certificados quedan en:
# /etc/letsencrypt/live/ai.tu-dominio.com/fullchain.pem
# /etc/letsencrypt/live/ai.tu-dominio.com/privkey.pem

# Copiar al directorio de nginx
sudo cp /etc/letsencrypt/live/ai.tu-dominio.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/ai.tu-dominio.com/privkey.pem nginx/ssl/

# Descomentar el bloque HTTPS en nginx/nginx.conf
# y descomentar la redirección HTTP → HTTPS

docker compose restart nginx
```

---

## Mantenimiento

```bash
# Ver logs de un servicio
docker compose logs -f api
docker compose logs -f ollama

# Reiniciar solo la API
docker compose restart api

# Actualizar código (sin perder datos)
git pull
docker compose up -d --build api

# Ver métricas
curl http://localhost/metrics

# Backup de la base de datos
docker compose exec api cat /app/data/praxis.db > backup_$(date +%Y%m%d).db
```

---

## Configurar n8n

En n8n → **Credentials** → **OpenAI API**:

```
API Key:  sk-tu-key-generada
Base URL: http://tu-vps-ip/v1
          (o https://ai.tu-dominio.com/v1 si usas SSL)
```

En cualquier nodo de OpenAI de n8n, selecciona el modelo `mistral`, `llama3`, o `phi3`.
También funciona con `gpt-3.5-turbo` (se mapea a mistral automáticamente).

---

## Arquitectura final

```
Internet
    │
    ▼
[Nginx :80/:443]
    │  reverse proxy + rate limit
    ▼
[FastAPI API :8000]
    │  auth + routing + metrics
    ▼
[Ollama :11434]
    │  LLM inference
    ├─ mistral
    ├─ llama3
    └─ phi3
```
