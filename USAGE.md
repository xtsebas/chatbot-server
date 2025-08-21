# USAGE – MCP Wordle Coach

## Arranque (stdio)
mcp-wordle-coach

## JSON-RPC ejemplos
{"jsonrpc":"2.0","id":"1","method":"suggest_move","params":{"state":null}}

{"jsonrpc":"2.0","id":"2","method":"apply_feedback","params":{"guess":"CRATE","feedback":"YGYKK"}}

{"jsonrpc":"2.0","id":"3","method":"explain","params":{"guess":"SOLAR"}}

{"jsonrpc":"2.0","id":"4","method":"reset","params":{}}
