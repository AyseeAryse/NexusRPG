"""
src/world/faction_conflict_sim.py — Симулятор межфракционных конфликтов (Phase 3).

Превращает 168 спящих `plot_hooks` из FACTIONS_MASTER.json в живые события
мира с throttling и Catastrophe Ceiling по тирам P0–P1.

Public API:
  - FactionConflictSimulator(kb_files).tick(player_tier, current_location) → list[dict]
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Tier-based scope (Phase 3 / backlog#4):
#   P0–P1: только локальные инциденты (санкции, забастовка, рейд, скачок цен 10-25%)
#   P2:   могут появиться региональные (волнения в секторе)
#   P3+:  планетарные (блокады, войны флотов) — но НЕ на P0–P1
LOCAL_INCIDENTS = {"sanctions", "strike", "raid", "price_shock", "scandal", "protest"}
REGIONAL_INCIDENTS = {"sector_unrest", "supply_disruption", "embargo_partial"}
PLANETARY_INCIDENTS = {"blockade", "fleet_war", "orbital_bombardment", "regime_change"}

# Локальные типы plot_hooks (только они на P0–P1)
LOCAL_HOOK_TYPES = {"ethical_debate", "scandal", "secret_project", "discovery",
                   "recruitment", "supply_dispute", "labor_dispute", "audit"}

# Pacing Guard: ≥4 тиков между кризисами в одной локации
THROTTLE_TICKS = 4

# Catastrophe Ceiling: ценовой шок для P0–P1
PRICE_SHOCK_MIN = 0.10  # +10%
PRICE_SHOCK_MAX = 0.25  # +25%


class FactionConflictSimulator:
    """Генерирует события мира на основе plot_hooks + throttling + tier ceiling."""

    def __init__(self, kb_files: Dict[str, Any]):
        self.kb = kb_files
        self._factions: List[Dict] = []
        self._factions_by_region: Dict[str, List[Dict]] = defaultdict(list)
        self._last_crisis_location: Dict[str, int] = {}  # location_key → tick_count
        self._current_tick = 0
        self._last_event: Optional[Dict] = None
        self._load_factions()

    def _load_factions(self) -> None:
        """Один раз при init: парсит FACTIONS_MASTER.json и группирует по influence_region."""
        factions_doc = self.kb.get("FACTIONS_MASTER.json") or {}
        factions = factions_doc.get("factions", [])
        self._factions = factions
        for f in factions:
            region = (f.get("influence_region") or "").lower().strip()
            if region:
                self._factions_by_region[region].append(f)

    @staticmethod
    def _location_key(location: Optional[Dict]) -> str:
        """Нормализует локацию в ключ для throttling."""
        if not location:
            return "unknown"
        planet = (location.get("planet") or "").lower()
        city = (location.get("city") or "").lower()
        district = (location.get("district") or "").lower()
        return f"{planet}|{city}|{district}"

    def _filter_factions_by_location(self, location: Optional[Dict]) -> List[Dict]:
        """Возвращает фракции текущей локации (по influence_region) + общие (вся солнечная)."""
        if not location:
            return list(self._factions)
        planet = (location.get("planet") or "").lower()
        city = (location.get("city") or "").lower()
        district = (location.get("district") or "").lower()
        out = []
        for region, factions in self._factions_by_region.items():
            r = region.lower()
            if "вся солнечная" in r:
                out.extend(factions)
                continue
            if planet in r or r in planet or city in r or district in r:
                out.extend(factions)
        return out

    def _tier_allowed(self, player_tier: int, incident_type: str) -> bool:
        """Catastrophe Ceiling: P0–P1 блокирует планетарные катастрофы."""
        if incident_type in PLANETARY_INCIDENTS:
            return player_tier >= 3
        if incident_type in REGIONAL_INCIDENTS:
            return player_tier >= 2
        # local — всегда разрешены
        return True

    def _throttle_ok(self, location_key: str) -> bool:
        """Pacing Guard: ≥4 тиков между кризисами в одной локации."""
        last = self._last_crisis_location.get(location_key, -10**9)
        return (self._current_tick - last) >= THROTTLE_TICKS

    def tick(self, player_tier: int, current_location: Optional[Dict] = None) -> List[Dict]:
        """Генерирует 0-2 события за тик (с учётом throttling и tier ceiling).

        Returns: list[dict] с полями:
          - id, faction_a, faction_b (опц.), type, description, scope
          - price_modifier_delta (float)
          - heat_delta (int)
          - location_key
        """
        self._current_tick += 1
        location_key = self._location_key(current_location)
        results: List[Dict] = []

        # Pacing Guard: пропускаем если слишком рано для повтора
        if not self._throttle_ok(location_key):
            return results

        factions = self._filter_factions_by_location(current_location)
        if not factions:
            return results

        # 1-2 пары конкурирующих фракций
        pairs = self._pick_pairs(factions, max_pairs=2)
        if not pairs:
            return results

        for f_a, f_b in pairs:
            event = self._build_event(f_a, f_b, player_tier, location_key)
            if event is None:
                continue
            results.append(event)
            # Обновляем throttling после первого события в этой локации
            self._last_crisis_location[location_key] = self._current_tick

        if results:
            self._last_event = results[-1]
        return results

    def _pick_pairs(self, factions: List[Dict], max_pairs: int = 2) -> List[tuple]:
        """Выбирает пары конкурирующих фракций (enemies ↔ targets)."""
        # Приоритет: пары с явными enemies-связями
        name_to_faction = {f.get("name"): f for f in factions}
        pairs = []
        used = set()
        for f in factions:
            name_a = f.get("name")
            if not name_a or name_a in used:
                continue
            enemies = f.get("enemies") or []
            for enemy_name in enemies:
                enemy_f = name_to_faction.get(enemy_name)
                if enemy_f and enemy_f.get("name") not in used:
                    pair = (f, enemy_f)
                    pairs.append(pair)
                    used.add(name_a)
                    used.add(enemy_name)
                    break
            if len(pairs) >= max_pairs:
                break
        # Если не набрали — случайные пары
        if not pairs and len(factions) >= 2:
            sample = random.sample(factions, min(max_pairs, len(factions) // 2) * 2)
            for i in range(0, len(sample) - 1, 2):
                pairs.append((sample[i], sample[i+1]))
        return pairs

    def _build_event(self, f_a: Dict, f_b: Dict, player_tier: int, location_key: str) -> Optional[Dict]:
        """Строит одно событие из plot_hooks пары фракций."""
        # Берём hook от faction_a (если есть)
        hooks_a = f_a.get("plot_hooks") or []
        hooks_b = f_b.get("plot_hooks") or []
        if not hooks_a and not hooks_b:
            return None
        hook = (hooks_a or hooks_b)[0]
        hook_type = hook.get("type", "discovery")

        # Map hook_type → incident scope
        if hook_type in LOCAL_HOOK_TYPES:
            incident_type = random.choice(["sanctions", "raid", "price_shock", "scandal"])
            scope = "local"
        elif hook_type in {"recruitment", "supply_dispute"}:
            incident_type = "sector_unrest"
            scope = "regional"
        else:
            incident_type = random.choice(list(REGIONAL_INCIDENTS))
            scope = "regional"

        # Catastrophe Ceiling
        if not self._tier_allowed(player_tier, incident_type):
            # Downgrade до local на P0–P1
            incident_type = "price_shock"
            scope = "local"

        # Экономический отклик: price_modifier_delta
        if incident_type == "price_shock":
            price_delta = random.uniform(PRICE_SHOCK_MIN, PRICE_SHOCK_MAX)
        else:
            price_delta = random.uniform(0.03, 0.08)

        # Heat delta
        heat_delta = 0
        if incident_type in ("raid", "scandal", "blockade"):
            heat_delta = random.randint(2, 8)
        elif incident_type in ("sanctions", "sector_unrest"):
            heat_delta = random.randint(1, 4)

        # Описание
        hook_desc = hook.get("description", "").strip()
        if not hook_desc:
            hook_desc = f"Кризис между {f_a.get('name')} и {f_b.get('name')}"

        return {
            "id": f"fcs_{self._current_tick}_{f_a.get('id', '?')}_{f_b.get('id', '?')}",
            "faction_a": f_a.get("name"),
            "faction_b": f_b.get("name"),
            "type": incident_type,
            "scope": scope,
            "description": hook_desc,
            "price_modifier_delta": round(price_delta, 3),
            "heat_delta": heat_delta,
            "location_key": location_key,
            "tick": self._current_tick,
        }

    def get_last_event_summary(self) -> Optional[str]:
        """Короткое (≤1 предложение) описание последнего локального события для scene_meta."""
        if not self._last_event:
            return None
        e = self._last_event
        scope = e.get("scope", "local")
        f_a = e.get("faction_a", "?")
        f_b = e.get("faction_b", "?")
        inc = e.get("type", "incident")
        return f"[{scope}/{inc}] {f_a} ↔ {f_b}"
