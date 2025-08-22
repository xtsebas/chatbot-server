from __future__ import annotations
import math
from collections import Counter, defaultdict
from typing import Dict, List

def pattern_for_guess(guess: str, answer: str) -> str:
    """
    Retorna patrón Wordle para guess vs answer:
    G=green, Y=yellow, K=gray. Maneja letras repetidas correctamente.
    """
    guess = guess.lower()
    answer = answer.lower()
    res = ["K"] * 5
    used = [False] * 5

    # greens
    for i in range(5):
        if guess[i] == answer[i]:
            res[i] = "G"
            used[i] = True

    # yellows con conteo remanente
    remaining = Counter(answer[i] for i in range(5) if not used[i])
    for i in range(5):
        if res[i] == "K" and remaining[guess[i]] > 0:
            res[i] = "Y"
            remaining[guess[i]] -= 1

    return "".join(res)

def apply_feedback_to_candidates(candidates: List[str], guess: str, feedback: str) -> List[str]:
    guess = guess.lower()
    feedback = feedback.upper()
    return [w for w in candidates if pattern_for_guess(guess, w) == feedback]

def pattern_distribution(guess: str, candidates: List[str]) -> Dict[str, int]:
    dist: Dict[str, int] = defaultdict(int)
    for cand in candidates:
        dist[pattern_for_guess(guess, cand)] += 1
    return dict(dist)

def entropy_bits(dist: Dict[str, int]) -> float:
    total = sum(dist.values())
    if total == 0:
        return 0.0
    H = 0.0
    for c in dist.values():
        p = c / total
        H += -p * math.log2(p)
    return H

def suggest_move(candidates: List[str]) -> dict:
    """
    Recorre candidatos y retorna el de mayor entropía esperada.
    """
    if not candidates:
        return {
            "guess": None,
            "expected_information_bits": 0.0,
            "estimated_pruning": 0.0,
            "why": "Sin candidatos."
        }

    best_guess = None
    best_H = -1.0
    best_dist = None

    # para diccionarios grandes se podría muestrear; aquí recorremos todo
    for guess in candidates:
        dist = pattern_distribution(guess, candidates)
        H = entropy_bits(dist)
        if H > best_H:
            best_guess, best_H, best_dist = guess, H, dist

    total = sum(best_dist.values()) or 1
    largest = max(best_dist.values()) or 1
    pruning = 1.0 - (largest / total)

    return {
        "guess": best_guess.upper(),
        "expected_information_bits": round(best_H, 3),
        "estimated_pruning": round(pruning, 3),
        "why": "Maximiza entropia sobre candidatos actuales."
    }
