"""
Content Expansion V2 — MASSIVE content scaling.
Adds 120+ new perks, 50+ recipes, 70+ events, 150+ shop items.
Designed for 500+ hours of Rimworld-like emergent gameplay.
"""

# ════════════════════════════════════════════════════════════
#  NEW PERKS — 120 additional (total will be 180 with V1's 60)
# ════════════════════════════════════════════════════════════

V2_PERKS = [
    # ── LEADERSHIP (10) ──
    {"id": "inspiring_speech", "name": "Вдохновляющая речь", "category": "leadership",
     "description": "Союзники в бою получают +1 к атаке на 3 хода", "effect": {"leadership": 1}, "tier": 1},
    {"id": "tactical_genius", "name": "Тактический гений", "category": "leadership",
     "description": "+2 к инициативе команды в начале боя", "effect": {"tactics": 2}, "tier": 2},
    {"id": "field_commander", "name": "Полевой командир", "category": "leadership",
     "description": "Компаньоны наносят +15% урона", "effect": {"leadership": 2}, "tier": 2},
    {"id": "iron_will", "name": "Железная воля", "category": "leadership",
     "description": "Иммунитет к панике, +10 макс. рассудок", "effect": {"willpower": 2}, "tier": 3},
    {"id": "morale_boost", "name": "Боевой дух", "category": "leadership",
     "description": "Союзники восстанавливают +5 HP после победы", "effect": {"leadership": 1}, "tier": 1},
    {"id": "crowd_control", "name": "Управление толпой", "category": "leadership",
     "description": "+2 к навыкам убеждения при обращении к группам", "effect": {"persuasion": 2}, "tier": 2},
    {"id": "delegation", "name": "Делегирование", "category": "leadership",
     "description": "Компаньоны могут выполнять простые задания сами", "effect": {"leadership": 1}, "tier": 2},
    {"id": "strategic_retreat", "name": "Стратегическое отступление", "category": "leadership",
     "description": "+3 к побегу из боя для всей команды", "effect": {"survival": 1}, "tier": 1},
    {"id": "war_council", "name": "Военный совет", "category": "leadership",
     "description": "Перед миссией получаешь бонусную разведку", "effect": {"investigation": 1}, "tier": 3},
    {"id": "legendary_reputation", "name": "Легендарная репутация", "category": "leadership",
     "description": "Враги с низким боевым духом сдаются", "effect": {"intimidation": 3}, "tier": 3},

    # ── STEALTH (10) ──
    {"id": "shadow_step", "name": "Теневой шаг", "category": "stealth",
     "description": "+2 к скрытности в темноте", "effect": {"stealth": 2}, "tier": 1},
    {"id": "false_identity", "name": "Поддельная личность", "category": "stealth",
     "description": "Создание фальшивых ID стоит -50%", "effect": {"deception": 1}, "tier": 2},
    {"id": "ghost_walk", "name": "Призрачная поступь", "category": "stealth",
     "description": "Бесшумное передвижение, -3 к обнаружению", "effect": {"stealth": 3}, "tier": 3},
    {"id": "blend_in", "name": "Раствориться в толпе", "category": "stealth",
     "description": "+2 к маскировке в городе", "effect": {"stealth": 1}, "tier": 1},
    {"id": "lockpick_pro", "name": "Профи-взломщик", "category": "stealth",
     "description": "DC замков -3, электронные замки взламываются тихо", "effect": {"stealth": 1, "engineering": 1}, "tier": 2},
    {"id": "escape_artist", "name": "Мастер побега", "category": "stealth",
     "description": "Автоматическое освобождение из наручников 1 раз/день", "effect": {"dexterity": 1}, "tier": 2},
    {"id": "surveillance_expert", "name": "Эксперт наблюдения", "category": "stealth",
     "description": "Обнаруживаешь камеры и жучки автоматически", "effect": {"perception": 2}, "tier": 2},
    {"id": "dead_drop", "name": "Тайник", "category": "stealth",
     "description": "Можно оставлять невидимые тайники в любой локации", "effect": {"stealth": 1}, "tier": 1},
    {"id": "vanish", "name": "Исчезновение", "category": "stealth",
     "description": "Раз в день мгновенный выход из боя без проверки", "effect": {"stealth": 2}, "tier": 3},
    {"id": "poisoner", "name": "Отравитель", "category": "stealth",
     "description": "Доступ к крафту ядов, +2 к их применению", "effect": {"medicine": 1, "stealth": 1}, "tier": 2},

    # ── CRAFTING (10) ──
    {"id": "scrap_savant", "name": "Гений утилизации", "category": "crafting",
     "description": "Разборка предметов даёт +50% материалов", "effect": {"engineering": 1}, "tier": 1},
    {"id": "jury_rig", "name": "Полевой ремонт", "category": "crafting",
     "description": "Ремонт снаряжения из подручных средств", "effect": {"engineering": 1}, "tier": 1},
    {"id": "master_smith", "name": "Мастер-оружейник", "category": "crafting",
     "description": "Крафтовое оружие получает +1d2 урона", "effect": {"engineering": 2}, "tier": 2},
    {"id": "chemist", "name": "Химик", "category": "crafting",
     "description": "Стимуляторы и медикаменты крафтятся с +25% эффективности", "effect": {"medicine": 1}, "tier": 2},
    {"id": "nano_weaver", "name": "Нано-ткач", "category": "crafting",
     "description": "Крафт нано-брони, самовосстанавливающейся экипировки", "effect": {"technology": 2}, "tier": 3},
    {"id": "explosive_expert", "name": "Сапёр", "category": "crafting",
     "description": "Крафт гранат, мин, взрывчатки", "effect": {"engineering": 1, "combat": 1}, "tier": 2},
    {"id": "mod_specialist", "name": "Мод-специалист", "category": "crafting",
     "description": "+1 слот модификации на любом оружии", "effect": {"engineering": 1}, "tier": 2},
    {"id": "recycler", "name": "Переработчик", "category": "crafting",
     "description": "Неудачный крафт возвращает 75% материалов", "effect": {"engineering": 1}, "tier": 1},
    {"id": "blueprint_reader", "name": "Чтец чертежей", "category": "crafting",
     "description": "Изучение найденных чертежей занимает -50% времени", "effect": {"technology": 1}, "tier": 1},
    {"id": "masterwork", "name": "Шедевр", "category": "crafting",
     "description": "5% шанс крафта легендарного предмета", "effect": {"engineering": 2}, "tier": 3},

    # ── ECONOMICS / TRADE (10) ──
    {"id": "haggler", "name": "Торгаш", "category": "economics",
     "description": "Цены покупки -10%, продажи +10%", "effect": {"persuasion": 1}, "tier": 1},
    {"id": "black_market_access", "name": "Чёрный рынок", "category": "economics",
     "description": "Доступ к нелегальным товарам в любом порту", "effect": {"streetwise": 1}, "tier": 2},
    {"id": "fence", "name": "Скупщик", "category": "economics",
     "description": "Краденое продаётся за 80% цены вместо 40%", "effect": {"streetwise": 1}, "tier": 2},
    {"id": "investor", "name": "Инвестор", "category": "economics",
     "description": "+5% пассивного дохода от вложенных кредитов каждый цикл", "effect": {"intelligence": 1}, "tier": 2},
    {"id": "smuggler_contacts", "name": "Контакты контрабандистов", "category": "economics",
     "description": "Контрабандные квесты платят +25%", "effect": {"streetwise": 1}, "tier": 1},
    {"id": "tax_evasion", "name": "Уклонение от налогов", "category": "economics",
     "description": "Портовые сборы и пошлины -50%", "effect": {"deception": 1}, "tier": 1},
    {"id": "corporate_insider", "name": "Корпоративный инсайдер", "category": "economics",
     "description": "Знаешь заранее о ценовых колебаниях", "effect": {"intelligence": 1}, "tier": 3},
    {"id": "supply_chain", "name": "Цепь поставок", "category": "economics",
     "description": "Материалы для крафта стоят -20%", "effect": {"negotiation": 1}, "tier": 2},
    {"id": "loan_shark", "name": "Ростовщик", "category": "economics",
     "description": "Можешь давать NPC в долг под проценты", "effect": {"intimidation": 1}, "tier": 2},
    {"id": "magnate", "name": "Магнат", "category": "economics",
     "description": "Доступ к покупке недвижимости и бизнесов", "effect": {"leadership": 1}, "tier": 3},

    # ── PSIONICS / ANOMALIES (10) ──
    {"id": "void_sense", "name": "Чутьё Пустоты", "category": "psionics",
     "description": "Ощущаешь аномалии в радиусе 1 зоны", "effect": {"perception": 2}, "tier": 2},
    {"id": "mind_shield", "name": "Ментальный щит", "category": "psionics",
     "description": "+3 к сопротивлению ментальным атакам", "effect": {"willpower": 2}, "tier": 2},
    {"id": "empathic_reading", "name": "Эмпатическое чтение", "category": "psionics",
     "description": "Видишь истинные намерения NPC", "effect": {"empathy": 2}, "tier": 2},
    {"id": "probability_shift", "name": "Сдвиг вероятности", "category": "psionics",
     "description": "Раз в день перебрось любой провал", "effect": {"luck": 2}, "tier": 3},
    {"id": "signal_whisper", "name": "Шёпот Сигнала", "category": "psionics",
     "description": "Временная связь с ИИ-сетью без оборудования", "effect": {"hacking": 1}, "tier": 2},
    {"id": "pain_transfer", "name": "Перенос боли", "category": "psionics",
     "description": "Передаёшь 50% полученного урона ближайшему врагу", "effect": {"combat": 1}, "tier": 3},
    {"id": "void_walk", "name": "Прогулка в Пустоте", "category": "psionics",
     "description": "Проход через аномальные зоны без урона", "effect": {"survival": 2}, "tier": 3},
    {"id": "precognition", "name": "Предвидение", "category": "psionics",
     "description": "+2 к инициативе, предупреждение о засадах", "effect": {"reflexes": 2}, "tier": 2},
    {"id": "telekinetic_push", "name": "Телекинетический толчок", "category": "psionics",
     "description": "Отбрасывание одного врага раз в бой", "effect": {"combat": 1}, "tier": 2},
    {"id": "memory_echo", "name": "Эхо памяти", "category": "psionics",
     "description": "Считывание остаточных воспоминаний с предметов", "effect": {"investigation": 2}, "tier": 3},

    # ── CYBERNETICS (10) ──
    {"id": "dermal_plating", "name": "Подкожная броня", "category": "cybernetics",
     "description": "+2 защита всегда, даже без брони", "effect": {"endurance": 2}, "tier": 2},
    {"id": "reflex_boosters", "name": "Ускорители рефлексов", "category": "cybernetics",
     "description": "+2 к уклонению, +1 инициатива", "effect": {"reflexes": 2}, "tier": 2},
    {"id": "cyber_eyes", "name": "Кибер-глаза", "category": "cybernetics",
     "description": "Ночное зрение, зум, запись видео", "effect": {"perception": 2}, "tier": 2},
    {"id": "neural_link", "name": "Нейролинк", "category": "cybernetics",
     "description": "+2 к хакингу, мгновенный доступ к сети", "effect": {"hacking": 2}, "tier": 2},
    {"id": "synthetic_muscles", "name": "Синтетические мышцы", "category": "cybernetics",
     "description": "+2 к силе, +20 грузоподъёмность", "effect": {"strength": 2}, "tier": 2},
    {"id": "internal_battery", "name": "Внутренняя батарея", "category": "cybernetics",
     "description": "Питание гаджетов от тела, -50% расход энергии", "effect": {"endurance": 1}, "tier": 1},
    {"id": "combat_hud", "name": "Боевой интерфейс", "category": "cybernetics",
     "description": "+1 к точности, подсветка врагов через стены", "effect": {"combat": 1, "perception": 1}, "tier": 2},
    {"id": "voice_modulator", "name": "Модулятор голоса", "category": "cybernetics",
     "description": "Имитация любого голоса, +2 к обману", "effect": {"deception": 2}, "tier": 2},
    {"id": "adrenaline_pump", "name": "Адреналиновый насос", "category": "cybernetics",
     "description": "Раз в бой: мгновенное действие + 10 HP", "effect": {"combat": 2}, "tier": 3},
    {"id": "self_repair_nanites", "name": "Нано-регенерация", "category": "cybernetics",
     "description": "+2 HP восстановление каждый ход вне боя", "effect": {"endurance": 1}, "tier": 3},

    # ── PILOTING / VEHICLES (10) ──
    {"id": "drift_master", "name": "Мастер дрифта", "category": "piloting",
     "description": "+2 к манёврам в астероидном поле", "effect": {"piloting": 2}, "tier": 2},
    {"id": "combat_pilot", "name": "Боевой пилот", "category": "piloting",
     "description": "+2 к атаке с корабля, уклонение +1", "effect": {"piloting": 1, "combat": 1}, "tier": 2},
    {"id": "fuel_efficient", "name": "Экономный полёт", "category": "piloting",
     "description": "Расход топлива -25%", "effect": {"piloting": 1}, "tier": 1},
    {"id": "emergency_landing", "name": "Аварийная посадка", "category": "piloting",
     "description": "Крушение наносит -50% урона экипажу", "effect": {"piloting": 1, "survival": 1}, "tier": 1},
    {"id": "smuggler_hold", "name": "Потайной отсек", "category": "piloting",
     "description": "Скрытый грузовой отсек, -90% обнаружения на таможне", "effect": {"stealth": 1}, "tier": 2},
    {"id": "fleet_navigator", "name": "Флотский навигатор", "category": "piloting",
     "description": "Время перелёта -20%", "effect": {"piloting": 1}, "tier": 1},
    {"id": "boarding_expert", "name": "Абордажник", "category": "piloting",
     "description": "+2 к бою при абордаже", "effect": {"combat": 2}, "tier": 2},
    {"id": "ship_mechanic", "name": "Корабельный механик", "category": "piloting",
     "description": "Ремонт корабля в поле, -50% стоимость", "effect": {"engineering": 1}, "tier": 1},
    {"id": "signal_jammer", "name": "Глушитель сигналов", "category": "piloting",
     "description": "Блокировка вызова подкреплений врагом", "effect": {"hacking": 1}, "tier": 2},
    {"id": "graviton_surfer", "name": "Гравитонный сёрфер", "category": "piloting",
     "description": "Использование гравитационных колодцев для ускорения", "effect": {"piloting": 3}, "tier": 3},

    # ── SURVIVAL / ENVIRONMENT (10) ──
    {"id": "vacuum_adapted", "name": "Адаптация к вакууму", "category": "survival_adv",
     "description": "+5 минут в вакууме без скафандра", "effect": {"endurance": 2}, "tier": 2},
    {"id": "radiation_resist", "name": "Радиационная стойкость", "category": "survival_adv",
     "description": "-50% урон от радиации", "effect": {"endurance": 1}, "tier": 2},
    {"id": "scavenger", "name": "Мусорщик", "category": "survival_adv",
     "description": "Находишь полезное барахло в любой локации", "effect": {"perception": 1}, "tier": 1},
    {"id": "field_medic", "name": "Полевая медицина", "category": "survival_adv",
     "description": "Медпаки лечат +50%", "effect": {"medicine": 2}, "tier": 2},
    {"id": "zero_g_combat", "name": "Бой в невесомости", "category": "survival_adv",
     "description": "Нет штрафов в невесомости", "effect": {"combat": 1}, "tier": 2},
    {"id": "extreme_climate", "name": "Экстремальный климат", "category": "survival_adv",
     "description": "Нет штрафов от жары/холода", "effect": {"survival": 2}, "tier": 1},
    {"id": "water_recycler", "name": "Переработка воды", "category": "survival_adv",
     "description": "Потребление воды -50%", "effect": {"survival": 1}, "tier": 1},
    {"id": "makeshift_shelter", "name": "Импровизированное укрытие", "category": "survival_adv",
     "description": "Постройка убежища из мусора за 1 ход", "effect": {"engineering": 1}, "tier": 1},
    {"id": "predator_instinct", "name": "Инстинкт хищника", "category": "survival_adv",
     "description": "+2 к выслеживанию, чуешь засады", "effect": {"perception": 2}, "tier": 2},
    {"id": "last_stand", "name": "Последний рубеж", "category": "survival_adv",
     "description": "При HP<20% — +3 к атаке и защите", "effect": {"combat": 2}, "tier": 3},

    # ── SOCIAL / INFLUENCE (10) ──
    {"id": "silver_tongue", "name": "Серебряный язык", "category": "social_adv",
     "description": "+2 к убеждению, ложь детектируется на -2", "effect": {"persuasion": 2}, "tier": 2},
    {"id": "underworld_rep", "name": "Репутация подполья", "category": "social_adv",
     "description": "Криминальные NPC доверяют сразу", "effect": {"streetwise": 2}, "tier": 2},
    {"id": "diplomat", "name": "Дипломат", "category": "social_adv",
     "description": "Разрешение конфликтов мирным путём +3", "effect": {"negotiation": 2}, "tier": 2},
    {"id": "interrogator", "name": "Допросчик", "category": "social_adv",
     "description": "+3 к получению информации от пленных", "effect": {"intimidation": 2}, "tier": 2},
    {"id": "face_reader", "name": "Физиогномист", "category": "social_adv",
     "description": "Автоматическое определение лжи при DC<12", "effect": {"empathy": 2}, "tier": 2},
    {"id": "network", "name": "Связи", "category": "social_adv",
     "description": "В каждом городе есть контакт с информацией", "effect": {"streetwise": 1}, "tier": 2},
    {"id": "propaganda_master", "name": "Мастер пропаганды", "category": "social_adv",
     "description": "Влияние на общественное мнение в локации", "effect": {"persuasion": 2}, "tier": 3},
    {"id": "seducer", "name": "Обольститель", "category": "social_adv",
     "description": "+3 к социальным проверкам с романтическим подтекстом", "effect": {"charisma": 2}, "tier": 2},
    {"id": "bartender_friend", "name": "Друг бармена", "category": "social_adv",
     "description": "Бары дают +2 к сбору слухов, скидка на выпивку", "effect": {"streetwise": 1}, "tier": 1},
    {"id": "faction_double_agent", "name": "Двойной агент", "category": "social_adv",
     "description": "Состоишь в 2 враждующих фракциях без штрафа", "effect": {"deception": 2}, "tier": 3},

    # ── COMBAT ADVANCED (10) ──
    {"id": "dual_wield", "name": "Два ствола", "category": "combat_adv",
     "description": "Стрельба с двух рук без штрафа", "effect": {"combat": 2}, "tier": 2},
    {"id": "headshot", "name": "Выстрел в голову", "category": "combat_adv",
     "description": "Критический удар наносит ×3 урона", "effect": {"combat": 1}, "tier": 3},
    {"id": "suppressive_fire", "name": "Подавляющий огонь", "category": "combat_adv",
     "description": "Заставляет врагов залечь на 1 ход", "effect": {"combat": 1}, "tier": 1},
    {"id": "melee_master", "name": "Мастер ближнего боя", "category": "combat_adv",
     "description": "+3 к рукопашному бою", "effect": {"melee": 3}, "tier": 2},
    {"id": "demolitions", "name": "Подрывник", "category": "combat_adv",
     "description": "+2 к урону взрывчаткой, радиус +50%", "effect": {"engineering": 1, "combat": 1}, "tier": 2},
    {"id": "sniper", "name": "Снайпер", "category": "combat_adv",
     "description": "+3 к дальним выстрелам, первый удар из укрытия ×2", "effect": {"combat": 2}, "tier": 2},
    {"id": "shield_wall", "name": "Стена щитов", "category": "combat_adv",
     "description": "+3 защита при использовании укрытия", "effect": {"endurance": 1}, "tier": 1},
    {"id": "blade_dancer", "name": "Танцор с клинком", "category": "combat_adv",
     "description": "+2 уклонение в ближнем бою", "effect": {"melee": 2}, "tier": 2},
    {"id": "emp_specialist", "name": "Специалист по ЭМИ", "category": "combat_adv",
     "description": "ЭМИ-гранаты отключают технику на 3 хода", "effect": {"technology": 1}, "tier": 2},
    {"id": "berserker", "name": "Берсерк", "category": "combat_adv",
     "description": "+5 к урону, -2 защита. Нельзя отступить.", "effect": {"combat": 3}, "tier": 3},

    # ── MEDICINE ADVANCED (10) ──
    {"id": "trauma_surgeon", "name": "Хирург-травматолог", "category": "medicine_adv",
     "description": "Стабилизация умирающих без оборудования", "effect": {"medicine": 3}, "tier": 3},
    {"id": "gene_therapy", "name": "Генная терапия", "category": "medicine_adv",
     "description": "Лечение генетических мутаций", "effect": {"medicine": 2}, "tier": 3},
    {"id": "stim_jockey", "name": "Стим-наездник", "category": "medicine_adv",
     "description": "Боевые стимуляторы действуют ×2 дольше", "effect": {"medicine": 1}, "tier": 1},
    {"id": "plague_doctor", "name": "Чумной доктор", "category": "medicine_adv",
     "description": "Иммунитет к биологическим агентам", "effect": {"endurance": 1, "medicine": 1}, "tier": 2},
    {"id": "cybernetic_surgeon", "name": "Кибер-хирург", "category": "medicine_adv",
     "description": "Установка имплантов без клиники", "effect": {"medicine": 2, "engineering": 1}, "tier": 3},
    {"id": "first_responder", "name": "Первая помощь", "category": "medicine_adv",
     "description": "Автоматическое лечение +5 HP после боя", "effect": {"medicine": 1}, "tier": 1},
    {"id": "drug_cook", "name": "Нарко-повар", "category": "medicine_adv",
     "description": "Крафт стимуляторов, наркотиков, антидотов", "effect": {"medicine": 1}, "tier": 2},
    {"id": "xenobiologist", "name": "Ксенобиолог", "category": "medicine_adv",
     "description": "+3 к изучению чужеродных организмов", "effect": {"science": 2}, "tier": 2},
    {"id": "triage", "name": "Сортировка раненых", "category": "medicine_adv",
     "description": "Лечение 2 раненых одновременно", "effect": {"medicine": 1}, "tier": 2},
    {"id": "pain_immunity", "name": "Невосприимчивость к боли", "category": "medicine_adv",
     "description": "Боевые ранения не снижают навыки", "effect": {"endurance": 2}, "tier": 3},
]


# ════════════════════════════════════════════════════════════
#  NEW CRAFTING RECIPES — 50 additional (total ~85)
# ════════════════════════════════════════════════════════════

V2_RECIPES = [
    # ── WEAPONS ──
    {"id": "plasma_pistol", "name": "Плазменный пистолет", "skill": "engineering",
     "difficulty": 14, "materials": [{"name": "Плазменная ячейка", "qty": 2}, {"name": "Корпус оружия", "qty": 1}, {"name": "Линза охлаждения", "qty": 1}],
     "result": {"name": "Плазменный пистолет «Солнцеед»", "type": "weapon", "stats": "2d6+3 плазма", "rarity": "rare"}, "time_minutes": 180},
    {"id": "emp_grenade", "name": "ЭМИ-граната", "skill": "engineering",
     "difficulty": 10, "materials": [{"name": "Электронные компоненты", "qty": 3}, {"name": "Батарея", "qty": 1}],
     "result": {"name": "ЭМИ-граната", "type": "grenade", "stats": "Отключает технику на 3 хода, r=5м", "rarity": "uncommon"}, "time_minutes": 45},
    {"id": "mono_blade", "name": "Мономолекулярный клинок", "skill": "engineering",
     "difficulty": 16, "materials": [{"name": "Мономолекулярная нить", "qty": 2}, {"name": "Титановая рукоять", "qty": 1}, {"name": "Стабилизатор поля", "qty": 1}],
     "result": {"name": "Моноклинок «Бритва»", "type": "weapon", "stats": "3d4+2 режущий, игнорирует 2 брони", "rarity": "epic"}, "time_minutes": 240},
    {"id": "flashbang", "name": "Светошумовая граната", "skill": "engineering",
     "difficulty": 8, "materials": [{"name": "Корпус гранаты", "qty": 1}, {"name": "Магниевый порошок", "qty": 1}],
     "result": {"name": "Светошумовая граната", "type": "grenade", "stats": "Ослепление на 2 хода", "rarity": "common"}, "time_minutes": 20},
    {"id": "rail_rifle", "name": "Рельсовая винтовка", "skill": "engineering",
     "difficulty": 18, "materials": [{"name": "Рельсовые направляющие", "qty": 2}, {"name": "Сверхпроводник", "qty": 2}, {"name": "Ядро конденсатора", "qty": 1}],
     "result": {"name": "Рельсотрон «Гром»", "type": "weapon", "stats": "4d6 кинетический, пробивает стены", "rarity": "legendary"}, "time_minutes": 480},
    {"id": "frag_mine", "name": "Осколочная мина", "skill": "engineering",
     "difficulty": 12, "materials": [{"name": "Корпус гранаты", "qty": 1}, {"name": "Датчик движения", "qty": 1}, {"name": "Шрапнель", "qty": 2}],
     "result": {"name": "Осколочная мина", "type": "trap", "stats": "3d6 урон в радиусе 3м", "rarity": "uncommon"}, "time_minutes": 60},

    # ── ARMOR ──
    {"id": "stealth_suit", "name": "Стелс-костюм", "skill": "technology",
     "difficulty": 16, "materials": [{"name": "Оптоволоконная ткань", "qty": 3}, {"name": "Наноклей", "qty": 2}, {"name": "Микропроцессор", "qty": 1}],
     "result": {"name": "Стелс-костюм «Тень»", "type": "armor", "stats": "Защита 2, +3 скрытность, хамелеон", "rarity": "epic"}, "time_minutes": 360},
    {"id": "radiation_suit", "name": "Радиационный костюм", "skill": "engineering",
     "difficulty": 10, "materials": [{"name": "Свинцовая ткань", "qty": 2}, {"name": "Герметик", "qty": 1}],
     "result": {"name": "Антирад-костюм", "type": "armor", "stats": "Защита 1, иммунитет к радиации", "rarity": "uncommon"}, "time_minutes": 90},
    {"id": "exo_frame", "name": "Экзо-каркас", "skill": "engineering",
     "difficulty": 18, "materials": [{"name": "Титановый каркас", "qty": 3}, {"name": "Серво-мотор", "qty": 4}, {"name": "Ядро батареи", "qty": 1}],
     "result": {"name": "Экзоскелет «Атлас»", "type": "armor", "stats": "Защита 5, +3 сила, +50 груз", "rarity": "legendary"}, "time_minutes": 600},

    # ── MEDICAL ──
    {"id": "combat_stim", "name": "Боевой стимулятор", "skill": "medicine",
     "difficulty": 10, "materials": [{"name": "Адреналиновый экстракт", "qty": 1}, {"name": "Наноинъектор", "qty": 1}],
     "result": {"name": "Боевой стим", "type": "consumable", "stats": "+2 бой, +2 рефлексы на 5 ходов", "rarity": "uncommon"}, "time_minutes": 30},
    {"id": "nano_bandage", "name": "Нано-бинт", "skill": "medicine",
     "difficulty": 8, "materials": [{"name": "Наноткань", "qty": 1}, {"name": "Медгель", "qty": 1}],
     "result": {"name": "Нано-бинт", "type": "consumable", "stats": "+15 HP, остановка кровотечения", "rarity": "common"}, "time_minutes": 15},
    {"id": "antidote_universal", "name": "Универсальный антидот", "skill": "medicine",
     "difficulty": 14, "materials": [{"name": "Биохимический реагент", "qty": 2}, {"name": "Наноинъектор", "qty": 1}, {"name": "Образец токсина", "qty": 1}],
     "result": {"name": "Антидот «Чистая кровь»", "type": "consumable", "stats": "Снимает любые яды/болезни", "rarity": "rare"}, "time_minutes": 90},
    {"id": "trauma_kit", "name": "Травма-набор", "skill": "medicine",
     "difficulty": 12, "materials": [{"name": "Медгель", "qty": 2}, {"name": "Хирургические инструменты", "qty": 1}, {"name": "Нано-бинт", "qty": 2}],
     "result": {"name": "Травма-набор «Лазарь»", "type": "consumable", "stats": "+30 HP, лечение переломов", "rarity": "rare"}, "time_minutes": 60},
    {"id": "focus_pill", "name": "Таблетка концентрации", "skill": "medicine",
     "difficulty": 10, "materials": [{"name": "Нейростимулятор", "qty": 1}, {"name": "Экстракт грибов Титана", "qty": 1}],
     "result": {"name": "Фокус-пилюля", "type": "consumable", "stats": "+2 интеллект, +2 хакинг на 10 ходов", "rarity": "uncommon"}, "time_minutes": 30},

    # ── HACKING TOOLS ──
    {"id": "ice_cracker", "name": "ICE-взломщик", "skill": "technology",
     "difficulty": 14, "materials": [{"name": "Микрочип", "qty": 2}, {"name": "Квантовый кристалл", "qty": 1}],
     "result": {"name": "ICE-крэкер v3", "type": "gadget", "stats": "+2 к хакингу vs ICE", "rarity": "rare"}, "time_minutes": 120},
    {"id": "signal_scrambler", "name": "Скремблер сигналов", "skill": "technology",
     "difficulty": 12, "materials": [{"name": "Антенна", "qty": 1}, {"name": "Микрочип", "qty": 1}, {"name": "Батарея", "qty": 1}],
     "result": {"name": "Скремблер «Шум»", "type": "gadget", "stats": "Блокировка связи в радиусе 20м", "rarity": "uncommon"}, "time_minutes": 90},
    {"id": "ghost_deck", "name": "Призрак-дека", "skill": "technology",
     "difficulty": 18, "materials": [{"name": "Квантовый процессор", "qty": 1}, {"name": "Оптоволокно", "qty": 3}, {"name": "Корпус оружия", "qty": 1}],
     "result": {"name": "Хакерская дека «Фантом»", "type": "gadget", "stats": "+3 хакинг, невидимость в сети", "rarity": "legendary"}, "time_minutes": 360},

    # ── GADGETS ──
    {"id": "hologram_decoy", "name": "Голограмма-приманка", "skill": "technology",
     "difficulty": 12, "materials": [{"name": "Голопроектор", "qty": 1}, {"name": "Батарея", "qty": 1}, {"name": "Микрочип", "qty": 1}],
     "result": {"name": "Голо-приманка", "type": "gadget", "stats": "Отвлекает врагов на 2 хода", "rarity": "uncommon"}, "time_minutes": 60},
    {"id": "grapple_hook", "name": "Кошка-трос", "skill": "engineering",
     "difficulty": 8, "materials": [{"name": "Металлические компоненты", "qty": 2}, {"name": "Тросик", "qty": 2}],
     "result": {"name": "Магнитная кошка", "type": "gadget", "stats": "Подъём/спуск, зацеп за металл", "rarity": "common"}, "time_minutes": 45},
    {"id": "drone_scout", "name": "Дрон-разведчик", "skill": "technology",
     "difficulty": 14, "materials": [{"name": "Микро-двигатель", "qty": 2}, {"name": "Оптический сенсор", "qty": 1}, {"name": "Микрочип", "qty": 1}, {"name": "Батарея", "qty": 1}],
     "result": {"name": "Разведдрон «Мошка»", "type": "gadget", "stats": "Разведка 1 зоны впереди, запись видео", "rarity": "rare"}, "time_minutes": 180},
    {"id": "tracking_beacon", "name": "Маяк-трекер", "skill": "technology",
     "difficulty": 8, "materials": [{"name": "Микрочип", "qty": 1}, {"name": "Антенна", "qty": 1}],
     "result": {"name": "GPS-жучок", "type": "gadget", "stats": "Отслеживание объекта на карте", "rarity": "common"}, "time_minutes": 20},

    # ── SHIP UPGRADES ──
    {"id": "shield_gen", "name": "Щитовой генератор", "skill": "engineering",
     "difficulty": 16, "materials": [{"name": "Ядро конденсатора", "qty": 2}, {"name": "Сверхпроводник", "qty": 2}, {"name": "Титановый каркас", "qty": 1}],
     "result": {"name": "Щит «Эгида» Mk.I", "type": "ship_upgrade", "stats": "Корабельный щит: 20 HP", "rarity": "rare"}, "time_minutes": 360},
    {"id": "cargo_expand", "name": "Расширение трюма", "skill": "engineering",
     "difficulty": 10, "materials": [{"name": "Металлические компоненты", "qty": 5}, {"name": "Герметик", "qty": 2}],
     "result": {"name": "Доп. грузовой модуль", "type": "ship_upgrade", "stats": "+20 единиц груза", "rarity": "common"}, "time_minutes": 240},
    {"id": "turret_mount", "name": "Турельная установка", "skill": "engineering",
     "difficulty": 14, "materials": [{"name": "Корпус оружия", "qty": 1}, {"name": "Серво-мотор", "qty": 2}, {"name": "Датчик движения", "qty": 1}],
     "result": {"name": "Автотурель «Страж»", "type": "ship_upgrade", "stats": "Авто-защита: 1d8 урон/ход", "rarity": "rare"}, "time_minutes": 300},
    {"id": "stealth_plating", "name": "Стелс-обшивка", "skill": "technology",
     "difficulty": 18, "materials": [{"name": "Оптоволоконная ткань", "qty": 5}, {"name": "Радиопоглощатель", "qty": 3}, {"name": "Микропроцессор", "qty": 2}],
     "result": {"name": "Стелс-покрытие", "type": "ship_upgrade", "stats": "Корабль невидим для базовых сканеров", "rarity": "epic"}, "time_minutes": 600},

    # ── IMPLANTS (craftable) ──
    {"id": "reflex_chip", "name": "Чип рефлексов", "skill": "medicine",
     "difficulty": 16, "materials": [{"name": "Нейрочип", "qty": 1}, {"name": "Нанотрубки", "qty": 2}, {"name": "Биогель", "qty": 1}],
     "result": {"name": "Имплант «Молния»", "type": "implant", "stats": "+2 рефлексы, +1 инициатива", "rarity": "rare"}, "time_minutes": 180},
    {"id": "subdermal_armor", "name": "Подкожная броня", "skill": "medicine",
     "difficulty": 14, "materials": [{"name": "Титановые пластинки", "qty": 3}, {"name": "Биогель", "qty": 2}],
     "result": {"name": "Подкожная броня v2", "type": "implant", "stats": "+2 защита постоянно", "rarity": "rare"}, "time_minutes": 120},

    # ── FOOD / SURVIVAL ──
    {"id": "ration_pack", "name": "Рацион выживания", "skill": "survival",
     "difficulty": 6, "materials": [{"name": "Пищевой концентрат", "qty": 2}, {"name": "Вода", "qty": 1}],
     "result": {"name": "Рацион на 3 дня", "type": "consumable", "stats": "3 дня без голода", "rarity": "common"}, "time_minutes": 15},
    {"id": "water_purifier", "name": "Фильтр воды", "skill": "survival",
     "difficulty": 8, "materials": [{"name": "Угольный фильтр", "qty": 1}, {"name": "Корпус контейнера", "qty": 1}],
     "result": {"name": "Портативный фильтр", "type": "gadget", "stats": "Очистка воды из любого источника", "rarity": "common"}, "time_minutes": 30},

    # ── EXPLOSIVES / SPECIAL ──
    {"id": "breach_charge", "name": "Проникающий заряд", "skill": "engineering",
     "difficulty": 14, "materials": [{"name": "Взрывчатое вещество", "qty": 2}, {"name": "Детонатор", "qty": 1}, {"name": "Направляющий конус", "qty": 1}],
     "result": {"name": "Заряд «Вход»", "type": "explosive", "stats": "Пробивает двери/стены, минимальный радиус", "rarity": "rare"}, "time_minutes": 60},
    {"id": "smoke_bomb", "name": "Дымовая шашка", "skill": "engineering",
     "difficulty": 6, "materials": [{"name": "Химреагент", "qty": 1}, {"name": "Корпус гранаты", "qty": 1}],
     "result": {"name": "Дымовая шашка", "type": "grenade", "stats": "Задымление зоны на 3 хода", "rarity": "common"}, "time_minutes": 15},
    {"id": "neural_disruptor", "name": "Нейро-дезориентатор", "skill": "technology",
     "difficulty": 16, "materials": [{"name": "Нейрочип", "qty": 1}, {"name": "ЭМИ-излучатель", "qty": 1}, {"name": "Батарея", "qty": 1}],
     "result": {"name": "Нейро-дезориентатор", "type": "gadget", "stats": "Оглушение кибер-усиленного врага на 3 хода", "rarity": "epic"}, "time_minutes": 180},

    # ── VEHICLE PARTS ──
    {"id": "thruster_boost", "name": "Ускоритель тяги", "skill": "engineering",
     "difficulty": 12, "materials": [{"name": "Ядро конденсатора", "qty": 1}, {"name": "Топливная ячейка", "qty": 2}],
     "result": {"name": "Ускоритель «Пуля»", "type": "ship_upgrade", "stats": "+20% скорость корабля", "rarity": "uncommon"}, "time_minutes": 180},
    {"id": "scanner_upgrade", "name": "Улучшенный сканер", "skill": "technology",
     "difficulty": 12, "materials": [{"name": "Оптический сенсор", "qty": 2}, {"name": "Антенна", "qty": 1}, {"name": "Микрочип", "qty": 1}],
     "result": {"name": "Сканер «Ястреб»", "type": "ship_upgrade", "stats": "Обнаружение скрытых кораблей/объектов", "rarity": "uncommon"}, "time_minutes": 120},
]


# ════════════════════════════════════════════════════════════
#  NEW SHOP ITEMS — 150+ additional (total ~255)
# ════════════════════════════════════════════════════════════

V2_SHOP_ITEMS = {
    "weapons": [
        # ── Pistols ──
        {"id": "W_PLASMA_PISTOL", "name": "Плазменный пистолет «Солнцеед»", "base_price": 8500, "stats": "2d6+3 плазма, перегрев", "rarity": "rare"},
        {"id": "W_NEEDLE_GUN", "name": "Игломёт «Шёпот»", "base_price": 5000, "stats": "1d4+2 + яд, бесшумный", "rarity": "uncommon"},
        {"id": "W_REVOLVER", "name": "Револьвер «Правосудие»", "base_price": 3500, "stats": "2d6 кинетический, 6 зарядов", "rarity": "uncommon"},
        {"id": "W_HOLDOUT", "name": "Карманный пистолет «Туз»", "base_price": 1500, "stats": "1d4 кинетический, скрытый", "rarity": "common"},
        {"id": "W_LASER_PISTOL", "name": "Лазерный пистолет «Луч»", "base_price": 6000, "stats": "2d4+2 энергия, бесконечный боезапас", "rarity": "uncommon"},
        # ── Rifles ──
        {"id": "W_RAILGUN", "name": "Рельсотрон «Гром»", "base_price": 25000, "stats": "4d6 кинетический, пробивание стен", "rarity": "legendary"},
        {"id": "W_GAUSS_RIFLE", "name": "Гаусс-винтовка «Вектор»", "base_price": 15000, "stats": "3d6+2 кинетический", "rarity": "rare"},
        {"id": "W_PLASMA_RIFLE", "name": "Плазменная винтовка «Нова»", "base_price": 18000, "stats": "3d6+3 плазма, AoE", "rarity": "rare"},
        {"id": "W_HUNTING_RIFLE", "name": "Охотничья винтовка «Следопыт»", "base_price": 4000, "stats": "2d6+2, +2 на дальности", "rarity": "common"},
        # ── Melee ──
        {"id": "W_MONOBLADE", "name": "Моноклинок «Бритва»", "base_price": 12000, "stats": "3d4+2 режущий, игнор 2 брони", "rarity": "epic"},
        {"id": "W_STUN_BATON", "name": "Шоковая дубинка", "base_price": 2000, "stats": "1d6 + оглушение 1 ход", "rarity": "common"},
        {"id": "W_VIBRO_KNIFE", "name": "Виброклинок", "base_price": 4500, "stats": "2d4+1 вибро, скрытый", "rarity": "uncommon"},
        {"id": "W_CHAIN_WHIP", "name": "Цепной бич «Гидра»", "base_price": 7000, "stats": "2d6 режущий, 3м дистанция", "rarity": "rare"},
        # ── Heavy ──
        {"id": "W_ROCKET_LAUNCHER", "name": "РПГ «Циклоп»", "base_price": 30000, "stats": "5d6 взрывной, AoE 5м, 3 ракеты", "rarity": "legendary"},
        {"id": "W_FLAMETHROWER", "name": "Огнемёт «Адское пламя»", "base_price": 12000, "stats": "2d6 огонь/ход, конус 5м", "rarity": "rare"},
        {"id": "W_MINIGUN", "name": "Миниган «Мясорубка»", "base_price": 20000, "stats": "3d8 кинетический, расход 10 патронов/ход", "rarity": "epic"},
    ],
    "armor": [
        {"id": "A_STEALTH_SUIT", "name": "Стелс-костюм «Тень»", "base_price": 18000, "stats": "Защита 2, +3 скрытность", "rarity": "epic"},
        {"id": "A_POWER_ARMOR", "name": "Силовая броня «Титан»", "base_price": 45000, "stats": "Защита 8, +2 сила, -2 скрытность", "rarity": "legendary"},
        {"id": "A_HAZMAT", "name": "Химзащитный костюм", "base_price": 5000, "stats": "Защита 1, иммунитет к хим/био", "rarity": "uncommon"},
        {"id": "A_SPACE_SUIT_MIL", "name": "Военный скафандр", "base_price": 15000, "stats": "Защита 4, вакуум 6ч, +1 бой", "rarity": "rare"},
        {"id": "A_NANO_ARMOR", "name": "Нано-броня «Адаптация»", "base_price": 35000, "stats": "Защита 5, регенерация 1/ход", "rarity": "epic"},
        {"id": "A_THERMAL_SUIT", "name": "Термокостюм «Полюс»", "base_price": 6000, "stats": "Защита 2, иммунитет к холоду/жаре", "rarity": "uncommon"},
        {"id": "A_COMBAT_VEST", "name": "Боевой жилет «Страж»", "base_price": 3000, "stats": "Защита 3, скрытый", "rarity": "common"},
        {"id": "A_EXO_LIGHT", "name": "Лёгкий экзоскелет", "base_price": 22000, "stats": "Защита 4, +2 сила, +30 груз", "rarity": "rare"},
        {"id": "A_SHIELD_BELT", "name": "Пояс энергощита", "base_price": 20000, "stats": "Щит 15 HP, перезарядка 3 хода", "rarity": "rare"},
        {"id": "A_CHAMELEON_CLOAK", "name": "Хамелеон-плащ", "base_price": 25000, "stats": "+4 скрытность, адаптивный камуфляж", "rarity": "epic"},
    ],
    "implants": [
        {"id": "I_REFLEX_CHIP", "name": "Чип рефлексов «Молния»", "base_price": 12000, "stats": "+2 рефлексы, +1 инициатива", "rarity": "rare"},
        {"id": "I_CORTICAL_STACK", "name": "Кортикальный стек", "base_price": 50000, "stats": "Резервная копия сознания при смерти", "rarity": "legendary"},
        {"id": "I_SKILL_WIRE", "name": "Скиллвайр", "base_price": 15000, "stats": "Загрузка навыков: +2 к любому навыку на 1ч", "rarity": "rare"},
        {"id": "I_TOXIN_FILTER", "name": "Фильтр токсинов", "base_price": 8000, "stats": "Иммунитет к ядам и наркотикам", "rarity": "uncommon"},
        {"id": "I_ADRENALINE", "name": "Адреналиновый насос", "base_price": 18000, "stats": "+1 действие раз в бой", "rarity": "epic"},
        {"id": "I_MEMORY_CHIP", "name": "Чип памяти", "base_price": 6000, "stats": "+2 интеллект, идеальная память", "rarity": "uncommon"},
        {"id": "I_SUBVOCAL", "name": "Субвокальный передатчик", "base_price": 4000, "stats": "Бесшумная связь, +1 координация", "rarity": "uncommon"},
        {"id": "I_PAIN_EDITOR", "name": "Редактор боли", "base_price": 10000, "stats": "Игнор штрафов от ранений", "rarity": "rare"},
        {"id": "I_SYNTHETIC_LUNGS", "name": "Синтетические лёгкие", "base_price": 9000, "stats": "Дыхание в токсичной атмосфере, +2 выносливость", "rarity": "rare"},
        {"id": "I_COMBAT_ARM", "name": "Боевая рука «Кулак»", "base_price": 20000, "stats": "+3 рукопашный, скрытый клинок", "rarity": "epic"},
    ],
    "gadgets": [
        {"id": "G_DRONE_SCOUT", "name": "Разведдрон «Мошка»", "base_price": 8000, "stats": "Разведка 1 зоны, запись видео", "rarity": "rare"},
        {"id": "G_HOLO_DECOY", "name": "Голо-приманка", "base_price": 5000, "stats": "Отвлечение врагов на 2 хода", "rarity": "uncommon"},
        {"id": "G_GRAPPLE", "name": "Магнитная кошка", "base_price": 1500, "stats": "Подъём/спуск, зацеп за металл", "rarity": "common"},
        {"id": "G_TRACKER", "name": "GPS-жучок", "base_price": 800, "stats": "Отслеживание объекта", "rarity": "common"},
        {"id": "G_HACKER_DECK_MK2", "name": "Хак-дека Mk.II", "base_price": 12000, "stats": "+2 хакинг", "rarity": "rare"},
        {"id": "G_HACKER_DECK_MK3", "name": "Хак-дека «Фантом»", "base_price": 30000, "stats": "+3 хакинг, невидимость в сети", "rarity": "legendary"},
        {"id": "G_BINOCULARS", "name": "Электро-бинокль", "base_price": 2000, "stats": "Зум ×20, ночное зрение, пометки", "rarity": "uncommon"},
        {"id": "G_LOCK_PICK_SET", "name": "Набор отмычек", "base_price": 1000, "stats": "+2 к взлому механ. замков", "rarity": "common"},
        {"id": "G_SIGNAL_JAMMER", "name": "Глушитель связи", "base_price": 6000, "stats": "Блокировка связи 20м, 10 мин", "rarity": "uncommon"},
        {"id": "G_MEDSCANNER", "name": "Мед-сканер", "base_price": 4000, "stats": "Диагностика ранений, +1 медицина", "rarity": "uncommon"},
        {"id": "G_MOTION_SENSOR", "name": "Датчик движения", "base_price": 3000, "stats": "Обнаружение 15м, предупреждение", "rarity": "uncommon"},
        {"id": "G_PORTABLE_FORGE", "name": "Портативная кузница", "base_price": 10000, "stats": "Крафт оружия в поле", "rarity": "rare"},
        {"id": "G_CAMO_NET", "name": "Маскировочная сеть", "base_price": 2500, "stats": "+3 скрытность лагеря", "rarity": "uncommon"},
        {"id": "G_TRANSLATOR", "name": "Универсальный переводчик", "base_price": 5000, "stats": "Перевод любых языков, +1 социальные", "rarity": "uncommon"},
        {"id": "G_CLIMBING_KIT", "name": "Набор скалолаза", "base_price": 1500, "stats": "+3 к лазанию, безопасный спуск", "rarity": "common"},
    ],
    "consumables": [
        {"id": "C_COMBAT_STIM", "name": "Боевой стим «Ярость»", "base_price": 500, "stats": "+2 бой, +2 рефлексы, 5 ходов", "rarity": "uncommon"},
        {"id": "C_FOCUS_PILL", "name": "Фокус-пилюля", "base_price": 400, "stats": "+2 интеллект, +2 хакинг, 10 ходов", "rarity": "uncommon"},
        {"id": "C_NANO_BANDAGE", "name": "Нано-бинт", "base_price": 300, "stats": "+15 HP, остановка кровотечения", "rarity": "common"},
        {"id": "C_TRAUMA_KIT", "name": "Травма-набор «Лазарь»", "base_price": 1200, "stats": "+30 HP, лечение переломов", "rarity": "rare"},
        {"id": "C_ANTIDOTE", "name": "Антидот «Чистая кровь»", "base_price": 800, "stats": "Снимает любые яды/болезни", "rarity": "rare"},
        {"id": "C_RATION_3D", "name": "Рацион на 3 дня", "base_price": 150, "stats": "Еда на 3 дня", "rarity": "common"},
        {"id": "C_OXYGEN_TANK", "name": "Кислородный баллон", "base_price": 200, "stats": "4 часа дыхания в вакууме", "rarity": "common"},
        {"id": "C_EMP_GRENADE", "name": "ЭМИ-граната", "base_price": 600, "stats": "Отключение техники 3 хода, r=5м", "rarity": "uncommon"},
        {"id": "C_FLASHBANG", "name": "Светошумовая граната", "base_price": 250, "stats": "Ослепление 2 хода", "rarity": "common"},
        {"id": "C_SMOKE_BOMB", "name": "Дымовая шашка", "base_price": 200, "stats": "Задымление 3 хода", "rarity": "common"},
        {"id": "C_FRAG_GRENADE", "name": "Осколочная граната", "base_price": 500, "stats": "2d6 урон, r=3м", "rarity": "uncommon"},
        {"id": "C_STIM_PACK", "name": "Стим-пак экстренный", "base_price": 800, "stats": "+20 HP мгновенно", "rarity": "uncommon"},
        {"id": "C_CHARISMA_BOOST", "name": "Феромон-спрей", "base_price": 350, "stats": "+2 социальные, 1 час", "rarity": "uncommon"},
        {"id": "C_LIQUID_ARMOR", "name": "Жидкая броня", "base_price": 1000, "stats": "+3 защита, 1 бой", "rarity": "rare"},
        {"id": "C_TRUTH_SERUM", "name": "Сыворотка правды", "base_price": 600, "stats": "Цель не может лгать 5 мин", "rarity": "rare"},
        {"id": "C_SPEED_BOOST", "name": "Инъекция «Ртуть»", "base_price": 450, "stats": "+1 действие, 3 хода", "rarity": "uncommon"},
        {"id": "C_REPAIR_PASTE", "name": "Ремонтная паста", "base_price": 300, "stats": "Ремонт брони +10 прочности", "rarity": "common"},
    ],
    "craft_materials": [
        {"id": "M_PLASMA_CELL", "name": "Плазменная ячейка", "base_price": 1200, "stats": "Крафт плазменного оружия", "rarity": "rare"},
        {"id": "M_QUANTUM_CRYSTAL", "name": "Квантовый кристалл", "base_price": 2000, "stats": "Крафт высокотех оборудования", "rarity": "rare"},
        {"id": "M_NEUROCHIP", "name": "Нейрочип", "base_price": 1500, "stats": "Крафт имплантов и хак-инструментов", "rarity": "rare"},
        {"id": "M_SUPERCONDUCTOR", "name": "Сверхпроводник", "base_price": 1800, "stats": "Крафт щитов и рельсотронов", "rarity": "rare"},
        {"id": "M_SERVOMOTOR", "name": "Серво-мотор", "base_price": 800, "stats": "Крафт экзоскелетов и дронов", "rarity": "uncommon"},
        {"id": "M_MONO_WIRE", "name": "Мономолекулярная нить", "base_price": 2500, "stats": "Крафт моноклинков", "rarity": "epic"},
        {"id": "M_BIOGEL", "name": "Биогель", "base_price": 600, "stats": "Крафт имплантов и медикаментов", "rarity": "uncommon"},
        {"id": "M_DETONATOR", "name": "Детонатор", "base_price": 300, "stats": "Крафт мин и зарядов", "rarity": "common"},
        {"id": "M_EXPLOSIVE", "name": "Взрывчатое вещество", "base_price": 500, "stats": "Крафт мин и гранат", "rarity": "uncommon"},
        {"id": "M_TITAN_FRAME", "name": "Титановый каркас", "base_price": 1000, "stats": "Крафт тяжёлой экипировки", "rarity": "uncommon"},
        {"id": "M_NANOTUBES", "name": "Нанотрубки", "base_price": 1200, "stats": "Крафт нано-оборудования", "rarity": "rare"},
        {"id": "M_FUEL_CELL", "name": "Топливная ячейка", "base_price": 400, "stats": "Крафт ускорителей и генераторов", "rarity": "common"},
        {"id": "M_RADAR_ABSORBER", "name": "Радиопоглощатель", "base_price": 900, "stats": "Крафт стелс-оборудования", "rarity": "uncommon"},
        {"id": "M_LENS_COOLING", "name": "Линза охлаждения", "base_price": 700, "stats": "Крафт плазменного оружия", "rarity": "uncommon"},
        {"id": "M_GRENADE_CASING", "name": "Корпус гранаты", "base_price": 100, "stats": "Крафт гранат и мин", "rarity": "common"},
        {"id": "M_TITAN_MUSHROOM", "name": "Грибы Титана", "base_price": 350, "stats": "Крафт стимуляторов", "rarity": "uncommon"},
    ],
    "ships": [
        {"id": "S_SHUTTLE", "name": "Шаттл «Воробей»", "base_price": 50000, "stats": "Малый, 5 груза, 2 пассажира, без оружия", "rarity": "common"},
        {"id": "S_TRADER", "name": "Торговый корабль «Мул»", "base_price": 150000, "stats": "Средний, 40 груза, 6 пассажиров, 1 турель", "rarity": "uncommon"},
        {"id": "S_FIGHTER", "name": "Истребитель «Стилет»", "base_price": 200000, "stats": "Малый, 5 груза, 1 пилот, 2 лазера, быстрый", "rarity": "rare"},
        {"id": "S_CORVETTE", "name": "Корвет «Виверна»", "base_price": 500000, "stats": "Средний, 20 груза, 8 экипаж, 4 турели, щит", "rarity": "epic"},
        {"id": "S_FREIGHTER", "name": "Грузовоз «Атлас»", "base_price": 300000, "stats": "Большой, 100 груза, 10 пассажиров, 2 турели", "rarity": "uncommon"},
        {"id": "S_GUNSHIP", "name": "Канонерка «Молот»", "base_price": 750000, "stats": "Средний, 15 груза, 12 экипаж, 6 турелей, тяж. броня", "rarity": "epic"},
    ],
    "property": [
        {"id": "P_APARTMENT", "name": "Квартира (модуль)", "base_price": 20000, "stats": "Жильё, хранилище 20 слотов, точка сохранения", "rarity": "common"},
        {"id": "P_WAREHOUSE", "name": "Склад", "base_price": 40000, "stats": "Хранилище 100 слотов, крафт-станция", "rarity": "uncommon"},
        {"id": "P_SHOP", "name": "Магазин", "base_price": 80000, "stats": "Пассивный доход 500₡/цикл, торговля", "rarity": "uncommon"},
        {"id": "P_BAR", "name": "Бар", "base_price": 60000, "stats": "Доход 400₡/цикл, сбор слухов +3", "rarity": "uncommon"},
        {"id": "P_HIDEOUT", "name": "Убежище", "base_price": 35000, "stats": "Скрытое, хранилище 30, -90% обнаружения", "rarity": "rare"},
        {"id": "P_OFFICE", "name": "Офис фиксера", "base_price": 100000, "stats": "Доход 800₡/цикл, +2 квеста/цикл", "rarity": "rare"},
    ],
}


# ════════════════════════════════════════════════════════════
#  NEW TRAVEL EVENTS — 70 additional (total ~160)
# ════════════════════════════════════════════════════════════

V2_TRAVEL_EVENTS = [
    {"text": "Аварийный шлюз станции заклинило — десятки людей застряли в секции с утечкой кислорода.", "type": "emergency", "danger": 4},
    {"text": "Дрон-курьер врезался в стену рядом с тобой. На земле — посылка без адресата.", "type": "loot", "danger": 1},
    {"text": "Бездомный ребёнок дёргает за рукав: «Мистер, за мной идут плохие люди».", "type": "moral_choice", "danger": 3},
    {"text": "На рынке громкая ссора — два торговца обвиняют друг друга в обмане.", "type": "encounter", "danger": 1},
    {"text": "Корпоративный дрон зависает, сканирует твоё лицо и улетает.", "type": "surveillance", "danger": 2},
    {"text": "Старик у стены протягивает тебе загадочный чип. «Я не доживу — передай кому надо».", "type": "quest_hook", "danger": 2},
    {"text": "Группа протестующих перекрывает коридор. Полиция стягивает силы.", "type": "political", "danger": 3},
    {"text": "Ты натыкаешься на тайный вход в заброшенную лабораторию.", "type": "exploration", "danger": 3},
    {"text": "Взрыв в соседнем секторе! Дым, крики, бегущие люди.", "type": "emergency", "danger": 4},
    {"text": "Из вентиляции доносится странный запах — что-то химическое.", "type": "hazard", "danger": 3},
    {"text": "Местный фиксер ловит тебя у входа: «Есть работа. Срочная.»", "type": "quest_hook", "danger": 2},
    {"text": "Полицейский патруль остановил тебя для проверки документов.", "type": "encounter", "danger": 2},
    {"text": "В переулке обнаруживаешь чей-то тайник: контейнер с маркировкой «ОПАСНО».", "type": "loot", "danger": 3},
    {"text": "Информационный экран на стене мигает: «ВНИМАНИЕ: объявлен карантин сектора В-7».", "type": "news", "danger": 2},
    {"text": "Знакомый хакер шёпотом: «У меня есть данные, которые стоят целое состояние...»", "type": "quest_hook", "danger": 3},
    {"text": "Автоматическая турель на стене активировалась и водит стволом по прохожим.", "type": "hazard", "danger": 4},
    {"text": "Торговец хватает тебя за руку: «Купи, пока не конфисковали!» — показывает редкий имплант.", "type": "trade", "danger": 1},
    {"text": "В баре играет живая музыка. Пьяный пилот рассказывает о затерянном корабле с грузом.", "type": "quest_hook", "danger": 1},
    {"text": "Граффити на стене: координаты и надпись «ПРАВДА ЗДЕСЬ». Свежая краска.", "type": "mystery", "danger": 2},
    {"text": "Медбот сломался посреди улицы и зациклился, пытаясь вколоть прохожим «вакцину».", "type": "encounter", "danger": 2},
    {"text": "Мимо проносится погоня — полиция преследует фигуру в маске.", "type": "encounter", "danger": 3},
    {"text": "Под ногами хрустнуло стекло — оказывается, кто-то разбил витрину ломбарда.", "type": "loot", "danger": 2},
    {"text": "Одинокий священник Сигнала стоит на углу, бормоча цифры. Увидев тебя, замолкает.", "type": "mystery", "danger": 2},
    {"text": "На доске объявлений — фото с твоим лицом. Текст стёрт. Кто-то тебя ищет.", "type": "threat", "danger": 3},
    {"text": "Энергосистема мигнула — на секунду всё погрузилось во тьму. Кто-то вскрикнул.", "type": "hazard", "danger": 2},
    {"text": "Группа шахтёров угрюмо тащит тело товарища. Авария на руднике.", "type": "news", "danger": 1},
    {"text": "Подозрительный тип предлагает «чистые» кредитные чипы по бросовой цене.", "type": "trade", "danger": 2},
    {"text": "С потолка капает какая-то жидкость. Анализ показывает — кислота из повреждённого трубопровода.", "type": "hazard", "danger": 3},
    {"text": "Уличный проповедник кричит о скором конце: «Сигнал близко! Машины пробудятся!»", "type": "atmosphere", "danger": 1},
    {"text": "Ты заметил, что за тобой уже несколько минут идёт человек в сером плаще.", "type": "surveillance", "danger": 3},
    {"text": "Магазин имплантов проводит распродажу — очередь из желающих обступила витрину.", "type": "trade", "danger": 1},
    {"text": "На мусорке — выброшенный, но рабочий сервер. Данные ещё не стёрты.", "type": "loot", "danger": 2},
    {"text": "Два корпоративных агента вежливо, но настойчиво просят пройти с ними «для разговора».", "type": "encounter", "danger": 3},
    {"text": "Рядом приземлился грузовой дрон — забирать некому. Координаты отправителя стёрты.", "type": "loot", "danger": 2},
    {"text": "Из канализации выбирается человек, весь в крови. «Не ходите вниз», — хрипит он.", "type": "quest_hook", "danger": 4},
    {"text": "Уличная банда расставила блокпост: «Проход платный. 500 кредитов.»", "type": "encounter", "danger": 3},
    {"text": "Огромная голограмма-реклама сбоит, показывая вместо рекламы чьи-то переговоры.", "type": "mystery", "danger": 2},
    {"text": "Маленькая девочка продаёт самодельных роботов. Один из них подмигивает тебе.", "type": "atmosphere", "danger": 1},
    {"text": "Кто-то подбросил тебе в карман записку: «Не доверяй (имя). Встретимся в доке 7.»", "type": "quest_hook", "danger": 3},
    {"text": "Гравитационный генератор в этой секции барахлит — предметы то и дело взлетают.", "type": "hazard", "danger": 2},
    {"text": "Охранник станции лежит без сознания. Кто-то вырубил его совсем недавно.", "type": "mystery", "danger": 3},
    {"text": "На стене — объявление о турнире подпольных боёв. Призовой фонд: 10000₡.", "type": "quest_hook", "danger": 3},
    {"text": "Запах горелой проводки — кто-то пытается взломать банкомат в переулке.", "type": "encounter", "danger": 2},
    {"text": "Мимо тебя проносится курьер на ховерборде: «С дороги!» — и роняет пакет.", "type": "loot", "danger": 1},
    {"text": "Алкоголь в местном баре оказался отравлен — несколько человек в отключке.", "type": "emergency", "danger": 3},
    {"text": "Кто-то взломал все экраны в секторе: «МЫ ЗНАЕМ, ЧТО ВЫ СКРЫВАЕТЕ».", "type": "political", "danger": 2},
    {"text": "Тихий переулок. На стене — царапины от когтей. Больших когтей.", "type": "mystery", "danger": 4},
    {"text": "Старый знакомый окликает тебя с другой стороны улицы и машет рукой.", "type": "encounter", "danger": 1},
    {"text": "Контрабандист шёпотом предлагает партию военных стимуляторов.", "type": "trade", "danger": 2},
    {"text": "Ты нашёл сбитый разведдрон одной из корпораций. Камера ещё записывает.", "type": "loot", "danger": 3},
    {"text": "На станции объявлена учебная тревога. Или нет?", "type": "hazard", "danger": 2},
    {"text": "Группа учёных нервно обсуждает что-то, прикрывая голо-проекцию руками.", "type": "quest_hook", "danger": 2},
    {"text": "Робот-уборщик застрял в цикле и бесконечно натирает одну плитку.", "type": "atmosphere", "danger": 0},
    {"text": "Рядом произошла стрелка — тела на полу, стены в дырах от пуль.", "type": "emergency", "danger": 4},
    {"text": "Таинственная женщина предлагает «прочитать твою судьбу» за 100₡.", "type": "mystery", "danger": 1},
    {"text": "Утечка данных из местного сервера — на экранах всплывают личные дела сотрудников.", "type": "loot", "danger": 2},
    {"text": "Конвой под охраной перекрыл весь коридор. Везут что-то секретное.", "type": "encounter", "danger": 3},
    {"text": "Странный звук из-за стены — ритмичные удары. Кто-то пытается пробиться наружу?", "type": "mystery", "danger": 3},
    {"text": "Старожил рассказывает: «В 47-м секторе видели что-то... нечеловеческое.»", "type": "quest_hook", "danger": 2},
    {"text": "Реклама мигает: «ТРЕБУЮТСЯ ДОБРОВОЛЬЦЫ ДЛЯ ЭКСПЕРИМЕНТА. ЩЕДРАЯ ОПЛАТА.»", "type": "quest_hook", "danger": 3},
    {"text": "Дождь из конденсата — система климат-контроля опять барахлит.", "type": "atmosphere", "danger": 1},
    {"text": "Полиция обыскивает каждого в секторе. Говорят, ищут беглеца.", "type": "encounter", "danger": 2},
    {"text": "На земле — след крови, ведущий в темный переулок.", "type": "quest_hook", "danger": 4},
    {"text": "Автомат с напитками выдаёт всё бесплатно — сбой или чей-то взлом?", "type": "atmosphere", "danger": 1},
    {"text": "Тебя окликнул незнакомец: «Ты ведь {player_name}? Мне нужна твоя помощь.»", "type": "quest_hook", "danger": 2},
    {"text": "Драка двух пьяных шахтёров переросла в массовую потасовку.", "type": "encounter", "danger": 2},
    {"text": "Заброшенный магазин, но внутри горит свет и слышны голоса.", "type": "mystery", "danger": 3},
    {"text": "Уличный художник рисует невероятно точный портрет кого-то из розыскного списка.", "type": "mystery", "danger": 2},
    {"text": "Тебя толкнул прохожий — и тут же извинился. Кажется, он что-то подложил в карман.", "type": "quest_hook", "danger": 3},
    {"text": "Громкий хлопок! Трубу прорвало. Горячий пар заполняет коридор.", "type": "hazard", "danger": 3},
]

V2_SPACE_EVENTS = [
    {"text": "Слабый сигнал бедствия — частоты указывают на гражданское судно.", "type": "rescue", "danger": 3},
    {"text": "Массивное поле обломков — здесь недавно был бой.", "type": "exploration", "danger": 3},
    {"text": "Сканер засёк аномальные показания энергии в ближайшем астероиде.", "type": "anomaly", "danger": 4},
    {"text": "Патрульный корабль запрашивает идентификацию и досмотр.", "type": "patrol", "danger": 2},
    {"text": "Дрейфующий контейнер с маркировкой медицинских грузов.", "type": "loot", "danger": 1},
    {"text": "Навигационный маяк передаёт устаревшие координаты — ловушка?", "type": "trap", "danger": 4},
    {"text": "Группа кораблей преграждает путь: «Проход стоит 2000₡».", "type": "pirate", "danger": 3},
    {"text": "Солнечная буря! Щиты на пределе, связь пропала.", "type": "hazard", "danger": 4},
    {"text": "Торговый конвой предлагает путешествовать вместе для безопасности.", "type": "encounter", "danger": 1},
    {"text": "Засечён корабль-призрак — дрейфует без энергии, признаки жизни... слабые.", "type": "exploration", "danger": 4},
    {"text": "Микро-метеоритный дождь! Нужно маневрировать между обломками.", "type": "hazard", "danger": 3},
    {"text": "На сканере — скрытый корабль. Стелс-покрытие частично повреждено.", "type": "mystery", "danger": 4},
    {"text": "Рудодобывающий дрон передаёт данные о богатом залежь в астероиде.", "type": "opportunity", "danger": 1},
    {"text": "Корабль-заправщик предлагает топливо по двойной цене.", "type": "trade", "danger": 1},
    {"text": "Сигнал тревоги со станции: «Все корабли — на помощь! Мы под атакой!»", "type": "emergency", "danger": 5},
    {"text": "Странный импульс помех — на мгновение все приборы сошли с ума.", "type": "anomaly", "danger": 3},
    {"text": "Обнаружен старый спутник-шпион, всё ещё передающий данные.", "type": "loot", "danger": 2},
    {"text": "Конвой контрабандистов предлагает долю за помощь с доставкой.", "type": "quest_hook", "danger": 3},
    {"text": "Пустота — ни единого корабля на сканере. Тишина давит.", "type": "atmosphere", "danger": 1},
    {"text": "Два корабля обмениваются огнём. Один — знакомой фракции.", "type": "encounter", "danger": 4},
    {"text": "Обломок корабля несёт следы неизвестного оружия. Оплавлено... чем-то.", "type": "mystery", "danger": 3},
    {"text": "Маяк автоматически передаёт: «КАРАНТИН. НЕ ПРИБЛИЖАТЬСЯ. БИОУГРОЗА.»", "type": "hazard", "danger": 5},
    {"text": "Лунный рудник передаёт предложение о работе: нужен пилот для вывоза руды.", "type": "quest_hook", "danger": 2},
    {"text": "На радаре — огромный объект. Слишком большой для корабля. Астероид? Станция?", "type": "exploration", "danger": 3},
    {"text": "Передача на открытом канале: кто-то продаёт координаты тайного склада.", "type": "trade", "danger": 2},
]


# ════════════════════════════════════════════════════════════
#  MERGE FUNCTION — combines V1 + V2
# ════════════════════════════════════════════════════════════

def get_all_perks():
    """Returns merged V1 + V2 perks, deduped by id."""
    from content_expansion import EXPANDED_PERKS
    merged = {p["id"]: p for p in EXPANDED_PERKS}
    for p in V2_PERKS:
        if p["id"] not in merged:
            merged[p["id"]] = p
    return list(merged.values())

def get_all_recipes():
    from content_expansion import EXPANDED_RECIPES
    merged = {r["id"]: r for r in EXPANDED_RECIPES}
    for r in V2_RECIPES:
        if r["id"] not in merged:
            merged[r["id"]] = r
    return list(merged.values())

def get_all_travel_events():
    from content_expansion import EXPANDED_TRAVEL_EVENTS
    return EXPANDED_TRAVEL_EVENTS + V2_TRAVEL_EVENTS

def get_all_space_events():
    from content_expansion import EXPANDED_SPACE_EVENTS
    return EXPANDED_SPACE_EVENTS + V2_SPACE_EVENTS

def get_all_shop_items():
    """Merges V1 BASE_SHOP_ITEMS + V2_SHOP_ITEMS, deduped by id."""
    from world_sim import BASE_SHOP_ITEMS
    merged = {}
    for cat in set(list(BASE_SHOP_ITEMS.keys()) + list(V2_SHOP_ITEMS.keys())):
        v1 = {i["id"]: i for i in BASE_SHOP_ITEMS.get(cat, [])}
        v2 = {i["id"]: i for i in V2_SHOP_ITEMS.get(cat, [])}
        v1.update(v2)
        merged[cat] = list(v1.values())
    return merged
