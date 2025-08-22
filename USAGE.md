# USAGE – MCP Wordle Coach

## Arranque (stdio)
mcp-wordle-coach

## JSON-RPC ejemplos
{"jsonrpc":"2.0","id":"1","method":"suggest_move","params":{"state":null}}

{"jsonrpc":"2.0","id":"2","method":"apply_feedback","params":{"guess":"CRATE","feedback":"YGYKK"}}

{"jsonrpc":"2.0","id":"3","method":"explain","params":{"guess":"SOLAR"}}

{"jsonrpc":"2.0","id":"4","method":"reset","params":{}}


## Llamadas MCP (tools)
1) Handshake
{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2025-06-18"}}

2) Listar herramientas
{"jsonrpc":"2.0","id":"2","method":"tools/list","params":{}}

3) Llamar tool: suggest_move
{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"suggest_move","arguments":{}}}

4) Llamar tool: apply_feedback
{"jsonrpc":"2.0","id":"4","method":"tools/call","params":{"name":"apply_feedback","arguments":{"guess":"CRATE","feedback":"YGYKK"}}}
