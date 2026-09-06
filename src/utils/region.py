"""
src/utils/region.py — утилита маппинга influence_region → planet.
Нейтральный слой, не зависит от core/ или server/.
"""
_en_ru = {
    "earth": "земля", "mars": "марс", "moon": "луна",
    "ceres": "церера", "ganymede": "ганимед", "belt": "пояс",
    "jupiter": "юпитер", "saturn": "сатурн", "venus": "венера",
}


def region_matches(region: str, planet: str) -> bool:
    """True если influence_region покрывает planet (для D3a-фильтра фракций).

    Маппинг: "вся солнечная" → все планеты; "пояс астероидов" → "пояс";
    en→ru алиасы; иначе подстрочное вхождение.
    """
    r = (region or "").lower()
    p = (planet or "").lower()
    if not r or not p:
        return False
    p = _en_ru.get(p, p)
    if p == "пояс астероидов":
        p = "пояс"
    if "вся солнечная" in r:
        return True
    return p in r
