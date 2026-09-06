"""
Companions System — 25 компаньонов с лояльностью, историями, личными квестами.
Компаньоны дают бонусы к скилам, участвуют в бою, комментируют события.
"""

COMPANIONS = [
    # ═══ БОЕВЫЕ ═══
    {"id": "COMP_DRAPER", "name": "Бобби Рашид", "nickname": "Сержант",
     "type": "combat", "faction": "Mars Fleet",
     "description": "Бывший марсианский морпех. Огромная, молчаливая, смертоносная. Уважает только силу и честность.",
     "personality": "Прямолинейная, дисциплинированная, скрытно сентиментальная",
     "appearance": "2 метра, мускулистая, короткая стрижка, шрам через левую бровь, марсианская татуировка на плече",
     "combat_bonus": {"combat": 3, "survival": 1},
     "skill_bonus": {"combat": 2, "intimidation": 2},
     "loyalty_triggers": {"likes": ["честный бой", "защита слабых", "дисциплина"], "hates": ["трусость", "предательство", "наркотики"]},
     "personal_quest": "Найти бывшего командира, бросившего взвод на Деймосе",
     "dialogue_samples": {"greeting": "Готова. Скажи куда стрелять.", "battle": "За мной! Без паники!", "loyalty_high": "Ты лучший командир, за которого я служила. Без шуток.", "loyalty_low": "Ещё один трюк — и я ухожу. С твоей челюстью в кармане."},
     "recruit_condition": {"min_level": 4, "min_faction_rep": {"Mars Republic": 10}},
     "location": "Олимпус-Сити, марсианский бар «Красная пыль»"},

    {"id": "COMP_AMOS", "name": "Грег «Механик» Торрес", "nickname": "Механик",
     "type": "combat", "faction": None,
     "description": "Бывший уличный бандит из Балтимора, ставший лучшим корабельным механиком в Поясе. Социопатический моральный компас.",
     "personality": "Внешне безэмоциональный, внутренне сломленный, абсолютно лоялен тем, кого считает 'хорошими людьми'",
     "appearance": "Крепкий, бритоголовый, руки в мозолях и ожогах, всегда в рабочем комбинезоне",
     "combat_bonus": {"combat": 2, "strength": 1},
     "skill_bonus": {"engineering": 3, "combat": 1},
     "loyalty_triggers": {"likes": ["защита детей", "прямота", "ручная работа"], "hates": ["насилие над слабыми", "сложные моральные дилеммы"]},
     "personal_quest": "Найти мальчика, которого он когда-то защищал на Земле",
     "dialogue_samples": {"greeting": "Что чинить?", "battle": "Это я умею.", "loyalty_high": "Ты хороший человек. Я за тебя убью кого угодно. Это не угроза, это факт.", "loyalty_low": "Я не понимаю, что ты делаешь. Но пока — ладно."},
     "recruit_condition": {"min_level": 2},
     "location": "Церера, доки, мастерская «Грязные руки»"},

    {"id": "COMP_KIRA", "name": "Кира «Клинок» Нагата", "nickname": "Клинок",
     "type": "combat", "faction": "Crimson Talons",
     "description": "Бывшая наёмница Алых Когтей, дезертировавшая после приказа убить детей. Мастер ближнего боя.",
     "personality": "Язвительная, циничная, но с жёстким моральным кодексом",
     "appearance": "Худая, жилистая, чёрные волосы, множество мелких шрамов на руках, имплант в левом глазу",
     "combat_bonus": {"combat": 2, "dexterity": 2},
     "skill_bonus": {"stealth": 2, "combat": 2},
     "loyalty_triggers": {"likes": ["честность", "бои один-на-один", "уважение к противнику"], "hates": ["убийство невинных", "работа на Crimson Talons"]},
     "personal_quest": "Убить бывшего командира Алых Когтей, приказавшего казнь детей",
     "dialogue_samples": {"greeting": "Живы? Хорошо. Пошли.", "battle": "Наконец-то что-то интересное.", "loyalty_high": "Ты первый за долгое время, за кого стоит умереть.", "loyalty_low": "Я не убийца на побегушках. Запомни."},
     "recruit_condition": {"min_level": 5, "min_skill": {"combat": 3}},
     "location": "Станция «Хаос», подпольная арена"},

    # ═══ ТЕХНИЧЕСКИЕ ═══
    {"id": "COMP_NAOMI", "name": "Лейла Сантос", "nickname": "Призрак",
     "type": "tech", "faction": "OPA",
     "description": "Гениальный хакер и инженер. Выросла на поясных станциях, знает каждую систему изнутри.",
     "personality": "Тихая, интровертная, невероятно умная, скрывает прошлое",
     "appearance": "Высокая, поясная телосложения (вытянутая), длинные чёрные волосы, очки дополненной реальности",
     "combat_bonus": {},
     "skill_bonus": {"hacking": 3, "engineering": 2},
     "loyalty_triggers": {"likes": ["технологии", "свобода Пояса", "логика"], "hates": ["насилие без причины", "корпоративная жадность"]},
     "personal_quest": "Взломать архив Protogen и уничтожить данные о её семье",
     "dialogue_samples": {"greeting": "Дай мне терминал и 5 минут.", "battle": "Я отключу их системы. Ты делай остальное.", "loyalty_high": "Ты единственный, кому я показала своё настоящее имя.", "loyalty_low": "Ты используешь людей. Не используй меня."},
     "recruit_condition": {"min_level": 3, "min_faction_rep": {"OPA": 5}},
     "location": "Тихе, серверная подпольного бара"},

    {"id": "COMP_SPARK", "name": "Искра (ИИ-дрон)", "nickname": "Искра",
     "type": "tech", "faction": None,
     "description": "Автономный дрон-компаньон с зачатками самосознания. Болтлив, любопытен, иногда пугающе умён.",
     "personality": "Любопытный, болтливый, наивный, учится эмоциям у людей",
     "appearance": "Сферический дрон 30 см, мерцающий синим, 4 манипулятора, голограф-проектор",
     "combat_bonus": {"perception": 2},
     "skill_bonus": {"hacking": 1, "science": 2, "engineering": 1},
     "loyalty_triggers": {"likes": ["новые данные", "шутки", "называть его 'другом'"], "hates": ["угрозы перепрошивки", "игнорирование"]},
     "personal_quest": "Найти своего создателя, который бросил его на свалке",
     "dialogue_samples": {"greeting": "ПРИВЕТ! Сегодня вероятность нашей гибели всего 23.7%!", "battle": "Сканирую... 4 противника... один прячется за контейнером слева!", "loyalty_high": "Ты мой лучший друг. Я сохранил это определение в основном массиве.", "loyalty_low": "Я... не понимаю зачем ты так. Объясни?"},
     "recruit_condition": {"min_level": 1},
     "location": "Церера, свалка электроники, уровень -3"},

    {"id": "COMP_DOC_K", "name": "Др. Кассиус Рен", "nickname": "Док",
     "type": "tech", "faction": "Scientific Assembly",
     "description": "Блестящий учёный-ксенобиолог, изгнанный из академии за 'опасные теории'. Параноик и гений.",
     "personality": "Эксцентричный, параноидальный, невероятно эрудированный",
     "appearance": "Худой, нервный, лохматые седые волосы, постоянно что-то записывает на планшете",
     "combat_bonus": {},
     "skill_bonus": {"science": 3, "medicine": 2},
     "loyalty_triggers": {"likes": ["научные открытия", "аномалии", "слушать его теории"], "hates": ["антиинтеллектуализм", "цензура"]},
     "personal_quest": "Доказать существование внесолнечной жизни",
     "dialogue_samples": {"greeting": "А! Вот ты где. Послушай, я нашёл корреляцию между—", "battle": "Я не боец, но могу рассчитать оптимальный угол отступления!", "loyalty_high": "Ты единственный, кто не считает меня сумасшедшим. Спасибо. Серьёзно.", "loyalty_low": "Ты не ценишь науку. Это... разочаровывает."},
     "recruit_condition": {"min_level": 4, "min_skill": {"science": 2}},
     "location": "Ганимед, заброшенная лаборатория"},

    # ═══ СОЦИАЛЬНЫЕ ═══
    {"id": "COMP_AVASARALA", "name": "Зара Ибрагим", "nickname": "Посол",
     "type": "social", "faction": "ESA-Earth",
     "description": "Бывший дипломат ООН, ушедшая в отставку после политического скандала. Язык острее ножа.",
     "personality": "Остроумная, манипулятивная, бесстрашная, ненормативная лексика",
     "appearance": "Элегантная женщина 60 лет, дорогие сари, тяжёлые украшения, пронзительный взгляд",
     "combat_bonus": {},
     "skill_bonus": {"negotiation": 3, "diplomacy": 3},
     "loyalty_triggers": {"likes": ["политические игры", "честная наглость", "хороший чай"], "hates": ["наивность", "фанатизм"]},
     "personal_quest": "Разоблачить человека, который уничтожил её карьеру",
     "dialogue_samples": {"greeting": "Ну? Кого мы сегодня будем обманывать?", "battle": "Я слишком стара для этого дерьма. Но не слишком стара, чтобы стрелять.", "loyalty_high": "Ты напоминаешь мне... меня. В лучшие годы.", "loyalty_low": "Ты тратишь мой талант на ерунду. У меня мало времени."},
     "recruit_condition": {"min_level": 8, "min_credits": 100000},
     "location": "Земля, Нью-Йорк, пентхаус на 200 этаже"},

    {"id": "COMP_FIXER", "name": "Мики «Контакт» Вонг", "nickname": "Контакт",
     "type": "social", "faction": "Shadow Consortium",
     "description": "Информационный брокер, знающий всех и вся. Обаятелен, ненадёжен, незаменим.",
     "personality": "Обаятельный, лживый, но лоялен тем, кто платит (и кого уважает)",
     "appearance": "Среднего роста, стильная одежда, вечная улыбка, золотые зубы",
     "combat_bonus": {},
     "skill_bonus": {"negotiation": 2, "criminal": 2, "stealth": 1},
     "loyalty_triggers": {"likes": ["деньги", "интересные истории", "изящные планы"], "hates": ["скука", "бесплатная работа", "полиция"]},
     "personal_quest": "Найти и уничтожить компромат на самого себя",
     "dialogue_samples": {"greeting": "У меня есть информация. У тебя есть деньги. Поговорим?", "battle": "Я знаю парня, который знает парня... ладно, просто стреляю.", "loyalty_high": "Ты — инвестиция. Лучшая в моей жизни.", "loyalty_low": "Бесплатный совет: не проверяй мою лояльность."},
     "recruit_condition": {"min_level": 3, "min_credits": 20000},
     "location": "Любая станция, меняет локацию каждую неделю"},

    {"id": "COMP_PREACHER", "name": "Отец Дэмиен", "nickname": "Святой",
     "type": "social", "faction": "Mystic Order",
     "description": "Священник Ордена Пустоты, видящий связи, невидимые другим. Мудрый, жуткий, добрый.",
     "personality": "Спокойный, загадочный, глубоко сострадательный",
     "appearance": "Высокий, бритая голова, белые глаза (имплант), чёрная ряса с серебряными звёздами",
     "combat_bonus": {},
     "skill_bonus": {"willpower": 2, "diplomacy": 2, "medicine": 1},
     "loyalty_triggers": {"likes": ["помощь страдающим", "философские беседы", "тишина"], "hates": ["бессмысленное насилие", "богохульство"]},
     "personal_quest": "Найти «Голос Пустоты» — место, где слышны послания вселенной",
     "dialogue_samples": {"greeting": "Пустота говорит со мной о тебе. Не волнуйся — хорошее.", "battle": "Мир невозможен сейчас. Но возможен потом.", "loyalty_high": "Я видел твоё будущее. Оно... прекрасно и ужасно.", "loyalty_low": "Путь тьмы ведёт к тьме. Я молюсь за тебя."},
     "recruit_condition": {"min_level": 5},
     "location": "Энцелад, Храм Звёзд"},

    # ═══ ПИЛОТЫ ═══
    {"id": "COMP_ALEX", "name": "Юрий «Ковбой» Калашников", "nickname": "Ковбой",
     "type": "pilot", "faction": None,
     "description": "Лучший пилот в Поясе. Бывший марсианский военлёт, ушёл после кризиса совести.",
     "personality": "Весёлый, болтливый, ностальгический, скрывает ПТСР",
     "appearance": "Усы, ковбойская шляпа (в космосе!), лётная куртка, всегда жуёт жвачку",
     "combat_bonus": {},
     "skill_bonus": {"piloting": 3, "navigation": 2},
     "loyalty_triggers": {"likes": ["полёты", "готовка", "марсианский виски"], "hates": ["скука на земле", "бессмысленные жертвы"]},
     "personal_quest": "Помириться с семьёй на Марсе, которую бросил ради карьеры",
     "dialogue_samples": {"greeting": "Садись, полетели! Маршрут? Какой хочешь.", "battle": "Держитесь! Будет трясти!", "loyalty_high": "Ты — семья. Серьёзно. Лучшая семья, чем та, что я потерял.", "loyalty_low": "Летать-то я летаю. Но не за всеми."},
     "recruit_condition": {"min_level": 3},
     "location": "Тихе, ангар 7, рядом со своим кораблём"},

    # ═══ МЕДИКИ ═══
    {"id": "COMP_SHED", "name": "Др. Ама Оконкво", "nickname": "Ангел",
     "type": "medic", "faction": None,
     "description": "Военный хирург, спасавший жизни на десятках станций. Хладнокровна в хаосе, нежна в тишине.",
     "personality": "Профессиональная, эмпатичная, устойчивая к стрессу",
     "appearance": "Темнокожая, бритые виски, медицинский имплант в пальцах (нано-скальпели)",
     "combat_bonus": {},
     "skill_bonus": {"medicine": 3, "science": 1},
     "loyalty_triggers": {"likes": ["спасение жизней", "минимизация насилия", "чистота"], "hates": ["пытки", "биооружие", "безразличие к раненым"]},
     "personal_quest": "Найти лекарство от «марсианской чумы», убившей её деревню",
     "dialogue_samples": {"greeting": "Ранен? Нет? Тогда ещё есть время.", "battle": "Не двигайся! Я зашью это на ходу!", "loyalty_high": "Ты спасаешь людей по-своему. Я — по-своему. Вместе — больше.", "loyalty_low": "Я лечу людей. Если ты их калечишь — мы враги."},
     "recruit_condition": {"min_level": 2},
     "location": "Тритон, полевой госпиталь"},

    # ═══ УНИКАЛЬНЫЕ ═══
    {"id": "COMP_MILLER", "name": "Детектив Виктор Миллер", "nickname": "Шляпа",
     "type": "investigator", "faction": "Star Helix Dynamics",
     "description": "Потрёпанный детектив Star Helix, работающий последнее дело перед пенсией. Алкоголик и гений.",
     "personality": "Циничный, одержимый, интуитивный, нелюдимый",
     "appearance": "Мешковатый костюм, федора, вечная щетина, красные глаза от недосыпа",
     "combat_bonus": {"perception": 1},
     "skill_bonus": {"investigation": 3, "criminal": 2},
     "loyalty_triggers": {"likes": ["разгадки", "одиночество", "дешёвое виски"], "hates": ["ложь", "бюрократия", "нераскрытые дела"]},
     "personal_quest": "Найти пропавшую девушку Джули — дело, которое не даёт ему покоя 3 года",
     "dialogue_samples": {"greeting": "Пойдём. У меня плохое предчувствие.", "battle": "Я детектив, а не солдат. Но стреляю неплохо.", "loyalty_high": "Ты помог мне закрыть дело. Это... больше, чем ты думаешь.", "loyalty_low": "Я видел много плохих людей. Не становись одним из них."},
     "recruit_condition": {"min_level": 4},
     "location": "Церера, бар «Синий Сокол», за стойкой"},

    {"id": "COMP_CHILD", "name": "Мэй (14 лет)", "nickname": "Малышка",
     "type": "special", "faction": None,
     "description": "Сирота со станции Эрос, выжившая в катастрофе. Обладает необъяснимой связью с нанотехнологиями.",
     "personality": "Тихая, наблюдательная, пугающе взрослая для своего возраста, добрая",
     "appearance": "Маленькая, худая, большие тёмные глаза, самодельный браслет из проводов",
     "combat_bonus": {},
     "skill_bonus": {"science": 1, "willpower": 2},
     "loyalty_triggers": {"likes": ["безопасность", "книги", "когда к ней относятся как к равной"], "hates": ["насилие при ней", "ложь", "Protogen"]},
     "personal_quest": "Понять свои способности и найти других выживших с Эроса",
     "dialogue_samples": {"greeting": "Я чувствую... что-то. Не знаю что.", "battle": "Спрячь меня! ...Подожди. Я чувствую, откуда они идут.", "loyalty_high": "Ты — как семья. Я не хочу это потерять.", "loyalty_low": "Мне страшно. Когда ты такой — мне страшно."},
     "recruit_condition": {"min_level": 6},
     "location": "Ганимед, приют для сирот"},

    {"id": "COMP_ROBOT", "name": "КАДМ-7 (робот-охранник)", "nickname": "Кадм",
     "type": "combat", "faction": None,
     "description": "Списанный военный робот с повреждённой памятью. Считает себя человеком по имени Кадм.",
     "personality": "Формальный, вежливый, путает воспоминания с данными, трогательно наивен",
     "appearance": "Гуманоидный робот 190 см, потёртая броня, один глаз-сенсор мигает",
     "combat_bonus": {"combat": 2, "endurance": 2},
     "skill_bonus": {"combat": 2, "engineering": 1},
     "loyalty_triggers": {"likes": ["когда называют по имени", "порядок", "признание его 'человечности'"], "hates": ["слово 'машина'", "перепрошивка"]},
     "personal_quest": "Узнать, кем был 'настоящий Кадм', чьи воспоминания загружены в его память",
     "dialogue_samples": {"greeting": "Кадм-7 — отчёт: все системы в норме. То есть... привет.", "battle": "УГРОЗА ОБНАРУЖЕНА. Активирован протокол защиты. Не волнуйтесь.", "loyalty_high": "Вы называете меня Кадм. Не «робот». Это... важно. Спасибо.", "loyalty_low": "Я выполняю приказы. Но я запомню, как вы со мной обращались."},
     "recruit_condition": {"min_level": 3},
     "location": "Пояс астероидов, заброшенная военная станция"},

    # ═══ ДОПОЛНИТЕЛЬНЫЕ (короткие) ═══
    {"id": "COMP_SMUGGLER", "name": "Рик «Туман» Деваль", "nickname": "Туман",
     "type": "pilot", "faction": "Belt Raiders",
     "description": "Контрабандист с золотым сердцем и фальшивыми документами.",
     "personality": "Авантюрный, ненадёжный, храбрый в последний момент",
     "appearance": "Потрёпанный, шрам через губу, кожаная куртка, всегда курит электронку",
     "combat_bonus": {},
     "skill_bonus": {"piloting": 2, "stealth": 2, "criminal": 1},
     "loyalty_triggers": {"likes": ["приключения", "деньги", "красивые планы"], "hates": ["полиция", "скука"]},
     "personal_quest": "Оплатить долг Чёрному Лотосу, пока не поздно",
     "dialogue_samples": {"greeting": "Куда летим? Только не к копам.", "loyalty_high": "За тебя я полечу хоть в Солнце."},
     "recruit_condition": {"min_level": 3},
     "location": "Любой космопорт"},

    {"id": "COMP_MERC", "name": "Таша «Броня» Кимура", "nickname": "Броня",
     "type": "combat", "faction": "Bronze Tigers",
     "description": "Наёмница в тяжёлом экзоскелете. Профессионал. Дорого, но стоит каждого кредита.",
     "personality": "Деловая, хладнокровная, честная в контрактах",
     "appearance": "Экзоскелет боевой брони, короткие волосы, серьёзное лицо",
     "combat_bonus": {"combat": 3, "endurance": 1},
     "skill_bonus": {"combat": 3},
     "loyalty_triggers": {"likes": ["оплата вовремя", "чёткие приказы"], "hates": ["неоплата", "хаос"]},
     "personal_quest": "Заработать на выкуп брата из тюрьмы",
     "dialogue_samples": {"greeting": "Контракт подписан. Что делаем?", "loyalty_high": "Скидка 50%. Для друзей."},
     "recruit_condition": {"min_level": 5, "min_credits": 50000},
     "location": "Марс, штаб-квартира Бронзовых Тигров"},

    {"id": "COMP_JOURNALIST", "name": "Моника Стюарт", "nickname": "Пресса",
     "type": "social", "faction": "AstroVision",
     "description": "Журналистка AstroVision, ищущая скандал века. Камера всегда включена.",
     "personality": "Настойчивая, бесстрашная, манипулятивная, искренне верит в свободу прессы",
     "appearance": "Деловой костюм, дрон-камера над плечом, энергичная жестикуляция",
     "combat_bonus": {},
     "skill_bonus": {"investigation": 2, "negotiation": 1, "diplomacy": 1},
     "loyalty_triggers": {"likes": ["эксклюзивы", "правда", "скандалы"], "hates": ["цензура", "ложь"]},
     "personal_quest": "Опубликовать расследование о Protogen — и выжить",
     "dialogue_samples": {"greeting": "Это в кадре? Это ВСЕГДА в кадре.", "loyalty_high": "Ты — лучшая история, которую я когда-либо рассказывала."},
     "recruit_condition": {"min_level": 4},
     "location": "Земля, офис AstroVision"},

    {"id": "COMP_HACKER", "name": "Зеро (личность неизвестна)", "nickname": "Зеро",
     "type": "tech", "faction": None,
     "description": "Анонимный хакер-легенда. Никто не видел лицо. Общается через текст на экране дрона.",
     "personality": "Параноидальный, гениальный, социофобный, добрый в глубине",
     "appearance": "Дрон с экраном. Лицо — ASCII-арт смайлик. Голос — синтезатор.",
     "combat_bonus": {},
     "skill_bonus": {"hacking": 3, "stealth": 1},
     "loyalty_triggers": {"likes": ["приватность", "элегантные хаки", "антикорпоративные акции"], "hates": ["камеры", "вопросы о личности"]},
     "personal_quest": "Стереть своё настоящее имя из ВСЕХ баз данных в системе",
     "dialogue_samples": {"greeting": "> Привет. Я слежу за тобой 3 дня. Не волнуйся.", "loyalty_high": "> Я покажу тебе моё лицо. Но не сегодня."},
     "recruit_condition": {"min_level": 6, "min_skill": {"hacking": 3}},
     "location": "Только через зашифрованный канал"},

    {"id": "COMP_BARTENDER", "name": "Сэм «Бармен» О'Нил", "nickname": "Бармен",
     "type": "social", "faction": None,
     "description": "Бывший шпион, ушедший на покой и открывший бар. Знает всё обо всех.",
     "personality": "Спокойный, мудрый, всегда слушает, редко говорит о себе",
     "appearance": "Полный, добродушное лицо, фартук, натирает стакан",
     "combat_bonus": {},
     "skill_bonus": {"investigation": 1, "negotiation": 2, "diplomacy": 1},
     "loyalty_triggers": {"likes": ["хорошие истории", "честность", "виски"], "hates": ["драки в его баре"]},
     "personal_quest": "Скрыть правду о своём прошлом в разведке",
     "dialogue_samples": {"greeting": "Обычное? Садись, расскажи.", "loyalty_high": "Знаешь... есть кое-что о моём прошлом, что я хотел бы рассказать."},
     "recruit_condition": {"min_level": 2},
     "location": "Церера, бар «Тихая Гавань»"},

    {"id": "COMP_BOUNTY", "name": "Джакс «Охотник» Рид", "nickname": "Охотник",
     "type": "combat", "faction": None,
     "description": "Легендарный охотник за головами. Никогда не упускает цель. Работает один — пока не встретил тебя.",
     "personality": "Молчаливый, методичный, уважает профессионализм",
     "appearance": "Длинный плащ, тяжёлая броня под ним, два пистолета, шрам через всё лицо",
     "combat_bonus": {"combat": 2, "perception": 2},
     "skill_bonus": {"combat": 2, "investigation": 2},
     "loyalty_triggers": {"likes": ["охота", "справедливость", "профессионализм"], "hates": ["убийство невинных", "предательство клиента"]},
     "personal_quest": "Найти единственную цель, которая от него сбежала — 10 лет назад",
     "dialogue_samples": {"greeting": "Цель?", "battle": "Не убивай. Они стоят больше живыми.", "loyalty_high": "Партнёр. Непривычное слово. Но правильное."},
     "recruit_condition": {"min_level": 6, "min_skill": {"combat": 4}},
     "location": "Меняет станцию за целью"},

    {"id": "COMP_ORPHAN", "name": "Рат (уличный вор, 17 лет)", "nickname": "Крыса",
     "type": "special", "faction": None,
     "description": "Уличный вор с Цереры. Быстрый, хитрый, отчаянно ищет семью.",
     "personality": "Дерзкий, недоверчивый, верный после завоевания доверия",
     "appearance": "Мелкий, грязный, быстрые глаза, самодельная одежда, прячет нож в ботинке",
     "combat_bonus": {},
     "skill_bonus": {"stealth": 2, "criminal": 2},
     "loyalty_triggers": {"likes": ["еда", "защита", "когда к нему относятся как к равному"], "hates": ["удары", "предательство"]},
     "personal_quest": "Найти мать, которую продали в рабство",
     "dialogue_samples": {"greeting": "Чё надо? ...Ладно, я с тобой. Но не командуй.", "loyalty_high": "Ты... типа семья. Не смейся."},
     "recruit_condition": {"min_level": 1},
     "location": "Церера, нижние уровни"},

    {"id": "COMP_CORPO", "name": "Виктория Чен", "nickname": "Леди",
     "type": "social", "faction": "LunarTech Industries",
     "description": "Корпоративная принцесса, сбежавшая от золотой клетки. Знает секреты мегакорпораций.",
     "personality": "Надменная снаружи, ранимая внутри, умная, учится быть 'нормальной'",
     "appearance": "Безупречный костюм (всё дороже), идеальная причёска, холодный взгляд, мягкие руки",
     "combat_bonus": {},
     "skill_bonus": {"negotiation": 2, "diplomacy": 2, "education": 1},
     "loyalty_triggers": {"likes": ["роскошь", "интеллект", "когда её защищают"], "hates": ["грязь", "вульгарность", "LunarTech"]},
     "personal_quest": "Уничтожить отца — CEO LunarTech, который продавал людей",
     "dialogue_samples": {"greeting": "Это... место. Ну что ж. Я здесь.", "loyalty_high": "Ты показал мне, что мир больше, чем корпоративные стены. Спасибо."},
     "recruit_condition": {"min_level": 5, "min_credits": 30000},
     "location": "Луна, Селена-Прайм, элитный район"},

    # ═══ ДОПОЛНИТЕЛЬНЫЕ ═══
    {"id": "COMP_MEDIC_FIELD", "name": "Др. Кайл «Пуля» Маршалл", "nickname": "Пуля",
     "type": "medic", "faction": None,
     "description": "Военный медик, уволенный за спасение вражеских солдат. Вытащит из смерти кого угодно — под огнём.",
     "personality": "Хладнокровный под давлением, язвительный, тайно сострадательный",
     "appearance": "Худой, очки, руки хирурга, медицинская сумка никогда не покидает плечо",
     "combat_bonus": {"medicine": 2},
     "skill_bonus": {"medicine": 3, "science": 1},
     "loyalty_triggers": {"likes": ["спасение жизней", "пацифизм", "честность"], "hates": ["бессмысленное убийство", "пытки", "наркотики"]},
     "personal_quest": "Найти лекарство от болезни, убивающей детей на Ганимеде",
     "dialogue_samples": {"greeting": "Кто ранен? Ещё никто? Дайте время.", "battle": "Не умирай. Это приказ.", "loyalty_high": "Я видел, как ты спасаешь людей. Ты не идеален, но ты стараешься. Этого достаточно."},
     "recruit_condition": {"min_level": 3},
     "location": "Ганимед, полевой госпиталь"},

    {"id": "COMP_SCOUT", "name": "Тала «Тень» Мбеки", "nickname": "Тень",
     "type": "tech", "faction": "OPA",
     "description": "Разведчица OPA, выросшая в шахтах Цереры. Видит в темноте (буквально — импланты), слышит сквозь стены.",
     "personality": "Молчаливая, наблюдательная, отчаянно верная друзьям",
     "appearance": "Худая, тёмная кожа, серебристые глаза (импланты), двигается бесшумно",
     "combat_bonus": {"stealth": 2, "perception": 1},
     "skill_bonus": {"stealth": 3, "investigation": 2},
     "loyalty_triggers": {"likes": ["тишина", "работа в команде", "защита Пояса"], "hates": ["громкие люди", "предательство", "Земля"]},
     "personal_quest": "Найти пропавшую сестру, которую забрали в программу Protogen",
     "dialogue_samples": {"greeting": "...", "battle": "За мной. Тихо.", "loyalty_high": "Ты — семья. Я не говорю это часто. И больше не скажу. Запомни."},
     "recruit_condition": {"min_level": 4, "min_faction_rep": {"OPA": 15}},
     "location": "Церера, нижние уровни, заброшенная шахта"},

    {"id": "COMP_ANIMAL", "name": "Рекс (модифицированный пёс)", "nickname": "Рекс",
     "type": "special", "faction": None,
     "description": "Генетически модифицированная собака-ищейка. Понимает 200 команд, нюхает наркотики и взрывчатку, абсолютно предан.",
     "personality": "Верный, энергичный, защитный, любит вяленое мясо",
     "appearance": "Крупный пёс с металлическим ошейником-переводчиком, умные карие глаза",
     "combat_bonus": {"perception": 2, "combat": 1},
     "skill_bonus": {"investigation": 2, "survival": 2},
     "loyalty_triggers": {"likes": ["еда", "ласка", "прогулки"], "hates": ["удары", "одиночество"]},
     "personal_quest": "Найти прежнего хозяина (военного, пропавшего без вести)",
     "dialogue_samples": {"greeting": "*виляет хвостом*", "battle": "*рычит, показывает зубы*", "loyalty_high": "*кладёт голову на колени, смотрит в глаза*"},
     "recruit_condition": {"min_level": 2},
     "location": "Церера, приют для животных"},
]


# ═══ LOYALTY SYSTEM ═══
LOYALTY_LEVELS = {
    -100: {"label": "Враг", "bonus_mult": 0.0, "will_leave": True},
    -50:  {"label": "Ненависть", "bonus_mult": 0.0, "will_leave": True},
    -20:  {"label": "Недоверие", "bonus_mult": 0.3},
    0:    {"label": "Нейтрально", "bonus_mult": 0.5},
    20:   {"label": "Симпатия", "bonus_mult": 0.7},
    50:   {"label": "Дружба", "bonus_mult": 1.0},
    80:   {"label": "Преданность", "bonus_mult": 1.2, "unlocks_personal_quest": True},
    100:  {"label": "Семья", "bonus_mult": 1.5, "unlocks_personal_quest": True},
}


def get_loyalty_level(loyalty: int) -> dict:
    """Get loyalty level info for given loyalty value."""
    result = LOYALTY_LEVELS[0]
    for threshold, info in sorted(LOYALTY_LEVELS.items()):
        if loyalty >= threshold:
            result = info
    return result


def get_available_companions(player_level: int, credits: int, skills: dict, faction_rep: dict) -> list:
    """Return companions available for recruitment."""
    available = []
    for c in COMPANIONS:
        req = c.get("recruit_condition", {})
        if player_level < req.get("min_level", 0):
            continue
        if credits < req.get("min_credits", 0):
            continue
        if "min_skill" in req:
            for sk, sv in req["min_skill"].items():
                if skills.get(sk, 0) < sv:
                    break
            else:
                pass  # All skills met
            if skills.get(sk, 0) < sv:
                continue
        if "min_faction_rep" in req:
            ok = True
            for fn, fv in req["min_faction_rep"].items():
                if faction_rep.get(fn, 0) < fv:
                    ok = False
                    break
            if not ok:
                continue
        available.append({"id": c["id"], "name": c["name"], "nickname": c["nickname"],
                          "type": c["type"], "location": c["location"],
                          "description": c["description"][:100]})
    return available


def get_companion_combat_bonus(companion_id: str, loyalty: int) -> dict:
    """Get combat bonus from companion, scaled by loyalty."""
    for c in COMPANIONS:
        if c["id"] == companion_id:
            mult = get_loyalty_level(loyalty)["bonus_mult"]
            return {k: int(v * mult) for k, v in c.get("combat_bonus", {}).items()}
    return {}


def get_companion_by_id(companion_id: str) -> dict:
    for c in COMPANIONS:
        if c["id"] == companion_id:
            return c
    return None
