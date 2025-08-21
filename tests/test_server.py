from src.mcp_server.server import handle_request

def run(method, params=None, state=None):
    req = {"jsonrpc":"2.0","id":"t","method":method,"params":params or {}}
    resp, st = handle_request(req, state or {})
    assert resp["jsonrpc"] == "2.0"
    return resp, st

def test_reset_and_suggest():
    resp, st = run("reset")
    assert resp["result"]["candidates"] > 0
    resp, st = run("suggest_move", state=st)
    assert "guess" in resp["result"]

def test_apply_feedback_filters():
    _, st = run("reset")
    resp, st = run("apply_feedback", {"guess":"CRATE","feedback":"YGYKK"}, st)
    assert isinstance(resp["result"]["candidates"], int)

def test_explain_shape():
    _, st = run("reset")
    resp, st = run("explain", {"guess":"SOLAR"}, st)
    assert "expected_information_bits" in resp["result"]["info"]
