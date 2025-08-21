import sys, json, math, random, argparse, os
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

WORDS_PATH = os.path.join(os.path.dirname(__file__), "words.txt")

def load_words() -> List[str]:
    with open(WORDS_PATH, "r", encoding="utf-8") as f:
        return [w.strip().lower() for w in f if len(w.strip()) == 5 and w.strip().isalpha()]

ALL_WORDS = load_words()

def pattern_for_guess(guess: str, answer: str) -> str:
    # G=green, Y=yellow, K=gray
    g, a = list(guess), list(answer)
    res = ["K"]*5
    used = [False]*5

    # greens
    for i in range(5):
        if g[i] == a[i]:
            res[i] = "G"
            used[i] = True

    # yellows con conteo
    remaining = Counter(a[i] for i in range(5) if not used[i])
    for i in range(5):
        if res[i] == "K" and remaining[g[i]] > 0:
            res[i] = "Y"
            remaining[g[i]] -= 1
    return "".join(res)

def apply_feedback_to_candidates(cands: List[str], guess: str, feedback: str) -> List[str]:
    return [w for w in cands if pattern_for_guess(guess, w) == feedback]

def pattern_distribution(guess: str, cands: List[str]) -> Dict[str, int]:
    dist = defaultdict(int)
    for w in cands:
        dist[pattern_for_guess(guess, w)] += 1
    return dict(dist)

def entropy_bits(dist: Dict[str, int]) -> float:
    total = sum(dist.values())
    if total == 0: return 0.0
    H = 0.0
    for c in dist.values():
        p = c/total
        H += -p*math.log2(p)
    return H

def suggest_move(cands: List[str]) -> Dict:
    best_guess, best_H, best_dist = None, -1.0, None
    pool = cands if len(cands) <= 3000 else cands[:3000]
    for guess in pool:
        dist = pattern_distribution(guess, cands)
        H = entropy_bits(dist)
        if H > best_H:
            best_guess, best_H, best_dist = guess, H, dist
    if best_guess is None:
        best_guess = random.choice(cands) if cands else "soare"
        best_dist = pattern_distribution(best_guess, cands)
        best_H = entropy_bits(best_dist)
    total = sum(best_dist.values()) or 1
    largest = max(best_dist.values()) or 1
    pruning = 1.0 - (largest/total)
    return {
        "guess": best_guess.upper(),
        "expected_information_bits": round(best_H, 3),
        "estimated_pruning": round(pruning, 3),
        "why": "Maximiza entropía sobre candidatos actuales."
    }

def jsonrpc_response(id_, result=None, error=None):
    return {"jsonrpc": "2.0", "id": id_, "result": result} if error is None \
        else {"jsonrpc": "2.0", "id": id_, "error": error}

def handle_request(req: dict, state: dict) -> Tuple[dict, dict]:
    mid = req.get("id")
    method = req.get("method")
    params = req.get("params") or {}
    state.setdefault("candidates", ALL_WORDS.copy())
    state.setdefault("history", [])

    try:
        if method == "suggest_move":
            pstate = params.get("state") or state
            cands = pstate.get("candidates", state["candidates"])
            return jsonrpc_response(mid, suggest_move(cands)), state

        if method == "apply_feedback":
            guess = (params.get("guess") or "").strip().lower()
            feedback = (params.get("feedback") or "").strip().upper()
            if len(guess)!=5 or len(feedback)!=5 or any(ch not in "GYK" for ch in feedback):
                raise ValueError("guess=5 letras, feedback=5 de G/Y/K")
            new_cands = apply_feedback_to_candidates(state["candidates"], guess, feedback)
            state["candidates"] = new_cands
            state["history"].append({"guess": guess.upper(), "feedback": feedback})
            return jsonrpc_response(mid, {
                "candidates": len(new_cands),
                "sample": [w.upper() for w in new_cands[:10]],
                "constraints_applied": [{"guess": guess.upper(), "feedback": feedback}]
            }), state

        if method == "explain":
            guess = (params.get("guess") or "").strip().lower()
            if len(guess)!=5: raise ValueError("guess=5 letras")
            dist = pattern_distribution(guess, state["candidates"])
            H = entropy_bits(dist)
            total = sum(dist.values()) or 1
            return jsonrpc_response(mid, {
                "guess": guess.upper(),
                "info": {
                    "pattern_distribution": {k:v/total for k,v in dist.items()},
                    "expected_information_bits": round(H, 3)
                },
                "rationale": "Cubre letras frecuentes; distribución de patrones relativamente uniforme."
            }), state

        if method == "reset":
            state["candidates"] = ALL_WORDS.copy()
            state["history"] = []
            return jsonrpc_response(mid, {"candidates": len(state["candidates"])}), state

        return jsonrpc_response(mid, error={"code": -32601, "message": "Method not found"}), state

    except Exception as e:
        return jsonrpc_response(mid, error={"code": -32602, "message": f"Invalid params: {e}"}), state

def run_stdio():
    state = {}
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Parse error"}}), flush=True)
            continue
        resp, state = handle_request(req, state)
        print(json.dumps(resp), flush=True)

def demo_cli():
    print("Wordle Coach demo | suggest | apply CRATE YGYKK | explain SOLAR | reset | quit")
    state = {"candidates": ALL_WORDS.copy(), "history": []}
    while True:
        cmd = input("> ").strip()
        if cmd in ("quit","exit"): break
        if cmd == "suggest":
            resp, state = handle_request({"id":"demo","method":"suggest_move","params":{}}, state); print(resp["result"]); continue
        if cmd.startswith("apply "):
            try:
                _, g, f = cmd.split(); resp, state = handle_request({"id":"demo","method":"apply_feedback","params":{"guess":g,"feedback":f}}, state); print(resp["result"])
            except: print("Usage: apply CRATE YGYKK"); continue
        if cmd.startswith("explain "):
            try:
                _, g = cmd.split(); resp, state = handle_request({"id":"demo","method":"explain","params":{"guess":g}}, state); print(json.dumps(resp["result"], indent=2))
            except: print("Usage: explain SOLAR"); continue
        if cmd == "reset":
            resp, state = handle_request({"id":"demo","method":"reset","params":{}}, state); print(resp["result"]); continue
        print("Unknown command.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    demo_cli() if args.demo else run_stdio()

if __name__ == "__main__":
    main()