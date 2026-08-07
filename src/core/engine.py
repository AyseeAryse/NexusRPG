"""
Game Engine - Core game state, mechanics, AI GM orchestration.
"""
import json
import os
import random
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
from src.systems.subsystems import HackingSystem, InvestigationSystem, CompanionSystem, ShipSystem, PropertySystem
# V5: Quest chains, companions, unique NPCs, auto-reputation, world effects
from src.systems.quests import QUEST_CHAINS, get_available_chains, get_chain_stage
from src.systems.companions import COMPANIONS, get_available_companions, get_companion_by_id, get_loyalty_level, get_companion_combat_bonus
from src.content.v5_legacy import (UNIQUE_NPCS, WorldEffectsManager,
    calculate_auto_reputation, apply_reputation_changes, get_reputation_summary)
# V6: Hard mechanics — buy/sell, travel, property income, conversation management
from src.systems.mechanics import (ShopMechanics, TravelSystem, PropertyIncomeManager,
    ConversationManager, detect_mechanical_action)
# V7: Combat engine, fail-forward, level up, subsystem triggers
from src.systems.combat import (CombatEngine, pick_enemies_for_encounter, apply_defeat,
    process_xp_gain, detect_subsystem_trigger)


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
        self.in_combat: bool = False
        self.combat_state: Dict = {}
        self.conversation_history: List[Dict] = []
        self.max_history = 30
        self.session_events: List[Dict] = []
        self.phase: str = "menu"
        self.world_sim: WorldSimulator = WorldSimulator()
        self.world_context: Dict = {}  # latest world tick results
        self.npc_registry: NPCRegistry = NPCRegistry()

    def to_dict(self) -> Dict:
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
            # Subsystem state — persisted since v5.0
            "_subsystems": {},  # placeholder, filled by GameEngine.save_game()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
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
        self.combat_engine = CombatEngine()  # V7: Tactical combat
        self.active_chain: dict = {}  # {chain_id, current_stage}
        self.completed_chains: list = []
        os.makedirs(self.saves_dir, exist_ok=True)
        # Cache creation data
        self._creation_data = None
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
            "roleplay_notes": preset.get("roleplay_notes", []),
            "story_hooks": preset.get("story_hooks", []),
        }
        self.state.faction_reputation = resources.get("reputation", {})
        self._set_starting_location(preset.get("lifepath", {}).get("origin", ""))
        return self.state.character

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
            "roleplay_notes": [], "story_hooks": [],
            "starting_equipment": spec_data.get("equipment", []) if spec_data else [],
        }

        # Set starting inventory from equipment
        if spec_data and spec_data.get("equipment"):
            for eq in spec_data["equipment"]:
                self.state.inventory.append({"name": eq, "qty": 1, "type": "equipment"})

        self._set_starting_location(origin_id)
        self._enforce_skill_caps()
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
        self.state.conversation_history.append({"role": "user", "content": action})

        # === V7: COMBAT ROUTING — if in combat, handle combat turn ===
        if self.combat_engine.in_combat:
            return self._process_combat_turn(action)

        # === V7: SUBSYSTEM TRIGGER — detect hacking/investigation/crafting/combat ===
        subsystem = detect_subsystem_trigger(action)
        subsystem_result = None
        if subsystem:
            subsystem_result = self._handle_subsystem_trigger(subsystem, action)
            # If combat was started, route to combat
            if subsystem_result and subsystem_result.get("combat_started"):
                return subsystem_result

        mechanical_result = self._check_mechanical_action(action)

        # === V6: DETECT BUY/SELL/TRAVEL MECHANICAL ACTIONS ===
        mech_action = detect_mechanical_action(action)
        mech_action_result = None
        if mech_action:
            mech_action_result = self._handle_mechanical_action(mech_action)

        # === V6: CONVERSATION MANAGEMENT — compress old history ===
        ConversationManager.manage_history(self.state.conversation_history)

        # === WORLD SIMULATION TICK ===
        tier = self.get_player_influence_tier()["tier"]
        self.state.world_context = self.state.world_sim.tick(
            self.state.game_time, self.state.current_location, tier
        )

        # === WORLD TICKER — major events ===
        world_events = self.world_ticker.tick(self.state)
        if world_events:
            self.state.world_context["world_events"] = world_events
            # V5: Apply event effects to world (prices, lockdowns, etc.)
            from src.content.v4_legacy import _game_time_to_hours
            current_h = _game_time_to_hours(self.state.game_time)
            for we in world_events:
                self.world_effects.apply_event_effects(we, current_h)

        # === CONSEQUENCES — check for delayed reactions ===
        turn = self.state.world_sim.turn_count
        triggered_consequences = self.consequences.check_consequences(turn)
        if triggered_consequences:
            self.state.world_context["consequences"] = triggered_consequences

        # === V5: AUTO-REPUTATION — analyze action for faction impact ===
        rep_changes = calculate_auto_reputation(action, self.state.faction_reputation)
        if rep_changes:
            apply_reputation_changes(self.state.faction_reputation, rep_changes)
            self.state.world_context["rep_changes"] = get_reputation_summary(rep_changes)

        # === V5: WORLD EFFECTS CONTEXT — active price mods, lockdowns ===
        from src.content.v4_legacy import _game_time_to_hours as _gth
        active_fx = self.world_effects.get_active_effects_summary(_gth(self.state.game_time))
        if active_fx:
            self.state.world_context["active_world_effects"] = active_fx

        # === V5: QUEST CHAIN — check if player should be offered one ===
        from src.content.v4_legacy import _game_time_to_hours as _gth2
        current_hours = _gth2(self.state.game_time)
        # Offer every 5-10 game-days (120-240 hours)
        if not hasattr(self, '_last_chain_offer_h'):
            self._last_chain_offer_h = current_hours - random.randint(100, 200)
        chain_cooldown = random.randint(120, 240)
        if not self.active_chain and (current_hours - self._last_chain_offer_h) >= chain_cooldown:
            available = get_available_chains(
                self.state.character.get("level", 1),
                self.state.character.get("credits", 0),
                self.state.faction_reputation)
            # Filter out completed chains
            available = [c for c in available if c["id"] not in self.completed_chains]
            if available:
                offer = random.choice(available)
                self.state.world_context["chain_offer"] = offer
                self._last_chain_offer_h = current_hours

        # === Maybe generate procedural quest (every 2-5 game-days) ===
        if not hasattr(self, '_last_quest_gen_h'):
            self._last_quest_gen_h = current_hours - random.randint(30, 80)
        quest_cooldown_h = random.randint(48, 120)  # 2-5 days
        if (current_hours - self._last_quest_gen_h) >= quest_cooldown_h and len(self.state.active_quests) < 5:
            pq = self.quest_generator.generate_quest(
                player_level=self.state.character.get("level", 1),
                location=self.state.current_location,
                faction_standings=self.state.faction_reputation,
            )
            self.state.active_quests.append(pq)
            self._last_quest_gen_h = current_hours
            self.state.world_context["new_quest"] = pq

        # === V6: PROPERTY INCOME — collect rent on time tick ===
        income_result = self.property_income.tick(current_hours, self.property,
                                                   self.state.character)
        if income_result:
            self.state.world_context["property_income"] = income_result

        system_prompt = self._build_system_prompt(action, mechanical_result,
                                                   mech_action_result, subsystem_result)
        ai_response = self.ai.generate(system_prompt=system_prompt, messages=self.state.conversation_history[-12:])
        parsed = self._parse_ai_response(ai_response)
        self.state.conversation_history.append({"role": "assistant", "content": parsed["narrative"]})
        self.state.session_events.append({
            "time": dict(self.state.game_time),
            "action": action[:100], "result": parsed["narrative"][:100],
        })
        # Use AI-determined time if available, else random
        time_mins = parsed.get("state_changes", {}).get("_custom_time", random.randint(5, 30))
        self._advance_time(minutes=time_mins)

        # === V7: PROPER XP → LEVEL UP ===
        xp_to_add = parsed.get("state_changes", {}).get("_xp_to_add", 0)
        level_up_info = None
        if xp_to_add and xp_to_add > 0:
            level_up_info = process_xp_gain(self.state.character, xp_to_add)

        # === V7: HP=0 DEFEAT CHECK (fail-forward, no permadeath) ===
        defeat_result = None
        if self.state.character.get("current_hp", 1) <= 0:
            defeat_result = apply_defeat(
                self.state.character, self.state.inventory,
                self.state.game_time, self.state.current_location
            )

        return {
            "narrative": parsed["narrative"],
            "dice_results": mechanical_result,
            "state_changes": parsed.get("state_changes", {}),
            "game_state": self._get_client_state(),
            "world_events": [e["text"] for e in world_events] if world_events else [],
            "consequences": [c["text"] for c in triggered_consequences] if triggered_consequences else [],
            "new_quest": self.state.world_context.get("new_quest"),
            "rep_changes": self.state.world_context.get("rep_changes", ""),
            "chain_offer": self.state.world_context.get("chain_offer"),
            "mechanical_action": mech_action_result,
            "property_income": income_result,
            "defeat": defeat_result,
            "level_up": level_up_info,
            "subsystem": subsystem_result,
        }

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
        char = self.state.character
        loc = self.state.current_location
        kb_context = self.kb.get_relevant_context(action, max_tokens=1200)
        wc = self.state.world_context  # world sim tick results

        # ─── CORE IDENTITY (always included, ~400 chars) ───
        parts = [
            "# ТЫ — ИИ ГМ текстовой RPG «NEXUS». Sci-fi нуар, 2387г.",
            "The Expanse+Cyberpunk+MGS. БЕЗ FTL/пришельцев/магии. Протомолекула=нанотех.",
            "",
            "## ПРАВИЛА ПИСЬМА:",
            "МИНИМУМ 3-4 АБЗАЦА текста в КАЖДОМ ответе. Пиши ПОДРОБНО и КИНЕМАТОГРАФИЧНО.",
            "Каждый абзац: 3+ предложения. Описывай окружение, атмосферу, звуки, запахи.",
            "ОБЯЗАТЕЛЬНО: 3+ сенсорных деталей (свет/звук/запах/тактильность/температура/вкус воздуха), "
            "2+ конкретных названий из мира (бренды/вывески/модели техники), "
            "1 фоновое действие (что делают другие вокруг), 1 неожиданная деталь.",
            "NPC: ВСЕГДА имя+внешность+манера речи+одежда. НЕ «мужчина сказал», А «Кэнджи Ито — худой, за 50, кибернетический глаз "
            "Zeiss-Mitsui мерцает синим, хриплый белтерский акцент, засаленный комбинезон с нашивкой OPA».",
            "Диалоги NPC: 2-3 фразы минимум, с характерной речью и эмоциями. Не одна строчка!",
            "СТИЛЬ: как будто описываешь сцену для фильма. Тёмные тона, неоновые блики, тяжёлая атмосфера.",
            "ЗАПРЕЩЕНО: короткие ответы менее 3 абзацев, сухие описания, безымянные NPC, мысли/чувства игрока, повтор вариантов.",
            "",
        ]

        # ─── WORLD CONTEXT (conditional, ~200 chars) ───
        if wc:
            wc_parts = []
            if wc.get("atmosphere"): wc_parts.append(f"Атмосфера: {wc['atmosphere']}")
            if wc.get("background_npcs"): wc_parts.append(f"Фон: {wc['background_npcs']}")
            if wc.get("news"): wc_parts.append(f"Новость: {wc['news'][0]}")
            if wc.get("rumors"): wc_parts.append(f"Слух: {wc['rumors'][0]}")
            if wc_parts:
                parts.append("## МИР СЕЙЧАС (впиши в сцену!):")
                parts.extend(wc_parts)
                parts.append("")

        # ─── CHARACTER + LOCATION (always, ~500 chars) ───
        attrs_compact = ", ".join(f"{k[:3]}:{v}" for k, v in char.get("attributes", {}).items())
        skills_compact = ", ".join(f"{k}:{v}" for k, v in char.get("skills", {}).items() if v > 0)
        parts += [
            f"## ПЕРСОНАЖ: {char.get('name','?')} | Lv{char.get('level',1)} | HP:{char.get('current_hp',50)}/{char.get('derived',{}).get('health_points',50)} | ₡{char.get('credits',0):,}",
            f"Рассудок:{char.get('current_sanity',50)} Стресс:{char.get('stress',0)} Человечность:{char.get('humanity',50)}",
            f"Атр: {attrs_compact}",
            f"Навыки: {skills_compact}",
            f"Происхождение: {char.get('origin_name', char.get('origin', '?'))} | Спец: {char.get('specialization_name', char.get('specialization', '?'))}",
            f"## ГДЕ: {loc.get('planet','?')} > {loc.get('city','?')} > {loc.get('district','')} | {self._format_game_time()}",
        ]
        # Galaxy map context (short)
        gm_ctx = self.galaxy_map.get_prompt_context(loc)
        if gm_ctx:
            parts.append(gm_ctx[:300])
        parts.append("")

        # ─── DICE RESULT (conditional, ~200 chars) ───
        if dice_result:
            result_word = "УСПЕХ" if dice_result['success'] else "ПРОВАЛ"
            parts.append(f"## 🎲 БРОСОК: {dice_result['skill']}+{dice_result['attribute']} = {dice_result['result']} vs DC{dice_result['difficulty']} → **{result_word}** ({dice_result['quality']})")
            parts.append("")

        # ─── MECHANICAL RESULT (conditional, ~200 chars) ───
        if mech_result:
            parts.append("## ⚙️ МЕХАНИКА (уже применено):")
            mt = mech_result.get("type", "")
            if mt == "buy" and mech_result.get("success"):
                parts.append(f"✅ Купил: {mech_result['bought']} за ₡{mech_result['price']}. Осталось: ₡{mech_result['credits_left']}")
            elif mt == "buy":
                parts.append(f"❌ Не купил: {mech_result.get('error','?')}")
            elif mt == "sell" and mech_result.get("success"):
                parts.append(f"✅ Продал: {mech_result['sold']} за ₡{mech_result['earned']}")
            elif mt in ("travel", "travel_planet") and mech_result.get("success"):
                parts.append(f"✅ Перемещение: → {mech_result.get('to', mech_result.get('to_planet','?'))}")
                enc = mech_result.get("encounter")
                if enc: parts.append(f"⚠️ Встреча: {enc.get('text','')[:80]}")
            elif mech_result.get("error"):
                parts.append(f"❌ {mech_result['error']}")
            parts.append("НЕ дублируй цифры в [STATE]!")
            parts.append("")

        # ─── SUBSYSTEM (conditional, ~100 chars) ───
        if subsystem_result:
            parts.append(f"## 🔧 {subsystem_result.get('system','').upper()}: {subsystem_result.get('narrative','')[:120]}")
            parts.append("")

        # ─── COMBAT (conditional, ~200 chars) ───
        combat_ctx = self.combat_engine.get_prompt_context()
        if combat_ctx:
            parts.append(combat_ctx)
            parts.append("")

        # ─── QUESTS (conditional, ~200 chars) ───
        all_quests = self.state.active_quests
        if all_quests:
            parts.append("## КВЕСТЫ: " + " | ".join(f"{q.get('title','?')}" for q in all_quests[:4]))

        # ─── QUEST CHAIN (conditional, ~200 chars) ───
        if self.active_chain:
            chain_id = self.active_chain.get("chain_id")
            stage_idx = self.active_chain.get("current_stage", 0)
            stage = get_chain_stage(chain_id, stage_idx)
            if stage:
                parts.append(f"## СЮЖЕТ: «{stage['chain_name']}» ({stage['stage_num']}/{stage['total_stages']}): {stage['title']}")
                parts.append(f"Цели: {', '.join(stage.get('objectives', []))}")
                if stage.get("branching"): parts.append("⚠️ КЛЮЧЕВОЙ ВЫБОР!")
                parts.append("")

        # ─── NPC CONTEXT (conditional, ~400 chars) ───
        npc_context = self.state.npc_registry.get_prompt_context(limit=5)
        if npc_context:
            parts.append(npc_context)
            parts.append("")

        # ─── UNIQUE NEARBY NPCs (conditional, ~300 chars) ───
        current_planet = loc.get("planet", "")
        current_city = loc.get("city", "")
        nearby_npcs = [n for n in UNIQUE_NPCS
                       if current_planet in n.get("location", "") or current_city in n.get("location", "")
                       or "Любой" in n.get("location", "") or "Меняет" in n.get("location", "")]
        if nearby_npcs:
            hour = self.state.game_time.get("hour", 12)
            time_period = "day" if 6 <= hour < 22 else "night"
            parts.append(f"## NPC РЯДОМ ({hour:02d}:00):")
            for npc in nearby_npcs[:3]:
                activity = npc.get("schedule", {}).get(time_period, "?")
                parts.append(f"• {npc['name']} ({npc['role']}): {activity}")
            parts.append("")

        # ─── COMPANIONS (conditional, ~200 chars) ───
        if self.active_companions:
            parts.append("## ГРУППА:")
            for cs in self.active_companions[:3]:
                comp = get_companion_by_id(cs["id"])
                if comp:
                    parts.append(f"• {comp['name']} «{comp['nickname']}» — {comp['type']}, лояльность {cs.get('loyalty',50)}%")
            parts.append("Компаньоны КОММЕНТИРУЮТ и РЕАГИРУЮТ!")
            parts.append("")

        # ─── INVENTORY (always, ~200 chars) ───
        if self.state.inventory:
            inv_compact = ", ".join(f"{i.get('name','?')}x{i.get('qty',1)}" for i in self.state.inventory[:8])
            parts.append(f"## ИНВЕНТАРЬ: {inv_compact}")
            parts.append("")

        # ─── REPUTATION / PSYCHOLOGY (conditional, ~150 chars) ───
        if self.state.faction_reputation:
            rep_compact = ", ".join(f"{k}:{v:+d}" for k, v in self.state.faction_reputation.items() if v != 0)
            if rep_compact:
                parts.append(f"## РЕПУТАЦИЯ: {rep_compact}")

        rep_summary = self.state.world_context.get("rep_changes", "")
        if rep_summary:
            parts.append(f"Изменение: {rep_summary}")

        psych_ctx = PsychologySystem.get_prompt_context(self.state.character)
        if psych_ctx:
            parts.append(psych_ctx[:200])
        parts.append("")

        # ─── WORLD EFFECTS (conditional, ~150 chars) ───
        active_fx = self.state.world_context.get("active_world_effects", [])
        if active_fx:
            parts.append("## МИРОВЫЕ ЭФФЕКТЫ: " + "; ".join(f"{fx['effect']}:{fx['value']}" for fx in active_fx[:3]))
            if self.world_effects.is_martial_law(): parts.append("⚠️ ВОЕННОЕ ПОЛОЖЕНИЕ!")
            parts.append("")

        # ─── KB REFERENCE (conditional, reduced to 1500 chars) ───
        if kb_context:
            parts += ["## СПРАВКА:", kb_context[:1500], ""]

        # ─── INFLUENCE TIER (always, ~60 chars) ───
        tier_info = self.get_player_influence_tier()
        parts.append(f"Тир влияния: {tier_info['tier']} — {tier_info['name']}")

        # ─── RECENT EVENTS (conditional, ~200 chars) ───
        if self.state.session_events:
            recent = " | ".join(e.get("action", "?")[:30] for e in self.state.session_events[-4:])
            parts.append(f"Недавно: {recent} — НЕ ПОВТОРЯЙ, двигай вперёд!")

        # ─── SUBSYSTEM STATUS (conditional, ~200 chars) ───
        for sys in [self.hacking, self.investigation, self.companions, self.ship, self.property]:
            ctx = sys.get_prompt_context()
            if ctx:
                parts.append(ctx)

        # ─── CHAIN OFFER / NEW QUEST (conditional) ───
        chain_offer = self.state.world_context.get("chain_offer")
        if chain_offer:
            parts.append(f"🆕 Доступна линия: «{chain_offer['name']}» — намекни через NPC")

        new_q = self.state.world_context.get("new_quest")
        if new_q:
            parts.append(f"🆕 Квест: «{new_q['title']}» — намекни")

        # ─── NEWS (conditional, ~100 chars) ───
        if self.state.world_sim.news_history:
            parts.append(f"Фон-новости: {self.state.world_sim.news_history[-1][:80]}")

        parts.append("")
        parts.append("Пиши на русском. ПОДРОБНАЯ кинематографичная сцена МИНИМУМ 3-4 абзаца + варианты.")
        parts.append("Каждый абзац — 3+ предложений. Описывай обстановку, людей, звуки, свет, атмосферу.")

        # ─── ВАРИАНТЫ ДЕЙСТВИЙ (always, ~250 chars) ───
        parts += [
            "",
            "## В КОНЦЕ — 6 вариантов + свободный:",
            "**Что будешь делать?**",
            "1.[конкретное] 2.[агрессивное] 3.[социальное] 4.[рискованное] 5.[скрытное] 6.[креативное] 7.Свой вариант",
            "",
        ]

        # ─── STATE BLOCK FORMAT (always, ~600 chars) ───
        parts += [
            "## [STATE] БЛОК (после вариантов, скрыт от игрока):",
            '[STATE]{"hp_change":0,"credits_change":0,"stress_change":0,"humanity_change":0,',
            '"location":null,"add_items":[],"remove_items":[],',
            '"npc_met":null,"quest_complete":null,"quest_advance":false,',
            '"combat_started":false,"combat_ended":false,"time_minutes":15,"xp_gained":0}[/STATE]',
            "hp_change: урон отрицат./лечение полож. | credits_change: +получил/-потратил",
            'location: {"planet":"X","city":"Y","district":"Z"} если перешёл, null если нет',
            'add_items: [{"name":"X","qty":1}] | remove_items: ["X"] | npc_met: "Имя" | time: 5-120мин | xp: 0-50',
        ]

        return "\n".join(parts)

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
                # Advance time for long travel
                self._advance_time(minutes=travel_result.get("travel_minutes", 60))
            result.update(travel_result)

        return result

    # ========== V7: COMBAT TURN HANDLER ==========

    def _process_combat_turn(self, action: str) -> Dict:
        """Handle a combat round when in_combat is True."""
        # Determine weapon damage from inventory
        weapon_dmg = "1d6"  # default: fists/basic
        for item in self.state.inventory:
            stats = item.get("stats", "")
            if "урон" in stats.lower() or "d" in stats:
                # Extract damage formula
                import re
                m = re.search(r'(\d+d\d+(?:\+\d+)?)', stats)
                if m:
                    weapon_dmg = m.group(1)
                    break

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
                "skills": char.get("skills", {}),
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

        quest_hints = ""
        if self.state.active_quests:
            titles = [q["title"] for q in self.state.active_quests[:3]]
            quest_hints = f"Активные квесты персонажа: {', '.join(titles)}. Намекни на первый из них в сцене. "

        intro_prompt = (
            f"Начни игру! ПЕРВАЯ сцена. Персонаж {character_name}, "
            f"происхождение: {origin_name}, специализация: {spec_name}. "
            f"{'Предыстория: ' + backstory + '. ' if backstory else ''}"
            f"Прибыл в {self.state.current_location['city']} на планете {self.state.current_location['planet']}. "
            f"{quest_hints}"
            f"Опиши атмосферное начало. Представь окружение, намекни на возможные приключения и контакты. "
            f"В конце ОБЯЗАТЕЛЬНО дай ровно 6 пронумерованных вариантов действий + 7й свободный."
        )
        return self.process_player_action(intro_prompt)

    def _assign_starting_quests(self, origin_id: str, spec_id: str):
        """Assign 2-3 starting quests from STARTING_QUESTS_COMPLETE.json."""
        try:
            quest_data = self.kb.get_file("STARTING_QUESTS_COMPLETE.json")
            if not quest_data:
                quest_data = self.kb.get_file("STARTING_QUESTS.json")
            if not quest_data:
                return

            data = quest_data.get("data", quest_data)

            # 1) Origin quest
            for q in data.get("origin_quests", []):
                req = q.get("origin", q.get("required_lifepath", [""])[0] if isinstance(q.get("required_lifepath"), list) else "")
                if req == origin_id:
                    self.state.active_quests.append(
                        QuestTracker.create_quest(
                            title=q["title"], description=q["description"],
                            giver=q.get("giver", ""), reward_credits=q.get("reward_credits", 0),
                            reward_xp=q.get("reward_xp", 200), stages=q.get("stages"),
                        )
                    )
                    break

            # 2) Specialization quest
            for q in data.get("specialization_quests", []):
                req = q.get("specialization", q.get("required_specialization", ""))
                if req == spec_id:
                    self.state.active_quests.append(
                        QuestTracker.create_quest(
                            title=q["title"], description=q["description"],
                            giver=q.get("giver", ""), reward_credits=q.get("reward_credits", 0),
                            reward_xp=q.get("reward_xp", 200), stages=q.get("stages"),
                        )
                    )
                    break

            # 3) Universal quest (random one)
            import random
            universals = data.get("universal_quests", [])
            if universals:
                uq = random.choice(universals)
                self.state.active_quests.append(
                    QuestTracker.create_quest(
                        title=uq["title"], description=uq["description"],
                        giver=uq.get("giver", ""), reward_credits=uq.get("reward_credits", 0),
                        reward_xp=uq.get("reward_xp", 200), stages=uq.get("stages"),
                    )
                )
        except Exception as e:
            print(f"[WARN] Failed to assign starting quests: {e}")

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

    def _enforce_skill_caps(self):
        """Enforce skill and attribute caps based on character level."""
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

    def get_player_influence_tier(self) -> dict:
        """Get current player influence tier and event role."""
        credits = self.state.character.get("credits", 0)
        tier = get_player_tier(credits)
        info = PLAYER_TIERS[tier]
        return {
            "tier": tier,
            "name": info["name"],
            "event_role": info["event_role"],
        }

    def add_credits(self, amount):
        self.state.character["credits"] = self.state.character.get("credits", 0) + amount

    def add_item(self, item):
        self.state.inventory.append(item)

    def get_inventory(self):
        return self.state.inventory

    def get_quests(self):
        return {"active": self.state.active_quests, "completed": self.state.completed_quests}

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
