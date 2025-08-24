from __future__ import annotations
import argparse
import json
import os
import sys
from typing import Dict, Tuple, List, Optional
from importlib.resources import files

from .engine import (
    pattern_for_guess,
    apply_feedback_to_candidates,
    pattern_distribution,
    entropy_bits,
    suggest_move,
)

VERSION = "0.1.0"
WORDS_PATH = os.path.join(os.path.dirname(__file__), "words.txt")

def load_words():
    txt = files("mcp_server").joinpath("words.txt").read_text(encoding="utf-8")
    return [w.strip() for w in txt.splitlines() if w.strip()]

ALL_WORDS = load_words()

# -------------------- JSON-RPC helpers --------------------
def jsonrpc_ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def jsonrpc_error(id_, code, message):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}

# -------------------- MCP "tools" descriptors --------------------
def tools_descriptor():
    return {
        "tools": [
            {
                "name": "suggest_move",
                "description": "Sugerir mejor jugada por entropia",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": ["object", "null"],
                            "description": "Estado opcional con candidatos y/o historial."
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "apply_feedback",
                "description": "Aplicar feedback G/Y/K para filtrar candidatos",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "guess": {"type": "string"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["guess", "feedback"]
                }
            },
            {
                "name": "explain",
                "description": "Explicar entropia y distribucion de patrones para un guess",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "guess": {"type": "string"}
                    },
                    "required": ["guess"]
                }
            },
            {
                "name": "reset",
                "description": "Reinicia el estado del servidor",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ],
        "nextCursor": None
    }

# -------------------- Core handler --------------------
def handle_request(req: dict, state: dict) -> Tuple[dict, dict]:
    """
    state: {
      "candidates": List[str],
      "history": List[{"guess":..., "feedback":...}]
    }
    """
    mid = req.get("id")
    method = req.get("method")
    params = req.get("params") or {}

    state.setdefault("candidates", ALL_WORDS.copy())
    state.setdefault("history", [])

    try:
        # ---- Handshake MCP ----
        if method == "initialize":
            return jsonrpc_ok(mid, {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "mcp-wordle-coach", "version": VERSION},
                "capabilities": {"tools": {}}
            }), state

        if method == "tools/list":
            return jsonrpc_ok(mid, tools_descriptor()), state

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            return tools_call_router(mid, name, arguments, state)

        # ---- Métodos directos (comodidad para pruebas) ----
        if method == "suggest_move":
            pstate = params.get("state") or state
            cands = pstate.get("candidates", state["candidates"])
            return jsonrpc_ok(mid, suggest_move(cands)), state

        if method == "apply_feedback":
            guess = (params.get("guess") or "").strip().lower()
            feedback = (params.get("feedback") or "").strip().upper()
            if len(guess) != 5 or len(feedback) != 5 or any(ch not in "GYK" for ch in feedback):
                return jsonrpc_error(mid, -32602, "guess=5 letras, feedback=5 de G/Y/K"), state
            new_cands = apply_feedback_to_candidates(state["candidates"], guess, feedback)
            state["candidates"] = new_cands
            state["history"].append({"guess": guess.upper(), "feedback": feedback})
            return jsonrpc_ok(mid, {
                "candidates": len(new_cands),
                "sample": [w.upper() for w in new_cands[:10]],
                "constraints_applied": [{"guess": guess.upper(), "feedback": feedback}]
            }), state

        if method == "explain":
            guess = (params.get("guess") or "").strip().lower()
            if len(guess) != 5:
                return jsonrpc_error(mid, -32602, "guess=5 letras"), state
            dist = pattern_distribution(guess, state["candidates"])
            H = entropy_bits(dist)
            total = sum(dist.values()) or 1
            return jsonrpc_ok(mid, {
                "guess": guess.upper(),
                "info": {
                    "pattern_distribution": {k: v/total for k, v in dist.items()},
                    "expected_information_bits": round(H, 3)
                },
                "rationale": "Cubre letras frecuentes; distribucion de patrones relativamente uniforme."
            }), state

        if method == "reset":
            state["candidates"] = ALL_WORDS.copy()
            state["history"] = []
            return jsonrpc_ok(mid, {"candidates": len(state["candidates"])}), state

        return jsonrpc_error(mid, -32601, "Method not found"), state

    except Exception as e:
        return jsonrpc_error(mid, -32603, f"Internal error: {e}"), state

def tools_call_router(mid, name: str, args: dict, state: dict) -> Tuple[dict, dict]:
    """
    Implementacion de tools/call al estilo MCP:
    retorno: { content: [ {type:'text', text:...}, {type:'json', json:{...}} ] }
    """
    if name == "suggest_move":
        pstate = args.get("state") or state
        cands = pstate.get("candidates", state["candidates"])
        sug = suggest_move(cands)
        return jsonrpc_ok(mid, {
            "content": [
                {"type": "text", "text": f"Sugerencia: {sug['guess']} | H~{sug['expected_information_bits']} | poda~{sug['estimated_pruning']}"},
                {"type": "json", "json": sug}
            ]
        }), state

    if name == "apply_feedback":
        guess = (args.get("guess") or "").strip().lower()
        feedback = (args.get("feedback") or "").strip().upper()
        if len(guess) != 5 or len(feedback) != 5 or any(ch not in "GYK" for ch in feedback):
            return jsonrpc_error(mid, -32602, "guess=5 letras, feedback=5 de G/Y/K"), state
        new_cands = apply_feedback_to_candidates(state["candidates"], guess, feedback)
        state["candidates"] = new_cands
        state["history"].append({"guess": guess.upper(), "feedback": feedback})
        payload = {
            "candidates": len(new_cands),
            "sample": [w.upper() for w in new_cands[:10]],
            "constraints_applied": [{"guess": guess.upper(), "feedback": feedback}]
        }
        return jsonrpc_ok(mid, {
            "content": [
                {"type": "text", "text": f"Quedan {payload['candidates']} candidatos."},
                {"type": "json", "json": payload}
            ]
        }), state

    if name == "explain":
        guess = (args.get("guess") or "").strip().lower()
        if len(guess) != 5:
            return jsonrpc_error(mid, -32602, "guess=5 letras"), state
        dist = pattern_distribution(guess, state["candidates"])
        H = entropy_bits(dist)
        total = sum(dist.values()) or 1
        info = {
            "guess": guess.upper(),
            "info": {
                "pattern_distribution": {k: v/total for k, v in dist.items()},
                "expected_information_bits": round(H, 3)
            },
            "rationale": "Cubre letras frecuentes; distribucion de patrones relativamente uniforme."
        }
        return jsonrpc_ok(mid, {"content": [{"type": "json", "json": info}]}), state

    if name == "reset":
        state["candidates"] = ALL_WORDS.copy()
        state["history"] = []
        return jsonrpc_ok(mid, {"content": [{"type": "text", "text": "Estado reiniciado"}]}), state

    return jsonrpc_error(mid, -32601, f"Tool not found: {name}"), state

# -------------------- IO loops --------------------
def run_stdio():
    state: Dict = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), flush=True)
            continue
        resp, state = handle_request(req, state)
        print(json.dumps(resp), flush=True)

def demo_cli():
    print("Wordle Coach demo | suggest | apply CRATE YGYKK | explain SOLAR | reset | quit")
    state: Dict = {"candidates": ALL_WORDS.copy(), "history": []}
    while True:
        try:
            cmd = input("> ").strip()
        except EOFError:
            break
        if cmd in ("quit", "exit"):
            break
        if cmd == "suggest":
            resp, state = handle_request({"id": "demo", "method": "suggest_move", "params": {}}, state)
            print(resp["result"]); continue
        if cmd.startswith("apply "):
            try:
                _, g, f = cmd.split()
                resp, state = handle_request({"id": "demo", "method": "apply_feedback", "params": {"guess": g, "feedback": f}}, state)
                print(resp["result"])
            except Exception:
                print("Uso: apply CRATE YGYKK")
            continue
        if cmd.startswith("explain "):
            try:
                _, g = cmd.split()
                resp, state = handle_request({"id": "demo", "method": "explain", "params": {"guess": g}}, state)
                print(json.dumps(resp["result"], indent=2))
            except Exception:
                print("Uso: explain SOLAR")
            continue
        if cmd == "reset":
            resp, state = handle_request({"id": "demo", "method": "reset", "params": {}}, state)
            print(resp["result"]); continue
        print("Comando desconocido.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Corre modo interactivo local")
    args = parser.parse_args()
    demo_cli() if args.demo else run_stdio()

if __name__ == "__main__":
    main()