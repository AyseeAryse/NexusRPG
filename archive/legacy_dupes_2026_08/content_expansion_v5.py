"""
Content Expansion V5:
1. Unique NPCs (30 штук) — запоминающиеся персонажи с квестами и расписанием
2. Event Effects → World — тировые события влияют на цены, фракции, доступ
3. Auto-Reputation — автоматическое изменение репутации за действия
"""

# ════════════════════════════════════════════════════════════
#  1. UNIQUE NPCs — 30 персонажей
# ════════════════════════════════════════════════════════════

UNIQUE_NPCS = [
    # ═══ ТОРГОВЦЫ ═══
    {"id": "NPC_TRADER_HASSAN", "name": "Хассан Аль-Рашид", "role": "Торговец оружием",
     "location": "Церера, Рынок Теней", "faction": "Ghost Merchants",
     "description": "Слепой торговец, который 'видит' через нано-импланты. Торгует запрещённым оружием, но никогда не продаёт детям и фанатикам.",
     "personality": "Философски спокойный, мудрый, говорит загадками",
     "services": ["rare_weapons", "weapon_mods", "information"],
     "schedule": {"day": "Рынок Теней, стенд 47", "night": "Медитация, недоступен"},
     "dialogue_hook": "Я вижу, что тебе нужно. Вопрос — готов ли ты заплатить цену?",
     "quest_hook": "Просит найти украденный клинок — семейную реликвию 300-летней давности"},

    {"id": "NPC_TRADER_YUKI", "name": "Юки Танака", "role": "Чёрная аптекарь",
     "location": "Нью-Токио (Марс), переулок Лотоса", "faction": None,
     "description": "Подпольный фармацевт, создающая любые стимуляторы на заказ. Бывший химик Protogen.",
     "personality": "Тихая, параноидальная, гениальная, зависима от собственной продукции",
     "services": ["stims", "antidotes", "custom_drugs", "protogen_intel"],
     "schedule": {"day": "Спит", "night": "Лаборатория, принимает клиентов"},
     "dialogue_hook": "Без имён. Без вопросов. Что нужно?",
     "quest_hook": "Хочет уничтожить формулу боевого стимулятора, который Protogen планирует массово производить"},

    {"id": "NPC_TRADER_FRITZ", "name": "Фриц «Свалка» Мюллер", "role": "Утилизатор",
     "location": "Пояс, станция «Обломки»", "faction": "Rust Hawks",
     "description": "Торгует всем, что нашёл в обломках кораблей. Иногда — частями тел. Иногда — артефактами.",
     "personality": "Жизнерадостный, нечистоплотный, бесстрашный",
     "services": ["salvage", "ship_parts", "rare_tech", "questionable_items"],
     "schedule": {"day": "Мастерская", "night": "Бар, пьёт"},
     "dialogue_hook": "А-а! Покупатель! Смотри что я нашёл сегодня — ты не поверишь!",
     "quest_hook": "Нашёл в обломках чёрный ящик военного корабля. Несколько фракций хотят его."},

    # ═══ ИНФОРМАТОРЫ ═══
    {"id": "NPC_INFO_DRUMMER", "name": "Камина «Барабан» Юнг", "role": "Информатор OPA",
     "location": "Тихе, бар «Свободный Пояс»", "faction": "OPA",
     "description": "Лидер ячейки OPA на Тихе. Харизматичная, жёсткая, не прощает предательства.",
     "personality": "Властная, прямая, страстная, опасная",
     "services": ["opa_quests", "belt_intel", "safe_houses"],
     "schedule": {"day": "Штаб OPA", "night": "Бар, агитация"},
     "dialogue_hook": "Пояс помнит. Ты с нами или против нас?",
     "quest_hook": "OPA узнала о тайной программе перевоспитания поясных детей на Земле"},

    {"id": "NPC_INFO_DAWES", "name": "Андерсон Прайс", "role": "Политик OPA",
     "location": "Церера, правительственный район", "faction": "OPA",
     "description": "Умеренное крыло OPA. Верит в дипломатию, а не в бомбы. Элегантный, образованный, опасный.",
     "personality": "Дипломатичный, хитрый, принципиальный по-своему",
     "services": ["political_quests", "diplomatic_contacts", "legal_help"],
     "schedule": {"day": "Кабинет", "night": "Приёмы"},
     "dialogue_hook": "Насилие — инструмент слабых. У нас есть инструменты посильнее.",
     "quest_hook": "Нужен посредник для секретных переговоров между OPA и ESA"},

    {"id": "NPC_INFO_CORTEZ", "name": "Мария Кортез", "role": "Шпионка ООН",
     "location": "Меняет локацию", "faction": "Earth UN Investigations",
     "description": "Шпионка под прикрытием. Контактирует через мёртвые почтовые ящики.",
     "personality": "Хладнокровная, профессиональная, одинокая",
     "services": ["earth_intel", "counter_intel", "identity_documents"],
     "schedule": {"day": "Под прикрытием", "night": "Связь через закладки"},
     "dialogue_hook": "Я знаю, кто ты. Вопрос — знаешь ли ты, кто я?",
     "quest_hook": "Обнаружила заговор внутри ООН — но не знает кому доверять"},

    # ═══ КВЕСТОДАТЕЛИ ═══
    {"id": "NPC_QUEST_FRED", "name": "Фред «Мясник» Джонсон", "role": "Лидер OPA на Тихе",
     "location": "Тихе, командный центр", "faction": "OPA",
     "description": "Бывший земной генерал, перешедший на сторону Пояса. Легенда для одних, предатель для других.",
     "personality": "Решительный, мудрый, несёт тяжкий груз прошлого",
     "services": ["major_quests", "fleet_access", "military_intel"],
     "dialogue_hook": "У меня есть работа. Опасная. Но может спасти тысячи жизней.",
     "quest_hook": "Планирует рискованную операцию по захвату протогенской лаборатории"},

    {"id": "NPC_QUEST_AVASARALA", "name": "Секретарь Чандра Кхан", "role": "Политик Земли",
     "location": "Земля, здание ООН", "faction": "ESA-Earth",
     "description": "Самый влиятельный человек на Земле. Острый ум, острый язык, руки в крови до локтей.",
     "personality": "Макиавеллиевская, остроумная, патриотичная, безжалостная",
     "services": ["political_quests", "earth_resources", "diplomatic_immunity"],
     "dialogue_hook": "Мне плевать на ваши чувства. Мне нужны результаты.",
     "quest_hook": "Хочет предотвратить войну — но для этого нужно начать маленькую войну"},

    {"id": "NPC_QUEST_MAO", "name": "Жюль-Пьер Мао", "role": "CEO Mao-Kwikowski",
     "location": "Мобильный (яхта «Гуаньси»)", "faction": "Mao-Kwikowski",
     "description": "Один из богатейших людей в системе. Финансирует Protogen. Убеждён, что всё ради прогресса.",
     "personality": "Утончённый, безжалостный, рационализирующий зло",
     "services": ["ultra_high_pay_quests", "protogen_access", "corporate_intel"],
     "dialogue_hook": "Прогресс требует жертв. Вопрос — кто жертвует, а кто жертва?",
     "quest_hook": "Предлагает миллионы за артефакт с Эроса — но зачем он ему?"},

    # ═══ МАСТЕРСКИЕ / СЕРВИСЫ ═══
    {"id": "NPC_MECH_TYCHO", "name": "Бэкс Тайхо", "role": "Корабельный механик",
     "location": "Тихе, верфь 12", "faction": "Titan Shipyards Collective",
     "description": "Лучший корабельный механик в Поясе. Берёт дорого, делает идеально.",
     "personality": "Перфекционист, немногословный, гордый",
     "services": ["ship_repair", "ship_upgrade", "custom_mods"],
     "dialogue_hook": "Я починю. Но не торопи. Торопливость — причина 80% аварий.",
     "quest_hook": "Нужен редкий сплав для секретного проекта — новый тип двигателя"},

    {"id": "NPC_MECH_RIPPER", "name": "Др. «Потрошитель» Ли", "role": "Подпольный кибердоктор",
     "location": "Церера, уровень -5, клиника", "faction": "CyberMedix",
     "description": "Ставит импланты без лицензии, вопросов и наркоза (по желанию). Руки хирурга, совесть пирата.",
     "personality": "Циничный, профессиональный, любит чёрный юмор",
     "services": ["implant_install", "implant_removal", "black_market_implants"],
     "dialogue_hook": "Руку? Глаз? Полную нервную систему? Бюджет?",
     "quest_hook": "Обнаружил бэкдор в импланте клиента — кто-то следит через все импланты CyberMedix"},

    {"id": "NPC_MECH_TINKER", "name": "Оливия «Тинкер» Рамирез", "role": "Оружейник",
     "location": "Нью-Токио, подвал «Стальная Роза»", "faction": "ArmorWorks",
     "description": "Создаёт кастомное оружие из мусора и гениальности. Каждый ствол — произведение искусства.",
     "personality": "Энтузиастка, болтушка, маниакально увлечённая огнестрелом",
     "services": ["weapon_crafting", "weapon_mods", "custom_ammo"],
     "dialogue_hook": "СМОТРИ! Я сделала рельсовый пистолет из кофеварки! Хочешь?!",
     "quest_hook": "Мечтает создать идеальное оружие — но нужен прототип из Марсианского арсенала"},

    # ═══ БАРМЕНЫ / СВЯЗНЫЕ ═══
    {"id": "NPC_BAR_DAWSON", "name": "Мэтт Доусон", "role": "Бармен «Синий Сокол»",
     "location": "Церера, бар «Синий Сокол»", "faction": None,
     "description": "Легендарный бар на Церере. Мэтт знает все слухи, видит всех, молчит — если не заплатить.",
     "personality": "Невозмутимый, мудрый, нейтральный",
     "services": ["rumors", "contacts", "safe_meetings"],
     "dialogue_hook": "Обычное? Или... информация?",
     "quest_hook": "Слышал, что кто-то планирует взорвать водоочистную станцию Цереры"},

    {"id": "NPC_BAR_LUNA", "name": "Луна (только имя)", "role": "Танцовщица / информатор",
     "location": "Нью-Токио, клуб «Электра»", "faction": "Shadow Consortium",
     "description": "Танцовщица в элитном клубе. На самом деле — глаза и уши Консорциума на Марсе.",
     "personality": "Обольстительная, опасная, трагичная",
     "services": ["mars_intel", "seduction_missions", "vip_access"],
     "dialogue_hook": "Танец? Или... другой вид развлечения? Информация, например.",
     "quest_hook": "Хочет сбежать из Консорциума, но знает слишком много"},

    # ═══ АВТОРИТЕТЫ ═══
    {"id": "NPC_BOSS_SERPENT", "name": "Серебряная Королева", "role": "Глава Silver Serpents",
     "location": "Марс, нижние уровни, тронный зал", "faction": "Silver Serpents",
     "description": "Никто не знает настоящего имени. Маска серебряной змеи. Контролирует наркоторговлю Марса.",
     "personality": "Величественная, жестокая, стратегически гениальная",
     "services": ["drug_trade", "mars_underworld", "assassination"],
     "dialogue_hook": "Ты пришёл ко мне. Значит, тебе нужно то, что не продаётся. Или наоборот.",
     "quest_hook": "Хочет уничтожить конкурирующий синдикат и нанимает 'специалиста'"},

    {"id": "NPC_BOSS_INAROS", "name": "Марко «Свободный» Инарос", "role": "Лидер радикалов OPA",
     "location": "Мобильный (корабль «Пелла»)", "faction": "OPA",
     "description": "Харизматичный экстремист. Мечтает о независимости Пояса любой ценой, включая миллионы жизней.",
     "personality": "Нарциссичный, харизматичный, фанатичный, опасный",
     "services": ["radical_quests", "weapons", "guerrilla_training"],
     "dialogue_hook": "Они называют нас террористами. Они называли каждого борца за свободу террористом.",
     "quest_hook": "Планирует атаку на Землю — остановить или помочь?"},

    {"id": "NPC_BOSS_PHANTOM", "name": "Капитан «Фантом»", "role": "Лидер Shadow Corsairs",
     "location": "Неизвестна (корабль «Мираж»)", "faction": "Shadow Corsairs",
     "description": "Элитный пират. Бывший адмирал, инсценировавший смерть. Грабит только корпорации.",
     "personality": "Благородный, саркастичный, тактический гений",
     "services": ["pirate_quests", "naval_tactics", "stolen_cargo"],
     "dialogue_hook": "Я не вор. Я перераспределяю ресурсы. С элегантностью.",
     "quest_hook": "Планирует «ограбление века» — корабль с золотом 5 мегакорпораций"},

    # ═══ УЧЁНЫЕ / СПЕЦИАЛИСТЫ ═══
    {"id": "NPC_SCI_ELENA", "name": "Др. Елена Ковалёва", "role": "Глава Scientific Assembly",
     "location": "Ганимед, Научная Станция Альфа", "faction": "Scientific Assembly",
     "description": "Нобелевский лауреат, посвятившая жизнь науке. Единственный человек, которому доверяют все фракции.",
     "personality": "Мягкая, решительная, бескомпромиссная в науке",
     "services": ["research_quests", "scientific_analysis", "neutral_mediation"],
     "dialogue_hook": "Знание — единственное, что нельзя украсть навсегда. Помогите мне найти его.",
     "quest_hook": "Расшифровала сигнал из-за пределов системы — нужна экспедиция"},

    {"id": "NPC_SCI_PROTO", "name": "Др. Юлиан Стресса", "role": "Бывший учёный Protogen",
     "location": "Скрывается (станция «Туман»)", "faction": None,
     "description": "Создатель протомолекулы. Сбежал из Protogen, когда понял масштаб ужаса. Живёт в страхе и вине.",
     "personality": "Сломленный, гениальный, отчаянно пытается искупить грехи",
     "services": ["protogen_data", "nano_research", "cure_development"],
     "dialogue_hook": "Я создал монстра. Теперь я должен его убить. Помогите мне.",
     "quest_hook": "Знает, как уничтожить протомолекулу, но нужна его бывшая лаборатория"},

    # ═══ СЛУЧАЙНЫЕ / КОЛОРИТНЫЕ ═══
    {"id": "NPC_COLOR_PREACHER", "name": "Пророк Исайя", "role": "Уличный проповедник",
     "location": "Церера, площадь Медузы", "faction": "Mystic Order",
     "description": "Безумный или прозорливый? Предсказывает события с пугающей точностью. Живёт на подаяния.",
     "personality": "Экстатичный, загадочный, непредсказуемый",
     "services": ["prophecies", "cryptic_hints", "spiritual_guidance"],
     "dialogue_hook": "Звёзды говорят! Тебе! Именно тебе! Слушай! СЛУШАЙ!",
     "quest_hook": "Его 'пророчества' — не бред, а расшифрованные перехваты военных передач"},

    {"id": "NPC_COLOR_CHEF", "name": "Шеф Гюнтер", "role": "Повар",
     "location": "Тихе, ресторан «Последний ужин»", "faction": None,
     "description": "Готовит настоящую еду из настоящих продуктов. На станции это роскошь. Еда лечит тело и душу.",
     "personality": "Страстный, громкий, щедрый, строгий к качеству",
     "services": ["meals_heal", "morale_boost", "gossip"],
     "dialogue_hook": "САДИСЬ! ЕШЬ! Потом поговорим. На голодный желудок не думают!",
     "quest_hook": "Нужны настоящие специи с Земли — готов заплатить состояние"},

    {"id": "NPC_COLOR_GAMBLER", "name": "Удача (азартный игрок)", "role": "Игрок",
     "location": "Любое казино", "faction": "Black Lotus Triad",
     "description": "Легендарный игрок, который никогда не проигрывает. Секрет? Имплант, считающий карты.",
     "personality": "Обаятельный, самоуверенный, тайно одинокий",
     "services": ["gambling_partner", "casino_intel", "money_laundering"],
     "dialogue_hook": "Партейку? Только не плачь, когда проиграешь.",
     "quest_hook": "Триада хочет его мёртвым за последний выигрыш — 2 миллиона кредитов"},

    {"id": "NPC_COLOR_ARTIST", "name": "НОВА (уличная художница)", "role": "Граффити-артист",
     "location": "Церера, нижние уровни", "faction": "OPA",
     "description": "Рисует фрески на стенах станций. Каждая — послание. OPA использует их для кодированной связи.",
     "personality": "Бунтарская, творческая, идеалистичная",
     "services": ["coded_messages", "opa_contact", "art_morale"],
     "dialogue_hook": "Стены говорят. Надо только уметь слушать.",
     "quest_hook": "Её последняя фреска содержит координаты секретной базы — и Star Helix хочет её закрасить"},

    {"id": "NPC_COLOR_VETERAN", "name": "Старик Чжоу", "role": "Ветеран войны",
     "location": "Тихе, парк ветеранов", "faction": None,
     "description": "Ветеран первой войны Земля-Марс. 90 лет. Помнит всё. Рассказывает истории всем, кто слушает.",
     "personality": "Мудрый, ностальгический, сердитый на молодых за повторение ошибок",
     "services": ["war_stories_lore", "historical_intel", "veteran_contacts"],
     "dialogue_hook": "Сядь. Послушай. Может, не повторишь наших ошибок.",
     "quest_hook": "Знает местоположение тайника с оружием первой войны — всё ещё работает"},

    {"id": "NPC_COLOR_ORPHAN_LEADER", "name": "Большая Сестра (Аника)", "role": "Глава сиротского дома",
     "location": "Ганимед, приют «Солнечный луч»", "faction": None,
     "description": "Бывшая боевая медсестра, теперь защищает 40 сирот. Убьёт любого, кто угрожает детям.",
     "personality": "Материнская, жёсткая, самоотверженная, устрашающая когда злится",
     "services": ["information_from_kids", "safe_house", "moral_compass"],
     "dialogue_hook": "Дети — единственное чистое, что осталось в этом мире. Не трогай их.",
     "quest_hook": "Кто-то похищает сирот по всему Поясу. Нужно найти и остановить."},

    {"id": "NPC_COLOR_ANDROID", "name": "Джейн Доу (андроид)", "role": "Загадка",
     "location": "Неизвестна, появляется случайно", "faction": None,
     "description": "Выглядит как человек, но... не совсем. Появляется в ключевые моменты. Никто не знает откуда.",
     "personality": "Пугающе спокойная, всезнающая, помогает без объяснения причин",
     "services": ["cryptic_warnings", "impossible_saves", "mystery"],
     "dialogue_hook": "Не сейчас. Через 3 часа повернёшь налево, не направо. Поверь мне.",
     "quest_hook": "Кто она? Что она? Почему помогает? Это загадка на всю игру."},

    # ═══ ДОПОЛНИТЕЛЬНЫЕ NPC ═══
    {"id": "NPC_FENCE_VIPER", "name": "Гадюка (только прозвище)", "role": "Скупщик краденого",
     "location": "Церера, уровень -3, трущобы", "faction": "Shadow Consortium",
     "description": "Скупает и перепродаёт всё. Шёпот — единственный его тон. У него нет лица — хирургически удалено.",
     "personality": "Параноидальный, расчётливый, уважает профессионалов",
     "services": ["fence_stolen_goods", "black_market_trade", "fake_ids"],
     "schedule": {"day": "Спит в бронированном контейнере", "night": "Принимает товар с 22:00"},
     "dialogue_hook": "Покажи. Молча. Если устроит — моргну.",
     "quest_hook": "Перехватил военный прототип — продать его могут все, но за покупателями охотятся спецслужбы трёх фракций"},

    {"id": "NPC_PILOT_ACE", "name": "Катерина «Комета» Орлова", "role": "Пилот-гонщица",
     "location": "Тихе, лётная палуба, ангар 7", "faction": None,
     "description": "Чемпионка гонки «Кольцо Сатурна» трижды. Теперь работает курьером — но мечтает о четвёртой победе.",
     "personality": "Адреналиновая, весёлая, бесстрашная, скрыто грустная",
     "services": ["fast_transport", "piloting_lessons", "racing_intel"],
     "schedule": {"day": "Ангар, чинит корабль", "night": "Бар, рассказывает байки"},
     "dialogue_hook": "Куда летим? Только быстро — я не умею медленно.",
     "quest_hook": "Её бывший штурман украл её корабль и участвует в нелегальных гонках под её именем"},

    {"id": "NPC_LAWYER_SINGH", "name": "Адвокат Равиндер Сингх", "role": "Космический юрист",
     "location": "Церера, бизнес-уровень, офис 4401", "faction": "Earth UN",
     "description": "Единственный честный адвокат в Поясе (по его словам). Берёт дорого, но вытаскивает из любой тюрьмы.",
     "personality": "Педантичный, красноречивый, тайно идеалистичный",
     "services": ["legal_defense", "contract_review", "bail", "corporate_lawsuits"],
     "schedule": {"day": "Офис, приём клиентов", "night": "Библиотека, изучает прецеденты"},
     "dialogue_hook": "Не говорите ничего. Вообще ничего. Я ваш адвокат — теперь говорю только я.",
     "quest_hook": "Взялся за дело против Mao-Kwikowski — нужны доказательства из их серверов"},

    {"id": "NPC_DOC_MERCY", "name": "Др. Мерси Адаму", "role": "Полевой хирург",
     "location": "Ганимед, медицинский район", "faction": "Scientific Assembly",
     "description": "Хирург без границ. Лечит всех — пиратов, полицейских, террористов. Никому не отказывает, ни за кого не выбирает сторону.",
     "personality": "Стоическая, измождённая, непреклонная в своих принципах",
     "services": ["healing", "surgery", "implant_check", "poison_cure"],
     "schedule": {"day": "Клиника, операции", "night": "Клиника, приём раненых"},
     "dialogue_hook": "Ложитесь. Молчите. Вопросы потом — если выживете.",
     "quest_hook": "Фракция хочет заставить её выдать пациента. Она отказывается. Нужна защита."},
]


# ════════════════════════════════════════════════════════════
#  2. EVENT EFFECTS → WORLD
# ════════════════════════════════════════════════════════════

# Эффекты событий, которые реально влияют на мир
EVENT_WORLD_EFFECTS = {
    # Effect key → handler description
    "trade_disruption": {"price_mod": 1.4, "affected_categories": ["all"], "duration_hours": 720},
    "trade_prices": {"price_mod_pct": True},  # value = percentage increase
    "trade_halt": {"price_mod": 3.0, "affected_categories": ["all"], "duration_hours": 2160},
    "economy_crash": {"price_mod": 0.5, "sell_penalty": 0.3, "duration_hours": 4320},
    "energy_prices": {"price_mod_pct": True, "affected_categories": ["consumables", "gadgets"]},
    "weapons_prices": {"price_mod_pct": True, "affected_categories": ["weapons", "armor"]},
    "smuggling_demand": {"black_market_bonus": 0.3},
    "medical_demand": {"price_mod": 2.0, "affected_categories": ["consumables"], "duration_hours": 720},
    "rare_items": {"unlock_rare_stock": True, "duration_hours": 720},
    "implant_discount": {"price_mod": 0.8, "affected_categories": ["implants"]},
    "tech_trade": {"price_mod": 0.85, "affected_categories": ["gadgets", "implants"]},
    "piracy_surge": {"travel_danger": 2.0, "escort_price": 1.5},
    "security_alert": {"patrol_increase": True, "crime_penalty": 2.0},
    "martial_law": {"curfew": True, "weapon_check": True},
    "area_lockdown": {"travel_blocked": True, "duration_hours": 240},
    "communications_down": {"no_fast_travel": True, "quest_timer_paused": True},
    "all_factions_war": {"all_rep_volatile": True, "combat_everywhere": True},
}


class ActiveWorldEffect:
    """Tracks an active world effect from an event."""
    def __init__(self, effect_key: str, value, source_event_id: str, 
                 start_hours: int, duration_hours: int):
        self.effect_key = effect_key
        self.value = value
        self.source_event_id = source_event_id
        self.start_hours = start_hours
        self.duration_hours = duration_hours
    
    def is_expired(self, current_hours: int) -> bool:
        return current_hours - self.start_hours >= self.duration_hours

    def to_dict(self, current_hours: int = 0):
        remaining = max(0, self.duration_hours - (current_hours - self.start_hours))
        return {"effect": self.effect_key, "value": self.value,
                "source": self.source_event_id, "remaining_hours": remaining}


class WorldEffectsManager:
    """Applies and tracks event effects on the game world."""
    
    def __init__(self):
        self.active_effects: list[ActiveWorldEffect] = []
    
    def apply_event_effects(self, event: dict, current_hours: int):
        """Apply effects from a tiered event to the world."""
        effects = event.get("effects", {})
        event_id = event.get("id", "unknown")
        duration_days = event.get("duration_days", event.get("duration", 1))
        duration_hours = duration_days * 24
        
        for key, value in effects.items():
            if key in EVENT_WORLD_EFFECTS:
                template = EVENT_WORLD_EFFECTS[key]
                dur = template.get("duration_hours", duration_hours)
                self.active_effects.append(
                    ActiveWorldEffect(key, value, event_id, current_hours, dur))
    
    def get_price_modifier(self, category: str = "all", current_hours: int = 0) -> float:
        """Calculate cumulative price modifier from all active effects."""
        modifier = 1.0
        for eff in self.active_effects:
            if eff.is_expired(current_hours):
                continue
            template = EVENT_WORLD_EFFECTS.get(eff.effect_key, {})
            cats = template.get("affected_categories", [])
            if "all" in cats or category in cats:
                if "price_mod" in template:
                    modifier *= template["price_mod"]
                elif template.get("price_mod_pct"):
                    modifier *= (1.0 + eff.value / 100.0)
        return round(modifier, 2)
    
    def is_area_locked(self, current_hours: int = 0) -> bool:
        for eff in self.active_effects:
            if eff.effect_key == "area_lockdown" and not eff.is_expired(current_hours):
                return True
        return False
    
    def is_martial_law(self, current_hours: int = 0) -> bool:
        for eff in self.active_effects:
            if eff.effect_key == "martial_law" and not eff.is_expired(current_hours):
                return True
        return False
    
    def get_active_effects_summary(self, current_hours: int = 0) -> list:
        """Return human-readable summary of active effects."""
        self._cleanup(current_hours)
        results = []
        for eff in self.active_effects:
            results.append(eff.to_dict(current_hours))
        return results
    
    def _cleanup(self, current_hours: int):
        self.active_effects = [e for e in self.active_effects if not e.is_expired(current_hours)]


# ════════════════════════════════════════════════════════════
#  3. AUTO-REPUTATION — за действия игрока
# ════════════════════════════════════════════════════════════

# Триггерные слова в действиях → изменения репутации
ACTION_REPUTATION_MAP = {
    # ═══ БОЕВЫЕ ═══
    "убить пирата": {"Star Helix Dynamics": 3, "Belt Raiders": -5, "Crimson Talons": -3},
    "kill pirate": {"Star Helix Dynamics": 3, "Belt Raiders": -5, "Crimson Talons": -3},
    "убить охранника": {"Star Helix Dynamics": -5, "OPA": 2, "Shadow Consortium": 2},
    "убить полицейского": {"Star Helix Dynamics": -10, "Earth UN": -5, "OPA": 3, "Belt Raiders": 2},
    "атаковать корпорацию": {"OPA": 3, "Belt Raiders": 2, "Shadow Consortium": 2, "Earth UN": -3},
    "атаковать opaшника": {"Earth UN": 3, "Star Helix Dynamics": 3, "OPA": -10},
    "защитить станцию": {"Ceres Mining Consortium": 5, "Star Helix Dynamics": 3, "OPA": 2},
    "защитить гражданских": {"Star Helix Dynamics": 3, "Earth UN": 2, "OPA": 2},
    "абордаж": {"Belt Raiders": 3, "Crimson Talons": 3, "Star Helix Dynamics": -5},
    "захватить корабль": {"Belt Raiders": 5, "Shadow Corsairs": 3, "Star Helix Dynamics": -5},
    "уничтожить корабль": {"Mars Fleet": -3, "Belt Raiders": 2},
    "напасть на конвой": {"Belt Raiders": 5, "Crimson Talons": 3, "BeltFreight Ltd.": -5, "Star Helix Dynamics": -5},
    "убить наёмник": {"Bronze Tigers": -5, "Mars Fleet": -3},
    "убить марсианского": {"Mars Republic": -8, "Mars Fleet": -5, "OPA": 3},
    "убить земного": {"Earth UN": -8, "ESA-Earth": -5, "OPA": 2},
    "драка в баре": {"Belt Raiders": 1, "Crimson Talons": 1},
    "сдаться": {"Star Helix Dynamics": 2, "Earth UN": 1, "OPA": -2},

    # ═══ КОНТРАБАНДА / КРИМИНАЛ ═══
    "продать контрабанд": {"Shadow Consortium": 3, "Ghost Merchants": 3, "Star Helix Dynamics": -3},
    "smuggle": {"Shadow Consortium": 3, "Ghost Merchants": 3, "Star Helix Dynamics": -3},
    "торговать легально": {"Earth UN": 1, "ESA-Earth": 1, "BeltFreight Ltd.": 2},
    "торговать наркотик": {"Silver Serpents": 5, "Black Lotus Triad": 3, "Star Helix Dynamics": -5},
    "перевозить груз": {"BeltFreight Ltd.": 2, "Ghost Merchants": 1},
    "украсть": {"Shadow Consortium": 2, "Star Helix Dynamics": -3, "Silver Serpents": 1},
    "ограбить": {"Belt Raiders": 3, "Star Helix Dynamics": -5, "Shadow Consortium": 2},
    "подделать документ": {"Ghost Merchants": 3, "Shadow Consortium": 2, "Earth UN": -3},
    "отмыть деньги": {"Black Lotus Triad": 3, "Shadow Consortium": 3, "Star Helix Dynamics": -2},
    "продать оружие": {"ArmorWorks": 2, "Star Helix Dynamics": -2},
    "продать информац": {"Ghost Merchants": 5, "Shadow Consortium": 3},
    "скупить краденое": {"Shadow Consortium": 3, "Star Helix Dynamics": -3},

    # ═══ ХАКЕРСТВО ═══
    "взломать корпоративн": {"OPA": 2, "Shadow Consortium": 3, "Earth UN": -2},
    "hack": {"Shadow Consortium": 2, "OPA": 1},
    "взломать полиц": {"Star Helix Dynamics": -5, "OPA": 3},
    "взломать военн": {"Mars Fleet": -5, "Earth UN": -5, "OPA": 3},
    "взломать банк": {"Shadow Consortium": 5, "Star Helix Dynamics": -5, "Earth UN": -3},
    "отключить камер": {"Shadow Consortium": 2, "Star Helix Dynamics": -2},
    "перехватить данные": {"Ghost Merchants": 3, "Shadow Consortium": 2},
    "создать вирус": {"Shadow Consortium": 3, "Star Helix Dynamics": -3, "Earth UN": -2},

    # ═══ СОЦИАЛЬНЫЕ / ДИПЛОМАТИЯ ═══
    "помочь opa": {"OPA": 5, "Earth UN": -3, "Star Helix Dynamics": -2},
    "помочь земле": {"Earth UN": 5, "ESA-Earth": 3, "OPA": -3},
    "помочь марс": {"Mars Republic": 5, "Mars Fleet": 3, "Earth UN": -2},
    "помочь пояс": {"OPA": 3, "Ceres Mining Consortium": 3, "Belt Raiders": 2},
    "помочь беженц": {"OPA": 5, "Earth UN": 2, "Mars Republic": 1},
    "пожертвовать": {"Mystic Order": 3, "OPA": 2},
    "donate": {"Mystic Order": 3, "OPA": 2},
    "предать": {"Shadow Consortium": 2},
    "шантажировать": {"Shadow Consortium": 2, "Earth UN": -2},
    "спасти ребёнк": {"Mystic Order": 3, "OPA": 2, "Star Helix Dynamics": 2},
    "спасти жизн": {"OPA": 2, "Earth UN": 1},
    "лечить бесплатно": {"OPA": 3, "Ceres Mining Consortium": 2},
    "выступить на суд": {"Earth UN": 2, "Star Helix Dynamics": 2},
    "подкупить": {"Shadow Consortium": 1, "Earth UN": -2, "Star Helix Dynamics": -2},
    "договориться мирно": {"Earth UN": 2, "Scientific Assembly": 2},
    "запугать": {"Belt Raiders": 2, "Crimson Talons": 2, "Star Helix Dynamics": -1},
    "обмануть": {"Shadow Consortium": 2, "Ghost Merchants": 1},
    "выдать информацию о": {"Star Helix Dynamics": 3, "Earth UN": 2},
    "доложить полиц": {"Star Helix Dynamics": 5, "Earth UN": 3, "OPA": -3, "Shadow Consortium": -3},
    "сотрудничать с полиц": {"Star Helix Dynamics": 5, "Belt Raiders": -3, "OPA": -3},
    "присоединиться к забастовке": {"OPA": 5, "Ceres Mining Consortium": 3, "Earth UN": -3},
    "подавить забастовк": {"Earth UN": 3, "Star Helix Dynamics": 3, "OPA": -8, "Ceres Mining Consortium": -5},

    # ═══ НАУКА / МЕДИЦИНА ═══
    "провести исследован": {"Scientific Assembly": 3, "Protogen": 1},
    "research": {"Scientific Assembly": 3},
    "опубликовать данные": {"Scientific Assembly": 5, "Ghost Merchants": -2},
    "скрыть данные": {"Protogen": 3, "Shadow Consortium": 2, "Scientific Assembly": -5},
    "создать лекарство": {"Scientific Assembly": 3, "OPA": 2},
    "провести эксперимент": {"Scientific Assembly": 2, "Protogen": 2},
    "нелегальный эксперимент": {"Protogen": 5, "Scientific Assembly": -5, "Earth UN": -3},

    # ═══ ФРАКЦИОННЫЕ ЗАДАНИЯ ═══
    "выполнить задание для opa": {"OPA": 8, "Earth UN": -3},
    "выполнить задание для земли": {"Earth UN": 8, "OPA": -3},
    "выполнить задание для марса": {"Mars Republic": 8, "Mars Fleet": 5},
    "выполнить задание для star helix": {"Star Helix Dynamics": 8, "OPA": -3, "Belt Raiders": -3},
    "работать на protogen": {"Protogen": 10, "Scientific Assembly": -5, "OPA": -5},
}


def calculate_auto_reputation(action: str, current_rep: dict) -> dict:
    """
    Analyze player action text and return reputation changes.
    Handles Russian verb morphology with stem-matching.
    Returns {faction_name: delta, ...} or empty dict.
    """
    action_lower = action.lower()
    changes = {}

    for trigger, rep_changes in ACTION_REPUTATION_MAP.items():
        matched = False
        # For Russian: match stem (first 4+ chars) to catch verb forms
        # "убить пирата" -> also matches "убил пирата", "убиваю пирата"
        words = trigger.split()
        if len(words) >= 2:
            # Use 3-char stem for Russian verbs (covers убить/убил/убиваю etc)
            stem = words[0][:3]
            rest = " ".join(words[1:])
            if stem in action_lower and rest in action_lower:
                matched = True
        # Single-word triggers: use 3-char stem
        if not matched and len(words) == 1:
            stem = trigger[:3]
            if stem in action_lower:
                matched = True
        # Exact substring match as fallback
        if not matched and trigger in action_lower:
            matched = True
        if matched:
            for faction, delta in rep_changes.items():
                changes[faction] = changes.get(faction, 0) + delta

    # Cap individual changes
    for faction in changes:
        changes[faction] = max(-15, min(15, changes[faction]))

    return changes


def apply_reputation_changes(current_rep: dict, changes: dict) -> dict:
    """Apply reputation changes, clamping to -100..100."""
    for faction, delta in changes.items():
        old_val = current_rep.get(faction, 0)
        new_val = max(-100, min(100, old_val + delta))
        current_rep[faction] = new_val
    return current_rep


def get_reputation_summary(changes: dict) -> str:
    """Human-readable summary of rep changes."""
    if not changes:
        return ""
    parts = []
    for faction, delta in sorted(changes.items(), key=lambda x: abs(x[1]), reverse=True):
        arrow = "▲" if delta > 0 else "▼"
        parts.append(f"{faction}: {arrow}{abs(delta)}")
    return "Репутация: " + ", ".join(parts)
