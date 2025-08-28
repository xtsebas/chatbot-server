from typing import List, Dict, Set

# 8=Cardio, 10=Piernas, 12=Hombros, 11=Pecho, 13=Espalda, 14=Brazos, 9=Core
CATEGORIES = {
    "cardio": 8,
    "piernas": 10,
    "hombros": 12,
    "pecho": 11,
    "espalda": 13,
    "brazos": 14,
    "core": 9,
}

# Musculos WGER por nombre simplificado → ids (subset util)
MUSCLES = {
    "cuadriceps": 10,
    "isquios": 11,
    "gluteos": 8,
    "pantorrillas": 7,
    "lumbares": 12,
    "abdominales": 6,
    "oblicuos": 14,
    "pectoral": 4,
    "deltoides": 2,
    "trapecio": 3,
    "dorsal": 1,
    "biceps": 5,
    "triceps": 13,
    "antebrazo": 9,
}

# Somatotipo → enfoque de repeticiones/volumen
SOMATOTYPE_REP_RANGE = {
    "ectomorfo": (6, 10),     # fuerza-hipertrofia, descansos medios
    "mesomorfo": (8, 12),     # hipertrofia clasica
    "endomorfo": (10, 15),    # mas repeticiones, mas gasto calorico
}

# Objetivo → foco de categorias/musculos
def objective_targets(objetivo: str) -> Dict[str, Set[int]]:
    objetivo = (objetivo or "").lower()
    cats: Set[int] = set()
    muscles: Set[int] = set()

    if "hipertrofia" in objetivo or "aumento" in objetivo or "volumen" in objetivo or "musculo" in objetivo:
        cats |= {CATEGORIES["pecho"], CATEGORIES["espalda"], CATEGORIES["piernas"], CATEGORIES["hombros"], CATEGORIES["brazos"], CATEGORIES["core"]}
    if "fuerza" in objetivo or "powerlifting" in objetivo:
        cats |= {CATEGORIES["piernas"], CATEGORIES["pecho"], CATEGORIES["espalda"], CATEGORIES["hombros"], CATEGORIES["core"]}
    if "perder" in objetivo or "definir" in objetivo or "bajar" in objetivo:
        cats |= {CATEGORIES["cardio"], CATEGORIES["piernas"], CATEGORIES["core"], CATEGORIES["espalda"], CATEGORIES["pecho"]}
    if "movilidad" in objetivo or "agilidad" in objetivo:
        cats |= {CATEGORIES["piernas"], CATEGORIES["core"], CATEGORIES["hombros"]}

    return {"categories": cats, "muscles": muscles}

# Deporte → musculos/categorias clave
def sport_targets(deporte: str) -> Dict[str, Set[int]]:
    deporte = (deporte or "").lower()
    cats: Set[int] = set()
    muscles: Set[int] = set()

    if "futbol" in deporte:
        cats |= {CATEGORIES["piernas"], CATEGORIES["core"], CATEGORIES["cardio"]}
        muscles |= {MUSCLES["cuadriceps"], MUSCLES["isquios"], MUSCLES["pantorrillas"], MUSCLES["gluteos"], MUSCLES["abdominales"], MUSCLES["oblicuos"]}
    if "basket" in deporte or "basquet" in deporte or "basketball" in deporte:
        cats |= {CATEGORIES["piernas"], CATEGORIES["core"], CATEGORIES["hombros"], CATEGORIES["espalda"]}
        muscles |= {MUSCLES["cuadriceps"], MUSCLES["isquios"], MUSCLES["gluteos"], MUSCLES["deltoides"], MUSCLES["dorsal"], MUSCLES["abdominales"]}
    if "saltar" in deporte or "vertical" in deporte:
        cats |= {CATEGORIES["piernas"], CATEGORIES["core"]}
        muscles |= {MUSCLES["cuadriceps"], MUSCLES["isquios"], MUSCLES["gluteos"], MUSCLES["pantorrillas"], MUSCLES["abdominales"]}
    if "calistenia" in deporte:
        cats |= {CATEGORIES["espalda"], CATEGORIES["pecho"], CATEGORIES["hombros"], CATEGORIES["brazos"], CATEGORIES["core"]}
    if "levantamiento" in deporte or "pesas" in deporte or "powerlifting" in deporte:
        cats |= {CATEGORIES["piernas"], CATEGORIES["espalda"], CATEGORIES["pecho"], CATEGORIES["hombros"], CATEGORIES["core"]}

    return {"categories": cats, "muscles": muscles}

# Sugerencias de series x repeticiones segun objetivo / somatotipo
def pick_set_rep(objetivo: str, somatotipo: str):
    low, high = SOMATOTYPE_REP_RANGE.get(somatotipo.lower(), (8, 12))
    objetivo = (objetivo or "").lower()
    sets = 3

    if "fuerza" in objetivo:
        return 4, max(3, low - 2)
    if "resistencia" in objetivo or "definir" in objetivo or "perder" in objetivo:
        return 3, min(15, high + 2)
    # hipertrofia por defecto
    return 3, min(12, max(8, (low + high)//2))
