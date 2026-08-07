"""
Content Expansion V3 — масштабирование контента.
+20 истоков, +15 формативных лет, +10 специализаций, +50 перков, +100 предметов.
"""

# ════════════════════════════════════════════════════════════
#  NEW ORIGINS (+20)  →  total ~46
# ════════════════════════════════════════════════════════════

V3_ORIGINS = [
    # ═══ ЗЕМНЫЕ (новые) ═══
    {
        "id": "ORIGIN_EARTH_CULT", "name": "Культист Неба", "rarity": "редкое",
        "group": "Земля",
        "description": "Выросли в закрытой секте, поклоняющейся космосу как божеству. Фанатичная дисциплина, но искажённое мировоззрение.",
        "attr_mods": {"willpower": 2, "charisma": 1, "intelligence": -1},
        "skill_mods": {"persuasion": 2, "survival": 1, "technology": -1},
        "credits": 5000,
    },
    {
        "id": "ORIGIN_EARTH_ATHLETE", "name": "Профессиональный Атлет", "rarity": "обычное",
        "group": "Земля",
        "description": "Звезда нулевой гравитации или боевого спорта. Тело — ваше главное оружие, но карьера закончилась после травмы.",
        "attr_mods": {"strength": 2, "dexterity": 1, "intelligence": -1},
        "skill_mods": {"combat": 2, "athletics": 1},
        "credits": 35000,
    },
    {
        "id": "ORIGIN_EARTH_DOCTOR", "name": "Военный Хирург", "rarity": "необычное",
        "group": "Земля",
        "description": "Спасали жизни на передовой колониальных войн. Видели худшее, что может случиться с человеческим телом.",
        "attr_mods": {"intelligence": 2, "willpower": 1, "strength": -1},
        "skill_mods": {"medicine": 3, "science": 1},
        "credits": 50000,
    },
    {
        "id": "ORIGIN_EARTH_ENTERTAINER", "name": "Медиа-Звезда", "rarity": "обычное",
        "group": "Земля",
        "description": "Были знамениты на нескольких планетах — актёр, певец или нет-стример. Слава рассеялась, но связи остались.",
        "attr_mods": {"charisma": 3, "strength": -1},
        "skill_mods": {"persuasion": 2, "deception": 1, "combat": -1},
        "credits": 80000, "influence": 5,
    },
    {
        "id": "ORIGIN_EARTH_ORPHAN_LAB", "name": "Подопытный Ребёнок", "rarity": "легендарное",
        "group": "Земля",
        "description": "Вас растили в корпоративной лаборатории как объект генетических экспериментов. Тело модифицировано, но психика надломлена.",
        "attr_mods": {"dexterity": 2, "endurance": 1, "willpower": -1},
        "skill_mods": {"athletics": 2, "stealth": 1},
        "credits": 0,
    },
    # ═══ МАРС (новые) ═══
    {
        "id": "ORIGIN_MARS_PRIEST", "name": "Жрец Красного Бога", "rarity": "редкое",
        "group": "Марс",
        "description": "Духовный лидер марсианского культа, обожествляющего планету. Вера даёт силу, но отталкивает корпоратов.",
        "attr_mods": {"willpower": 2, "charisma": 1},
        "skill_mods": {"persuasion": 2, "medicine": 1, "hacking": -1},
        "credits": 10000,
    },
    {
        "id": "ORIGIN_MARS_GLADIATOR", "name": "Гладиатор Арены", "rarity": "необычное",
        "group": "Марс",
        "description": "Выживали в подпольных боях без правил в куполах Марса. Каждый шрам — история, каждый бой — урок.",
        "attr_mods": {"strength": 2, "endurance": 1, "intelligence": -1},
        "skill_mods": {"combat": 3, "intimidation": 1},
        "credits": 15000,
    },
    {
        "id": "ORIGIN_MARS_ARCHIVIST", "name": "Архивариус Купола", "rarity": "необычное",
        "group": "Марс",
        "description": "Хранили знания Марса в глубинных архивах. Знаете секреты, за которые убивают.",
        "attr_mods": {"intelligence": 2, "perception": 1, "strength": -1},
        "skill_mods": {"education": 3, "investigation": 1},
        "credits": 20000,
    },
    # ═══ ПОЯС АСТЕРОИДОВ (новые) ═══
    {
        "id": "ORIGIN_BELT_PIRATE", "name": "Пират Пояса", "rarity": "редкое",
        "group": "Пояс астероидов",
        "description": "Грабили торговые суда между Марсом и Юпитером. Жизнь вне закона — единственная, которую вы знаете.",
        "attr_mods": {"dexterity": 2, "perception": 1, "willpower": -1},
        "skill_mods": {"piloting": 2, "combat": 1, "diplomacy": -1},
        "credits": 40000,
    },
    {
        "id": "ORIGIN_BELT_MEDIC", "name": "Полевой Медик Пояса", "rarity": "обычное",
        "group": "Пояс астероидов",
        "description": "Лечили шахтёров в условиях нулевой гравитации и без нормального оборудования. Импровизация — второе имя.",
        "attr_mods": {"intelligence": 1, "dexterity": 1, "willpower": 1},
        "skill_mods": {"medicine": 2, "engineering": 1, "survival": 1},
        "credits": 12000,
    },
    {
        "id": "ORIGIN_BELT_SALVAGER_BOSS", "name": "Барон Свалки", "rarity": "редкое",
        "group": "Пояс астероидов",
        "description": "Контролировали крупнейшую утилизационную станцию Пояса. Мусор одних — золото других.",
        "attr_mods": {"charisma": 1, "intelligence": 1, "perception": 1},
        "skill_mods": {"negotiation": 2, "engineering": 1, "bureaucracy": 1},
        "credits": 70000,
    },
    # ═══ ВНЕШНИЕ КОЛОНИИ (новые) ═══
    {
        "id": "ORIGIN_OUTER_NOMAD_FLEET", "name": "Капитан Кочевого Флота", "rarity": "редкое",
        "group": "Внешние колонии",
        "description": "Командовали небольшим караваном кораблей, путешествующим между станциями. Дом — весь космос.",
        "attr_mods": {"charisma": 1, "willpower": 1, "perception": 1},
        "skill_mods": {"piloting": 2, "leadership": 1, "negotiation": 1},
        "credits": 25000,
    },
    {
        "id": "ORIGIN_OUTER_PRISON", "name": "Заключённый Тюрьмы-Астероида", "rarity": "обычное",
        "group": "Внешние колонии",
        "description": "Отбывали срок на тюрьме-астероиде за пределами Пояса. Научились выживать среди худших — и стали одним из них.",
        "attr_mods": {"endurance": 2, "willpower": 1, "charisma": -1},
        "skill_mods": {"combat": 2, "intimidation": 1, "stealth": 1},
        "credits": 2000,
    },
    {
        "id": "ORIGIN_OUTER_XENOBIOLOGIST", "name": "Ксенобиолог", "rarity": "легендарное",
        "group": "Внешние колонии",
        "description": "Изучали внеземные формы жизни на спутниках Юпитера. То, что вы нашли, изменило вас навсегда.",
        "attr_mods": {"intelligence": 2, "perception": 1, "endurance": -1},
        "skill_mods": {"science": 3, "xenology": 1},
        "credits": 30000,
    },
    {
        "id": "ORIGIN_OUTER_COURIER", "name": "Межпланетный Курьер", "rarity": "обычное",
        "group": "Внешние колонии",
        "description": "Доставляли посылки и информацию между станциями. Быстро, тихо, без вопросов.",
        "attr_mods": {"dexterity": 1, "perception": 1, "willpower": 1},
        "skill_mods": {"piloting": 2, "stealth": 1, "navigation": 1},
        "credits": 18000,
    },
    # ═══ ОСОБЫЕ ═══
    {
        "id": "ORIGIN_SYNTH_HYBRID", "name": "Синт-Гибрид", "rarity": "легендарное",
        "group": "Особые",
        "description": "Частично синтетическое существо — человеческий мозг в искусственном теле. Общество боится вас.",
        "attr_mods": {"endurance": 2, "strength": 1, "charisma": -2},
        "skill_mods": {"technology": 2, "engineering": 1},
        "credits": 5000,
    },
    {
        "id": "ORIGIN_CLONE", "name": "Корпоративный Клон", "rarity": "редкое",
        "group": "Особые",
        "description": "Вас создали как копию богатого клиента. Когда оригинал умер, вас выбросили. Идентичность — миф.",
        "attr_mods": {"intelligence": 1, "dexterity": 1, "willpower": -1},
        "skill_mods": {"deception": 2, "stealth": 1},
        "credits": 500,
    },
    {
        "id": "ORIGIN_AMNESIA", "name": "Человек без Прошлого", "rarity": "легендарное",
        "group": "Особые",
        "description": "Очнулись на станции без памяти. Кто-то стёр ваше прошлое. Осталось только имя — и ощущение, что за вами следят.",
        "attr_mods": {"perception": 2, "willpower": 1},
        "skill_mods": {"investigation": 1, "survival": 1},
        "credits": 3000,
    },
    {
        "id": "ORIGIN_DESERTER", "name": "Дезертир Флота", "rarity": "необычное",
        "group": "Особые",
        "description": "Бежали из военного флота после того, что видели. Военный трибунал ищет вас. Навыки остались.",
        "attr_mods": {"dexterity": 1, "willpower": 1, "endurance": 1},
        "skill_mods": {"combat": 1, "piloting": 1, "stealth": 1, "technology": 1},
        "credits": 8000,
    },
    {
        "id": "ORIGIN_AI_CULT", "name": "Последователь Машинного Разума", "rarity": "редкое",
        "group": "Особые",
        "description": "Член секты, поклоняющейся ИИ как высшей форме сознания. Считаете, что люди — переходная форма.",
        "attr_mods": {"intelligence": 2, "charisma": -1},
        "skill_mods": {"hacking": 2, "technology": 2, "persuasion": -1},
        "credits": 7000,
    },
]

# ════════════════════════════════════════════════════════════
#  NEW FORMATIVE YEARS (+15)  →  total ~38
# ════════════════════════════════════════════════════════════

V3_FORMATIVE_YEARS = [
    # ═══ КРИМИНАЛЬНЫЕ ═══
    {
        "id": "FY_GANG_LEADER", "name": "Лидер Банды",
        "group": "Криминальные",
        "description": "Возглавляли уличную банду в подуровнях мегаполиса. Научились управлять людьми через страх и уважение.",
        "attr_mods": {"charisma": 1, "willpower": 1},
        "skill_mods": {"intimidation": 2, "leadership": 1, "combat": 1},
    },
    {
        "id": "FY_ASSASSIN_SCHOOL", "name": "Школа Теней",
        "group": "Криминальные",
        "description": "Тренировались в секретной школе наёмных убийц. Каждое движение отточено до смертельного совершенства.",
        "attr_mods": {"dexterity": 2},
        "skill_mods": {"stealth": 2, "combat": 2, "persuasion": -1},
    },
    {
        "id": "FY_SMUGGLER_ROUTE", "name": "Контрабандные Маршруты",
        "group": "Криминальные",
        "description": "Годы перевозки запрещённых грузов через блокпосты и патрули. Знаете каждую лазейку в системе.",
        "attr_mods": {"perception": 1, "dexterity": 1},
        "skill_mods": {"piloting": 1, "stealth": 1, "negotiation": 1, "navigation": 1},
    },
    # ═══ НАУЧНЫЕ ═══
    {
        "id": "FY_QUANTUM_LAB", "name": "Квантовая Лаборатория",
        "group": "Научные",
        "description": "Работали на переднем крае квантовой физики. Реальность — не то, чем кажется, и вы это доказали.",
        "attr_mods": {"intelligence": 2},
        "skill_mods": {"science": 3, "hacking": 1},
    },
    {
        "id": "FY_BIOTECH_INTERN", "name": "Стажёр Биотеха",
        "group": "Научные",
        "description": "Три года в биотехнологической компании. Генная инженерия, клонирование, импланты — всё это ваша стихия.",
        "attr_mods": {"intelligence": 1, "dexterity": 1},
        "skill_mods": {"medicine": 2, "science": 1, "technology": 1},
    },
    {
        "id": "FY_XENO_EXPEDITION", "name": "Ксеноэкспедиция",
        "group": "Научные",
        "description": "Участвовали в экспедиции по изучению аномалий во внешней системе. Видели то, что не укладывается в науку.",
        "attr_mods": {"willpower": 1, "perception": 1},
        "skill_mods": {"science": 2, "survival": 1, "xenology": 1},
    },
    # ═══ КОММЕРЧЕСКИЕ ═══
    {
        "id": "FY_CORP_SPY", "name": "Корпоративный Шпион",
        "group": "Коммерческие",
        "description": "Внедрялись в конкурирующие компании, крали секреты и вербовали инсайдеров. Доверие — ваше оружие.",
        "attr_mods": {"charisma": 1, "perception": 1},
        "skill_mods": {"deception": 2, "investigation": 1, "hacking": 1},
    },
    {
        "id": "FY_TRADE_CARAVAN", "name": "Торговый Караван",
        "group": "Коммерческие",
        "description": "Пересекали солнечную систему с торговым караваном. Научились торговать, ремонтировать и защищаться.",
        "attr_mods": {"endurance": 1, "charisma": 1},
        "skill_mods": {"negotiation": 2, "engineering": 1, "piloting": 1},
    },
    {
        "id": "FY_BLACK_MARKET", "name": "Чёрный Рынок",
        "group": "Коммерческие",
        "description": "Работали на подпольный рынок — продавали всё, от информации до органов. Грязно, но прибыльно.",
        "attr_mods": {"charisma": 1, "willpower": 1},
        "skill_mods": {"negotiation": 2, "deception": 1, "stealth": 1},
    },
    # ═══ ВОЕННЫЕ (новые) ═══
    {
        "id": "FY_MECH_PILOT", "name": "Пилот Меха",
        "group": "Военные",
        "description": "Управляли тяжёлым боевым мехом в зонах конфликтов. Машина стала продолжением вашего тела.",
        "attr_mods": {"dexterity": 1, "endurance": 1},
        "skill_mods": {"piloting": 2, "combat": 1, "engineering": 1},
    },
    {
        "id": "FY_SPEC_OPS", "name": "Спецназ",
        "group": "Военные",
        "description": "Элитное подразделение для невозможных миссий. Вы — оружие, заточенное до бритвенной остроты.",
        "attr_mods": {"strength": 1, "dexterity": 1},
        "skill_mods": {"combat": 2, "stealth": 1, "athletics": 1},
    },
    # ═══ СОЦИАЛЬНЫЕ ═══
    {
        "id": "FY_DIPLOMAT_CORPS", "name": "Дипломатический Корпус",
        "group": "Социальные",
        "description": "Представляли свою фракцию на межпланетных переговорах. Слова — ваше оружие.",
        "attr_mods": {"charisma": 2},
        "skill_mods": {"diplomacy": 2, "persuasion": 1, "education": 1},
    },
    {
        "id": "FY_STREET_PREACHER", "name": "Уличный Проповедник",
        "group": "Социальные",
        "description": "Несли свою правду в массы на станциях и в куполах. Не все слушали, но те, кто слушал, были преданы.",
        "attr_mods": {"charisma": 1, "willpower": 1},
        "skill_mods": {"persuasion": 2, "survival": 1, "intimidation": 1},
    },
    # ═══ ТЕХНИЧЕСКИЕ ═══
    {
        "id": "FY_SHIPYARD_WORKER", "name": "Рабочий Верфи",
        "group": "Технические",
        "description": "Строили и ремонтировали корабли на орбитальных верфях. Знаете каждый болт и каждый сварочный шов.",
        "attr_mods": {"strength": 1, "endurance": 1},
        "skill_mods": {"engineering": 3, "technology": 1},
    },
    {
        "id": "FY_AI_ARCHITECT", "name": "Архитектор ИИ",
        "group": "Технические",
        "description": "Проектировали искусственные интеллекты для станций и кораблей. Понимаете машинный разум лучше человеческого.",
        "attr_mods": {"intelligence": 2},
        "skill_mods": {"hacking": 2, "technology": 2, "persuasion": -1},
    },
]

# ════════════════════════════════════════════════════════════
#  NEW SPECIALIZATIONS (+10)  →  total ~29
# ════════════════════════════════════════════════════════════

V3_SPECIALIZATIONS = [
    {
        "id": "SPEC_BOUNTY_HUNTER", "name": "Охотник за Головами",
        "group": "Боевые",
        "description": "Выслеживаете цели по всей солнечной системе. Терпение, навыки преследования и точный выстрел — ваши инструменты.",
        "skill_mods": {"combat": 2, "investigation": 2, "stealth": 1},
        "equipment": ["Стелс-сканер", "Наручники с ЭМИ", "Пистолет с усыпляющими зарядами"],
    },
    {
        "id": "SPEC_SABOTEUR", "name": "Диверсант",
        "group": "Боевые",
        "description": "Мастер разрушения и саботажа. Взрывчатка, яды, вирусы — всё это ваши кисти, а мир — холст.",
        "skill_mods": {"engineering": 2, "stealth": 2, "combat": 1},
        "equipment": ["Набор взрывчатки", "Универсальный отравитель", "Маскировочное поле"],
    },
    {
        "id": "SPEC_CORPO_FIXER", "name": "Корпоративный Решала",
        "group": "Социальные",
        "description": "Решаете проблемы — любые проблемы. От слияний до исчезновений. У вас есть контакт на каждый случай.",
        "skill_mods": {"negotiation": 2, "deception": 2, "bureaucracy": 1},
        "equipment": ["Зашифрованный коммлинк", "Корпо-ID (поддельный)", "Кредитная карта на предъявителя"],
    },
    {
        "id": "SPEC_XENOLINGUIST", "name": "Ксенолингвист",
        "group": "Научные",
        "description": "Изучаете и расшифровываете языки, включая потенциально внеземные. Границы — это языковые барьеры, и вы их стираете.",
        "skill_mods": {"science": 2, "xenology": 2, "diplomacy": 1},
        "equipment": ["Универсальный переводчик", "Архив языков", "Нейро-словарь"],
    },
    {
        "id": "SPEC_GENETICIST", "name": "Генетик",
        "group": "Научные",
        "description": "Манипулируете ДНК как кодом. Улучшения, мутации, клонирование — этика отстаёт от ваших возможностей.",
        "skill_mods": {"science": 3, "medicine": 2},
        "equipment": ["Ген-секвенсор", "Образцы мутагенов", "Портативная лаборатория"],
    },
    {
        "id": "SPEC_MECH_OPERATOR", "name": "Оператор Мехов",
        "group": "Технические",
        "description": "Управляете тяжёлой техникой — от грузовых экзоскелетов до боевых мехов. Машина — продолжение тела.",
        "skill_mods": {"piloting": 3, "engineering": 1, "combat": 1},
        "equipment": ["Лёгкий экзоскелет", "Нейро-шлем пилота", "Ремкомплект мехов"],
    },
    {
        "id": "SPEC_PSYCH_PROFILER", "name": "Психопрофайлер",
        "group": "Социальные",
        "description": "Читаете людей как открытую книгу. Микровыражения, тон голоса, язык тела — от вас не скроется ничто.",
        "skill_mods": {"investigation": 2, "persuasion": 2, "medicine": 1},
        "equipment": ["Анализатор микровыражений", "Нейросканер", "Психологический профиль-база"],
    },
    {
        "id": "SPEC_VOID_NAVIGATOR", "name": "Навигатор Пустоты",
        "group": "Технические",
        "description": "Прокладываете маршруты через аномалии, астероидные поля и гравитационные колодцы. Там, где другие видят хаос, вы видите путь.",
        "skill_mods": {"navigation": 3, "piloting": 1, "science": 1},
        "equipment": ["Звёздные карты (обновлённые)", "Навигационный ИИ", "Детектор аномалий"],
    },
    {
        "id": "SPEC_UNDERGROUND_DOC", "name": "Подпольный Доктор",
        "group": "Медицинские",
        "description": "Лечите тех, кто не может пойти в обычную клинику. Без вопросов, за наличные. Установка имплантов — бонус.",
        "skill_mods": {"medicine": 3, "stealth": 1, "negotiation": 1},
        "equipment": ["Хирургический набор (полевой)", "Анестетики", "База органов на чёрном рынке"],
    },
    {
        "id": "SPEC_INFO_BROKER", "name": "Инфоброкер",
        "group": "Социальные",
        "description": "Информация — валюта будущего, и вы — её банкир. Покупаете, продаёте и торгуете секретами.",
        "skill_mods": {"hacking": 2, "negotiation": 2, "investigation": 1},
        "equipment": ["Зашифрованная база данных", "Сеть информаторов", "Скремблер связи"],
    },
]

# ════════════════════════════════════════════════════════════
#  NEW PERKS (+50)  →  total ~211
# ════════════════════════════════════════════════════════════

V3_PERKS = [
    # ── SURVIVAL (8) ──
    {"id": "v3_iron_stomach", "name": "Железный желудок", "category": "survival",
     "description": "Можете есть испорченную пищу без последствий", "effect": {"endurance": 1}, "tier": 1},
    {"id": "v3_rad_resistant", "name": "Радиационная устойчивость", "category": "survival",
     "description": "Половина урона от радиации", "effect": {"endurance": 1}, "tier": 1},
    {"id": "v3_zero_g_native", "name": "Дитя невесомости", "category": "survival",
     "description": "+2 к действиям в нулевой гравитации", "effect": {"dexterity": 1}, "tier": 1},
    {"id": "v3_vacuum_lung", "name": "Вакуумные лёгкие", "category": "survival",
     "description": "Задержка дыхания 5 минут в вакууме", "effect": {"endurance": 2}, "tier": 2},
    {"id": "v3_resource_scavenger", "name": "Собиратель ресурсов", "category": "survival",
     "description": "+30% ресурсов при обыске", "effect": {"perception": 1}, "tier": 1},
    {"id": "v3_cold_adapted", "name": "Хладнокровный", "category": "survival",
     "description": "Не теряете действия от холода", "effect": {"endurance": 1}, "tier": 1},
    {"id": "v3_terrain_expert", "name": "Эксперт местности", "category": "survival",
     "description": "+1 к навигации на изученных планетах", "effect": {"navigation": 1}, "tier": 2},
    {"id": "v3_emergency_medic", "name": "Полевая медицина", "category": "survival",
     "description": "Стимуляторы лечат +50% при критическом здоровье", "effect": {"medicine": 1}, "tier": 2},

    # ── COMBAT ADVANCED (8) ──
    {"id": "v3_dual_wield", "name": "Двойное оружие", "category": "combat",
     "description": "Стреляете с двух рук без штрафа", "effect": {"combat": 1}, "tier": 2},
    {"id": "v3_heavy_weapons", "name": "Тяжёлое вооружение", "category": "combat",
     "description": "Можете использовать тяжёлое оружие без штрафа к скорости", "effect": {"combat": 2}, "tier": 3},
    {"id": "v3_counter_attack", "name": "Контрудар", "category": "combat",
     "description": "30% шанс автоматической контратаки при уклонении", "effect": {"dexterity": 1}, "tier": 2},
    {"id": "v3_armor_piercing", "name": "Бронебойный", "category": "combat",
     "description": "Игнорировать 2 единицы брони врага", "effect": {"combat": 1}, "tier": 2},
    {"id": "v3_grenadier", "name": "Гренадёр", "category": "combat",
     "description": "+50% радиус и урон гранат", "effect": {"combat": 1}, "tier": 1},
    {"id": "v3_execution", "name": "Казнь", "category": "combat",
     "description": "Мгновенное убийство оглушённых врагов", "effect": {"combat": 2}, "tier": 3},
    {"id": "v3_iron_skin", "name": "Железная кожа", "category": "combat",
     "description": "+2 базовая броня без экипировки", "effect": {"endurance": 2}, "tier": 2},
    {"id": "v3_adrenaline_rush", "name": "Адреналиновый шторм", "category": "combat",
     "description": "При здоровье <25% урон увеличивается на 50%", "effect": {"strength": 1}, "tier": 3},

    # ── SOCIAL (8) ──
    {"id": "v3_silver_tongue", "name": "Серебряный язык", "category": "social",
     "description": "+2 к цене продажи товаров", "effect": {"persuasion": 1}, "tier": 1},
    {"id": "v3_intimidation_master", "name": "Мастер запугивания", "category": "social",
     "description": "Враги со слабой волей сдаются без боя", "effect": {"intimidation": 2}, "tier": 2},
    {"id": "v3_false_identity", "name": "Ложная личность", "category": "social",
     "description": "Поддерживаете вторую личность с документами", "effect": {"deception": 2}, "tier": 2},
    {"id": "v3_information_network", "name": "Информационная сеть", "category": "social",
     "description": "Получаете подсказки о квестах в каждом городе", "effect": {"investigation": 1}, "tier": 1},
    {"id": "v3_born_leader", "name": "Прирождённый лидер", "category": "social",
     "description": "Компаньоны получают +1 ко всем навыкам", "effect": {"leadership": 2}, "tier": 3},
    {"id": "v3_underworld_contacts", "name": "Контакты преступного мира", "category": "social",
     "description": "Доступ к чёрному рынку на любой станции", "effect": {"negotiation": 1}, "tier": 1},
    {"id": "v3_political_savvy", "name": "Политическая хватка", "category": "social",
     "description": "+1 к дипломатии с фракциями", "effect": {"diplomacy": 1}, "tier": 1},
    {"id": "v3_empathy_engine", "name": "Эмпатия", "category": "social",
     "description": "Видите скрытые опции в диалогах", "effect": {"perception": 1}, "tier": 2},

    # ── TECH / ENGINEERING (8) ──
    {"id": "v3_overclocker", "name": "Разгон систем", "category": "tech",
     "description": "Импланты работают на 20% эффективнее", "effect": {"technology": 1}, "tier": 1},
    {"id": "v3_jury_rig", "name": "На коленке", "category": "tech",
     "description": "Временный ремонт любого оборудования без запчастей", "effect": {"engineering": 1}, "tier": 1},
    {"id": "v3_drone_master", "name": "Повелитель дронов", "category": "tech",
     "description": "Управляете до 3 дронов одновременно", "effect": {"technology": 2}, "tier": 2},
    {"id": "v3_emp_shield", "name": "ЭМИ-щит", "category": "tech",
     "description": "Ваши импланты защищены от электромагнитных атак", "effect": {"technology": 1}, "tier": 2},
    {"id": "v3_salvage_expert", "name": "Эксперт-утилизатор", "category": "tech",
     "description": "+50% материалов при разборке предметов", "effect": {"engineering": 1}, "tier": 1},
    {"id": "v3_weapon_modder", "name": "Оружейный мод", "category": "tech",
     "description": "Можете устанавливать дополнительные моды на оружие", "effect": {"engineering": 2}, "tier": 2},
    {"id": "v3_ship_mechanic", "name": "Корабельный механик", "category": "tech",
     "description": "+30% эффективность ремонта кораблей", "effect": {"engineering": 1}, "tier": 1},
    {"id": "v3_quantum_processor", "name": "Квантовый процессор", "category": "tech",
     "description": "+2 к хакингу, но стресс при провале удваивается", "effect": {"hacking": 2}, "tier": 3},

    # ── PILOTING / NAVIGATION (6) ──
    {"id": "v3_evasive_pilot", "name": "Уклончивый пилот", "category": "piloting",
     "description": "+2 к уклонению в космическом бою", "effect": {"piloting": 1}, "tier": 1},
    {"id": "v3_asteroid_runner", "name": "Астероидный бегун", "category": "piloting",
     "description": "Нет штрафа при полёте через астероидные поля", "effect": {"piloting": 2}, "tier": 2},
    {"id": "v3_fuel_efficiency", "name": "Экономия топлива", "category": "piloting",
     "description": "-25% расход топлива", "effect": {"piloting": 1}, "tier": 1},
    {"id": "v3_smuggler_hold", "name": "Тайный отсек", "category": "piloting",
     "description": "Скрытый отсек в корабле, невидимый для сканеров", "effect": {"stealth": 1}, "tier": 2},
    {"id": "v3_combat_pilot", "name": "Боевой пилот", "category": "piloting",
     "description": "+2 к урону корабельного оружия", "effect": {"piloting": 2}, "tier": 2},
    {"id": "v3_speed_demon", "name": "Демон скорости", "category": "piloting",
     "description": "+20% скорость корабля, -10% маневренность", "effect": {"piloting": 1}, "tier": 1},

    # ── IMPLANT-SPECIFIC (6) ──
    {"id": "v3_cyber_eyes_upgrade", "name": "Кибер-глаза v2", "category": "implants",
     "description": "Тепловизор + zoom 10x + распознавание лиц", "effect": {"perception": 2}, "tier": 2},
    {"id": "v3_subdermal_armor", "name": "Субдермальная броня", "category": "implants",
     "description": "+3 броня, невидима для сканеров", "effect": {"endurance": 1}, "tier": 3},
    {"id": "v3_reflex_booster", "name": "Ускоритель рефлексов", "category": "implants",
     "description": "+2 к инициативе, +1 к уклонению", "effect": {"dexterity": 2}, "tier": 2},
    {"id": "v3_cortex_bomb", "name": "Кортексная бомба", "category": "implants",
     "description": "При смерти наносите 3d10 урона всем рядом. Отключаемая.", "effect": {"willpower": -1}, "tier": 3},
    {"id": "v3_synth_blood", "name": "Синтетическая кровь", "category": "implants",
     "description": "Регенерация 1 HP/ход, иммунитет к ядам", "effect": {"endurance": 2}, "tier": 3},
    {"id": "v3_muscle_wire", "name": "Мышечные провода", "category": "implants",
     "description": "+2 к силе, +1 к ближнему бою", "effect": {"strength": 2}, "tier": 2},

    # ── STEALTH (6) ──
    {"id": "v3_shadow_step", "name": "Шаг тени", "category": "stealth",
     "description": "Бесшумное перемещение даже в броне", "effect": {"stealth": 2}, "tier": 2},
    {"id": "v3_distraction", "name": "Отвлечение", "category": "stealth",
     "description": "Создаёте звуковую приманку для отвлечения врагов", "effect": {"stealth": 1}, "tier": 1},
    {"id": "v3_vanish", "name": "Исчезновение", "category": "stealth",
     "description": "Выход из боя без проверки при стелсе 6+", "effect": {"stealth": 2}, "tier": 3},
    {"id": "v3_pickpocket", "name": "Карманник", "category": "stealth",
     "description": "Можете красть предметы у NPC в диалоге", "effect": {"dexterity": 1}, "tier": 1},
    {"id": "v3_forger", "name": "Фальсификатор", "category": "stealth",
     "description": "Создание поддельных документов и ID", "effect": {"deception": 2}, "tier": 2},
    {"id": "v3_ghost_walk", "name": "Призрачный шаг", "category": "stealth",
     "description": "Камеры и датчики не обнаруживают вас", "effect": {"stealth": 3}, "tier": 3},
]

# ════════════════════════════════════════════════════════════
#  NEW SHOP ITEMS (+120)  →  total ~314
# ════════════════════════════════════════════════════════════

V3_SHOP_ITEMS = {
    "weapons": [
        # ── Пистолеты ──
        {"id": "W_PISTOL_STEALTH", "name": "Бесшумный «Шёпот» Mk.III", "base_price": 8000,
         "stats": "1d6+2 урона, silent, бонус +1 stealth", "rarity": "uncommon"},
        {"id": "W_PISTOL_HEAVY", "name": "Тяжёлый «Носорог»", "base_price": 12000,
         "stats": "2d6+3 урона, -1 инициатива", "rarity": "uncommon"},
        {"id": "W_PISTOL_SMART", "name": "Умный «Синапс»", "base_price": 25000,
         "stats": "1d8+2 урона, самонаводящиеся пули, требует нейроинтерфейс", "rarity": "rare"},
        {"id": "W_PISTOL_PLASMA", "name": "Плазменный «Солнцеед»", "base_price": 45000,
         "stats": "2d8 урона, игнорирует 3 брони, перегрев 1/3 выстрела", "rarity": "rare"},
        # ── Дробовики ──
        {"id": "W_SHOTGUN_BREACHER", "name": "Штурмовой «Кувалда»", "base_price": 15000,
         "stats": "3d6 урона ближний, разбрасывание, -2 средний/дальний", "rarity": "uncommon"},
        {"id": "W_SHOTGUN_FLECHETTE", "name": "Флешетный «Ёж»", "base_price": 20000,
         "stats": "2d6+4 урона, игнорирует лёгкую броню", "rarity": "uncommon"},
        # ── Винтовки ──
        {"id": "W_RIFLE_SNIPER", "name": "Снайперская «Комета»", "base_price": 35000,
         "stats": "3d8 урона дальний, требует 1 ход прицеливания", "rarity": "rare"},
        {"id": "W_RIFLE_ASSAULT_V2", "name": "Штурмовая «Гидра» Mk.II", "base_price": 22000,
         "stats": "2d6+2 урона, автоматический огонь, 30 патронов", "rarity": "uncommon"},
        {"id": "W_RIFLE_GAUSS", "name": "Гаусс-винтовка «Рельса»", "base_price": 60000,
         "stats": "4d6 урона, пробивает стены, 3 выстрела/бой", "rarity": "epic"},
        # ── Ближний бой ──
        {"id": "W_MELEE_VIBROBLADE", "name": "Виброклинок «Осколок»", "base_price": 10000,
         "stats": "2d6+2 урона, игнорирует 2 брони", "rarity": "uncommon"},
        {"id": "W_MELEE_MONOWHIP", "name": "Моноструна", "base_price": 40000,
         "stats": "3d6 урона, шанс мгновенного убийства 5%, требует dex 7+", "rarity": "rare"},
        {"id": "W_MELEE_STUN_BATON", "name": "Шоковая дубинка «Гром»", "base_price": 5000,
         "stats": "1d6 урона + оглушение 1 ход", "rarity": "common"},
        {"id": "W_MELEE_POWER_FIST", "name": "Силовой кулак", "base_price": 30000,
         "stats": "2d8+4 урона, отбрасывание, -2 к dex", "rarity": "rare"},
        # ── Тяжёлое ──
        {"id": "W_HEAVY_MINIGUN", "name": "Минигат «Вулкан»", "base_price": 80000,
         "stats": "4d6 урона по области, 100 патронов, нужна сила 8+", "rarity": "epic"},
        {"id": "W_HEAVY_ROCKET", "name": "РПО «Немезида»", "base_price": 50000,
         "stats": "5d8 урона по области, 1 выстрел, перезарядка 2 хода", "rarity": "rare"},
        {"id": "W_HEAVY_FLAMER", "name": "Огнемёт «Ифрит»", "base_price": 35000,
         "stats": "2d6 урона/ход, область 3м, горение 3 хода", "rarity": "rare"},
    ],
    "armor": [
        {"id": "A_STEALTH_SUIT", "name": "Стелс-костюм «Тень»", "base_price": 25000,
         "stats": "Защита 2, +2 stealth, активный камуфляж", "rarity": "rare"},
        {"id": "A_POWER_ARMOR_LIGHT", "name": "Лёгкая силовая броня", "base_price": 60000,
         "stats": "Защита 6, +1 сила, -1 dex, батарея 8 часов", "rarity": "rare"},
        {"id": "A_POWER_ARMOR_HEAVY", "name": "Тяжёлая силовая броня «Титан»", "base_price": 120000,
         "stats": "Защита 10, +2 сила, -3 dex, герметичная, батарея 4 часа", "rarity": "epic"},
        {"id": "A_EXOSUIT_WORKER", "name": "Рабочий экзоскелет", "base_price": 30000,
         "stats": "Защита 3, +3 сила, +100 грузоподъёмность", "rarity": "uncommon"},
        {"id": "A_NANOWEAVE", "name": "Наноткань «Кокон»", "base_price": 40000,
         "stats": "Защита 4, самовосстановление 1/ход, лёгкая", "rarity": "rare"},
        {"id": "A_HAZMAT_SUIT", "name": "Костюм химзащиты", "base_price": 8000,
         "stats": "Защита 1, иммунитет к ядам/радиации/био", "rarity": "common"},
        {"id": "A_RIOT_ARMOR", "name": "Штурмовая броня «Бастион»", "base_price": 35000,
         "stats": "Защита 7, +1 к запугиванию, -2 stealth", "rarity": "uncommon"},
        {"id": "A_FLIGHT_SUIT", "name": "Лётный костюм «Кондор»", "base_price": 15000,
         "stats": "Защита 2, +1 piloting, герметичный, аварийный маяк", "rarity": "common"},
        {"id": "A_UNDERCOVER_VEST", "name": "Скрытый бронежилет", "base_price": 12000,
         "stats": "Защита 3, невидим под одеждой", "rarity": "uncommon"},
        {"id": "A_CERAMIC_PLATES", "name": "Керамические пластины", "base_price": 18000,
         "stats": "Защита 5, одноразовая (разрушается после 1 крит. попадания)", "rarity": "uncommon"},
    ],
    "implants": [
        {"id": "I_COMBAT_REFLEX", "name": "Боевые рефлексы v3", "base_price": 45000,
         "stats": "+2 инициатива, +1 уклонение", "rarity": "rare"},
        {"id": "I_DERMAL_PLATING", "name": "Дермальное покрытие", "base_price": 55000,
         "stats": "+3 броня, -5% человечности", "rarity": "rare"},
        {"id": "I_THERMAL_EYES", "name": "Термо-глаза «Хищник»", "base_price": 30000,
         "stats": "+2 perception, тепловизор, ночное зрение", "rarity": "uncommon"},
        {"id": "I_TOXIN_FILTER", "name": "Токсин-фильтр", "base_price": 20000,
         "stats": "Иммунитет к ядам и наркотикам", "rarity": "uncommon"},
        {"id": "I_MUSCLE_GRAFTS", "name": "Мышечные имплантаты", "base_price": 40000,
         "stats": "+2 сила, +1 ближний бой, -3% человечности", "rarity": "rare"},
        {"id": "I_SPEED_SPINE", "name": "Спинной ускоритель", "base_price": 65000,
         "stats": "+2 dex, +1 инициатива, -5% человечности", "rarity": "epic"},
        {"id": "I_MEMORY_CHIP", "name": "Чип памяти «Мнемозина»", "base_price": 25000,
         "stats": "+1 intelligence, +1 education, запись всего", "rarity": "uncommon"},
        {"id": "I_VOICE_MOD", "name": "Модуль голоса «Сирена»", "base_price": 15000,
         "stats": "+2 persuasion, имитация любого голоса", "rarity": "uncommon"},
        {"id": "I_ADRENAL_PUMP", "name": "Адреналиновый насос", "base_price": 50000,
         "stats": "1/бой: +3 к атаке и урону на 2 хода", "rarity": "rare"},
        {"id": "I_NEURO_FIREWALL", "name": "Нейро-файрвол", "base_price": 35000,
         "stats": "Иммунитет к хакингу имплантов, +1 willpower", "rarity": "rare"},
        {"id": "I_GILLS", "name": "Био-жабры «Нептун»", "base_price": 22000,
         "stats": "Дыхание под водой, +1 к действиям в жидкости", "rarity": "uncommon"},
        {"id": "I_BONE_LACING", "name": "Костное армирование", "base_price": 60000,
         "stats": "+2 endurance, кости нельзя сломать, -5% человечности", "rarity": "epic"},
    ],
    "gadgets": [
        {"id": "G_HOLO_DECOY", "name": "Голо-обманка", "base_price": 12000,
         "stats": "Создаёт голограмму-двойника на 30 сек", "rarity": "uncommon"},
        {"id": "G_EMP_GRENADE", "name": "ЭМИ-граната", "base_price": 3000,
         "stats": "Отключает электронику в радиусе 10м на 1 ход", "rarity": "common"},
        {"id": "G_FLASHBANG", "name": "Светошумовая граната", "base_price": 1500,
         "stats": "Оглушение всех в 5м на 1 ход", "rarity": "common"},
        {"id": "G_SMOKE_BOMB", "name": "Дымовая шашка", "base_price": 800,
         "stats": "Дым в 10м на 3 хода, -3 к стрельбе", "rarity": "common"},
        {"id": "G_MINE_PROXIMITY", "name": "Мина приближения", "base_price": 5000,
         "stats": "2d8 урона, авто-детонация", "rarity": "uncommon"},
        {"id": "G_GRAPPLE_GUN", "name": "Крюк-пушка", "base_price": 7000,
         "stats": "Перемещение по вертикали 30м, крепление к поверхности", "rarity": "uncommon"},
        {"id": "G_DRONE_RECON", "name": "Разведдрон «Оса»", "base_price": 15000,
         "stats": "Разведка 200м, камера + микрофон, 2 часа полёта", "rarity": "uncommon"},
        {"id": "G_DRONE_COMBAT", "name": "Боевой дрон «Шершень»", "base_price": 40000,
         "stats": "1d8 урона, автономный, 1 час работы", "rarity": "rare"},
        {"id": "G_LOCKPICK_QUANTUM", "name": "Квантовый взломщик", "base_price": 20000,
         "stats": "+3 к взлому электронных замков", "rarity": "rare"},
        {"id": "G_MEDSCANNER", "name": "Медсканер «Диагност»", "base_price": 10000,
         "stats": "+2 к medicine, диагностика за 1 действие", "rarity": "uncommon"},
        {"id": "G_SIGNAL_JAMMER", "name": "Глушилка связи", "base_price": 8000,
         "stats": "Блокирует связь в 50м на 10 мин", "rarity": "uncommon"},
        {"id": "G_PORTABLE_TURRET", "name": "Портативная турель", "base_price": 25000,
         "stats": "1d6 урона/ход, автоматическая, 10 ходов работы", "rarity": "rare"},
        {"id": "G_CLIMBING_KIT", "name": "Магнитные перчатки", "base_price": 6000,
         "stats": "Перемещение по стенам и потолкам", "rarity": "common"},
        {"id": "G_HOLO_MAP", "name": "Голографическая карта", "base_price": 5000,
         "stats": "+1 navigation, показывает POI в 500м", "rarity": "common"},
        {"id": "G_BREACHING_CHARGE", "name": "Заряды для штурма", "base_price": 4000,
         "stats": "Вскрывает двери и стены, 3 шт.", "rarity": "common"},
    ],
    "consumables": [
        {"id": "C_STIM_REFLEX", "name": "Рефлекс-стимулятор", "base_price": 1200,
         "stats": "+2 dexterity 3 хода", "rarity": "common"},
        {"id": "C_STIM_FOCUS", "name": "Стим «Фокус»", "base_price": 1000,
         "stats": "+2 intelligence 3 хода", "rarity": "common"},
        {"id": "C_STIM_RAGE", "name": "Боевой стим «Ярость»", "base_price": 1500,
         "stats": "+3 combat, -2 perception на 3 хода", "rarity": "uncommon"},
        {"id": "C_MEDKIT_ADVANCED", "name": "Продвинутая аптечка", "base_price": 3000,
         "stats": "Восстановление 50% HP", "rarity": "uncommon"},
        {"id": "C_MEDKIT_TRAUMA", "name": "Травма-набор", "base_price": 5000,
         "stats": "Восстановление 75% HP + снятие 1 ранения", "rarity": "rare"},
        {"id": "C_ANTIDOTE", "name": "Универсальное противоядие", "base_price": 2000,
         "stats": "Снимает все яды и токсины", "rarity": "common"},
        {"id": "C_RAD_AWAY", "name": "Анти-рад «Чистота»", "base_price": 1500,
         "stats": "Убирает 50 ед. радиации", "rarity": "common"},
        {"id": "C_NANO_REPAIR", "name": "Нано-спрей ремонта", "base_price": 2500,
         "stats": "Восстанавливает 30% прочности брони", "rarity": "uncommon"},
        {"id": "C_OXYGEN_TANK", "name": "Кислородный баллон", "base_price": 500,
         "stats": "4 часа дыхания в вакууме/под водой", "rarity": "common"},
        {"id": "C_FOOD_RATION_FANCY", "name": "Премиум-рацион «Гурман»", "base_price": 300,
         "stats": "+1 к восстановлению, +1 morale", "rarity": "common"},
        {"id": "C_HACK_CHIP", "name": "Одноразовый чип взлома", "base_price": 4000,
         "stats": "+4 к одной попытке хакинга", "rarity": "uncommon"},
        {"id": "C_STEALTH_FIELD", "name": "Стелс-генератор (одноразовый)", "base_price": 8000,
         "stats": "Невидимость 30 секунд", "rarity": "rare"},
        {"id": "C_ENERGY_CELL", "name": "Энергоячейка", "base_price": 200,
         "stats": "Заряд для энергетического оружия (20 выстрелов)", "rarity": "common"},
        {"id": "C_FLARE", "name": "Сигнальная ракета", "base_price": 100,
         "stats": "Освещение области 50м, 5 мин", "rarity": "common"},
        {"id": "C_DRUG_SYNTH", "name": "Синт-нейро «Прозрение»", "base_price": 6000,
         "stats": "+3 perception 5 ходов, риск зависимости 10%", "rarity": "rare"},
    ],
    "craft_materials": [
        {"id": "M_V3_TITANIUM", "name": "Титановый сплав", "base_price": 200,
         "stats": "Компонент для брони и мехов", "rarity": "uncommon"},
        {"id": "M_V3_CARBON_NANO", "name": "Углеродные нанотрубки", "base_price": 350,
         "stats": "Компонент для лёгких конструкций", "rarity": "uncommon"},
        {"id": "M_V3_BIOGEL", "name": "Биогель регенеративный", "base_price": 500,
         "stats": "Компонент для медпрепаратов и имплантов", "rarity": "rare"},
        {"id": "M_V3_QUANTUM_CHIP", "name": "Квантовый чип", "base_price": 800,
         "stats": "Компонент для высокотехнологичных устройств", "rarity": "rare"},
        {"id": "M_V3_PLASMA_CORE", "name": "Плазменное ядро", "base_price": 1200,
         "stats": "Компонент для плазменного оружия", "rarity": "epic"},
        {"id": "M_V3_SCRAP_REFINED", "name": "Очищенный лом", "base_price": 30,
         "stats": "Базовый материал для ремонта", "rarity": "common"},
        {"id": "M_V3_EXPLOSIVE_COMP", "name": "Взрывчатый компонент", "base_price": 150,
         "stats": "Компонент для гранат и мин", "rarity": "common"},
        {"id": "M_V3_NEURAL_FIBER", "name": "Нейроволокно", "base_price": 600,
         "stats": "Компонент для нейроимплантов", "rarity": "rare"},
        {"id": "M_V3_CRYO_FLUID", "name": "Крио-жидкость", "base_price": 100,
         "stats": "Охлаждающий компонент для оружия", "rarity": "common"},
        {"id": "M_V3_EXOTIC_ALLOY", "name": "Экзотический сплав", "base_price": 2000,
         "stats": "Редкий материал из внешней системы", "rarity": "legendary"},
    ],
    "ships": [
        {"id": "S_INTERCEPTOR", "name": "Перехватчик «Стилет»", "base_price": 120000,
         "stats": "Быстрый, 2 оружия, 2 груза, 1 пассажир, щит 1", "rarity": "uncommon"},
        {"id": "S_FREIGHTER", "name": "Грузовик «Муравей»", "base_price": 80000,
         "stats": "Медленный, без оружия, 50 груза, 4 пассажира", "rarity": "common"},
        {"id": "S_GUNSHIP", "name": "Канонерка «Коршун»", "base_price": 250000,
         "stats": "Средний, 4 оружия, 10 груза, 6 экипаж, щит 2", "rarity": "rare"},
        {"id": "S_STEALTH_SHIP", "name": "Стелс-корабль «Призрак»", "base_price": 300000,
         "stats": "Невидим для сканеров, 1 оружие, 5 груза, 2 экипаж", "rarity": "epic"},
        {"id": "S_MINING_VESSEL", "name": "Шахтёрский бот «Крот»", "base_price": 60000,
         "stats": "Буровое оборудование, 30 руды, 2 экипаж", "rarity": "common"},
        {"id": "S_LUXURY_YACHT", "name": "Яхта «Зенит»", "base_price": 500000,
         "stats": "Быстрый, без оружия, 5 груза, 8 пассажиров, +2 влияние", "rarity": "epic"},
    ],
    "property": [
        {"id": "P_WORKSHOP", "name": "Мастерская", "base_price": 40000,
         "stats": "Крафтинг-станция, хранилище 30, +1 к крафту", "rarity": "uncommon"},
        {"id": "P_SAFEHOUSE", "name": "Конспиративная квартира", "base_price": 15000,
         "stats": "Скрытая, хранилище 10, невидима для властей", "rarity": "uncommon"},
        {"id": "P_CLINIC", "name": "Подпольная клиника", "base_price": 50000,
         "stats": "Лечение, установка имплантов, хранилище 15", "rarity": "rare"},
        {"id": "P_BAR", "name": "Бар «Последний Причал»", "base_price": 70000,
         "stats": "Доход 500/нед, центр информации, +1 к слухам", "rarity": "rare"},
        {"id": "P_HANGAR", "name": "Ангар (станция)", "base_price": 30000,
         "stats": "Стоянка для 2 кораблей, базовый ремонт", "rarity": "uncommon"},
        {"id": "P_PENTHOUSE", "name": "Пентхаус «Олимп»", "base_price": 200000,
         "stats": "Жильё, хранилище 50, +3 влияние, секретный выход", "rarity": "epic"},
        {"id": "P_BUNKER", "name": "Подземный бункер", "base_price": 100000,
         "stats": "Укрытие, хранилище 40, оружейная, генератор", "rarity": "rare"},
    ],
}


# ════════════════════════════════════════════════════════════
#  MERGE FUNCTIONS  — V1 + V2 + V3
# ════════════════════════════════════════════════════════════

def get_all_origins():
    """Merges base ORIGINS + V3_ORIGINS."""
    from src.content.creation_data import ORIGINS
    merged = {o["id"]: o for o in ORIGINS}
    for o in V3_ORIGINS:
        if o["id"] not in merged:
            merged[o["id"]] = o
    return list(merged.values())

def get_all_formative_years():
    """Merges base FORMATIVE_YEARS + V3."""
    from src.content.creation_data import FORMATIVE_YEARS
    merged = {f["id"]: f for f in FORMATIVE_YEARS}
    for f in V3_FORMATIVE_YEARS:
        if f["id"] not in merged:
            merged[f["id"]] = f
    return list(merged.values())

def get_all_specializations():
    """Merges base SPECIALIZATIONS + V3."""
    from src.content.creation_data import SPECIALIZATIONS
    merged = {s["id"]: s for s in SPECIALIZATIONS}
    for s in V3_SPECIALIZATIONS:
        if s["id"] not in merged:
            merged[s["id"]] = s
    return list(merged.values())

def get_all_perks_v3():
    """Returns merged V1 + V2 + V3 perks."""
    from src.content.v2_legacy import get_all_perks
    merged = {p["id"]: p for p in get_all_perks()}
    for p in V3_PERKS:
        if p["id"] not in merged:
            merged[p["id"]] = p
    return list(merged.values())

def get_all_shop_items_v3():
    """Merges V1 + V2 + V3 shop items."""
    from src.content.v2_legacy import get_all_shop_items
    base = get_all_shop_items()
    for cat, items in V3_SHOP_ITEMS.items():
        if cat not in base:
            base[cat] = []
        existing_ids = {i["id"] for i in base[cat]}
        for item in items:
            if item["id"] not in existing_ids:
                base[cat].append(item)
    return base
