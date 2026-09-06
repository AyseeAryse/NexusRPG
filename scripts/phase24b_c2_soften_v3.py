# Фаза 24b C2: нарративное смягчение 11 записей Годов становления в v3_legacy.py
# + исправление призрачных навыков/атрибутов. Только текст и моды по одобренной таблице.
import re

PATH = r"D:\NexusRPG-main\src\content\v3_legacy.py"
t = open(PATH, encoding="utf-8").read()
orig = t

REPL = [
    # FY_GANG_LEADER — только текст
    ('"description": "Возглавляли уличную банду в подуровнях мегаполиса. Научились управлять людьми через страх и уважение.",',
     '"description": "Заслужили авторитет в уличной группировке подуровней мегаполиса — старшие слушались, младшие смотрели в рот. Первые уроки управления людьми.",'),

    # FY_CORP_SPY — текст + perception→intelligence + investigation→tracking
    ('"description": "Внедрялись в конкурирующие компании, крали секреты и вербовали инсайдеров. Доверие — ваше оружие.",',
     '"description": "Курьером носили пакеты для людей корпорации — и быстро поняли: кто владеет информацией, тот владеет всеми.",'),
    ('"attr_mods": {"charisma": 1, "perception": 1},',
     '"attr_mods": {"charisma": 1, "intelligence": 1},'),
    ('"skill_mods": {"deception": 2, "investigation": 1, "hacking": 1}',
     '"skill_mods": {"deception": 2, "tracking": 1, "hacking": 1}'),

    # FY_DIPLOMAT_CORPS — текст
    ('"description": "Представляли свою фракцию на межпланетных переговорах. Слова — ваше оружие.",',
     '"description": "Сопровождали наставника на межпланетных переговорах и однажды замолвили слово за свою фракцию — и вас услышали.",'),

    # FY_MECH_PILOT — текст
    ('"description": "Управляли тяжёлым боевым мехом в зонах конфликтов. Машина стала продолжением вашего тела.",',
     '"description": "Освоили тренажёры и учебный мех на базе родственника — к 18 машина слушалась вас лучше собственных ног.",'),

    # FY_SPEC_OPS — текст
    ('"description": "Элитное подразделение для невозможных миссий. Вы — оружие, заточенное до бритвенной остроты.",',
     '"description": "Юношеская программа военной подготовки с репутацией «готовят лучших». Инструкторы отмечали вашу выучку.",'),

    # FY_QUANTUM_LAB — текст
    ('"description": "Работали на переднем крае квантовой физики. Реальность — не то, чем кажется, и вы это доказали.",',
     '"description": "Ассистировали в квантовой лаборатории, поражая исследователей хваткой. Реальность — не то, чем кажется, и вы почувствовали это первым.",'),

    # FY_BLACK_MARKET — текст
    ('"description": "Работали на подпольный рынок — продавали всё, от информации до органов. Грязно, но прибыльно.",',
     '"description": "Помогали в лавке на чёрном рынке — подмечали цены, покупателей и правила грязной торговли. Прибыльно. И опасно.",'),

    # FY_ASSASSIN_SCHOOL — текст + persuasion→negotiation
    ('"description": "Тренировались в секретной школе наёмных убийц. Каждое движение отточено до смертельного совершенства.",',
     '"description": "Тайный наставник обучил искусству бесшумного движения и точного удара. Кем он был на самом деле — вы так и не узнали.",'),
    ('"skill_mods": {"stealth": 2, "combat": 2, "persuasion": -1}',
     '"skill_mods": {"stealth": 2, "combat": 2, "negotiation": -1}'),

    # FY_SHIPYARD_WORKER — текст
    ('"description": "Строили и ремонтировали корабли на орбитальных верфях. Знаете каждый болт и каждый сварочный шов.",',
     '"description": "Подрабатывали подмастерьем на орбитальной верфи — корпуса, стыки, сварные швы. Корабли стали вам как родные.",'),

    # FY_SMUGGLER_ROUTE — текст + perception→reflexes + navigation→streetwise
    ('"description": "Годы перевозки запрещённых грузов через блокпосты и патрули. Знаете каждую лазейку в системе.",',
     '"description": "Бегали мелкими поручениями для контрабандистов через блокпосты — и запомнили каждую лазейку патрульной системы.",'),
    ('"attr_mods": {"perception": 1, "dexterity": 1},',
     '"attr_mods": {"reflexes": 1, "dexterity": 1},'),
    ('"skill_mods": {"piloting": 1, "stealth": 1, "negotiation": 1, "navigation": 1}',
     '"skill_mods": {"piloting": 1, "stealth": 1, "negotiation": 1, "streetwise": 1}'),

    # FY_AI_ARCHITECT — текст + persuasion→empathy_read
    ('"description": "Проектировали искусственные интеллекты для станций и кораблей. Понимаете машинный разум лучше человеческого.",',
     '"description": "Собирали собственного домашнего ИИ из списанных компонентов — и понимаете машинную логику лучше человеческой.",'),
    ('"skill_mods": {"hacking": 2, "technology": 2, "persuasion": -1}',
     '"skill_mods": {"hacking": 2, "technology": 2, "empathy_read": -1}'),

    # FY_XENO_EXPEDITION — текст + perception→intelligence + science→research_method + xenology→protomolecule_theory
    ('"description": "Участвовали в экспедиции по изучению аномалий во внешней системе. Видели то, что не укладывается в науку.",',
     '"description": "Пошли юнцом в экспедицию по изучению аномалий внешней системы. Видели то, что не укладывается в науку — и не забыли это никогда.",'),
    ('"attr_mods": {"willpower": 1, "perception": 1},',
     '"attr_mods": {"willpower": 1, "intelligence": 1},'),
    ('"skill_mods": {"science": 2, "survival": 1, "xenology": 1}',
     '"skill_mods": {"research_method": 2, "survival": 1, "protomolecule_theory": 1}'),
]

applied, failed = 0, []
for old, new in REPL:
    if old in t:
        t = t.replace(old, new, 1)
        applied += 1
    else:
        failed.append(old[:70])

open(PATH, "w", encoding="utf-8").write(t)
print(f"Применено замен: {applied}/{len(REPL)}")
if failed:
    print("НЕ НАЙДЕНЫ:")
    for f in failed:
        print("  ", f)

# Контроль: призраков в целевых записях больше нет
for ghost in ("persuasion", "navigation", "xenology", '"science"', "perception"):
    n = len(re.findall(ghost, t))
    print(f"  '{ghost}' в файле: {n}")
