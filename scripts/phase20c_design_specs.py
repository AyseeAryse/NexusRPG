"""Фаза 20c: 53 новых специализации в оба слоя.

Слой A: src/content/creation_data.py — SPEC_* с {id,name,group,description,skill_mods{}}
Слой B: game_data/CHARACTER_SPECIALIZATIONS_V3_MASSIVE.json — effects+equipment+tone_modifiers

Правила:
- skill_mods/effects ТОЛЬКО из 87-пула (реальные skill_id)
- квота: ни один skill_id не более чем в 6 специализациях суммарно (старые+новые)
- разнообразие доменов внутри одного SPEC
"""
import json, os, re
os.chdir(r"D:\NexusRPG-main")

sk = json.load(open("game_data/CHARACTER_SKILLS.json", encoding="utf-8"))
VALID = {s["skill_id"] for s in sk["skills"]}
ATTRS = {"strength","dexterity","intelligence","charisma","endurance","willpower",
         "reflexes","tech_empathy"}

# Существующие 41 SPEC и их реальные skills (для квоты)
sp = json.load(open("game_data/CHARACTER_SPECIALIZATIONS_V3_MASSIVE.json", encoding="utf-8"))
existing_specs = sp["specializations_expansion"]["new_specializations"]
EXISTING_IDS = set(existing_specs.keys())
usage = {}
def count_use(skill):
    usage[skill] = usage.get(skill, 0) + 1

for v in existing_specs.values():
    for e in v.get("effects", {}):
        if e in VALID: count_use(e)

# 53 новых: (spec_id, group, name_ru, description_short, [3 skills], equipment[3], tone{2})
NEW = [
    # ===== ТЕХНИЧЕСКИЕ +7 =====
    ("SPEC_DRONE_OPERATOR","Технические","Оператор дронов",
     "Управление роем боевых и грузовых дронов на расстоянии",
     ["drones","combat","sensor_operations"],
     ["Пульт роя","Запасные батареи","Ремонтный набор"],
     {"precision":6,"detachment":5}),
    ("SPEC_AI_WHISPERER","Технические","Шепчущий ИИ",
     "Договориться с ограниченным ИИ там, где люди бессильны",
     ["ai_interface","hacking","negotiation"],
     ["Квантовый терминал","Нейроинтерфейс","Библиотека промптов"],
     {"curiosity":7,"patience":4}),
    ("SPEC_FABRICATOR","Технические","Фабрикатор",
     "Печатает что угодно из чего угодно — почти",
     ["fabrication_3d","weapon_smithing","accounting_finance"],
     ["Портативная фабрика","Каталог чертежей","Материалы"],
     {"pragmatism":6,"ingenuity":5}),
    ("SPEC_SIGNAL_GHOST","Технические","Призрак эфира",
     "Перехватывает и глушит любую связь в радиусе",
     ["comms_jamming","crypto_analysis","stealth"],
     ["Перехватчик","Антенна-зонт","Глушилка"],
     {"secrecy":7,"focus":4}),
    ("SPEC_ROBOTICS_SURGEON","Технические","Хирург роботов",
     "Чинит то, что чинить нельзя — и улучшает",
     ["robotics","electronics_repair","implant_surgery_calibration"],
     ["Микроманипуляторы","Диагностический модуль","Запчасти"],
     {"meticulousness":7,"calm":5}),
    ("SPEC_SHIP_ENGINEER","Технические","Корабельный инженер",
     "Корабль — его тело: системы, пробеги, перегрузки",
     ["ship_systems","vehicle_maintenance","engineering"],
     ["Инструментальный пояс","Схемы кораблей","Запас деталей"],
     {"reliability":6,"stubbornness":5}),
    ("SPEC_TECH_ARCHAEOLOGIST","Технические","Техноархеолог",
     "Оживляет технологии мёртвых эпох",
     ["archaeology","electronics_repair","history" if "history" in VALID else "education"],
     ["Копалка артефактов","Анализатор сплавов","Каталог эпох"],
     {"wonder":6,"caution":5}),
    # ===== БОЕВЫЕ +6 =====
    ("SPEC_SNIPER_SPECIALIST","Боевые","Снайпер-специалист",
     "Один выстрел — один контракт. Дистанция решает",
     ["sniping","sensor_operations","evasion"],
     ["Снайперская винтовка","Дальномер","Маскировочная сеть"],
     {"patience":8,"cold_blood":6}),
    ("SPEC_CQB_MASTER","Боевые","Мастер CQB",
     "Коридоры, шлюзы, теснота — его территория",
     ["close_quarters","boarding_tactics","first_aid_combat"],
     ["Дробовик","Тактическая броня","Стробоскопы"],
     {"aggression":6,"speed":5}),
    ("SPEC_HEAVY_ORDNANCE","Боевые","Специалист тяжёлых систем",
     "Тяжёлая броня, турели, ракеты — медленно и необратимо",
     ["heavy_weapons","armor_operation","turret_gunnery"],
     ["Экзоскелет","Пусковая установка","Реактивная броня"],
     {"immovability":7,"menace":5}),
    ("SPEC_VOID_MARINE","Боевые","Пустотный морпех",
     "Бой в вакууме и нуль-G без права на ошибку",
     ["zero_g_combat","vacuum_ops","heavy_weapons"],
     ["Вакуумная броня","Магнитные ботинки","Импульсная винтовка"],
     {"discipline":7,"endurance_mind":5}),
    ("SPEC_FIELD_MEDIC_COMBAT","Боевые","Боевой медик",
     "Держит пульс отряда буквально",
     ["first_aid_combat","medicine","evasion"],
     ["Полевая аптечка","Гемостатик","Медсканер"],
     {"loyalty":7,"stress_resist":5}),
    ("SPEC_DEMO_EXPERT","Боевые","Подрывник",
     "Знает, где тонко — разорвёт точно",
     ["explosives_ordnance","demolition","physics"],
     ["Детонаторы","Пластид","Дальнобойный пульт"],
     {"math_mind":6,"nerves":5}),
    # ===== СОЦИАЛЬНЫЕ +6 =====
    ("SPEC_CON_ARTIST","Социальные","Мошенник высшей лиги",
     "Продаёт мечты тем, кто не покупает дешёво",
     ["deception","streetwise","empathy_read"],
     ["Набор личностей","Фальшивые креденциалы","Компакт-зеркало"],
     {"charm":7,"cynicism":6}),
    ("SPEC_BROADCASTER","Социальные","Медийное лицо",
     "Его голос слушается чаще, чем законы",
     ["public_speaking","writing_journalism","rumor_network"],
     ["Портативная студия","Подписной контур","Архив сюжетов"],
     {"fame_hunger":6,"eloquence":6}),
    ("SPEC_LABYRINTH_FIXER","Социальные","Фиксер лабиринтов",
     "Знает, кто кому должен и кто кого боится",
     ["rumor_network","streetwise","law"],
     ["Контактная книга","Шифрованный коммуникатор","Досье"],
     {"networking":7,"opportunism":5}),
    ("SPEC_INTERROGATOR_SOCIAL","Социальные","Дипломат-дознаватель",
     "Вытягивает правду за бокалом вина",
     ["interrogation","empathy_read","etiquette"],
     ["Дипломат-кейс","Регистратор микроэмоций","Хороший вкус"],
     {"insight":7,"control":5}),
    ("SPEC_STAGE_LEGEND","Социальные","Легенда сцены",
     "Выступления как прикрытие операций",
     ["performance","music_instrument","art_design"],
     ["Сценический грим","Инструмент","Фан-клуб"],
     {"expressiveness":7,"vanity":5}),
    ("SPEC_LEADER_COMMAND","Социальные","Прирождённый командир",
     "Люди идут за ним даже в Пояс",
     ["leadership","instruction","logistics_planning"],
     ["Командный интерфейс","Знаки различия","Устав в голове"],
     {"authority":7,"responsibility":6}),
    # ===== ПИЛОТЫ +5 =====
    ("SPEC_ATMO_RACER","Пилоты","Гоночник атмосферы",
     "Штурмовики и гоночные корпуса — стихия",
     ["piloting_atmospheric","piloting","evasion"],
     ["Гоночный шлем","Форсаж-модуль","Трофейный борт"],
     {"adrenaline":7,"reflex_pride":5}),
    ("SPEC_ASTRO_NAVIGATOR","Пилоты","Астронавигатор",
     "Проложит маршрут через мусорную бурю",
     ["navigation_astrogation","astrophysics","sensor_operations"],
     ["Навигационный комплекс","Звёздные карты","Расчётный блок"],
     {"spatial_thinking":7,"perfectionism":4}),
    ("SPEC_SMUGGLING_ACE","Пилоты","Ас контрабандных рейсов",
     "Тайники внутри тайников, маршруты вне карт",
     ["smuggler_knowledge" if False else "criminal","navigation_astrogation","evasion"],
     ["Двойное дно","Сканер патрулей","Кодовые маячки"],
     {"cool_head":7,"greed":4}),
    ("SPEC_RESCUE_PILOT","Пилоты","Спасательный пилот",
     "Летит туда, откуда все улетают",
     ["piloting","vacuum_ops","first_aid_combat"],
     ["Спасательный борт","Медкапсула","Тросовая система"],
     {"altruism":7,"fearlessness":5}),
    ("SPEC_CARAVAN_CAPTAIN","Пилоты","Капитан каравана",
     "Ведёт колонны через мёртвые зоны",
     ["logistics_planning","navigation_astrogation","leadership"],
     ["Флагманский модуль","Караванные протоколы","Охранное крыло"],
     {"command":6,"persistence":5}),
    # ===== МЕДИЦИНСКИЕ +4 =====
    ("SPEC_PHARMA_BROKER","Медицинские","Фармаброкер",
     "Достанет препарат, которого «не существует»",
     ["pharmacology","negotiation","bureaucracy"],
     ["Каталог веществ","Связи в логистике","Скрытый склад"],
     {"profit_sense":6,"ethics_flex":5}),
    ("SPEC_XENO_VET","Медицинские","Ксенобиолог-практик",
     "Лечит то, что не описано в учебниках",
     ["xenobiology","biology","medicine"],
     ["Полевой ксенолаб","Седатики широкого спектра","Образцы"],
     {"openness":6,"bravery":5}),
    ("SPEC_GENETIC_TAILOR","Медицинские","Генетический портной",
     "Подгоняет геном под заказ клиента",
     ["genetics","pharmacology","protomolecule_theory"],
     ["Геном-редактор","Банк образцов","Этический обход"],
     {"ambition":6,"taboo_comfort":5}),
    ("SPEC_TRAUMA_SURGEON_FIELD","Медицинские","Хирург полевых госпиталей",
     "Оперирует при свете аварийных ламп",
     ["medicine","first_aid_combat","pain_tolerance"],
     ["Полевой оперблок","Плазма-заменитель","Стальные нервы"],
     {"steadiness":7,"compassion":4}),
    # ===== РАЗВЕДКА +5 =====
    ("SPEC_CRYPTO_HUNTER","Разведка","Охотник за шифрами",
     "Взламывает не системы — смыслы",
     ["crypto_analysis","mathematics","hacking"],
     ["Криптоблок","Перехваченные архивы","Терпение"],
     {"pattern_eye":7,"obsession":5}),
    ("SPEC_TRACKER_BELT","Разведка","Следопыт Пояса",
     "Читает обломки как газету",
     ["tracking","salvage_ops","survival"],
     ["Спектральный сканер","Гарпун-коуш","Журнал находок"],
     {"tenacity":6,"intuition":5}),
    ("SPEC_DEEP_INTERROGATOR","Разведка","Глубокий дознаватель",
     "Сломает легенду любого агента",
     ["interrogation","psychology_read" if False else "empathy_read","law"],
     ["Протоколы давления","Юридические дыры","Тихая камера"],
     {"ruthlessness":6,"method":5}),
    ("SPEC_SURVEILLANCE_NET","Разведка","Оператор сетей наблюдения",
     "Город смотрит его глазами",
     ["sensor_operations","drones","comms_jamming"],
     ["Сеть камер","Аналитический ИИ","Список слепых зон"],
     {"omniscience_craving":6,"paranoia":5}),
    ("SPEC_INFILTRATION_SCOUT","Разведка","Скаут-инфильтратор",
     "Первый входит, последний выходит, никто не видел",
     ["stealth","evasion","tracking"],
     ["Хамелеон-костюм","Граффити-метки","Тихий шаг"],
     {"ghost_nature":7,"discipline":4}),
    # ===== ВЫЖИВАНИЕ +6 =====
    ("SPEC_EVA_SPECIALIST","Выживание","Специалист EVA",
     "Вакуум — дом, трос — umbilical",
     ["vacuum_ops","zero_g_combat","radiation_handling"],
     ["Скафандр повышенной автономии","Йо-йо трос","Дозиметр"],
     {"void_calm":7,"self_reliance":5}),
    ("SPEC_RAD_SURVIVOR","Выживание","Радиационный сталкер",
     "Ходит там, где счетчик орёт хором",
     ["radiation_handling","medicine","survival"],
     ["Свинцовый плащ","Стабилизаторы","Карта горячих точек"],
     {"fatalism":6,"calculation":5}),
    ("SPEC_ICE_WANDERER","Выживание","Скиталец льдов",
     "Европа/Энцелад: холод — просто погода",
     ["cold_survival","survival","climbing"],
     ["Термокостюм","Ледовые якоря","Метановая горелка"],
     {"stoicism":6,"wanderlust":5}),
    ("SPEC_DUST_RUNNER","Выживание","Бегущий по пыли",
     "Марсианские бури — расписание, не катастрофа",
     ["heat_survival","survival","navigation_astrogation"],
     ["Пыленепробиваемый плащ","Резерв воды","Компас бури"],
     {"hardened":6,"route_memory":5}),
    ("SPEC_FORAGE_MASTER","Выживание","Мастер подножного корма",
     "Накормит отряд на мёртвой планете",
     ["foraging","chemistry","biology"],
     ["Анализатор биомассы","Семенной банк","Рецепты выживания"],
     {"resourcefulness":6,"gastronomy_love":4}),
    ("SPEC_PRESSURE_DIVER","Выживание","Дайвер глубоких давлений",
     "Европейский океан подо льдом — его офис",
     ["swimming_diving","cold_survival","vacuum_ops"],
     ["Глубоководный костюм","Сонарь","Аварийный пузырь"],
     {"depth_calm":6,"pressure_love":4}),
    # ===== УНИКАЛЬНЫЕ +8 =====
    ("SPEC_PROTO_THEORIST","Уникальные","Теоретик Протомолекулы",
     "Понимает её лучше, чем она понимает нас",
     ["protomolecule_theory","quantum_theory","research_method"],
     ["Закрытые архивы","Изолиния-лаб","Красная папка"],
     {"obsession_depth":8,"isolation":5}),
    ("SPEC_QUANTUM_RITUALIST","Уникальные","Квантовый ритуалист",
     "Наука на грани мистики — или наоборот",
     ["quantum_theory","technology","philosophy" if "philosophy" in VALID else "education"],
     ["Когерентный коллайдер","Ритуальные схемы","Успокоительное"],
     {"mystic_mind":7,"rigor":4}),
    ("SPEC_CULT_STRATEGIST","Уникальные","Стратег культов",
     "Вера как инструмент, паства как сеть",
     ["public_speaking","rumor_network","deception"],
     ["Священные тексты","Сеть проповедников","Казна культа"],
     {"charismatic_dark":8,"manipulation":6}),
    ("SPEC_ANOMALY_HUNTER","Уникальные","Охотник за аномалиями",
     "Ищет то, что меняет физику вокруг себя",
     ["sensor_operations","quantum_theory","vacuum_ops"],
     ["Аномалия-детектор","Изоляционные контейнеры","Журнал совпадений"],
     {"curiosity_fatal":7,"luck":5}),
    ("SPEC_MEMORY_LIBRARIAN","Уникальные","Библиотекарь памяти",
     "Хранит чужие воспоминания как книги",
     ["ai_interface","empathy_read","education"],
     ["Мнемо-архив","Кристаллы записи","Каталог личностей"],
     {"archival_mind":7,"burden":5}),
    ("SPEC_SOLAR_PROPHET","Уникальные","Солнечный пророк",
     "Предсказывает вспышки — и политические бури",
     ["astrophysics","public_speaking","rumor_network"],
     ["Обсерватория-маячок","Гелиосейсмограф","Паства"],
     {"vision":7,"showmanship":5}),
    ("SPEC_GATE_SCOUT","Уникальные","Скаут врат",
     "Видит двери там, где другие видят стену",
     ["navigation_astrogation","quantum_theory","evasion"],
     ["Фазовый компас","Маркерные буи","Легенда о возвращении"],
     {"frontier_spirit":7,"restlessness":5}),
    ("SPEC_SYMBIONT_ENGINEER","Уникальные","Инженер симбионтов",
     "Строит машины, которые хотят жить",
     ["robotics","genetics","ai_interface"],
     ["Био-силиконовый каркас","Нейро-скелет","Контракт symbiosis"],
     {"bio_dream":7,"ethics_gray":5}),
    # ===== КРИМИНАЛ +6 =====
    ("SPEC_FORGERY_MASTER","Криминал","Мастер подделок",
     "Документы, подписи, происхождения — всё нарисует",
     ["forgery_docs","bureaucracy","deception"],
     ["Набор фальсификатора","Бланки всех миров","Печати"],
     {"artisan_crime":7,"detail_obsession":5}),
    ("SPEC_BLACK_MARKET_BARON","Криминал","Барон чёрного рынка",
     "Если это запрещено — он это продаёт",
     ["streetwise","negotiation","logistics_planning"],
     ["Склад-призрак","Сеть наводчиков","Взяточный фонд"],
     {"empire_vision":7,"merciless":5}),
    ("SPEC_SALVAGE_PIRATE","Криминал","Салваж-пират",
     "Чужие крушения — его доходная статья",
     ["salvage_ops","mining","criminal"],
     ["Резак корпусов","Тральщик","Фальшивый SOS"],
     {"scavenger_code":6,"boldness":5}),
    ("SPEC_DATA_FENCER","Криминал","Скупщик данных",
     "Купит компромат, продаст дважды",
     ["crypto_analysis","rumor_network","accounting_finance"],
     ["Холодный кошелёк","Аукционный лист","Проверка подлинности"],
     {"valuation_eye":7,"trust_none":6}),
    ("SPEC_SMUGGLER_ROUTE_SMITH","Криминал","Кузнец контрабандных путей",
     "Проектирует маршруты, которых нет на картах",
     ["navigation_astrogation","comms_jamming","bureaucracy"],
     ["Тайниковый чертёж","Взятые патрули","Тихий транспондер"],
     {"route_genius":7,"quiet_greed":5}),
    ("SPEC_ENFORGER_CONTRACT","Криминал","Исполнитель контрактов",
     "Долг вернётся. С процентами. Он вернёт.",
     ["intimidation","close_quarters","law"],
     ["Контрактный планшет","Внушительный калибр","Список должников"],
     {"fear_brand":7,"code_honor":4}),
]

assert len(NEW) == 53, len(NEW)

# --- Валидация ---
seen_ids = set()
errors = []
skill_total = dict(usage)  # квота с учётом существующих
for sid_, grp, name, desc, skills, equip, tone in NEW:
    if sid_ in EXISTING_IDS or sid_ in seen_ids:
        errors.append(f"дубль id: {sid_}")
    seen_ids.add(sid_)
    for s in skills:
        if s not in VALID:
            errors.append(f"{sid_}: призрачный навык {s}")
        skill_total[s] = skill_total.get(s,0)+1

over_quota = {k:v for k,v in skill_total.items() if v > 6 and k in VALID}
if errors:
    print("ОШИБКИ:"); [print(" -", e) for e in errors]; raise SystemExit(1)
print(f"53 SPEC спроектированы | призрачных навыков: 0 | id уникальны")
print(f"Квота >6 после добавления: {over_quota or 'нет ✅'}")

json.dump({"new_specs":[
    {"spec_id":s_,"group":g,"name":nm,"description":d,"skills":skl,
     "equipment":eq,"tone":tn} for s_,g,nm,d,skl,eq,tn in NEW]},
    open("_audit/phase20c_new_specs.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("проект сохранён: _audit/phase20c_new_specs.json")