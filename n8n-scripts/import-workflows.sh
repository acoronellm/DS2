#!/bin/bash
set -e

N8N_URL="http://n8n:5678"   # "n8n" es el nombre del contenedor
N8N_USER="admin"
N8N_PASSWORD="admin123"

# esperar a que n8n esté arriba
until curl -s "$N8N_URL/healthz" > /dev/null; do
  echo "Esperando a que n8n arranque..."
  sleep 2
done

# autenticarse y guardar cookie
COOKIE=$(curl -c - -s -X POST "$N8N_URL/rest/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$N8N_USER\",\"password\":\"$N8N_PASSWORD\"}" \
  | grep -o 'n8n-auth.*' | cut -f1)

# importar cada workflow
for f in /workflows/*.json; do
  echo "Importando $f..."
  curl -s -X POST "$N8N_URL/rest/workflows" \
    -H "Cookie: $COOKIE" \
    -H "Content-Type: application/json" \
    --data-binary @"$f"
done

echo "Importación completada!"