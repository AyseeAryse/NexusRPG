"""
Генератор предметов Фазы 14 (Блок 1).
Ценовая лестница — инвариант Фазы 13, цены ВЫВОДЯТСЯ из редкости (не задаются вручную),
что исключает Берсерк-паттерн по построению.
"""
import json

LADDER = {
    "обычный":     (300, 4000),
    "редкий":      (5000, 11000),
    "эпический":   (12000, 18000),
    "легендарный": (19000, 42000),
    "уникальный":  (26000, 45000),
    "артефакт":    (100000, 150000),
}

def price_for(rarity: str, pos: float = 0.5) -> int:
    lo, hi = LADDER[rarity]
    return int((lo + (hi - lo) * pos) // 50 * 50)

def weapon(fid, name, wtype, rarity, dmg, dtype, rng, special, pos=0.5):
    return {"id": fid, "name": name, "type": wtype, "rarity": rarity,
            "damage": dmg, "damage_type": dtype, "range": rng,
            "cost": price_for(rarity, pos), "description": f"{wtype}. {special}.",
            "special": special}

def implant(fid, name, rarity, effect, drawback, pos=0.5):
    return {"id": fid, "name": name, "type": "Имплант", "rarity": rarity,
            "cost": price_for(rarity, pos), "effect": effect,
            "description": f"{effect}. Минус: {drawback}.", "drawback": drawback}

def consumable(fid, name, rarity, effect, note, pos=0.5):
    return {"id": fid, "name": name, "type": "Расходник", "rarity": rarity,
            "cost": price_for(rarity, pos), "effect": effect,
            "description": f"{effect}. ({note})"}
