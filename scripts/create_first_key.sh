#!/bin/bash
# Crea la primera API key de admin usando el ADMIN_SECRET del .env
# Uso: bash scripts/create_first_key.sh

set -e

# Leer ADMIN_SECRET desde .env
source .env 2>/dev/null || true

API_URL="${API_URL:-http://localhost:80}"

echo "Creando API key de admin..."

RESPONSE=$(curl -s -X POST "$API_URL/v1/keys" \
  -H "Authorization: Bearer $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin-principal", "is_admin": true}')

echo ""
echo "Respuesta:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""
echo "⚠️  Guarda la 'key' en lugar seguro. No se volverá a mostrar."
