#!/bin/sh

echo "Esperando n8n..."

while ! wget -qO- http://localhost:5678 >/dev/null 2>&1; do
  sleep 2
done

echo "n8n listo"

echo "Importando workflow..."
n8n import:workflow --input=/workflows/text-flow.json

echo "Importando credenciales..."
n8n import:credentials --input=/credentials.json

echo "Iniciando n8n..."
exec n8n startpor 