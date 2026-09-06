"""
src/utils/clinic.py — проверка доступности клиники/госпиталя поблизости
для имплант-хирургии. Извлечено из app.py при рефакторинге blueprints.
"""
from typing import Dict

_CLINIC_WORDS = ["клиник", "госпиталь", "больниц", "медик", "лаборатор", "doctor", "медцентр"]
_SURGERY_SERVICES = ["healing", "surgery", "implant_install", "implant_check"]

# Phase 26: константы имплант-хирургии (из app.py при рефакторинге blueprints)
SURGERY_FEE_BASE = 5000
SELF_SURGERY_DC_PENALTY = 3


def _check_clinic_nearby(loc: Dict) -> bool:
    """True если в текущей локации (place/district) есть медицинские сервисы."""
    place = (loc.get("place") or "").lower()
    district = (loc.get("district") or "").lower()
    if any(w in place for w in _CLINIC_WORDS) or any(w in district for w in _CLINIC_WORDS):
        return True
    # Fallback: проверяем establishments в district data
    engine = None
    try:
        from src.server.routes._deps import get_engine
        engine = get_engine()
    except Exception:
        return False
    dist_data = engine.galaxy_map.get_district(
        loc.get("planet", ""), loc.get("city", ""), loc.get("district", ""))
    if dist_data:
        for est in dist_data.get("establishments", []):
            services = est.get("services", [])
            if any(s in services for s in _SURGERY_SERVICES):
                return True
    return False
