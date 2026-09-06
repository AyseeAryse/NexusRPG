"""
Expense Cycle (Мастер-план А3)
==============================

Симметричный доходам цикл трат: upkeep недвижимости, обслуживание корабля,
стоимость жизни по тиру влияния. Вводится НОВАЯ механика (не пересчёт старых
балансов): расходы начисляются по игровым часам в том же тике, где
PropertyIncomeManager собирает доход.

Принципы:
  - Не трогает баланс origins/расходников (инварианты Фаз 10-11).
  - Расходы не могут увести кредиты ниже 0 — долг фиксируется как "debt".
  - Всё сериализуемо (to_dict/from_dict) для сейва.
"""

from typing import Dict, Optional

# ── Black Market / Heat Thresholds (Вариант I) ──
HEAT_RAID_THRESHOLD = 5       # heat ≥ 5 → рейд (штраф/потеря предметов)
HEAT_LOCKOUT_THRESHOLD = 10   # heat ≥ 10 → локаут законных магазинов 24ч
HEAT_DECAY_PER_WEEK = 1       # -1 heat за неделю без нарушений

# Upkeep недвижимости: % от income_per_cycle ИЛИ фикс для бездоходных типов.
PROPERTY_UPKEEP = {
    # type: {"rate": доля от дохода, "fixed": фикс за цикл}
    "apartment":  {"fixed": 50},     # коммуналка
    "warehouse":  {"fixed": 100},    # аренда площади
    "shop":       {"rate": 0.30},    # 30% дохода уходит на оборот
    "bar":        {"rate": 0.35},
    "hideout":    {"fixed": 150},    # конспирация стоит денег
    "office":     {"rate": 0.30},
}
DEFAULT_UPKEEP_FIXED = 75   # неизвестный тип — базовая коммуналка

# Стоимость жизни по тиру влияния (в час; тик ~168ч = неделя)
LIFESTYLE_COST_PER_HOUR = {0: 2, 1: 8, 2: 25, 3: 80}

# Обслуживание корабля: от стоимости судна, начисляется раз в цикл
# Прогрессивная шкала: чем дороже корабль, тем ниже процент (эффект масштаба)
SHIP_UPKEEP_TIERS = [
    (2_000_000, 0.002),    # первые 2M: 0.2%
    (10_000_000, 0.0008),  # от 2M до 10M: 0.08%
]                        # свыше 10M: 0.03%
SHIP_UPKEEP_RATE_FLOOR = 0.0003


def _progressive_upkeep(ship_value: int) -> int:
    """Прогрессивная шкала обслуживания корабля (Фаза 15).
    Первые 2M по 0.2%, от 2M до 10M по 0.08%, свыше 10M по 0.03%.
    Устраняет ловушку бедности: дешёвый корабль не блокирует накопление."""
    if ship_value <= 0:
        return 0
    upkeep = 0.0
    tier1 = min(ship_value, 2_000_000)
    upkeep += tier1 * 0.002
    tier2 = min(max(0, ship_value - 2_000_000), 8_000_000)
    if tier2 > 0:
        upkeep += tier2 * 0.0008
    tier3 = max(0, ship_value - 10_000_000)
    if tier3 > 0:
        upkeep += tier3 * 0.0003
    return int(upkeep)


class ExpenseCycle:
    """Недельный цикл расходов. Вызывается синхронно с PropertyIncomeManager.tick."""

    def __init__(self):
        self.last_cycle_hours = 0
        self.income_interval_hours = 168
        self.total_paid = 0
        self.history = []          # последние записи расходов

    def due(self, current_hours: float) -> bool:
        return (current_hours - self.last_cycle_hours) >= self.income_interval_hours

    def tick(self, current_hours: float, property_system, ship_system,
             character: Dict, player_tier: int = 0) -> Optional[Dict]:
        """
        Начислить и списать расходы. Возвращает dict брейкдауна или None.
        Расходы вычитаются из character["credits"], при нехватке копится debt.
        """
        if not self.due(current_hours):
            return None
        self.last_cycle_hours = current_hours

        breakdown = {"property_upkeep": 0, "lifestyle": 0, "ship_maintenance": 0}

        # 1) Недвижимость
        for p in getattr(property_system, "properties", []) or []:
            rule = PROPERTY_UPKEEP.get(p.get("type"), {"fixed": DEFAULT_UPKEEP_FIXED})
            if "rate" in rule:
                cost = int(p.get("income_per_cycle", 0) * rule["rate"])
            else:
                cost = rule["fixed"]
            # Плохое состояние удорожает содержание
            condition = p.get("condition", 100)
            if condition < 60:
                cost = int(cost * 1.5)
            breakdown["property_upkeep"] += cost

        # 2) Стоимость жизни по тиру
        breakdown["lifestyle"] = LIFESTYLE_COST_PER_HOUR.get(player_tier, 2) * (self.income_interval_hours // 24)

        # 3) Корабль (прогрессивная шкала — Фаза 15)
        ship_val = 0
        try:
            ship_val = int(ship_system.ship.get("value", 0)) if ship_system and ship_system.ship else 0
        except Exception:
            ship_val = 0
        breakdown["ship_maintenance"] = _progressive_upkeep(ship_val)

        total = sum(breakdown.values())

        credits = character.get("credits", 0)
        if credits >= total:
            character["credits"] = credits - total
            paid, debt = total, 0
        else:
            paid = credits
            debt = total - credits
            character["credits"] = 0
        character["debt"] = character.get("debt", 0) + debt

        # ── Heat decay (Вариант I): -1 heat за неделю без нарушений ──
        heat = character.get("heat", 0)
        heat_decayed = 0
        if heat > 0:
            heat_decayed = min(HEAT_DECAY_PER_WEEK, heat)
            character["heat"] = heat - heat_decayed

        record = {"cycle_hours": current_hours, "paid": paid, "debt_added": debt,
                  "total_due": total, "heat_decayed": heat_decayed, **breakdown}
        self.total_paid += paid
        self.history.append(record)
        self.history = self.history[-12:]
        return record

    def to_dict(self) -> Dict:
        return {"last_cycle_hours": self.last_cycle_hours,
                "income_interval_hours": self.income_interval_hours,
                "total_paid": self.total_paid,
                "history": self.history[-6:]}

    @classmethod
    def from_dict(cls, data: Dict) -> "ExpenseCycle":
        e = cls()
        e.last_cycle_hours = data.get("last_cycle_hours", 0)
        e.income_interval_hours = data.get("income_interval_hours", 168)
        e.total_paid = data.get("total_paid", 0)
        e.history = data.get("history", [])
        return e