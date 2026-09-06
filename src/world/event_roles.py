"""
Event Role Layer (Фаза 13 / Мастер-план А1)
============================================

Вычисляет РОЛЬ игрока в мировом событии на основе тира влияния и ресурсов.
Строится ПОВЕРХ существующего TieredEventManager (v4_legacy): тир события
(1-8, где 1 — галактический масштаб) уже определяет доступ; этот слой
определяет, КАК игрок может взаимодействовать с событием.

Роли:
    INITIATOR          — игрок может запустить/повлиять на ход события такого масштаба
    PARTICIPANT        — может влиять на исход как участник
    VICTIM_BYSTANDER   — событие происходит С ним или рядом; исход вне его контроля
    UNINVOLVED         — событие вне поля зрения игрока (не показывается)

Инварианты прошлых фаз не затрагиваются: только чтение PLAYER_TIERS/TieredEventManager,
никаких изменений баланса/костей/каталога фракций.
"""

from typing import Dict, Optional

# Порог роли: событие тира N требует минимум такой "веса" игрока для INITIATOR/PARTICIPANT.
# Вес игрока = f(уровень, кредиты, макс. репутация фракций). Шкала 0-8 зеркалит тиры событий.
#
# Тир события: 1 = галактический ... 8 = бытовой.
# Логика: INITIATOR возможен, когда player_weight >= event_tier_weight + 2;
#         PARTICIPANT при >= event_tier_weight; иначе VICTIM_BYSTANDER,
#         UNINVOLVED если событие к тому же никак не связано с игроком.

def compute_player_weight(player: Dict) -> int:
    """
    Вычислить «вес» игрока (0-8) из уровня, кредитов и максимальной репутации.
    Использует те же пороги, что PLAYER_TIERS (engine), чтобы не расходиться с ними.
    """
    level = player.get("level", 1)
    credits = player.get("credits", 0)
    faction_rep = player.get("faction_rep", {}) or {}
    max_rep = max(faction_rep.values()) if faction_rep else 0

    weight = 0
    # Уровень: до 20 уровня даёт до ~5 пунктов
    if level >= 18: weight += 5
    elif level >= 14: weight += 4
    elif level >= 10: weight += 3
    elif level >= 6: weight += 2
    elif level >= 3: weight += 1

    # Кредиты: пороги PLAYER_TIERS (50k / 500k / 5M)
    if credits >= 5_000_000: weight += 3
    elif credits >= 500_000: weight += 2
    elif credits >= 50_000: weight += 1

    # Связи: репутация фракции
    if max_rep >= 60: weight += 1

    return max(0, min(8, weight))


# Минимальный вес игрока для INITIATOR по тиру события (1=галактический..8=бытовой)
INITIATOR_WEIGHT = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
# Для PARTICIPANT — на ступень ниже
PARTICIPANT_WEIGHT = {t: max(0, w - 2) for t, w in INITIATOR_WEIGHT.items()}

# Триггеры связи с игроком: локация/фракция/квест проверяются вызывающей стороной
# (у события могут быть involved_factions; у игрока — текущая локация и активные квесты)


def compute_event_role(event_tier: int, player: Dict,
                       event_factions: Optional[list] = None,
                       player_location_faction: Optional[str] = None,
                       event_touches_player_quest: bool = False,
                       player_tier: int = None) -> Dict:
    """
    Определить роль игрока в событии.

    event_tier: 1..8 (тир из TieredEventManager)
    player: dict {level, credits, faction_rep, location, active_quest_ids...}
    player_tier: P-tier (0-7) from compute_player_tier() — overrides weight calc
    event_factions: фракции, задействованные в событии
    player_location_faction: фракция, контролирующая текущую локацию игрока (если есть)
    event_touches_player_quest: событие связано с активным квестом игрока

    Возвращает {"role": str, "weight": int, "available_actions": [...]}
    """
    # Фаза 16: use player_tier if provided (multi-factor model), else legacy weight
    p = player_tier if player_tier is not None else compute_player_weight(player)
    tier = max(1, min(8, int(event_tier)))

    if player_tier is not None:
        # Фаза 16 исправлено: event_tier 1=галактический (нужен высокий P), 8=бытовой (любой)
        required_initiator = max(1, 8 - tier)
        required_participant = max(1, required_initiator - 2)
        if p >= required_initiator:
            role = "INITIATOR"
        elif p >= required_participant:
            role = "PARTICIPANT"
        else:
            role = "VICTIM_BYSTANDER"
    else:
        # Legacy weight-based fallback
        if weight >= INITIATOR_WEIGHT[tier]:
            role = "INITIATOR"
        elif weight >= PARTICIPANT_WEIGHT[tier]:
            role = "PARTICIPANT"
        else:
            role = "VICTIM_BYSTANDER"

    # UNINVOLVED: событие высоких тиров, игрок ниже участника И нет личной связи
    has_rep_link = any(v >= 40 for v in (player.get("faction_rep") or {}).values())
    loc_linked = bool(event_factions and player_location_faction
                      and player_location_faction in event_factions)
    if role == "VICTIM_BYSTANDER" and not (
        event_touches_player_quest or loc_linked or has_rep_link
    ):
        # Низкокалиберные события (7-8) видны всем — это местная жизнь
        if tier < 7:
            return {"role": "UNINVOLVED", "weight": p, "available_actions": []}

    actions = available_actions(role, tier)
    return {"role": role, "weight": p, "available_actions": actions}


def available_actions(role: str, tier: int):
    """Набор действий игрока в событии по роли."""
    if role == "INITIATOR":
        base = ["запустить", "направить", "спонсировать", "саботировать", "наблюдать"]
    elif role == "PARTICIPANT":
        base = ["присоединиться", "помочь одной из сторон", "саботировать", "наблюдать"]
    elif role == "VICTIM_BYSTANDER":
        base = ["спрятаться", "бежать", "использовать хаос", "наблюдать"]
    else:
        return []
    # Чем ниже тир события (локальнее), тем больше личных опций
    if tier >= 6 and role != "UNINVOLVED":
        base.append("вмешаться лично")
    return base


def describe_role(role: str) -> str:
    return {
        "INITIATOR": "Инициатор — вы можете запустить это событие или развернуть его ход",
        "PARTICIPANT": "Участник — вы можете влиять на исход",
        "VICTIM_BYSTANDER": "Свидетель/жертва — событие происходит с вами или рядом",
        "UNINVOLVED": "Вне вашей орбиты — вы узнаете об этом из новостей",
    }.get(role, role)
