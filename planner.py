from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from exercise_sources import multi_source_recommend

# -------- modelos ----------
class UserStats(BaseModel):
    sexo: Optional[str] = Field(None, description="male|female")
    edad: Optional[int] = None
    altura_cm: Optional[float] = None
    peso_kg: Optional[float] = None
    bmi: Optional[float] = None

class GoalRequest(BaseModel):
    objetivo: str
    deporte: Optional[str] = None
    limite: int = 20
    source_priority: List[str] = Field(default_factory=lambda: ["ninjas", "local"])  # "rapidapi" opcional

class RoutineRequest(BaseModel):
    objetivo: str
    deporte: Optional[str] = None
    somatotipo: Optional[str] = None
    dias_por_semana: int = 3
    minutos_por_sesion: int = 60
    experiencia: Optional[str] = "intermedio"
    source_priority: List[str] = Field(default_factory=lambda: ["ninjas", "local"])

# -------- métricas ----------
def compute_bmi(peso_kg: float, altura_cm: float) -> float:
    if not peso_kg or not altura_cm: return 0.0
    h = altura_cm/100.0
    return round(peso_kg/(h*h), 2)

def compute_bmr_mifflin(sexo: str, peso_kg: float, altura_cm: float, edad: int) -> float:
    if not (sexo and peso_kg and altura_cm and edad): return 0.0
    if (sexo or "").lower().startswith("m"):
        bmr = 10*peso_kg + 6.25*altura_cm - 5*edad + 5
    else:
        bmr = 10*peso_kg + 6.25*altura_cm - 5*edad - 161
    return round(bmr, 1)

# -------- sets/reps ----------
def pick_set_rep(objetivo: str, somatotipo: Optional[str]) -> (int, int):
    s = (somatotipo or "").lower()
    if "ecto" in s:   base = (3, 8)
    elif "endo" in s: base = (3, 12)
    else:             base = (3, 10)
    if "fuerza" in (objetivo or "").lower():
        return (4, 5)
    if any(k in (objetivo or "").lower() for k in ["perder", "definir", "resistencia"]):
        return (3, 12)
    return base

# -------- selección ejercicios ----------
def select_exercises(goal: GoalRequest) -> List[Dict[str, Any]]:
    return multi_source_recommend(goal.objetivo, goal.deporte, goal.limite, goal.source_priority)

# -------- rutina ----------
def build_routine(req: RoutineRequest) -> Dict[str, Any]:
    sets, reps = pick_set_rep(req.objetivo, req.somatotipo or "mesomorfo")
    pool = select_exercises(GoalRequest(
        objetivo=req.objetivo, deporte=req.deporte, limite=max(20, req.dias_por_semana*6),
        source_priority=req.source_priority
    ))
    if not pool:
        return {"dias": [], "recomendacion": "No se encontraron ejercicios", "prescripcion": {"sets": sets, "reps": reps}}

    days = req.dias_por_semana
    per_day = 6 if req.minutos_por_sesion >= 60 else 4

    day_plans: List[Dict[str, Any]] = []
    i = 0
    for d in range(days):
        dia = []
        while len(dia) < per_day and i < len(pool):
            dia.append(pool[i]); i += 1
        day_plans.append({
            "dia": d+1,
            "ejercicios": [
                {"name": e["name"], "sets": sets, "reps": reps, "notes": e.get("difficulty"), "source": e.get("source")}
                for e in dia
            ]
        })

    return {"dias": day_plans, "prescripcion": {"sets": sets, "reps": reps}, "notas": "Ajusta cargas segun RIR 1-2"}

# -------- recomendaciones por métricas ----------
def recommend_by_metrics(stats: UserStats, objetivo: str, deporte: Optional[str],
                         limit: int, source_priority: List[str]) -> Dict[str, Any]:
    bmi = stats.bmi or compute_bmi(stats.peso_kg or 0, stats.altura_cm or 0)
    clas = ("bajo" if bmi and bmi < 18.5 else "normal" if bmi and bmi < 25 else "sobrepeso" if bmi and bmi < 30 else "obesidad" if bmi else "desconocido")
    # Heurística simple
    obj = objetivo
    if clas in ("sobrepeso", "obesidad") and "fuerza" not in (objetivo or ""):
        obj = "perder grasa y resistencia"
    elif clas == "bajo" and "hipertrofia" not in (objetivo or ""):
        obj = "hipertrofia"

    items = multi_source_recommend(obj, deporte, limit, source_priority)
    return {"bmi": bmi, "bmi_clase": clas, "objetivo_ajustado": obj, "ejercicios": items}
