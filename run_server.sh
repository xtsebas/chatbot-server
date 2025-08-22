#!/usr/bin/env bash
set -e

echo "== MCP Wordle Coach server =="

# 1. Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
  echo "-- Creando entorno virtual..."
  python3 -m venv .venv
fi

# 2. Activar entorno
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
else
  echo "No se pudo encontrar activate en .venv"
  exit 1
fi

# 3. Instalar dependencias del proyecto
echo "-- Instalando paquete en modo editable..."
pip install -U pip
pip install -e . pytest

# 4. Correr pruebas unitarias
# echo "-- Ejecutando tests..."
# pytest -q || { echo "Tests fallaron"; exit 1; }

# 5. Ejecutar server
if [ "$1" = "--demo" ]; then
  echo "-- Corriendo en modo demo (CLI interactiva)..."
  python -m mcp_server.server --demo
else
  echo "-- Corriendo en modo stdio (para conectar host)..."
  python -m mcp_server.server
fi
