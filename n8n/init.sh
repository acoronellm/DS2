#!/bin/sh

echo "Iniciando n8n en segundo plano..."
n8n start &

echo "Esperando a que n8n levante..."

while ! wget -qO- http://localhost:5678 >/dev/null 2>&1
do
  sleep 2
done

echo "n8n listo"

echo "Importando workflow..."
n8n import:workflow --input=/workflows/text-flow.json

echo "Importando credenciales..."
n8n import:credentials --input=/credentials.json

echo "Reiniciando n8n en modo principal..."
pkill node

exec n8n start