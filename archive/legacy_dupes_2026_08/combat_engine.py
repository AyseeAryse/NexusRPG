"""
combat_engine.py — NEXUS RPG v4.7
Tactical combat system + Fail-Forward defeat + Level Up integration
+ Hacking/Investigation/Crafting trigger detection

Design philosophy from MECHANICS.json:
  "fail_forward": неудача не останавливает историю, а усложняет её
  
No permadeath. HP=0 → defeat → consequences (capture, injury, loss).
"""

import random
import re
from typing import Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════
#  ENEMY TEMPLATES
# ════════════════════════════════════════════════════════════

ENEMY_TEMPLATES = {
    # ═══ TIER 0 — Street Level (player lv 1-3) ═══
    "thug": {"name": "Головорез", "hp": 20, "attack": 3, "defense": 1,
             "initiative": 4, "damage": "1d6", "xp": 15, "loot_credits": (50, 200),
             "tactics": "aggressive", "abilities": []},
    "pickpocket": {"name": "Карманник", "hp": 12, "attack": 2, "defense": 3,
                   "initiative": 7, "damage": "1d4", "xp": 10, "loot_credits": (20, 100),
                   "tactics": "flee_at_50", "abilities": ["steal"]},
    "gang_member": {"name": "Бандит", "hp": 25, "attack": 4, "defense": 2,
                    "initiative": 5, "damage": "1d6+2", "xp": 20, "loot_credits": (100, 400),
                    "tactics": "aggressive", "abilities": []},
    "junkie": {"name": "Торчок с ножом", "hp": 14, "attack": 3, "defense": 0,
               "initiative": 3, "damage": "1d6+1", "xp": 10, "loot_credits": (5, 50),
               "tactics": "aggressive", "abilities": ["frenzy"]},
    "scavenger": {"name": "Падальщик", "hp": 18, "attack": 3, "defense": 2,
                  "initiative": 5, "damage": "1d6", "xp": 12, "loot_credits": (30, 150),
                  "tactics": "flee_at_50", "abilities": ["scrounge"]},
    "street_samurai": {"name": "Уличный самурай", "hp": 28, "attack": 5, "defense": 2,
                       "initiative": 6, "damage": "1d8+1", "xp": 25, "loot_credits": (100, 350),
                       "tactics": "aggressive", "abilities": ["quick_draw"]},
    # ═══ TIER 1 — Professional (player lv 4-6) ═══
    "mercenary": {"name": "Наёмник", "hp": 35, "attack": 5, "defense": 3,
                  "initiative": 6, "damage": "1d8+2", "xp": 35, "loot_credits": (200, 800),
                  "tactics": "tactical", "abilities": ["aimed_shot"]},
    "security_guard": {"name": "Охранник", "hp": 30, "attack": 4, "defense": 4,
                       "initiative": 5, "damage": "1d6+1", "xp": 25, "loot_credits": (100, 300),
                       "tactics": "defensive", "abilities": ["call_backup"]},
    "pirate": {"name": "Пират", "hp": 30, "attack": 5, "defense": 2,
               "initiative": 6, "damage": "1d8+1", "xp": 30, "loot_credits": (300, 1000),
               "tactics": "aggressive", "abilities": ["boarding"]},
    "bounty_hunter": {"name": "Охотник за головами", "hp": 38, "attack": 6, "defense": 3,
                      "initiative": 7, "damage": "1d8+3", "xp": 40, "loot_credits": (300, 1200),
                      "tactics": "tactical", "abilities": ["tracking", "bola"]},
    "opa_militant": {"name": "Боевик OPA", "hp": 32, "attack": 5, "defense": 3,
                     "initiative": 6, "damage": "1d8+2", "xp": 30, "loot_credits": (150, 600),
                     "tactics": "guerrilla", "abilities": ["improvised_explosive"]},
    "smuggler": {"name": "Контрабандист", "hp": 28, "attack": 4, "defense": 3,
                 "initiative": 7, "damage": "1d6+2", "xp": 25, "loot_credits": (400, 1500),
                 "tactics": "flee_at_50", "abilities": ["smoke_bomb", "hidden_weapon"]},
    "rogue_drone": {"name": "Сбойный боевой дрон", "hp": 25, "attack": 5, "defense": 5,
                    "initiative": 8, "damage": "1d8+1", "xp": 30, "loot_credits": (100, 400),
                    "tactics": "aggressive", "abilities": ["scanner", "self_destruct"]},
    "cyber_psycho": {"name": "Киберпсихопат", "hp": 45, "attack": 6, "defense": 2,
                     "initiative": 4, "damage": "1d10+3", "xp": 45, "loot_credits": (200, 800),
                     "tactics": "aggressive", "abilities": ["frenzy", "pain_resist"]},
    # ═══ TIER 2 — Elite (player lv 7-9) ═══
    "corporate_agent": {"name": "Корп-агент", "hp": 40, "attack": 6, "defense": 5,
                        "initiative": 7, "damage": "1d10+3", "xp": 50, "loot_credits": (500, 2000),
                        "tactics": "tactical", "abilities": ["emp_grenade", "tactical_retreat"]},
    "mcrn_marine": {"name": "Марсианский морпех", "hp": 50, "attack": 7, "defense": 5,
                    "initiative": 7, "damage": "1d10+4", "xp": 60, "loot_credits": (300, 1000),
                    "tactics": "tactical", "abilities": ["suppressive_fire", "power_armor"]},
    "assassin": {"name": "Ассасин", "hp": 30, "attack": 8, "defense": 4,
                 "initiative": 9, "damage": "2d6+3", "xp": 70, "loot_credits": (1000, 3000),
                 "tactics": "alpha_strike", "abilities": ["stealth_attack", "poison"]},
    "protogen_operative": {"name": "Оперативник Протоген", "hp": 48, "attack": 7, "defense": 6,
                           "initiative": 7, "damage": "1d10+4", "xp": 65, "loot_credits": (800, 2500),
                           "tactics": "tactical", "abilities": ["stim_inject", "tactical_retreat"]},
    "sentinel_commando": {"name": "Коммандо SENTINEL", "hp": 55, "attack": 7, "defense": 5,
                          "initiative": 6, "damage": "2d6+3", "xp": 60, "loot_credits": (400, 1500),
                          "tactics": "tactical", "abilities": ["flashbang", "breach_charge"]},
    "black_lotus_enforcer": {"name": "Исполнитель Чёрного Лотоса", "hp": 42, "attack": 7, "defense": 4,
                             "initiative": 8, "damage": "1d10+3", "xp": 55, "loot_credits": (600, 2000),
                             "tactics": "alpha_strike", "abilities": ["poison", "martial_arts"]},
    "rogue_ai_shell": {"name": "Дрон ИИ-отщепенца", "hp": 60, "attack": 6, "defense": 7,
                       "initiative": 5, "damage": "1d10+2", "xp": 55, "loot_credits": (200, 600),
                       "tactics": "defensive", "abilities": ["hacking_attack", "shield_regen"]},
    # ═══ TIER 3 — Boss (player lv 10+) ═══
    "crime_boss": {"name": "Криминальный босс", "hp": 60, "attack": 6, "defense": 6,
                   "initiative": 5, "damage": "1d10+5", "xp": 100, "loot_credits": (2000, 10000),
                   "tactics": "defensive", "abilities": ["bodyguards", "intimidate"]},
    "mech_suit": {"name": "Боевой экзоскелет", "hp": 80, "attack": 8, "defense": 8,
                  "initiative": 3, "damage": "2d8+5", "xp": 120, "loot_credits": (1000, 5000),
                  "tactics": "aggressive", "abilities": ["heavy_armor", "rockets"]},
    "warlord": {"name": "Военный лорд Пояса", "hp": 70, "attack": 8, "defense": 6,
                "initiative": 6, "damage": "2d6+5", "xp": 110, "loot_credits": (3000, 12000),
                "tactics": "tactical", "abilities": ["rally_troops", "power_armor", "intimidate"]},
    "corporate_director": {"name": "Директор корпорации", "hp": 45, "attack": 5, "defense": 7,
                           "initiative": 8, "damage": "1d8+3", "xp": 90, "loot_credits": (5000, 20000),
                           "tactics": "defensive", "abilities": ["bodyguards", "emp_grenade", "bribe"]},
    "prototype_mech": {"name": "Прототип «Титан»", "hp": 120, "attack": 10, "defense": 9,
                       "initiative": 2, "damage": "2d10+6", "xp": 200, "loot_credits": (2000, 8000),
                       "tactics": "aggressive", "abilities": ["heavy_armor", "rockets", "shield_regen"]},
    "rogue_ai_core": {"name": "Ядро ИИ-отщепенца", "hp": 100, "attack": 9, "defense": 8,
                      "initiative": 10, "damage": "2d8+4", "xp": 180, "loot_credits": (1000, 5000),
                      "tactics": "tactical", "abilities": ["hacking_attack", "drone_swarm", "emp_grenade"]},
    "protomolecule_hybrid": {"name": "Протомолекулярный гибрид", "hp": 150, "attack": 10, "defense": 6,
                             "initiative": 5, "damage": "3d6+5", "xp": 250, "loot_credits": (500, 2000),
                             "tactics": "aggressive", "abilities": ["regeneration", "frenzy", "bio_attack"]},
}

# Scale enemies to player level
def scale_enemy(template_key: str, player_level: int) -> Dict:
    """Create enemy instance scaled to player level."""
    t = ENEMY_TEMPLATES.get(template_key, ENEMY_TEMPLATES["thug"])
    level_bonus = max(0, player_level - 1)
    enemy = {
        "id": f"enemy_{random.randint(1000,9999)}",
        "template": template_key,
        "name": t["name"],
        "hp": t["hp"] + level_bonus * 3,
        "max_hp": t["hp"] + level_bonus * 3,
        "attack": t["attack"] + level_bonus // 2,
        "defense": t["defense"] + level_bonus // 3,
        "initiative": t["initiative"],
        "damage_formula": t["damage"],
        "xp_value": t["xp"] + level_bonus * 5,
        "loot_credits": t["loot_credits"],
        "tactics": t["tactics"],
        "abilities": list(t["abilities"]),
        "status_effects": [],
        "turns_alive": 0,
    }
    return enemy

def pick_enemies_for_encounter(player_level: int, difficulty: str = "normal") -> List[Dict]:
    """Generate enemies appropriate for player level and difficulty."""
    tier_map = {
        (1, 3): ["thug", "pickpocket", "gang_member", "junkie", "scavenger", "street_samurai"],
        (4, 6): ["gang_member", "street_samurai", "mercenary", "security_guard", "pirate",
                  "bounty_hunter", "opa_militant", "smuggler", "rogue_drone", "cyber_psycho"],
        (7, 9): ["mercenary", "bounty_hunter", "corporate_agent", "mcrn_marine", "assassin",
                  "protogen_operative", "sentinel_commando", "black_lotus_enforcer", "rogue_ai_shell"],
        (10, 99): ["corporate_agent", "assassin", "crime_boss", "mech_suit", "warlord",
                    "corporate_director", "prototype_mech", "rogue_ai_core", "protomolecule_hybrid"],
    }
    pool = []
    for (lo, hi), templates in tier_map.items():
        if lo <= player_level <= hi:
            pool = templates
            break
    if not pool:
        pool = ["thug"]

    count_map = {"easy": 1, "normal": random.randint(1, 2), "hard": random.randint(2, 3), "boss": 1}
    count = count_map.get(difficulty, 1)

    if difficulty == "boss":
        # Pick highest tier available
        boss_pool = ["crime_boss", "mech_suit", "assassin"]
        template = random.choice([t for t in boss_pool if t in pool] or pool)
        return [scale_enemy(template, player_level)]

    enemies = []
    for _ in range(count):
        template = random.choice(pool)
        enemies.append(scale_enemy(template, player_level))
    return enemies


# ════════════════════════════════════════════════════════════
#  WEAPON DAMAGE PARSING
# ════════════════════════════════════════════════════════════

WEAPON_DAMAGE_MAP = {
    # From inventory item stats field
    "1d4": (1, 4, 0), "1d6": (1, 6, 0), "1d6+1": (1, 6, 1), "1d6+2": (1, 6, 2),
    "1d8": (1, 8, 0), "1d8+1": (1, 8, 1), "1d8+2": (1, 8, 2), "1d8+3": (1, 8, 3),
    "1d10": (1, 10, 0), "1d10+2": (1, 10, 2), "1d10+3": (1, 10, 3), "1d10+4": (1, 10, 4),
    "1d10+5": (1, 10, 5),
    "2d6": (2, 6, 0), "2d6+2": (2, 6, 2), "2d6+3": (2, 6, 3),
    "2d8": (2, 8, 0), "2d8+3": (2, 8, 3), "2d8+5": (2, 8, 5),
    "3d6": (3, 6, 0),
}

def roll_damage(formula: str) -> int:
    """Roll damage from formula like '2d6+3'."""
    parsed = WEAPON_DAMAGE_MAP.get(formula)
    if parsed:
        count, sides, bonus = parsed
        return sum(random.randint(1, sides) for _ in range(count)) + bonus
    # Fallback: parse manually
    m = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', formula)
    if m:
        count, sides = int(m.group(1)), int(m.group(2))
        bonus = int(m.group(3)) if m.group(3) else 0
        return sum(random.randint(1, sides) for _ in range(count)) + bonus
    return random.randint(2, 8)  # fallback


# ════════════════════════════════════════════════════════════
#  STATUS EFFECTS (from COMBAT.json)
# ════════════════════════════════════════════════════════════

STATUS_EFFECTS = {
    "bleeding": {"name": "Кровотечение", "dot": 1, "duration": 3,
                 "text": "кровоточит (-1 HP/раунд)"},
    "stunned": {"name": "Оглушение", "penalty": -3, "duration": 2,
                "text": "оглушён (-3 к действиям)"},
    "poisoned": {"name": "Отравление", "dot": 2, "duration": 4,
                 "text": "отравлен (-2 HP/раунд)"},
    "blinded": {"name": "Слепота", "penalty": -8, "duration": 2,
                "text": "ослеплён (-8 к атакам)"},
    "suppressed": {"name": "Подавлен", "penalty": -4, "duration": 1,
                   "text": "под огнём (-4 к точности)"},
    "burning": {"name": "Горение", "dot": 3, "duration": 2,
                "text": "горит (-3 HP/раунд)"},
}

def apply_status_dot(entity: Dict) -> List[str]:
    """Apply damage-over-time from status effects. Returns log entries."""
    log = []
    expired = []
    for eff in entity.get("status_effects", []):
        eff_data = STATUS_EFFECTS.get(eff["key"], {})
        # Tick damage
        dot = eff_data.get("dot", 0)
        if dot > 0:
            entity["hp"] = max(0, entity["hp"] - dot)
            log.append(f"{entity['name']}: {eff_data['text']} → -{dot} HP")
        # Tick duration
        eff["remaining"] -= 1
        if eff["remaining"] <= 0:
            expired.append(eff)
            log.append(f"{entity['name']}: {eff_data['name']} прошло")
    for e in expired:
        entity["status_effects"].remove(e)
    return log


# ════════════════════════════════════════════════════════════
#  COMBAT ENGINE
# ════════════════════════════════════════════════════════════

class CombatEngine:
    """
    Tactical round-based combat.
    
    Flow:
    1. start_combat() → creates combat state
    2. player_turn(action) → player acts, then each enemy acts
    3. Repeat until all enemies dead OR player HP=0
    4. HP=0 → fail_forward_defeat() → consequences, not death
    """

    def __init__(self):
        self.combat = None

    @property
    def in_combat(self) -> bool:
        return self.combat is not None and self.combat.get("status") == "active"

    def start_combat(self, player: Dict, enemies: List[Dict],
                     companions: List[Dict] = None) -> Dict:
        """Initialize combat. Returns initial state."""
        # Player initiative
        player_init = (player.get("attributes", {}).get("reflexes", 5) +
                       random.randint(1, 6))

        # Companions
        ally_list = []
        if companions:
            for comp in companions:
                ally_list.append({
                    "name": comp.get("name", "Компаньон"),
                    "hp": comp.get("hp", 30),
                    "max_hp": comp.get("max_hp", 30),
                    "attack": comp.get("combat_bonus", 2) + 3,
                    "defense": 2,
                    "damage_formula": "1d6+1",
                    "status_effects": [],
                })

        self.combat = {
            "status": "active",
            "round": 1,
            "player_initiative": player_init,
            "player_hp_start": player.get("current_hp", 50),
            "enemies": enemies,
            "allies": ally_list,
            "log": [],
            "total_damage_dealt": 0,
            "total_damage_taken": 0,
            "enemies_killed": 0,
        }

        # Sort by initiative
        order = []
        order.append({"type": "player", "init": player_init, "name": player.get("name", "Игрок")})
        for e in enemies:
            e_init = e["initiative"] + random.randint(1, 6)
            order.append({"type": "enemy", "init": e_init, "name": e["name"], "id": e["id"]})
        for a in ally_list:
            a_init = random.randint(3, 8)
            order.append({"type": "ally", "init": a_init, "name": a["name"]})
        order.sort(key=lambda x: -x["init"])
        self.combat["turn_order"] = order

        # Log
        enemy_names = ", ".join(f"{e['name']} (HP:{e['hp']})" for e in enemies)
        self.combat["log"].append(f"⚔️ БОЙ НАЧАЛСЯ! Противники: {enemy_names}")
        if ally_list:
            self.combat["log"].append(f"Союзники: {', '.join(a['name'] for a in ally_list)}")
        self.combat["log"].append(f"Инициатива: {' → '.join(o['name'] for o in order)}")

        return self._get_combat_state()

    def player_turn(self, action: str, player: Dict, weapon_damage: str = None) -> Dict:
        """Process player combat action, then enemy turns."""
        if not self.in_combat:
            return {"error": "Нет активного боя"}

        combat = self.combat
        log = combat["log"]
        enemies = combat["enemies"]
        allies = combat["allies"]

        # Determine weapon damage
        if not weapon_damage:
            weapon_damage = self._get_player_weapon_damage(player)

        # === PLAYER TURN ===
        action_lower = action.lower()
        player_result = None

        # Get status penalties
        penalty = sum(STATUS_EFFECTS.get(eff["key"], {}).get("penalty", 0)
                      for eff in player.get("status_effects", []))

        if any(kw in action_lower for kw in ["атаковать", "стрелять", "ударить", "бить", "attack", "shoot"]):
            player_result = self._player_attack(player, enemies, weapon_damage, penalty)
        elif any(kw in action_lower for kw in ["укрытие", "защита", "блок", "cover", "defend"]):
            player_result = self._player_defend(player)
        elif any(kw in action_lower for kw in ["аптечка", "лечить", "heal", "стим"]):
            player_result = self._player_heal(player)
        elif any(kw in action_lower for kw in ["гранат", "grenade", "взрывчат"]):
            player_result = self._player_grenade(player, enemies, penalty)
        elif any(kw in action_lower for kw in ["бежать", "отступить", "flee", "retreat"]):
            player_result = self._player_flee(player)
            if player_result.get("escaped"):
                combat["status"] = "fled"
                log.append("🏃 Вы сбежали из боя!")
                return self._get_combat_state()
        else:
            # Default: attack
            player_result = self._player_attack(player, enemies, weapon_damage, penalty)

        if player_result:
            log.append(player_result["text"])

        # Remove dead enemies
        dead = [e for e in enemies if e["hp"] <= 0]
        for d in dead:
            combat["enemies_killed"] += 1
            log.append(f"💀 {d['name']} повержен!")
        combat["enemies"] = [e for e in enemies if e["hp"] > 0]
        enemies = combat["enemies"]

        # Check victory
        if not enemies:
            combat["status"] = "victory"
            log.append("🏆 ПОБЕДА!")
            return self._get_combat_state()

        # === ALLY TURNS ===
        for ally in allies:
            if ally["hp"] <= 0:
                continue
            # Status DOT
            ally_dot_log = apply_status_dot(ally)
            log.extend(ally_dot_log)
            if ally["hp"] <= 0:
                log.append(f"💔 {ally['name']} выведен из строя!")
                continue
            # Ally attacks random enemy
            target = random.choice(enemies)
            ally_roll = random.randint(1, 20) + ally["attack"]
            if ally_roll >= 10 + target["defense"]:
                dmg = roll_damage(ally["damage_formula"])
                target["hp"] = max(0, target["hp"] - dmg)
                log.append(f"🤝 {ally['name']} → {target['name']}: {dmg} урона")
                if target["hp"] <= 0:
                    combat["enemies_killed"] += 1
                    log.append(f"💀 {target['name']} повержен!")
            else:
                log.append(f"🤝 {ally['name']} → {target['name']}: промах")

        # Re-filter dead
        combat["enemies"] = [e for e in enemies if e["hp"] > 0]
        enemies = combat["enemies"]
        if not enemies:
            combat["status"] = "victory"
            log.append("🏆 ПОБЕДА!")
            return self._get_combat_state()

        # === ENEMY TURNS ===
        for enemy in enemies:
            enemy["turns_alive"] += 1
            # Status DOT
            e_dot_log = apply_status_dot(enemy)
            log.extend(e_dot_log)
            if enemy["hp"] <= 0:
                log.append(f"💀 {enemy['name']} пал от статус-эффекта!")
                combat["enemies_killed"] += 1
                continue

            # Enemy AI based on tactics
            enemy_action = self._enemy_ai(enemy, player, allies)
            log.append(enemy_action["text"])
            if enemy_action.get("damage"):
                combat["total_damage_taken"] += enemy_action["damage"]

        # Re-filter
        combat["enemies"] = [e for e in combat["enemies"] if e["hp"] > 0]

        # === PLAYER STATUS DOT ===
        player_dot = apply_status_dot(player)
        log.extend(player_dot)

        # Check player defeat
        if player.get("current_hp", 1) <= 0:
            combat["status"] = "defeat"
            log.append("⚠️ Вы падаете... Мир темнеет...")
            return self._get_combat_state()

        # Advance round
        combat["round"] += 1
        if combat["round"] > 20:
            combat["status"] = "timeout"
            log.append("⏰ Бой затянулся — противники отступают.")

        return self._get_combat_state()

    # ─── Player Actions ───

    def _player_attack(self, player: Dict, enemies: List[Dict],
                       weapon_dmg: str, penalty: int) -> Dict:
        """Player attacks the first alive enemy."""
        if not enemies:
            return {"text": "Нет целей!", "damage": 0}

        target = enemies[0]  # Attack first enemy (could be targeting later)
        combat_skill = player.get("skills", {}).get("combat", 0)
        dex = player.get("attributes", {}).get("dexterity", 5)
        attack_roll = random.randint(1, 20) + combat_skill + (dex - 5) + penalty

        # Critical hit
        raw_roll = attack_roll - combat_skill - (dex - 5) - penalty
        is_crit = raw_roll >= 19

        ac = 10 + target["defense"]
        if attack_roll >= ac:
            dmg = roll_damage(weapon_dmg)
            if is_crit:
                dmg *= 2
                # Critical hit location
                locations = ["голову", "торс", "конечность"]
                hit_loc = random.choice(locations)
                if hit_loc == "голову":
                    dmg = int(dmg * 1.5)
                    target["status_effects"].append({"key": "stunned", "remaining": 1})
                elif hit_loc == "торс":
                    target["status_effects"].append({"key": "bleeding", "remaining": 3})

            target["hp"] = max(0, target["hp"] - dmg)
            self.combat["total_damage_dealt"] += dmg

            crit_text = f" 💥КРИТ в {hit_loc}!" if is_crit else ""
            return {
                "text": f"🎯 Атака → {target['name']}: {dmg} урона (бросок {attack_roll} vs AC {ac}){crit_text} [HP: {target['hp']}/{target['max_hp']}]",
                "damage": dmg, "hit": True, "critical": is_crit,
            }
        else:
            return {
                "text": f"❌ Промах по {target['name']}! (бросок {attack_roll} vs AC {ac})",
                "damage": 0, "hit": False,
            }

    def _player_defend(self, player: Dict) -> Dict:
        """Player takes cover: +4 defense this round, heals 1 HP."""
        player["_defending"] = True
        heal = min(2, player.get("derived", {}).get("health_points", 50) - player.get("current_hp", 50))
        if heal > 0:
            player["current_hp"] = player.get("current_hp", 50) + heal
        return {"text": f"🛡️ Укрытие! Защита +4 до следующего хода. (+{heal} HP)", "damage": 0}

    def _player_heal(self, player: Dict) -> Dict:
        """Use medkit."""
        heal = random.randint(10, 20)
        max_hp = player.get("derived", {}).get("health_points", 50)
        player["current_hp"] = min(max_hp, player.get("current_hp", 50) + heal)
        return {"text": f"💊 Аптечка! +{heal} HP [HP: {player['current_hp']}/{max_hp}]", "damage": 0}

    def _player_grenade(self, player: Dict, enemies: List[Dict], penalty: int) -> Dict:
        """AoE damage to all enemies."""
        total_dmg = 0
        texts = []
        for e in enemies:
            dmg = roll_damage("2d6")
            e["hp"] = max(0, e["hp"] - dmg)
            total_dmg += dmg
            texts.append(f"{e['name']}: -{dmg}")
        self.combat["total_damage_dealt"] += total_dmg
        return {"text": f"💣 Граната! {', '.join(texts)}", "damage": total_dmg}

    def _player_flee(self, player: Dict) -> Dict:
        """Try to escape. Dex check."""
        dex = player.get("attributes", {}).get("dexterity", 5)
        roll = random.randint(1, 20) + dex
        enemies_init = max(e["initiative"] for e in self.combat["enemies"]) if self.combat["enemies"] else 0
        dc = 10 + enemies_init // 2
        if roll >= dc:
            return {"text": f"🏃 Побег! ({roll} vs DC {dc})", "escaped": True}
        else:
            return {"text": f"🏃 Не удалось сбежать! ({roll} vs DC {dc})", "escaped": False}

    # ─── Enemy AI ───

    def _enemy_ai(self, enemy: Dict, player: Dict, allies: List[Dict]) -> Dict:
        """Enemy chooses action based on tactics."""
        tactics = enemy["tactics"]

        # Flee check
        if tactics == "flee_at_50" and enemy["hp"] < enemy["max_hp"] * 0.5:
            if random.random() < 0.5:
                enemy["hp"] = 0  # removes from combat
                return {"text": f"🏃 {enemy['name']} сбегает!", "damage": 0}

        # Choose target
        target_player = True
        if allies and random.random() < 0.3:
            alive_allies = [a for a in allies if a["hp"] > 0]
            if alive_allies:
                target_player = False
                target_ally = random.choice(alive_allies)

        # Attack
        attack_bonus = enemy["attack"]
        defense_bonus = 0

        if target_player:
            # Calculate player AC
            player_defense = (player.get("attributes", {}).get("dexterity", 5) - 5 +
                              player.get("skills", {}).get("combat", 0) // 2)
            if player.get("_defending"):
                player_defense += 4
                player["_defending"] = False
            ac = 10 + player_defense
        else:
            ac = 10 + target_ally.get("defense", 2)

        roll = random.randint(1, 20) + attack_bonus
        raw_roll = roll - attack_bonus
        is_crit = raw_roll >= 19

        if roll >= ac:
            dmg = roll_damage(enemy["damage_formula"])
            if is_crit:
                dmg *= 2
            if tactics == "alpha_strike" and enemy["turns_alive"] == 0:
                dmg = int(dmg * 1.5)  # First hit bonus

            if target_player:
                player["current_hp"] = max(0, player.get("current_hp", 50) - dmg)
                return {
                    "text": f"🔴 {enemy['name']} → Вы: {dmg} урона {'💥КРИТ!' if is_crit else ''}(бросок {roll} vs AC {ac}) [HP: {player['current_hp']}]",
                    "damage": dmg,
                }
            else:
                target_ally["hp"] = max(0, target_ally["hp"] - dmg)
                return {
                    "text": f"🔴 {enemy['name']} → {target_ally['name']}: {dmg} урона [HP: {target_ally['hp']}]",
                    "damage": 0,
                }
        else:
            target_name = "Вас" if target_player else target_ally["name"]
            return {
                "text": f"🟡 {enemy['name']} промахивается по {target_name} ({roll} vs AC {ac})",
                "damage": 0,
            }

    def _get_player_weapon_damage(self, player: Dict) -> str:
        """Determine player weapon damage from inventory or default."""
        # This is a simplified version - in full game, would check equipped weapon
        return "1d6+1"  # Default: basic pistol

    def _get_combat_state(self) -> Dict:
        """Return combat state for client/AI."""
        c = self.combat
        return {
            "in_combat": c["status"] == "active",
            "status": c["status"],
            "round": c["round"],
            "enemies": [{
                "name": e["name"], "hp": e["hp"], "max_hp": e["max_hp"],
                "status": [STATUS_EFFECTS.get(s["key"], {}).get("name", "") for s in e.get("status_effects", [])]
            } for e in c["enemies"]],
            "allies": [{
                "name": a["name"], "hp": a["hp"], "max_hp": a["max_hp"],
            } for a in c.get("allies", []) if a["hp"] > 0],
            "log": c["log"][-8:],  # last 8 entries for display
            "total_damage_dealt": c["total_damage_dealt"],
            "enemies_killed": c["enemies_killed"],
        }

    def get_combat_rewards(self) -> Dict:
        """Calculate rewards after victory."""
        if not self.combat:
            return {}
        c = self.combat
        total_xp = 0
        total_credits = 0
        for e_template in [ENEMY_TEMPLATES.get(e.get("template", "thug"), ENEMY_TEMPLATES["thug"])
                           for e in (c.get("_original_enemies", []) or [])]:
            # Fallback: use killed count
            pass

        # Simple: XP based on enemies killed and damage
        total_xp = c["enemies_killed"] * 25 + c["total_damage_dealt"] // 5
        total_credits = c["enemies_killed"] * random.randint(100, 500)
        bonus_xp = 10 if c["total_damage_taken"] == 0 else 0  # flawless bonus

        return {
            "xp": total_xp + bonus_xp,
            "credits": total_credits,
            "enemies_killed": c["enemies_killed"],
            "flawless": c["total_damage_taken"] == 0,
        }

    def get_prompt_context(self) -> str:
        """Generate combat context for AI prompt."""
        if not self.in_combat:
            return ""
        c = self.combat
        lines = [f"## ⚔️ АКТИВНЫЙ БОЙ (раунд {c['round']}):"]
        for e in c["enemies"]:
            status_text = ", ".join(STATUS_EFFECTS.get(s["key"], {}).get("name", "") for s in e.get("status_effects", []))
            lines.append(f"  🔴 {e['name']}: HP {e['hp']}/{e['max_hp']}{' ['+status_text+']' if status_text else ''}")
        for a in c.get("allies", []):
            if a["hp"] > 0:
                lines.append(f"  🟢 {a['name']}: HP {a['hp']}/{a['max_hp']}")
        lines.append(f"  Раунд: {c['round']}, убито: {c['enemies_killed']}")
        lines.append("  Игрок может: атаковать, укрытие, аптечка, граната, бежать")
        return "\n".join(lines)

    def end_combat(self):
        """Clean up after combat."""
        result = None
        if self.combat:
            result = {
                "status": self.combat["status"],
                "rounds": self.combat["round"],
                "enemies_killed": self.combat["enemies_killed"],
                "damage_dealt": self.combat["total_damage_dealt"],
                "damage_taken": self.combat["total_damage_taken"],
                "log": self.combat["log"],
            }
        self.combat = None
        return result


# ════════════════════════════════════════════════════════════
#  FAIL-FORWARD DEFEAT SYSTEM
# ════════════════════════════════════════════════════════════

DEFEAT_CONSEQUENCES = [
    {
        "id": "captured",
        "name": "Захват",
        "description": "Очнулся в плену. Руки связаны, снаряжение отобрано.",
        "hp_restore": 0.3,       # restore to 30% max HP
        "credits_loss": 0.5,     # lose 50% credits
        "items_lost": 2,         # lose 2 random items
        "time_skip_hours": 8,    # 8 hours pass
        "stress_gain": 10,
        "reputation_hit": {"all": -2},
        "narrative_hook": "escape_captivity",
    },
    {
        "id": "left_for_dead",
        "name": "Оставлен умирать",
        "description": "Приходишь в себя в луже собственной крови. Грабители забрали что могли.",
        "hp_restore": 0.2,
        "credits_loss": 0.7,
        "items_lost": 3,
        "time_skip_hours": 12,
        "stress_gain": 15,
        "scar": True,
        "narrative_hook": "recovery",
    },
    {
        "id": "rescued",
        "name": "Спасён случайным NPC",
        "description": "Кто-то нашёл тебя без сознания и помог. Теперь ты должен.",
        "hp_restore": 0.5,
        "credits_loss": 0.2,
        "items_lost": 1,
        "time_skip_hours": 6,
        "stress_gain": 5,
        "debt": True,
        "narrative_hook": "owe_debt",
    },
    {
        "id": "medical_evac",
        "name": "Экстренная эвакуация",
        "description": "Компаньон / прохожий вытащил тебя. Счёт за лечение — космический.",
        "hp_restore": 0.6,
        "credits_loss": 0.3,
        "items_lost": 0,
        "time_skip_hours": 24,
        "stress_gain": 8,
        "medical_bill": True,
        "narrative_hook": "hospital_recovery",
    },
    {
        "id": "cybernetic_damage",
        "name": "Повреждение имплантов",
        "description": "Импланты повреждены ударом. Нужен ремонт. Некоторые функции отключены.",
        "hp_restore": 0.4,
        "credits_loss": 0.1,
        "items_lost": 0,
        "time_skip_hours": 4,
        "stress_gain": 12,
        "skill_penalty": {"hacking": -1, "combat": -1},
        "narrative_hook": "repair_implants",
    },
    {
        "id": "blackout_aftermath",
        "name": "Провал в памяти",
        "description": "Очнулся в незнакомом месте. Что произошло? Кто-то видел тебя делающим... что-то.",
        "hp_restore": 0.4,
        "credits_loss": 0.2,
        "items_lost": 1,
        "time_skip_hours": 16,
        "stress_gain": 20,
        "location_change": True,
        "narrative_hook": "mystery_blackout",
    },
]

SCARS = [
    "глубокий шрам через левую щёку",
    "обожженная кожа на предплечье",
    "хромота после травмы колена",
    "контузия — периодический звон в ушах",
    "сломанный нос — криво сросся",
    "ожог от лазера на плече",
    "повреждённый глаз — нужен кибер-протез",
    "шрам на шее — на дюйм от смерти",
]


def apply_defeat(character: Dict, inventory: List[Dict],
                 game_time: Dict, current_location: Dict) -> Dict:
    """
    Apply fail-forward defeat consequences. NO PERMADEATH.
    Returns dict describing what happened.
    """
    consequence = random.choice(DEFEAT_CONSEQUENCES)
    result = {
        "consequence": consequence["id"],
        "name": consequence["name"],
        "description": consequence["description"],
        "narrative_hook": consequence["narrative_hook"],
        "changes": [],
    }

    # Restore some HP (not to 0!)
    max_hp = character.get("derived", {}).get("health_points", 50)
    restored_hp = max(5, int(max_hp * consequence["hp_restore"]))
    character["current_hp"] = restored_hp
    result["changes"].append(f"HP восстановлено до {restored_hp}/{max_hp}")

    # Lose credits
    credits = character.get("credits", 0)
    lost_credits = int(credits * consequence["credits_loss"])
    character["credits"] = max(0, credits - lost_credits)
    if lost_credits > 0:
        result["changes"].append(f"Потеряно ₡{lost_credits}")
        result["credits_lost"] = lost_credits

    # Lose items
    items_to_lose = min(consequence["items_lost"], len(inventory))
    lost_items = []
    for _ in range(items_to_lose):
        if inventory:
            item = random.choice(inventory)
            lost_items.append(item.get("name", "?"))
            inventory.remove(item)
    if lost_items:
        result["changes"].append(f"Потеряно: {', '.join(lost_items)}")
        result["items_lost"] = lost_items

    # Time skip
    hours = consequence["time_skip_hours"]
    game_time["hour"] = (game_time.get("hour", 0) + hours) % 24
    game_time["day"] = game_time.get("day", 1) + hours // 24
    result["changes"].append(f"Прошло {hours} часов")
    result["time_skip_hours"] = hours

    # Stress
    stress_gain = consequence["stress_gain"]
    character["stress"] = min(100, character.get("stress", 0) + stress_gain)
    result["changes"].append(f"Стресс +{stress_gain}")

    # Scar
    if consequence.get("scar"):
        scar = random.choice(SCARS)
        if "scars" not in character:
            character["scars"] = []
        character["scars"].append(scar)
        result["changes"].append(f"Новый шрам: {scar}")
        result["scar"] = scar

    # Skill penalty
    if consequence.get("skill_penalty"):
        for skill, penalty in consequence["skill_penalty"].items():
            if skill in character.get("skills", {}):
                character["skills"][skill] = max(0, character["skills"][skill] + penalty)
                result["changes"].append(f"{skill} {penalty}")

    # Location change (blackout)
    if consequence.get("location_change"):
        # Random nearby district
        result["force_location_change"] = True

    # Reputation hit
    if consequence.get("reputation_hit"):
        result["reputation_hit"] = consequence["reputation_hit"]

    # Debt
    if consequence.get("debt"):
        result["changes"].append("Теперь вы кому-то должны...")
        result["debt"] = True

    # Medical bill
    if consequence.get("medical_bill"):
        bill = random.randint(500, 2000)
        character["credits"] = max(0, character.get("credits", 0) - bill)
        result["changes"].append(f"Счёт за лечение: ₡{bill}")

    # XP penalty — lose 20% of current level's XP
    xp_loss = character.get("xp", 0) // 5
    character["xp"] = max(0, character.get("xp", 0) - xp_loss)
    if xp_loss > 0:
        result["changes"].append(f"XP -{xp_loss}")

    return result


# ════════════════════════════════════════════════════════════
#  LEVEL UP INTEGRATION
# ════════════════════════════════════════════════════════════

def process_xp_gain(character: Dict, xp_amount: int) -> Optional[Dict]:
    """
    Add XP and check for level up. Uses proper LevelUpSystem.
    Returns level_up info if leveled, else None.
    """
    if xp_amount <= 0:
        return None

    character["xp"] = character.get("xp", 0) + xp_amount
    xp_per_level = 100  # base
    current_level = character.get("level", 1)

    # XP needed for next level scales
    xp_needed = xp_per_level + (current_level - 1) * 50  # 100, 150, 200, 250...

    if character["xp"] >= xp_needed:
        character["xp"] -= xp_needed
        character["level"] = current_level + 1

        # Grant skill points
        skill_points = 3
        character["unspent_skill_points"] = character.get("unspent_skill_points", 0) + skill_points

        # Perk every 2 levels
        perk_available = (character["level"] % 2 == 0)

        # HP increase
        endurance = character.get("attributes", {}).get("endurance", 5)
        hp_gain = 5 + endurance // 2
        character["derived"]["health_points"] = character["derived"].get("health_points", 50) + hp_gain
        character["current_hp"] = min(
            character["current_hp"] + hp_gain,
            character["derived"]["health_points"]
        )

        return {
            "new_level": character["level"],
            "skill_points": skill_points,
            "unspent": character["unspent_skill_points"],
            "perk_available": perk_available,
            "hp_gain": hp_gain,
            "xp_for_next": xp_per_level + (character["level"] - 1) * 50,
        }

    return None


# ════════════════════════════════════════════════════════════
#  SUBSYSTEM TRIGGER DETECTION
# ════════════════════════════════════════════════════════════

HACK_KEYWORDS = ["взломать", "хакнуть", "хакаю", "взлом", "hack", "crack", "decrypt",
                 "подключиться к терминалу", "обойти защиту", "взломать систему"]

INVESTIGATE_KEYWORDS = ["расследовать", "расследую", "осмотреть улики", "искать улики",
                        "исследовать тело", "проверить камеры", "допросить свидетел",
                        "изучить место преступления", "investigate"]

CRAFT_KEYWORDS = ["собрать", "скрафтить", "крафт", "craft", "сделать из", "создать",
                  "модифицировать", "улучшить оружие", "собрать устройство"]

COMBAT_KEYWORDS = ["атаковать", "напасть", "ударить", "стрелять", "драться",
                   "бой", "нападаю", "attack", "fight"]


def detect_subsystem_trigger(action: str) -> Optional[Dict]:
    """
    Detect if player action should trigger a subsystem mini-game.
    Returns: {"system": "hacking"|"investigation"|"crafting"|"combat", ...}
    """
    action_lower = action.lower().strip()

    for kw in HACK_KEYWORDS:
        if kw in action_lower:
            # Determine target type from context
            target = "terminal"  # default
            if any(w in action_lower for w in ["сервер", "server", "корпорат"]):
                target = "corporate_server"
            elif any(w in action_lower for w in ["безопасность", "security", "камер"]):
                target = "security"
            elif any(w in action_lower for w in ["база данных", "database", "данные"]):
                target = "database"
            elif any(w in action_lower for w in ["военн", "military"]):
                target = "military_net"
            elif any(w in action_lower for w in ["ИИ", "AI", "ядро"]):
                target = "ai_core"
            return {"system": "hacking", "target_type": target}

    for kw in INVESTIGATE_KEYWORDS:
        if kw in action_lower:
            case_type = None
            if any(w in action_lower for w in ["убийств", "труп", "тело"]):
                case_type = "murder"
            elif any(w in action_lower for w in ["краж", "украден"]):
                case_type = "theft"
            elif any(w in action_lower for w in ["исчез", "пропал"]):
                case_type = "disappearance"
            elif any(w in action_lower for w in ["заговор", "conspir"]):
                case_type = "conspiracy"
            elif any(w in action_lower for w in ["саботаж"]):
                case_type = "sabotage"
            return {"system": "investigation", "case_type": case_type}

    for kw in CRAFT_KEYWORDS:
        if kw in action_lower:
            idx = action_lower.find(kw) + len(kw)
            target = action[idx:].strip().strip('«»"\'.,!?')
            return {"system": "crafting", "target": target}

    # Combat only if explicitly aggressive AND not already in combat
    for kw in COMBAT_KEYWORDS:
        if kw in action_lower:
            return {"system": "combat"}

    return None
