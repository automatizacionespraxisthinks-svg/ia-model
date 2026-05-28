#!/bin/bash
# Descarga los modelos en Ollama al iniciar.
# Ejecutar una sola vez: docker compose exec ollama bash /scripts/pull_models.sh
#
# Modelos:
#   - qwen3.5         (latest = 9b, ~6.6 GB)   modelo principal, prompts medios/largos
#   - granite4.1:3b   (~2.1 GB)                modelo ligero, prompts cortos
#
# Para que la API pueda referirse a "granite4.1" sin tag explícito,
# retageamos la versión 3b como :latest.

set -e

echo "→ Descargando qwen3.5 (latest = 9b)..."
ollama pull qwen3.5
echo "✓ qwen3.5 listo"

echo "→ Descargando granite4.1:3b..."
ollama pull granite4.1:3b
echo "→ Retageando granite4.1:3b como granite4.1:latest..."
ollama cp granite4.1:3b granite4.1:latest
echo "✓ granite4.1 listo"

echo ""
echo "Modelos disponibles:"
ollama list
