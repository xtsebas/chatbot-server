# MCP Wordle Coach (Local MCP Server)

Servidor MCP por **stdio** que sugiere jugadas de Wordle vía **JSON-RPC 2.0**.

## Instalar
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

## Ejecutar (stdio JSON-RPC)
mcp-wordle-coach
# o modo demo:
mcp-wordle-coach --demo