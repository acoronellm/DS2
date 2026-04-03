#!/bin/sh

echo "Esperando a que n8n esté listo..."
sleep 10

echo "Importando workflow..."
n8n import:workflow --input=/workflows/text-flow.json

echo "Iniciando n8n..."
exec n8n start