"""
World Simulator — живой мир NEXUS RPG.
Генерирует фоновые события, новости, экономику, атмосферу.
Запускается каждый ход и подаёт контекст AI-мастеру.
"""
import random
import re
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

# Backlog#4 (Вариант III): региональная карта легальности.
# Глобальная метка из каталога = база; планета модифицирует её.
# Планета не в карте → без изменений (Земля/Луна сознательно отсутствуют).
REGIONAL_LEGALITY_MAP = {
    "Пояс астероидов": {  # лорно: там всем всё равно
        "illegal": "restricted",
        "restricted": "legal",
    },
    "Марс": {              # военный контроль: жёстче
        "restricted": "illegal",
    },
    "Ганимед": {           # свободный порт
        "restricted": "legal",
    },
}


def local_legality(base_legality: str, planet: str) -> str:
    """Backlog#4 (III): местный статус предмета на планете.

    Чистая функция, карта — данные (константа выше). Неизвестная планета
    или отсутствие модификатора → глобальная метка.
    """
    mods = REGIONAL_LEGALITY_MAP.get(planet or "", {})
    return mods.get(base_legality or "legal", base_legality or "legal")


# Add craft materials to shop
# Фаза 24c B5: legality материалов (детонаторы/взрывчатка — restricted, остальное legal)
BASE_SHOP_ITEMS["craft_materials"] = [
    {"id": f"M_{i}", "name": m["name"], "base_price": m["price"],
     "stats": "Компонент для крафта", "rarity": m["rarity"],
     "legality": ("restricted" if re.search(r"детонатор|взрывчат|термит|плазменн", m["name"], re.I)
                  else "legal")}
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

# backlog#5: выделенный шаблон для форс-упоминания фракции игрока (rep>=40).
# Базовые 48 шаблонов почти не содержат {faction1}/{corp}, поэтому при форсе
# используется этот — упоминание гарантированно попадает в текст.
NEWS_NOTABLE_TEMPLATE = (
    "«{faction1}» снова в заголовках: источники связывают недавние события с её "
    "растущим влиянием. Аналитики расходятся во мнениях, но все согласны в одном — "
    "за этой фракцией теперь следит вся система."
)


class WorldSimulator:
    """Симулятор живого мира. Генерирует фон, новости, экономику каждый ход."""

    def __init__(self):
        self.news_history: List[str] = []
        self.price_modifier: float = 1.0  # global price fluctuation
        self.instability: int = 30  # 0-100, higher = more events
        self.turn_count: int = 0
        self.last_notable_turn: int = -10  # backlog#5: кулдаун форс-упоминаний
        self._atmosphere_cache: str = ""  # Phase 31 H7: атмосфера обновляется раз в ~10 тиков
        self._atmosphere_turn: int = -999  # тик последней генерации атмосферы

    def tick(self, game_time: Dict, location: Dict, tier: int,
             notable_factions: Optional[List[str]] = None,
             character: Optional[Dict] = None) -> Dict:
        """Run one world simulation tick. Returns context for AI prompt.

        backlog#5: notable_factions — фракции игрока с rep>=40; новость может
        принудительно упомянуть одну из них (шанс 33%, кулдаун 10 ходов)."""
        self.turn_count += 1
        # Phase 31 H7: атмосфера — периодическая фоновая деталь, а не ежеходовая.
        # Регенерируем раз в 10 тиков (или при смене локации, кэш пуст); между
        # обновлениями возвращаем сохранённый текст.
        location_key = f"{location.get('planet','')}|{location.get('city','')}|{location.get('district','')}"
        if not hasattr(self, "_atmosphere_loc_key"):
            self._atmosphere_loc_key = location_key
        location_changed = location_key != self._atmosphere_loc_key
        if (self.turn_count - self._atmosphere_turn) >= 10 or location_changed or not self._atmosphere_cache:
            self._atmosphere_cache = self._generate_atmosphere(game_time, location)
            self._atmosphere_turn = self.turn_count
            self._atmosphere_loc_key = location_key
        result = {
            "atmosphere": self._atmosphere_cache,
            "background_npcs": self._generate_background(location),
            "news": [],
            "rumors": [],
            "economic_event": None,
        }

        # News every 3-5 turns
        if self.turn_count % random.randint(3, 5) == 0 or self.turn_count == 1:
            news, news_category, mentioned = self._generate_news(
                location, tier, notable_factions=notable_factions)
            self.news_history.append({"text": news, "category": news_category})
            result["news"].append(news)
            if mentioned:
                # backlog#5: факт упоминания — движок начислит FAME_PER_NEWS_MENTION
                result["news_mention"] = mentioned

            # А4: новость получает минимальное механическое влияние — ценовой шок
            # категории товаров на 24 игровых часа (через WorldEffectsManager).
            shock = self.NEWS_PRICE_SHOCKS.get(news_category)
            if shock and getattr(self, "world_effects_ref", None):
                self.world_effects_ref.apply_event_effects(
                    {"id": f"news_shock_{self.turn_count}", "effects": shock["effect"],
                     "duration_days": 1}, self._current_hours_estimate())
                result["news_effect"] = shock["effect"]

        # Rumors occasionally
        if random.random() < 0.25:
            result["rumors"].append(self._generate_rumor(location, character))

        # Economic fluctuations
        if self.turn_count % 4 == 0:
            result["economic_event"] = self._economic_tick()

        # Instability drift
        self.instability = max(10, min(90, self.instability + random.randint(-5, 5)))

        return result

    # А4: карта «категория новости → ценовой эффект» (механическое влияние новостей)
    NEWS_PRICE_SHOCKS = {
        "crime":     {"effect": {"black_market_surge": 8}},
        "political": {"effect": {"trade_disruption": 6}},
        "military":  {"effect": {"military_alert_prices": 8}},
        "economic":  {"effect": {"market_boom": -5}},
    }

    def _current_hours_estimate(self) -> int:
        """А4: грубая оценка игровых часов для длительности новостного шока."""
        t = getattr(self, "_last_game_time", None) or {}
        try:
            return (int(t.get("day", 1)) * 24 + int(t.get("hour", 12)))
        except Exception:
            return 0

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

        # Phase 28 F4: время суток — по-русски, сводка — литературная, без канцелярита
        tod_ru = {"morning": "Утро", "afternoon": "День",
                  "evening": "Вечер", "night": "Ночь"}.get(tod, tod)
        return (
            f"{tod_ru}. {atm['light']}. {atm['sounds']}. "
            f"{atm['activity']}. {atm['mood']}. "
            f"{weather}. "
            f"{planet_vibe}"
        )

    def _generate_background(self, location: Dict) -> str:
        count = random.randint(2, 3)
        selected = random.sample(NPC_BACKGROUND_ACTIONS, min(count, len(NPC_BACKGROUND_ACTIONS)))
        return " | ".join(selected)

    def _generate_news(self, location: Dict, tier: int,
                       notable_factions: Optional[List[str]] = None):
        # Higher tier = more political/military news
        if tier >= 2:
            category = random.choice(["political", "military", "economic", "tech"])
        elif tier >= 1:
            category = random.choice(["economic", "crime", "local", "tech", "military"])
        else:
            category = random.choice(["local", "crime", "economic", "local"])

        templates = NEWS_TEMPLATES.get(category, NEWS_TEMPLATES["local"])
        template = random.choice(templates)

        # backlog#5: форс-упоминание фракции игрока (rep>=40): шанс 33%,
        # жёсткий кулдаун 10 ходов (шанс НЕ действует внутри кулдауна).
        # Только 2/48 базовых шаблонов имеют {faction1}/{corp}, поэтому при
        # форсе используется выделенный шаблон (категория local).
        forced_mention = None
        cooldown_over = self.turn_count - self.last_notable_turn >= 10
        if notable_factions and cooldown_over and random.random() < 0.33:
            forced_mention = random.choice(notable_factions)
            template = NEWS_NOTABLE_TEMPLATE
            category = "local"
            factions = [forced_mention]  # {faction1} выделенного шаблона — фракция игрока
            self.last_notable_turn = self.turn_count

        # Б4: единый каталог фракций (Фаза 9/12) вместо хардкода; lazy-загрузка + кэш
        if not getattr(self, "_faction_name_cache", None):
            try:
                import json as _json, os as _os
                _fm_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                         "..", "game_data", "FACTIONS_MASTER.json")
                _fm = _json.load(open(_fm_path, encoding="utf-8"))
                by_t = {}
                for f in _fm["factions"]:
                    if "canonical_duplicate_of" not in f:
                        by_t.setdefault(f.get("type"), []).append(f["name"])
                self._faction_name_cache = {
                    "factions": by_t.get("Clan", [])[:10] or ["OPA"],
                    "pmcs": by_t.get("PMC", [])[:10] or ["SENTINEL Corp"],
                    "corps": (by_t.get("Megacorp", []) + by_t.get("Conglomerate", []))[:10] or ["Helios Energy Corp"],
                }
            except Exception:
                self._faction_name_cache = {
                    "factions": ["OPA", "UEG", "МКР"],
                    "pmcs": ["SENTINEL Corp"],
                    "corps": ["Helios Energy Corp"],
                }
        factions = self._faction_name_cache["factions"]
        pmcs = self._faction_name_cache["pmcs"]
        corps = self._faction_name_cache["corps"]
        districts = ["Индустриальный коридор", "Нижние уровни", "Торговые палубы", "Доки", "Жилой сектор"]
        items = ["военные импланты", "контрабандное оружие", "протомолекулярные чипы", "фальшивые ID"]
        npc_names = ["Виктор Моррис", "Кира Сантос", "Безликий", "Шакал", "доктор Вэнь"]

        # backlog#5: при форсе {faction1} выделенного шаблона — фракция игрока
        if forced_mention:
            factions = [forced_mention]

        text = template.format(
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
        # backlog#5: упоминание = форс ИЛИ случайное совпадение имени фракции игрока
        mentioned = None
        if forced_mention and forced_mention in text:
            mentioned = forced_mention
        elif notable_factions:
            mentioned = next((f for f in notable_factions if f in text), None)
        return text, category, mentioned

    # Phase 28 G5: контекстные пулы слухов — что слышит персонаж данной профессии/локации
    CONTEXT_RUMORS = {
        "research": [
            "В лабораториях шепчутся: {corp} вот-вот получит грант на изучение протомолекулы.",
            "Кто-то слил данные исследования с {location} — охота на информатора уже началась.",
            "Говорят, партия био-образцов для {corp} «потерялась» при транспортировке через {district}.",
            "Коллеги болтают: рецензия на статью {npc} сорвалась из-за давления инвесторов.",
        ],
        "medic": [
            "В мед-отсеках говорят о вспышке нейро-эрозии среди носителей имплантов 3-го поколения.",
            "Кто-то продал партию контрабандных стимуляторов через {district} — пострадали пациенты.",
            "{corp} вербует хирургов для закрытого проекта. Условия засекречены.",
        ],
        "criminal": [
            "{npc} объявил награду за голову конкурента из {faction}.",
            "Через {district} идёт партия {item} — ищут барыгу с плечом.",
            "Black Lotus Triad начала собирать долги в доках. Кровь уже пролилась.",
        ],
        "military": [
            "{pmc} перебрасывает инструкторов к {location}. Готовится что-то крупное.",
            "Военные контракты {faction} продлены ещё на два квартала.",
            "На полигоне видели испытания новых {item}.",
        ],
    }
    CONTEXT_MARKERS = {
        "research": ("SCIENTIST", "RESEARCH", "QUANTUM", "TECH", "SCIENCE", "GANYMEDE", "LAB"),
        "medic": ("MEDIC", "TRAUMA", "GENE", "PHARMA", "XENO", "SURGEON"),
        "criminal": ("SLUMS", "CRIMINAL", "SMUGGL", "THIEF", "STREET", "BLACK", "SALVAGE", "CERES_MINER"),
        "military": ("SOLDIER", "MARINE", "MILITARY", "CQB", "SNIPER", "ORDNANCE"),
    }

    def _generate_rumor(self, location: Dict, character: Dict = None) -> str:
        # Phase 28 G5: слух привязан к профессии персонажа; фоллбэк — общий пул
        template = None
        if character:
            spec = str(character.get("specialization", "")).upper()
            origin = str(character.get("origin", "")).upper()
            hay = f"{spec}|{origin}"
            for ctx_key, markers in self.CONTEXT_MARKERS.items():
                if any(m in hay for m in markers):
                    ctx_pool = self.CONTEXT_RUMORS[ctx_key]
                    if random.random() < 0.6:  # 60% контекстный слух, 40% общий
                        template = random.choice(ctx_pool)
                    break
        if template is None:
            template = random.choice(RUMORS)

        pmcs = ["SENTINEL Corp", "Iron Wolves", "Black Aegis"]
        corps = ["Protogen", "Genesis Bioworks", "LunarTech"]
        factions = ["OPA", "Free Mars", "Data Rebels", "Black Lotus Triad"]
        npc_names = ["Кэнджи", "Безликий", "Мама Ро", "Шакал", "Доктор Вэнь"]
        # G5: районы слухов — приоритетно из текущей локации
        cur_district = location.get("district", "")
        districts = [cur_district] if cur_district else ["Нижние уровни", "Доки", "Заброшенный сектор"]
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

    def get_shop_items(self, location: Dict, tier: int, event_price_mods: Dict = None,
                           include_black_market: bool = False, character: Dict = None) -> List[Dict]:
        """Get available items with dynamic prices based on location, economy, and world events.
        
        Args:
            include_black_market: if True, include illegal items at ×1.5 markup (black market)
            character: player character dict (needed for heat/criminal rep checks)
        """
        planet = location.get("planet", "Земля")
        all_items = []
        black_market_risk = False

        for category, items in BASE_SHOP_ITEMS.items():
            # Event-based price modifier per category
            cat_event_mod = 1.0
            if event_price_mods:
                cat_event_mod = event_price_mods.get(category, event_price_mods.get("all", 1.0))

            for item in items:
                # Price modifiers by planet
                planet_mod = {"Земля": 1.0, "Марс": 1.1, "Пояс астероидов": 0.85, "Ганимед": 1.2}.get(planet, 1.0)
                final_price = int(item["base_price"] * planet_mod * self.price_modifier * cat_event_mod)

                # Filter by rarity — rare items need higher tier
                if item["rarity"] == "rare" and tier < 1:
                    continue

                legality = item.get("legality", "legal")
                local_leg = local_legality(legality, planet)

                # ── Black Market logic (Вариант I: Комбо А+В) ──
                if include_black_market and character is not None:
                    # Check rep ≥ 25 with any criminal faction (canonical names)
                    from src.systems.game_systems import FACTION_CATEGORIES
                    criminal_factions = FACTION_CATEGORIES.get("криминал", [])
                    player_rep = character.get("faction_reputation", {})
                    has_criminal_rep = any(
                        player_rep.get(f, 0) >= 25 for f in criminal_factions
                    )

                    if not has_criminal_rep:
                        # Вариант В: always accessible with risk
                        # No access check — player can always use black market,
                        # but without criminal rep, every purchase adds extra heat
                        black_market_risk = True
                    else:
                        black_market_risk = False

                    # Apply markup based on legality
                    if legality == "illegal" or local_leg == "illegal":
                        final_price = int(final_price * 1.5)
                    elif legality == "restricted" or local_leg == "restricted":
                        final_price = int(final_price * 1.25)
                elif include_black_market and character is None:
                    # Black market requested but no character — return empty
                    continue
                elif legality == "illegal" or local_leg == "illegal":
                    # Regular shop: skip illegal items (handled by black market)
                    continue

                all_items.append({
                    "id": item["id"],
                    "name": item["name"],
                    "category": category,
                    "price": final_price,
                    "stats": item["stats"],
                    "rarity": item["rarity"],
                    "legality": legality,
                    "local_legality": local_leg,
                    "black_market_risk": black_market_risk,
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
