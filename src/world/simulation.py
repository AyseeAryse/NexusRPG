"""
World Simulator — живой мир NEXUS RPG.
Генерирует фоновые события, новости, экономику, атмосферу.
Запускается каждый ход и подаёт контекст AI-мастеру.
"""
import random
from typing import Dict, List, Optional


# ═══════════════════════════════════════
# НОВОСТИ И СЛУХИ
# ═══════════════════════════════════════

NEWS_TEMPLATES = {
    "political": [
        "Совет Солнечной Системы объявил о новых санкциях против {faction1} за нарушение Хартии Меча.",
        "Марсианская Конгрессионная Республика отозвала посла с Земли — дипломатический кризис углубляется.",
        "OPA выступила с заявлением: «Пояс не будет кормить Землю бесплатно». Белтеры готовят забастовку.",
        "Скандал в UEG: утечка документов показала тайное финансирование ЧВК {pmc} из бюджета.",
        "Голосование в Совете провалилось — Марс наложил вето на регуляцию протомолекулярных исследований.",
        "Губернатор Цереры арестован по обвинению в коррупции. OPA требует новых выборов.",
        "Free Mars Movement провело крупнейший митинг в истории Нового Бостона. МКР усилила патрули.",
        "DataVault Corp обвинена в продаже персональных данных трём разведкам одновременно.",
    ],
    "economic": [
        "Цены на гелий-3 выросли на {percent}% после аварии на добывающей станции Титана.",
        "QuantumMeals объявила о повышении цен на синтетическую пищу — беднейшие районы Земли на грани бунта.",
        "Helios Energy Corp поглотила мелкого конкурента — монополия на энергетику усиливается.",
        "Чёрный рынок Цереры переживает бум: спрос на контрабандные импланты вырос втрое.",
        "Kurosawa Heavy Industries представила новое поколение Frame Unit — акции взлетели на {percent}%.",
        "Экономический пузырь в секторе биотехнологий — аналитики предрекают крах в ближайшие месяцы.",
        "Торговый маршрут Земля-Марс нарушен: пираты Void Reapers захватили грузовой конвой.",
        "Кредитные дуэли на Церере набирают популярность — подпольные арены генерируют миллионы.",
    ],
    "military": [
        "SENTINEL Corp перебросила 3 батальона к границе Пояса. Белтеры в тревоге.",
        "Iron Wolves объявили о наборе — нужны пилоты Frame Unit для «охранного контракта».",
        "Неопознанный военный корабль замечен в секторе Юпитера. Все фракции отрицают причастность.",
        "Black Aegis провела кибератаку на серверы конкурента — данные тысяч контрактов в открытом доступе.",
        "Марсианский флот провёл учения вблизи Цереры. OPA расценила это как провокацию.",
        "Бой между пиратами и конвоем Helios в Поясе — 12 погибших, 3 корабля уничтожены.",
        "Ronin Group отказалась от контракта UEG — причины не раскрыты. Аналитики в замешательстве.",
        "Прототип нового Frame Unit Mk.IV украден с завода Kurosawa. Подозревают агентов Protogen.",
    ],
    "tech": [
        "Protogen объявила о прорыве в исследовании протомолекулы — подробности засекречены.",
        "Genesis Bioworks выпустила новую линейку имплантов — на 40% меньше побочных эффектов.",
        "LunarTech Industries представила квантовый ИИ 7-го поколения. Этические комиссии бьют тревогу.",
        "Хакеры Data Rebels взломали спутниковую сеть UEG — транслировали секретные документы 4 часа.",
        "Новая болезнь «нейро-эрозия» поражает носителей имплантов 3-го поколения. Массовый отзыв.",
        "На Ганимеде обнаружен новый слой протомолекулы — учёные говорят о «живом артефакте».",
        "Вирус «DataStorm 2.0» парализовал банковскую систему Пояса на 6 часов. Убытки — миллиарды.",
        "Первый успешный перенос сознания в цифровую среду. Этический скандал разгорается.",
    ],
    "crime": [
        "Black Lotus Triad захватила контроль над 3 доковыми зонами Цереры. Полиция бессильна.",
        "Серия убийств корпоративных менеджеров в Нью-Токио — полиция подозревает ЧВК.",
        "Подпольная лаборатория по производству «Красного Льда» обнаружена в жилом секторе.",
        "Контрабандисты используют новый маршрут через обломки станции «Тихон».",
        "Загадочный хакер «Немезида» снова появился — опубликованы данные о коррупции в Совете.",
        "Ограбление транспорта Genesis Bioworks — похищена партия экспериментальных имплантов.",
        "В нижних уровнях Нью-Токио обнаружена подпольная арена боёв на Frame Units.",
        "Информатор Совета найден мёртвым на станции Тихо. Дело засекречено.",
    ],
    "local": [
        "В {district} произошла утечка токсичных отходов. Район эвакуирован на 12 часов.",
        "Забастовка докеров парализовала грузовые терминалы. Товары задерживаются.",
        "Фестиваль «Неоновые Ночи» привлёк тысячи туристов. Полиция усилила патрули.",
        "Пожар на складском уровне — трое погибших, десятки пострадавших.",
        "Новый бар «Красный Дракон» открылся в районе — ходят слухи о связях с Triad.",
        "Странные сигналы из заброшенного сектора станции. Техники отказываются проверять.",
        "Корпоративная охрана {corp} ужесточила проверки — очереди на входе растут.",
        "Местный авторитет «Шакал» объявил о «защите» района. Жители платят или уходят.",
    ],
}

RUMORS = [
    "Ходят слухи, что {npc} связан с Shadow Consortium.",
    "Говорят, под {location} есть заброшенные тоннели с довоенным оборудованием.",
    "Кто-то видел, как агенты {pmc} встречались с людьми из {faction}.",
    "Слышал, что {corp} проводит незаконные эксперименты на людях.",
    "Бармен рассказал, что скоро будет большая «чистка» в {district}.",
    "Торговец шепнул, что партия {item} будет на чёрном рынке через пару дней.",
    "Похоже, {npc} ищет наёмника для деликатной работы. Хорошо платит.",
    "Кто-то видел, как в доках разгружали контейнер с маркировкой Protogen.",
]

# ═══════════════════════════════════════
# АТМОСФЕРА ПО ВРЕМЕНИ И МЕСТУ
# ═══════════════════════════════════════

ATMOSPHERE = {
    "time_of_day": {
        "morning": {
            "light": "тусклый утренний свет пробивается сквозь смог и неон",
            "sounds": "гул просыпающегося города, лязг металла, далёкие сирены",
            "activity": "Рабочие спешат на смены, дроны-уборщики убирают ночной мусор",
            "mood": "Город просыпается тяжело, как с похмелья",
        },
        "afternoon": {
            "light": "резкий искусственный свет и блики голограмм на мокром асфальте",
            "sounds": "какофония рекламы, гудение аэромобилей, крики торговцев",
            "activity": "Толпы людей, патрульные дроны, корпоративные курьеры",
            "mood": "Город бурлит энергией и отчаянием одновременно",
        },
        "evening": {
            "light": "неоновое зарево заливает улицы красным и синим, тени удлиняются",
            "sounds": "басы из баров, смех, далёкие выстрелы, шёпот информаторов",
            "activity": "Ночная жизнь пробуждается — бары, казино, подпольные арены",
            "mood": "Опасность и возможности прячутся за каждым углом",
        },
        "night": {
            "light": "мерцающий неон — единственный свет, остальное тонет в тени",
            "sounds": "капли конденсата, шаги в темноте, гул вентиляции, далёкие крики",
            "activity": "Контрабандисты, наёмники, корпоративные агенты — ночные жители",
            "mood": "Ночь принадлежит тем, кто не боится темноты",
        },
    },
    "weather": {
        "universal": [
            "Густой смог висит над городом, видимость — 30 метров.",
            "Ясно, но небо серое от промышленных выбросов. Солнце — тусклый диск за пеленой.",
            "Электромагнитная буря — голограммы мерцают, дроны летают нестабильно.",
            "Жара от вентиляционных выбросов. Воздух дрожит, пахнет озоном и раскалённым металлом.",
        ],
        "Земля": [
            "Кислотный дождь стучит по козырькам и зонтам, оставляя разводы на бетоне.",
            "Мелкая морось, смешанная со смогом — воздух густой, серый, давит на лёгкие.",
            "Удушающая влажность, от вентиляционных решёток поднимается пар.",
        ],
        "Марс": [
            "Снежная пыль — красноватые хлопья оседают на визорах и плечах.",
            "Песчаная буря за куполом — небо стало оранжевым, стены гудят.",
            "Тонкий иней на внутренней стороне купола — система отопления барахлит.",
        ],
        "Пояс астероидов": [
            "В куполе станции всегда одинаковая температура, но сегодня система сбоит — холодно.",
            "Лёгкая вибрация пола — мимо станции прошёл грузовой конвой.",
            "Воздух сухой и переработанный, пахнет металлом и антисептиком.",
        ],
        "Ганимед": [
            "За стенами станции -160°C. Изнутри — холодный конденсат на переборках.",
            "Подземный уровень — тихое гудение теплообменников, стерильный воздух.",
            "Лёгкая дрожь — тектоническая активность Ганимеда напоминает о себе.",
        ],
    },
    "planet_vibes": {
        "Земля": "Перенаселённая, задыхающаяся. Неон и бетон. Корпоративные небоскрёбы возвышаются над трущобами.",
        "Марс": "Красная пыль, купола, военная дисциплина. Чистые линии архитектуры. Патриотические плакаты.",
        "Пояс астероидов": "Переработанный металл, невесомость, импровизация. Свобода и опасность рядом.",
        "Ганимед": "Ледяной мир, подземные станции, научные лаборатории. Тишина и холод.",
    },
}

# ═══════════════════════════════════════
# ЭКОНОМИКА — МАГАЗИНЫ И ЦЕНЫ
# ═══════════════════════════════════════

from src.content.base import EXPANDED_SHOP_ITEMS, EXPANDED_MATERIALS
from src.content.v2_legacy import V2_SHOP_ITEMS
from src.content.v3_legacy import V3_SHOP_ITEMS

BASE_SHOP_ITEMS = EXPANDED_SHOP_ITEMS

# Add craft materials to shop
BASE_SHOP_ITEMS["craft_materials"] = [
    {"id": f"M_{i}", "name": m["name"], "base_price": m["price"],
     "stats": "Компонент для крафта", "rarity": m["rarity"]}
    for i, m in enumerate(EXPANDED_MATERIALS)
]

# Merge V2 expanded items (dedup by id)
for cat, items in V2_SHOP_ITEMS.items():
    existing_ids = {i["id"] for i in BASE_SHOP_ITEMS.get(cat, [])}
    if cat not in BASE_SHOP_ITEMS:
        BASE_SHOP_ITEMS[cat] = []
    for item in items:
        if item["id"] not in existing_ids:
            BASE_SHOP_ITEMS[cat].append(item)

# Merge V3 expanded items (dedup by id)
for cat, items in V3_SHOP_ITEMS.items():
    existing_ids = {i["id"] for i in BASE_SHOP_ITEMS.get(cat, [])}
    if cat not in BASE_SHOP_ITEMS:
        BASE_SHOP_ITEMS[cat] = []
    for item in items:
        if item["id"] not in existing_ids:
            BASE_SHOP_ITEMS[cat].append(item)

# ═══════════════════════════════════════
# ФОНОВЫЕ NPC-ДЕЙСТВИЯ
# ═══════════════════════════════════════

NPC_BACKGROUND_ACTIONS = [
    "Группа белтеров горячо спорит у входа в доки о забастовке.",
    "Корпоративный курьер в бронекостюме бежит мимо, прижимая кейс к груди.",
    "Патрульный дрон завис над толпой, сканируя лица красным лазером.",
    "Двое в форме SENTINEL о чём-то шепчутся, бросая взгляды по сторонам.",
    "Уличный торговец раскладывает на тряпке подозрительные импланты.",
    "Бездомный мужчина с кибернетической ногой просит кредиты на «ремонт».",
    "Девушка с фиолетовыми глазами (импланты?) читает что-то на голо-планшете.",
    "Из подворотни доносятся звуки драки и крик — затем тишина.",
    "Рекламный дрон назойливо предлагает «лучшие импланты от Genesis Bioworks».",
    "Группа подростков с граффити-дронами расписывает стену логотипами Data Rebels.",
    "Корпоративный лимузин с тонированными стёклами медленно проезжает по улице.",
    "Охранник бара выкинул пьяного наёмника на тротуар. Тот ругается на трёх языках.",
    "Старик в инвалидном кресле-ховере торгует самодельной электроникой.",
    "Два дрона-курьера столкнулись в воздухе — обломки рассыпались по тротуару.",
    "Женщина в дорогом костюме вышла из такси и скрылась в переулке — странно для этого района.",
]


class WorldSimulator:
    """Симулятор живого мира. Генерирует фон, новости, экономику каждый ход."""

    def __init__(self):
        self.news_history: List[str] = []
        self.price_modifier: float = 1.0  # global price fluctuation
        self.instability: int = 30  # 0-100, higher = more events
        self.turn_count: int = 0

    def tick(self, game_time: Dict, location: Dict, tier: int) -> Dict:
        """Run one world simulation tick. Returns context for AI prompt."""
        self.turn_count += 1
        result = {
            "atmosphere": self._generate_atmosphere(game_time, location),
            "background_npcs": self._generate_background(location),
            "news": [],
            "rumors": [],
            "economic_event": None,
        }

        # News every 3-5 turns
        if self.turn_count % random.randint(3, 5) == 0 or self.turn_count == 1:
            news = self._generate_news(location, tier)
            self.news_history.append(news)
            result["news"].append(news)

        # Rumors occasionally
        if random.random() < 0.25:
            result["rumors"].append(self._generate_rumor(location))

        # Economic fluctuations
        if self.turn_count % 4 == 0:
            result["economic_event"] = self._economic_tick()

        # Instability drift
        self.instability = max(10, min(90, self.instability + random.randint(-5, 5)))

        return result

    def _generate_atmosphere(self, game_time: Dict, location: Dict) -> str:
        hour = game_time.get("hour", 12)
        if 5 <= hour < 11:
            tod = "morning"
        elif 11 <= hour < 17:
            tod = "afternoon"
        elif 17 <= hour < 22:
            tod = "evening"
        else:
            tod = "night"

        atm = ATMOSPHERE["time_of_day"][tod]
        planet = location.get("planet", "Земля")
        planet_vibe = ATMOSPHERE["planet_vibes"].get(planet, "")

        # Planet-specific weather
        weather_pool = ATMOSPHERE["weather"]["universal"][:]
        planet_weather = ATMOSPHERE["weather"].get(planet, [])
        weather_pool.extend(planet_weather)
        weather = random.choice(weather_pool)

        return (
            f"ВРЕМЯ СУТОК: {tod}. {atm['light']}. {atm['sounds']}. "
            f"{atm['activity']}. Настроение: {atm['mood']}. "
            f"ПОГОДА: {weather} "
            f"ПЛАНЕТА: {planet_vibe}"
        )

    def _generate_background(self, location: Dict) -> str:
        count = random.randint(2, 3)
        selected = random.sample(NPC_BACKGROUND_ACTIONS, min(count, len(NPC_BACKGROUND_ACTIONS)))
        return " | ".join(selected)

    def _generate_news(self, location: Dict, tier: int) -> str:
        # Higher tier = more political/military news
        if tier >= 2:
            category = random.choice(["political", "military", "economic", "tech"])
        elif tier >= 1:
            category = random.choice(["economic", "crime", "local", "tech", "military"])
        else:
            category = random.choice(["local", "crime", "economic", "local"])

        templates = NEWS_TEMPLATES.get(category, NEWS_TEMPLATES["local"])
        template = random.choice(templates)

        factions = ["OPA", "UEG", "МКР", "Free Mars Movement", "Data Rebels"]
        pmcs = ["SENTINEL Corp", "Iron Wolves", "Black Aegis", "Ronin Group", "Void Reapers"]
        corps = ["Helios Energy Corp", "LunarTech Industries", "Protogen", "Genesis Bioworks", "Kurosawa Heavy Industries"]
        districts = ["Индустриальный коридор", "Нижние уровни", "Торговые палубы", "Доки", "Жилой сектор"]
        items = ["военные импланты", "контрабандное оружие", "протомолекулярные чипы", "фальшивые ID"]
        npc_names = ["Виктор Моррис", "Кира Сантос", "Безликий", "Шакал", "доктор Вэнь"]

        return template.format(
            faction1=random.choice(factions),
            faction2=random.choice(factions),
            pmc=random.choice(pmcs),
            corp=random.choice(corps),
            district=random.choice(districts),
            percent=random.randint(8, 35),
            item=random.choice(items),
            npc=random.choice(npc_names),
            location=random.choice(districts),
        )

    def _generate_rumor(self, location: Dict) -> str:
        template = random.choice(RUMORS)
        pmcs = ["SENTINEL Corp", "Iron Wolves", "Black Aegis"]
        corps = ["Protogen", "Genesis Bioworks", "LunarTech"]
        factions = ["OPA", "Free Mars", "Data Rebels", "Black Lotus Triad"]
        npc_names = ["Кэнджи", "Безликий", "Мама Ро", "Шакал", "Доктор Вэнь"]
        districts = ["Нижние уровни", "Доки", "Заброшенный сектор"]
        items = ["Рефлекс-бусты", "Протомолекулярные чипы", "военные дроны"]

        return template.format(
            npc=random.choice(npc_names),
            pmc=random.choice(pmcs),
            corp=random.choice(corps),
            faction=random.choice(factions),
            district=random.choice(districts),
            location=random.choice(districts),
            item=random.choice(items),
        )

    def _economic_tick(self) -> str:
        change = random.uniform(-0.15, 0.15)
        self.price_modifier = max(0.7, min(1.5, self.price_modifier + change))
        if change > 0.05:
            return f"Цены растут (+{int(change*100)}%). Нестабильность рынка."
        elif change < -0.05:
            return f"Цены падают ({int(change*100)}%). Хороший момент для покупок."
        return None

    def get_shop_items(self, location: Dict, tier: int, event_price_mods: Dict = None) -> List[Dict]:
        """Get available items with dynamic prices based on location, economy, and world events."""
        planet = location.get("planet", "Земля")
        all_items = []

        for category, items in BASE_SHOP_ITEMS.items():
            # Event-based price modifier per category
            cat_event_mod = 1.0
            if event_price_mods:
                cat_event_mod = event_price_mods.get(category, event_price_mods.get("all", 1.0))

            for item in items:
                # Price modifiers by planet
                planet_mod = {"Земля": 1.0, "Марс": 1.1, "Пояс астероидов": 0.85, "Ганимед": 1.2}.get(planet, 1.0)
                # Black market discount for illegal items
                is_illegal = "наркотик" in item["name"].lower() or item["rarity"] == "rare"

                final_price = int(item["base_price"] * planet_mod * self.price_modifier * cat_event_mod)

                # Filter by rarity — rare items need higher tier
                if item["rarity"] == "rare" and tier < 1:
                    continue

                all_items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "category": category,
                    "price": final_price,
                    "stats": item["stats"],
                    "rarity": item["rarity"],
                })

        return all_items

    def to_dict(self) -> Dict:
        return {
            "news_history": self.news_history[-10:],
            "price_modifier": self.price_modifier,
            "instability": self.instability,
            "turn_count": self.turn_count,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WorldSimulator":
        ws = cls()
        ws.news_history = data.get("news_history", [])
        ws.price_modifier = data.get("price_modifier", 1.0)
        ws.instability = data.get("instability", 30)
        ws.turn_count = data.get("turn_count", 0)
        return ws
