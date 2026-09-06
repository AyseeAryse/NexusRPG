"""
src/systems/contract_generator.py — Генератор контрактов из plot_hooks (Phase 3).

Превращает 168 спящих plot_hooks в активные задания с Dual-Path Requirement:
минимум 2 альтернативных пути решения (силовой/прямой vs технический/социальный).

Public API:
  - ContractGenerator(kb_files).get_available_contracts(location, player_tier) → list[dict]
"""
from __future__ import annotations
import hashlib
import random
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Tier 0: 1 500 – 4 500 ₡
# (Tier 1: 3 000 – 9 000, Tier 2: 6 000 – 18 000, ...)
TIER_REWARD_RANGES = {
    0: (1500, 4500),
    1: (3000, 9000),
    2: (6000, 18000),
    3: (12000, 36000),
    4: (24000, 72000),
    5: (48000, 144000),
    6: (96000, 288000),
    7: (192000, 576000),
}

TIER_XP = {
    0: 50, 1: 120, 2: 250, 3: 500, 4: 1000,
    5: 2000, 6: 4000, 7: 8000,
}

# Dual-Path Requirement: hook_type → список из ≥2 альтернатив
HOOK_TYPE_PATHS = {
    "ethical_debate": [
        ("Инфильтрация в лабораторию и сбор компромата через [Взлом]",
         "Скандал через СМИ и формирование общественного мнения через [Переговоры]"),
    ],
    "scandal": [
        ("Прямое расследование через [Расследование] и слежка",
         "Утечка информации через [Взлом] внутренних серверов"),
    ],
    "secret_project": [
        ("Проникновение на объект через [Скрытность] и кража чертежей",
         "Внедрение агента через [Переговоры] и выкуп инсайдера"),
    ],
    "discovery": [
        ("Экспедиция в опасную зону через [Выживание] и сбор образцов",
         "Удалённый анализ через [Взлом] сетей наблюдения и реконструкция"),
    ],
    "recruitment": [
        ("Вербовка цели напрямую через [Убеждение] или [Запугивание]",
         "Компрометация через [Взлом] личных данных с последующим шантажом"),
    ],
    "supply_dispute": [
        ("Перехват груза через силовое вмешательство и [Бой]",
         "Дипломатическое давление через [Переговоры] с альтернативными поставщиками"),
    ],
    "labor_dispute": [
        ("Поддержка стачечников через [Лидерство] и публичные выступления",
         ("Саботаж производства через [Скрытность] для давления на руководство")),
    ],
    "audit": [
        ("Заказ независимого аудита через [Переговоры] с конкурирующей фирмой",
         "Утечка финансовых документов через [Взлом] и публичный скандал"),
    ],
    "default": [
        ("Силовой путь: прямое вмешательство и [Бой]",
         "Технический путь: [Взлом] систем и удалённый саботаж"),
        ("Социальный путь: [Переговоры] с ключевыми фигурами"),
    ],
}


def _stable_id(prefix: str, *parts: str) -> str:
    """Генерирует стабильный ID на основе содержимого."""
    h = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


class ContractGenerator:
    """Конвертирует plot_hooks фракций в активные контракты для игрока."""

    def __init__(self, kb_files: Dict[str, Any]):
        self.kb = kb_files
        self._factions: List[Dict] = []
        self._factions_by_region: Dict[str, List[Dict]] = defaultdict(list)
        self._load_factions()

    def _load_factions(self) -> None:
        factions_doc = self.kb.get("FACTIONS_MASTER.json") or {}
        self._factions = factions_doc.get("factions", [])

    @staticmethod
    def _normalize_region(region: str) -> str:
        return (region or "").lower().strip()

    def _factions_for_location(self, location: Optional[Dict]) -> List[Dict]:
        """Возвращает фракции текущего региона (по influence_region)."""
        if not location:
            return []
        planet = (location.get("planet") or "").lower()
        city = (location.get("city") or "").lower()
        district = (location.get("district") or "").lower()

        # 1) Точное совпадение по district
        for f in self._factions:
            r = self._normalize_region(f.get("influence_region", ""))
            if r and (district in r or r in district):
                yield f
                continue
        # 2) По city
        for f in self._factions:
            r = self._normalize_region(f.get("influence_region", ""))
            if r and (city in r or r in city):
                yield f
                continue
        # 3) По planet
        for f in self._factions:
            r = self._normalize_region(f.get("influence_region", ""))
            if r and (planet in r or r in planet):
                yield f

    def _paths_for_hook(self, hook_type: str) -> List[tuple]:
        """Возвращает ≥2 альтернативных пути решения (Dual-Path Requirement)."""
        return HOOK_TYPE_PATHS.get(hook_type, HOOK_TYPE_PATHS["default"])

    def _reward_for_tier(self, player_tier: int) -> tuple:
        rng = TIER_REWARD_RANGES.get(min(player_tier, 7), TIER_REWARD_RANGES[7])
        credits = random.randint(rng[0], rng[1])
        xp = TIER_XP.get(min(player_tier, 7), TIER_XP[7])
        return credits, xp

    def deterministic_reward(self, faction_id: str, hook_id: str,
                             player_tier: int) -> tuple:
        """Phase 3 final close: детерминированная награда для (faction, hook, tier).

        В отличие от _reward_for_tier() (которай использует глобальный
        random и пересчитывает награду при каждом вызове get_available_contracts),
        эта функция даёт СТАБИЛЬНУЮ награду для конкретной пары
        (faction_id, hook_id, tier). Используется при accept_contract,
        чтобы награда не менялась между запросами available и accept.
        """
        rng = TIER_REWARD_RANGES.get(min(player_tier, 7), TIER_REWARD_RANGES[7])
        # Детерминированный seed через md5 от стабильного ключа
        seed_str = f"{faction_id}|{hook_id}|{player_tier}"
        h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)
        credits = rng[0] + (h % (rng[1] - rng[0] + 1))
        xp = TIER_XP.get(min(player_tier, 7), TIER_XP[7])
        return credits, xp

    def _build_stages(self, hook: Dict, faction_name: str) -> List[Dict]:
        """Генерирует 2-3 этапа контракта (research → action → resolution)."""
        hook_desc = hook.get("description", "Задание").strip()
        return [
            {"id": "stage_1_research", "label": "Разведка", "description": f"Собрать информацию о ситуации ({hook_desc[:60]}...)"},
            {"id": "stage_2_action", "label": "Действие", "description": f"Выполнить основную задачу для {faction_name}"},
            {"id": "stage_3_resolution", "label": "Отчёт", "description": f"Доложить о результатах {faction_name}"},
        ]

    def _build_requirements(self, hook_type: str) -> Dict:
        """Минимальные требования (стат. скиллы) на основе типа хука."""
        requirements = {
            "ethical_debate": {"skills": ["investigation"], "min_reputation": 10},
            "scandal": {"skills": ["investigation", "stealth"], "min_reputation": 5},
            "secret_project": {"skills": ["stealth", "hacking"], "min_reputation": 0},
            "discovery": {"skills": ["survival", "science"], "min_reputation": 0},
            "recruitment": {"skills": ["negotiation"], "min_reputation": 15},
            "supply_dispute": {"skills": ["negotiation", "leadership"], "min_reputation": 10},
            "labor_dispute": {"skills": ["leadership", "negotiation"], "min_reputation": 5},
            "audit": {"skills": ["investigation"], "min_reputation": 20},
        }
        return requirements.get(hook_type, {"skills": [], "min_reputation": 0})

    def get_available_contracts(self, location: Optional[Dict], player_tier: int) -> List[Dict]:
        """Возвращает список активных контрактов для текущей локации и тира."""
        contracts = []
        for faction in self._factions_for_location(location):
            for hook in (faction.get("plot_hooks") or []):
                paths = self._paths_for_hook(hook.get("type", "default"))
                if len(paths) < 2:
                    # Если для hook_type нет ≥2 путей, дополняем из default
                    paths = HOOK_TYPE_PATHS["default"][:2]
                credits, xp = self.deterministic_reward(
                    faction.get("id", ""), hook.get("id", ""), player_tier)
                contract = {
                    "id": _stable_id("contract", faction.get("id", ""), hook.get("id", ""), str(player_tier)),
                    "title": f"{hook.get('type', 'mission').replace('_', ' ').title()}: {faction.get('name', 'Unknown')}",
                    "description": hook.get("description", ""),
                    "giver": faction.get("name", "Unknown"),
                    "type": hook.get("type", "default"),
                    "reward_credits": credits,
                    "reward_xp": xp,
                    "stages": self._build_stages(hook, faction.get("name", "Unknown")),
                    "requirements": self._build_requirements(hook.get("type", "default")),
                    "paths": [{"id": f"path_{i}", "label": f"Вариант {i+1}", "description": desc} for i, desc in enumerate(paths)],
                }
                contracts.append(contract)
        return contracts
