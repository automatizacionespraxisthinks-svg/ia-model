#!/bin/bash
# Descarga los modelos en Ollama al iniciar.
# Ejecutar una sola vez: docker compose exec ollama bash /scripts/pull_models.sh

set -e

MODELS=("mistral" "llama3" "phi3")

for model in "${MODELS[@]}"; do
    echo "→ Descargando $model..."
    ollama pull "$model"
    echo "✓ $model listo"
done

echo ""
echo "Modelos disponibles:"
ollama list
