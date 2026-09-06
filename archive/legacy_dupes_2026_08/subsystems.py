"""
Subsystems — deep gameplay modules.
- HackingSystem: node-based hacking mini-game
- InvestigationSystem: clue collection, deduction
- CompanionSystem: recruitment, loyalty, commands
- ShipSystem: ownership, upgrades, cargo, space combat
- PropertySystem: buy/rent locations, income, storage, defense
"""
import random
import uuid
from typing import Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════
#  HACKING SYSTEM — node-based ICE cracking
# ════════════════════════════════════════════════════════════

ICE_TYPES = [
    {"type": "firewall", "name": "Фаервол", "difficulty": 8, "effect": "Блокирует доступ", "bypass_skill": "hacking"},
    {"type": "tracer", "name": "Трейсер", "difficulty": 10, "effect": "Обратная трассировка — обнаружение через 3 хода", "bypass_skill": "stealth"},
    {"type": "black_ice", "name": "Чёрный лёд", "difficulty": 14, "effect": "Нейроурон: 2d6 урона рассудку", "bypass_skill": "hacking"},
    {"type": "honeypot", "name": "Ловушка-приманка", "difficulty": 12, "effect": "Ложные данные, трата хода", "bypass_skill": "investigation"},
    {"type": "daemon", "name": "Демон-страж", "difficulty": 16, "effect": "Контратака: 3d6 урона, тревога", "bypass_skill": "combat"},
    {"type": "encryption", "name": "Шифрование", "difficulty": 10, "effect": "Данные нечитаемы без ключа", "bypass_skill": "technology"},
    {"type": "neural_lock", "name": "Нейро-замок", "difficulty": 18, "effect": "Требует биометрию, иначе откат", "bypass_skill": "medicine"},
]

HACK_TARGETS = [
    {"type": "terminal", "name": "Терминал", "nodes": 2, "ice_count": 1, "data_value": "low"},
    {"type": "security", "name": "Система безопасности", "nodes": 3, "ice_count": 2, "data_value": "medium"},
    {"type": "database", "name": "База данных", "nodes": 4, "ice_count": 3, "data_value": "high"},
    {"type": "corporate_server", "name": "Корпоративный сервер", "nodes": 5, "ice_count": 4, "data_value": "very_high"},
    {"type": "military_net", "name": "Военная сеть", "nodes": 6, "ice_count": 5, "data_value": "critical"},
    {"type": "ai_core", "name": "Ядро ИИ", "nodes": 8, "ice_count": 6, "data_value": "legendary"},
]

HACK_LOOT_TABLES = {
    "low": [
        "Логи доступа — кто заходил и когда",
        "Личная переписка — компромат на мелкого чиновника",
        "Код доступа к складу",
        "Электронный кошелёк: 200-500₡",
    ],
    "medium": [
        "Финансовые записи — доказательства махинаций",
        "Схема охранной системы здания",
        "Данные о перемещениях цели",
        "Доступ к камерам наблюдения",
        "Электронный кошелёк: 500-2000₡",
    ],
    "high": [
        "Корпоративные секреты — можно продать за 5000-10000₡",
        "Чертёж прототипа (рецепт крафта)",
        "Компромат на высокопоставленного NPC",
        "Список агентов — фракция будет благодарна",
        "Доступ к банковским счетам: 2000-5000₡",
    ],
    "very_high": [
        "Секретные проекты корпорации — стоимость огромна",
        "Бэкдор в систему — постоянный доступ",
        "Координаты тайного объекта",
        "ИИ-модуль — можно установить на корабль",
        "Доступ к счетам: 5000-15000₡",
    ],
    "critical": [
        "Военные коды — доступ к арсеналу",
        "План вторжения фракции",
        "Данные о секретном оружии",
        "Полный контроль над станцией на 1 час",
        "Доступ к счетам: 10000-50000₡",
    ],
    "legendary": [
        "Код самосознания ИИ — бесценно",
        "Координаты утерянной колонии",
        "Секрет «Сигнала» — Церковь заплатит любую цену",
        "Корневой доступ к инфраструктуре системы",
        "Бэкдор во ВСЕ системы фракции",
    ],
}


class HackingSystem:
    """Node-based hacking mini-game."""

    def __init__(self):
        self.active_hack = None
        self.hack_history = []

    def start_hack(self, target_type: str, player_hacking: int, player_stealth: int) -> Dict:
        target = next((t for t in HACK_TARGETS if t["type"] == target_type), HACK_TARGETS[0])
        nodes = []
        for i in range(target["nodes"]):
            node = {"id": i, "type": "data" if i == target["nodes"] - 1 else "junction",
                    "accessed": False, "ice": None}
            if i < target["ice_count"]:
                ice = random.choice(ICE_TYPES)
                node["ice"] = dict(ice)
                node["ice"]["active"] = True
            nodes.append(node)

        self.active_hack = {
            "id": str(uuid.uuid4())[:8],
            "target": target,
            "nodes": nodes,
            "current_node": 0,
            "alert_level": 0,
            "max_alert": 5,
            "turns_left": target["nodes"] + 3,
            "player_hacking": player_hacking,
            "player_stealth": player_stealth,
            "loot": [],
            "status": "active",
        }
        return self.active_hack

    def hack_action(self, action: str) -> Dict:
        if not self.active_hack or self.active_hack["status"] != "active":
            return {"error": "Нет активного взлома"}

        hack = self.active_hack
        node = hack["nodes"][hack["current_node"]]
        result = {"action": action, "success": False, "narrative": "", "alert_change": 0}

        if action == "crack_ice" and node.get("ice") and node["ice"]["active"]:
            ice = node["ice"]
            roll = random.randint(1, 6) + random.randint(1, 6) + hack["player_hacking"]
            success = roll >= ice["difficulty"]
            result["roll"] = roll
            result["dc"] = ice["difficulty"]

            if success:
                ice["active"] = False
                result["success"] = True
                result["narrative"] = f"ICE «{ice['name']}» нейтрализован! Бросок: {roll} vs DC {ice['difficulty']}"
            else:
                hack["alert_level"] += 1
                result["alert_change"] = 1
                result["narrative"] = f"Не удалось взломать «{ice['name']}»! Бросок: {roll} vs DC {ice['difficulty']}. Тревога +1!"
                if ice["type"] == "black_ice":
                    damage = random.randint(2, 12)
                    result["sanity_damage"] = damage
                    result["narrative"] += f" Чёрный лёд наносит {damage} урона рассудку!"

        elif action == "advance":
            if node.get("ice") and node["ice"]["active"]:
                result["narrative"] = "Невозможно продвинуться — ICE блокирует путь!"
            elif hack["current_node"] < len(hack["nodes"]) - 1:
                hack["current_node"] += 1
                new_node = hack["nodes"][hack["current_node"]]
                result["success"] = True
                ice_text = f" Обнаружен ICE: {new_node['ice']['name']}!" if new_node.get("ice") and new_node["ice"]["active"] else ""
                result["narrative"] = f"Продвижение к узлу {hack['current_node']}.{ice_text}"
            else:
                result["narrative"] = "Ты уже на последнем узле!"

        elif action == "stealth_bypass":
            if node.get("ice") and node["ice"]["active"]:
                roll = random.randint(1, 6) + random.randint(1, 6) + hack["player_stealth"]
                dc = node["ice"]["difficulty"] + 2
                if roll >= dc:
                    node["ice"]["active"] = False
                    result["success"] = True
                    result["narrative"] = f"Тихий обход ICE «{node['ice']['name']}»! ({roll} vs DC {dc})"
                else:
                    hack["alert_level"] += 2
                    result["alert_change"] = 2
                    result["narrative"] = f"Обход провален! Тревога +2! ({roll} vs DC {dc})"
            else:
                result["narrative"] = "Нечего обходить."

        elif action == "extract_data":
            if hack["current_node"] == len(hack["nodes"]) - 1 and not (node.get("ice") and node["ice"]["active"]):
                loot_table = HACK_LOOT_TABLES.get(hack["target"]["data_value"], HACK_LOOT_TABLES["low"])
                loot = random.choice(loot_table)
                hack["loot"].append(loot)
                hack["status"] = "success"
                result["success"] = True
                result["narrative"] = f"ДАННЫЕ ИЗВЛЕЧЕНЫ: {loot}"
                result["loot"] = loot
                self.hack_history.append(hack)
            else:
                result["narrative"] = "Сначала доберись до последнего узла и нейтрализуй ICE!"

        elif action == "disconnect":
            hack["status"] = "aborted"
            result["narrative"] = "Отключение. Взлом прерван."
            result["success"] = True

        # Tick timer
        hack["turns_left"] -= 1
        if hack["turns_left"] <= 0:
            hack["status"] = "timeout"
            result["narrative"] += " ⚠️ ВРЕМЯ ИСТЕКЛО! Системы перезагрузились."
        if hack["alert_level"] >= hack["max_alert"]:
            hack["status"] = "detected"
            result["narrative"] += " 🚨 ОБНАРУЖЕН! Охрана оповещена!"

        result["hack_state"] = {
            "current_node": hack["current_node"],
            "total_nodes": len(hack["nodes"]),
            "alert": hack["alert_level"],
            "max_alert": hack["max_alert"],
            "turns_left": hack["turns_left"],
            "status": hack["status"],
        }
        return result

    def get_prompt_context(self) -> str:
        if not self.active_hack or self.active_hack["status"] != "active":
            return ""
        h = self.active_hack
        return (f"[ХАКИНГ] Цель: {h['target']['name']}, узел {h['current_node']}/{len(h['nodes'])-1}, "
                f"тревога {h['alert_level']}/{h['max_alert']}, ходов осталось: {h['turns_left']}")

    def to_dict(self) -> Dict:
        return {"active_hack": self.active_hack, "hack_history": self.hack_history[-20:]}

    @classmethod
    def from_dict(cls, data: Dict) -> 'HackingSystem':
        h = cls()
        h.active_hack = data.get("active_hack")
        h.hack_history = data.get("hack_history", [])
        return h


# ════════════════════════════════════════════════════════════
#  INVESTIGATION SYSTEM — clues, deduction, case files
# ════════════════════════════════════════════════════════════

CLUE_TYPES = [
    "physical", "digital", "testimony", "forensic", "circumstantial",
    "documentary", "surveillance", "financial", "biological", "psychological",
]

INVESTIGATION_TEMPLATES = [
    {"type": "murder", "name": "Убийство", "clues_needed": 5, "suspects_min": 3,
     "clue_sources": ["место преступления", "камеры", "свидетели", "медэксперт", "цифровые следы"]},
    {"type": "theft", "name": "Кража", "clues_needed": 4, "suspects_min": 2,
     "clue_sources": ["место кражи", "охрана", "камеры", "информаторы"]},
    {"type": "disappearance", "name": "Исчезновение", "clues_needed": 5, "suspects_min": 2,
     "clue_sources": ["последнее место", "родственники", "камеры", "цифровые следы", "финансы"]},
    {"type": "conspiracy", "name": "Заговор", "clues_needed": 7, "suspects_min": 4,
     "clue_sources": ["информатор", "документы", "слежка", "финансы", "перехват связи", "инсайдер", "физулики"]},
    {"type": "sabotage", "name": "Саботаж", "clues_needed": 4, "suspects_min": 2,
     "clue_sources": ["место инцидента", "записи доступа", "техосмотр", "мотивы"]},
    {"type": "corruption", "name": "Коррупция", "clues_needed": 6, "suspects_min": 3,
     "clue_sources": ["финансы", "информатор", "документы", "слежка", "цифровые следы", "свидетели"]},
    {"type": "smuggling", "name": "Контрабандная сеть", "clues_needed": 5, "suspects_min": 3,
     "clue_sources": ["таможня", "информатор", "слежка", "груз", "финансы"]},
    {"type": "espionage", "name": "Шпионаж", "clues_needed": 6, "suspects_min": 3,
     "clue_sources": ["контрразведка", "цифровые следы", "слежка", "перехват связи", "допросы", "документы"]},
]


class InvestigationSystem:
    """Track investigation cases with clues and deduction."""

    def __init__(self):
        self.active_cases = []
        self.closed_cases = []

    def open_case(self, case_type: str = None, custom_name: str = None) -> Dict:
        template = next((t for t in INVESTIGATION_TEMPLATES if t["type"] == case_type), None)
        if not template:
            template = random.choice(INVESTIGATION_TEMPLATES)

        case = {
            "id": str(uuid.uuid4())[:8],
            "type": template["type"],
            "name": custom_name or f"{template['name']} — дело #{random.randint(100,999)}",
            "clues_needed": template["clues_needed"],
            "clues_found": [],
            "suspects": [],
            "leads": list(template["clue_sources"]),
            "conclusion": None,
            "status": "open",
            "created_turn": 0,
        }
        self.active_cases.append(case)
        return case

    def add_clue(self, case_id: str, clue_text: str, source: str, reliability: str = "medium") -> Dict:
        case = next((c for c in self.active_cases if c["id"] == case_id), None)
        if not case:
            return {"error": "Дело не найдено"}

        clue = {
            "id": str(uuid.uuid4())[:6],
            "text": clue_text,
            "source": source,
            "type": random.choice(CLUE_TYPES),
            "reliability": reliability,
            "connected_to": [],
        }
        case["clues_found"].append(clue)

        progress = len(case["clues_found"]) / case["clues_needed"]
        return {
            "clue": clue,
            "progress": f"{len(case['clues_found'])}/{case['clues_needed']}",
            "can_conclude": progress >= 1.0,
        }

    def add_suspect(self, case_id: str, suspect_name: str, motive: str = "", evidence: str = "") -> Dict:
        case = next((c for c in self.active_cases if c["id"] == case_id), None)
        if not case:
            return {"error": "Дело не найдено"}

        suspect = {"name": suspect_name, "motive": motive, "evidence": evidence, "cleared": False}
        case["suspects"].append(suspect)
        return {"suspect_added": suspect, "total_suspects": len(case["suspects"])}

    def conclude_case(self, case_id: str, conclusion: str, suspect_name: str = None) -> Dict:
        case = next((c for c in self.active_cases if c["id"] == case_id), None)
        if not case:
            return {"error": "Дело не найдено"}

        clue_ratio = len(case["clues_found"]) / case["clues_needed"]
        # More clues = higher accuracy
        accuracy = min(clue_ratio, 1.0)
        correct = random.random() < accuracy

        case["conclusion"] = conclusion
        case["suspect_accused"] = suspect_name
        case["correct"] = correct
        case["status"] = "closed"
        self.active_cases.remove(case)
        self.closed_cases.append(case)

        return {
            "case_closed": True,
            "accuracy": f"{accuracy*100:.0f}%",
            "clues_used": len(case["clues_found"]),
            "conclusion": conclusion,
        }

    def get_prompt_context(self) -> str:
        if not self.active_cases:
            return ""
        lines = ["[РАССЛЕДОВАНИЯ]"]
        for c in self.active_cases:
            lines.append(f"  Дело: {c['name']}, улик: {len(c['clues_found'])}/{c['clues_needed']}, "
                        f"подозреваемых: {len(c['suspects'])}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {"active_cases": self.active_cases, "closed_cases": self.closed_cases[-20:]}

    @classmethod
    def from_dict(cls, data: Dict) -> 'InvestigationSystem':
        inv = cls()
        inv.active_cases = data.get("active_cases", [])
        inv.closed_cases = data.get("closed_cases", [])
        return inv


# ════════════════════════════════════════════════════════════
#  COMPANION SYSTEM — recruitment, loyalty, commands
# ════════════════════════════════════════════════════════════

COMPANION_TEMPLATES = [
    {"type": "mercenary", "name_pool": ["Рекс", "Вайпер", "Мавка", "Булат", "Шторм"],
     "skills": {"combat": 4, "survival": 3}, "personality": "Грубый, но надёжный", "cost": 5000,
     "loyalty_base": 40, "combat_bonus": 2, "utility": "Бой и охрана"},
    {"type": "hacker", "name_pool": ["Н3он", "Глитч", "Зеро", "Спарк", "Пиксель"],
     "skills": {"hacking": 5, "technology": 3}, "personality": "Нервный гик", "cost": 4000,
     "loyalty_base": 50, "combat_bonus": 0, "utility": "Взлом и техподдержка"},
    {"type": "medic", "name_pool": ["Док", "Анджело", "Хил", "Мерси", "Пластырь"],
     "skills": {"medicine": 5, "science": 2}, "personality": "Спокойный и заботливый", "cost": 4500,
     "loyalty_base": 60, "combat_bonus": 0, "utility": "Лечение и диагностика"},
    {"type": "pilot", "name_pool": ["Ас", "Комета", "Дрифт", "Маверик", "Стелла"],
     "skills": {"piloting": 5, "engineering": 2}, "personality": "Безбашенный", "cost": 5000,
     "loyalty_base": 45, "combat_bonus": 1, "utility": "Пилотирование и механика"},
    {"type": "fixer", "name_pool": ["Крот", "Связной", "Шёпот", "Тень", "Мозг"],
     "skills": {"streetwise": 4, "negotiation": 3, "deception": 3}, "personality": "Хитрый и скользкий", "cost": 6000,
     "loyalty_base": 35, "combat_bonus": 0, "utility": "Контакты, торговля, информация"},
    {"type": "enforcer", "name_pool": ["Танк", "Кувалда", "Скала", "Бизон", "Стена"],
     "skills": {"combat": 3, "intimidation": 4, "endurance": 4}, "personality": "Молчаливый громила", "cost": 4000,
     "loyalty_base": 50, "combat_bonus": 3, "utility": "Ближний бой и запугивание"},
    {"type": "scout", "name_pool": ["Ястреб", "Лис", "Призрак", "Следопыт", "Рысь"],
     "skills": {"stealth": 4, "perception": 4, "survival": 3}, "personality": "Тихий и наблюдательный", "cost": 4500,
     "loyalty_base": 45, "combat_bonus": 1, "utility": "Разведка, скрытность, выживание"},
    {"type": "engineer", "name_pool": ["Ключ", "Тесла", "Болт", "Гайка", "Сварка"],
     "skills": {"engineering": 5, "technology": 3}, "personality": "Помешан на механизмах", "cost": 5000,
     "loyalty_base": 55, "combat_bonus": 0, "utility": "Ремонт, крафт, сапёрное дело"},
]

LOYALTY_EVENTS = {
    "positive": [
        {"trigger": "saved_life", "change": 15, "text": "{name} благодарен за спасение жизни."},
        {"trigger": "shared_loot", "change": 8, "text": "{name} доволен честным дележом."},
        {"trigger": "helped_personal", "change": 12, "text": "{name} ценит помощь с личной проблемой."},
        {"trigger": "won_battle", "change": 5, "text": "{name} вдохновлён победой."},
        {"trigger": "respect_decision", "change": 6, "text": "{name} уважает твоё решение."},
    ],
    "negative": [
        {"trigger": "left_behind", "change": -20, "text": "{name} зол, что его бросили."},
        {"trigger": "unfair_loot", "change": -10, "text": "{name} считает дележ несправедливым."},
        {"trigger": "moral_conflict", "change": -8, "text": "{name} не согласен с твоим выбором."},
        {"trigger": "friendly_fire", "change": -12, "text": "{name} ранен по твоей вине."},
        {"trigger": "broke_promise", "change": -15, "text": "{name} разочарован нарушенным обещанием."},
    ],
}


class CompanionSystem:
    """Manage companion recruitment, loyalty, and commands."""

    MAX_COMPANIONS = 3

    def __init__(self):
        self.companions = []
        self.dismissed = []

    def get_available_recruits(self, location = None) -> List[Dict]:
        """Get companions available at current location."""
        from companions import COMPANIONS

        recruited_ids = {c.get("template_id") for c in self.companions}
        dismissed_ids = {c.get("template_id") for c in self.dismissed}

        # Match location to companion locations
        loc_planet = ""
        loc_city = ""
        loc_district = ""
        if isinstance(location, dict):
            loc_planet = location.get("planet", "").lower()
            loc_city = location.get("city", "").lower()
            loc_district = location.get("district", "").lower()
        elif isinstance(location, str):
            loc_planet = location.lower()

        recruits = []
        for comp in COMPANIONS:
            # Skip already recruited or dismissed
            if comp["id"] in recruited_ids or comp["id"] in dismissed_ids:
                continue

            # Location matching — check if companion's location matches player's area
            comp_loc = comp.get("location", "").lower()
            if not comp_loc:
                continue

            # Match by planet/city keywords
            match = False
            if loc_planet and any(w in comp_loc for w in loc_planet.split()):
                match = True
            if loc_city:
                for word in loc_city.replace("-", " ").split():
                    if len(word) > 2 and word in comp_loc:
                        match = True
            # Special mappings: Церера ↔ Пояс, Тихе ↔ Пояс
            if "церера" in loc_city or "пояс" in loc_planet:
                if "церера" in comp_loc or "пояс" in comp_loc or "тихе" in comp_loc:
                    match = True
            if "марс" in loc_planet:
                if "марс" in comp_loc or "олимпус" in comp_loc:
                    match = True
            if "земля" in loc_planet:
                if "нью-токио" in comp_loc or "земл" in comp_loc or "токио" in comp_loc:
                    match = True

            if not match:
                continue

            # Build recruit data
            recruit = {
                "id": comp["id"],
                "template_id": comp["id"],
                "name": comp["name"],
                "nickname": comp.get("nickname", ""),
                "type": comp["type"],
                "description": comp["description"],
                "personality": comp.get("personality", ""),
                "appearance": comp.get("appearance", ""),
                "skills": comp.get("skill_bonus", {}),
                "combat_bonus": comp.get("combat_bonus", {}),
                "cost": comp.get("recruit_condition", {}).get("cost",
                        3000 + random.randint(0, 5000)),
                "loyalty": 50,
                "max_loyalty": 100,
                "hp": 40 + random.randint(0, 20),
                "max_hp": 60,
                "status": "available",
                "personal_quest": comp.get("personal_quest"),
                "location": comp.get("location", ""),
                "dialogue": comp.get("dialogue_samples", {}),
                "recruit_condition": comp.get("recruit_condition", {}),
                "faction": comp.get("faction"),
            }

            # Assign cost based on type
            if comp["type"] == "combat":
                recruit["cost"] = 5000 + random.randint(0, 3000)
            elif comp["type"] == "tech":
                recruit["cost"] = 4000 + random.randint(0, 4000)
            elif comp["type"] == "social":
                recruit["cost"] = 3000 + random.randint(0, 2000)
            else:
                recruit["cost"] = 2000 + random.randint(0, 3000)

            recruit["utility"] = f"{comp['type']} — {comp.get('nickname', comp['name'])}"
            recruits.append(recruit)

        # If no location-specific companions, add 1-2 random generic ones
        if not recruits:
            count = random.randint(1, 2)
            for _ in range(count):
                template = random.choice(COMPANION_TEMPLATES)
                name = random.choice(template["name_pool"])
                recruit = {
                    "id": str(uuid.uuid4())[:8],
                    "name": name,
                    "type": template["type"],
                    "skills": dict(template["skills"]),
                    "personality": template["personality"],
                    "cost": template["cost"] + random.randint(-500, 500),
                    "loyalty": template["loyalty_base"],
                    "max_loyalty": 100,
                    "combat_bonus": template["combat_bonus"],
                    "utility": template["utility"],
                    "hp": 30 + random.randint(0, 20),
                    "max_hp": 50,
                    "status": "available",
                    "personal_quest": None,
                }
                recruits.append(recruit)

        return recruits

    def recruit(self, companion: Dict, player_credits: int) -> Dict:
        if len(self.companions) >= self.MAX_COMPANIONS:
            return {"error": f"Максимум {self.MAX_COMPANIONS} компаньона"}
        if player_credits < companion["cost"]:
            return {"error": f"Не хватает кредитов: нужно {companion['cost']}₡"}

        companion["status"] = "active"
        self.companions.append(companion)
        return {"recruited": companion["name"], "cost": companion["cost"],
                "team_size": len(self.companions)}

    def dismiss(self, companion_id: str) -> Dict:
        comp = next((c for c in self.companions if c["id"] == companion_id), None)
        if not comp:
            return {"error": "Компаньон не найден"}
        self.companions.remove(comp)
        comp["status"] = "dismissed"
        self.dismissed.append(comp)
        return {"dismissed": comp["name"]}

    def update_loyalty(self, companion_id: str, event_type: str) -> Dict:
        comp = next((c for c in self.companions if c["id"] == companion_id), None)
        if not comp:
            return {"error": "Компаньон не найден"}

        events = LOYALTY_EVENTS.get("positive" if event_type in
            [e["trigger"] for e in LOYALTY_EVENTS["positive"]] else "negative", [])
        event = next((e for e in events if e["trigger"] == event_type), None)
        if not event:
            return {"error": "Неизвестное событие"}

        comp["loyalty"] = max(0, min(100, comp["loyalty"] + event["change"]))
        text = event["text"].format(name=comp["name"])

        if comp["loyalty"] <= 0:
            self.companions.remove(comp)
            comp["status"] = "deserted"
            text += f" {comp['name']} покинул команду!"

        return {"loyalty": comp["loyalty"], "change": event["change"], "text": text}

    def get_combat_bonus(self) -> int:
        return sum(c["combat_bonus"] for c in self.companions if c["status"] == "active")

    def get_skill_bonus(self, skill: str) -> int:
        bonus = 0
        for c in self.companions:
            if c["status"] == "active" and skill in c["skills"]:
                bonus = max(bonus, c["skills"][skill] // 2)
        return bonus

    def get_prompt_context(self) -> str:
        if not self.companions:
            return ""
        lines = ["[КОМАНДА]"]
        for c in self.companions:
            lines.append(f"  {c['name']} ({c['type']}): лояльность {c['loyalty']}%, HP {c['hp']}/{c['max_hp']}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {"companions": self.companions, "dismissed": self.dismissed}

    @classmethod
    def from_dict(cls, data: Dict) -> 'CompanionSystem':
        cs = cls()
        cs.companions = data.get("companions", [])
        cs.dismissed = data.get("dismissed", [])
        return cs


# ════════════════════════════════════════════════════════════
#  SHIP SYSTEM — ownership, upgrades, cargo, space combat
# ════════════════════════════════════════════════════════════

SHIP_CLASSES = {
    "shuttle": {"name": "Шаттл", "hull": 30, "cargo": 5, "crew": 2, "weapon_slots": 0,
                "speed": 3, "stealth": 1, "fuel_max": 100, "fuel_per_jump": 10},
    "trader": {"name": "Торговец", "hull": 50, "cargo": 40, "crew": 6, "weapon_slots": 1,
               "speed": 2, "stealth": 0, "fuel_max": 200, "fuel_per_jump": 20},
    "fighter": {"name": "Истребитель", "hull": 40, "cargo": 5, "crew": 1, "weapon_slots": 2,
                "speed": 5, "stealth": 2, "fuel_max": 80, "fuel_per_jump": 8},
    "corvette": {"name": "Корвет", "hull": 80, "cargo": 20, "crew": 8, "weapon_slots": 4,
                 "speed": 3, "stealth": 1, "fuel_max": 250, "fuel_per_jump": 25},
    "freighter": {"name": "Грузовоз", "hull": 70, "cargo": 100, "crew": 10, "weapon_slots": 2,
                  "speed": 1, "stealth": 0, "fuel_max": 300, "fuel_per_jump": 30},
    "gunship": {"name": "Канонерка", "hull": 100, "cargo": 15, "crew": 12, "weapon_slots": 6,
                "speed": 2, "stealth": 0, "fuel_max": 200, "fuel_per_jump": 25},
}

SHIP_UPGRADES = [
    {"id": "shield_mk1", "name": "Щит «Эгида» Mk.I", "type": "shield", "stats": {"shield_hp": 20}, "price": 15000},
    {"id": "shield_mk2", "name": "Щит «Эгида» Mk.II", "type": "shield", "stats": {"shield_hp": 40}, "price": 35000},
    {"id": "engine_boost", "name": "Ускоритель «Пуля»", "type": "engine", "stats": {"speed": 1}, "price": 12000},
    {"id": "cargo_bay", "name": "Доп. грузовой отсек", "type": "cargo", "stats": {"cargo": 20}, "price": 8000},
    {"id": "stealth_plating", "name": "Стелс-покрытие", "type": "stealth", "stats": {"stealth": 3}, "price": 40000},
    {"id": "scanner_hawk", "name": "Сканер «Ястреб»", "type": "scanner", "stats": {"detection": 3}, "price": 10000},
    {"id": "turret_auto", "name": "Автотурель «Страж»", "type": "weapon", "stats": {"auto_damage": 4}, "price": 18000},
    {"id": "hull_reinforce", "name": "Усиление корпуса", "type": "hull", "stats": {"hull": 20}, "price": 12000},
    {"id": "fuel_tank", "name": "Доп. топливный бак", "type": "fuel", "stats": {"fuel_max": 100}, "price": 5000},
    {"id": "medbay", "name": "Медотсек", "type": "utility", "stats": {"healing": 5}, "price": 15000},
    {"id": "smuggler_hold", "name": "Потайной отсек", "type": "cargo", "stats": {"hidden_cargo": 10}, "price": 20000},
    {"id": "mining_laser", "name": "Горный лазер", "type": "utility", "stats": {"mining": 3}, "price": 10000},
]


class ShipSystem:
    """Manage player ship: ownership, upgrades, cargo, fuel."""

    def __init__(self):
        self.ship = None

    def buy_ship(self, ship_class: str, name: str = None) -> Dict:
        template = SHIP_CLASSES.get(ship_class)
        if not template:
            return {"error": "Неизвестный класс корабля"}

        self.ship = {
            "id": str(uuid.uuid4())[:8],
            "name": name or f"Корабль-{random.randint(100,999)}",
            "class": ship_class,
            "class_name": template["name"],
            "hull": template["hull"],
            "max_hull": template["hull"],
            "shield_hp": 0,
            "max_shield": 0,
            "cargo_capacity": template["cargo"],
            "cargo": [],
            "crew_capacity": template["crew"],
            "weapon_slots": template["weapon_slots"],
            "weapons": [],
            "upgrades": [],
            "speed": template["speed"],
            "stealth": template["stealth"],
            "fuel": template["fuel_max"],
            "fuel_max": template["fuel_max"],
            "fuel_per_jump": template["fuel_per_jump"],
            "condition": 100,
        }
        return {"ship_acquired": self.ship}

    def install_upgrade(self, upgrade_id: str) -> Dict:
        if not self.ship:
            return {"error": "Нет корабля"}

        upgrade = next((u for u in SHIP_UPGRADES if u["id"] == upgrade_id), None)
        if not upgrade:
            return {"error": "Неизвестный апгрейд"}

        self.ship["upgrades"].append(upgrade)
        for stat, val in upgrade["stats"].items():
            if stat in self.ship:
                self.ship[stat] += val
            elif stat == "shield_hp":
                self.ship["shield_hp"] += val
                self.ship["max_shield"] += val
            elif stat == "cargo":
                self.ship["cargo_capacity"] += val

        return {"installed": upgrade["name"], "ship": self.ship}

    def load_cargo(self, item_name: str, quantity: int = 1) -> Dict:
        if not self.ship:
            return {"error": "Нет корабля"}
        current = len(self.ship["cargo"])
        if current + quantity > self.ship["cargo_capacity"]:
            return {"error": f"Нет места: {current}/{self.ship['cargo_capacity']}"}

        for _ in range(quantity):
            self.ship["cargo"].append(item_name)
        return {"loaded": item_name, "qty": quantity,
                "cargo": f"{len(self.ship['cargo'])}/{self.ship['cargo_capacity']}"}

    def use_fuel(self, jumps: int = 1) -> Dict:
        if not self.ship:
            return {"error": "Нет корабля"}
        cost = self.ship["fuel_per_jump"] * jumps
        if self.ship["fuel"] < cost:
            return {"error": f"Мало топлива: {self.ship['fuel']}/{cost}"}
        self.ship["fuel"] -= cost
        return {"fuel_used": cost, "fuel_remaining": self.ship["fuel"]}

    def repair(self, amount: int = None) -> Dict:
        if not self.ship:
            return {"error": "Нет корабля"}
        if amount is None:
            amount = self.ship["max_hull"] - self.ship["hull"]
        cost = amount * 50
        self.ship["hull"] = min(self.ship["max_hull"], self.ship["hull"] + amount)
        return {"repaired": amount, "hull": f"{self.ship['hull']}/{self.ship['max_hull']}", "cost": cost}

    def get_prompt_context(self) -> str:
        if not self.ship:
            return ""
        s = self.ship
        return (f"[КОРАБЛЬ] «{s['name']}» ({s['class_name']}): корпус {s['hull']}/{s['max_hull']}, "
                f"щит {s['shield_hp']}/{s['max_shield']}, груз {len(s['cargo'])}/{s['cargo_capacity']}, "
                f"топливо {s['fuel']}/{s['fuel_max']}, скорость {s['speed']}, стелс {s['stealth']}")

    def to_dict(self) -> Dict:
        return {"ship": self.ship}

    @classmethod
    def from_dict(cls, data: Dict) -> 'ShipSystem':
        ss = cls()
        ss.ship = data.get("ship")
        return ss


# ════════════════════════════════════════════════════════════
#  PROPERTY SYSTEM — owned locations, income, storage
# ════════════════════════════════════════════════════════════

PROPERTY_TYPES = {
    "apartment": {"name": "Квартира", "storage": 20, "income": 0, "defense": 1, "features": ["отдых", "сохранение"]},
    "warehouse": {"name": "Склад", "storage": 100, "income": 0, "defense": 2, "features": ["крафт-станция", "хранение"]},
    "shop": {"name": "Магазин", "storage": 30, "income": 500, "defense": 1, "features": ["торговля", "доход"]},
    "bar": {"name": "Бар", "storage": 15, "income": 400, "defense": 1, "features": ["слухи +3", "доход", "рекрут"]},
    "hideout": {"name": "Убежище", "storage": 30, "income": 0, "defense": 4, "features": ["скрытное", "безопасный дом"]},
    "office": {"name": "Офис фиксера", "storage": 10, "income": 800, "defense": 2, "features": ["квесты +2", "доход", "контакты"]},
}


class PropertySystem:
    """Manage owned properties: purchase, income, storage, defense."""

    def __init__(self):
        self.properties = []

    def buy_property(self, prop_type: str, location: str, name: str = None) -> Dict:
        template = PROPERTY_TYPES.get(prop_type)
        if not template:
            return {"error": "Неизвестный тип недвижимости"}

        prop = {
            "id": str(uuid.uuid4())[:8],
            "type": prop_type,
            "name": name or f"{template['name']} в {location}",
            "location": location,
            "storage_capacity": template["storage"],
            "stored_items": [],
            "income_per_cycle": template["income"],
            "defense_level": template["defense"],
            "features": list(template["features"]),
            "upgrades": [],
            "condition": 100,
        }
        self.properties.append(prop)
        return {"acquired": prop}

    def collect_income(self) -> Dict:
        total = 0
        breakdown = []
        for p in self.properties:
            if p["income_per_cycle"] > 0:
                income = p["income_per_cycle"]
                # Condition affects income
                income = int(income * (p["condition"] / 100))
                total += income
                breakdown.append({"name": p["name"], "income": income})
        return {"total_income": total, "breakdown": breakdown}

    def store_item(self, property_id: str, item_name: str) -> Dict:
        prop = next((p for p in self.properties if p["id"] == property_id), None)
        if not prop:
            return {"error": "Недвижимость не найдена"}
        if len(prop["stored_items"]) >= prop["storage_capacity"]:
            return {"error": "Хранилище полно"}
        prop["stored_items"].append(item_name)
        return {"stored": item_name, "capacity": f"{len(prop['stored_items'])}/{prop['storage_capacity']}"}

    def get_prompt_context(self) -> str:
        if not self.properties:
            return ""
        lines = ["[НЕДВИЖИМОСТЬ]"]
        for p in self.properties:
            lines.append(f"  {p['name']}: {', '.join(p['features'])}, "
                        f"хранилище {len(p['stored_items'])}/{p['storage_capacity']}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {"properties": self.properties}

    @classmethod
    def from_dict(cls, data: Dict) -> 'PropertySystem':
        ps = cls()
        ps.properties = data.get("properties", [])
        return ps
