"""
Galaxy Map — navigation system for planets, cities, districts, and establishments.
Based on WORLDBUILD.json data, expanded with travel routes and local flavor.
"""
from typing import Dict, List, Optional

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

    def get_planet(self, planet_name: str) -> Optional[Dict]:
        return self.map.get(planet_name)

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
        planet = self.get_planet(planet_name)
        if not planet:
            return {}
        return planet.get("routes", {})

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
