"""
Faction Resolver — Phase 3 P0 fix: маппинг CL{i}/MC{i}/SC{i}/NF{i}/SME{i} ↔ реальные
записи FACTIONS_MASTER.json.

Содержит FactionResolver, который:
- грузит FACTIONS_MASTER.json один раз (кэш),
- резолвит значение (id или name) в запись,
- нормализует faction к каноничному id (например, "LunarTech Industries" → "MC1"),
- предоставляет alias-map CL{i} ↔ MC{i} для случаев, когда NPC ссылается
  на «слот» фракции по CL-индексу, а не по реальному id (Phase 19+ остаточные данные).

Зачем:
- Закрывает разрыв NPC↔Faction (P0 долг): 166 NPC в NAMED_NPCS.json используют
  faction=MC1..SME52, и каждый такой id должен резолвиться в фактическую запись
  FACTIONS_MASTER.json.
- Нормализует процедурно сгенерированных NPC (faction="LunarTech Industries" → "MC1"),
  чтобы единое поле faction у всех NPC всегда содержало валидный id.
"""
import json
import os
from typing import Dict, Optional


# Phase 19: исторически NPC ссылались на слоты по CL{i}. Если в данных ещё
# остались такие ссылки — резолвим их через позиционный порядок FACTIONS_MASTER.
# Это fallback, основная форма уже использует MC/SC/NF/SME id напрямую.
CL_SLOT_ALIAS = {
    # CL1 → factions[0], CL2 → factions[1], …, CL166 → factions[165]
}


def _project_root() -> str:
    """Корень репо: src/world/faction_resolver.py → ../../."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


class FactionResolver:
    """Phase 3 P0 fix: резолвер связывания NPC ↔ Фракции.

    Использование:
        r = FactionResolver()
        rec = r.resolve("MC1")        # → {"id": "MC1", "name": "LunarTech Industries", …}
        rec = r.resolve("LunarTech")  # → то же самое по name
        cid = r.canonical("LunarTech Industries")  # → "MC1"
        ok  = r.is_valid("MC1")       # → True

    Резолвер оперирует фактическими записями FACTIONS_MASTER.json. Если файл
    не найден, FactionResolver работает как пустой — is_valid() всегда False.
    """

    FACTIONS_FILE = "FACTIONS_MASTER.json"

    def __init__(self, game_data_dir: Optional[str] = None):
        self._by_id: Dict[str, Dict] = {}
        self._by_name_lower: Dict[str, Dict] = {}
        self._ordered_ids: list = []
        self._loaded = False
        self._game_data_dir = game_data_dir or os.path.join(_project_root(), "game_data")
        self.load()

    def load(self) -> None:
        """Грузит FACTIONS_MASTER.json и строит индексы."""
        path = os.path.join(self._game_data_dir, self.FACTIONS_FILE)
        if not os.path.exists(path):
            self._loaded = True
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self._loaded = True
            return
        factions = data.get("factions") or []
        for f in factions:
            fid = f.get("id")
            if not fid:
                continue
            self._by_id[fid] = f
            name = f.get("name")
            if name:
                self._by_name_lower[str(name).lower()] = f
        self._ordered_ids = list(self._by_id.keys())
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    # ───────── основной API ─────────

    def by_id(self, fid: str) -> Optional[Dict]:
        return self._by_id.get(fid)

    def by_name(self, name: str) -> Optional[Dict]:
        return self._by_name_lower.get(str(name).lower())

    def is_valid(self, value) -> bool:
        """True если value — известный id или name фракции."""
        if not value:
            return False
        s = str(value).strip()
        if s in self._by_id:
            return True
        return s.lower() in self._by_name_lower

    def resolve(self, value) -> Optional[Dict]:
        """Резолв по id, name или CL{i}-слоту. Возвращает запись или None."""
        if not value:
            return None
        s = str(value).strip()
        if not s:
            return None
        # 1) прямой id
        if s in self._by_id:
            return self._by_id[s]
        # 2) name (case-insensitive)
        if s.lower() in self._by_name_lower:
            return self._by_name_lower[s.lower()]
        # 3) CL{i} слот → i-я по порядку фракция
        if s.upper().startswith("CL") and s[2:].isdigit():
            idx = int(s[2:]) - 1
            if 0 <= idx < len(self._ordered_ids):
                return self._by_id[self._ordered_ids[idx]]
        return None

    def canonical(self, value) -> Optional[str]:
        """Нормализует любое значение к каноничному id фракции или None."""
        rec = self.resolve(value)
        if not rec:
            return None
        return rec.get("id")

    def all_factions(self) -> list:
        """Список всех id фракций в порядке следования в JSON."""
        return list(self._ordered_ids)


# ───────── удобный singleton для горячих путей ─────────

_default_resolver: Optional[FactionResolver] = None


def get_default_resolver() -> FactionResolver:
    """Ленивый singleton (один резолвер на процесс)."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = FactionResolver()
    return _default_resolver
