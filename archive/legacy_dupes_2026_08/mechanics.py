"""
mechanics.py — Hard game mechanics for NEXUS RPG v4.6
Implements: ShopMechanics, TravelSystem, PropertyIncome, ConversationManager

All of these were previously "narrated" by AI without real state changes.
Now they enforce actual rules.
"""

import random
import re
from typing import Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════
#  SHOP MECHANICS — buy/sell with credit checks
# ════════════════════════════════════════════════════════════

class ShopMechanics:
    """Mechanical buy/sell with actual credit/inventory changes."""

    SELL_RATIO = 0.4  # items sell for 40% of shop price

    @staticmethod
    def buy_item(character: Dict, inventory: List[Dict], item: Dict) -> Dict:
        """
        Buy an item. Returns success/error dict.
        item = {"id": "W_PISTOL_BASIC", "name": "...", "price": 2500, "category": "weapons", "stats": "..."}
        """
        credits = character.get("credits", 0)
        price = item.get("price", 0)

        if price <= 0:
            return {"error": "Некорректная цена"}
        if credits < price:
            return {"error": f"Недостаточно кредитов: {credits}/{price}",
                    "shortfall": price - credits}

        # Deduct credits
        character["credits"] = credits - price

        # Add to inventory
        item_name = item.get("name", "?")
        found = False
        for inv_item in inventory:
            if inv_item.get("name") == item_name:
                inv_item["qty"] = inv_item.get("qty", 1) + 1
                found = True
                break
        if not found:
            inventory.append({
                "name": item_name,
                "id": item.get("id", ""),
                "qty": 1,
                "category": item.get("category", "misc"),
                "stats": item.get("stats", ""),
                "buy_price": price,
            })

        return {
            "success": True,
            "bought": item_name,
            "price": price,
            "credits_left": character["credits"],
        }

    @staticmethod
    def sell_item(character: Dict, inventory: List[Dict], item_name: str,
                  qty: int = 1) -> Dict:
        """Sell item from inventory at 40% value."""
        item_name_lower = item_name.lower()
        target = None
        for inv_item in inventory:
            if inv_item.get("name", "").lower() == item_name_lower:
                target = inv_item
                break
        # Fuzzy match
        if not target:
            for inv_item in inventory:
                if item_name_lower in inv_item.get("name", "").lower():
                    target = inv_item
                    break

        if not target:
            return {"error": f"Предмет «{item_name}» не найден в инвентаре"}

        if target.get("qty", 1) < qty:
            return {"error": f"Недостаточно: {target.get('qty', 1)} шт."}

        # Calculate sell price
        buy_price = target.get("buy_price", 100)
        sell_price = max(10, int(buy_price * ShopMechanics.SELL_RATIO)) * qty

        # Remove from inventory
        target["qty"] = target.get("qty", 1) - qty
        if target["qty"] <= 0:
            inventory.remove(target)

        # Add credits
        character["credits"] = character.get("credits", 0) + sell_price

        return {
            "success": True,
            "sold": target.get("name", item_name),
            "qty": qty,
            "earned": sell_price,
            "credits_now": character["credits"],
        }

    @staticmethod
    def find_shop_item(shop_items: List[Dict], query: str) -> Optional[Dict]:
        """Fuzzy-find item in shop by name or id."""
        q = query.lower().strip()
        # Exact id match
        for item in shop_items:
            if item.get("id", "").lower() == q:
                return item
        # Name contains
        for item in shop_items:
            if q in item.get("name", "").lower():
                return item
        # Partial match
        for item in shop_items:
            words = q.split()
            if all(w in item.get("name", "").lower() for w in words):
                return item
        return None


# ════════════════════════════════════════════════════════════
#  TRAVEL SYSTEM — mechanical movement with time & encounters
# ════════════════════════════════════════════════════════════

# Local travel times (minutes) by district type
LOCAL_TRAVEL_TIME = {
    "same_district": 5,
    "adjacent_district": 15,
    "cross_city": 30,
    "other_city": 120,
}

# Interplanetary travel data
PLANET_TRAVEL = {
    ("Земля", "Луна"): {"hours": 3, "fuel": 5, "risk": 0.05},
    ("Луна", "Земля"): {"hours": 3, "fuel": 5, "risk": 0.05},
    ("Земля", "Марс"): {"hours": 120, "fuel": 30, "risk": 0.10},
    ("Марс", "Земля"): {"hours": 120, "fuel": 30, "risk": 0.10},
    ("Земля", "Пояс астероидов"): {"hours": 200, "fuel": 50, "risk": 0.15},
    ("Пояс астероидов", "Земля"): {"hours": 200, "fuel": 50, "risk": 0.15},
    ("Земля", "Ганимед"): {"hours": 180, "fuel": 45, "risk": 0.15},
    ("Ганимед", "Земля"): {"hours": 180, "fuel": 45, "risk": 0.15},
    ("Марс", "Пояс астероидов"): {"hours": 100, "fuel": 25, "risk": 0.10},
    ("Пояс астероидов", "Марс"): {"hours": 100, "fuel": 25, "risk": 0.10},
    ("Марс", "Ганимед"): {"hours": 150, "fuel": 40, "risk": 0.12},
    ("Ганимед", "Марс"): {"hours": 150, "fuel": 40, "risk": 0.12},
    ("Пояс астероидов", "Ганимед"): {"hours": 80, "fuel": 20, "risk": 0.10},
    ("Ганимед", "Пояс астероидов"): {"hours": 80, "fuel": 20, "risk": 0.10},
    ("Марс", "Луна"): {"hours": 110, "fuel": 28, "risk": 0.08},
    ("Луна", "Марс"): {"hours": 110, "fuel": 28, "risk": 0.08},
    ("Луна", "Пояс астероидов"): {"hours": 190, "fuel": 48, "risk": 0.14},
    ("Пояс астероидов", "Луна"): {"hours": 190, "fuel": 48, "risk": 0.14},
    ("Луна", "Ганимед"): {"hours": 170, "fuel": 42, "risk": 0.13},
    ("Ганимед", "Луна"): {"hours": 170, "fuel": 42, "risk": 0.13},
}

SPACE_ENCOUNTERS = [
    {"name": "Пиратский рейдер", "type": "combat", "chance": 0.3,
     "text": "Радар засекает приближающийся корабль — транспондер отключён. Пираты!",
     "hp_risk": -15, "credits_risk": -500},
    {"name": "Астероидное поле", "type": "hazard", "chance": 0.2,
     "text": "Поток мелких астероидов на курсе. Корпус содрогается от ударов.",
     "hp_risk": -10, "credits_risk": 0},
    {"name": "Сигнал бедствия", "type": "choice", "chance": 0.15,
     "text": "Слабый сигнал SOS с дрейфующего корабля. Может быть ловушка, а может — выжившие.",
     "hp_risk": 0, "credits_risk": 0},
    {"name": "Патруль МФЗС", "type": "check", "chance": 0.15,
     "text": "Патрульный крейсер запрашивает идентификацию. Сканирование груза.",
     "hp_risk": 0, "credits_risk": -200},
    {"name": "Блуждающий контейнер", "type": "loot", "chance": 0.1,
     "text": "Обнаружен дрейфующий грузовой контейнер. Содержимое неизвестно.",
     "hp_risk": 0, "credits_risk": 300},
    {"name": "Протомолекулярная аномалия", "type": "mystery", "chance": 0.05,
     "text": "Датчики сходят с ума — голубое свечение по курсу. Протомолекула?",
     "hp_risk": -5, "credits_risk": 0},
    {"name": "Торговый караван", "type": "trade", "chance": 0.05,
     "text": "Встречный конвой предлагает обмен на лёту. Хорошие цены.",
     "hp_risk": 0, "credits_risk": 200},
]

# Local (ground) encounters during district travel
LOCAL_ENCOUNTERS = [
    {"text": "Уличный проповедник кричит о конце времён. Толпа вокруг.", "chance": 0.1},
    {"text": "Полиция оцепила переулок — кто-то ограблен.", "chance": 0.08},
    {"text": "Драка двух пьяных у бара. Охрана не вмешивается.", "chance": 0.07},
    {"text": "Беспилотник-курьер врезается в стену. Содержимое рассыпается.", "chance": 0.06},
    {"text": "Подозрительный тип предлагает «товар по хорошей цене».", "chance": 0.08},
    {"text": "Группа протестующих OPA блокирует коридор.", "chance": 0.06},
    {"text": "На экранах срочная новость — взрыв на соседней станции.", "chance": 0.05},
    {"text": "Знакомое лицо мелькает в толпе и исчезает.", "chance": 0.04},
    {"text": "Запах свежеприготовленного рамена из подвального кафе.", "chance": 0.1},
    {"text": "Мерцающая голограмма рекламирует новые импланты.", "chance": 0.1},
]


class TravelSystem:
    """Mechanical travel: local + interplanetary with time, fuel, encounters."""

    @staticmethod
    def travel_local(current_loc: Dict, destination: str, galaxy_map) -> Dict:
        """
        Travel within the same planet. Returns travel result.
        destination = district name or establishment name
        """
        planet = current_loc.get("planet", "")
        city = current_loc.get("city", "")
        current_district = current_loc.get("district", "")

        # Try to find destination district
        dest_district = None
        dest_city = city
        dest_place = ""

        # 1. Exact district match in current city
        districts = galaxy_map.list_districts(planet, city)
        for d in districts:
            if destination.lower() in d["name"].lower():
                dest_district = d["name"]
                break

        # 2. Check establishments in current city
        if not dest_district:
            for d in districts:
                estabs = galaxy_map.list_establishments(planet, city, d["name"])
                for e in estabs:
                    if destination.lower() in e["name"].lower():
                        dest_district = d["name"]
                        dest_place = e["name"]
                        break
                if dest_district:
                    break

        # 3. Check other cities on same planet
        if not dest_district:
            for other_city in galaxy_map.list_cities(planet):
                if other_city == city:
                    continue
                other_districts = galaxy_map.list_districts(planet, other_city)
                for d in other_districts:
                    if destination.lower() in d["name"].lower():
                        dest_district = d["name"]
                        dest_city = other_city
                        break
                if dest_district:
                    break

        if not dest_district:
            return {
                "error": f"Не удалось найти «{destination}» на {planet}",
                "available": [d["name"] for d in districts],
            }

        # Calculate travel time
        if dest_district == current_district:
            travel_min = LOCAL_TRAVEL_TIME["same_district"]
        elif dest_city != city:
            travel_min = LOCAL_TRAVEL_TIME["other_city"]
        else:
            travel_min = LOCAL_TRAVEL_TIME["adjacent_district"]

        # Random encounter?
        encounter = None
        if random.random() < 0.15:
            enc_candidates = [e for e in LOCAL_ENCOUNTERS if random.random() < e["chance"]]
            if enc_candidates:
                encounter = random.choice(enc_candidates)

        # New location
        new_loc = {
            "planet": planet,
            "city": dest_city,
            "district": dest_district,
            "place": dest_place,
        }

        return {
            "success": True,
            "travel_type": "local",
            "from": current_district,
            "to": dest_district,
            "place": dest_place,
            "new_location": new_loc,
            "travel_minutes": travel_min,
            "encounter": encounter,
        }

    @staticmethod
    def travel_interplanetary(current_loc: Dict, dest_planet: str,
                               ship_system, character: Dict) -> Dict:
        """
        Travel between planets. Requires ship, fuel. Returns result.
        """
        from_planet = current_loc.get("planet", "")

        if from_planet == dest_planet:
            return {"error": "Вы уже на этой планете"}

        # Check ship
        if not ship_system.ship:
            return {"error": "Нет корабля! Купите или наймите транспорт."}

        # Find route
        route_key = (from_planet, dest_planet)
        route = PLANET_TRAVEL.get(route_key)
        if not route:
            return {"error": f"Нет маршрута {from_planet} → {dest_planet}"}

        # Check fuel
        fuel_needed = route["fuel"]
        current_fuel = ship_system.ship.get("fuel", 0)
        if current_fuel < fuel_needed:
            return {
                "error": f"Недостаточно топлива: {current_fuel}/{fuel_needed}",
                "need_fuel": fuel_needed - current_fuel,
            }

        # Consume fuel
        ship_system.ship["fuel"] = current_fuel - fuel_needed

        # Travel time in hours
        hours = route["hours"]
        # Speed modifier from ship
        speed_mod = ship_system.ship.get("speed", 5) / 5.0
        hours = max(1, int(hours / speed_mod))

        # Space encounter?
        encounter = None
        if random.random() < route["risk"]:
            candidates = [e for e in SPACE_ENCOUNTERS if random.random() < e["chance"]]
            if candidates:
                encounter = random.choice(candidates)
                # Apply hp/credit risks
                if encounter.get("hp_risk", 0) < 0:
                    hull_dmg = abs(encounter["hp_risk"])
                    ship_system.ship["hull"] = max(0,
                        ship_system.ship.get("hull", 50) - hull_dmg)
                if encounter.get("credits_risk", 0) != 0:
                    character["credits"] = max(0,
                        character.get("credits", 0) + encounter["credits_risk"])

        # Default arrival location per planet
        PLANET_DEFAULTS = {
            "Земля": {"city": "Нью-Токио", "district": "Индустриальный коридор"},
            "Марс": {"city": "Новый Бостон", "district": "Окружное кольцо"},
            "Пояс астероидов": {"city": "Станция Церера-Прайм", "district": "Шахтёрский квартал"},
            "Ганимед": {"city": "Станция Юпитер-Прайм", "district": "Торговые палубы"},
            "Луна": {"city": "Лунаград", "district": "Центральный купол"},
        }
        dest_info = PLANET_DEFAULTS.get(dest_planet, {"city": dest_planet, "district": "Центр"})

        new_loc = {
            "planet": dest_planet,
            "city": dest_info["city"],
            "district": dest_info["district"],
            "place": "",
        }

        return {
            "success": True,
            "travel_type": "interplanetary",
            "from_planet": from_planet,
            "to_planet": dest_planet,
            "new_location": new_loc,
            "travel_hours": hours,
            "travel_minutes": hours * 60,
            "fuel_used": fuel_needed,
            "fuel_remaining": ship_system.ship["fuel"],
            "encounter": encounter,
        }


# ════════════════════════════════════════════════════════════
#  PROPERTY INCOME ON TIME TICK
# ════════════════════════════════════════════════════════════

class PropertyIncomeManager:
    """Collect property income based on game-time, not turns."""

    def __init__(self):
        self.last_collection_hours = 0  # game-time hours of last collection
        self.income_interval_hours = 168  # collect every ~7 game-days

    def tick(self, current_hours: float, property_system, character: Dict) -> Optional[Dict]:
        """Check if income should be collected. Returns income dict or None."""
        if not property_system.properties:
            return None

        if (current_hours - self.last_collection_hours) >= self.income_interval_hours:
            result = property_system.collect_income()
            total = result.get("total_income", 0)
            if total > 0:
                character["credits"] = character.get("credits", 0) + total
                self.last_collection_hours = current_hours
                return result
        return None

    def to_dict(self) -> Dict:
        return {
            "last_collection_hours": self.last_collection_hours,
            "income_interval_hours": self.income_interval_hours,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PropertyIncomeManager':
        m = cls()
        m.last_collection_hours = data.get("last_collection_hours", 0)
        m.income_interval_hours = data.get("income_interval_hours", 168)
        return m


# ════════════════════════════════════════════════════════════
#  CONVERSATION MANAGER — summarize old messages
# ════════════════════════════════════════════════════════════

class ConversationManager:
    """Manage conversation history: keep recent, summarize old."""

    MAX_RECENT = 12  # keep last 12 messages as-is for AI
    SUMMARIZE_BATCH = 10  # summarize every 10 old messages into 1 summary

    @staticmethod
    def manage_history(conversation_history: List[Dict]) -> List[Dict]:
        """
        If history > MAX_RECENT * 2, compress older messages into summaries.
        Returns the managed history list (modified in place).
        """
        if len(conversation_history) <= ConversationManager.MAX_RECENT * 2:
            return conversation_history

        # Split: old + recent
        recent_count = ConversationManager.MAX_RECENT
        old = conversation_history[:-recent_count]
        recent = conversation_history[-recent_count:]

        # Summarize old messages in batches
        summaries = []
        for i in range(0, len(old), ConversationManager.SUMMARIZE_BATCH):
            batch = old[i:i + ConversationManager.SUMMARIZE_BATCH]
            summary = ConversationManager._summarize_batch(batch)
            summaries.append({
                "role": "system",
                "content": f"[КРАТКОЕ СОДЕРЖАНИЕ ПРЕДЫДУЩИХ СОБЫТИЙ]\n{summary}",
            })

        # Replace old with summaries
        new_history = summaries + recent
        conversation_history.clear()
        conversation_history.extend(new_history)
        return conversation_history

    @staticmethod
    def _summarize_batch(messages: List[Dict]) -> str:
        """Create a brief summary of a batch of messages."""
        actions = []
        events = []
        npcs_seen = set()

        for msg in messages:
            content = msg.get("content", "")[:200]
            role = msg.get("role", "")

            if role == "user":
                # Extract action verbs
                actions.append(content[:80])
            elif role == "assistant":
                # Extract key events and NPC names
                # Find capitalized names (Russian pattern)
                names = re.findall(r'[А-Я][а-яё]+\s+[А-Я][а-яё]+', content)
                npcs_seen.update(names[:2])
                # Extract first sentence as event
                first_sent = content.split('.')[0][:80] if content else ""
                if first_sent:
                    events.append(first_sent)
            elif role == "system":
                # Keep system summaries as-is
                return content[:200]

        parts = []
        if actions:
            parts.append(f"Действия: {'; '.join(actions[:3])}")
        if events:
            parts.append(f"События: {'; '.join(events[:3])}")
        if npcs_seen:
            parts.append(f"NPC: {', '.join(list(npcs_seen)[:4])}")

        return " | ".join(parts) if parts else "Обычные события."


# ════════════════════════════════════════════════════════════
#  ACTION PARSER — detect buy/sell/travel from player text
# ════════════════════════════════════════════════════════════

# Keywords for mechanical actions
BUY_KEYWORDS = ["купить", "куплю", "покупаю", "приобрести", "приобретаю", "беру"]
SELL_KEYWORDS = ["продать", "продаю", "продам", "сбыть", "сбываю"]
TRAVEL_KEYWORDS = ["идти", "иду", "пойти", "перейти", "поехать", "еду", "лететь",
                    "летим", "направиться", "двигаться", "отправиться", "отправляюсь",
                    "переместиться", "перехожу", "go to", "travel"]


def detect_mechanical_action(action: str) -> Optional[Dict]:
    """
    Parse player text to detect buy/sell/travel intent.
    Returns {type: "buy"|"sell"|"travel", target: str} or None.
    """
    action_lower = action.lower().strip()

    # Buy detection
    for kw in BUY_KEYWORDS:
        if kw in action_lower:
            # Extract what comes after the keyword
            idx = action_lower.find(kw) + len(kw)
            target = action[idx:].strip().strip('«»"\'.,!?')
            if target:
                return {"type": "buy", "target": target}

    # Sell detection
    for kw in SELL_KEYWORDS:
        if kw in action_lower:
            idx = action_lower.find(kw) + len(kw)
            target = action[idx:].strip().strip('«»"\'.,!?')
            if target:
                return {"type": "sell", "target": target}

    # Travel detection
    for kw in TRAVEL_KEYWORDS:
        if kw in action_lower:
            # Look for preposition patterns: "в доки", "на марс", "к бару"
            patterns = [
                rf'{kw}\s+(?:в|на|к|до)\s+(.+)',
                rf'{kw}\s+(.+)',
            ]
            for pattern in patterns:
                m = re.search(pattern, action_lower)
                if m:
                    target = m.group(1).strip().strip('«»"\'.,!?')
                    if target and len(target) > 1:
                        return {"type": "travel", "target": target}

    # Planet names direct mention with travel context
    planets = ["земля", "марс", "пояс астероидов", "ганимед", "луна", "церер"]
    for p in planets:
        if p in action_lower and any(kw in action_lower for kw in ["лететь", "летим", "полететь", "курс на", "на " + p]):
            target_planet = p.title()
            if "церер" in p:
                target_planet = "Пояс астероидов"
            return {"type": "travel_planet", "target": target_planet}

    return None
