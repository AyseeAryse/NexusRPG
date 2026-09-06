"""
Multi-Factor Player Tier System (Фаза 16)
==========================================

Заменяет одноосевую модель PLAYER_TIERS (только credits) на 6-осевую модель
с AND-гейтингом. Тир игрока P0-P7 синхронизирован с тирами событий
TieredEventManager (1-8, зеркально: P7 = события тира 1).

Оси:
  1. Net worth (кредиты + недвижимость + корабль) — не только наличные
  2. Max faction reputation (глубина связей)
  3. Factions with rep >= 25 (широта связей)
  4. Fame (известность, накапливается через квесты/новости/rep-up)
  5. Character level
  6. max(intelligence, charisma) (компетентностный атрибут)

Тир повышается ТОЛЬКО когда ВСЕ 6 порогов достигнуты одновременно (AND).
"""

from typing import Dict, Tuple

# ── Пороги по осям для каждого тира P0-P7 ──
# Индексы: [net_worth, max_rep, fac_count, fame, level, max_int_cha]
TIER_THRESHOLDS: Dict[str, Tuple] = {
    "P0": (0,           0,  0,   0,   1,  1),
    "P1": (75_000,     15,  1,   5,   3,  3),
    "P2": (300_000,    30,  2,   15,  6,  5),
    "P3": (1_000_000,  45,  3,   35,  9,  6),
    "P4": (3_000_000,  55,  4,   70,  11, 7),
    "P5": (8_000_000,  65,  5,   120, 13, 8),
    "P6": (20_000_000, 75,  7,   200, 16, 9),
    "P7": (50_000_000, 85,  9,   350, 18, 10),
}

TIER_ORDER = ["P0","P1","P2","P3","P4","P5","P6","P7"]

# ── Fame accumulation rates ──
FAME_PER_QUEST_TIER = {
    1: 100, 2: 65, 3: 40, 4: 20, 5: 12, 6: 7, 7: 4, 8: 3,
}
FAME_PER_REP_UP = 5          # при rep_change >= +10
FAME_PER_NEWS_MENTION = 15   # когда новость упоминает фракцию игрока (rep >= 40)
# D4b: верный вывод дела (conclude_case correct=True). Масштаб: дело ~ квест
# тира 4 (FAME_PER_QUEST_TIER[4] = 20); крупнее REP_UP/NEWS_MENTION, т.к.
# закрытие дела — редкое сюжетное событие, требующее полного набора улик.
FAME_PER_CORRECT_CONCLUSION = 20

# ── Lifestyle cost per day by player tier ──
LIFESTYLE_PER_DAY = {0:2, 1:8, 2:25, 3:80, 4:150, 5:300, 6:500, 7:800}


def compute_net_worth(character: Dict, property_system=None, ship_system=None) -> int:
    """Net worth = credits + property values + ship value."""
    credits = character.get("credits", 0)
    prop_value = 0
    if property_system and hasattr(property_system, "properties"):
        for p in property_system.properties:
            prop_value += p.get("value", p.get("income_per_cycle", 0) * 50)  # fallback: 50x weekly income
    ship_value = 0
    if ship_system and getattr(ship_system, "ship", None):
        ship_value = ship_system.ship.get("value", ship_system.ship.get("price", 0))
    return credits + prop_value + ship_value


def compute_player_tier(character: Dict, faction_rep: Dict,
                        fame: int = 0, net_worth: int = None) -> Dict:
    """
    Вычислить тир игрока P0-P7 по 6 осям (AND-гейтинг).

    Returns: {"tier": int, "tier_name": str, "axes": {...}, "blocking_axes": [...]}
    """
    level = character.get("level", 1)
    credits = character.get("credits", 0)
    attrs = character.get("attributes", {})
    intelligence = attrs.get("intelligence", 1)
    charisma = attrs.get("charisma", 1)
    competence = max(intelligence, charisma)

    max_rep = max(faction_rep.values()) if faction_rep else 0
    fac_count = len([r for r in faction_rep.values() if r >= 25])

    if net_worth is None:
        net_worth = credits

    axes = [net_worth, max_rep, fac_count, fame, level, competence]
    axis_names = ["net_worth", "max_rep", "fac_count", "fame", "level", "competence"]

    # Find highest tier where ALL axes meet thresholds
    tier = 0
    blocking = []
    for t_idx in range(7, -1, -1):
        t_name = TIER_ORDER[t_idx]
        thresholds = TIER_THRESHOLDS[t_name]
        met = all(axes[i] >= thresholds[i] for i in range(6))
        if met:
            tier = t_idx
            break
        # Track which axes block this tier
        if t_idx > tier:  # only record for tiers above current
            for i in range(6):
                if axes[i] < thresholds[i] and axis_names[i] not in blocking:
                    blocking.append(axis_names[i])

    # Determine blocking axes for the NEXT tier
    next_t = min(tier + 1, 7)
    next_thresholds = TIER_THRESHOLDS[TIER_ORDER[next_t]]
    next_blocking = [axis_names[i] for i in range(6) if axes[i] < next_thresholds[i]]

    return {
        "tier": tier,
        "tier_name": TIER_ORDER[tier],
        "axes": dict(zip(axis_names, axes)),
        "blocking_axes": next_blocking,
    }


def compute_player_weight(player_tier: int) -> int:
    """Compatibility shim: convert P-tier to numeric weight for event_roles."""
    return player_tier


def lifestyle_cost_per_week(player_tier: int) -> int:
    return LIFESTYLE_PER_DAY.get(player_tier, 2) * 7


# ── Tier display names (Russian) ──
TIER_NAMES_RU = {
    0: "Никто",
    1: "Новичок",
    2: "Известный в районе",
    3: "Влиятельный игрок",
    4: "Фигура городского масштаба",
    5: "Системный игрок",
    6: "Влиятель на систему",
    7: "Легенда системы",
}
