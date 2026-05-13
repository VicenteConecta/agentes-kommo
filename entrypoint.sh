#!/bin/bash
set -e

# Cloud Run inyecta la variable PORT
# Si no está definida, usar 8080 como default
PORT=${PORT:-8080}

echo "🚀 Iniciando Agentes Kommo en puerto $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
