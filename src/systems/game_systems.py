"""
Game Systems — connects design data to actual gameplay mechanics.
Covers: quests, factions, psychology, perks, crafting, leveling, location-events.
"""
import random
from typing import Dict, List, Optional, Tuple
from src.content.base import (
    EXPANDED_PERKS, EXPANDED_RECIPES, EXPANDED_MATERIALS,
    EXPANDED_TRAVEL_EVENTS, EXPANDED_SPACE_EVENTS,
)
from src.content.v2_legacy import (
    V2_PERKS, V2_RECIPES, V2_TRAVEL_EVENTS, V2_SPACE_EVENTS,
    get_all_perks, get_all_recipes, get_all_travel_events, get_all_space_events,
)
from src.content.v3_legacy import get_all_perks_v3


# ════════════════════════════════════════════════════════════
#  QUEST TRACKER — stages, conditions, rewards, chains
# ════════════════════════════════════════════════════════════

class QuestTracker:
    """Manages quest lifecycle: accept → stages → complete/fail."""

    STAGES = ["received", "in_progress", "completed", "failed"]

    @staticmethod
    def create_quest(title: str, description: str, giver: str = "",
                     reward_credits: int = 0, reward_xp: int = 0,
                     reward_items: List = None, stages: List[str] = None,
                     chain_next: str = "") -> Dict:
        return {
            "id": f"q_{random.randint(1000,9999)}",
            "title": title,
            "description": description,
            "giver": giver,
            "status": "received",
            "current_stage": 0,
            "stages": stages or ["Начать", "Выполнить", "Завершить"],
            "reward_credits": reward_credits,
            "reward_xp": reward_xp,
            "reward_items": reward_items or [],
            "chain_next": chain_next,
            "notes": [],
        }

    @staticmethod
    def advance_quest(quest: Dict) -> Dict:
        """Move quest to next stage."""
        if quest["status"] in ("completed", "failed"):
            return quest
        quest["current_stage"] = min(quest["current_stage"] + 1, len(quest["stages"]) - 1)
        if quest["current_stage"] >= len(quest["stages"]) - 1:
            quest["status"] = "completed"
        else:
            quest["status"] = "in_progress"
        return quest

    @staticmethod
    def fail_quest(quest: Dict) -> Dict:
        quest["status"] = "failed"
        return quest

    @staticmethod
    def get_prompt_context(active_quests: List[Dict]) -> str:
        if not active_quests:
            return ""
        lines = ["## АКТИВНЫЕ КВЕСТЫ (отслеживай прогресс!):"]
        for q in active_quests[:5]:
            stages = q.get("stages", [])
            current = q.get("current_stage", 0)
            stage_str = " → ".join(
                f"[{s}]" if i == current else s
                for i, s in enumerate(stages)
            )
            lines.append(
                f"- **{q['title']}** ({q['status']}): {q['description'][:80]}"
            )
            lines.append(f"  Стадии: {stage_str}")
            if q.get("giver"):
                lines.append(f"  Квестодатель: {q['giver']}")
        return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  FACTION REPUTATION — effects on prices, access, dialogue
# ════════════════════════════════════════════════════════════

FACTION_THRESHOLDS = {
    "враг":      (-100, -51),
    "недоверие":  (-50, -21),
    "недовольство": (-20, -1),
    "нейтрально": (0, 19),
    "симпатия":   (20, 49),
    "союзник":    (50, 79),
    "легенда":    (80, 100),
}

# Major faction categories for gameplay effects
FACTION_CATEGORIES = {
    "корпорации": ["LunarTech Industries", "Helios Energy Corp", "Protogen",
                   "Genesis Bioworks", "Nexus Pharmaceuticals", "Aetherium Dynamics"],
    "военные": ["Mars Fleet", "SENTINEL PMC", "Iron Wolves", "Black Aegis",
                "Omega Defense Systems"],
    "криминал": ["Black Lotus Triad", "Shadow Consortium", "Blackwater Cartel"],
    "повстанцы": ["OPA", "Data Rebels", "Марсианская Республика"],
    "наука": ["ESA-Earth", "Genesis Bioworks", "Quantum Horizons"],
    "правительство": ["ООН Земли", "Марсианская Республика"],
}


class FactionSystem:
    """Faction reputation with gameplay consequences."""

    @staticmethod
    def get_standing(reputation: int) -> str:
        """Get faction standing label from reputation number."""
        for label, (lo, hi) in FACTION_THRESHOLDS.items():
            if lo <= reputation <= hi:
                return label
        return "враг" if reputation < -50 else "легенда"

    @staticmethod
    def get_price_modifier(faction_rep: Dict[str, int], location_factions: List[str]) -> float:
        """Calculate price modifier based on reputation with local factions."""
        if not location_factions:
            return 1.0
        mods = []
        for f in location_factions:
            rep = faction_rep.get(f, 0)
            if rep >= 50:
                mods.append(0.85)  # 15% discount
            elif rep >= 20:
                mods.append(0.93)
            elif rep <= -50:
                mods.append(1.30)  # 30% markup
            elif rep <= -20:
                mods.append(1.15)
            else:
                mods.append(1.0)
        return round(sum(mods) / len(mods), 2)

    @staticmethod
    def check_access(faction_rep: Dict[str, int], required_faction: str,
                     min_standing: str = "нейтрально") -> bool:
        """Check if player has enough reputation for access."""
        rep = faction_rep.get(required_faction, 0)
        thresholds = {"враг": -100, "недоверие": -50, "недовольство": -20,
                      "нейтрально": 0, "симпатия": 20, "союзник": 50, "легенда": 80}
        return rep >= thresholds.get(min_standing, 0)

    @staticmethod
    def modify_reputation(faction_rep: Dict[str, int], faction: str, amount: int) -> Tuple[int, str]:
        """Change reputation and return new value + standing."""
        old = faction_rep.get(faction, 0)
        new = max(-100, min(100, old + amount))
        faction_rep[faction] = new
        return new, FactionSystem.get_standing(new)

    @staticmethod
    def get_prompt_context(faction_rep: Dict[str, int]) -> str:
        """Generate faction context for AI prompt."""
        if not faction_rep:
            return ""
        lines = ["## РЕПУТАЦИЯ ФРАКЦИЙ (влияет на диалоги и цены!):"]
        for faction, rep in sorted(faction_rep.items(), key=lambda x: -abs(x[1])):
            if rep == 0:
                continue
            standing = FactionSystem.get_standing(rep)
            emoji = "💚" if rep > 20 else "❤️‍🔥" if rep < -20 else "⚪"
            lines.append(f"- {emoji} {faction}: {rep} ({standing})")
        return "\n".join(lines) if len(lines) > 1 else ""


# ════════════════════════════════════════════════════════════
#  PSYCHOLOGY — stress, humanity, morale effects
# ════════════════════════════════════════════════════════════

STRESS_EFFECTS = {
    (0, 20):   {"label": "Спокоен", "skill_mod": 0, "social_mod": 0},
    (21, 40):  {"label": "Напряжён", "skill_mod": 0, "social_mod": -1},
    (41, 60):  {"label": "Стресс", "skill_mod": -1, "social_mod": -1},
    (61, 80):  {"label": "На грани", "skill_mod": -2, "social_mod": -2},
    (81, 100): {"label": "Сломлен", "skill_mod": -3, "social_mod": -3},
}

HUMANITY_EFFECTS = {
    (0, 20):   {"label": "Машина", "empathy_blocked": True, "combat_bonus": 2, "tone": "холодный, механический"},
    (21, 40):  {"label": "Отстранённый", "empathy_blocked": True, "combat_bonus": 1, "tone": "безразличный"},
    (41, 60):  {"label": "Нормальный", "empathy_blocked": False, "combat_bonus": 0, "tone": "обычный"},
    (61, 80):  {"label": "Эмпатичный", "empathy_blocked": False, "combat_bonus": 0, "tone": "тёплый, внимательный"},
    (81, 100): {"label": "Сострадательный", "empathy_blocked": False, "combat_bonus": -1, "tone": "глубоко эмоциональный"},
}


class PsychologySystem:
    """Manages stress, humanity, and their gameplay effects."""

    @staticmethod
    def get_stress_effect(stress: int) -> Dict:
        for (lo, hi), effect in STRESS_EFFECTS.items():
            if lo <= stress <= hi:
                return effect
        return STRESS_EFFECTS[(81, 100)]

    @staticmethod
    def get_humanity_effect(humanity: int) -> Dict:
        for (lo, hi), effect in HUMANITY_EFFECTS.items():
            if lo <= humanity <= hi:
                return effect
        return HUMANITY_EFFECTS[(41, 60)]

    @staticmethod
    def apply_stress_change(character: Dict, amount: int, reason: str = "") -> Dict:
        """Change stress and return info about the change."""
        old = character.get("stress", 30)
        new = max(0, min(100, old + amount))
        character["stress"] = new
        old_effect = PsychologySystem.get_stress_effect(old)
        new_effect = PsychologySystem.get_stress_effect(new)
        return {
            "old": old, "new": new,
            "old_label": old_effect["label"],
            "new_label": new_effect["label"],
            "changed": old_effect["label"] != new_effect["label"],
            "reason": reason,
        }

    @staticmethod
    def apply_humanity_change(character: Dict, amount: int, reason: str = "") -> Dict:
        old = character.get("humanity", 60)
        new = max(0, min(100, old + amount))
        character["humanity"] = new
        old_effect = PsychologySystem.get_humanity_effect(old)
        new_effect = PsychologySystem.get_humanity_effect(new)
        return {
            "old": old, "new": new,
            "old_label": old_effect["label"],
            "new_label": new_effect["label"],
            "changed": old_effect["label"] != new_effect["label"],
            "reason": reason,
        }

    @staticmethod
    def get_skill_modifier(character: Dict) -> int:
        """Get total skill modifier from psychology."""
        stress = character.get("stress", 30)
        return PsychologySystem.get_stress_effect(stress)["skill_mod"]

    @staticmethod
    def get_social_modifier(character: Dict) -> int:
        """Get social skill modifier (negotiation, diplomacy)."""
        stress = character.get("stress", 30)
        humanity = character.get("humanity", 60)
        s_mod = PsychologySystem.get_stress_effect(stress)["social_mod"]
        h_effect = PsychologySystem.get_humanity_effect(humanity)
        if h_effect.get("empathy_blocked"):
            s_mod -= 2  # Can't connect emotionally
        return s_mod

    @staticmethod
    def get_prompt_context(character: Dict) -> str:
        stress = character.get("stress", 30)
        humanity = character.get("humanity", 60)
        s_eff = PsychologySystem.get_stress_effect(stress)
        h_eff = PsychologySystem.get_humanity_effect(humanity)

        parts = [f"## ПСИХОЛОГИЯ ПЕРСОНАЖА:"]
        parts.append(f"Стресс: {stress}/100 ({s_eff['label']}) — модификатор навыков: {s_eff['skill_mod']}")
        parts.append(f"Человечность: {humanity}/100 ({h_eff['label']}) — тон речи: {h_eff['tone']}")
        if s_eff['skill_mod'] < 0:
            parts.append(f"⚠ Высокий стресс! Персонаж может срываться, ошибаться, действовать импульсивно.")
        if h_eff.get("empathy_blocked"):
            parts.append(f"⚠ Низкая человечность! Персонаж холоден, не способен к эмпатии. NPC это чувствуют.")
        return "\n".join(parts)


# ════════════════════════════════════════════════════════════
#  PERKS — passive bonuses from leveling / quests
# ════════════════════════════════════════════════════════════

PERK_DATABASE = get_all_perks_v3()


class PerkSystem:
    """Manages character perks — selection and effects."""

    @staticmethod
    def get_available_perks(character: Dict, count: int = 3) -> List[Dict]:
        """Get perks available for selection (not already owned, no name duplicates)."""
        owned_ids = {p["id"] for p in character.get("perks", [])}
        owned_names = {p["name"] for p in character.get("perks", [])}
        # Remove already owned + name-duplicates from pool
        seen_names = set()
        available = []
        for p in PERK_DATABASE:
            if p["id"] in owned_ids or p["name"] in owned_names:
                continue
            if p["name"] in seen_names:
                continue  # skip name-duplicates (v3_ copies)
            seen_names.add(p["name"])
            available.append(p)
        # Prioritize perks matching character's top skills
        skills = character.get("skills", {})
        top_skills = sorted(skills.items(), key=lambda x: -x[1])[:3]
        top_categories = set()
        skill_to_cat = {
            "hacking": "hacking", "combat": "combat", "negotiation": "social",
            "diplomacy": "social", "stealth": "combat", "technology": "tech",
            "engineering": "tech", "piloting": "piloting", "survival": "survival",
            "criminal": "social",
        }
        for sk, _ in top_skills:
            cat = skill_to_cat.get(sk)
            if cat:
                top_categories.add(cat)

        # Mix: some matching + some random
        matching = [p for p in available if p["category"] in top_categories]
        other = [p for p in available if p["category"] not in top_categories]
        random.shuffle(matching)
        random.shuffle(other)

        result = matching[:2] + other[:1]
        if len(result) < count:
            result += other[:count - len(result)]
        return result[:count]

    @staticmethod
    def apply_perk(character: Dict, perk_id: str) -> Optional[Dict]:
        """Apply a perk to character. Returns perk data or None."""
        perk = next((p for p in PERK_DATABASE if p["id"] == perk_id), None)
        if not perk:
            return None

        owned = character.get("perks", [])
        if any(p["id"] == perk_id for p in owned):
            return None  # Already owned

        owned.append(perk)
        character["perks"] = owned

        # Apply stat effects
        for stat, bonus in perk.get("effect", {}).items():
            if stat in character.get("skills", {}):
                character["skills"][stat] += bonus
            elif stat in character.get("attributes", {}):
                character["attributes"][stat] += bonus
            elif stat == "hp_bonus":
                character["derived"] = character.get("derived", {})
                character["derived"]["health_points"] = character["derived"].get("health_points", 50) + bonus
                character["current_hp"] = character.get("current_hp", 50) + bonus

        return perk

    @staticmethod
    def get_perk_bonuses(character: Dict) -> Dict[str, int]:
        """Sum all perk bonuses for display."""
        bonuses = {}
        for perk in character.get("perks", []):
            for stat, val in perk.get("effect", {}).items():
                bonuses[stat] = bonuses.get(stat, 0) + val
        return bonuses


# ════════════════════════════════════════════════════════════
#  LEVEL UP — skill points + perk selection
# ════════════════════════════════════════════════════════════

class LevelUpSystem:
    """Handles level-up rewards: skill points and perk selection."""

    SKILL_POINTS_PER_LEVEL = 3
    PERK_EVERY_N_LEVELS = 2  # Get perk choice every 2 levels

    @staticmethod
    def process_level_up(character: Dict) -> Dict:
        """Process a level up — returns info about what player gets."""
        level = character.get("level", 1)
        result = {
            "new_level": level,
            "skill_points": LevelUpSystem.SKILL_POINTS_PER_LEVEL,
            "perk_available": level % LevelUpSystem.PERK_EVERY_N_LEVELS == 0,
            "available_perks": [],
        }

        # Add unspent skill points
        character["unspent_skill_points"] = character.get("unspent_skill_points", 0) + result["skill_points"]

        # Check for perk
        if result["perk_available"]:
            result["available_perks"] = PerkSystem.get_available_perks(character)

        return result

    @staticmethod
    def spend_skill_point(character: Dict, skill_name: str) -> bool:
        """Spend one skill point on a skill."""
        points = character.get("unspent_skill_points", 0)
        if points <= 0:
            return False
        skills = character.get("skills", {})
        if skill_name not in skills:
            return False
        skills[skill_name] += 1
        character["unspent_skill_points"] = points - 1
        return True


# ════════════════════════════════════════════════════════════
#  CRAFTING — basic blueprint system
# ════════════════════════════════════════════════════════════

CRAFTING_RECIPES = get_all_recipes()

# Crafting materials available at shops
CRAFTING_MATERIALS = EXPANDED_MATERIALS


class CraftingSystem:
    """Basic crafting: check materials, skill check, produce item."""

    @staticmethod
    def get_recipes() -> List[Dict]:
        return CRAFTING_RECIPES

    @staticmethod
    def get_materials() -> List[Dict]:
        return CRAFTING_MATERIALS

    @staticmethod
    def can_craft(recipe_id: str, inventory: List[Dict], character: Dict) -> Dict:
        """Check if player can craft a recipe. Returns status + missing items."""
        recipe = next((r for r in CRAFTING_RECIPES if r["id"] == recipe_id), None)
        if not recipe:
            return {"can_craft": False, "reason": "Рецепт не найден"}

        # Check materials
        missing = []
        for mat in recipe["materials"]:
            has = sum(1 for i in inventory if i.get("name") == mat["name"])
            if has < mat["qty"]:
                missing.append(f"{mat['name']} (нужно {mat['qty']}, есть {has})")

        # Check skill
        skill_val = character.get("skills", {}).get(recipe["skill"], 0)
        attr_val = character.get("attributes", {}).get("intelligence", 5)

        return {
            "can_craft": len(missing) == 0,
            "missing_materials": missing,
            "skill": recipe["skill"],
            "skill_value": skill_val + attr_val,
            "difficulty": recipe["difficulty"],
            "recipe": recipe,
        }

    @staticmethod
    def craft(recipe_id: str, inventory: List[Dict], character: Dict, dice_roller) -> Dict:
        """Attempt to craft. Consumes materials, does skill check."""
        check = CraftingSystem.can_craft(recipe_id, inventory, character)
        if not check["can_craft"]:
            return {"success": False, "reason": "Не хватает материалов", "missing": check["missing_materials"]}

        recipe = check["recipe"]

        # Consume materials
        for mat in recipe["materials"]:
            removed = 0
            for i in range(len(inventory) - 1, -1, -1):
                if inventory[i].get("name") == mat["name"] and removed < mat["qty"]:
                    inventory.pop(i)
                    removed += 1

        # Skill check
        skill_val = character.get("skills", {}).get(recipe["skill"], 0)
        attr_val = character.get("attributes", {}).get("intelligence", 5)
        roll_result = dice_roller.skill_check(skill_val, attr_val, 0, recipe["difficulty"])

        if roll_result["success"]:
            # Add crafted item
            item = dict(recipe["result"])
            item["qty"] = 1
            inventory.append(item)
            return {"success": True, "item": item, "roll": roll_result}
        else:
            # Failed — materials lost
            return {"success": False, "reason": "Провал! Материалы потрачены впустую.", "roll": roll_result}


# ════════════════════════════════════════════════════════════
#  LOCATION EVENTS — random encounters on travel
# ════════════════════════════════════════════════════════════

TRAVEL_EVENTS = get_all_travel_events()

SPACE_EVENTS = get_all_space_events()


class LocationEvents:
    """Generates events when player moves between locations."""

    @staticmethod
    def on_district_change(security: str = "Средний") -> Optional[Dict]:
        """Maybe trigger event when changing districts."""
        # Higher chance in low-security areas
        chance = {"Минимальный": 0.6, "Низкий": 0.4, "Средний": 0.25, "Высокий": 0.15, "Максимальный": 0.05}
        if random.random() > chance.get(security, 0.25):
            return None
        event = random.choice(TRAVEL_EVENTS)
        return event

    @staticmethod
    def on_planet_travel() -> Optional[Dict]:
        """Maybe trigger event during interplanetary travel."""
        if random.random() > 0.5:
            return None
        return random.choice(SPACE_EVENTS)
