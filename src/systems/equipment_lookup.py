"""
Equipment Stats Lookup (Фаза 17, A1)
=====================================

Мост между каталогом TECH_EQUIPMENT и боевым кодом.
Инвентарь хранит предметы как {name, qty, category} — этот модуль
резолвит имя предмета в его боевые статы (damage/defense) из каталога.

Кэшируется при первом обращении (каталог не меняется в рантайме).
"""

import json
import os
import re

_EQUIPMENT_INDEX = None


def _load_index():
    """Построить индекс name -> {damage, defense, range, damage_type} из TECH_EQUIPMENT."""
    global _EQUIPMENT_INDEX
    if _EQUIPMENT_INDEX is not None:
        return _EQUIPMENT_INDEX

    index = {}
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "game_data", "TECH_EQUIPMENT.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for w in data.get("weapons", []):
            index[w["name"]] = {
                "kind": "weapon",
                "damage": w.get("damage", ""),
                "damage_type": w.get("damage_type", "physical"),
                "range": w.get("range", ""),
            }
        for c in data.get("consumables", []):
            # Лечебные формулы парсим из текста эффекта («восстанавливает 2d6+2 HP»);
            # прочие эффекты (баффы/антидоты) в боевой механике не числятся.
            effect = str(c.get("effect", ""))
            m = re.search(r"(\d+d\d+(?:\+\d+)?)\s*HP", effect)
            if m and any(w in effect.lower() for w in ("восстанавливает", "hp")):
                index[c["name"]] = {
                    "kind": "consumable_heal",
                    "heal_formula": m.group(1),
                    "effect_text": effect,
                }

        for a in data.get("armor", []):
            # Защита каталога в шкале 1-15; конверсия defense/3 → +0..+5 AC.
            # Нечисловые значения ("Специальный" у щита Аврора с origin-механикой)
            # дают бонус через свои особые правила, в общий AC не добавляются.
            try:
                defense = int(a.get("defense", 0))
                defense_bonus = round(defense / 3)
            except (TypeError, ValueError):
                defense_bonus = 0
            index[a["name"]] = {
                "kind": "armor",
                "defense_bonus": defense_bonus,
                "durability": a.get("durability", 100),
            }
    except (OSError, json.JSONDecodeError):
        pass  # Каталог недоступен — пустой индекс, бой работает на дефолтах

    # Phase 28 G1: индексируем также магазинный каталог (BASE_SHOP_ITEMS).
    # Купленные в магазине предметы ("Винтовка «Ястреб»") не из TECH_EQUIPMENT —
    # раньше resolve_item возвращал None → слот-классификация валила всё в "pocket".
    try:
        from src.world.simulation import BASE_SHOP_ITEMS  # отложенный импорт (циклич. зависимость)
        _CAT_KIND = {"weapons": "weapon", "armor": "armor", "implants": "implant",
                     "gadgets": "gadget", "consumables": "consumable"}
        for category, items in BASE_SHOP_ITEMS.items():
            kind = _CAT_KIND.get(category, "misc")
            for it in items:
                nm = it.get("name")
                if not nm or nm in index:
                    continue
                entry = {"kind": kind, "category": category,
                         "base_price": it.get("base_price", 0)}
                if kind == "weapon":
                    entry["damage"] = it.get("stats", "")
                    entry["range"] = ""
                elif kind == "armor":
                    entry["defense"] = it.get("stats", "")
                index[nm] = entry
    except Exception:
        pass  # магазинный каталог недоступен — слоты работают на TECH_EQUIPMENT

    _EQUIPMENT_INDEX = index
    return index


def resolve_item(name: str):
    """Вернуть статы предмета по имени или None."""
    return _load_index().get((name or "").strip())



# Зонные band'ы оружия (единый источник для combat.py и выбора оружия, Фаза 18)
RANGE_NAME_TO_BAND = {
    "Ближняя": [0],
    "Короткая": [0, 1],
    "Средняя": [1],
    "Дальняя": [1, 2],
    "Конус": [0, 1],
    "Любая": [0, 1, 2],
}


def weapon_zone_band(range_name):
    """Band зон [0=ближняя,1=средняя,2=дальняя] по строке range из каталога."""
    return RANGE_NAME_TO_BAND.get((range_name or "").strip(), [0, 1, 2])


def parse_damage(formula: str):
    """
    Распарсить формулу урона. Возвращает (count, sides, bonus, burst) или None.
    Поддерживает: '2d6', '2d6+1', '1d4x3' / '1d4x3 очереди' (burst-множитель).
    """
    m = re.match(r"(\d+)d(\d+)(?:\+(\d+))?(?:\s*x(\d+))?", (formula or "").strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)),
            int(m.group(3) or 0), int(m.group(4) or 1))


def expected_damage(formula: str, hit_penalty: int = 0) -> float:
    """
    Ожидаемый урон формулы с учётом штрафa к броску попадания (-3 вне зоны).
    Модель: каждый пункт штрафа ≈ −5% шанс попадания (шкала d20),
    множитель очереди умножает средний урон за атаку.
    """
    parsed = parse_damage(formula)
    if not parsed:
        return 0.0
    count, sides, bonus, burst = parsed
    avg = count * (sides + 1) / 2 + bonus
    hit_mult = max(0.05, 1.0 - abs(hit_penalty) * 0.05 * -1 if False else max(0.05, 1.0 + min(0, hit_penalty) * 0.15))
    return avg * burst * hit_mult


def weapon_damage_for_inventory(inventory, current_zone=None):
    """
    Найти лучшее оружие в инвентаре.

    Без current_zone — как раньше (максимум dice-потолка).
    С current_zone (0=ближняя/1=средняя/2=дальняя) — выбирает оружие по
    ОЖИДАЕМОМУ урону: вне band'а оружия применяется зонный штраф −3 к броску
    (≈ −45% ожидаемого урона), поэтому более слабое оружие в своей зоне может
    выиграть у сильного со штрафом.
    Возвращает (formula, name).
    """
    best_formula = None
    best_name = None
    best_score = -1.0

    def score(formula: str, rng: str) -> float:
        parsed = parse_damage(formula)
        if not parsed:
            return -1.0
        count, sides, bonus, burst = parsed
        power = count * sides + bonus
        if current_zone is None:
            return float(power)
        band = weapon_zone_band(rng)
        penalty = 0 if current_zone in band else 3
        # ожидаемый урон за атаку: среднее × burst × штраф-множитель
        avg = count * (sides + 1) / 2 + bonus
        return avg * burst * (1.0 - penalty * 0.15)

    for item in inventory or []:
        # Прямое поле damage (каталог TECH_EQUIPMENT)
        dmg = item.get("damage")
        rng_name = item.get("range") or (resolve_item(item.get("name")) or {}).get("range", "")
        if isinstance(dmg, str) and parse_damage(dmg):
            s = score(dmg, rng_name)
            if s > best_score:
                best_score, best_formula, best_name = s, dmg.split(" ")[0], item.get("name")
            continue

        # Резолв по имени через каталог
        stats = resolve_item(item.get("name"))
        if stats and stats.get("kind") == "weapon" and stats.get("damage"):
            s = score(stats["damage"], stats.get("range", ""))
            if s > best_score:
                best_score, best_formula, best_name = s, stats["damage"], item.get("name")
            continue

        # Legacy: поле stats с формулой внутри
        legacy = item.get("stats") or ""
        m = re.search(r"(\d+d\d+(?:\+\d+)?)", str(legacy))
        if m:
            s = score(m.group(1), "")
            if s > best_score:
                best_score, best_formula, best_name = s, m.group(1), item.get("name")

    return (best_formula or "1d6"), best_name


def armor_defense_bonus_for_inventory(inventory) -> int:
    """
    Суммарный бонус защиты от брони в инвентаре (максимум одного комплекта носится,
    но для простоты берём лучший defense_bonus среди всей брони в инвентаре).
    """
    best = 0
    for item in inventory or []:
        stats = resolve_item(item.get("name"))
        if stats and stats.get("kind") == "armor":
            best = max(best, stats.get("defense_bonus", 0))
    return best


def find_heal_consumable(inventory):
    """Вернуть (index_in_list, name, heal_formula) первого лечебного расходника."""
    for i, item in enumerate(inventory or []):
        qty = item.get("qty", 1)
        if qty is not None and qty <= 0:
            continue
        stats = resolve_item(item.get("name"))
        if stats and stats.get("kind") == "consumable_heal":
            return i, item.get("name"), stats["heal_formula"]
    return None, None, None


def consume_at(inventory, index):
    """Списать одну единицу предмета; удалить запись при исчерпании."""
    item = inventory[index]
    item["qty"] = item.get("qty", 1) - 1
    if item["qty"] <= 0:
        inventory.pop(index)


def roll_formula(formula):
    """Бросок формулы вида NdM+B (для урона и лечения)."""
    import random as _random
    m = re.match(r"(\d+)d(\d+)(?:\+(\d+))?", formula or "")
    if not m:
        return 0
    total = 0
    for _ in range(int(m.group(1))):
        total += _random.randint(1, int(m.group(2)))
    if m.group(3):
        total += int(m.group(3))
    return total


def find_grenade_consumable(inventory):
    """Вернуть (index, name, formula) первой гранаты. Гранаты ищем по имени/типу
    в каталоге оружия с damage_type explosive ИЛИ по маркеру имени."""
    for i, item in enumerate(inventory or []):
        qty = item.get("qty", 1)
        if qty is not None and qty <= 0:
            continue
        stats = resolve_item(item.get("name"))
        if stats and stats.get("kind") == "weapon" and stats.get("damage_type") == "explosive":
            return i, item.get("name"), stats["damage"]
    return None, None, None


def make_vehicle_enemy(vehicle: dict) -> dict:
    """
    Конвертировать транспортную запись VEHICLES.json в противника для CombatEngine
    (Фаза 18, П.1 — одобренный план). hull → hp, armor//5 → defense (RAW, цикл сам
    добавляет базу AC=10+), dmg по sqrt-шкале: count = max(2, round(sqrt(hull)/8)).
    """
    import math
    hull = int(vehicle.get("hull", 50))
    armor = int(vehicle.get("armor", 0))
    count = max(2, round(math.sqrt(hull) / 8))
    bonus = armor // 5
    category = str(vehicle.get("category", ""))
    zone = 2 if category in ("military", "industrial", "commercial") else 1
    import uuid
    return {
        "id": f"veh_{uuid.uuid4().hex[:6]}",
        "name": vehicle.get("name", "Транспорт"),
        "hp": hull,
        "max_hp": hull,
        "attack": max(1, armor // 5 + 2),
        "defense": max(0, armor // 5),
        "initiative": 3,
        "damage": f"{count}d6+{bonus}",
        "damage_formula": f"{count}d6+{bonus}",
        "loot_credits": (int(vehicle.get("price", 0) * 0.01),
                         int(vehicle.get("price", 0) * 0.03)),
        "tactics": "aggressive",
        "abilities": ["armored"],
        "status_effects": [],
        "turns_alive": 0,
        "_vehicle": True,
        "_zone_default": zone,
    }


# ══════════════════════════════════════════════════════════════════
#  IMPLANT CATALOG (Phase 24c B5-3 refactor — moved from src/server/app.py
#  to break circular dependency: core/engine.py → server/app.py)
# ══════════════════════════════════════════════════════════════════

# Structured skill bonuses for all implants (parsed from stats text).
# Ключ — id импланта в каталоге (или v3-префикс), значение — механика.
IMPLANT_SKILL_MAP = {
    "I_NEURO_BASIC":  {"skill_bonuses": {"hacking": 1}, "humanity_cost": 2, "surgery_dc": 8},
    "I_OPTICS":       {"skill_bonuses": {"education": 1}, "humanity_cost": 3, "surgery_dc": 10},
    "I_ARM_CYBER":    {"skill_bonuses": {"combat": 1}, "attr_bonuses": {"strength": 2}, "humanity_cost": 5, "surgery_dc": 12},
    "I_REFLEX_BOOST": {"skill_bonuses": {}, "attr_bonuses": {"reflexes": 1}, "humanity_cost": 4, "surgery_dc": 14},
    "I_NANOBLOOD":    {"skill_bonuses": {}, "hp_regen": 2, "humanity_cost": 6, "surgery_dc": 15},
    "I_NEURO_ADV":    {"skill_bonuses": {"hacking": 2, "technology": 1}, "humanity_cost": 4, "surgery_dc": 12},
    "I_LEGS_CYBER":   {"skill_bonuses": {"stealth": 1}, "attr_bonuses": {"dexterity": 2}, "humanity_cost": 5, "surgery_dc": 13},
    "I_SKIN_ARMOR":   {"skill_bonuses": {}, "defense_bonus": 4, "humanity_cost": 7, "surgery_dc": 16},
    "I_LUNG_FILTER":  {"skill_bonuses": {"survival": 1}, "attr_bonuses": {"endurance": 1}, "humanity_cost": 3, "surgery_dc": 10},
    "I_BONE_LACING":  {"skill_bonuses": {}, "attr_bonuses": {"strength": 1, "endurance": 1}, "hp_bonus": 15, "humanity_cost": 8, "surgery_dc": 16},
    "I_EMOTION_CHIP": {"skill_bonuses": {"diplomacy": 2}, "attr_bonuses": {"willpower": -1}, "humanity_cost": 4, "surgery_dc": 14},
    "I_COMBAT_CHIP":  {"skill_bonuses": {"combat": 2}, "attr_bonuses": {"reflexes": 1}, "humanity_cost": 5, "surgery_dc": 14},
    "I_MEMORY_BANK":  {"skill_bonuses": {"education": 1}, "attr_bonuses": {"intelligence": 1}, "humanity_cost": 3, "surgery_dc": 11},
    "I_THERMAL_EYES": {"skill_bonuses": {"education": 1}, "humanity_cost": 3, "surgery_dc": 11},
    "I_SUBVOCAL":     {"skill_bonuses": {}, "humanity_cost": 1, "surgery_dc": 7},
    # v3 implants
    "v3_cyber_eyes_upgrade": {"skill_bonuses": {"education": 2}, "humanity_cost": 4, "surgery_dc": 12},
    "v3_subdermal_armor":    {"skill_bonuses": {}, "defense_bonus": 3, "humanity_cost": 6, "surgery_dc": 15},
    "v3_reflex_booster":     {"skill_bonuses": {}, "attr_bonuses": {"reflexes": 2}, "humanity_cost": 5, "surgery_dc": 14},
    "v3_cortex_bomb":        {"skill_bonuses": {}, "humanity_cost": 10, "surgery_dc": 18},
    "v3_synth_blood":        {"skill_bonuses": {"survival": 1}, "hp_regen": 1, "humanity_cost": 4, "surgery_dc": 13},
    "v3_muscle_wire":        {"skill_bonuses": {"combat": 1}, "attr_bonuses": {"strength": 2}, "humanity_cost": 6, "surgery_dc": 14},
}

# Default fallback для неизвестных имплантов
IMPLANT_DEFAULT = {"skill_bonuses": {}, "humanity_cost": 3, "surgery_dc": 12}

# Константы хирургии (используются в install/remove endpoints)
SURGERY_FEE_BASE = 5000
SELF_SURGERY_DC_PENALTY = 4
