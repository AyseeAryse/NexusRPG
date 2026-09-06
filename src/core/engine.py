"""
Game Engine - Core game state, mechanics, AI GM orchestration.
"""
import json
import os
import random
import re
import time
import uuid
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from src import config
from src.ai import AIConnector, KnowledgeBase
from src.content import ORIGINS, FORMATIVE_YEARS, SPECIALIZATIONS
from src.content.v4_legacy import (
    get_all_origins_v4, get_all_formative_years_v4, get_all_specializations_v4,
)
from src.content.v3_legacy import get_all_shop_items_v3
from src.world import WorldSimulator, NPCRegistry, SPEECH_STYLES, GalaxyMap
from src.systems import (QuestTracker, FactionSystem, PsychologySystem,
                          PerkSystem, LevelUpSystem, CraftingSystem,
                          LocationEvents)
from src.world.procedural import ProceduralQuestGenerator, WorldTicker, ConsequenceTracker
from src.world.world_tick_service import WorldTickService
from src.ai.system_prompt_service import SystemPromptService
from src.systems.player_action_service import PlayerActionService
from src.world.player_tiers import compute_player_tier, compute_net_worth, TIER_NAMES_RU
from src.systems.subsystems import HackingSystem, InvestigationSystem, CompanionSystem, ShipSystem, PropertySystem
from src.systems.subsystems import HackingSystem, InvestigationSystem, CompanionSystem, ShipSystem, PropertySystem
from src.systems.profession_abilities import ProfessionAbilityManager
# V5: Quest chains, companions, unique NPCs, auto-reputation, world effects
from src.systems.quests import QUEST_CHAINS, get_available_chains, get_chain_stage
from src.systems.companions import COMPANIONS, get_available_companions, get_companion_by_id, get_loyalty_level, get_companion_combat_bonus
from src.content.v5_legacy import (UNIQUE_NPCS, WorldEffectsManager,
    calculate_auto_reputation, apply_reputation_changes, get_reputation_summary)
# V6: Hard mechanics — buy/sell, travel, property income, conversation management
from src.systems.expenses import ExpenseCycle
from src.systems.mechanics import (ShopMechanics, TravelSystem, PropertyIncomeManager,
    ConversationManager, detect_mechanical_action)
# V7: Combat engine, fail-forward, level up, subsystem triggers
from src.systems.combat import (CombatEngine, pick_enemies_for_encounter, apply_defeat,
    process_xp_gain, detect_subsystem_trigger, _attr_points_for_level)


# ══════════ BALANCE CONSTANTS ══════════
SKILL_CAPS = {
    # level_range: (max_skill, max_attribute)
    (1, 3): (4, 7),
    (4, 6): (6, 8),
    (7, 9): (8, 9),
    (10, 999): (10, 10),
}

PLAYER_TIERS = {
    # (min_credits, min_reputation) -> tier
    0: {"name": "Никто", "credits_min": 0, "event_role": "Свидетель, жертва обстоятельств"},
    1: {"name": "Местная известность", "credits_min": 50000, "event_role": "Мелкий участник, исполнитель"},
    2: {"name": "Региональное влияние", "credits_min": 500000, "event_role": "Значимый участник, может повлиять на исход"},
    3: {"name": "Системное влияние", "credits_min": 5000000, "event_role": "Ключевая фигура, может инициировать события"},
}

DC_TABLE = {
    "trivial": 6, "easy": 8, "medium": 10, "hard": 12,
    "very_hard": 14, "heroic": 16, "legendary": 18, "impossible": 20,
}

ORIGIN_BALANCE_BUDGET = {
    "обычное": {"attr_max": 3, "skill_max": 4},
    "необычное": {"attr_max": 3, "skill_max": 4},
    "редкое": {"attr_max": 3, "skill_max": 4},
    "легендарное": {"attr_max": 4, "skill_max": 5},
}


def get_skill_cap(level: int) -> tuple:
    """Returns (max_skill, max_attribute) for given character level."""
    for (lo, hi), caps in SKILL_CAPS.items():
        if lo <= level <= hi:
            return caps
    return (10, 10)


def get_player_tier(credits: int) -> int:
    """Returns player influence tier (0-3) based on credits."""
    tier = 0
    for t, info in PLAYER_TIERS.items():
        if credits >= info["credits_min"]:
            tier = t
    return tier


class DiceRoller:
    @staticmethod
    def roll(dice_str: str) -> Tuple[int, List[int]]:
        import re
        match = re.match(r"(\d+)d(\d+)([+-]\d+)?", dice_str.lower().strip())
        if not match: return (0, [])
        num, sides = int(match.group(1)), int(match.group(2))
        mod = int(match.group(3)) if match.group(3) else 0
        rolls = [random.randint(1, sides) for _ in range(num)]
        return (sum(rolls) + mod, rolls)

    @staticmethod
    def skill_check(skill_level: int, attribute_value: int, difficulty: int = 10) -> Dict:
        # Balanced formula: attr 5→0, 6→1, 7→1, 8→2, 9→2, 10→3
        attr_mod = (attribute_value - 4) // 2
        total_bonus = skill_level + attr_mod
        roll_total, rolls = DiceRoller.roll("2d6")
        result = roll_total + total_bonus
        is_crit_s = rolls == [6, 6]
        is_crit_f = rolls == [1, 1]
        success = (result >= difficulty or is_crit_s) and not is_crit_f
        margin = result - difficulty
        if is_crit_s: quality = "critical_success"
        elif is_crit_f: quality = "critical_failure"
        elif margin >= 5: quality = "great_success"
        elif margin >= 0: quality = "success"
        elif margin >= -4: quality = "failure"
        else: quality = "bad_failure"
        return {
            "rolls": rolls, "roll_total": roll_total, "bonus": total_bonus,
            "result": result, "difficulty": difficulty, "success": success,
            "margin": margin, "quality": quality,
        }


class GameState:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.character: Dict = {}
        self.current_location: Dict = {
            "planet": "Земля", "city": "Нью-Токио",
            "district": "Индустриальный коридор", "place": ""
        }
        self.game_time: Dict = {"year": 2387, "month": 3, "day": 15, "hour": 8, "minute": 0}
        self.active_quests: List[Dict] = []
        self.completed_quests: List[Dict] = []
        self.inventory: List[Dict] = []
        self.relationships: Dict[str, Dict] = {}
        self.faction_reputation: Dict[str, int] = {}
        self.fame: int = 0
        self.in_combat: bool = False
        self.combat_state: Dict = {}
        self.conversation_history: List[Dict] = []
        self.max_history = 30
        self.session_events: List[Dict] = []
        self.phase: str = "menu"
        self.world_sim: WorldSimulator = WorldSimulator()
        self.world_context: Dict = {}  # latest world tick results
        self.npc_registry: NPCRegistry = NPCRegistry()
        # Phase 26: tone profile (None until build_character_tone runs)
        self.tone_profile = None

    def to_dict(self) -> Dict:
        from src.core.tone_model import ToneProfile
        return {
            "id": self.id, "created_at": self.created_at,
            "updated_at": datetime.now().isoformat(),
            "character": self.character,
            "current_location": self.current_location,
            "game_time": self.game_time,
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,
            "inventory": self.inventory,
            "relationships": self.relationships,
            "faction_reputation": self.faction_reputation,
            "in_combat": self.in_combat,
            "combat_state": self.combat_state,
            "conversation_history": self.conversation_history[-self.max_history:],
            "session_events": self.session_events[-50:],
            "phase": self.phase,
            "world_sim": self.world_sim.to_dict(),
            "npc_registry": self.npc_registry.to_dict(),
            # Phase 26: tone profile (ToneProfile.to_dict() or None)
            "tone_profile": self.tone_profile.to_dict() if self.tone_profile else None,
            # Subsystem state — persisted since v5.0
            "_subsystems": {},  # placeholder, filled by GameEngine.save_game()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        from src.core.tone_model import ToneProfile
        s = cls()
        for k in ['id','created_at','character','current_location','game_time',
                   'active_quests','completed_quests','inventory','relationships',
                   'faction_reputation','in_combat','combat_state',
                   'conversation_history','session_events','phase']:
            if k in data:
                setattr(s, k, data[k])
        if 'world_sim' in data:
            s.world_sim = WorldSimulator.from_dict(data['world_sim'])
        if 'npc_registry' in data:
            s.npc_registry = NPCRegistry.from_dict(data['npc_registry'])
        # Phase 26: восстановление tone_profile из сейва
        if 'tone_profile' in data and data['tone_profile']:
            try:
                s.tone_profile = ToneProfile.from_dict(data['tone_profile'])
            except Exception as e:
                print(f"[GameState] tone_profile restore failed: {e}")
                s.tone_profile = None
        return s


class GameEngine:
    def __init__(self, data_dir=None, saves_dir=None, db_dir=None):
        self.data_dir = data_dir or config.GAME_DATA_DIR
        self.saves_dir = saves_dir or config.SAVES_DIR
        self.db_dir = db_dir or config.DATABASE_DIR
        self.kb = KnowledgeBase(self.data_dir, self.db_dir)
        self.ai = AIConnector()
        self.dice = DiceRoller()
        self.state = GameState()
        self.galaxy_map = GalaxyMap()
        # Phase 3 P0 fix: загрузить TRADE_ROUTES_MASTER.json в galaxy_map
        # (конвертирует start_point/end_point → planet routes)
        # Маскировка запрещена (Phase 3 prep) — сбой загрузки маршрутов падает с трейсбеком.
        routes_data = self.kb.get_file("TRADE_ROUTES_MASTER.json") or self.kb.get_file("TRADE_ROUTES_MASTER")
        if routes_data:
            self.galaxy_map.load_routes_from_kb(routes_data)
        # Procedural systems
        self.quest_generator = ProceduralQuestGenerator()
        self.world_ticker = WorldTicker()
        self.consequences = ConsequenceTracker()
        # Deep gameplay subsystems
        self.hacking = HackingSystem()
        self.investigation = InvestigationSystem()
        self.companions = CompanionSystem()
        self.ship = ShipSystem()
        self.property = PropertySystem()
        # V5: World effects manager, companion/quest chain state
        self.world_effects = WorldEffectsManager()
        self.active_companions: list = []  # [{id, loyalty, recruited_turn}]
        self.property_income = PropertyIncomeManager()
        self.expenses = ExpenseCycle()
        self.combat_engine = CombatEngine()  # V7: Tactical combat
        self.profession_abilities = ProfessionAbilityManager()
        # Phase 3: Living World — межфракционные конфликты + контракты из plot_hooks
        from src.world.faction_conflict_sim import FactionConflictSimulator
        from src.systems.contract_generator import ContractGenerator
        self.faction_sim = FactionConflictSimulator(self.kb.files if hasattr(self.kb, "files") else {})
        self.contract_gen = ContractGenerator(self.kb.files if hasattr(self.kb, "files") else {})
        self.active_chain: dict = {}  # {chain_id, current_stage}
        self.completed_chains: list = []
        # Phase 26: Tone Engine + SystemPromptBuilder (Step 4 интеграции)
        from src.systems.tone_engine import ToneEngine
        from src.ai.prompt_builder import SystemPromptBuilder
        self.tone_engine = ToneEngine(self.kb.files if hasattr(self.kb, "files") else {})
        self.prompt_builder = SystemPromptBuilder()
        self.state.tone_profile = None  # populated by build_character_tone()
        os.makedirs(self.saves_dir, exist_ok=True)
        # Cache creation data
        self._creation_data = None
        # Phase 30: world tick вынесен в сервис (DI — объекты создаются выше,
        # сервис получает только ссылки). GameEngine остаётся владельцем.
        self.world_tick_service = WorldTickService(
            state=self.state,
            world_effects=self.world_effects,
            world_ticker=self.world_ticker,
            consequences=self.consequences,
            faction_sim=self.faction_sim,
            property_income=self.property_income,
            property=self.property,
            expenses=self.expenses,
            get_player_tier=self.get_player_influence_tier,
        )
        # Phase 30 шаг 2: сборка системного промпта вынесена в SystemPromptService
        # (DI — ссылки на уже созданные объекты).
        self.system_prompt_service = SystemPromptService(
            state=self.state,
            kb=self.kb,
            combat_engine=self.combat_engine,
            galaxy_map=self.galaxy_map,
            hacking=self.hacking,
            investigation=self.investigation,
            companions=self.companions,
            ship=self.ship,
            property=self.property,
            world_effects=self.world_effects,
            get_player_tier=self.get_player_influence_tier,
            format_game_time=self._format_game_time,
        )
        # Phase 30 шаг 3: оркестрация хода игрока вынесена в PlayerActionService.
        # Внутренняя логика combat/mechanical/subsystem-триггеров и т.д. остаётся
        # в engine.py как callback-методы — отдельный долг.
        self.player_action_service = PlayerActionService(
            state=self.state,
            get_ai=lambda: self.ai,
            prompt_builder=self.prompt_builder,
            combat_engine=self.combat_engine,
            profession_abilities=self.profession_abilities,
            quest_generator=self.quest_generator,
            property_income=self.property_income,
            property=self.property,
            world_effects=self.world_effects,
            world_tick_service=self.world_tick_service,
            process_combat_turn=self._process_combat_turn,
            handle_subsystem_trigger=self._handle_subsystem_trigger,
            check_mechanical_action=self._check_mechanical_action,
            handle_mechanical_action=self._handle_mechanical_action,
            parse_ai_response=self._parse_ai_response,
            get_client_state=self._get_client_state,
            advance_time=self._advance_time,
            planet_hook_factions=self._planet_hook_factions,
            get_active_chain=lambda: self.active_chain,
            get_completed_chains=lambda: self.completed_chains,
        )
        print(f"[Engine] Init. Data: {len(self.kb.files)} files.")

    # ========== CHARACTER CREATION ==========

    def get_creation_data(self) -> Dict:
        """Return full character creation data for the UI."""
        if self._creation_data:
            return self._creation_data

        data = {
            "origins": get_all_origins_v4(),
            "formative_years": get_all_formative_years_v4(),
            "specializations": get_all_specializations_v4(),
            "attributes": [
                {"id": "strength", "name": "Сила", "abbr": "СИЛ", "desc": "Физическая мощь"},
                {"id": "dexterity", "name": "Ловкость", "abbr": "ЛОВ", "desc": "Координация и рефлексы тела"},
                {"id": "intelligence", "name": "Интеллект", "abbr": "ИНТ", "desc": "Ум и обучаемость"},
                {"id": "charisma", "name": "Харизма", "abbr": "ХАР", "desc": "Обаяние и лидерство"},
                {"id": "endurance", "name": "Выносливость", "abbr": "ВЫН", "desc": "Стойкость и здоровье"},
                {"id": "willpower", "name": "Воля", "abbr": "ВОЛ", "desc": "Психическая устойчивость"},
                {"id": "reflexes", "name": "Рефлексы", "abbr": "РЕФ", "desc": "Скорость реакции"},
                {"id": "tech_empathy", "name": "Тех-Эмпатия", "abbr": "ТЕХ", "desc": "Связь с технологиями"},
            ],
            "skills": [
                "hacking", "piloting", "negotiation", "combat", "stealth",
                "technology", "medicine", "engineering", "education", "criminal",
                "law", "biology", "survival", "diplomacy", "bureaucracy"
            ],
            "skill_names": {
                "hacking": "Хакинг", "piloting": "Пилотирование", "negotiation": "Переговоры",
                "combat": "Бой", "stealth": "Скрытность", "technology": "Технологии",
                "medicine": "Медицина", "engineering": "Инженерия", "education": "Образование",
                "criminal": "Криминал", "law": "Право", "biology": "Биология",
                "survival": "Выживание", "diplomacy": "Дипломатия", "bureaucracy": "Бюрократия"
            },
            "age_ranges": [
                {"id": "young", "label": "Молодой (16-25)", "min": 16, "max": 25,
                 "effects": {"dexterity": 1, "endurance": 1, "intelligence": -1}},
                {"id": "adult", "label": "Взрослый (26-45)", "min": 26, "max": 45,
                 "effects": {}},
                {"id": "mature", "label": "Зрелый (46-65)", "min": 46, "max": 65,
                 "effects": {"intelligence": 1, "willpower": 1, "dexterity": -1}},
                {"id": "elder", "label": "Пожилой (66-80)", "min": 66, "max": 80,
                 "effects": {"willpower": 2, "intelligence": 1, "endurance": -2}},
            ],
            "presets": self.get_presets(),
            "point_budget": {"attributes": 40, "attr_min": 2, "attr_max": 10, "attr_base": 5,
                            "skills": 10, "skill_min": 0, "skill_max": 5},
        }

        self._creation_data = data
        return data

    def get_presets(self) -> List[Dict]:
        return self.kb.get_character_presets()

    def create_character_from_preset(self, preset_id: str) -> Dict:
        presets = self.get_presets()
        preset = next((p for p in presets if p.get("id") == preset_id), None)
        if not preset:
            return {"error": f"Пресет {preset_id} не найден"}

        stats = preset.get("final_stats", {})
        attrs = stats.get("attributes", {})
        skills = stats.get("skills", {})
        resources = stats.get("starting_resources", {})
        derived = self._compute_derived_stats(attrs, skills)

        # Phase 27 R2: новая игра = чистое состояние. Без сброса инвентарь
        # предыдущей сессии либо дублируется, либо «исчезает» после отката сейва.
        self.state.inventory = []
        self.state.active_quests = []
        self.state.completed_quests = []

        self.state.character = {
            "name": "", "preset_id": preset_id,
            "preset_name": preset["name"],
            "description": preset.get("description", ""),
            "origin": preset.get("lifepath", {}).get("origin", ""),
            "origin_name": preset.get("lifepath", {}).get("origin_name", ""),
            "specialization": preset.get("lifepath", {}).get("specialization", ""),
            "age": preset.get("lifepath", {}).get("age", 30),
            "level": 1, "xp": 0, "xp_next": 1000,
            "attributes": attrs, "skills": skills,
            "derived": derived,
            "current_hp": derived["health_points"],
            "current_sanity": derived["sanity_points"],
            "credits": resources.get("credits", 50000),
            "attr_bonuses": {}, "unspent_attribute_points": 0,
            "roleplay_notes": preset.get("roleplay_notes", []),
            "story_hooks": preset.get("story_hooks", []),
        }
        self.state.faction_reputation = resources.get("reputation", {})
        # Phase 27 D5: пресет обязан выдавать стартовый набор снаряжения.
        # Пресет → специализация (equipment[]) → военный бонус-набор.
        self._grant_starting_equipment(
            spec_id=preset.get("lifepath", {}).get("specialization", ""),
            origin_id=preset.get("lifepath", {}).get("origin", ""),
        )
        self._set_starting_location(preset.get("lifepath", {}).get("origin", ""))
        # Phase 31 H1 + H1-блокер1: preset-путь строит ToneProfile. Без try/except:
        # если build_character_tone падает — пусть падает с трейсбеком здесь
        # (прецедент Phase 2.1 «демонтаж маскировки»), а не молча оставляет
        # tone_profile=None для скрытого краша apply_scene_context в другом месте.
        self.state.tone_profile = self.tone_engine.build_character_tone(self.state.character)
        return self.state.character

    # Phase 28 F2: архетипные стартовые наборы. Ключи — маркеры в id специализации
    # или происхождения (без префиксов SPEC_/ORIGIN_). Каждому архетипу — узнаваемый
    # набор: ни один пресет не должен начинать с пустым инвентарём.
    ARCHETYPE_KITS: Dict[str, List[str]] = {
        # ── Учёный / Медик / Техник ──
        "research": [
            "Датапад исследователя",            # планшет с базой данных
            "Полевой биосканер",
            "Лёгкий лабораторный комбинезон",
            "Стимпак", "Стимпак",               # набор стимуляторов (2 шт.)
            "Инъектор антидота",
        ],
        "science": [
            "Датапад исследователя", "Полевой биосканер",
            "Лёгкий лабораторный комбинезон", "Стимпак", "Стимпак", "Инъектор антидота",
        ],
        "medic": [
            "Полевой медкит", "Полевой биосканер",
            "Лёгкий лабораторный комбинезон", "Стимпак", "Стимпак", "Инъектор антидота",
        ],
        "medic_combat": [
            "Полевой медкит", "Полевой биосканер",
            "Лёгкий лабораторный комбинезон", "Стимпак", "Стимпак", "Инъектор антидота",
        ],
        "medic_combat_trauma": [
            "Полевой медкит", "Полевой биосканер",
            "Лёгкий лабораторный комбинезон", "Стимпак", "Стимпак", "Инъектор антидота",
        ],
        "engineer": [
            "Датапад инженера", "Мультитул", "Ремонтный набор электроники", "Стимпак",
        ],
        "tech": [
            "Датапад исследователя", "Полевой биосканер",
            "Лёгкий лабораторный комбинезон", "Стимпак", "Стимпак", "Инъектор антидота",
        ],
        "tech_archaeologist": [
            "Датапад исследователя", "Мультитул", "Лёгкий лабораторный комбинезон", "Стимпак",
        ],
        # ── Корпорат / Дипломат ──
        "corporate": [
            "Стильный костюм с кевларовой нитью",
            "Премиальный коммуникатор",
            "Кредитный чип",
            "Карманный шокер",
        ],
        "negotiator": [
            "Стильный костюм с кевларовой нитью",
            "Премиальный коммуникатор",
            "Кредитный чип",
            "Карманный шокер",
        ],
        "diplomat": [
            "Стильный костюм с кевларовой нитью",
            "Премиальный коммуникатор",
            "Кредитный чип",
            "Карманный шокер",
        ],
        "fixer": [
            "Стильный костюм с кевларовой нитью",
            "Премиальный коммуникатор", "Кредитный чип", "Карманный шокер",
        ],
        # ── Бродяга / Уличный вор ──
        "slums": [
            "Самодельный нож",
            "Скрытые отмычки",
            "Декодер замков",
            "Куртка с капюшоном",
            "Синтетические сигареты",
        ],
        "smuggler": [
            "Самодельный нож", "Скрытые отмычки",
            "Куртка с капюшоном", "Синтетические сигареты",
        ],
        "criminal": [
            "Самодельный нож", "Скрытые отмычки",
            "Куртка с капюшоном", "Синтетические сигареты",
        ],
        "street": [
            "Самодельный нож", "Скрытые отмычки",
            "Куртка с капюшоном", "Синтетические сигареты",
        ],
    }

    def _grant_starting_equipment(self, spec_id: str = "", origin_id: str = "") -> None:
        """Phase 27 D5 + Phase 28 F2: стартовая экипировка для ВСЕХ архетипов.
        Источники: архетипный набор → специализация → происхождение → военный бонус.
        Ни один пресет не должен начинать с пустым инвентарём."""
        creation = self.get_creation_data()

        # F2-фикс: spec_id приходит без префикса ("SOLDIER"), в каталоге — "SPEC_SOLDIER".
        # Сравниваем по нормализованному хвосту.
        def _spec_match(s_id: str) -> bool:
            return s_id == spec_id or s_id.endswith(f"_{spec_id}")

        spec_data = next((s for s in creation["specializations"] if _spec_match(s["id"])), None)
        origin_data = next((o for o in creation["origins"]
                            if o["id"] == origin_id
                            or o["id"] == f"ORIGIN_{origin_id}"
                            or o["id"].endswith(f"_{origin_id}")), None)

        items = []

        # 1) Архетипный набор по маркерам (F2)
        hay = f"{spec_id or ''}|{origin_id or ''}".upper()
        for marker, kit in self.ARCHETYPE_KITS.items():
            if marker.upper() in hay:
                for kit_item in kit:
                    if kit_item not in items:
                        items.append(kit_item)
                break  # первый совпавший архетип — самый специфичный порядок не гарантирован, но киты не пересекаются

        # 2) Специализационное оборудование
        if spec_data and spec_data.get("equipment"):
            for eq in spec_data["equipment"]:
                if eq not in items:
                    items.append(eq)

        # 3) Происхождение (equipment[])
        if origin_data and origin_data.get("equipment"):
            for eq in origin_data["equipment"]:
                if eq not in items:
                    items.append(eq)

        # 4) Военный бонус-набор (Phase 27 D5)
        military_markers = ("SOLDIER", "MARINE", "CQB", "MILITARY", "ORDNANCE", "SNIPER")
        is_military = any(m in (spec_id or "").upper() or m in (origin_id or "").upper()
                          for m in military_markers)
        if is_military:
            military_kit = [
                "Пистолет «Ржавый аргумент»",   # табельный пистолет (WEAPON_011)
                "Скафандр 'Глубокий космос' EVA-12",  # армейская средняя броня (ARMOR_003)
                "Стимпак",                       # полевой стимулятор (CONSUMABLE_001B)
                "Боевой стимулятор 'Адреналин-X'",  # боевой стимулятор (CONSUMABLE_002B)
                "Армейский нож К-17",            # штык-нож (WEAPON_014)
                "Полевой коммуникатор",          # связь отделения
            ]
            for kit_item in military_kit:
                if kit_item not in items:
                    items.append(kit_item)

        # 5) Гарантия непустого старта: если после всего инвентарь пуст — базовый набор выживания
        if not items:
            items = ["Стимпак", "Полевой коммуникатор", "Мультитул"]

        existing = {i.get("name") for i in self.state.inventory}
        for eq in items:
            if eq not in existing:
                self.state.inventory.append({"name": eq, "qty": 1, "type": "equipment"})

    def create_custom_character(self, data: Dict) -> Dict:
        """Create character from full custom creation data."""
        name = data.get("name", "Безымянный")
        age = data.get("age", 30)
        origin_id = data.get("origin", "ORIGIN_EARTH_SLUMS")
        formative_id = data.get("formative_years", "")
        spec_id = data.get("specialization", "SPEC_HACKER")
        backstory = data.get("backstory", "")

        # Base attributes from data or defaults
        attrs = data.get("attributes", {
            "strength": 5, "dexterity": 5, "intelligence": 5, "charisma": 5,
            "endurance": 5, "willpower": 5, "reflexes": 5, "tech_empathy": 5,
        })
        skills = data.get("skills", {})
        credits = data.get("credits", 50000)

        # Phase 27 R2: чистое состояние при новой игре (см. create_character_from_preset)
        self.state.inventory = []
        self.state.active_quests = []
        self.state.completed_quests = []

        # Apply origin modifiers
        creation = self.get_creation_data()
        origin_data = next((o for o in creation["origins"] if o["id"] == origin_id), None)
        if origin_data:
            for ak, av in origin_data.get("attr_mods", {}).items():
                if ak in attrs: attrs[ak] = max(1, attrs[ak] + av)
            for sk, sv in origin_data.get("skill_mods", {}).items():
                skills[sk] = skills.get(sk, 0) + sv
            credits = origin_data.get("credits", credits)

        # Apply formative years modifiers
        fy_data = next((f for f in creation["formative_years"] if f["id"] == formative_id), None)
        if fy_data:
            for ak, av in fy_data.get("attr_mods", {}).items():
                if ak in attrs: attrs[ak] = max(1, attrs[ak] + av)
            for sk, sv in fy_data.get("skill_mods", {}).items():
                skills[sk] = skills.get(sk, 0) + sv

        # Apply specialization modifiers
        spec_data = next((s for s in creation["specializations"] if s["id"] == spec_id), None)
        spec_name = spec_data["name"] if spec_data else spec_id
        if spec_data:
            for sk, sv in spec_data.get("skill_mods", {}).items():
                skills[sk] = skills.get(sk, 0) + sv

        # Apply age modifiers
        for ar in creation["age_ranges"]:
            if ar["min"] <= age <= ar["max"]:
                for ak, av in ar.get("effects", {}).items():
                    if ak in attrs: attrs[ak] = max(1, attrs[ak] + av)
                break

        # Clean negative skills
        skills = {k: max(0, v) for k, v in skills.items() if v > 0}

        derived = self._compute_derived_stats(attrs, skills)

        origin_name = origin_data["name"] if origin_data else origin_id
        fy_name = fy_data["name"] if fy_data else formative_id

        self.state.character = {
            "name": name, "preset_id": "custom",
            "preset_name": spec_name,
            "description": backstory,
            "origin": origin_id, "origin_name": origin_name,
            "formative_years": formative_id, "formative_years_name": fy_name,
            "specialization": spec_id, "specialization_name": spec_name,
            "age": age, "level": 1, "xp": 0, "xp_next": 1000,
            "attributes": attrs, "skills": skills,
            "derived": derived,
            "current_hp": derived["health_points"],
            "current_sanity": derived["sanity_points"],
            "credits": credits,
            "attr_bonuses": {}, "unspent_attribute_points": 0,
            "roleplay_notes": [], "story_hooks": [],
            "starting_equipment": spec_data.get("equipment", []) if spec_data else [],
        }

        # Set starting inventory from equipment
        if spec_data and spec_data.get("equipment"):
            for eq in spec_data["equipment"]:
                self.state.inventory.append({"name": eq, "qty": 1, "type": "equipment"})
        # Фаза 18: origin тоже может давать стартовый предмет (equipment[])
        if origin_data and origin_data.get("equipment"):
            for eq in origin_data["equipment"]:
                self.state.inventory.append({"name": eq, "qty": 1, "type": "equipment"})

        self._set_starting_location(origin_id)
        # Фаза 24b C3: heat из Годов становления (после создания character dict)
        if fy_data and fy_data.get("heat_mods"):
            self.state.character["heat"] = self.state.character.get("heat", 0) + fy_data["heat_mods"]
        self._enforce_skill_caps()
        # Phase 26: build ToneProfile. Phase 31 H1-блокер1: маскирующий try/except
        # снят (прецедент Phase 2.1 «демонтаж маскировки») — сбой build_character_tone
        # обязан падать с трейсбеком здесь, а не оставлять tone_profile=None для
        # отложенного скрытого краша apply_scene_context.
        self.state.tone_profile = self.tone_engine.build_character_tone(self.state.character)
        return self.state.character

    def _compute_derived_stats(self, attrs: Dict, skills: Dict) -> Dict:
        end = attrs.get("endurance", 5)
        str_ = attrs.get("strength", 5)
        wil = attrs.get("willpower", 5)
        ref = attrs.get("reflexes", 5)
        dex = attrs.get("dexterity", 5)
        return {
            "health_points": (end + str_) * 5,
            "sanity_points": wil * 10,
            "initiative": ref + dex,
            "defense": dex + skills.get("stealth", 0) // 2,
            "carry_capacity": str_ * 10,
        }

    def _set_starting_location(self, origin: str):
        """Стартовая локация из данных origin (Фаза 23: поле starting_location).
        Фолбэк — старый keyword-match, если поле отсутствует."""
        origin_data = None
        try:
            creation = self.get_creation_data()
            origin_data = next((o for o in creation["origins"] if o["id"] == origin), None)
        except Exception:
            origin_data = None
        loc = (origin_data or {}).get("starting_location")
        if isinstance(loc, dict) and loc.get("planet"):
            self.state.current_location = {
                "planet": loc.get("planet", ""),
                "city": loc.get("city", ""),
                "district": loc.get("district", ""),
                "place": loc.get("place", ""),
            }
            return
        # ── legacy fallback ──
        o = origin.upper()
        if "EARTH" in o or "UNIQUE" in o:
            self.state.current_location = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор", "place": ""}
        elif "MARS" in o:
            self.state.current_location = {"planet": "Марс", "city": "Новый Бостон", "district": "Окружное кольцо", "place": ""}
        elif any(x in o for x in ["BELT","CERES","ASTEROID","VESTA","SALVAG","NOMAD","TRADER"]):
            self.state.current_location = {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Шахтёрский квартал", "place": ""}
        elif any(x in o for x in ["GANYMEDE","EUROPA","TITAN","JUPITER","OUTER"]):
            self.state.current_location = {"planet": "Ганимед", "city": "Станция Юпитер-Прайм", "district": "Торговые палубы", "place": ""}
        else:
            self.state.current_location = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор", "place": ""}

    # ========== GAME ACTIONS ==========

    def process_player_action(self, action: str) -> Dict:
        """Phase 30 шаг 3: оркестрация хода игрока вынесена в PlayerActionService.
        Сигнатура публичного API не изменилась; routes/gameplay.py не тронут."""
        return self.player_action_service.run(action)

    def universal_skill_check(self, character: Dict, skill_id: str,
                              difficulty: int = 10) -> Optional[Dict]:
        """Фаза 20b: универсальная проверка ЛЮБОГО навыка по id.
        Атрибут берётся из base_attribute (CHARACTER_SKILLS.json через KB).
        Канон: 2d6 + skill + (attr-4)//2 vs DC. None = навык неизвестен."""
        skills = character.get("skills", {})
        attrs = character.get("attributes", {})
        attr_bonuses = character.get("attr_bonuses", {})  # Phase 24c B5-3: implants отдельно
        sv = skills.get(skill_id, 0)
        # base_attribute из каталога навыков
        attr_name = None
        try:
            sk_file = self.kb.get_file("CHARACTER_SKILLS.json") or {}
            for s in sk_file.get("skills", []):
                if s.get("skill_id") == skill_id:
                    attr_name = s.get("base_attribute")
                    break
        except Exception:
            attr_name = None
        if not attr_name:
            return None
        av = attrs.get(attr_name, 5) + attr_bonuses.get(attr_name, 0)
        result = self.dice.skill_check(sv, av, difficulty)
        result["skill"] = skill_id
        result["attribute"] = attr_name
        return result


    def _check_mechanical_action(self, action: str) -> Optional[Dict]:
        """Detect skill checks from player action text. Real 2d6 + skill + attr vs DC."""
        action_lower = action.lower()

        # === EXPANDED TRIGGER TABLE ===
        # Format: list of trigger words → (skill, attribute, base_dc)
        SKILL_TRIGGERS = [
            # Hacking / Tech
            (["взломать", "хакнуть", "hack", "взлом", "подключиться к сети",
              "обойти защиту", "обойти систему", "проникнуть в систему", "перехватить сигнал",
              "расшифровать", "дешифровать", "подобрать пароль", "вскрыть терминал"],
             "hacking", "intelligence", 9),
            # Persuasion / Negotiation
            (["убедить", "уговорить", "договориться", "торговаться", "переговор",
              "торгуюсь", "предложить сделку", "уломать", "разжалобить", "мотивировать",
              "дипломатия", "успокоить", "уладить", "помирить", "польстить"],
             "negotiation", "charisma", 8),
            # Deception / Manipulation
            (["обмануть", "соврать", "блефовать", "ввести в заблуждение", "притвориться",
              "выдать себя за", "прикинуться", "подделать", "обман", "блеф", "манипулировать"],
             "criminal", "charisma", 9),
            # Stealth
            (["красться", "прятаться", "скрыться", "незаметно", "тихо пройти",
              "спрятаться", "затаиться", "stealth", "замаскироваться", "стелс",
              "проскользнуть", "прокрасться", "пролезть незаметно", "пробраться"],
             "stealth", "dexterity", 8),
            # Combat (melee)
            (["ударить", "атаковать", "врезать", "пробить", "бить кулаком",
              "сбить с ног", "схватить", "борьба", "рукопашн"],
             "combat", "strength", 8),
            # Combat (ranged)
            (["стрелять", "выстрелить", "прицелиться", "открыть огонь", "пальнуть",
              "снять прицелом", "обстрелять"],
             "combat", "dexterity", 8),
            # Medicine
            (["лечить", "перевязать", "оказать помощь", "остановить кровь", "реанимир",
              "ввести лекарство", "медпомощь", "операци", "хирург", "диагноз", "вылечить"],
             "medicine", "intelligence", 8),
            # Engineering / Repair
            (["чинить", "починить", "ремонт", "отремонтировать", "собрать", "разобрать",
              "перепаять", "перенастроить", "модифицировать", "улучшить", "инженер"],
             "engineering", "intelligence", 8),
            # Piloting
            (["пилотировать", "за штурвал", "управлять кораблём", "манёвр", "уклон",
              "посадить корабль", "взлететь", "сесть за руль", "лететь", "вести корабль"],
             "piloting", "reflexes", 8),
            # Investigation / Perception
            (["осмотреть", "обыскать", "исследовать", "изучить", "найти улик",
              "заметить", "внимательно посмотреть", "прислушаться", "понюхать",
              "проверить", "обследовать", "разведать", "высматривать", "разглядеть"],
             "education", "intelligence", 7),
            # Stealing / Pickpocket
            (["украсть", "стащить", "обчистить", "вытащить из кармана", "карманн",
              "своровать", "подрезать кошелёк", "взять без спросу", "слямзить"],
             "criminal", "dexterity", 9),
            # Interrogation / Interview
            (["допросить", "расспросить", "выведать", "выбить информацию", "надавить",
              "запугать", "угрожать", "шантажировать", "припугнуть", "устрашить"],
             "diplomacy", "charisma", 8),
            # Intimidation
            (["запугать", "угрожать", "шантажировать", "припугнуть", "устрашить",
              "надавить силой", "навести страх"],
             "combat", "charisma", 9),
            # Survival
            (["выживать", "развести костёр", "найти воду", "ориентироваться",
              "выживание", "спрятать следы", "найти путь", "следопыт"],
             "survival", "endurance", 7),
            # Technology
            (["проанализировать", "сканировать", "запрограммировать", "настроить прибор",
              "идентифицировать", "подключить", "технологи"],
             "technology", "intelligence", 7),
            # Lockpicking / Physical bypass
            (["вскрыть замок", "отмычка", "открыть дверь", "выломать", "взломать замок",
              "подобрать ключ", "открыть без ключа"],
             "criminal", "dexterity", 8),
            # Acrobatics / Athletics
            (["перепрыгнуть", "перелезть", "забраться", "карабкаться", "уклониться",
              "увернуться", "кувырок", "сальто", "акробат", "бежать", "спрыгнуть"],
             "survival", "dexterity", 7),
        ]

        # === CONTEXT-AWARE DIFFICULTY ===
        loc = self.state.current_location
        dist_data = self.galaxy_map.get_district(
            loc.get("planet",""), loc.get("city",""), loc.get("district",""))
        security = "medium"
        if dist_data:
            security = dist_data.get("security", "medium")

        # Security → DC modifier (softer: max +3)
        security_dc_mod = {
            "none": -2, "low": -1, "medium": 0, "high": +1, "very_high": +2, "maximum": +3
        }.get(security, 0)

        # Player level → DC scaling (slower: +1 every 4 levels, max +2)
        level = self.state.character.get("level", 1)
        level_dc_mod = min(level // 4, 2)

        for triggers, skill, attr, base_dc in SKILL_TRIGGERS:
            for trigger in triggers:
                if trigger in action_lower:
                    sv = self.state.character.get("skills", {}).get(skill, 0)
                    av = self.state.character.get("attributes", {}).get(attr, 5)

                    # Context-aware DC
                    dc = base_dc + level_dc_mod
                    # Security affects stealth, hacking, criminal checks
                    if skill in ("stealth", "hacking", "criminal"):
                        dc += security_dc_mod
                    # Фаза 20d: Бэкдор — одноразовое снижение DC следующего хакинг-чека
                    if skill == "hacking":
                        bd = getattr(self.state, "backdoor_dc_override", None)
                        if bd:
                            dc = min(dc, bd)
                            self.state.backdoor_dc_override = None

                    # Apply psychology modifiers
                    psych_mod = PsychologySystem.get_skill_modifier(self.state.character)
                    if skill in ("negotiation", "diplomacy"):
                        psych_mod = PsychologySystem.get_social_modifier(self.state.character)
                    sv = max(0, sv + psych_mod)

                    # Apply companion bonuses
                    comp_bonuses = self.get_companion_bonuses()
                    comp_bonus = comp_bonuses.get(skill, 0)
                    sv = sv + comp_bonus

                    # Apply implant bonuses
                    implant_bonus = self._get_implant_bonus(skill)
                    sv = sv + implant_bonus

                    result = self.dice.skill_check(sv, av, dc)
                    result["skill"] = skill
                    result["attribute"] = attr
                    result["trigger"] = trigger
                    if psych_mod != 0: result["psych_modifier"] = psych_mod
                    if comp_bonus != 0: result["companion_bonus"] = comp_bonus
                    if implant_bonus != 0: result["implant_bonus"] = implant_bonus
                    if security_dc_mod != 0: result["security_mod"] = security_dc_mod
                    return result
        return None

    def _get_implant_bonus(self, skill: str) -> int:
        """Get bonus from installed implants for a skill."""
        bonus = 0
        for item in self.state.inventory:
            if item.get("installed") and item.get("category") == "implants":
                for mod_skill, mod_val in item.get("skill_bonuses", {}).items():
                    if mod_skill == skill:
                        bonus += mod_val
        return bonus

    def _build_system_prompt(self, action: str, dice_result: Optional[Dict] = None,
                             mech_result: Optional[Dict] = None,
                             subsystem_result: Optional[Dict] = None) -> str:
        """Phase 30 шаг 2: сборка промпта вынесена в SystemPromptService.build().
        Сигнатура публичного API не изменилась."""
        return self.system_prompt_service.build(
            action=action,
            dice_result=dice_result,
            mech_result=mech_result,
            subsystem_result=subsystem_result,
            active_chain=self.active_chain,
            active_companions=self.active_companions,
        )

    def _handle_mechanical_action(self, mech: Dict) -> Dict:
        """Handle detected buy/sell/travel action with real state changes."""
        action_type = mech.get("type", "")
        target = mech.get("target", "")
        result = {"type": action_type}

        if action_type == "buy":
            # Get shop items for current location
            from src.content.v4_legacy import _game_time_to_hours
            event_mods = {}
            for cat in ["weapons", "armor", "implants", "gadgets", "consumables"]:
                mod = self.get_shop_price_modifier(cat)
                if mod != 1.0:
                    event_mods[cat] = mod
            shop_items = self.state.world_sim.get_shop_items(
                self.state.current_location,
                self.get_player_influence_tier()["tier"],
                event_mods or None
            )
            item = ShopMechanics.find_shop_item(shop_items, target)
            if item:
                buy_result = ShopMechanics.buy_item(
                    self.state.character, self.state.inventory, item
                )
                result.update(buy_result)
            else:
                result["error"] = f"Товар «{target}» не найден в магазине"
                # Suggest closest matches
                suggestions = [i["name"] for i in shop_items
                               if any(w in i["name"].lower() for w in target.lower().split())]
                if suggestions:
                    result["suggestions"] = suggestions[:3]

        elif action_type == "sell":
            sell_result = ShopMechanics.sell_item(
                self.state.character, self.state.inventory, target
            )
            result.update(sell_result)

        elif action_type == "travel":
            # Check if target is a planet name (with Russian case endings)
            target_lower = target.lower().strip()
            PLANET_NAMES = {
                "земл": "Земля", "марс": "Марс", "пояс": "Пояс астероидов",
                "церер": "Пояс астероидов", "ганимед": "Ганимед", "лун": "Луна",
                "юпитер": "Ганимед",
            }
            detected_planet = None
            for stem, planet_name in PLANET_NAMES.items():
                if target_lower.startswith(stem):
                    detected_planet = planet_name
                    break

            if detected_planet and detected_planet != self.state.current_location.get("planet"):
                # Interplanetary travel
                travel_result = TravelSystem.travel_interplanetary(
                    self.state.current_location, detected_planet,
                    self.ship, self.state.character
                )
                if travel_result.get("success"):
                    self.state.current_location = travel_result["new_location"]
                    self._apply_tone_to_current_location()
                    # Фаза 18 П.1: встреча с враждебным транспортом → запуск боя
                    enc = travel_result.get("encounter") or {}
                    if enc.get("type") == "combat_vehicle" and enc.get("vehicle_enemy"):
                        from src.systems.equipment_lookup import (
                            make_vehicle_enemy, armor_defense_bonus_for_inventory)
                        veh_enemy = make_vehicle_enemy(enc["vehicle_enemy"])
                        combat_state = self.combat_engine.start_combat(
                            self.state.character, [veh_enemy], [])
                        self.state.in_combat = True
                        self.state.character["_armor_defense_bonus"] = \
                            armor_defense_bonus_for_inventory(self.state.inventory)
                        travel_result["vehicle_combat_started"] = True
                    self._advance_time(minutes=travel_result.get("travel_minutes", 60))
                result.update(travel_result)
            else:
                # Local travel
                travel_result = TravelSystem.travel_local(
                    self.state.current_location, target, self.galaxy_map
                )
                if travel_result.get("success"):
                    self.state.current_location = travel_result["new_location"]
                elif travel_result.get("error") and detected_planet:
                    # Already on this planet, try district-level
                    pass  # return the error as-is
                result.update(travel_result)

        elif action_type == "travel_planet":
            travel_result = TravelSystem.travel_interplanetary(
                self.state.current_location, target,
                self.ship, self.state.character
            )
            if travel_result.get("success"):
                self.state.current_location = travel_result["new_location"]
                self._apply_tone_to_current_location()
                # Фаза 18 П.1: встреча с враждебным транспортом → запуск боя
                enc = travel_result.get("encounter") or {}
                if enc.get("type") == "combat_vehicle" and enc.get("vehicle_enemy"):
                    from src.systems.equipment_lookup import (
                        make_vehicle_enemy, armor_defense_bonus_for_inventory)
                    veh_enemy = make_vehicle_enemy(enc["vehicle_enemy"])
                    self.combat_engine.start_combat(
                        self.state.character, [veh_enemy], [])
                    self.state.in_combat = True
                    self.state.character["_armor_defense_bonus"] = \
                        armor_defense_bonus_for_inventory(self.state.inventory)
                    travel_result["vehicle_combat_started"] = True
                # Advance time for long travel
                self._advance_time(minutes=travel_result.get("travel_minutes", 60))
            result.update(travel_result)

        return result

    # ========== V7: COMBAT TURN HANDLER ==========

    def _process_combat_turn(self, action: str) -> Dict:
        """Handle a combat round when in_combat is True."""
        # Determine weapon damage from inventory (Фаза 17 A1: каталог TECH_EQUIPMENT)
        from src.systems.equipment_lookup import (weapon_damage_for_inventory,
                                                  armor_defense_bonus_for_inventory,
                                                  resolve_item)
        # Фаза 18: учёт зоны боя при выборе оружия (ожидаемый урон, не dice-потолок)
        current_zone = None
        if getattr(self, "combat_engine", None) and getattr(self.combat_engine, "in_combat", False):
            current_zone = self.combat_engine.combat.get("zone")
        weapon_dmg, _equipped_weapon = weapon_damage_for_inventory(
            self.state.inventory, current_zone=current_zone)
        self.state.character["_equipped_weapon_name"] = _equipped_weapon
        self.state.character["_armor_defense_bonus"] = armor_defense_bonus_for_inventory(self.state.inventory)
        self.state.character["_inventory_ref"] = self.state.inventory   # A3: для расходников

# (Фаза 18: имя оружия возвращается weapon_damage_for_inventory)

        # Run combat turn
        combat_state = self.combat_engine.player_turn(
            action, self.state.character, weapon_dmg
        )

        # Check combat end
        defeat_result = None
        victory_rewards = None
        narrative_suffix = ""

        if combat_state["status"] == "victory":
            rewards = self.combat_engine.get_combat_rewards()
            victory_rewards = rewards
            # Apply rewards
            self.state.character["credits"] = self.state.character.get("credits", 0) + rewards.get("credits", 0)
            level_up = process_xp_gain(self.state.character, rewards.get("xp", 0))
            if level_up:
                victory_rewards["level_up"] = level_up
            narrative_suffix = (f"\n\n🏆 **ПОБЕДА!** +{rewards['xp']} XP, +₡{rewards['credits']}"
                              f"{' 🌟 БЕЗУПРЕЧНО!' if rewards.get('flawless') else ''}")
            if level_up:
                narrative_suffix += f"\n⬆️ **УРОВЕНЬ {level_up['new_level']}!** +{level_up['skill_points']} очков навыков"
                if level_up.get('attribute_points', 0) > 0:
                    narrative_suffix += f" +{level_up['attribute_points']} очков атрибута"
            self.state.in_combat = False
            self.combat_engine.end_combat()

        elif combat_state["status"] == "defeat":
            defeat_result = apply_defeat(
                self.state.character, self.state.inventory,
                self.state.game_time, self.state.current_location
            )
            narrative_suffix = f"\n\n⚠️ **{defeat_result['name'].upper()}**\n{defeat_result['description']}"
            for change in defeat_result["changes"]:
                narrative_suffix += f"\n  • {change}"
            self.state.in_combat = False
            self.combat_engine.end_combat()

        elif combat_state["status"] == "fled":
            self.state.in_combat = False
            self.combat_engine.end_combat()
            narrative_suffix = "\n\n🏃 Вы сбежали из боя."

        # Build narrative from combat log
        log_text = "\n".join(combat_state["log"][-6:])
        narrative = f"**Раунд {combat_state['round']}**\n{log_text}{narrative_suffix}"

        # Add to conversation
        self.state.conversation_history.append({"role": "assistant", "content": narrative})
        self._advance_time(minutes=5)  # each combat round ~ 5 min

        return {
            "narrative": narrative,
            "combat_state": combat_state,
            "game_state": self._get_client_state(),
            "victory_rewards": victory_rewards,
            "defeat": defeat_result,
        }

    # ========== V7: SUBSYSTEM TRIGGER HANDLER ==========

    def _handle_subsystem_trigger(self, subsystem: Dict, action: str) -> Optional[Dict]:
        """Handle detected subsystem trigger (hacking/investigation/crafting/combat)."""
        sys_type = subsystem.get("system")

        if sys_type == "combat" and not self.combat_engine.in_combat:
            # Start tactical combat
            player_level = self.state.character.get("level", 1)
            # Determine difficulty from context
            difficulty = "normal"
            action_lower = action.lower()
            if any(w in action_lower for w in ["босс", "главар", "лидер"]):
                difficulty = "boss"
            elif any(w in action_lower for w in ["группа", "банда", "толпа"]):
                difficulty = "hard"
            elif any(w in action_lower for w in ["один", "часовой", "охранник"]):
                difficulty = "easy"

            enemies = pick_enemies_for_encounter(player_level, difficulty)

            # Get companion combat allies
            allies = []
            for comp_state in self.active_companions[:3]:
                comp_data = get_companion_by_id(comp_state["id"])
                if comp_data:
                    allies.append({
                        "name": comp_data.get("name", "Компаньон"),
                        "hp": 30, "max_hp": 30,
                        "combat_bonus": comp_data.get("combat_bonus", 2),
                        "skills": comp_data.get("skills", {}),
                    })

            # Фаза 17 A1: экипированная броня добавляется к защите на весь бой
            from src.systems.equipment_lookup import armor_defense_bonus_for_inventory
            self.state.character["_armor_defense_bonus"] = armor_defense_bonus_for_inventory(
                self.state.inventory)

            combat_state = self.combat_engine.start_combat(
                self.state.character, enemies, allies
            )
            self.state.in_combat = True

            # Build initial combat narrative
            enemy_desc = ", ".join(f"{e['name']} (HP:{e['hp']})" for e in enemies)
            narrative = (f"⚔️ **БОЙ!**\n\nПротивники: {enemy_desc}\n\n"
                        + "\n".join(combat_state["log"]))
            self.state.conversation_history.append({"role": "assistant", "content": narrative})

            return {
                "combat_started": True,
                "narrative": narrative,
                "combat_state": combat_state,
                "game_state": self._get_client_state(),
            }

        elif sys_type == "hacking" and not self.hacking.active_hack:
            # Start hacking mini-game
            target_type = subsystem.get("target_type", "terminal")
            player_hacking = self.state.character.get("skills", {}).get("hacking", 0)
            player_stealth = self.state.character.get("skills", {}).get("stealth", 0)
            hack_state = self.hacking.start_hack(target_type, player_hacking, player_stealth)
            return {
                "system": "hacking",
                "hack_state": hack_state,
                "narrative": f"⚡ Подключение к {hack_state['target']['name']}... "
                           f"Узлов: {len(hack_state['nodes'])}, ICE обнаружен. "
                           f"Ходов: {hack_state['turns_left']}.",
            }

        elif sys_type == "investigation":
            case_type = subsystem.get("case_type")
            if not self.investigation.active_cases:
                case = self.investigation.open_case(case_type)
                return {
                    "system": "investigation",
                    "case": case,
                    "narrative": f"🔍 Дело открыто: «{case['name']}». "
                               f"Нужно улик: {case['clues_needed']}. "
                               f"Источники: {', '.join(case['leads'][:3])}.",
                }

        elif sys_type == "crafting":
            target = subsystem.get("target", "")
            from src.systems.game_systems import CraftingSystem
            recipes = CraftingSystem.get_recipes()
            # Find matching recipe
            matched = None
            for r in recipes:
                if target.lower() in r.get("name", "").lower():
                    matched = r
                    break
            if matched:
                check = CraftingSystem.can_craft(matched["id"], self.state.inventory, self.state.character)
                return {
                    "system": "crafting",
                    "recipe": matched,
                    "can_craft": check.get("can_craft", False),
                    "narrative": (f"🔨 Рецепт: «{matched['name']}». "
                                 f"{'✅ Материалы есть!' if check['can_craft'] else '❌ ' + check.get('reason', 'Не хватает материалов')}"),
                }

        return None

    # Канонические планеты/города из GALAXY_MAP (backlog#6: «Zемля»-опечатка)
    # Визуальные пары (A-А, B-В...) + фонетические r/s (Mars→Марс, Zemlya)
    _LOC_LAT_TO_CYR = str.maketrans(
        "ABCEHKMOPTXYZRS", "АВСЕНКМОРТХУЗРС")
    _LOC_LAT_TO_CYR.update(str.maketrans("abcehkmoptxyzrs", "абсенкмортухзрс"))

    def _canonicalize_location(self, loc: Dict) -> Dict:
        """Backlog#6: [STATE].location от AI может содержать опечатки
        («Zемля» — латинская Z), из-за которых регион-фильтр D3 терял 21 фракцию.
        Нормализуем латиницу→кириллицу и fuzzy-match к GALAXY_MAP;
        нераспознанные значения остаются как есть (не терять данные ГМа)."""
        from src.world.galaxy import GALAXY_MAP

        def fix(value, canon_list):
            if not isinstance(value, str) or not value:
                return value  # None/пусто проходят без изменений
            if value in canon_list:
                return value
            norm = value.translate(self._LOC_LAT_TO_CYR).lower().replace("ё", "е")
            for cand in canon_list:
                cand_n = cand.lower().replace("ё", "е")
                if norm == cand_n or (len(norm) >= 4 and (norm in cand_n or cand_n in norm)):
                    return cand
            return value

        fixed = dict(loc)
        if "planet" in fixed:
            planets = list(GALAXY_MAP.keys())
            fixed["planet"] = fix(fixed.get("planet"), planets)
        if "city" in fixed:
            planet_cities = list(GALAXY_MAP.get(fixed.get("planet", ""), {})
                                 .get("cities", {}).keys())
            if planet_cities:
                fixed["city"] = fix(fixed.get("city"), planet_cities)
        if "district" in fixed:
            city_districts = list(GALAXY_MAP.get(fixed.get("planet", ""), {})
                                  .get("cities", {}).get(fixed.get("city", ""), {})
                                  .get("districts", {}).keys())
            if city_districts:
                fixed["district"] = fix(fixed.get("district"), city_districts)
        # Phase 31 H3: place (заведение) канонизируем против establishments района.
        # Модель может прислать place из [STATE].location — если он совпадает с
        # известным заведением района (fuzzy), канонизируем; неизвестное место
        # обнуляем (нельзя «войти» в заведение не из текущего района через текст).
        if "place" in fixed and fixed.get("place"):
            gm = getattr(self, "galaxy_map", None)
            if gm is not None:
                try:
                    ests = gm.list_establishments(
                        fixed.get("planet", self.state.current_location.get("planet", "")),
                        fixed.get("city", self.state.current_location.get("city", "")),
                        fixed.get("district", self.state.current_location.get("district", "")),
                    ) or []
                except Exception:
                    ests = []
                names = [est.get("name") if isinstance(est, dict) else str(est) for est in ests]
                fixed["place"] = fix(fixed.get("place"), names)
                if fixed["place"] not in names:
                    fixed["place"] = ""  # несуществующее заведение — сброс
        return fixed

    # Regex телеметрии: [HP: +5], [HEAT: -2], [TIME: +3ч], [CREDITS: ±N],
    # [STRESS: ±N], [HUMANITY: ±N] и любые другие [ТЕГ: значение].
    # Cut BEFORE history/UI — в окно истории попадает только литературный нарратив.
    TELEMETRY_LINE_RE = re.compile(
        r"^\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|CREDIT|SANITY|FUEL|HEAT_LEVEL)\s*[:±][^\]]*\]\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    TELEMETRY_INLINE_RE = re.compile(
        r"\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|CREDIT|SANITY|FUEL)\s*[:±][^\]]*\]",
        re.IGNORECASE,
    )
    # Phase 27 R7: модель копирует заголовки структуры промпта в ответ
    # («1) НАРРАТИВ», «2) МЕХАНИЧЕСКИЕ ИЗМЕНЕНИЯ», «3) ЗАГОЛОВОК ВЫБОРА»...)
    PROMPT_HEADER_RE = re.compile(
        r"^\s*(?:#+\s*)?\*{0,2}\d\s*[).—-]\s*"
        r"(?:НАРРАТИВ|МЕХАНИЧЕСКИЕ\s+ИЗМЕНЕНИЯ|ЗАГОЛОВОК\s+ВЫБОРА|ПРОНУМЕРОВАННЫХ\s+ВАРИАНТОВ"
        r"|ВАРИАНТЫ\s+ДЕЙСТВИЙ|SВОБОдНЫЙ\s+ВВОД|СВОБОДНЫЙ\s+ВВОД|7-Й\s+ВАРИАНТ"
        r"|СТРУКТУРА\s+ОТВЕТА)\b[^\n]*$",
        re.MULTILINE | re.IGNORECASE,
    )
    # Phase 28 F1: сырые markdown-блоки ```json ... ``` и ``` ... ```
    CODE_FENCE_RE = re.compile(r"```(?:json)?\s*\n?[\s\S]*?```", re.IGNORECASE)
    # Незакрытый ``` в конце ответа (модель начала JSON-блок и не закрыла)
    CODE_FENCE_OPEN_RE = re.compile(r"```(?:json)?[\s\S]*$", re.IGNORECASE)
    # Инструкции нумерации из промпта («5-6 ПРОНУМЕРОВАННЫХ ВАРИАНТОВ ДЕЙСТВИЙ:»,
    # «СТРОГО в формате ...», «Ролевые теги ВСЕГДА ...»)
    PROMPT_INSTRUCTION_RE = re.compile(
        r"^[ \t]*(?:#+[ \t]*)?\*{0,2}"
        r"(?:\d\s*[).—-]?[ \t]*(?:\d\s*[-—]\s*\d\s*)?)?"
        r"(?:ПРОНУМЕРОВАННЫХ\s+ВАРИАНТОВ\s+ДЕЙСТВИЙ[^\n]*"
        r"|СТРОГО\s+В\s+ФОРМАТЕ[^\n]*"
        r"|Ролевые\s+теги\s+ВСЕГДА[^\n]*"
        r"|После\s+тега\s+—[^\n]*"
        r"|7-Й\s+ВАРИАНТ\s+—\s+СВОБОДНЫЙ\s+ВВОД[^\n]*"
        r"|Если\s+требуется\s+проверка\s+навыков[^\n]*"
        r"|НЕ\s+выходи\s+за\s+пределы[^\n]*)"
        r"\*{0,2}[ \t]*$",
        re.MULTILINE | re.IGNORECASE,
    )

    @staticmethod
    def _strip_telemetry(text: str) -> str:
        """Phase 27 D1/R7 + Phase 28 F1: убрать телеметрию, заголовки структуры,
        сырые ```json-блоки и инструкции нумерации из нарратива."""
        text = GameEngine.TELEMETRY_LINE_RE.sub("", text)
        text = GameEngine.TELEMETRY_INLINE_RE.sub("", text)
        text = GameEngine.PROMPT_HEADER_RE.sub("", text)
        text = GameEngine.CODE_FENCE_RE.sub("", text)
        text = GameEngine.CODE_FENCE_OPEN_RE.sub("", text)
        text = GameEngine.PROMPT_INSTRUCTION_RE.sub("", text)
        # Схлопнуть оставшиеся пустые строки (более 2 подряд)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response: extract narrative and apply [STATE] block changes."""
        import json as _json
        narrative = response
        state_changes = {}

        # Extract [STATE]...[/STATE] block
        start_tag = "[STATE]"
        end_tag = "[/STATE]"
        si = response.find(start_tag)
        ei = response.find(end_tag)

        if si != -1 and ei != -1 and ei > si:
            json_str = response[si + len(start_tag):ei].strip()
            narrative = (response[:si] + response[ei + len(end_tag):]).strip()

            try:
                state_changes = _json.loads(json_str)
            except _json.JSONDecodeError:
                # Try to fix common issues
                try:
                    # Remove trailing commas, fix quotes
                    fixed = json_str.replace("'", '"').rstrip(",}")
                    if not fixed.endswith("}"): fixed += "}"
                    state_changes = _json.loads(fixed)
                except Exception:
                    state_changes = {}
        elif si != -1:
            # Phase 27 D1 fix + Phase 28 G2: модель часто забывает [/STATE].
            # JSON-объект [STATE]{...} может быть В СЕРЕДИНЕ ответа, а после него
            # идут варианты выбора — вырезать всё до конца нельзя (G2: пропадали
            # нумерованные кнопки). Извлекаем только сам {...} балансом скобок.
            json_str = response[si + len(start_tag):].strip()
            rest_after_json = ""
            brace_depth = 0
            json_end = -1
            for ci, ch in enumerate(json_str):
                if ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        json_end = ci
                        break
            if json_end != -1:
                candidate = json_str[:json_end + 1]
                rest_after_json = json_str[json_end + 1:].strip()
            else:
                candidate = json_str
            narrative = (response[:si] + "\n" + rest_after_json).strip()
            try:
                fixed = candidate.replace("'", '"').rstrip(",}")
                if not fixed.endswith("}"): fixed += "}"
                state_changes = _json.loads(fixed)
            except Exception:
                state_changes = {}

        # === APPLY STATE CHANGES ===
        char = self.state.character

        # HP
        hp_change = state_changes.get("hp_change", 0)
        if hp_change:
            max_hp = char.get("derived", {}).get("health_points", 50)
            char["current_hp"] = max(0, min(max_hp, char.get("current_hp", max_hp) + hp_change))

        # Credits
        credits_change = state_changes.get("credits_change", 0)
        if credits_change:
            char["credits"] = max(0, char.get("credits", 0) + credits_change)

        # Stress
        stress_change = state_changes.get("stress_change", 0)
        if stress_change:
            PsychologySystem.apply_stress_change(char, stress_change)

        # Humanity
        humanity_change = state_changes.get("humanity_change", 0)
        if humanity_change:
            PsychologySystem.apply_humanity_change(char, humanity_change)

        # Location change
        new_loc = state_changes.get("location")
        if new_loc and isinstance(new_loc, dict):
            old_loc = dict(self.state.current_location)
            new_loc = self._canonicalize_location(new_loc)  # backlog#6: «Zемля» → «Земля»
            self.state.current_location.update(new_loc)
            # Record travel in NPC memory
            if old_loc.get("district") != new_loc.get("district", old_loc.get("district")):
                self.state.session_events.append({
                    "time": dict(self.state.game_time),
                    "action": f"travel:{old_loc.get('district','?')}→{new_loc.get('district','?')}",
                    "result": "перемещение",
                })

        # Add items
        for item in state_changes.get("add_items", []):
            if isinstance(item, dict) and item.get("name"):
                # Check if already in inventory
                found = False
                for inv_item in self.state.inventory:
                    if inv_item.get("name") == item["name"]:
                        inv_item["qty"] = inv_item.get("qty", 1) + item.get("qty", 1)
                        found = True
                        break
                if not found:
                    self.state.inventory.append({
                        "name": item["name"],
                        "qty": item.get("qty", 1),
                        "category": item.get("category", "misc"),
                    })

        # Remove items
        for item_name in state_changes.get("remove_items", []):
            if isinstance(item_name, str):
                self.state.inventory = [
                    i for i in self.state.inventory
                    if i.get("name", "").lower() != item_name.lower()
                ]

        # NPC met — register in NPC registry
        npc_met = state_changes.get("npc_met")
        if npc_met and isinstance(npc_met, str):
            npc = self.state.npc_registry.get_npc(npc_met)
            if not npc:
                self.state.npc_registry.generate_npc(
                    planet=self.state.current_location.get("planet", "Земля"),
                    name=npc_met,
                    location=self.state.current_location.get("district", ""),
                )
            self.state.npc_registry.record_encounter(
                npc_met, self.state.world_sim.turn_count,
                context=f"Встреча в {self.state.current_location.get('district', '?')}"
            )

        # Quest complete
        quest_id = state_changes.get("quest_complete")
        if quest_id:
            completed = [q for q in self.state.active_quests if q.get("id") == quest_id or q.get("title") == quest_id]
            for q in completed:
                q["status"] = "completed"
                self.state.completed_quests.append(q)
            self.state.active_quests = [q for q in self.state.active_quests if q.get("status") != "completed"]

        # Quest chain advance
        if state_changes.get("quest_advance") and self.active_chain:
            self.advance_quest_chain()

        # Combat state
        if state_changes.get("combat_started"):
            self.state.in_combat = True
        if state_changes.get("combat_ended"):
            self.state.in_combat = False
            self.state.combat_state = {}

        # XP — just record, actual level-up check done by caller via process_xp_gain
        xp = state_changes.get("xp_gained", 0)
        if xp > 0:
            state_changes["_xp_to_add"] = xp  # marker for caller

        # Custom time advance (override default)
        custom_time = state_changes.get("time_minutes")
        if custom_time and isinstance(custom_time, (int, float)) and custom_time > 0:
            state_changes["_custom_time"] = int(custom_time)

        # Phase 27 D1: телеметрия ([HP: ...], [HEAT: ...], [TIME: ...]) не попадает
        # ни в историю, ни в UI — вырезаем ДО возврата.
        narrative = self._strip_telemetry(narrative)

        return {"narrative": narrative, "state_changes": state_changes}

    def _advance_time(self, minutes: int = 10):
        t = self.state.game_time
        total = t["hour"] * 60 + t["minute"] + minutes
        t["hour"] = (total // 60) % 24
        t["minute"] = total % 60
        if total >= 1440:
            t["day"] += total // 1440
            if t["day"] > 30:
                t["day"] = 1
                t["month"] += 1
                if t["month"] > 12:
                    t["month"] = 1
                    t["year"] += 1

    def _format_game_time(self) -> str:
        t = self.state.game_time
        return f"{t['year']}.{t['month']:02d}.{t['day']:02d} {t['hour']:02d}:{t['minute']:02d}"

    def _get_origin_traits(self) -> list:
        """Phase 27 D6: черты происхождения (Origin Traits) для листа персонажа."""
        traits = []
        origin_id = self.state.character.get("origin", "")
        if not origin_id:
            return traits
        try:
            creation = self.get_creation_data()
            origin_data = next((o for o in creation["origins"]
                                if o["id"] == origin_id or o["id"].endswith(f"_{origin_id}")), None)
            if not origin_data:
                return traits
            # Черты: effects (текстовые), attr_mods, skill_mods
            for eff in origin_data.get("effects", []) or []:
                if isinstance(eff, str):
                    traits.append(eff)
            attr_names_ru = {"strength": "СИЛ", "dexterity": "ЛОВ", "intelligence": "ИНТ",
                             "charisma": "ХАР", "endurance": "ВЫН", "willpower": "ВОЛ",
                             "reflexes": "РЕФ", "tech_empathy": "ТЕХ"}
            for ak, av in (origin_data.get("attr_mods") or {}).items():
                sign = "+" if av >= 0 else ""
                traits.append(f"{attr_names_ru.get(ak, ak)} {sign}{av}")
            skill_names = self.state.character.get("_skill_names_ru", {}) or {}
            for sk, sv in (origin_data.get("skill_mods") or {}).items():
                sign = "+" if sv >= 0 else ""
                traits.append(f"{skill_names.get(sk, sk)} {sign}{sv}")
        except Exception as e:
            print(f"[WARN] origin traits: {e}")
        return traits

    def _get_regional_faction_relations(self) -> list:
        """Phase 27 D6: отношения с ключевыми фракциями текущего региона.
        Возвращает [{name, standing, attitude}] для фракций региона локации."""
        from src.utils.region import region_matches
        planet = (self.state.current_location or {}).get("planet", "")
        if not planet:
            return []
        rep = getattr(self.state, "faction_reputation", {}) or {}
        result = []
        try:
            resolver = getattr(self.state.npc_registry, "faction_resolver", None)
            factions_master = self.kb.get_file("FACTIONS_MASTER.json") or {}
            for f in factions_master.get("factions", []):
                if "canonical_duplicate_of" in f:
                    continue
                if not region_matches(f.get("influence_region", ""), planet):
                    continue
                fname = f.get("name", "?")
                fid = f.get("id", "")
                standing = rep.get(fname, rep.get(fid, None))
                if standing is None:
                    attitude = "нейтрально"
                elif standing >= 25:
                    attitude = "союзник"
                elif standing >= 5:
                    attitude = "дружелюбно"
                elif standing <= -25:
                    attitude = "враг"
                elif standing <= -5:
                    attitude = "враждебно"
                else:
                    attitude = "нейтрально"
                result.append({
                    "name": fname,
                    "faction_id": fid,
                    "standing": standing if standing is not None else 0,
                    "attitude": attitude,
                })
        except Exception as e:
            print(f"[WARN] faction relations: {e}")
        result.sort(key=lambda x: -abs(x.get("standing", 0)))
        return result[:12]

    def _get_client_state(self) -> Dict:
        char = self.state.character
        derived = char.get("derived", {})
        return {
            "character": {
                "name": char.get("name", ""),
                "class": char.get("preset_name", ""),
                "origin_name": char.get("origin_name", ""),
                "specialization_name": char.get("specialization_name", char.get("preset_name", "")),
                "age": char.get("age", 0),
                "level": char.get("level", 1),
                "xp": char.get("xp", 0),
                "xp_next": char.get("xp_next", 1000),
                "hp": char.get("current_hp", 0),
                "hp_max": derived.get("health_points", 50),
                "sanity": char.get("current_sanity", 0),
                "sanity_max": derived.get("sanity_points", 50),
                "credits": char.get("credits", 0),
                "attributes": char.get("attributes", {}),
                "attr_bonuses": char.get("attr_bonuses", {}),
                "unspent_attribute_points": char.get("unspent_attribute_points", 0),
                "max_attribute": get_skill_cap(char.get("level", 1))[1],
                "skills": char.get("skills", {}),
                # Phase 27 D6: полнота листа персонажа
                "influence_tier": self.get_player_influence_tier(),
                "origin_traits": self._get_origin_traits(),
                "faction_relations": self._get_regional_faction_relations(),
            },
            "location": self.state.current_location,
            "time": self._format_game_time(),
            "active_quests": len(self.state.active_quests),
            "inventory_count": len(self.state.inventory),
            "phase": self.state.phase,
            "influence_tier": self.get_player_influence_tier(),
            "skill_cap": get_skill_cap(char.get("level", 1)),
            "companions": [{"name": c.get("name","?"), "type": c.get("type","?"),
                           "loyalty": c.get("loyalty",50),
                           "hp": c.get("hp", c.get("max_hp", 30))} for c in self.companions.companions],
            "ship": {"name": self.ship.ship.get("name","?"),
                     "class": self.ship.ship.get("class_name", self.ship.ship.get("ship_class","?")),
                     "hull": f"{self.ship.ship.get('hull',0)}/{self.ship.ship.get('max_hull',0)}",
                     "fuel": f"{self.ship.ship.get('fuel',0)}/{self.ship.ship.get('fuel_max',0)}",
                     "cargo": f"{len(self.ship.ship.get('cargo',[]))}/{self.ship.ship.get('cargo_capacity',0)}",
                     } if self.ship.ship else None,
            "properties": [{"name": p.get("name","?"), "type": p.get("type","?"),
                           "income": p.get("income_per_cycle",0)} for p in self.property.properties],
            "active_investigations": len(self.investigation.active_cases),
            "active_hack": bool(self.hacking.active_hack and self.hacking.active_hack.get("status") == "active"),
        }

    # ========== START GAME ==========

    def start_game(self, character_name: str) -> Dict:
        self.state.character["name"] = character_name
        self.state.phase = "playing"

        origin_name = self.state.character.get("origin_name", "")
        origin_id = self.state.character.get("origin", "")
        spec_name = self.state.character.get("specialization_name", self.state.character.get("preset_name", ""))
        spec_id = self.state.character.get("specialization", "")
        backstory = self.state.character.get("description", "")

        # ── Assign starting quests based on origin + specialization ──
        self._assign_starting_quests(origin_id, spec_id)

        # А2: мир прожил время между сессиями — фоновый догон
        try:
            self._background_catch_up(max_ticks=5)
        except Exception:
            pass

        quest_hints = ""
        if self.state.active_quests:
            titles = [q["title"] for q in self.state.active_quests[:3]]
            quest_hints = f"Активные квесты персонажа: {', '.join(titles)}. Намекни на первый из них в сцене. "

        # Phase 26: применяем scene_context к tone_profile (локация + tier).
        # Phase 31 H1-блокер1: print-маскировка снята — сбой здесь тонул молча
        # (именно так H1 жил 5+ фаз). Если tone_profile None (битый старый сейв) —
        # детерминированно пересобираем из персонажа вместо отложенного краша.
        location = self.state.current_location
        if self.state.tone_profile is None:
            self.state.tone_profile = self.tone_engine.build_character_tone(self.state.character)
        tier_info = self.get_player_influence_tier() if hasattr(self, "get_player_influence_tier") else None
        self.tone_engine.apply_scene_context(
            self.state.tone_profile, location=location, tier_info=tier_info
        )

        # Phase 26: используем prompt_builder для intro-action (Phase 2.1)
        intro_prompt = self.prompt_builder.build_intro_action(
            self.state.tone_profile,
            character=self.state.character,
            location=location,
            quest_hints=quest_hints,
        )
        return self.process_player_action(intro_prompt)

    def _assign_starting_quests(self, origin_id: str, spec_id: str):
        """Phase 27 D2: при старте выдаётся МАКСИМУМ 1 вводный квест.
        Приоритет: квест происхождения → квест специализации → универсальный.
        Остальные квесты игрок берёт добровольно (контракты, диалоги, доски объявлений)."""
        try:
            quest_data = self.kb.get_file("STARTING_QUESTS_COMPLETE.json")
            if not quest_data:
                quest_data = self.kb.get_file("STARTING_QUESTS.json")
            if not quest_data:
                return

            data = quest_data.get("data", quest_data)

            def _norm(x: str) -> str:
                """Normalize id: strip ORIGIN_/SPEC_ prefix for comparison."""
                x = (x or "").strip()
                if x.startswith("ORIGIN_"): x = x[len("ORIGIN_"):]
                elif x.startswith("SPEC_"):  x = x[len("SPEC_"):]
                return x

            candidates = []

            # 1) Origin quest (приоритет)
            for q in data.get("origin_quests", []):
                req = q.get("origin", q.get("required_lifepath", [""])[0] if isinstance(q.get("required_lifepath"), list) else "")
                if _norm(req) == _norm(origin_id):
                    candidates.append(q)
                    break

            # 2) Specialization quest
            for q in data.get("specialization_quests", []):
                req = q.get("specialization", q.get("required_specialization", ""))
                if _norm(req) == _norm(spec_id):
                    candidates.append(q)
                    break

            # 3) Universal quest (random one)
            import random
            universals = data.get("universal_quests", [])
            if universals:
                candidates.append(random.choice(universals))

            # Жёсткий лимит: не более ОДНОГО вводного квеста
            if not candidates:
                return
            starter = candidates[0]
            self.state.active_quests.append(
                QuestTracker.create_quest(
                    title=starter["title"], description=starter["description"],
                    giver=starter.get("giver", ""), reward_credits=starter.get("reward_credits", 0),
                    reward_xp=starter.get("reward_xp", 200), stages=starter.get("stages"),
                    reward_reputation=starter.get("reward_reputation", {}),  # Фаза 24d
                    tier=starter.get("tier"),  # Фаза 24d
                )
            )
        except Exception as e:
            print(f"[WARN] Failed to assign starting quests: {e}")

    def _planet_hook_factions(self, planet: str):
        """Backlog#3: имена фракций с plot_hooks, чей influence_region матчит планету."""
        import json as _json, os as _os
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                             "..", "..", "game_data", "FACTIONS_MASTER.json")
        try:
            fm = _json.load(open(path, encoding="utf-8"))
        except Exception:
            return []
        result = []
        for f in fm["factions"]:
            if "canonical_duplicate_of" in f or not f.get("plot_hooks"):
                continue
            if self._region_matches(f.get("influence_region", ""), planet):
                result.append(f["name"])
        return result

    def _region_matches(self, region: str, planet: str) -> bool:
        """Делегирует в src/utils/region.py (Phase 26: единая утилита)."""
        from src.utils.region import region_matches
        return region_matches(region, planet)

    def generate_quest_from_hook(self, faction_name: str) -> Dict:
        """Backlog#3: ручная точка — квест из хука конкретной фракции."""
        quest = self.quest_generator.generate_quest_from_hook(
            faction_name,
            player_level=self.state.character.get("level", 1),
            location=self.state.current_location)
        if "error" not in quest and len(self.state.active_quests) < 8:
            self.state.active_quests.append(quest)
            self.state.world_context["new_quest"] = quest
        return quest

    def accept_contract(self, contract_id: str) -> dict:
        """Phase 3 loop (шаг 2): взять процедурный контракт в работу.

        Получает список доступных контрактов для текущей локации через
        self.contract_gen.get_available_contracts(), находит контракт
        по id, проверяет что он ещё не взят (нет в active_quests), и
        добавляет его в self.state.active_quests в формате стандартного
        квеста + служебные поля для двусторонней синхронизации с
        ContractGenerator.

        Args:
            contract_id: id контракта из get_available_contracts(...).

        Returns:
            {"success": True, "quest": {...}} — успех.
            {"success": False, "error": "...", "code": "..."} — ошибка.
                code ∈ {"invalid_id", "no_location", "no_contracts",
                         "not_found", "already_accepted"}
        """
        if not contract_id or not isinstance(contract_id, str):
            return {"success": False, "error": "contract_id не указан",
                    "code": "invalid_id"}

        # 1) Текущая локация и тир игрока
        location = self.state.current_location
        if not location or not location.get("planet"):
            return {"success": False, "error": "Локация не определена",
                    "code": "no_location"}

        tier_info = self.get_player_influence_tier()
        tier = tier_info.get("tier", 0) if isinstance(tier_info, dict) else 0

        # 2) Получаем доступные контракты
        contracts = self.contract_gen.get_available_contracts(
            location=location,
            player_tier=tier,
        )
        if not contracts:
            return {"success": False, "error": "Нет доступных контрактов в локации",
                    "code": "no_contracts"}

        # 3) Ищем контракт по id
        target = None
        for c in contracts:
            if c.get("id") == contract_id:
                target = c
                break
        if target is None:
            return {"success": False,
                    "error": f"Контракт {contract_id!r} не найден среди доступных",
                    "code": "not_found"}

        # 4) Проверяем, что контракт ещё не взят
        for q in self.state.active_quests:
            if q.get("id") == contract_id or q.get("contract_id") == contract_id:
                return {"success": False,
                        "error": f"Контракт {contract_id!r} уже взят",
                        "code": "already_accepted"}

        # 5) Собираем квест в формате стандартного квеста + служебные поля
        quest = {
            "id": target.get("id"),
            "title": target.get("title", ""),
            "description": target.get("description", ""),
            "giver": target.get("giver", "Unknown"),
            "rewards": {
                "credits": target.get("reward_credits", 0),
                "xp": target.get("reward_xp", 0),
            },
            # Плоские дубликаты для обратной совместимости с уже существующим
            # кодом, который читает reward_credits / reward_xp напрямую.
            "reward_credits": target.get("reward_credits", 0),
            "reward_xp": target.get("reward_xp", 0),
            "stages": target.get("stages", []),
            "requirements": target.get("requirements", {}),
            "paths": target.get("paths", []),
            "contract_type": target.get("type", "default"),
            "contract_id": target.get("id"),  # alias для идемпотентной проверки
            "status": "active",
            "source": "contract_generator",
            "accepted_at": dict(self.state.game_time),
        }

        # 6) Добавляем в active_quests
        self.state.active_quests.append(quest)
        self.state.world_context["new_quest"] = quest

        return {"success": True, "quest": quest}

    def complete_contract(self, contract_id: str) -> dict:
        """Phase 3 final close (шаг 1): успешно завершить процедурный контракт.

        Находит квест в self.state.active_quests по contract_id или id,
        начисляет награды (credits + xp), переносит квест из active_quests
        в completed_quests с отметкой completed_at.

        Args:
            contract_id: id контракта (= id квеста в active_quests).

        Returns:
            {"success": True, "reward_credits", "reward_xp", "quest"} — успех.
            {"success": False, "error", "code"} — ошибка.
                code ∈ {"invalid_id", "not_found"}.
        """
        if not contract_id or not isinstance(contract_id, str):
            return {"success": False, "error": "contract_id не указан",
                    "code": "invalid_id"}

        # 1) Ищем квест в active_quests
        quest = None
        quest_index = None
        for i, q in enumerate(self.state.active_quests):
            if not isinstance(q, dict):
                continue
            if q.get("id") == contract_id or q.get("contract_id") == contract_id:
                quest = q
                quest_index = i
                break
        if quest is None:
            return {"success": False,
                    "error": f"Контракт {contract_id!r} не найден среди активных",
                    "code": "not_found"}

        # 2) Извлекаем награды (поддерживаем оба формата: rewards.{credits,xp}
        # и плоские reward_credits/reward_xp).
        rewards = quest.get("rewards") or {}
        if isinstance(rewards, dict) and ("credits" in rewards or "xp" in rewards):
            reward_credits = int(rewards.get("credits", 0))
            reward_xp = int(rewards.get("xp", 0))
        else:
            reward_credits = int(quest.get("reward_credits", 0))
            reward_xp = int(quest.get("reward_xp", 0))

        # 3) Начисляем кредиты
        if reward_credits > 0:
            self.state.character["credits"] = (
                self.state.character.get("credits", 0) + reward_credits
            )

        # 4) Начисляем XP через стандартный путь (обрабатывает level-up)
        level_ups = []
        if reward_xp > 0:
            level_ups = self.add_xp(reward_xp)

        # 5) Помечаем квест как завершённый и переносим в completed_quests
        completed = dict(quest)
        completed["status"] = "completed"
        completed["completed_at"] = dict(self.state.game_time)
        completed["reward_credits_awarded"] = reward_credits
        completed["reward_xp_awarded"] = reward_xp
        if level_ups:
            completed["level_ups"] = level_ups
        # 6) Удаляем из active_quests, добавляем в completed_quests
        self.state.active_quests.pop(quest_index)
        self.state.completed_quests.append(completed)
        self.state.world_context["contract_completed"] = completed

        return {
            "success": True,
            "reward_credits": reward_credits,
            "reward_xp": reward_xp,
            "quest": completed,
            "level_ups": level_ups,
        }

    def _world_tick(self) -> Dict:
        """А2: один мировой тик. Phase 30: логика перенесена в
        WorldTickService.tick() (src/world/world_tick_service.py);
        метод остался делегатом — публичная сигнатура не изменилась."""
        return self.world_tick_service.tick()

    def _background_catch_up(self, max_ticks: int = 20):
        """А2: прогнать мировые тики за время, пока игрок не действовал.
        Вызывается при загрузке сессии и по «ожиданию» — мир живёт без игрока."""
        ticks = min(max(0, int(max_ticks)), 50)
        for _ in range(ticks):
            self._world_tick()

    # ========== SAVE / LOAD ==========

    def save_game(self, slot_name: str = None) -> Dict:
        if not slot_name:
            slot_name = f"save_{self.state.id}_{int(time.time())}"
        # End active combat/hack on save (can't serialize mid-action)
        if self.combat_engine.in_combat:
            self.combat_engine.end_combat()
            self.state.in_combat = False
        if self.hacking.active_hack and self.hacking.active_hack.get("status") == "active":
            self.hacking.active_hack["status"] = "aborted"
        # V5: serialize world effects
        we_list = []
        for eff in self.world_effects.active_effects:
            we_list.append({
                "effect_key": eff.effect_key, "value": eff.value,
                "source_event_id": eff.source_event_id,
                "start_hours": eff.start_hours, "duration_hours": eff.duration_hours,
            })
        save_data = {
            "slot_name": slot_name,
            "save_time": datetime.now().isoformat(),
            "character_name": self.state.character.get("name", "Безымянный"),
            "character_class": self.state.character.get("preset_name", ""),
            "level": self.state.character.get("level", 1),
            "location": self.state.current_location,
            "game_time": self.state.game_time,
            "state": self.state.to_dict(),
            # V5 engine-level state
            "v5_active_companions": self.active_companions,
            "v5_active_chain": self.active_chain,
            "v5_completed_chains": self.completed_chains,
            "v5_world_effects": we_list,
            "v6_property_income": self.property_income.to_dict(),
            "v16_fame": getattr(self.state, "fame", 0),
            "v13_expenses": self.expenses.to_dict(),
            # V7: subsystem states
            "v7_hacking": self.hacking.to_dict(),
            "v7_investigation": self.investigation.to_dict(),
            "v7_companions_sys": self.companions.to_dict(),
            "v7_ship": self.ship.to_dict(),
            "v7_property": self.property.to_dict(),
        }
        filepath = os.path.join(self.saves_dir, f"{slot_name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        return {"success": True, "slot_name": slot_name}

    def load_game(self, slot_name: str) -> Dict:
        filepath = os.path.join(self.saves_dir, f"{slot_name}.json")
        if not os.path.exists(filepath):
            return {"error": f"Сохранение '{slot_name}' не найдено"}
        with open(filepath, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        self.state = GameState.from_dict(save_data["state"])
        # V5: Restore engine-level state
        self.active_companions = save_data.get("v5_active_companions", [])
        self.active_chain = save_data.get("v5_active_chain", {})
        self.completed_chains = save_data.get("v5_completed_chains", [])
        # Restore world effects
        from src.content.v5_legacy import WorldEffectsManager, ActiveWorldEffect
        self.world_effects = WorldEffectsManager()
        for we_data in save_data.get("v5_world_effects", []):
            self.world_effects.active_effects.append(ActiveWorldEffect(
                we_data["effect_key"], we_data["value"], we_data["source_event_id"],
                we_data["start_hours"], we_data["duration_hours"],
            ))
        # V6: Restore property income manager
        if "v13_expenses" in save_data:
            self.expenses = ExpenseCycle.from_dict(save_data["v13_expenses"])
        if "v16_fame" in save_data:
            self.state.fame = save_data["v16_fame"]
        if "v6_property_income" in save_data:
            self.property_income = PropertyIncomeManager.from_dict(save_data["v6_property_income"])
        # V7: Restore subsystem states
        if "v7_hacking" in save_data:
            self.hacking = HackingSystem.from_dict(save_data["v7_hacking"])
        if "v7_investigation" in save_data:
            self.investigation = InvestigationSystem.from_dict(save_data["v7_investigation"])
        if "v7_companions_sys" in save_data:
            self.companions = CompanionSystem.from_dict(save_data["v7_companions_sys"])
        if "v7_ship" in save_data:
            self.ship = ShipSystem.from_dict(save_data["v7_ship"])
        if "v7_property" in save_data:
            self.property = PropertySystem.from_dict(save_data["v7_property"])
        # Phase 24c B5-3: Migration — separate attr_bonuses from attributes
        self._migrate_attr_bonuses()

        # Phase 26: fallback — если сейв старый (без tone_profile),
        # пересобираем профиль из character (Origin/Spec/FY).
        if not self.state.tone_profile:
            try:
                self.state.tone_profile = self.tone_engine.build_character_tone(self.state.character)
            except Exception as e:
                print(f"[Engine] load_game tone_profile fallback failed: {e}")
                self.state.tone_profile = None

        # Return chat history for UI restoration
        return {
            "success": True,
            "character_name": save_data.get("character_name", ""),
            "game_state": self._get_client_state(),
            "conversation_history": self.state.conversation_history,
        }

    def list_saves(self) -> List[Dict]:
        saves = []
        for fname in sorted(os.listdir(self.saves_dir), reverse=True):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(self.saves_dir, fname), "r", encoding="utf-8") as f:
                        d = json.load(f)
                    saves.append({
                        "slot_name": d.get("slot_name", fname[:-5]),
                        "character_name": d.get("character_name", "?"),
                        "character_class": d.get("character_class", ""),
                        "level": d.get("level", 1),
                        "save_time": d.get("save_time", ""),
                        "location": d.get("location", {}),
                        "game_time": d.get("game_time", {}),
                    })
                except (json.JSONDecodeError, KeyError, IOError): pass
        return saves

    def delete_save(self, slot_name: str) -> Dict:
        fp = os.path.join(self.saves_dir, f"{slot_name}.json")
        if os.path.exists(fp):
            os.remove(fp)
            return {"success": True}
        return {"error": "Не найдено"}

    # ========== COMBAT ==========

    def start_combat(self, enemies=None):
        self.state.in_combat = True
        self.state.phase = "combat"
        if not enemies:
            enemies = [{"name": "Наёмник", "hp": 30, "hp_max": 30, "attack": 3, "defense": 2, "initiative": 8}]
        pi = self.dice.skill_check(
            self.state.character.get("attributes", {}).get("reflexes", 5),
            self.state.character.get("attributes", {}).get("dexterity", 5), 0)
        self.state.combat_state = {
            "round": 1, "enemies": enemies,
            "player_initiative": pi["result"],
            "player_turn": pi["result"] >= enemies[0].get("initiative", 5),
            "log": [],
        }
        return self.state.combat_state

    def combat_action(self, action: str) -> Dict:
        return self.process_player_action(f"[БОЕВОЕ ДЕЙСТВИЕ] {action}")

    # ========== UTILITY ==========

    def get_full_state(self) -> Dict:
        return self._get_client_state()

    def apply_damage(self, amount):
        self.state.character["current_hp"] = max(0, self.state.character.get("current_hp", 50) - amount)

    def heal(self, amount):
        mx = self.state.character.get("derived", {}).get("health_points", 50)
        self.state.character["current_hp"] = min(mx, self.state.character.get("current_hp", 0) + amount)

    def add_xp(self, amount):
        self.state.character["xp"] = self.state.character.get("xp", 0) + amount
        level_ups = []
        while self.state.character["xp"] >= self.state.character.get("xp_next", 1000):
            self.state.character["xp"] -= self.state.character["xp_next"]
            self.state.character["level"] = self.state.character.get("level", 1) + 1
            self.state.character["xp_next"] = int(self.state.character["xp_next"] * 1.5)
            self._enforce_skill_caps()
            # Process level up rewards
            lu_info = LevelUpSystem.process_level_up(self.state.character)
            level_ups.append(lu_info)
        return level_ups

    def _apply_tone_to_current_location(self) -> None:
        """Phase 26 Step 3 Blocker: обновить mood_descriptors в tone_profile
        под текущую локацию. Вызывать ПОСЛЕ каждого изменения
        self.state.current_location. Если tone_profile отсутствует — no-op.
        """
        if not self.state.tone_profile:
            return
        try:
            tier_info = self.get_player_influence_tier()
        except Exception:
            tier_info = None
        try:
            self.tone_engine.apply_scene_context(
                self.state.tone_profile,
                location=self.state.current_location,
                tier_info=tier_info,
            )
        except Exception as e:
            # Фаза 3: убрать маскировку. Сборка сцены критична для промпта.
            raise RuntimeError(f"apply_scene_context failed: {e}") from e

    def _enforce_skill_caps(self):
        level = self.state.character.get("level", 1)
        max_skill, max_attr = get_skill_cap(level)

        # Cap skills
        skills = self.state.character.get("skills", {})
        for skill_name, val in skills.items():
            if val > max_skill:
                skills[skill_name] = max_skill

        # Cap attributes
        attrs = self.state.character.get("attributes", {})
        for attr_name, val in attrs.items():
            if val > max_attr:
                attrs[attr_name] = max_attr

    def _migrate_attr_bonuses(self):
        """Phase 24c B5-3: Retroactive migration for old saves.

        Old saves have attr_bonuses from implants baked into character['attributes'].
        This reconstructs attr_bonuses from currently installed implants, subtracts
        them from attributes, and grants retroactive unspent_attribute_points.

        If all implants are still installed (normal case), this is lossless:
        effective attr value = base + attr_bonuses stays the same before and after.
        """
        char = self.state.character
        if char.get("attr_bonuses") is not None:
            # Already migrated
            return

        attrs = char.get("attributes", {})
        attr_bonuses = {}

        # Reconstruct implant attr_bonuses from inventory installed implants
        from src.systems.equipment_lookup import IMPLANT_SKILL_MAP
        for item in self.state.inventory:
            if not item.get("installed"):
                continue
            if item.get("type") != "implants" and item.get("category") != "implants":
                continue
            implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), {})
            for attr, val in implant_info.get("attr_bonuses", {}).items():
                attr_bonuses[attr] = attr_bonuses.get(attr, 0) + val

        if attr_bonuses:
            # Subtract reconstructed bonuses from attributes
            for attr, val in attr_bonuses.items():
                cur = attrs.get(attr, 5)
                attrs[attr] = max(2, cur - val)  # floor at 2

        char["attr_bonuses"] = attr_bonuses

        # Retroactive unspent_attribute_points
        level = char.get("level", 1)
        total_attr_points = sum(_attr_points_for_level(l) for l in range(2, level + 1))
        already_spent = char.get("unspent_attribute_points", 0)
        char["unspent_attribute_points"] = max(0, total_attr_points - already_spent)

    def get_player_influence_tier(self) -> dict:
        """Get current player influence tier (multi-factor, Фаза 16)."""
        from src.world.player_tiers import compute_player_tier
        char = self.state.character
        faction_rep = getattr(self.state, 'faction_reputation', {})
        fame = getattr(self.state, 'fame', 0)
        nw = compute_net_worth(char, getattr(self, 'property', None), getattr(self, 'ship', None))
        result = compute_player_tier(char, faction_rep, fame, nw)
        return {
            "tier": result["tier"],
            "name": TIER_NAMES_RU.get(result["tier"], result["tier_name"]),
            "tier_name": result["tier_name"],
            "axes": result["axes"],
            "blocking_axes": result["blocking_axes"],
        }

    def add_credits(self, amount):
        self.state.character["credits"] = self.state.character.get("credits", 0) + amount

    def add_item(self, item):
        self.state.inventory.append(item)

    def get_inventory(self):
        return self.state.inventory

    def get_quests(self):
        return {"active": self.state.active_quests, "completed": self.state.completed_quests}

    def abandon_quest(self, quest_id: str) -> Dict:
        """Phase 27 D2: игрок добровольно отказывается от квеста."""
        if not quest_id:
            return {"success": False, "error": "Не указан ID квеста"}
        target = None
        for q in self.state.active_quests:
            if str(q.get("id", "")) == str(quest_id) or str(q.get("contract_id", "")) == str(quest_id):
                target = q
                break
        if not target:
            return {"success": False, "error": "Квест не найден среди активных"}
        self.state.active_quests.remove(target)
        target["status"] = "abandoned"
        target["abandoned_at"] = dict(self.state.game_time)
        self.state.completed_quests.append(target)
        return {
            "success": True,
            "quest_title": target.get("title", quest_id),
            "game_state": self._get_client_state(),
        }

    # ═══ V5: COMPANION MANAGEMENT ═══

    def get_available_companions_list(self) -> list:
        """Return companions available for recruitment at current state."""
        already = [c["id"] for c in self.active_companions]
        avail = get_available_companions(
            self.state.character.get("level", 1),
            self.state.character.get("credits", 0),
            self.state.character.get("skills", {}),
            self.state.faction_reputation)
        return [c for c in avail if c["id"] not in already]

    def recruit_companion(self, companion_id: str) -> dict:
        """Recruit a companion. Max 3 active."""
        if len(self.active_companions) >= 3:
            return {"success": False, "error": "Максимум 3 компаньона в группе"}
        comp = get_companion_by_id(companion_id)
        if not comp:
            return {"success": False, "error": "Компаньон не найден"}
        if any(c["id"] == companion_id for c in self.active_companions):
            return {"success": False, "error": "Уже в группе"}
        self.active_companions.append({
            "id": companion_id, "loyalty": 30,
            "recruited_turn": self.state.world_sim.turn_count})
        return {"success": True, "companion": comp["name"],
                "greeting": comp.get("dialogue_samples", {}).get("greeting", "")}

    def dismiss_companion(self, companion_id: str) -> dict:
        self.active_companions = [c for c in self.active_companions if c["id"] != companion_id]
        return {"success": True}

    def change_companion_loyalty(self, companion_id: str, delta: int):
        for c in self.active_companions:
            if c["id"] == companion_id:
                c["loyalty"] = max(-100, min(100, c.get("loyalty", 0) + delta))
                ll = get_loyalty_level(c["loyalty"])
                if ll.get("will_leave"):
                    self.dismiss_companion(companion_id)
                    return {"left": True, "name": companion_id}
                return {"loyalty": c["loyalty"], "label": ll["label"]}
        return {}

    def get_companion_bonuses(self) -> dict:
        """Get total skill bonuses from all active companions."""
        totals = {}
        for comp_state in self.active_companions:
            comp = get_companion_by_id(comp_state["id"])
            if comp:
                loy = comp_state.get("loyalty", 50)
                ll = get_loyalty_level(loy)
                mult = ll.get("bonus_mult", 0.5)
                for skill, val in comp.get("skill_bonus", {}).items():
                    totals[skill] = totals.get(skill, 0) + int(val * mult)
        return totals

    # ═══ V5: QUEST CHAIN MANAGEMENT ═══

    def get_available_quest_chains(self) -> list:
        """Return quest chains available to start."""
        return get_available_chains(
            self.state.character.get("level", 1),
            self.state.character.get("credits", 0),
            self.state.faction_reputation)

    def start_quest_chain(self, chain_id: str) -> dict:
        """Start a quest chain."""
        if self.active_chain:
            return {"success": False, "error": "Уже есть активная сюжетная линия"}
        if chain_id in self.completed_chains:
            return {"success": False, "error": "Эта линия уже завершена"}
        stage = get_chain_stage(chain_id, 0)
        if not stage:
            return {"success": False, "error": "Цепочка не найдена"}
        self.active_chain = {"chain_id": chain_id, "current_stage": 0}
        return {"success": True, "stage": stage}

    def advance_quest_chain(self) -> dict:
        """Advance to next stage in active chain."""
        if not self.active_chain:
            return {"success": False, "error": "Нет активной линии"}
        chain_id = self.active_chain["chain_id"]
        next_idx = self.active_chain["current_stage"] + 1
        stage = get_chain_stage(chain_id, next_idx)
        if not stage:
            # Chain complete
            self.completed_chains.append(chain_id)
            self.active_chain = {}
            return {"success": True, "complete": True, "chain_id": chain_id}
        self.active_chain["current_stage"] = next_idx
        # Apply stage rewards
        reward = stage.get("reward_credits", 0)
        if reward:
            self.add_credits(reward)
        rep_rewards = stage.get("reward_rep", {})
        if rep_rewards:
            apply_reputation_changes(self.state.faction_reputation, rep_rewards)
        return {"success": True, "stage": stage, "reward_credits": reward}

    # ═══ V5: WORLD EFFECTS QUERIES ═══

    def get_shop_price_modifier(self, category: str = "all") -> float:
        """Get current price modifier from active world effects."""
        from src.content.v4_legacy import _game_time_to_hours
        return self.world_effects.get_price_modifier(
            category, _game_time_to_hours(self.state.game_time))

    def get_world_effects_summary(self) -> list:
        from src.content.v4_legacy import _game_time_to_hours
        return self.world_effects.get_active_effects_summary(
            _game_time_to_hours(self.state.game_time))
