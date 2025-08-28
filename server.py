import os
import asyncio
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from planner import (
    UserStats, GoalRequest, RoutineRequest,
    compute_bmi, compute_bmr_mifflin, select_exercises, build_routine, recommend_by_metrics
)

mcp = FastMCP("mcp-personal-trainer")

# Timeout por herramienta (segundos), configurable por env
TRAINER_TOOL_TIMEOUT = float(os.getenv("TRAINER_TOOL_TIMEOUT", "25.0"))

# ---------- Schemas ----------
class ComputeMetricsParams(BaseModel):
    sexo: Optional[str] = Field(None, description="male|female")
    edad: Optional[int] = None
    altura_cm: Optional[float] = None
    peso_kg: Optional[float] = None

class RecommendParams(BaseModel):
    objetivo: str
    deporte: Optional[str] = None
    limite: int = 12
    source_priority: List[str] = Field(default_factory=lambda: ["ninjas", "local"])  # "rapidapi" opcional

class RoutineParams(BaseModel):
    objetivo: str
    deporte: Optional[str] = None
    somatotipo: Optional[str] = None
    dias_por_semana: int = 3
    minutos_por_sesion: int = 60
    experiencia: Optional[str] = "intermedio"
    source_priority: List[str] = Field(default_factory=lambda: ["ninjas", "local"])

class RecommendByMetricsParams(BaseModel):
    sexo: Optional[str] = None
    edad: Optional[int] = None
    altura_cm: Optional[float] = None
    peso_kg: Optional[float] = None
    bmi: Optional[float] = None
    objetivo: str
    deporte: Optional[str] = None
    limite: int = 12
    source_priority: List[str] = Field(default_factory=lambda: ["ninjas", "local"])

# ---------- Helpers ----------
async def _run(fn, *args, timeout: Optional[float] = None):
    """Ejecuta una función de planner en hilo con timeout configurable."""
    to = timeout if timeout is not None else TRAINER_TOOL_TIMEOUT
    return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=to)

# ---------- Tools ----------
@mcp.tool()
async def compute_metrics(params: ComputeMetricsParams) -> Dict[str, Any]:
    """Calcula BMI y BMR (Mifflin-St Jeor)"""
    bmi = compute_bmi(params.peso_kg or 0, params.altura_cm or 0)
    bmr = compute_bmr_mifflin(params.sexo or "male", params.peso_kg or 0, params.altura_cm or 0, params.edad or 0)
    clas = ("bajo peso" if bmi and bmi < 18.5 else "normal" if bmi and bmi < 25 else "sobrepeso" if bmi and bmi < 30 else "obesidad" if bmi else "desconocido")
    return {"bmi": bmi, "bmi_clase": clas, "bmr": bmr}

@mcp.tool()
async def recommend_exercises(params: RecommendParams) -> List[Dict[str, Any]]:
    """Recomienda ejercicios usando API Ninjas / datasets locales."""
    gr = GoalRequest(objetivo=params.objetivo, deporte=params.deporte, limite=params.limite, source_priority=params.source_priority)
    return await _run(select_exercises, gr)

@mcp.tool()
async def build_routine_tool(params: RoutineParams) -> Dict[str, Any]:
    """Genera una rutina semanal con sets/reps y enlaces/notes."""
    rr = RoutineRequest(**params.model_dump())
    return await _run(build_routine, rr)

@mcp.tool()
async def recommend_by_metrics_tool(params: RecommendByMetricsParams) -> Dict[str, Any]:
    """Con altura/peso/edad/BMI + objetivo/deporte devuelve métricas y ejercicios adecuados."""
    stats = UserStats(sexo=params.sexo, edad=params.edad, altura_cm=params.altura_cm, peso_kg=params.peso_kg, bmi=params.bmi)
    return await _run(recommend_by_metrics, stats, params.objetivo, params.deporte, params.limite, params.source_priority)

if __name__ == "__main__":
    mcp.run()