import os, csv, glob
from typing import Any, Dict, List, Optional, Tuple
import httpx
from cachetools import TTLCache, cached

# -------- Config --------
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY", "").strip()
RAPIDAPI_KEY   = os.getenv("RAPIDAPI_KEY", "").strip()
RAPIDAPI_HOST  = "ai-workout-planner-exercise-fitness-nutrition-guide.p.rapidapi.com"

FILES_DIR = os.path.join(os.path.dirname(__file__), "files")

# Intentamos detectar nombres reales de archivos
def _find_file(stem: str) -> Optional[str]:
    # acepta 'gym_exercise_dataset' o 'gym_exercise_dataset.csv'
    patterns = [f"{stem}", f"{stem}.csv", f"{stem}*.csv"]
    for p in patterns:
        paths = glob.glob(os.path.join(FILES_DIR, p))
        if paths:
            return paths[0]
    return None

GYM_FILE      = _find_file("gym_exercise_dataset") or _find_file("gym_exercise_dataset.csv")
STRETCH_FILE  = _find_file("stretch_exercise_dataset") or _find_file("stretch_exercise_dataset.csv")
TRACKER_FILE  = _find_file("workout_fitness_tracker_data") or _find_file("workout_fitness_tracker_data.csv")

# -------- HTTP Clients --------
_transport = httpx.HTTPTransport(retries=2)
_client_ninjas = httpx.Client(
    base_url="https://api.api-ninjas.com",
    timeout=httpx.Timeout(connect=3, read=6, write=6, pool=3),
    headers={"X-Api-Key": API_NINJAS_KEY} if API_NINJAS_KEY else {},
    transport=_transport,
)
_client_rapid  = httpx.Client(
    base_url=f"https://{RAPIDAPI_HOST}",
    timeout=httpx.Timeout(connect=3, read=8, write=8, pool=3),
    headers={
        "Content-Type": "application/json",
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    } if RAPIDAPI_KEY else {},
    transport=_transport,
)

_cache = TTLCache(maxsize=512, ttl=1200)

# -------- Mapeos a API Ninjas --------
# https://api.api-ninjas.com/v1/exercises params: name, type, muscle, difficulty, equipment
NINJAS_MUSCLES = {
    "piernas": ["quadriceps", "hamstrings", "calves", "glutes"],
    "saltos": ["quadriceps", "hamstrings", "calves", "glutes", "abdominals"],
    "pecho": ["chest"],
    "espalda": ["lats", "middle_back", "lower_back"],
    "hombros": ["shoulders"],
    "brazos": ["biceps", "triceps", "forearms"],
    "core": ["abdominals", "obliques"],
    "futbol": ["quadriceps", "hamstrings", "calves", "glutes", "abdominals", "obliques"],
    "basketball": ["quadriceps", "hamstrings", "calves", "glutes", "abdominals", "shoulders", "lats"],
    "calistenia": ["chest", "lats", "abdominals", "biceps", "triceps", "shoulders"],
    "pesas": ["chest", "lats", "quadriceps", "hamstrings", "glutes", "shoulders", "abdominals"],
}
def target_to_ninjas(objetivo: str, deporte: Optional[str]) -> Tuple[List[str], List[str]]:
    objetivo = (objetivo or "").lower()
    deporte  = (deporte or "").lower()
    muscles: List[str] = []
    types: List[str] = []

    if any(k in objetivo for k in ["hipertrofia", "aumento", "volumen", "musculo"]):
        types.append("strength")
    if any(k in objetivo for k in ["fuerza", "powerlifting"]):
        types.append("powerlifting")
    if any(k in objetivo for k in ["perder", "definir", "bajar", "resistencia"]):
        types.append("cardio")

    # deporte
    if "futbol" in deporte:
        muscles += NINJAS_MUSCLES["futbol"]
    elif "basket" in deporte or "basquet" in deporte or "basketball" in deporte:
        muscles += NINJAS_MUSCLES["basketball"]
    elif "saltar" in deporte or "vertical" in deporte:
        muscles += NINJAS_MUSCLES["saltos"]
    elif "calistenia" in deporte:
        muscles += NINJAS_MUSCLES["calistenia"]
    elif "levantamiento" in deporte or "pesas" in deporte:
        muscles += NINJAS_MUSCLES["pesas"]
    else:
        # generico
        muscles += NINJAS_MUSCLES["piernas"] + NINJAS_MUSCLES["core"] + ["chest", "lats", "shoulders"]

    # si no hay type, poner strength por defecto
    if not types:
        types = ["strength"]

    # dedup conservando orden
    uniq_m, seen = [], set()
    for m in muscles:
        if m not in seen:
            uniq_m.append(m); seen.add(m)
    return uniq_m, types

# -------- Normalización --------
def _norm(ex: Dict[str, Any]) -> Dict[str, Any]:
    # API Ninjas estructura: name, type, muscle, equipment, difficulty, instructions
    return {
        "id": f"ninjas:{ex.get('name','')}-{ex.get('muscle','')}-{ex.get('type','')}",
        "name": ex.get("name"),
        "muscle": ex.get("muscle"),
        "type": ex.get("type"),
        "equipment": ex.get("equipment"),
        "difficulty": ex.get("difficulty"),
        "instructions": ex.get("instructions", ""),
        "url": None,
        "source": "api_ninjas",
    }

def _norm_local(row: Dict[str, Any]) -> Dict[str, Any]:
    name = row.get("Exercise Name") or row.get("exercise") or row.get("name")
    return {
        "id": f"local:{name}",
        "name": name,
        "muscle": (row.get("Main_muscle") or row.get("Target_Muscles") or "").strip(),
        "type": row.get("Mechanics") or row.get("Utility") or "unknown",
        "equipment": row.get("Equipment"),
        "difficulty": row.get("Difficulty (1-5)") or row.get("difficulty"),
        "instructions": (row.get("Preparation") or "") + " " + (row.get("Execution") or ""),
        "url": None,
        "source": "local_dataset",
    }

# -------- Lectura datasets locales --------
@cached(_cache)
def load_local_exercises() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in filter(None, [GYM_FILE, STRETCH_FILE]):
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    ex = _norm_local(r)
                    if ex["name"]:
                        out.append(ex)
        except Exception:
            # segundo intento con latin-1
            try:
                with open(path, "r", encoding="latin-1", newline="") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        ex = _norm_local(r)
                        if ex["name"]:
                            out.append(ex)
            except Exception:
                pass
    return out

def _filter_local_by_muscles(rows: List[Dict[str, Any]], muscles: List[str], limit: int) -> List[Dict[str, Any]]:
    # coincidencia por substring simple
    mus = [m.lower() for m in muscles]
    picked = []
    for r in rows:
        blob = (r.get("muscle") or "").lower()
        if any(m in blob for m in mus):
            picked.append(r)
            if len(picked) >= limit:
                break
    return picked

# -------- API Ninjas --------
def ninjas_query(muscles: List[str], types: List[str], limit: int) -> List[Dict[str, Any]]:
    if not API_NINJAS_KEY:
        return []
    results: List[Dict[str, Any]] = []
    for t in types:
        for m in muscles:
            try:
                res = _client_ninjas.get("/v1/exercises", params={"type": t, "muscle": m, "offset": 0})
                if res.status_code == 200:
                    arr = res.json()
                    for ex in arr:
                        results.append(_norm(ex))
                        if len(results) >= limit:
                            return results
            except Exception:
                continue
    return results[:limit]

# -------- RapidAPI (opcional) --------
def rapid_generate_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not RAPIDAPI_KEY:
        return {"plan": None, "note": "RAPIDAPI_KEY no configurada"}
    try:
        r = _client_rapid.post("/generateWorkoutPlan?noqueue=1", json=payload)
        if r.status_code == 200:
            return r.json()
        return {"plan": None, "status": r.status_code, "text": r.text[:500]}
    except Exception as e:
        return {"plan": None, "error": str(e)}

# -------- Selector de fuente --------
def get_exercises_from_source(objetivo: str, deporte: Optional[str], limit: int, source: str) -> List[Dict[str, Any]]:
    muscles, types = target_to_ninjas(objetivo, deporte)
    if source == "ninjas":
        res = ninjas_query(muscles, types, limit)
        if res:
            return res
        # fallback a local si API falla
        return _filter_local_by_muscles(load_local_exercises(), muscles, limit)
    elif source == "rapidapi":
        # no retorna lista de ejercicios simple; generamos usando datasets si se quiere lista
        return _filter_local_by_muscles(load_local_exercises(), muscles, limit)
    else:  # local
        return _filter_local_by_muscles(load_local_exercises(), muscles, limit)

def multi_source_recommend(objetivo: str, deporte: Optional[str], limit: int,
                           source_priority: List[str]) -> List[Dict[str, Any]]:
    for src in source_priority:
        items = get_exercises_from_source(objetivo, deporte, limit, src)
        if items:
            return items[:limit]
    return []
