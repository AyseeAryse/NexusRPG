"""
Comprehensive character creation data for NEXUS RPG.
All origins, formative years, and specializations with full descriptions,
attribute/skill modifiers, starting credits, equipment, etc.
"""

ORIGINS = [
    # ═══ ЗЕМНЫЕ ═══
    {
        "id": "ORIGIN_EARTH_ELITE", "name": "Наследник Земной Элиты", "rarity": "редкое",
        "group": "Земля",
        "description": "Родились в элитном анклаве Земли, окружённые приватной охраной и лучшими технологиями. Высокое образование, дипломатические связи, но оторванность от реальной жизни.",
        "attr_mods": {"charisma": 1, "intelligence": 1, "endurance": -1},
        "skill_mods": {"education": 2, "diplomacy": 1, "survival": -1},
        "credits": 100000, "influence": 10,
    },
    {
        "id": "ORIGIN_EARTH_SLUMS", "name": "Дитя Трущоб", "rarity": "обычное",
        "group": "Земля",
        "description": "Выжили в нижних уровнях города, где неон гасится пылью и страхом. Закалены жизнью на улицах, но образование минимальное.",
        "attr_mods": {"endurance": 2, "dexterity": 1, "intelligence": -1},
        "skill_mods": {"survival": 2, "stealth": 1, "education": -1},
        "credits": 1000,
    },
    {
        "id": "ORIGIN_EARTH_CORP_HEIR", "name": "Корпоративный Наследник", "rarity": "редкое",
        "group": "Земля",
        "description": "Семья владеет акциями крупных корпораций. Престиж, власть и огромная ответственность. Вы привыкли к роскоши и интригам.",
        "attr_mods": {"charisma": 2},
        "skill_mods": {"negotiation": 2, "bureaucracy": 1},
        "credits": 250000, "influence": 15,
    },
    {
        "id": "ORIGIN_EARTH_JOURNALIST", "name": "Журналист-Расследователь", "rarity": "необычное",
        "group": "Земля",
        "description": "Родители — известные журналисты. Научились искать правду в мире корпоративной лжи. У вас есть контакты в самых неожиданных местах.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"education": 2, "negotiation": 1, "stealth": 1},
        "credits": 35000,
    },
    {
        "id": "ORIGIN_EARTH_MILITARY", "name": "Военный Отпрыск", "rarity": "обычное",
        "group": "Земля",
        "description": "Выросли на военных базах Земли, окружённые дисциплиной и тренировками. Военная жизнь — единственное, что вы знаете.",
        "attr_mods": {"strength": 1, "willpower": 1},
        "skill_mods": {"combat": 1, "survival": 1},
        "credits": 45000,
    },
    {
        "id": "ORIGIN_EARTH_DIPLOMAT", "name": "Дипломат Земли", "rarity": "необычное",
        "group": "Земля",
        "description": "Представитель Объединённого Правительства Земли в межпланетных отношениях. Мастер переговоров и политических интриг.",
        "attr_mods": {"charisma": 2, "intelligence": 1},
        "skill_mods": {"diplomacy": 2, "law": 1, "bureaucracy": 1},
        "credits": 80000, "influence": 8,
    },
    {
        "id": "ORIGIN_EARTH_HACKER", "name": "Хакер-Активист Земли", "rarity": "необычное",
        "group": "Земля",
        "description": "Член подпольной группы кибер-активистов, борющихся с корпоративным контролем. Виртуозное владение кодом — ваш главный козырь.",
        "attr_mods": {"intelligence": 2, "endurance": -1},
        "skill_mods": {"hacking": 3, "technology": 1, "criminal": 1},
        "credits": 15000,
    },
    {
        "id": "ORIGIN_EARTH_REFUGEE", "name": "Беженец из Лагеря", "rarity": "обычное",
        "group": "Земля",
        "description": "Пережили худшее, что может предложить человечество. Климатические катастрофы отняли дом, но не сломили дух.",
        "attr_mods": {"willpower": 2, "endurance": 1},
        "skill_mods": {"survival": 3, "stealth": 1},
        "credits": 500,
    },
    # ═══ МАРС ═══
    {
        "id": "ORIGIN_MARS_MILITARY", "name": "Потомок Марсианских Солдат", "rarity": "обычное",
        "group": "Марс",
        "description": "Привыкли к дисциплине и симуляциям боевых учений в республиканской академии. Марсианская военная школа закалила ваш характер.",
        "attr_mods": {"strength": 1, "endurance": 1, "willpower": 1},
        "skill_mods": {"combat": 1, "piloting": 1},
        "credits": 35000, "influence": 5,
    },
    {
        "id": "ORIGIN_MARS_SCIENTIST", "name": "Учёный Марса", "rarity": "необычное",
        "group": "Марс",
        "description": "Родились среди терраформеров и исследователей. Для вас наука — это всё. Лаборатория была вашей детской площадкой.",
        "attr_mods": {"intelligence": 2, "tech_empathy": 1, "charisma": -1},
        "skill_mods": {"technology": 2, "engineering": 1},
        "credits": 50000, "influence": 3,
    },
    {
        "id": "ORIGIN_MARS_REBEL", "name": "Марсианский Повстанец", "rarity": "редкое",
        "group": "Марс",
        "description": "Семья участвовала в борьбе за независимость Марса от Земли. Вы выросли с оружием в руках и идеалами свободы в сердце.",
        "attr_mods": {"willpower": 1, "endurance": 1},
        "skill_mods": {"combat": 2, "stealth": 2, "survival": 1},
        "credits": 8000,
    },
    {
        "id": "ORIGIN_MARS_ENGINEER", "name": "Марсианский Инженер-Терраформер", "rarity": "необычное",
        "group": "Марс",
        "description": "Родители работали над преобразованием атмосферы Марса. Инженерная мысль течёт в ваших венах.",
        "attr_mods": {"intelligence": 1, "tech_empathy": 1},
        "skill_mods": {"engineering": 3, "technology": 1, "survival": 1},
        "credits": 55000,
    },
    {
        "id": "ORIGIN_MARS_TUNNELER", "name": "Марсианский Туннельный Крыс", "rarity": "обычное",
        "group": "Марс",
        "description": "Выросли в подземных городах, научились выживать в замкнутых пространствах. Знаете каждый коридор и вентиляцию.",
        "attr_mods": {"dexterity": 1, "endurance": 1},
        "skill_mods": {"survival": 2, "stealth": 2, "engineering": 1},
        "credits": 5000,
    },
    # ═══ ПОЯС АСТЕРОИДОВ ═══
    {
        "id": "ORIGIN_BELT_SMUGGLER", "name": "Потомок Контрабандистов Пояса", "rarity": "необычное",
        "group": "Пояс астероидов",
        "description": "Семья жила тайной торговлей во Внешней системе. Вы научились летать раньше, чем ходить.",
        "attr_mods": {"reflexes": 2, "dexterity": 1},
        "skill_mods": {"piloting": 2, "criminal": 2},
        "credits": 25000,
    },
    {
        "id": "ORIGIN_BELT_MINER", "name": "Шахтёр с Цереры", "rarity": "обычное",
        "group": "Пояс астероидов",
        "description": "Добывали руду в недрах астероида, починив всё подручными средствами. Тяжёлый труд сделал вас крепким и находчивым.",
        "attr_mods": {"strength": 2, "endurance": 1},
        "skill_mods": {"engineering": 1, "survival": 1},
        "credits": 12000,
    },
    {
        "id": "ORIGIN_BELT_SALVAGER", "name": "Космический Утилизатор", "rarity": "необычное",
        "group": "Пояс астероидов",
        "description": "Специализировались на утилизации обломков кораблей и станций. Каждый выход в открытый космос мог стать последним.",
        "attr_mods": {"tech_empathy": 1, "reflexes": 1},
        "skill_mods": {"piloting": 2, "technology": 2, "engineering": 1},
        "credits": 18000,
    },
    {
        "id": "ORIGIN_BELT_NOMAD", "name": "Кочевник-Шахтер", "rarity": "обычное",
        "group": "Пояс астероидов",
        "description": "Кочующие шахтёрские корабли — весь ваш мир. Знаете навигацию по звёздам и как экономить каждый литр кислорода.",
        "attr_mods": {"endurance": 1, "willpower": 1},
        "skill_mods": {"piloting": 1, "survival": 2, "engineering": 1},
        "credits": 8000,
    },
    {
        "id": "ORIGIN_BELT_TRADER", "name": "Семья Межзвёздных Торговцев", "rarity": "необычное",
        "group": "Пояс астероидов",
        "description": "Торговые рейсы к дальним колониям. Вы знаете цену каждому товару и умеете торговаться с любым существом.",
        "attr_mods": {"charisma": 1, "intelligence": 1},
        "skill_mods": {"negotiation": 2, "piloting": 1, "diplomacy": 1},
        "credits": 60000,
    },
    # ═══ ВНЕШНЯЯ СИСТЕМА ═══
    {
        "id": "ORIGIN_OUTER_EUROPA", "name": "Глубоководный Исследователь Европы", "rarity": "редкое",
        "group": "Внешняя система",
        "description": "Выросли на спутнике Юпитера, исследуя подлёдный океан. Подводные базы и океанические экспедиции — ваша стихия.",
        "attr_mods": {"intelligence": 1, "willpower": 1, "endurance": -1},
        "skill_mods": {"biology": 2, "technology": 1, "survival": 1},
        "credits": 40000,
    },
    {
        "id": "ORIGIN_OUTER_TITAN", "name": "Метановый Фермер Титана", "rarity": "необычное",
        "group": "Внешняя система",
        "description": "Родители добывали метан в атмосфере Титана для топлива. Суровые условия воспитали стойкость и изобретательность.",
        "attr_mods": {"endurance": 2},
        "skill_mods": {"piloting": 2, "engineering": 1, "survival": 1},
        "credits": 32000,
    },
    {
        "id": "ORIGIN_OUTER_GANYMEDE", "name": "Исследователь Ганимеда", "rarity": "редкое",
        "group": "Внешняя система",
        "description": "Изучали биохимию в подледных лабораториях. Самая передовая научная колония человечества стала вашим домом.",
        "attr_mods": {"intelligence": 3, "tech_empathy": 1, "endurance": -1},
        "skill_mods": {"medicine": 1, "technology": 2, "biology": 1},
        "credits": 80000, "influence": 5,
    },
    {
        "id": "ORIGIN_OUTER_VESTA", "name": "Военная База Весты", "rarity": "необычное",
        "group": "Внешняя система",
        "description": "Секретная подготовка элиты на Весте. Вас тренировали быть лучшими — или быть мёртвыми.",
        "attr_mods": {"strength": 1, "reflexes": 2, "charisma": -1},
        "skill_mods": {"combat": 2, "stealth": 1, "piloting": 1},
        "credits": 30000,
    },
    # ═══ УНИКАЛЬНЫЕ ═══
    {
        "id": "ORIGIN_UNIQUE_MAGNATE", "name": "Технологический Магнат", "rarity": "легендарное",
        "group": "Уникальные",
        "description": "Молодой миллиардер, создавший революционную технологию. Ваше имя знают на каждой станции системы. Но изоляция в мире богатства оставила пробелы в уличных навыках.",
        "attr_mods": {"intelligence": 1, "charisma": 1, "endurance": -1},
        "skill_mods": {"technology": 2, "negotiation": 1, "bureaucracy": 1},
        "credits": 500000, "influence": 30,
    },
    {
        "id": "ORIGIN_UNIQUE_NOMAD", "name": "Ребёнок Космических Кочевников", "rarity": "редкое",
        "group": "Уникальные",
        "description": "Родились на борту торгового корабля, странствующего по системе. Космос — ваш единственный дом.",
        "attr_mods": {"dexterity": 1, "reflexes": 1},
        "skill_mods": {"piloting": 2, "negotiation": 1, "survival": 1},
        "credits": 28000,
    },
    {
        "id": "ORIGIN_UNIQUE_EXPERIMENT", "name": "Корпоративный Эксперимент", "rarity": "легендарное",
        "group": "Уникальные",
        "description": "Вы — продукт секретной корпоративной программы. Генетические модификации дали силу, но забрали часть человечности.",
        "attr_mods": {"strength": 2, "reflexes": 2, "endurance": 1, "charisma": -2},
        "skill_mods": {"combat": 2, "technology": 1},
        "credits": 5000,
    },
    {
        "id": "ORIGIN_UNIQUE_AI_CHILD", "name": "Воспитанник ИИ", "rarity": "легендарное",
        "group": "Уникальные",
        "description": "Ребёнок-сирота, которого вырастил автономный ИИ заброшенной космической станции. Ваше понимание машин — на грани сверхъестественного.",
        "attr_mods": {"intelligence": 2, "tech_empathy": 3, "charisma": -2},
        "skill_mods": {"hacking": 2, "technology": 2, "engineering": 1},
        "credits": 10000,
    },
]


FORMATIVE_YEARS = [
    # ═══ ВОЕННЫЕ / БОЕВЫЕ ═══
    {
        "id": "FY_MARS_ACADEMY", "name": "Военная Академия Марса",
        "group": "Военные",
        "description": "Четыре года жёсткой муштры, тактических симуляций и боевых учений. Вы научились стрелять, командовать и выживать.",
        "attr_mods": {"strength": 1, "willpower": 1},
        "skill_mods": {"combat": 2, "technology": 1},
    },
    {
        "id": "FY_SLUMS_GANGWAR", "name": "Война банд в трущобах",
        "group": "Криминальные",
        "description": "Территориальные войны научили вас драться не по правилам. Шрамы — как карта вашей юности.",
        "attr_mods": {"endurance": 1},
        "skill_mods": {"combat": 2, "stealth": 1, "criminal": 1},
    },
    {
        "id": "FY_MILITARY_VOLUNTEER", "name": "Добровольная военная подготовка",
        "group": "Военные",
        "description": "Записались добровольцем в планетарную милицию. Дисциплина и товарищество стали вашей второй натурой.",
        "attr_mods": {"willpower": 1},
        "skill_mods": {"combat": 1, "survival": 1, "diplomacy": 1},
    },
    # ═══ КОРПОРАТИВНЫЕ ═══
    {
        "id": "FY_CORP_INTERNSHIP", "name": "Корпоративная стажировка",
        "group": "Корпоративные",
        "description": "Стажировка в мегакорпорации открыла глаза на мир корпоративных интриг. Вы научились составлять отчёты, вести переговоры и лавировать между боссами.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"bureaucracy": 2, "negotiation": 1},
    },
    {
        "id": "FY_CORP_ESPIONAGE", "name": "Свидетель корпоративного шпионажа",
        "group": "Корпоративные",
        "description": "Случайно стали свидетелем промышленного шпионажа. Это научило вас быть осторожным и замечать ложь.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"stealth": 1, "hacking": 1, "education": 1},
    },
    {
        "id": "FY_FAMILY_BUSINESS", "name": "Наследование семейного бизнеса",
        "group": "Корпоративные",
        "description": "В юном возрасте взяли на себя управление семейным делом. Ранняя ответственность закалила характер и обострила деловую хватку.",
        "attr_mods": {"charisma": 1},
        "skill_mods": {"negotiation": 2, "bureaucracy": 1},
    },
    # ═══ АКАДЕМИЧЕСКИЕ ═══
    {
        "id": "FY_GIFTED_PROGRAM", "name": "Программа для одарённых детей",
        "group": "Академические",
        "description": "Ваш IQ открыл двери в элитную академию. Ускоренное обучение, научные олимпиады и первые патенты ещё до совершеннолетия.",
        "attr_mods": {"intelligence": 2},
        "skill_mods": {"education": 2, "technology": 1},
    },
    {
        "id": "FY_SCIENTIFIC_DISCOVERY", "name": "Участие в научном открытии",
        "group": "Академические",
        "description": "Помогали исследовательской группе и стали соавтором важного открытия. Мир науки распахнул перед вами двери.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"biology": 1, "technology": 1, "education": 1},
    },
    {
        "id": "FY_YOUNG_HACKER", "name": "Признание как юный хакер",
        "group": "Технологические",
        "description": "В 14 лет взломали корпоративную базу данных. Арест, условный срок — и репутация в хакерском подполье.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"hacking": 2, "technology": 1, "criminal": 1},
    },
    # ═══ КРИМИНАЛЬНЫЕ ═══
    {
        "id": "FY_STREET_LIFE", "name": "Жизнь на улице",
        "group": "Криминальные",
        "description": "Беспризорная юность научила воровать, прятаться и не доверять никому. Улица была жестоким, но эффективным учителем.",
        "attr_mods": {"dexterity": 1, "endurance": 1},
        "skill_mods": {"stealth": 2, "criminal": 1, "survival": 1},
    },
    {
        "id": "FY_SMUGGLING_RUNS", "name": "Контрабандные рейсы",
        "group": "Криминальные",
        "description": "Подрабатывали курьером для контрабандистов Пояса. Научились летать быстро и не задавать вопросов.",
        "attr_mods": {"reflexes": 1},
        "skill_mods": {"piloting": 2, "criminal": 1},
    },
    # ═══ КАТАСТРОФЫ ═══
    {
        "id": "FY_COSMIC_CATASTROPHE", "name": "Пережили космическую катастрофу",
        "group": "Катастрофы",
        "description": "Разгерметизация станции, взрыв реактора или столкновение с астероидом — вы выжили, когда другие погибли. Это оставило шрамы, но закалило.",
        "attr_mods": {"willpower": 2, "endurance": 1},
        "skill_mods": {"survival": 2, "medicine": 1},
    },
    {
        "id": "FY_FAMILY_BANKRUPTCY", "name": "Банкротство семьи",
        "group": "Катастрофы",
        "description": "Из роскоши — в нищету за одну ночь. Крах семейного бизнеса научил ценить каждый кредит и не доверять внешнему блеску.",
        "attr_mods": {"willpower": 1},
        "skill_mods": {"survival": 1, "negotiation": 1, "criminal": 1},
    },
    # ═══ СОЦИАЛЬНЫЕ ═══
    {
        "id": "FY_DIPLOMATIC_MISSION", "name": "Участие в дипломатической миссии",
        "group": "Социальные",
        "description": "Сопровождали родителей или наставника в дипломатической миссии. Научились понимать политику и видеть за словами скрытые мотивы.",
        "attr_mods": {"charisma": 1},
        "skill_mods": {"diplomacy": 2, "law": 1},
    },
    {
        "id": "FY_SPORTS_ACHIEVEMENTS", "name": "Спортивные достижения",
        "group": "Социальные",
        "description": "Чемпион колонии по гравитационному боксу или нулевому-G акробатике. Тело — ваш главный инструмент.",
        "attr_mods": {"strength": 1, "dexterity": 1, "endurance": 1},
        "skill_mods": {"combat": 1},
    },
    {
        "id": "FY_ARTISTIC_TALENT", "name": "Признание художественного таланта",
        "group": "Социальные",
        "description": "Ваши работы выставлялись в галереях от Земли до Ганимеда. Творчество научило видеть красоту и манипулировать эмоциями.",
        "attr_mods": {"charisma": 2},
        "skill_mods": {"diplomacy": 1, "negotiation": 1},
    },
    # ═══ ТЕХНОЛОГИЧЕСКИЕ ═══
    {
        "id": "FY_ROBOT_BUILDER", "name": "Собирали роботов с детства",
        "group": "Технологические",
        "description": "Первого дрона собрали в 10 лет из деталей мусорника. К 18 у вас была мастерская и десяток патентов.",
        "attr_mods": {"tech_empathy": 2},
        "skill_mods": {"engineering": 2, "technology": 1},
    },
    {
        "id": "FY_CYBERNETIC_IMPLANT", "name": "Ранняя кибернетическая модификация",
        "group": "Технологические",
        "description": "Первый имплант поставили в 15 — нейроинтерфейс для ускоренного обучения. Побочные эффекты: мигрени и ощущение чужеродности.",
        "attr_mods": {"intelligence": 1, "tech_empathy": 1},
        "skill_mods": {"hacking": 1, "technology": 1},
    },
    # ═══ МЕДИЦИНСКИЕ ═══
    {
        "id": "FY_PLAGUE_SURVIVOR", "name": "Пережили космическую чуму",
        "group": "Катастрофы",
        "description": "Эпидемия на станции. Вы помогали медикам и видели смерть вблизи. После выздоровления решили, что жизнь слишком коротка для страха.",
        "attr_mods": {"willpower": 1, "endurance": 1},
        "skill_mods": {"medicine": 2, "biology": 1},
    },
    {
        "id": "FY_MEDICAL_APPRENTICE", "name": "Ученик полевого медика",
        "group": "Медицинские",
        "description": "Подрабатывали ассистентом хирурга в трущобных клиниках. Научились зашивать раны и ставить капельницы в полевых условиях.",
        "attr_mods": {"intelligence": 1},
        "skill_mods": {"medicine": 2, "biology": 1},
    },
    # ═══ КОСМИЧЕСКИЕ ═══
    {
        "id": "FY_FIRST_SPACEFLIGHT", "name": "Первый одиночный полёт",
        "group": "Космические",
        "description": "В 16 лет угнали отцовский шаттл и слетали до ближайшей станции. Нагоняй был страшный, но с тех пор космос — ваша стихия.",
        "attr_mods": {"reflexes": 1, "dexterity": 1},
        "skill_mods": {"piloting": 2, "engineering": 1},
    },
    {
        "id": "FY_ALIEN_ARTIFACT", "name": "Нашли инопланетный артефакт",
        "group": "Космические",
        "description": "На заброшенном астероиде обнаружили объект нечеловеческого происхождения. С тех пор вас преследуют странные сны и ощущение чужого присутствия.",
        "attr_mods": {"intelligence": 1, "willpower": 1},
        "skill_mods": {"technology": 1, "education": 1, "biology": 1},
    },
    {
        "id": "FY_LOVE_TRIANGLE", "name": "Любовный треугольник",
        "group": "Социальные",
        "description": "Бурный роман, предательство и разбитое сердце. Эмоциональные шрамы научили разбираться в людях и защищать своё сердце.",
        "attr_mods": {"charisma": 1},
        "skill_mods": {"negotiation": 1, "stealth": 1},
    },
    # ═══ ДОПОЛНИТЕЛЬНЫЕ ═══
    {
        "id": "FY_UNDERGROUND_FIGHTS", "name": "Подпольные бои",
        "group": "Криминальные",
        "description": "С 14 лет дрались на подпольных рингах в нижних уровнях. Шрамы, сломанный нос и навсегда перебитые костяшки — но зато научились выживать.",
        "attr_mods": {"endurance": 1, "strength": 1},
        "skill_mods": {"combat": 2, "survival": 1},
    },
    {
        "id": "FY_MERCHANT_FLEET", "name": "Каюта на торговом корабле",
        "group": "Космические",
        "description": "Выросли на борту торгового судна, курсирующего между станциями Пояса. Научились торговаться, чинить трубы и спать при нулевой гравитации.",
        "attr_mods": {"dexterity": 1},
        "skill_mods": {"piloting": 1, "engineering": 1, "negotiation": 1},
    },
    {
        "id": "FY_ORPHANAGE_AI", "name": "Воспитание в приюте ИИ",
        "group": "Технологические",
        "description": "Автоматизированный приют, где единственными «родителями» были обучающие программы. Гениальная база знаний, но пробелы в человеческих эмоциях.",
        "attr_mods": {"intelligence": 2},
        "skill_mods": {"technology": 1, "education": 1},
    },
    {
        "id": "FY_MINING_ACCIDENT", "name": "Авария на шахте",
        "group": "Катастрофы",
        "description": "Обвал в марсианской шахте — неделя в темноте, рацион на троих, кислород на двоих. Выжили, но с тех пор боитесь тесных пространств и цените каждый вдох.",
        "attr_mods": {"willpower": 1, "endurance": 1},
        "skill_mods": {"survival": 2, "engineering": 1},
    },
    {
        "id": "FY_ELITE_BOARDING_SCHOOL", "name": "Элитная школа-интернат",
        "group": "Академические",
        "description": "Лучшие репетиторы, костюмы от Мицубиси-Армани и однокурсники из семей членов Совета ООН. Связи на всю жизнь — и пара скелетов в шкафу.",
        "attr_mods": {"charisma": 1, "intelligence": 1},
        "skill_mods": {"diplomacy": 1, "education": 1},
    },
    {
        "id": "FY_PIRATE_CAPTIVE", "name": "Пленник космических пиратов",
        "group": "Криминальные",
        "description": "Полгода в плену у пиратов-утилизаторов. Научились их языку, повадкам и в итоге сбежали, прихватив их карты маршрутов.",
        "attr_mods": {"reflexes": 1},
        "skill_mods": {"stealth": 1, "survival": 1, "criminal": 1},
    },
    {
        "id": "FY_MILITARY_BRAT", "name": "Ребёнок военной базы",
        "group": "Военные",
        "description": "Росли среди казарм, плацев и оружейных складов. К 12 годам разбирали и собирали автомат вслепую. Дисциплина в крови.",
        "attr_mods": {"endurance": 1},
        "skill_mods": {"combat": 1, "survival": 1, "stealth": 1},
    },
    {
        "id": "FY_MEDIA_SENSATION", "name": "Медийная сенсация",
        "group": "Социальные",
        "description": "В 15 лет случайно записали на видео коррупцию чиновника. Стали героями сети на неделю — а потом целью для тех, кого разоблачили.",
        "attr_mods": {"charisma": 1},
        "skill_mods": {"negotiation": 1, "stealth": 1, "criminal": 1},
    },
    {
        "id": "FY_LAB_SUBJECT", "name": "Подопытный в лаборатории",
        "group": "Медицинские",
        "description": "«Добровольное» участие в экспериментах корпорации Протоген. Инъекции, тесты, мониторинг 24/7. Сбежали, но кое-что в организме изменилось навсегда.",
        "attr_mods": {"endurance": 1, "willpower": 1},
        "skill_mods": {"medicine": 1, "biology": 1},
    },
    {
        "id": "FY_STATION_MECHANIC", "name": "Механик орбитальной станции",
        "group": "Технологические",
        "description": "С 13 лет помогали отцу чинить системы жизнеобеспечения на станции Тихо. Знаете каждый клапан и каждую трубу — и цену ошибки при ремонте.",
        "attr_mods": {"dexterity": 1},
        "skill_mods": {"engineering": 2, "technology": 1},
    },
]


SPECIALIZATIONS = [
    # ═══ ТЕХНИЧЕСКИЕ ═══
    {
        "id": "SPEC_HACKER", "name": "Хакер",
        "group": "Технические",
        "description": "Мастер цифрового мира. Взламываете сети, обходите защиту и крадёте данные — ваш мозг и нейроинтерфейс опаснее любого оружия.",
        "skill_mods": {"hacking": 3, "technology": 2},
        "equipment": ["Портативный хакерский комплект", "Зашифрованный коммлинк", "Нейроинтерфейс"],
    },
    {
        "id": "SPEC_ENGINEER", "name": "Инженер",
        "group": "Технические",
        "description": "Техсистемы и ремонт — ваша стихия. Можете починить реактор скотчем и проволокой, а собрать дрона — с закрытыми глазами.",
        "skill_mods": {"engineering": 3, "technology": 2},
        "equipment": ["Инженерный набор", "Диагностический сканер", "Ремкомплект"],
    },
    {
        "id": "SPEC_SCIENTIST", "name": "Учёный",
        "group": "Технические",
        "description": "Исследователь и аналитик. Вы видите закономерности там, где другие видят хаос. Данные — ваше оружие.",
        "skill_mods": {"education": 2, "biology": 2, "technology": 1},
        "equipment": ["Лабораторный набор", "Анализатор данных", "Научный журнал"],
    },
    {
        "id": "SPEC_QUANTUM_HACKER", "name": "Квантовый хакер",
        "group": "Технические",
        "description": "Специалист по квантовым компьютерам и криптографии нового поколения. Обычные хакеры ломают пароли — вы ломаете реальность.",
        "skill_mods": {"hacking": 3, "technology": 1, "education": 1},
        "equipment": ["Квантовый компьютер", "Шифровальные ключи", "Нейроинтерфейс v2"],
    },
    # ═══ БОЕВЫЕ ═══
    {
        "id": "SPEC_SOLDIER", "name": "Солдат",
        "group": "Боевые",
        "description": "Военный боец, обученный убивать. Огнестрельное оружие, тактика, выживание на поле боя — ваш хлеб.",
        "skill_mods": {"combat": 3, "survival": 1, "piloting": 1},
        "equipment": ["Штурмовая винтовка", "Бронежилет", "Медкит"],
    },
    {
        "id": "SPEC_ASSASSIN", "name": "Корпоративный убийца",
        "group": "Боевые",
        "description": "Профессиональный киллер на службе мегакорпораций. Тихо, чисто, без следов — ваш фирменный стиль.",
        "skill_mods": {"combat": 2, "stealth": 3},
        "equipment": ["Бесшумное оружие", "Корпоративные документы", "Набор ядов"],
    },
    {
        "id": "SPEC_BOUNTY_HUNTER", "name": "Охотник за головами",
        "group": "Боевые",
        "description": "Цель объявлена — цель будет найдена. Вы выслеживаете беглецов по всей системе за хорошую награду.",
        "skill_mods": {"combat": 2, "stealth": 1, "piloting": 1, "criminal": 1},
        "equipment": ["Плазменный пистолет", "Трекер-маяк", "Наручники", "Бронежилет"],
    },
    # ═══ СОЦИАЛЬНЫЕ ═══
    {
        "id": "SPEC_NEGOTIATOR", "name": "Переговорщик",
        "group": "Социальные",
        "description": "Дипломат и медиатор. Ваши слова — оружие мощнее любого бластера. Вы можете убедить врага стать другом.",
        "skill_mods": {"negotiation": 3, "diplomacy": 2},
        "equipment": ["Дипимунитет", "Переводчик", "Элитный костюм"],
    },
    {
        "id": "SPEC_TRADER", "name": "Торговец",
        "group": "Социальные",
        "description": "Коммерция и сети. Знаете цену каждому товару от Земли до Плутона. Связи — ваш главный капитал.",
        "skill_mods": {"negotiation": 2, "bureaucracy": 1, "diplomacy": 1, "piloting": 1},
        "equipment": ["Торговая лицензия", "Кредитная карта VIP", "Каталог товаров"],
    },
    {
        "id": "SPEC_ARTIST", "name": "Артист",
        "group": "Социальные",
        "description": "Влияние и сцена. Музыкант, актёр или визуальный художник — ваше искусство открывает любые двери.",
        "skill_mods": {"diplomacy": 2, "negotiation": 2, "education": 1},
        "equipment": ["Сценический костюм", "Аудио-система", "Фан-база"],
    },
    {
        "id": "SPEC_FIXER", "name": "Фиксер",
        "group": "Социальные",
        "description": "Посредник теневого мира. Вы знаете всех и всё, и за правильную цену можете организовать что угодно.",
        "skill_mods": {"negotiation": 2, "criminal": 2, "stealth": 1},
        "equipment": ["Зашифрованный телефон", "Сеть контактов", "Поддельные документы"],
    },
    # ═══ ПИЛОТЫ ═══
    {
        "id": "SPEC_PILOT", "name": "Пилот",
        "group": "Пилоты",
        "description": "Ас пилотирования. От шахтёрских баржей до истребителей — вы можете управлять чем угодно.",
        "skill_mods": {"piloting": 3, "engineering": 1, "survival": 1},
        "equipment": ["Доступ к личному кораблю", "Навигационный компьютер", "Лётная куртка"],
    },
    {
        "id": "SPEC_SMUGGLER", "name": "Контрабандист",
        "group": "Пилоты",
        "description": "Быстрый корабль, тайные маршруты и холодные нервы. Вы доставите что угодно куда угодно — без вопросов.",
        "skill_mods": {"piloting": 2, "criminal": 2, "stealth": 1},
        "equipment": ["Быстрый корабль с тайником", "Сканер патрулей", "Фальшивые накладные"],
    },
    # ═══ МЕДИЦИНСКИЕ ═══
    {
        "id": "SPEC_MEDIC", "name": "Медик",
        "group": "Медицинские",
        "description": "Специалист по медицине. От полевой хирургии до кибернетических имплантов — вы спасаете жизни.",
        "skill_mods": {"medicine": 3, "biology": 1, "technology": 1},
        "equipment": ["Медицинский сканер", "Хирургический набор", "Стимпаки x5"],
    },
    {
        "id": "SPEC_GENE_SCULPTOR", "name": "Генный скульптор",
        "group": "Медицинские",
        "description": "Мастер генетических модификаций и биологического дизайна. Создаёте жизнь по чертежам.",
        "skill_mods": {"biology": 3, "medicine": 2},
        "equipment": ["Генетический сканер", "Био-лаборатория", "Образцы генов"],
    },
    # ═══ РАЗВЕДКА ═══
    {
        "id": "SPEC_SPY", "name": "Шпион",
        "group": "Разведка",
        "description": "Скрытность и информация. Двойная жизнь — ваша норма. Никто не знает вашего настоящего имени.",
        "skill_mods": {"stealth": 3, "hacking": 1, "diplomacy": 1},
        "equipment": ["Камуфляж", "Жучки-прослушки", "Поддельные документы"],
    },
    {
        "id": "SPEC_INVESTIGATOR", "name": "Детектив",
        "group": "Разведка",
        "description": "Частный сыщик космической эры. Находите людей, раскрываете заговоры и копаете до истины.",
        "skill_mods": {"education": 2, "stealth": 1, "hacking": 1, "negotiation": 1},
        "equipment": ["Детективный набор", "Базы данных", "Замаскированная камера"],
    },
    {
        "id": "SPEC_VOID_PRIEST", "name": "Жрец Пустоты",
        "group": "Уникальные",
        "description": "Духовный лидер космических культов и мистических сект. Ваша вера — в бездну между звёзд.",
        "skill_mods": {"diplomacy": 2, "education": 1, "medicine": 1, "negotiation": 1},
        "equipment": ["Религиозные артефакты", "Ритуальные одеяния", "Медитативные препараты"],
    },
    {
        "id": "SPEC_MEMORY_THIEF", "name": "Похититель воспоминаний",
        "group": "Уникальные",
        "description": "Эксперт по извлечению и изменению человеческих воспоминаний. Вы крадёте не вещи — вы крадёте саму суть людей.",
        "skill_mods": {"hacking": 2, "medicine": 1, "stealth": 1, "technology": 1},
        "equipment": ["Экстрактор памяти", "Нейро-препараты", "Мозговой сканер"],
    },

    {
        "id": "SPEC_DRONE_OPERATOR", "name": "Оператор дронов",
        "group": "Технические",
        "description": "Управление роем боевых и грузовых дронов на расстоянии",
        "skill_mods": {"drones": 3, "combat": 2, "sensor_operations": 1},
        "equipment": ["Пульт роя", "Запасные батареи", "Ремонтный набор"],
    },
    {
        "id": "SPEC_AI_WHISPERER", "name": "Шепчущий ИИ",
        "group": "Технические",
        "description": "Договориться с ограниченным ИИ там, где люди бессильны",
        "skill_mods": {"ai_interface": 3, "hacking": 2, "negotiation": 1},
        "equipment": ["Квантовый терминал", "Нейроинтерфейс", "Библиотека промптов"],
    },
    {
        "id": "SPEC_FABRICATOR", "name": "Фабрикатор",
        "group": "Технические",
        "description": "Печатает что угодно из чего угодно — почти",
        "skill_mods": {"fabrication_3d": 3, "weapon_smithing": 2, "accounting_finance": 1},
        "equipment": ["Портативная фабрика", "Каталог чертежей", "Материалы"],
    },
    {
        "id": "SPEC_SIGNAL_GHOST", "name": "Призрак эфира",
        "group": "Технические",
        "description": "Перехватывает и глушит любую связь в радиусе",
        "skill_mods": {"comms_jamming": 3, "crypto_analysis": 2, "stealth": 1},
        "equipment": ["Перехватчик", "Антенна-зонт", "Глушилка"],
    },
    {
        "id": "SPEC_ROBOTICS_SURGEON", "name": "Хирург роботов",
        "group": "Технические",
        "description": "Чинит то, что чинить нельзя — и улучшает",
        "skill_mods": {"robotics": 3, "electronics_repair": 2, "implant_surgery_calibration": 1},
        "equipment": ["Микроманипуляторы", "Диагностический модуль", "Запчасти"],
    },
    {
        "id": "SPEC_SHIP_ENGINEER", "name": "Корабельный инженер",
        "group": "Технические",
        "description": "Корабль — его тело: системы, пробеги, перегрузки",
        "skill_mods": {"ship_systems": 3, "vehicle_maintenance": 2, "engineering": 1},
        "equipment": ["Инструментальный пояс", "Схемы кораблей", "Запас деталей"],
    },
    {
        "id": "SPEC_TECH_ARCHAEOLOGIST", "name": "Техноархеолог",
        "group": "Технические",
        "description": "Оживляет технологии мёртвых эпох",
        "skill_mods": {"archaeology": 3, "electronics_repair": 2, "tailoring_gear": 1},
        "equipment": ["Копалка артефактов", "Анализатор сплавов", "Каталог эпох"],
    },
    {
        "id": "SPEC_SNIPER_SPECIALIST", "name": "Снайпер-специалист",
        "group": "Боевые",
        "description": "Один выстрел — один контракт. Дистанция решает",
        "skill_mods": {"sniping": 3, "sensor_operations": 2, "evasion": 1},
        "equipment": ["Снайперская винтовка", "Дальномер", "Маскировочная сеть"],
    },
    {
        "id": "SPEC_CQB_MASTER", "name": "Мастер CQB",
        "group": "Боевые",
        "description": "Коридоры, шлюзы, теснота — его территория",
        "skill_mods": {"close_quarters": 3, "boarding_tactics": 2, "first_aid_combat": 1},
        "equipment": ["Дробовик", "Тактическая броня", "Стробоскопы"],
    },
    {
        "id": "SPEC_HEAVY_ORDNANCE", "name": "Специалист тяжёлых систем",
        "group": "Боевые",
        "description": "Тяжёлая броня, турели, ракеты — медленно и необратимо",
        "skill_mods": {"heavy_weapons": 3, "armor_operation": 2, "turret_gunnery": 1},
        "equipment": ["Экзоскелет", "Пусковая установка", "Реактивная броня"],
    },
    {
        "id": "SPEC_VOID_MARINE", "name": "Пустотный морпех",
        "group": "Боевые",
        "description": "Бой в вакууме и нуль-G без права на ошибку",
        "skill_mods": {"zero_g_combat": 3, "vacuum_ops": 2, "heavy_weapons": 1},
        "equipment": ["Вакуумная броня", "Магнитные ботинки", "Импульсная винтовка"],
    },
    {
        "id": "SPEC_FIELD_MEDIC_COMBAT", "name": "Боевой медик",
        "group": "Боевые",
        "description": "Держит пульс отряда буквально",
        "skill_mods": {"first_aid_combat": 3, "medicine": 2, "evasion": 1},
        "equipment": ["Полевая аптечка", "Гемостатик", "Медсканер"],
    },
    {
        "id": "SPEC_DEMO_EXPERT", "name": "Подрывник",
        "group": "Боевые",
        "description": "Знает, где тонко — разорвёт точно",
        "skill_mods": {"explosives_ordnance": 3, "demolition": 2, "close_quarters": 1},
        "equipment": ["Детонаторы", "Пластид", "Дальнобойный пульт"],
    },
    {
        "id": "SPEC_CON_ARTIST", "name": "Мошенник высшей лиги",
        "group": "Социальные",
        "description": "Продаёт мечты тем, кто не покупает дешёво",
        "skill_mods": {"deception": 3, "streetwise": 2, "empathy_read": 1},
        "equipment": ["Набор личностей", "Фальшивые креденциалы", "Компакт-зеркало"],
    },
    {
        "id": "SPEC_BROADCASTER", "name": "Медийное лицо",
        "group": "Социальные",
        "description": "Его голос слушается чаще, чем законы",
        "skill_mods": {"public_speaking": 3, "writing_journalism": 2, "rumor_network": 1},
        "equipment": ["Портативная студия", "Подписной контур", "Архив сюжетов"],
    },
    {
        "id": "SPEC_LABYRINTH_FIXER", "name": "Фиксер лабиринтов",
        "group": "Социальные",
        "description": "Знает, кто кому должен и кто кого боится",
        "skill_mods": {"rumor_network": 3, "streetwise": 2, "law": 1},
        "equipment": ["Контактная книга", "Шифрованный коммуникатор", "Досье"],
    },
    {
        "id": "SPEC_INTERROGATOR_SOCIAL", "name": "Дипломат-дознаватель",
        "group": "Социальные",
        "description": "Вытягивает правду за бокалом вина",
        "skill_mods": {"interrogation": 3, "empathy_read": 2, "etiquette": 1},
        "equipment": ["Дипломат-кейс", "Регистратор микроэмоций", "Хороший вкус"],
    },
    {
        "id": "SPEC_STAGE_LEGEND", "name": "Легенда сцены",
        "group": "Социальные",
        "description": "Выступления как прикрытие операций",
        "skill_mods": {"performance": 3, "music_instrument": 2, "art_design": 1},
        "equipment": ["Сценический грим", "Инструмент", "Фан-клуб"],
    },
    {
        "id": "SPEC_LEADER_COMMAND", "name": "Прирождённый командир",
        "group": "Социальные",
        "description": "Люди идут за ним даже в Пояс",
        "skill_mods": {"leadership": 3, "instruction": 2, "logistics_planning": 1},
        "equipment": ["Командный интерфейс", "Знаки различия", "Устав в голове"],
    },
    {
        "id": "SPEC_ATMO_RACER", "name": "Гоночник атмосферы",
        "group": "Пилоты",
        "description": "Штурмовики и гоночные корпуса — стихия",
        "skill_mods": {"piloting_atmospheric": 3, "piloting": 2, "evasion": 1},
        "equipment": ["Гоночный шлем", "Форсаж-модуль", "Трофейный борт"],
    },
    {
        "id": "SPEC_ASTRO_NAVIGATOR", "name": "Астронавигатор",
        "group": "Пилоты",
        "description": "Проложит маршрут через мусорную бурю",
        "skill_mods": {"navigation_astrogation": 3, "astrophysics": 2, "sensor_operations": 1},
        "equipment": ["Навигационный комплекс", "Звёздные карты", "Расчётный блок"],
    },
    {
        "id": "SPEC_SMUGGLING_ACE", "name": "Ас контрабандных рейсов",
        "group": "Пилоты",
        "description": "Тайники внутри тайников, маршруты вне карт",
        "skill_mods": {"criminal": 3, "navigation_astrogation": 2, "evasion": 1},
        "equipment": ["Двойное дно", "Сканер патрулей", "Кодовые маячки"],
    },
    {
        "id": "SPEC_RESCUE_PILOT", "name": "Спасательный пилот",
        "group": "Пилоты",
        "description": "Летит туда, откуда все улетают",
        "skill_mods": {"piloting": 3, "vacuum_ops": 2, "first_aid_combat": 1},
        "equipment": ["Спасательный борт", "Медкапсула", "Тросовая система"],
    },
    {
        "id": "SPEC_CARAVAN_CAPTAIN", "name": "Капитан каравана",
        "group": "Пилоты",
        "description": "Ведёт колонны через мёртвые зоны",
        "skill_mods": {"logistics_planning": 3, "navigation_astrogation": 2, "leadership": 1},
        "equipment": ["Флагманский модуль", "Караванные протоколы", "Охранное крыло"],
    },
    {
        "id": "SPEC_PHARMA_BROKER", "name": "Фармаброкер",
        "group": "Медицинские",
        "description": "Достанет препарат, которого «не существует»",
        "skill_mods": {"pharmacology": 3, "negotiation": 2, "bureaucracy": 1},
        "equipment": ["Каталог веществ", "Связи в логистике", "Скрытый склад"],
    },
    {
        "id": "SPEC_XENO_VET", "name": "Ксенобиолог-практик",
        "group": "Медицинские",
        "description": "Лечит то, что не описано в учебниках",
        "skill_mods": {"xenobiology": 3, "biology": 2, "medicine": 1},
        "equipment": ["Полевой ксенолаб", "Седатики широкого спектра", "Образцы"],
    },
    {
        "id": "SPEC_GENETIC_TAILOR", "name": "Генетический портной",
        "group": "Медицинские",
        "description": "Подгоняет геном под заказ клиента",
        "skill_mods": {"genetics": 3, "pharmacology": 2, "protomolecule_theory": 1},
        "equipment": ["Геном-редактор", "Банк образцов", "Этический обход"],
    },
    {
        "id": "SPEC_TRAUMA_SURGEON_FIELD", "name": "Хирург полевых госпиталей",
        "group": "Медицинские",
        "description": "Оперирует при свете аварийных ламп",
        "skill_mods": {"medicine": 3, "first_aid_combat": 2, "pain_tolerance": 1},
        "equipment": ["Полевой оперблок", "Плазма-заменитель", "Стальные нервы"],
    },
    {
        "id": "SPEC_CRYPTO_HUNTER", "name": "Охотник за шифрами",
        "group": "Разведка",
        "description": "Взламывает не системы — смыслы",
        "skill_mods": {"crypto_analysis": 3, "comms_jamming": 2, "hacking": 1},
        "equipment": ["Криптоблок", "Перехваченные архивы", "Терпение"],
    },
    {
        "id": "SPEC_TRACKER_BELT", "name": "Следопыт Пояса",
        "group": "Разведка",
        "description": "Читает обломки как газету",
        "skill_mods": {"tracking": 3, "salvage_ops": 2, "climbing": 1},
        "equipment": ["Спектральный сканер", "Гарпун-коуш", "Журнал находок"],
    },
    {
        "id": "SPEC_DEEP_INTERROGATOR", "name": "Глубокий дознаватель",
        "group": "Разведка",
        "description": "Сломает легенду любого агента",
        "skill_mods": {"interrogation": 3, "empathy_read": 2, "law": 1},
        "equipment": ["Протоколы давления", "Юридические дыры", "Тихая камера"],
    },
    {
        "id": "SPEC_SURVEILLANCE_NET", "name": "Оператор сетей наблюдения",
        "group": "Разведка",
        "description": "Город смотрит его глазами",
        "skill_mods": {"sensor_operations": 3, "drones": 2, "comms_jamming": 1},
        "equipment": ["Сеть камер", "Аналитический ИИ", "Список слепых зон"],
    },
    {
        "id": "SPEC_INFILTRATION_SCOUT", "name": "Скаут-инфильтратор",
        "group": "Разведка",
        "description": "Первый входит, последний выходит, никто не видел",
        "skill_mods": {"stealth": 3, "evasion": 2, "tracking": 1},
        "equipment": ["Хамелеон-костюм", "Граффити-метки", "Тихий шаг"],
    },
    {
        "id": "SPEC_EVA_SPECIALIST", "name": "Специалист EVA",
        "group": "Выживание",
        "description": "Вакуум — дом, трос — umbilical",
        "skill_mods": {"vacuum_ops": 3, "zero_g_combat": 2, "radiation_handling": 1},
        "equipment": ["Скафандр повышенной автономии", "Йо-йо трос", "Дозиметр"],
    },
    {
        "id": "SPEC_RAD_SURVIVOR", "name": "Радиационный сталкер",
        "group": "Выживание",
        "description": "Ходит там, где счетчик орёт хором",
        "skill_mods": {"radiation_handling": 3, "medicine": 2, "survival": 1},
        "equipment": ["Свинцовый плащ", "Стабилизаторы", "Карта горячих точек"],
    },
    {
        "id": "SPEC_ICE_WANDERER", "name": "Скиталец льдов",
        "group": "Выживание",
        "description": "Европа/Энцелад: холод — просто погода",
        "skill_mods": {"cold_survival": 3, "survival": 2, "climbing": 1},
        "equipment": ["Термокостюм", "Ледовые якоря", "Метановая горелка"],
    },
    {
        "id": "SPEC_DUST_RUNNER", "name": "Бегущий по пыли",
        "group": "Выживание",
        "description": "Марсианские бури — расписание, не катастрофа",
        "skill_mods": {"heat_survival": 3, "survival": 2, "navigation_astrogation": 1},
        "equipment": ["Пыленепробиваемый плащ", "Резерв воды", "Компас бури"],
    },
    {
        "id": "SPEC_FORAGE_MASTER", "name": "Мастер подножного корма",
        "group": "Выживание",
        "description": "Накормит отряд на мёртвой планете",
        "skill_mods": {"foraging": 3, "chemistry": 2, "biology": 1},
        "equipment": ["Анализатор биомассы", "Семенной банк", "Рецепты выживания"],
    },
    {
        "id": "SPEC_PRESSURE_DIVER", "name": "Дайвер глубоких давлений",
        "group": "Выживание",
        "description": "Европейский океан подо льдом — его офис",
        "skill_mods": {"swimming_diving": 3, "cold_survival": 2, "vacuum_ops": 1},
        "equipment": ["Глубоководный костюм", "Сонарь", "Аварийный пузырь"],
    },
    {
        "id": "SPEC_PROTO_THEORIST", "name": "Теоретик Протомолекулы",
        "group": "Уникальные",
        "description": "Понимает её лучше, чем она понимает нас",
        "skill_mods": {"protomolecule_theory": 3, "pain_tolerance": 2, "research_method": 1},
        "equipment": ["Закрытые архивы", "Изолиния-лаб", "Красная папка"],
    },
    {
        "id": "SPEC_QUANTUM_RITUALIST", "name": "Квантовый ритуалист",
        "group": "Уникальные",
        "description": "Наука на грани мистики — или наоборот",
        "skill_mods": {"quantum_theory": 3, "technology": 2, "performance": 1},
        "equipment": ["Когерентный коллайдер", "Ритуальные схемы", "Успокоительное"],
    },
    {
        "id": "SPEC_CULT_STRATEGIST", "name": "Стратег культов",
        "group": "Уникальные",
        "description": "Вера как инструмент, паства как сеть",
        "skill_mods": {"public_speaking": 3, "rumor_network": 2, "etiquette": 1},
        "equipment": ["Священные тексты", "Сеть проповедников", "Казна культа"],
    },
    {
        "id": "SPEC_ANOMALY_HUNTER", "name": "Охотник за аномалиями",
        "group": "Уникальные",
        "description": "Ищет то, что меняет физику вокруг себя",
        "skill_mods": {"sensor_operations": 3, "quantum_theory": 2, "piloting_atmospheric": 1},
        "equipment": ["Аномалия-детектор", "Изоляционные контейнеры", "Журнал совпадений"],
    },
    {
        "id": "SPEC_MEMORY_LIBRARIAN", "name": "Библиотекарь памяти",
        "group": "Уникальные",
        "description": "Хранит чужие воспоминания как книги",
        "skill_mods": {"ai_interface": 3, "empathy_read": 2, "music_instrument": 1},
        "equipment": ["Мнемо-архив", "Кристаллы записи", "Каталог личностей"],
    },
    {
        "id": "SPEC_SOLAR_PROPHET", "name": "Солнечный пророк",
        "group": "Уникальные",
        "description": "Предсказывает вспышки — и политические бури",
        "skill_mods": {"astrophysics": 3, "public_speaking": 2, "instruction": 1},
        "equipment": ["Обсерватория-маячок", "Гелиосейсмограф", "Паства"],
    },
    {
        "id": "SPEC_GATE_SCOUT", "name": "Скаут врат",
        "group": "Уникальные",
        "description": "Видит двери там, где другие видят стену",
        "skill_mods": {"navigation_astrogation": 3, "quantum_theory": 2, "evasion": 1},
        "equipment": ["Фазовый компас", "Маркерные буи", "Легенда о возвращении"],
    },
    {
        "id": "SPEC_SYMBIONT_ENGINEER", "name": "Инженер симбионтов",
        "group": "Уникальные",
        "description": "Строит машины, которые хотят жить",
        "skill_mods": {"robotics": 3, "genetics": 2, "ai_interface": 1},
        "equipment": ["Био-силиконовый каркас", "Нейро-скелет", "Контракт symbiosis"],
    },
    {
        "id": "SPEC_FORGERY_MASTER", "name": "Мастер подделок",
        "group": "Криминал",
        "description": "Документы, подписи, происхождения — всё нарисует",
        "skill_mods": {"forgery_docs": 3, "bureaucracy": 2, "deception": 1},
        "equipment": ["Набор фальсификатора", "Бланки всех миров", "Печати"],
    },
    {
        "id": "SPEC_BLACK_MARKET_BARON", "name": "Барон чёрного рынка",
        "group": "Криминал",
        "description": "Если это запрещено — он это продаёт",
        "skill_mods": {"streetwise": 3, "negotiation": 2, "logistics_planning": 1},
        "equipment": ["Склад-призрак", "Сеть наводчиков", "Взяточный фонд"],
    },
    {
        "id": "SPEC_SALVAGE_PIRATE", "name": "Салваж-пират",
        "group": "Криминал",
        "description": "Чужие крушения — его доходная статья",
        "skill_mods": {"salvage_ops": 3, "mining": 2, "criminal": 1},
        "equipment": ["Резак корпусов", "Тральщик", "Фальшивый SOS"],
    },
    {
        "id": "SPEC_DATA_FENCER", "name": "Скупщик данных",
        "group": "Криминал",
        "description": "Купит компромат, продаст дважды",
        "skill_mods": {"crypto_analysis": 3, "rumor_network": 2, "accounting_finance": 1},
        "equipment": ["Холодный кошелёк", "Аукционный лист", "Проверка подлинности"],
    },
    {
        "id": "SPEC_SMUGGLER_ROUTE_SMITH", "name": "Кузнец контрабандных путей",
        "group": "Криминал",
        "description": "Проектирует маршруты, которых нет на картах",
        "skill_mods": {"navigation_astrogation": 3, "comms_jamming": 2, "bureaucracy": 1},
        "equipment": ["Тайниковый чертёж", "Взятые патрули", "Тихий транспондер"],
    },
    {
        "id": "SPEC_ENFORGER_CONTRACT", "name": "Исполнитель контрактов",
        "group": "Криминал",
        "description": "Долг вернётся. С процентами. Он вернёт.",
        "skill_mods": {"intimidation": 3, "close_quarters": 2, "law": 1},
        "equipment": ["Контрактный планшет", "Внушительный калибр", "Список должников"],
    }
]
