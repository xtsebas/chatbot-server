# mcp-personal-trainer

A **Model Context Protocol (MCP)** server over **STDIO** that exposes personal trainer tools:

- `compute_metrics` — BMI and BMR (Mifflin–St Jeor)
- `recommend_exercises` — recommendations by goal/sport
- `build_routine_tool` — weekly routine (sets/reps/timing)
- `recommend_by_metrics_tool` — recommendations using metrics + goal

> The server **does not** speak HTTP; an MCP host invokes it via **STDIO**.

---

## Requirements

- **Python 3.10+**
- `pip` and the `venv` module
- (Optional) API keys if your `planner.py` uses them (e.g., API Ninjas)

---

## Installation

```bash
# 1) Clone the repo
git clone <your-repo>.git
cd <your-repo>

# 2) Create a venv
python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 3) Install dependencies
pip install -U pip
# If you have a requirements.txt in the repo:
pip install -r requirements.txt
# If not, install the basics:
pip install "mcp[cli]>=1.2.0" pydantic httpx python-dotenv
```

Expected minimal files:
```
server.py                     # this MCP server (calls mcp.run())
planner.py                    # implements compute_bmi, build_routine, etc.
```

---

## Run in dev mode (without a host)

Use the MCP CLI to start the server in dev mode:

```bash
mcp dev server.py
```

This launches the process over STDIO and shows helpful logs. Stop with `Ctrl+C`.

---

## Connect to **any** MCP host

Configure your preferred MCP host to run a **STDIO server** with:

- **Command**: `python server.py stdio`
- **Working directory**: the repo folder
- **Environment**: optional (`TRAINER_TOOL_TIMEOUT`, external keys, etc.)

> Each host has its own UI to register MCP servers. Just ensure it executes **that command** in the repo directory.

---

## MCP JSON examples

> All messages use LSP-like framing:
>
> ```
> Content-Length: <N>\r\n
> \r\n
> <JSON>
> ```

### 1) Initialize

```json
{"jsonrpc":"2.0","id":1,"method":"initialize",
 "params":{"capabilities":{},"clientInfo":{"name":"my-host","version":"1.0"}}}
```

### 2) List tools

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

### 3) Call each tool

**compute_metrics**
```json
{"jsonrpc":"2.0","id":3,"method":"tools/call",
 "params":{"name":"compute_metrics",
           "arguments":{"sexo":"male","edad":28,"altura_cm":175,"peso_kg":78}}}
```

**recommend_exercises**
```json
{"jsonrpc":"2.0","id":4,"method":"tools/call",
 "params":{"name":"recommend_exercises",
           "arguments":{"objetivo":"gain muscle mass","deporte":"calisthenics","limite":10}}}
```

**build_routine_tool**
```json
{"jsonrpc":"2.0","id":5,"method":"tools/call",
 "params":{"name":"build_routine_tool",
           "arguments":{"objetivo":"volleyball","dias_por_semana":4,"minutos_por_sesion":60,"experiencia":"intermedio"}}}
```

**recommend_by_metrics_tool**
```json
{"jsonrpc":"2.0","id":6,"method":"tools/call",
 "params":{"name":"recommend_by_metrics_tool",
           "arguments":{"sexo":"male","edad":30,"altura_cm":170,"peso_kg":90,"objetivo":"fat loss","limite":8}}}
```

The server responds with `{"jsonrpc":"2.0","id":<id>,"result":...}` or `{"error":...}`.

---
## Try a MCP remote
**connect to a finance MCP with this url**

```bash
https://finance-mcp.finance-xtsebas74.workers.dev/regla_503020
```

And try the tool for the 50-30-20 rule  
--

## Troubleshooting

- **The process seems unresponsive**  
  Make sure you send messages with the correct framing (`Content-Length` + body) and read exactly that many bytes.

- **Timeouts**  
  Increase `TRAINER_TOOL_TIMEOUT` (per tool). If your host has its own timeout, tune it there too.

- **Missing keys/datasets**  
  If `planner.py` uses external APIs/datasets, define the required env vars or paths.

- **Some tool doesn’t appear in `tools/list`**  
  Ensure `@mcp.tool()` decorates it and `server.py` ends with `mcp.run()`.

---