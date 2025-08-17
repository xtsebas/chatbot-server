# MCP Server (Python) — Chatbot Server

This repository contains a **Modular Context Protocol (MCP) server** implemented in Python. It exposes one or more tools (see `src/mcp_server/spec.json`) that an MCP **host/chatbot** can call via the MCP JSON‑RPC interface.

> This repo is intentionally separate from the host, as required by the project. Keep this server public and link it from the host’s documentation.

---

## Highlights

- Python MCP server designed to be **spawned by a host over STDIO**.
- Clear separation between **protocol layer** (`server.py`) and **domain logic** (`engine.py`).
- A machine‑readable **spec** (`spec.json`) that documents tools, arguments, and example calls.
- Minimal dependencies; easy to run locally or containerize for remote use.

---

## Repository layout

```
chatbot-server/
├─ src/
│  └─ mcp_server/
│     ├─ __init__.py        # Package marker
│     ├─ engine.py          # Domain logic (pure Python)
│     ├─ server.py          # JSON‑RPC/MCP bridge (STDIO by default)
│     └─ spec.json          # Server/tool specification
├─ pyproject.toml            # Project metadata and dependencies
├─ .gitignore
└─ README.md
```

---

## Requirements

- Python **3.11+**
- A virtual environment tool (`uv` or `python -m venv`)
- No API keys required unless your `engine.py` uses external services

---

## Installation

```bash
git clone <this-repo-url> chatbot-server
cd chatbot-server

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install the package (editable mode for development)
pip install -U pip
pip install -e .
```

If you use `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

---

## Running the server (STDIO)

Most MCP hosts **spawn servers as subprocesses** and communicate via **STDIO**. To run this server directly:

```bash
# Inside the virtual environment
python -m mcp_server.server
```

> Run `python -m mcp_server.server --help` to see any available options (if implemented).

### Integrate with your MCP host

Add an entry to your host’s server registry (example YAML):

```yaml
# mcp_clients.yaml (example used by the host)
servers:
  - name: chatbot-server
    command: ["python", "-m", "mcp_server.server"]
    env: {}
```

Then start your host and request a tool call from this server.

---

## Tools / API surface

The **authoritative list of tools** is in `src/mcp_server/spec.json`. Keep it updated if you add or rename methods.

Typical fields you might include in the spec (illustrative):
```jsonc
{
  "name": "chatbot-server",
  "version": "0.1.0",
  "tools": [
    {
      "name": "do_something",
      "description": "One‑line summary of what it does.",
      "input_schema": {
        "type": "object",
        "properties": { "text": { "type": "string" } },
        "required": ["text"]
      },
      "examples": [
        { "input": { "text": "hello" }, "note": "Returns a processed result" }
      ]
    }
  ]
}
```
> Keep the spec synchronized with your implementation in `engine.py`/`server.py`.

---

## Development notes

- **`engine.py`** should remain free of protocol concerns (pure functions/classes) so it can be unit tested easily.
- **`server.py`** is responsible for:
  - reading requests from STDIO,
  - dispatching to `engine.py`,
  - serializing responses,
  - and handling errors consistently.
- Log at appropriate levels (`INFO` for normal operations, `ERROR` for failures).

### Testing

If you add tests, a typical layout is:

```
tests/
  test_engine.py
  test_server_integration.py
```

Run with:

```bash
pytest -q
```

---

## Remote deployment (optional)

If you need a **remote MCP server**, containerize this repo and expose the entry point. A minimal `Dockerfile` typically:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -U pip && pip install .
COPY src ./src
ENTRYPOINT ["python", "-m", "mcp_server.server"]
```

> If you add a **TCP mode** to `server.py`, document host/port and authentication. Otherwise, keep the default STDIO mode for host‑spawned servers.

---

## Versioning & compatibility

- Bump the version in `pyproject.toml` and `spec.json` when you change tool names or schemas.
- Document breaking changes in the “Changelog” section below.

---

## Changelog

- **0.1.0** — Initial public version (STDIO server, `engine.py`, `spec.json`).

---
