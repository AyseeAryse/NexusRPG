"""
Galaxy Map — navigation system for planets, cities, districts, and establishments.
Based on WORLDBUILD.json data, expanded with travel routes and local flavor.
"""
from typing import Dict, List, Optional

# ==========================================
# PLANET ALIAS (Phase 3 P0 fix v2)
# ==========================================
# Каноничные русские имена планет в galaxy.py (ключи GALAXY_MAP).
# Алиасы — все варианты написания (EN из TRADE_ROUTES_MASTER.json,
# старые/нестандартные имена, разные регистры), которые должны
# резолвиться в каноничное имя.
#
# Применяется в:
#   - _normalize_route_endpoint() — нормализация значений из route endpoints
#   - get_route() / get_routes_from() — нормализация имени планеты при поиске
#   - load_routes_from_kb() — нормализация start_point/end_point при загрузке
#
# NB: ключи — UPPERCASE формы (как в TRADE_ROUTES_MASTER.json), регистр
# в lookup игнорируется (см. _normalize_planet_alias).
PLANET_ALIAS: Dict[str, str] = {
    # Английские коды → русские имена
    "EARTH": "Земля", "MARS": "Марс", "LUNA": "Луна",
    "GANYMEDE": "Ганимед", "CERES": "Церера", "VENUS": "Венера",
    "SATURN": "Сатурн", "JUPITER": "Юпитер", "BELT": "Пояс астероидов",
    # Синонимы/варианты написания (без учёта регистра)
    "MOON": "Луна", "MOON_EARTH": "Луна",
    "ASTEROID_BELT": "Пояс астероидов", "BELT_ASTEROIDS": "Пояс астероидов",
}

# Phase 3 loop (шаг 1): ROUTE_KEY_ALIAS — нормализация destination-ключей
# маршрутов в hardcoded GALAXY_MAP. "Церера" в routes указывает на станцию
# Церера-Прайм в Поясе астероидов, но географически это не отдельная планета,
# а регион Пояса. Для симметрии двусторонних маршрутов normalизуем эти ключи.
# Применяется ТОЛЬКО в контексте маршрутов, чтобы не сломать другие места,
# где "Церера" используется как имя станции/персонажа.
ROUTE_KEY_ALIAS: Dict[str, str] = {
    "Церера": "Пояс астероидов",
    "Ceres": "Пояс астероидов",
    "CERES": "Пояс астероидов",
}


def _normalize_planet_alias(value: str) -> str:
    """Нормализует имя планеты через PLANET_ALIAS (case-insensitive).

    Если value есть в PLANET_ALIAS (или его uppercase форма есть) — возвращает
    каноничное русское имя. Иначе возвращает value как есть (например,
    "Земля" → "Земля").
    """
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    if not stripped:
        return ""
    # Прямой lookup (с учётом регистра)
    if stripped in PLANET_ALIAS:
        return PLANET_ALIAS[stripped]
    # Case-insensitive lookup
    upper = stripped.upper()
    if upper in PLANET_ALIAS:
        return PLANET_ALIAS[upper]
    return stripped


def _normalize_route_key(value: str) -> str:
    """Нормализует destination-ключ маршрута через ROUTE_KEY_ALIAS.

    Применяется ТОЛЬКО в контексте маршрутов (destination-ключи в
    GALAXY_MAP[routes], не имена планет/станций в общем смысле).

    Например: hardcoded "Церера" в routes — это историческая ошибка
    данных (станция Церера-Прайм географически в Поясе астероидов),
    поэтому для симметрии маршрутов нормализуем в каноничный ключ планеты.
    """
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped in ROUTE_KEY_ALIAS:
        return ROUTE_KEY_ALIAS[stripped]
    upper = stripped.upper()
    if upper in ROUTE_KEY_ALIAS:
        return ROUTE_KEY_ALIAS[upper]
    return stripped

# ==========================================
# COMPLETE GALAXY MAP
# ==========================================
GALAXY_MAP = {
    "Земля": {
        "type": "planet",
        "gravity": 1.0,
        "population": "12 млрд",
        "governance": "ООН Земли",
        "vibe": "Перенаселённая, задыхающаяся. Неон и бетон. Корпоративные небоскрёбы над трущобами.",
        "cities": {
            "Нью-Токио": {
                "population": "500 млн",
                "description": "Крупнейший мегаполис Земли. Неоновые джунгли, корпоративные башни, подземные трущобы.",
                "districts": {
                    "Правительственное ядро": {
                        "type": "Political",
                        "security": "Максимальный",
                        "income": "Высокий",
                        "factions": ["ООН Земли"],
                        "description": "Башни власти на бывших линиях метро. Дипломаты, бюрократы, протестующие у входов.",
                        "establishments": [
                            {"name": "Зал Генеральной Ассамблеи ООН", "type": "government", "services": ["дипломатия", "голосования"]},
                            {"name": "Квартал «Новая Шанхай»", "type": "residential", "services": ["корпоративные офисы", "элитное жильё"]},
                            {"name": "Пресс-центр UNN", "type": "media", "services": ["новости", "пропаганда", "контакты журналистов"]},
                            {"name": "Кафе «Капитолий»", "type": "restaurant", "services": ["встречи", "подслушивание", "деловые обеды"]},
                            {"name": "Бюро безопасности ООН", "type": "security", "services": ["допуск", "расследования", "аресты"]},
                        ],
                    },
                    "Индустриальный коридор": {
                        "type": "Industrial",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["Корпорации", "OPA"],
                        "description": "Фабрики дронов, доки, грузовые терминалы. Запах масла и озона. Рабочие кварталы.",
                        "establishments": [
                            {"name": "Бар «Чёрная Луна»", "type": "bar", "services": ["выпивка", "слухи", "контакты"]},
                            {"name": "Доки Сектора 7", "type": "logistics", "services": ["грузоперевозки", "контрабанда"]},
                            {"name": "Мастерская Танаки", "type": "workshop", "services": ["ремонт", "модификации оружия"]},
                            {"name": "Клиника доктора Чена", "type": "medical", "services": ["лечение", "импланты", "нелегальные операции"]},
                            {"name": "Рынок «Неон-базар»", "type": "market", "services": ["оружие", "электроника", "нелегальный товар"]},
                        ],
                    },
                    "Корпоративный квартал": {
                        "type": "Corporate",
                        "security": "Высокий",
                        "income": "Очень высокий",
                        "factions": ["LunarTech Industries", "Helios Energy", "Protogen"],
                        "description": "Стеклянные небоскрёбы, чистый воздух за фильтрами, частная охрана. Другой мир над трущобами.",
                        "establishments": [
                            {"name": "Башня LunarTech", "type": "corporate", "services": ["офисы", "R&D", "корпоративная безопасность"]},
                            {"name": "Купол WallStreet", "type": "financial", "services": ["биржа", "криптовалюты", "банки"]},
                            {"name": "Ресторан «Олимп»", "type": "restaurant", "services": ["элитная кухня", "деловые встречи"]},
                            {"name": "Казино «Джекпот»", "type": "entertainment", "services": ["азартные игры", "VIP-залы", "информация"]},
                        ],
                    },
                    "Нижний город (Трущобы)": {
                        "type": "Slums",
                        "security": "Минимальный",
                        "income": "Низкий",
                        "factions": ["Black Lotus Triad", "Data Rebels", "OPA"],
                        "description": "Под землёй. Тусклый свет, переработанный воздух, граффити OPA. Закон — только сила.",
                        "establishments": [
                            {"name": "Притон «Красный Фонарь»", "type": "bar", "services": ["нелегальное", "наркотики", "информация"]},
                            {"name": "Чёрный рынок Ванга", "type": "black_market", "services": ["оружие", "импланты", "документы"]},
                            {"name": "Штаб Data Rebels", "type": "hideout", "services": ["хакинг", "безопасная связь"]},
                            {"name": "Подпольная арена «Яма»", "type": "arena", "services": ["бои", "ставки", "наёмники"]},
                        ],
                    },
                },
            },
            "Нью-Йорк": {
                "population": "350 млн",
                "description": "Политическая столица Земли. Штаб-квартира ООН, дипломатический центр.",
                "districts": {
                    "Дипломатический квартал": {
                        "type": "Political",
                        "security": "Максимальный",
                        "income": "Высокий",
                        "factions": ["ООН Земли"],
                        "description": "Посольства, резиденции, охрана на каждом углу.",
                        "establishments": [
                            {"name": "Штаб ООН", "type": "government", "services": ["дипломатия", "разведка"]},
                            {"name": "Посольский ряд", "type": "government", "services": ["визы", "контакты", "информация"]},
                            {"name": "Ресторан «Дипломат»", "type": "restaurant", "services": ["деловые встречи", "переговоры"]},
                            {"name": "Архив МИДа", "type": "archive", "services": ["документы", "досье", "история"]},
                        ],
                    },
                    "Старый Манхэттен": {
                        "type": "Residential",
                        "security": "Средний",
                        "income": "Низкий",
                        "factions": ["ООН Земли", "OPA"],
                        "description": "Заброшенные небоскрёбы превращены в жилые блоки. Мигранты, артисты, хакеры.",
                        "establishments": [
                            {"name": "Сквот «Вавилонская башня»", "type": "residential", "services": ["ночлег", "слухи", "контрабанда"]},
                            {"name": "Подпольный клуб «NEON»", "type": "entertainment", "services": ["музыка", "наркотики", "контакты"]},
                            {"name": "Мастерская «FixIt»", "type": "workshop", "services": ["ремонт", "модификации", "хакинг"]},
                            {"name": "Клиника «Надежда»", "type": "medical", "services": ["дешёвое лечение", "контрабандные лекарства"]},
                        ],
                    },
                    "Порт Бруклин": {
                        "type": "Logistics",
                        "security": "Низкий",
                        "income": "Средний",
                        "factions": ["Корпорации", "Black Lotus Triad"],
                        "description": "Грузовые доки, контейнерные лабиринты. Половина грузов — контрабанда.",
                        "establishments": [
                            {"name": "Доки Атлантик", "type": "logistics", "services": ["грузоперевозки", "контрабанда", "перелёты"]},
                            {"name": "Склад 17", "type": "warehouse", "services": ["хранение", "чёрный рынок"]},
                            {"name": "Забегаловка «Якорь»", "type": "bar", "services": ["выпивка", "наёмники", "работа"]},
                        ],
                    },
                },
            },
        },
        "routes": {
            "Марс": {"time": "72-180 часов", "delta_v": "5.5 км/с", "risk": "low"},
            "Луна": {"time": "3 часа", "delta_v": "3.2 км/с", "risk": "minimal"},
            "Церера": {"time": "200 часов", "delta_v": "9.5 км/с", "risk": "medium"},
            "Ганимед": {"time": "180 часов", "delta_v": "9.0 км/с", "risk": "medium"},
        },
    },

    "Марс": {
        "type": "planet",
        "gravity": 0.38,
        "population": "800 млн",
        "governance": "Марсианская Республика",
        "vibe": "Красная пыль, купола, индустриальная мощь. Военная дисциплина и стремление к независимости.",
        "cities": {
            "Новый Бостон": {
                "population": "200 млн",
                "description": "Столица Марса. Под куполами — город контрастов: военные базы и научные центры.",
                "districts": {
                    "Терраформные проекты": {
                        "type": "Scientific",
                        "security": "Высокий",
                        "income": "Высокий",
                        "factions": ["Марсианская Республика"],
                        "description": "Биокупола и атмосферные процессоры. Учёные и инженеры терраформирования.",
                        "establishments": [
                            {"name": "Био-купол «Ренессанс»", "type": "research", "services": ["генетика", "экосистемы"]},
                            {"name": "Ферма RedSand", "type": "agricultural", "services": ["еда", "семена"]},
                            {"name": "Лаборатория атмосферных процессоров", "type": "research", "services": ["терраформирование", "климат-контроль"]},
                            {"name": "Общежитие учёных «Хаб»", "type": "residential", "services": ["ночлег", "контакты учёных", "слухи"]},
                        ],
                    },
                    "Окружное кольцо": {
                        "type": "Logistics",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["Mars Fleet", "Корпорации"],
                        "description": "Торговая станция и порт для грузовых судов. Базары, доки, наёмники.",
                        "establishments": [
                            {"name": "МарсГейт Терминал", "type": "logistics", "services": ["грузоперевозки", "таможня"]},
                            {"name": "Бар «Красная пыль»", "type": "bar", "services": ["выпивка", "наёмники", "слухи"]},
                            {"name": "Оружейная «Стальной кулак»", "type": "shop", "services": ["оружие", "броня", "боеприпасы"]},
                            {"name": "Казарма Iron Wolves", "type": "military", "services": ["контракты ЧВК", "тренировки"]},
                        ],
                    },
                    "Военный сектор": {
                        "type": "Military",
                        "security": "Максимальный",
                        "income": "Высокий",
                        "factions": ["Mars Fleet", "SENTINEL PMC"],
                        "description": "Базы Mars Fleet, верфи, академия. Строгий контроль доступа.",
                        "establishments": [
                            {"name": "Академия Mars Fleet", "type": "military", "services": ["обучение", "вербовка"]},
                            {"name": "Верфь «Арес»", "type": "shipyard", "services": ["корабли", "Frame Units"]},
                            {"name": "Оружейная лаборатория SENTINEL", "type": "research", "services": ["прототипы оружия", "боевые дроны"]},
                            {"name": "Госпиталь «Олимп»", "type": "medical", "services": ["военная медицина", "протезирование", "ПТСР"]},
                            {"name": "Кантина «Разводящий»", "type": "bar", "services": ["выпивка", "военные контракты", "слухи с фронта"]},
                        ],
                    },
                },
            },
        },
        "routes": {
            "Земля": {"time": "72-180 часов", "delta_v": "5.5 км/с", "risk": "low"},
            "Церера": {"time": "120 часов", "delta_v": "6.8 км/с", "risk": "medium"},
            "Ганимед": {"time": "180 часов", "delta_v": "8.0 км/с", "risk": "medium"},
        },
    },

    "Луна": {
        "type": "moon",
        "gravity": 0.165,
        "population": "150 млн",
        "governance": "ООН Земли / Марсианская Республика (совместный контроль)",
        "vibe": "Серая пустыня снаружи, хайтек-лаборатории внутри. Шпионы и учёные.",
        "cities": {
            "Армстронг-Сити": {
                "population": "60 млн",
                "description": "Главный город Луны. Секретные лаборатории, корпоративные центры.",
                "districts": {
                    "Лаборатории Alpha": {
                        "type": "Research",
                        "security": "Максимальный",
                        "income": "Высокий",
                        "factions": ["Protogen"],
                        "description": "Секретные исследовательские комплексы. Эксперименты с протомолекулой.",
                        "establishments": [
                            {"name": "Protogen Alpha Labs", "type": "research", "services": ["протомолекула", "AI"]},
                            {"name": "Серверная ферма «Нексус»", "type": "datacenter", "services": ["хакинг", "данные", "ИИ-эксперименты"]},
                            {"name": "Карантинная зона B-7", "type": "restricted", "services": ["биоопасность", "секретные образцы"]},
                            {"name": "Кафетерий учёных", "type": "restaurant", "services": ["еда", "сплетни", "утечки информации"]},
                        ],
                    },
                    "Ново-Пекин": {
                        "type": "Commercial",
                        "security": "Высокий",
                        "income": "Очень высокий",
                        "factions": ["Nexus Pharmaceuticals"],
                        "description": "Коммерческий центр. Nexus Pharma, банки, элитные магазины.",
                        "establishments": [
                            {"name": "Nexus Pharma Tower", "type": "corporate", "services": ["лекарства", "нейростабилизация"]},
                            {"name": "Торговый центр «Лунный свет»", "type": "market", "services": ["товары", "электроника"]},
                            {"name": "Банк «Лунный кредит»", "type": "financial", "services": ["кредиты", "обмен валют", "сейфы"]},
                            {"name": "Чайный дом «Тишина»", "type": "restaurant", "services": ["переговоры", "контакты", "отдых"]},
                        ],
                    },
                    "Лунные туннели": {
                        "type": "Underground",
                        "security": "Низкий",
                        "income": "Низкий",
                        "factions": ["OPA", "Data Rebels"],
                        "description": "Заброшенные шахтные тоннели, превращённые в поселение для беженцев и хакеров. Слабая гравитация, вечный мрак.",
                        "establishments": [
                            {"name": "Серверный бункер «Призрак»", "type": "hideout", "services": ["хакинг", "зашифрованная связь", "укрытие"]},
                            {"name": "Нелегальная клиника доктора Ву", "type": "medical", "services": ["нелегальные импланты", "экстракция чипов"]},
                            {"name": "Шахтёрская таверна «Кратер»", "type": "bar", "services": ["выпивка", "чёрный рынок", "контакты подполья"]},
                            {"name": "Схрон контрабандистов", "type": "warehouse", "services": ["хранение", "контрабанда", "фальшивые документы"]},
                        ],
                    },
                },
            },
        },
        "routes": {
            "Земля": {"time": "3 часа", "delta_v": "3.2 км/с", "risk": "minimal"},
            "Марс": {"time": "96 часов", "delta_v": "4.0 км/с", "risk": "low"},
        },
    },

    "Пояс астероидов": {
        "type": "asteroid_belt",
        "gravity": 0.028,
        "population": "100 млн",
        "governance": "OPA (Outer Planets Alliance)",
        "vibe": "Тесные станции, переработанный воздух, шахтёрская культура. Свобода и нищета.",
        "cities": {
            "Станция Церера-Прайм": {
                "population": "40 млн",
                "description": "Крупнейшая станция Пояса. Тоннели, доки, нелегальные рынки.",
                "districts": {
                    "Шахтёрский квартал": {
                        "type": "Residential",
                        "security": "Низкий",
                        "income": "Низкий",
                        "factions": ["OPA"],
                        "description": "Кольцеобразные тоннели. Тесно, сыро, вечный полумрак. Люди закалённые.",
                        "establishments": [
                            {"name": "Бар «Забой»", "type": "bar", "services": ["нелегальные бои", "чёрный рынок оружия", "выпивка"]},
                            {"name": "Контора OPA", "type": "political", "services": ["работа", "защита прав", "вербовка"]},
                            {"name": "Лавка старьёвщика Пита", "type": "shop", "services": ["б/у снаряжение", "запчасти", "электроника"]},
                        ],
                    },
                    "Производственная зона": {
                        "type": "Industrial",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["Vesta Industrial Union"],
                        "description": "Фабрики по переработке руды и топлива. Круглосуточная работа.",
                        "establishments": [
                            {"name": "Завод Vesta Industrial", "type": "factory", "services": ["работа", "компоненты"]},
                            {"name": "Доки и причалы", "type": "logistics", "services": ["грузоперевозки", "ремонт кораблей"]},
                            {"name": "Профсоюзный зал VIU", "type": "political", "services": ["работа", "защита прав", "забастовки"]},
                            {"name": "Столовая «Третья смена»", "type": "restaurant", "services": ["дешёвая еда", "слухи рабочих"]},
                        ],
                    },
                    "Торговые палубы": {
                        "type": "Commercial",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["OPA", "Независимые торговцы"],
                        "description": "Рынки, меняльные лавки, рестораны. Многоязычный гомон, запах специй.",
                        "establishments": [
                            {"name": "Рынок «Вавилон»", "type": "market", "services": ["всё на свете", "валютный обмен"]},
                            {"name": "Чайхана «Звёздная пыль»", "type": "restaurant", "services": ["еда", "переговоры"]},
                            {"name": "Ломбард «Второй виток»", "type": "shop", "services": ["скупка", "б/у товары", "редкости"]},
                            {"name": "Информбюро Фрэнка", "type": "fixer", "services": ["контракты", "информация", "подделка документов"]},
                        ],
                    },
                    "Нижние уровни": {
                        "type": "Underworld",
                        "security": "Нулевой",
                        "income": "Криминальный",
                        "factions": ["Black Lotus Triad", "OPA"],
                        "description": "Дно станции. Отключённые камеры, самоуправление бандитов, нелегальные бои и лаборатории.",
                        "establishments": [
                            {"name": "Арена «Бездна»", "type": "arena", "services": ["бои насмерть", "ставки", "наёмники"]},
                            {"name": "Нарколаборатория «Звёздная пыль»", "type": "lab", "services": ["стимуляторы", "боевая химия"]},
                            {"name": "Притон «Тень»", "type": "hideout", "services": ["укрытие", "фальшивые документы", "скупка краденого"]},
                            {"name": "Чёрный док", "type": "logistics", "services": ["контрабанда", "угнанные корабли", "нелегальные грузы"]},
                        ],
                    },
                },
            },
        },
        "routes": {
            "Земля": {"time": "200 часов", "delta_v": "9.5 км/с", "risk": "medium"},
            "Марс": {"time": "120 часов", "delta_v": "6.8 км/с", "risk": "medium"},
            "Ганимед": {"time": "120 часов", "delta_v": "7.0 км/с", "risk": "high"},
        },
    },

    "Ганимед": {
        "type": "moon",
        "gravity": 0.146,
        "population": "200 млн",
        "governance": "ESA-Earth (де-юре), корпорации (де-факто)",
        "vibe": "Ледяной мир. Подземные лаборатории, гидропонные фермы. Наука и секреты.",
        "cities": {
            "Станция Юпитер-Прайм": {
                "population": "18 млн",
                "description": "Орбитальный торговый узел Ганимеда. Учёные, торговцы и контрабандисты био-образцов.",
                "districts": {
                    "Торговые палубы": {
                        "type": "Commercial",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["Независимые торговцы", "Genesis Bioworks"],
                        "description": "Палубы orbital-торговли: мед-отсеки, бары, перекупщики и склады био-образцов.",
                        "establishments": [
                            {"name": "Мед-отсек «БиоГеном»", "type": "medical", "services": ["генетическая терапия", "импланты", "лечение"]},
                            {"name": "Бар «Ледяной Шторм»", "type": "bar", "services": ["выпивка", "наёмники", "слухи"]},
                            {"name": "Терминал перекупщика", "type": "market", "services": ["скупка", "б/у товары", "нелегальный товар"]},
                            {"name": "Склад био-образцов", "type": "warehouse", "services": ["биоматериалы", "хранение", "контрабанда"]},
                            {"name": "Магазин «Ледяной компас-2»", "type": "shop", "services": ["снаряжение", "научное оборудование", "электроника"]},
                        ],
                    },
                },
            },
            "Технохаб": {
                "population": "50 млн",
                "description": "Научный центр человечества. Подземный город-лаборатория.",
                "districts": {
                    "Биоэтический центр": {
                        "type": "Corporate",
                        "security": "Высокий",
                        "income": "Высокий",
                        "factions": ["Genesis Bioworks"],
                        "description": "Лаборатории генетики и клиники. Этические протесты у входа.",
                        "establishments": [
                            {"name": "Genesis Bioworks HQ", "type": "corporate", "services": ["эксперименты", "импланты", "регенерация"]},
                            {"name": "Клиника «Второй шанс»", "type": "medical", "services": ["генетическая терапия", "протезирование"]},
                        ],
                    },
                    "Ганимедские фермы": {
                        "type": "Agricultural",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["ESA-Earth"],
                        "description": "Гигантские гидропонные комплексы. Кормят половину внешних планет.",
                        "establishments": [
                            {"name": "Гидропонная ферма «Эдем»", "type": "agricultural", "services": ["еда", "биоматериалы"]},
                            {"name": "Генетическая теплица №4", "type": "research", "services": ["экспериментальные культуры", "модифицированные семена"]},
                            {"name": "Перевалочный склад", "type": "logistics", "services": ["хранение продовольствия", "грузоперевозки"]},
                        ],
                    },
                    "Торговый квартал": {
                        "type": "Commercial",
                        "security": "Средний",
                        "income": "Средний",
                        "factions": ["Независимые"],
                        "description": "Маленький, но оживлённый. Учёные расслабляются после смен.",
                        "establishments": [
                            {"name": "Бар «Абсолютный ноль»", "type": "bar", "services": ["выпивка", "учёные", "слухи"]},
                            {"name": "Магазин «Ледяной компас»", "type": "shop", "services": ["снаряжение", "научное оборудование"]},
                            {"name": "Гостиница «Ганимед Инн»", "type": "residential", "services": ["ночлег", "конференц-залы"]},
                            {"name": "Аптека «Крио-мед»", "type": "medical", "services": ["лекарства", "стимуляторы", "криотерапия"]},
                            {"name": "Мед-отсек «БиоГеном»", "type": "medical", "services": ["генетическая терапия", "импланты", "лечение"]},
                            {"name": "Бар «Ледяной Шторм»", "type": "bar", "services": ["выпивка", "наёмники", "слухи"]},
                            {"name": "Терминал перекупщика", "type": "market", "services": ["скупка", "б/у товары", "нелегальный товар"]},
                            {"name": "Склад био-образцов", "type": "warehouse", "services": ["биоматериалы", "хранение", "контрабанда"]},
                        ],
                    },
                },
            },
        },
        "routes": {
            "Земля": {"time": "180 часов", "delta_v": "9.0 км/с", "risk": "medium"},
            "Марс": {"time": "180 часов", "delta_v": "8.0 км/с", "risk": "medium"},
            "Пояс астероидов": {"time": "120 часов", "delta_v": "7.0 км/с", "risk": "high"},
        },
    },
}


class GalaxyMap:
    """Navigation and location system."""

    def __init__(self):
        self.map = GALAXY_MAP
        # Phase 3 loop (шаг 1): закрываем асимметрию hardcoded маршрутов.
        # Например, Земля→Марс есть, но Марс→Земля в некоторых случаях
        # отсутствует. symmetrize_routes() добавляет обратные маршруты.
        self.symmetrize_routes()

    def get_planet(self, planet_name: str) -> Optional[Dict]:
        """Достаёт планету по имени с поддержкой PLANET_ALIAS.

        "EARTH" → "Земля" → planet dict.
        """
        key = _normalize_planet_alias(planet_name)
        if key in self.map:
            return self.map[key]
        # Если после нормализации ключа нет — пробуем оригинал (на случай,
        # когда нормализация вернула значение, но планета не существует,
        # либо ключ уже каноничный).
        if planet_name != key and planet_name in self.map:
            return self.map[planet_name]
        return None

    def get_city(self, planet_name: str, city_name: str) -> Optional[Dict]:
        planet = self.get_planet(planet_name)
        if not planet:
            return None
        return planet.get("cities", {}).get(city_name)

    def get_district(self, planet_name: str, city_name: str, district_name: str) -> Optional[Dict]:
        city = self.get_city(planet_name, city_name)
        if not city:
            return None
        return city.get("districts", {}).get(district_name)

    def list_planets(self) -> List[Dict]:
        result = []
        for name, data in self.map.items():
            result.append({
                "name": name,
                "type": data["type"],
                "population": data["population"],
                "governance": data["governance"],
            })
        return result

    def list_cities(self, planet_name: str) -> List[str]:
        planet = self.get_planet(planet_name)
        if not planet:
            return []
        return list(planet.get("cities", {}).keys())

    def list_districts(self, planet_name: str, city_name: str) -> List[Dict]:
        city = self.get_city(planet_name, city_name)
        if not city:
            return []
        result = []
        for name, data in city.get("districts", {}).items():
            result.append({
                "name": name,
                "type": data.get("type", ""),
                "security": data.get("security", ""),
                "description": data.get("description", "")[:100],
            })
        return result

    def list_establishments(self, planet_name: str, city_name: str, district_name: str) -> List[Dict]:
        district = self.get_district(planet_name, city_name, district_name)
        if not district:
            return []
        return district.get("establishments", [])

    def get_routes_from(self, planet_name: str) -> Dict:
        """Возвращает маршруты с планеты-источника (с поддержкой PLANET_ALIAS).

        "EARTH" → "Земля" → routes от Земли.
        """
        planet = self.get_planet(planet_name)
        if not planet:
            return {}
        return planet.get("routes", {})

    @staticmethod
    def _normalize_route_endpoint(value) -> str:
        """Нормализует значение endpoint маршрута: dict → str, str → str.

        Поддерживает:
          - str (например "Земля", "EARTH", "Марс")
          - dict (например {"planet": "Марс"}, {"name": "Луна"}, {"id": "ceres"})
          - None → ""

        Если результат — известный алиас планеты (PLANET_ALIAS),
        возвращает каноничное русское имя ("EARTH" → "Земля").
        """
        if isinstance(value, dict):
            value = value.get("planet") or value.get("name") or value.get("id") or ""
        if value is None:
            return ""
        s = str(value).strip()
        return _normalize_planet_alias(s)

    def get_route(self, from_planet: str, to_planet: str) -> Optional[Dict]:
        """Универсальный поиск маршрута между планетами.

        Принимает:
          - str ("Земля", "EARTH") или dict ({planet: "Земля"})
          - форматы start_point/end_point / from/to / planet_a/planet_b
          - любой регистр и алиас из PLANET_ALIAS

        Возвращает маршрут из planet['routes'] или None, если маршрута нет.
        """
        # Нормализуем вход: принимаем str или dict (с PLANET_ALIAS)
        from_p = self._normalize_route_endpoint(from_planet)
        to_p = self._normalize_route_endpoint(to_planet)
        if not from_p or not to_p:
            return None
        # Ищем маршрут в routes планеты-источника (с PLANET_ALIAS)
        routes = self.get_routes_from(from_p)
        if not routes:
            return None
        # routes может иметь ключи "Марс" или {"planet": "Марс", ...}
        # Нормализуем ключи destinations тоже
        for key, route in routes.items():
            dest = self._normalize_route_endpoint(key)
            if dest == to_p or key == to_p:
                return route
        return None

    def load_routes_from_kb(self, trade_routes_data: Dict) -> int:
        """Phase 3 P0 fix: загружает маршруты из TRADE_ROUTES_MASTER.json,
        конвертируя start_point/end_point → planet routes.
        Возвращает количество загруженных маршрутов.

        Использует модульный PLANET_ALIAS для нормализации имён планет.

        Phase 3 loop (шаг 1): двусторонняя регистрация — после добавления
        маршрута A→B автоматически регистрируется обратный маршрут B→A,
        если он отсутствует в карте планеты B.
        """
        routes = trade_routes_data.get("routes", [])
        loaded = 0
        for route in routes:
            # Phase 3 P0 fix: унифицируем ключи start_point/end_point → from/to
            from_raw = (
                route.get("from")
                or route.get("start_point")
                or route.get("planet_a")
            )
            to_raw = (
                route.get("to")
                or route.get("end_point")
                or route.get("planet_b")
            )
            # _normalize_route_endpoint уже применяет PLANET_ALIAS
            from_p = self._normalize_route_endpoint(from_raw)
            to_p = self._normalize_route_endpoint(to_raw)
            if not from_p or not to_p or from_p == to_p:
                continue
            # Добавляем в routes планеты-источника
            planet = self.get_planet(from_p)
            if not planet:
                continue
            if "routes" not in planet:
                planet["routes"] = {}
            # Конвертируем время: base_travel_time_days (TRADE_ROUTES) → time (galaxy формат)
            if "time" not in route:
                days = route.get("base_travel_time_days", 72)
                # Конвертируем в формат galaxy ("X часов" или "X-Y часов")
                if days <= 24:
                    time_str = f"{days} часов"
                else:
                    time_str = f"{days * 24} часов"
                route_data = {
                    "time": time_str,
                    "delta_v": "varies",
                    "risk": (route.get("base_risk_level") or "medium").lower(),
                }
            else:
                route_data = dict(route)  # copy, чтобы не делить ссылку с обратным маршрутом
            planet["routes"][to_p] = route_data
            loaded += 1
            # Phase 3 loop: автоматическая регистрация обратного маршрута B→A
            self._ensure_reverse_route(from_p, to_p, route_data)
        return loaded

    def _ensure_reverse_route(self, from_p: str, to_p: str, route_data: Dict) -> bool:
        """Регистрирует обратный маршрут to_p → from_p, если его ещё нет.

        Args:
            from_p: планета-источник (A), откуда идёт route_data.
            to_p: планета-назначение (B), куда нужно добавить обратный маршрут.
            route_data: параметры маршрута (time/delta_v/risk) — копируются
                как есть, потому что большинство маршрутов симметричны по
                времени (round-trip).

        Returns:
            True если обратный маршрут был добавлен, False если уже существовал
            или не удалось зарегистрировать.
        """
        # Нормализуем обе стороны:
        # - from_p через _normalize_route_endpoint (PLANET_ALIAS для имён планет)
        # - to_p через _normalize_route_key (ROUTE_KEY_ALIAS для destination-ключей
        #   маршрутов, чтобы "Церера" в hardcoded стала "Пояс астероидов").
        from_norm = self._normalize_route_endpoint(from_p)
        to_norm = _normalize_route_key(to_p)
        # Дополнительно нормализуем to_norm через PLANET_ALIAS на случай
        # EN-имени ("CERES" → "Церера" → "Пояс астероидов" не сработает,
        # потому что PLANET_ALIAS стоит ПОСЛЕ ROUTE_KEY_ALIAS по логике,
        # но ROUTE_KEY_ALIAS уже содержит CERES).
        if not from_norm or not to_norm or from_norm == to_norm:
            return False
        dest = self.get_planet(to_norm)
        if not dest:
            return False
        if "routes" not in dest:
            dest["routes"] = {}
        # Если обратный маршрут уже есть — не перезаписываем (приоритет
        # у явно заданного маршрута, чтобы не затирать hardcoded данные).
        if from_norm in dest["routes"]:
            return False
        # Копируем данные (round-trip: те же time/delta_v/risk).
        dest["routes"][from_norm] = dict(route_data)
        return True

    def symmetrize_routes(self) -> int:
        """Двусторонняя регистрация ВСЕХ маршрутов из hardcoded GALAXY_MAP.

        Phase 3 loop (шаг 1): для каждой планеты с маршрутами проходит
        по каждому destination и регистрирует обратный маршрут, если
        его нет. Это закрывает асимметрию, унаследованную от hardcoded
        данных (например, Земля→Церера есть, но Церера→Земля — нет;
        после нормализации "Церера"→"Пояс астероидов" симметрия
        обеспечивается автоматически).

        Returns:
            Количество добавленных обратных маршрутов.
        """
        added = 0
        # Берём список планет (keys) перед итерацией, чтобы новые маршруты
        # не вызвали реентрантность.
        planet_names = list(self.map.keys())
        # Сохраняем список пар (from, to, data), чтобы обработать после
        # полного сбора (избегаем модификации словаря во время итерации).
        pairs = []
        for planet_name in planet_names:
            planet = self.map.get(planet_name)
            if not planet or "routes" not in planet:
                continue
            for dest_name, route_data in planet["routes"].items():
                if dest_name == planet_name:  # self-loop
                    continue
                pairs.append((planet_name, dest_name, route_data))
        for from_p, to_p, route_data in pairs:
            if self._ensure_reverse_route(from_p, to_p, route_data):
                added += 1
        return added

    def get_location_description(self, planet: str, city: str, district: str) -> str:
        """Generate a rich description for AI prompt."""
        planet_data = self.get_planet(planet)
        city_data = self.get_city(planet, city)
        district_data = self.get_district(planet, city, district)

        parts = []
        if planet_data:
            parts.append(f"ПЛАНЕТА: {planet} — {planet_data['vibe']}")
            parts.append(f"Гравитация: {planet_data['gravity']}g, население: {planet_data['population']}")
        if city_data:
            parts.append(f"ГОРОД: {city} — {city_data.get('description', '')}")
        if district_data:
            parts.append(f"РАЙОН: {district} — {district_data.get('description', '')}")
            parts.append(f"Безопасность: {district_data.get('security', '?')}, доход: {district_data.get('income', '?')}")
            factions = district_data.get("factions", [])
            if factions:
                parts.append(f"Фракции: {', '.join(factions)}")
            establishments = district_data.get("establishments", [])
            if establishments:
                names = [e["name"] for e in establishments[:5]]
                parts.append(f"Заведения: {', '.join(names)}")

        return "\n".join(parts)

    def get_prompt_context(self, location: Dict) -> str:
        """Generate location context for AI prompt."""
        planet = location.get("planet", "")
        city = location.get("city", "")
        district = location.get("district", "")
        return self.get_location_description(planet, city, district)
