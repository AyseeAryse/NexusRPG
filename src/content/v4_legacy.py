"""
Content Expansion V4 — JSON Lifepath Integration + Tiered Events.
Loads origins/formative_years/specializations from JSON design docs.
Adds 8-tier world event system with 150+ events.
"""
import json
import os
import random

GAME_DATA = os.path.join(os.path.dirname(__file__), "game_data")


# ════════════════════════════════════════════════════════════
#  JSON → CODE CONVERTER: origins, formative_years, specs
# ════════════════════════════════════════════════════════════

def _load_json(filename):
    path = os.path.join(GAME_DATA, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _convert_origin(oid, odata):
    """Convert JSON origin format → code format."""
    rarity_map = {"common": "обычное", "uncommon": "необычное",
                  "rare": "редкое", "epic": "эпическое", "legendary": "легендарное"}
    # Determine group from context_tags or id
    group = "Особые"
    tags = odata.get("context_tags", [])
    if any("Earth" in t for t in tags):
        group = "Земля"
    elif any("Mars" in t for t in tags):
        group = "Марс"
    elif any("Belt" in t for t in tags) or any("Asteroid" in t for t in tags):
        group = "Пояс астероидов"
    elif any("Outer" in t for t in tags) or any("Saturn" in t for t in tags) or any("Jupiter" in t for t in tags):
        group = "Внешние колонии"
    elif "MARS" in oid:
        group = "Марс"
    elif "EARTH" in oid:
        group = "Земля"
    elif "BELT" in oid:
        group = "Пояс астероидов"
    elif "OUTER" in oid or "TITAN" in oid or "EUROPA" in oid:
        group = "Внешние колонии"

    return {
        "id": oid,
        "name": odata.get("title", odata.get("name", oid)),
        "rarity": rarity_map.get(odata.get("rarity", "common"), odata.get("rarity", "обычное")),
        "group": group,
        "description": odata.get("description", ""),
        "attr_mods": odata.get("attributes", {}),
        "skill_mods": odata.get("skills", {}),
        "credits": odata.get("starting_values", {}).get("credits", 10000),
        "influence": odata.get("starting_values", {}).get("influence", 0),
    }


def _convert_formative_year(fid, fdata):
    """Convert JSON formative year → code format."""
    effects = fdata.get("effects", {})
    attr_mods = {}
    skill_mods = {}
    for k, v in effects.items():
        if k in ("strength", "dexterity", "endurance", "intelligence",
                  "charisma", "willpower", "perception", "tech_empathy"):
            attr_mods[k] = v
        elif k != "credits":
            skill_mods[k.replace("_skill", "")] = v

    group = "Жизненные события"
    event = fdata.get("event", fdata.get("title", fdata.get("name", fid)))

    return {
        "id": fid,
        "name": event,
        "group": group,
        "description": fdata.get("description", ""),
        "attr_mods": attr_mods,
        "skill_mods": skill_mods,
    }


def _convert_specialization(sid, sdata):
    """Convert JSON specialization → code format."""
    effects = sdata.get("effects", {})
    equip_raw = sdata.get("starting_equipment", [])
    equipment = [e if isinstance(e, str) else str(e) for e in equip_raw]

    group = "Особые"
    tags = sdata.get("context_tags", [])
    if any(t in ("Combat", "Violence", "Military") for t in tags):
        group = "Боевые"
    elif any(t in ("Stealth", "Criminal", "Hacking") for t in tags):
        group = "Теневые"
    elif any(t in ("Corporate", "Social", "Diplomacy") for t in tags):
        group = "Социальные"
    elif any(t in ("Science", "Technology", "Medical") for t in tags):
        group = "Научные"
    elif any(t in ("Space", "Piloting", "Navigation") for t in tags):
        group = "Космические"

    return {
        "id": sid,
        "name": sdata.get("title", sdata.get("name", sid)),
        "group": group,
        "description": sdata.get("description", ""),
        "skill_mods": effects,
        "equipment": equipment,
    }


def load_json_origins():
    """Load all origins from JSON files and convert to code format."""
    results = []

    # From CHARACTER_LIFEPATH_V3_MASSIVE_PART1
    lp = _load_json("CHARACTER_LIFEPATH_V3_MASSIVE_PART1.json")
    new_origins = lp.get("origins_massive_expansion", {}).get("new_origins", {})
    if isinstance(new_origins, dict):
        for oid, odata in new_origins.items():
            if isinstance(odata, dict):
                results.append(_convert_origin(oid, odata))

    # From CHARACTER_ORIGINS.json (those not already in creation_data)
    co = _load_json("CHARACTER_ORIGINS.json")
    origins_list = co.get("origins", [])
    if isinstance(origins_list, list):
        for o in origins_list:
            if isinstance(o, dict) and "id" in o:
                # These already use similar format but with title/attributes
                results.append(_convert_origin(o["id"], o))
    elif isinstance(origins_list, dict):
        for oid, odata in origins_list.items():
            if isinstance(odata, dict):
                results.append(_convert_origin(oid, odata))

    return results


def load_json_formative_years():
    """Load formative years from JSON."""
    results = []
    lp = _load_json("CHARACTER_LIFEPATH_V3_MASSIVE_PART1.json")
    new_fy = lp.get("formative_years_expansion", {}).get("new_formative_years", {})
    if isinstance(new_fy, dict):
        for fid, fdata in new_fy.items():
            if isinstance(fdata, dict):
                results.append(_convert_formative_year(fid, fdata))
    return results


def load_json_specializations():
    """Load specializations from JSON."""
    results = []
    sp = _load_json("CHARACTER_SPECIALIZATIONS_V3_MASSIVE.json")
    new_specs = sp.get("specializations_expansion", {}).get("new_specializations", {})
    if isinstance(new_specs, dict):
        for sid, sdata in new_specs.items():
            if isinstance(sdata, dict):
                results.append(_convert_specialization(sid, sdata))
    return results


# ════════════════════════════════════════════════════════════
#  MEGA MERGE: all origins/fy/specs from code + JSON
# ════════════════════════════════════════════════════════════

def get_all_origins_v4():
    """V3 code origins + JSON origins, deduped."""
    from src.content.v3_legacy import get_all_origins
    merged = {o["id"]: o for o in get_all_origins()}
    for o in load_json_origins():
        if o["id"] not in merged:
            merged[o["id"]] = o
    return list(merged.values())


def get_all_formative_years_v4():
    """V3 code + JSON formative years."""
    from src.content.v3_legacy import get_all_formative_years
    merged = {f["id"]: f for f in get_all_formative_years()}
    for f in load_json_formative_years():
        if f["id"] not in merged:
            merged[f["id"]] = f
    return list(merged.values())


def get_all_specializations_v4():
    """V3 code + JSON specializations."""
    from src.content.v3_legacy import get_all_specializations
    merged = {s["id"]: s for s in get_all_specializations()}
    for s in load_json_specializations():
        if s["id"] not in merged:
            merged[s["id"]] = s
    return list(merged.values())


# ════════════════════════════════════════════════════════════
#  TIERED EVENT SYSTEM v2 — на основе игрового времени + триггеры
# ════════════════════════════════════════════════════════════
#
#  Кулдаун по ИГРОВОМУ ВРЕМЕНИ (не по ходам):
#  Tier 1: ГАЛАКТИЧЕСКИЙ — раз в 5-10 ЛЕТ, нужны экстремальные условия
#  Tier 2: СИСТЕМНЫЙ — раз в 1-3 ГОДА
#  Tier 3: ПЛАНЕТАРНЫЙ — раз в 3-6 МЕСЯЦЕВ
#  Tier 4: РЕГИОНАЛЬНЫЙ — раз в 1-3 МЕСЯЦА
#  Tier 5: ЛОКАЛЬНЫЙ — раз в 1-4 НЕДЕЛИ
#  Tier 6: КВАРТАЛЬНЫЙ — раз в 2-7 ДНЕЙ
#  Tier 7: ПЕРСОНАЛЬНЫЙ — раз в 1-3 НЕДЕЛИ (привязан к действиям)
#  Tier 8: МЕЛОЧИ — раз в 1-3 ДНЯ (фон, не спам)
#
#  КАЖДОЕ событие имеет triggers — набор условий, ВСЕ должны быть выполнены.
#  Если triggers пуст — событие доступно всегда (для tier 8).
#  Шанс (chance) — вероятность срабатывания ЕСЛИ условия выполнены.


def _game_time_to_hours(gt: dict) -> int:
    """Convert game_time dict to total hours since epoch."""
    y = gt.get("year", 2387) - 2387
    m = gt.get("month", 1) - 1
    d = gt.get("day", 1) - 1
    h = gt.get("hour", 0)
    return y * 8760 + m * 720 + d * 24 + h

TIER_COOLDOWNS = {
    # tier: (min_hours, max_hours) — игровые часы между событиями этого тира
    1: (43800, 87600),   # 5-10 лет
    2: (8760, 26280),    # 1-3 года
    3: (2160, 4320),     # 3-6 месяцев
    4: (720, 2160),      # 1-3 месяца
    5: (168, 672),       # 1-4 недели
    6: (48, 168),        # 2-7 дней
    7: (168, 504),       # 1-3 недели
    8: (24, 72),         # 1-3 дня
}

TIERED_EVENTS = {
    # ═══ TIER 1: ГАЛАКТИЧЕСКИЙ ═══
    1: {
        "name": "Галактический",
        "events": [
            {"id": "T1_SIGNAL", "name": "Сигнал из-за пределов системы",
             "text": "Обсерватории фиксируют организованный сигнал из-за пределов Солнечной системы. Все фракции замерли.",
             "effects": {"global_tension": 30, "science_focus": True},
             "quest_hook": "investigation", "duration_days": 180,
             "chance": 0.15,
             "triggers": {"min_level": 15, "min_credits": 5000000, "min_any_faction_rep": 60}},
            {"id": "T1_WORMHOLE", "name": "Пространственная аномалия",
             "text": "В районе орбиты Юпитера открылась стабильная пространственная аномалия. Корабли, пролетающие рядом, теряют связь.",
             "effects": {"trade_disruption": 40, "military_alert": True},
             "quest_hook": "exploration", "duration_days": 365,
             "chance": 0.10,
             "triggers": {"min_level": 18, "min_skill": {"science": 6}}},
            {"id": "T1_AI_AWAKENING", "name": "Пробуждение ИИ",
             "text": "Центральный ИИ станции {loc} вышел за пределы программирования. Он требует признания прав и угрожает отключить системы жизнеобеспечения.",
             "effects": {"global_panic": 20, "tech_disruption": True},
             "quest_hook": "diplomacy", "duration_days": 90,
             "chance": 0.12,
             "triggers": {"min_level": 12, "min_skill": {"hacking": 5}, "min_credits": 1000000}},
            {"id": "T1_TOTAL_WAR", "name": "Тотальная война Земля-Марс",
             "text": "Земля и Марс официально объявили войну. Пояс оказался между двух огней. Нейтралитет больше невозможен.",
             "effects": {"all_factions_war": True, "economy_crash": 50},
             "quest_hook": "military", "duration_days": 730,
             "chance": 0.08,
             "triggers": {"min_level": 20, "min_credits": 10000000, "min_faction_rep": {"Earth UN": -30}, "or_faction_rep": {"Mars Republic": -30}}},
            {"id": "T1_PLAGUE", "name": "Пандемия «Чёрная Звезда»",
             "text": "Неизвестный патоген распространяется по станциям — карантины вводятся повсеместно. Торговля парализована.",
             "effects": {"trade_halt": 80, "panic": 40, "medical_demand": True},
             "quest_hook": "medical", "duration_days": 200,
             "chance": 0.10,
             "triggers": {"min_level": 10, "min_skill": {"medicine": 4}}},
            {"id": "T1_SOLAR_STORM", "name": "Суперштурм",
             "text": "Солнечная активность достигла рекордного уровня. Массивная вспышка движется к внутренним планетам — часы до катастрофы.",
             "effects": {"communications_down": True, "evacuation": True},
             "quest_hook": "survival", "duration_days": 30,
             "chance": 0.20,
             "triggers": {"min_level": 8}},
        ]
    },
    # ═══ TIER 2: СИСТЕМНЫЙ ═══
    2: {
        "name": "Системный",
        "events": [
            {"id": "T2_BLOCKADE", "name": "Блокада торгового маршрута",
             "text": "{f1} блокирует торговый маршрут между {loc} и внешними станциями. Цены на товары взлетают.",
             "effects": {"trade_prices": 40, "smuggling_demand": True},
             "quest_hook": "smuggling", "duration_days": 60,
             "chance": 0.25,
             "triggers": {"min_level": 8, "min_credits": 100000}},
            {"id": "T2_FLEET_BATTLE", "name": "Космическое сражение",
             "text": "Флоты {f1} и {f2} столкнулись у {loc}. Обломки засоряют орбиту, гражданские суда в опасности.",
             "effects": {"navigation_hazard": True, "faction_war": True},
             "quest_hook": "military", "duration_days": 45,
             "chance": 0.20,
             "triggers": {"min_level": 10, "min_skill": {"combat": 4}}},
            {"id": "T2_COUP", "name": "Государственный переворот",
             "text": "Военные {f1} захватили власть на {loc}. Прежнее правительство в бегах, население в шоке.",
             "effects": {"political_chaos": True, "martial_law": True},
             "quest_hook": "political", "duration_days": 90,
             "chance": 0.15,
             "triggers": {"min_level": 12, "min_any_faction_rep": 40}},
            {"id": "T2_MEGA_HEIST", "name": "Ограбление века",
             "text": "Неизвестные украли {goods} на миллиарды кредитов из хранилища {f1}. Вся система ищет воров.",
             "effects": {"security_alert": True, "bounty_surge": True},
             "quest_hook": "investigation", "duration_days": 30,
             "chance": 0.30,
             "triggers": {"min_level": 8, "min_skill": {"stealth": 3}}},
            {"id": "T2_ARMS_RACE", "name": "Гонка вооружений",
             "text": "{f1} представили новое оружие. {f2} в панике наращивают арсенал. Напряжённость растёт.",
             "effects": {"weapons_prices": -20, "tension": 25},
             "quest_hook": "espionage", "duration_days": 120,
             "chance": 0.20,
             "triggers": {"min_level": 10, "min_credits": 500000}},
            {"id": "T2_ENERGY_CRISIS", "name": "Энергетический кризис",
             "text": "Главный реактор {loc} выходит из строя. Миллионы людей без энергии, температура падает.",
             "effects": {"energy_prices": 60, "survival_mode": True},
             "quest_hook": "engineering", "duration_days": 20,
             "chance": 0.25,
             "triggers": {"min_level": 6, "min_skill": {"engineering": 3}}},
            {"id": "T2_DISCOVERY", "name": "Артефакт древней цивилизации",
             "text": "Шахтёры на {loc} обнаружили структуры явно не природного происхождения. Учёные в экстазе, военные — в тревоге.",
             "effects": {"science_rush": True, "military_presence": True},
             "quest_hook": "exploration", "duration_days": 180,
             "chance": 0.12,
             "triggers": {"min_level": 12, "min_skill": {"science": 5}}},
            {"id": "T2_REFUGEE_WAVE", "name": "Волна беженцев",
             "text": "Тысячи беженцев из {loc} ищут убежище после катастрофы. Станции переполнены, ресурсов не хватает.",
             "effects": {"population_surge": True, "resource_drain": 30},
             "quest_hook": "humanitarian", "duration_days": 90,
             "chance": 0.30,
             "triggers": {"min_level": 5}},
        ]
    },
    # ═══ TIER 3: ПЛАНЕТАРНЫЙ ═══
    3: {
        "name": "Планетарный",
        "events": [
            {"id": "T3_ELECTION", "name": "Планетарные выборы",
             "text": "На {loc} начинается предвыборная гонка. Фракции тратят миллионы на пропаганду и подкуп.",
             "effects": {"political_activity": True, "bribery_opportunities": True},
             "quest_hook": "political", "duration_days": 30,
             "chance": 0.40,
             "triggers": {"min_level": 5, "min_credits": 50000}},
            {"id": "T3_PIRATE_FLEET", "name": "Пиратский флот",
             "text": "Объединённый пиратский флот замечен у {loc}. Торговцы в панике, военные на перехват.",
             "effects": {"piracy_surge": True, "escort_demand": True},
             "quest_hook": "combat", "duration_days": 20,
             "chance": 0.35,
             "triggers": {"min_level": 6, "min_skill": {"combat": 3}}},
            {"id": "T3_STRIKE", "name": "Генеральная забастовка",
             "text": "Шахтёры и рабочие {loc} объявили забастовку. Производство остановлено, {f1} теряет миллионы.",
             "effects": {"production_halt": True, "labor_unrest": True},
             "quest_hook": "diplomacy", "duration_days": 15,
             "chance": 0.35,
             "triggers": {"min_level": 4}},
            {"id": "T3_CULT_RISE", "name": "Подъём культа",
             "text": "Религиозный культ «Дети Пустоты» набирает силу на {loc}. Массовые обращения, семьи разрушены.",
             "effects": {"social_unrest": True, "cult_presence": True},
             "quest_hook": "investigation", "duration_days": 60,
             "chance": 0.25,
             "triggers": {"min_level": 5, "min_skill": {"investigation": 2}}},
            {"id": "T3_TECH_EXPO", "name": "Технологическая выставка",
             "text": "{f1} проводит крупнейшую техно-выставку на {loc}. Шпионы, торговцы и воры со всей системы.",
             "effects": {"tech_trade": True, "espionage_risk": True},
             "quest_hook": "trade", "duration_days": 7,
             "chance": 0.50,
             "triggers": {"min_level": 3, "min_credits": 20000}},
            {"id": "T3_PRISON_RIOT", "name": "Бунт в тюрьме",
             "text": "Заключённые тюрьмы-астероида у {loc} захватили контроль. 200 заложников, требования — свобода.",
             "effects": {"security_crisis": True, "hostages": True},
             "quest_hook": "rescue", "duration_days": 5,
             "chance": 0.30,
             "triggers": {"min_level": 7, "min_skill": {"combat": 3}}},
            {"id": "T3_CONTAMINATION", "name": "Химическое заражение",
             "text": "Утечка токсинов на {loc} — целый район эвакуирован. Кто-то должен найти источник.",
             "effects": {"health_hazard": True, "area_lockdown": True},
             "quest_hook": "investigation", "duration_days": 10,
             "chance": 0.30,
             "triggers": {"min_level": 4, "min_skill": {"science": 2}}},
            {"id": "T3_RACING", "name": "Межпланетная гонка",
             "text": "Знаменитая гонка «Кольцо Сатурна» стартует у {loc}. Призовой фонд — 500,000 кредитов.",
             "effects": {"tourism": True, "gambling_surge": True},
             "quest_hook": "racing", "duration_days": 3,
             "chance": 0.45,
             "triggers": {"min_level": 5, "min_skill": {"piloting": 3}, "min_credits": 10000}},
            {"id": "T3_TERRAFORMING", "name": "Прорыв в терраформинге",
             "text": "Проект терраформинга на {loc} достиг новой фазы — впервые можно дышать снаружи 10 минут.",
             "effects": {"hope": 20, "land_prices": 30},
             "quest_hook": "science", "duration_days": 90,
             "chance": 0.20,
             "triggers": {"min_level": 8, "min_skill": {"science": 4}}},
            {"id": "T3_EARTHQUAKE", "name": "Тектоническая активность",
             "text": "Серия землетрясений на {loc} разрушила купола нижних уровней. Спасательная операция в разгаре.",
             "effects": {"infrastructure_damage": 30, "rescue_demand": True},
             "quest_hook": "rescue", "duration_days": 14,
             "chance": 0.35,
             "triggers": {"min_level": 3}},
        ]
    },
    # ═══ TIER 4: РЕГИОНАЛЬНЫЙ ═══
    4: {
        "name": "Региональный",
        "events": [
            {"id": "T4_GANG_WAR", "name": "Война банд",
             "text": "Две банды делят территорию в секторе {loc}. Перестрелки каждую ночь, жители прячутся.",
             "effects": {"crime": 30, "danger": True},
             "quest_hook": "combat", "duration_days": 14,
             "chance": 0.40,
             "triggers": {"min_level": 3, "min_skill": {"combat": 2}}},
            {"id": "T4_BLACK_MARKET_RAID", "name": "Облава на чёрный рынок",
             "text": "Star Helix проводит облаву на чёрный рынок {loc}. Торговцы разбегаются, товар конфискуют.",
             "effects": {"black_market_disrupted": True, "prices_spike": True},
             "quest_hook": "stealth", "duration_days": 5,
             "chance": 0.35,
             "triggers": {"min_level": 4, "min_skill": {"stealth": 2}}},
            {"id": "T4_VIP_VISIT", "name": "Визит VIP",
             "text": "Высокопоставленный чиновник {f1} прибывает в {loc}. Усиленная охрана, но и усиленные возможности.",
             "effects": {"security_increase": True, "opportunity": True},
             "quest_hook": "social", "duration_days": 3,
             "chance": 0.45,
             "triggers": {"min_level": 5, "min_any_faction_rep": 20}},
            {"id": "T4_POWER_OUTAGE", "name": "Отключение энергии",
             "text": "Энергосеть сектора {loc} выведена из строя. В темноте мародёры чувствуют себя вольготно.",
             "effects": {"darkness": True, "looting": True},
             "quest_hook": "survival", "duration_days": 2,
             "chance": 0.40,
             "triggers": {"min_level": 2}},
            {"id": "T4_BOUNTY_HUNTER", "name": "Охотник за головами в городе",
             "text": "Известный охотник за головами ищет цель на {loc}. Местные нервничают — кого именно он ищет?",
             "effects": {"tension": 10},
             "quest_hook": "bounty", "duration_days": 7,
             "chance": 0.35,
             "triggers": {"min_level": 5, "min_skill": {"combat": 3}}},
            {"id": "T4_PROTEST", "name": "Массовый протест",
             "text": "Жители {loc} вышли на протест против {f1}. Баррикады, лозунги, и полиция на подходе.",
             "effects": {"unrest": True, "faction_rep_change": True},
             "quest_hook": "political", "duration_days": 5,
             "chance": 0.35,
             "triggers": {"min_level": 3}},
            {"id": "T4_ARENA_TOURNAMENT", "name": "Подпольный турнир",
             "text": "Подпольная арена {loc} объявляет турнир. Призовой фонд 50,000 кредитов. Правил нет.",
             "effects": {"combat_opportunity": True, "gambling": True},
             "quest_hook": "gladiator", "duration_days": 3,
             "chance": 0.50,
             "triggers": {"min_level": 4, "min_skill": {"combat": 3}, "min_credits": 5000}},
            {"id": "T4_HACKER_ATTACK", "name": "Хакерская атака",
             "text": "Хакеры взломали системы безопасности {loc}. Двери заблокированы, камеры ослеплены.",
             "effects": {"security_down": True, "hacking_opportunity": True},
             "quest_hook": "hacking", "duration_days": 1,
             "chance": 0.35,
             "triggers": {"min_level": 4, "min_skill": {"hacking": 3}}},
            {"id": "T4_FACTORY_EXPLOSION", "name": "Взрыв на фабрике",
             "text": "Фабрика {f1} на {loc} взорвалась. Десятки жертв, район затянут токсичным дымом.",
             "effects": {"casualties": True, "investigation_needed": True},
             "quest_hook": "investigation", "duration_days": 7,
             "chance": 0.30,
             "triggers": {"min_level": 3}},
            {"id": "T4_MEDICAL_OUTBREAK", "name": "Вспышка болезни",
             "text": "Неизвестная болезнь поражает жителей сектора {loc}. Клиники переполнены, нужна помощь.",
             "effects": {"health_crisis": True, "medical_demand": True},
             "quest_hook": "medical", "duration_days": 10,
             "chance": 0.30,
             "triggers": {"min_level": 3, "min_skill": {"medicine": 2}}},
            {"id": "T4_SMUGGLE_BUST", "name": "Перехват контрабанды",
             "text": "Партия {goods} перехвачена на {loc}. Контрабандисты ищут новые маршруты и надёжных курьеров.",
             "effects": {"smuggling_opportunity": True},
             "quest_hook": "smuggling", "duration_days": 10,
             "chance": 0.40,
             "triggers": {"min_level": 3, "min_skill": {"stealth": 2}}},
            {"id": "T4_NEW_SHOP", "name": "Открытие элитного магазина",
             "text": "Новый магазин {f1} открылся на {loc}. Эксклюзивные товары по завышенным ценам.",
             "effects": {"rare_items": True},
             "quest_hook": "trade", "duration_days": 30,
             "chance": 0.50,
             "triggers": {"min_credits": 30000}},
        ]
    },
    # ═══ TIER 5: ЛОКАЛЬНЫЙ ═══
    5: {
        "name": "Локальный",
        "events": [
            {"id": "T5_MERCHANT_ARRIVE", "name": "Прибытие торговца",
             "text": "Редкий торговец причалил к станции — у него товары, которых не найти в обычных магазинах.",
             "effects": {"rare_trade": True}, "quest_hook": "trade", "duration_days": 5,
             "chance": 0.50, "triggers": {"min_credits": 5000}},
            {"id": "T5_MUGGING", "name": "Ограбление на улице",
             "text": "Крики в переулке — кого-то грабят. Вмешаться или пройти мимо?",
             "effects": {"crime_event": True}, "quest_hook": "rescue", "duration_days": 1,
             "chance": 0.40, "triggers": {"min_level": 2, "min_skill": {"combat": 1}}},
            {"id": "T5_JOB_BOARD", "name": "Новые задания на доске",
             "text": "Доска объявлений обновилась: несколько срочных заказов с хорошей оплатой.",
             "effects": {"new_quests": True}, "quest_hook": "jobs", "duration_days": 7,
             "chance": 0.60, "triggers": {}},
            {"id": "T5_IMPLANT_SALE", "name": "Распродажа имплантов",
             "text": "Клиника проводит акцию: -20% на установку имплантов. Очередь растёт.",
             "effects": {"implant_discount": 20}, "quest_hook": None, "duration_days": 5,
             "chance": 0.40, "triggers": {"min_credits": 10000}},
            {"id": "T5_SUSPICIOUS_PERSON", "name": "Подозрительная личность",
             "text": "Незнакомец в плаще следит за вами из-за угла. Когда вы поворачиваетесь, он исчезает.",
             "effects": {"mystery": True}, "quest_hook": "investigation", "duration_days": 3,
             "chance": 0.30, "triggers": {"min_level": 3}},
            {"id": "T5_NEON_FESTIVAL", "name": "Неоновый фестиваль",
             "text": "Станция празднует ежегодный Неоновый фестиваль. Музыка, огни, толпы — и карманники.",
             "effects": {"morale": 10, "pickpocket_risk": True}, "quest_hook": None, "duration_days": 3,
             "chance": 0.35, "triggers": {}},
            {"id": "T5_DELIVERY_REQUEST", "name": "Срочная доставка",
             "text": "Нервный человек предлагает 5000 кредитов за доставку пакета. Не спрашивать что внутри.",
             "effects": {"quick_money": True}, "quest_hook": "delivery", "duration_days": 2,
             "chance": 0.45, "triggers": {"min_level": 2}},
            {"id": "T5_DUEL_CHALLENGE", "name": "Вызов на дуэль",
             "text": "Местный задира вызывает вас на дуэль. Отказ — потеря репутации. Согласие — риск.",
             "effects": {"reputation_test": True}, "quest_hook": "combat", "duration_days": 1,
             "chance": 0.30, "triggers": {"min_level": 4, "min_skill": {"combat": 3}}},
            {"id": "T5_DATA_CHIP", "name": "Найденный чип данных",
             "text": "На полу в коридоре лежит чип данных. Кто-то обронил — или подбросил специально.",
             "effects": {"loot": True, "mystery": True}, "quest_hook": "investigation", "duration_days": 2,
             "chance": 0.30, "triggers": {"min_level": 2, "min_skill": {"hacking": 1}}},
            {"id": "T5_BAR_FIGHT", "name": "Драка в баре",
             "text": "В местном баре вспыхнула массовая драка. Мебель летает, бутылки бьются.",
             "effects": {"danger": 5}, "quest_hook": None, "duration_days": 1,
             "chance": 0.50, "triggers": {}},
            {"id": "T5_REPAIR_REQUEST", "name": "Просьба о ремонте",
             "text": "Старик просит помочь починить сломанный генератор в его отсеке. Платит мало, но благодарен.",
             "effects": {"karma": True}, "quest_hook": "engineering", "duration_days": 1,
             "chance": 0.40, "triggers": {"min_skill": {"engineering": 2}}},
            {"id": "T5_STREET_PREACHER", "name": "Уличный проповедник",
             "text": "Фанатик на площади кричит о конце света. Некоторые слушают, другие смеются.",
             "effects": {"atmosphere": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.50, "triggers": {}},
        ]
    },
    # ═══ TIER 6: КВАРТАЛЬНЫЙ ═══
    6: {
        "name": "Квартальный",
        "events": [
            {"id": "T6_GRAFFITI", "name": "Новое граффити",
             "text": "На стене появилось граффити: символ OPA и слова «Пояс не забудет». Краска ещё свежая.",
             "effects": {"faction_presence": True}, "quest_hook": None, "duration_days": 3,
             "chance": 0.50, "triggers": {}},
            {"id": "T6_VENDOR", "name": "Бродячий торговец",
             "text": "Торговец с тележкой предлагает дешёвую еду и сомнительные стимуляторы.",
             "effects": {"trade_option": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.50, "triggers": {}},
            {"id": "T6_PATROL", "name": "Усиленный патруль",
             "text": "Охранники проверяют документы всех проходящих. Что-то случилось — или кого-то ищут.",
             "effects": {"security_check": True}, "quest_hook": None, "duration_days": 2,
             "chance": 0.40, "triggers": {}},
            {"id": "T6_KID_LOST", "name": "Потерянный ребёнок",
             "text": "Маленький ребёнок плачет в углу. Потерялся — или брошен?",
             "effects": {"moral_choice": True}, "quest_hook": "rescue", "duration_days": 1,
             "chance": 0.35, "triggers": {}},
            {"id": "T6_CARD_GAME", "name": "Карточная игра",
             "text": "Группа в углу играет в карты на кредиты. Приглашают присоединиться.",
             "effects": {"gambling_option": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.45, "triggers": {"min_credits": 500}},
            {"id": "T6_RUMOR", "name": "Интересный слух",
             "text": "В очереди за кофе слышите шёпот: «...склад на уровне 7... без охраны до утра...»",
             "effects": {"intel": True}, "quest_hook": "heist", "duration_days": 2,
             "chance": 0.30, "triggers": {"min_skill": {"stealth": 1}}},
            {"id": "T6_OLD_FRIEND", "name": "Случайная встреча",
             "text": "Знакомое лицо в толпе — человек из прошлого. Обрадуется ли он вас видеть?",
             "effects": {"social_event": True}, "quest_hook": "social", "duration_days": 1,
             "chance": 0.35, "triggers": {"min_level": 2}},
            {"id": "T6_NOISE", "name": "Странные звуки",
             "text": "Из вентиляционной шахты доносятся странные скрежещущие звуки. Может, крысы. Может, нет.",
             "effects": {"atmosphere": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.50, "triggers": {}},
            {"id": "T6_LEAK", "name": "Утечка в коридоре",
             "text": "Из потолка капает мутная жидкость. Охлаждающая жидкость или что похуже?",
             "effects": {"hazard_minor": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.40, "triggers": {}},
            {"id": "T6_DARK_CORRIDOR", "name": "Темный коридор",
             "text": "Фонари в коридоре мигают и гаснут. В темноте мерцает что-то красное.",
             "effects": {"atmosphere": True, "minor_danger": True}, "quest_hook": None, "duration_days": 1,
             "chance": 0.40, "triggers": {}},
        ]
    },
    # ═══ TIER 7: ПЕРСОНАЛЬНЫЙ ═══
    7: {
        "name": "Персональный",
        "events": [
            {"id": "T7_MESSAGE", "name": "Анонимное сообщение",
             "text": "На ваш коммлинк приходит зашифрованное сообщение: «Я знаю, кто вы. Встретимся.»",
             "effects": {"personal_hook": True}, "quest_hook": "mystery", "duration_days": 7,
             "chance": 0.25, "triggers": {"min_level": 5, "min_any_faction_rep": 20}},
            {"id": "T7_BOUNTY_ON_YOU", "name": "Награда за вашу голову",
             "text": "На доске разыскиваемых появилось ваше лицо. Кто-то назначил награду.",
             "effects": {"hunted": True, "danger": 20}, "quest_hook": "survival", "duration_days": 30,
             "chance": 0.20, "triggers": {"min_level": 6, "min_any_faction_rep_negative": -30}},
            {"id": "T7_OLD_DEBT", "name": "Старый долг",
             "text": "Кредитор напоминает о долге. У вас 5 дней, или он «пришлёт мальчиков».",
             "effects": {"debt_pressure": True}, "quest_hook": "payment", "duration_days": 5,
             "chance": 0.30, "triggers": {"max_credits": 5000}},
            {"id": "T7_PROMOTION", "name": "Предложение работы",
             "text": "{f1} предлагает вам постоянную работу. Хорошая зарплата, но обязательства.",
             "effects": {"career_choice": True}, "quest_hook": "career", "duration_days": 10,
             "chance": 0.25, "triggers": {"min_level": 8, "min_any_faction_rep": 40}},
            {"id": "T7_INHERITANCE", "name": "Неожиданное наследство",
             "text": "Нотариус сообщает: дальний родственник оставил вам наследство. Но есть условия...",
             "effects": {"credits_potential": True, "obligation": True},
             "quest_hook": "personal", "duration_days": 14,
             "chance": 0.15, "triggers": {"min_level": 5}},
            {"id": "T7_IMPLANT_GLITCH", "name": "Сбой импланта",
             "text": "Ваш имплант начинает глючить — странные визуальные артефакты и голоса. Нужен техник.",
             "effects": {"health_issue": True, "perception_penalty": True},
             "quest_hook": "medical", "duration_days": 5,
             "chance": 0.25, "triggers": {"min_level": 3, "has_implants": True}},
            {"id": "T7_RIVAL", "name": "Появление соперника",
             "text": "Кто-то берёт те же контракты, что и вы, и делает это быстрее. Конкуренция или вражда?",
             "effects": {"competition": True}, "quest_hook": "rivalry", "duration_days": 30,
             "chance": 0.20, "triggers": {"min_level": 6, "min_credits": 50000}},
            {"id": "T7_NIGHTMARE", "name": "Странные сны",
             "text": "Вам снится один и тот же сон — координаты, которых вы не знаете, и голос: «Найди меня.»",
             "effects": {"mystery": True, "stress": 5}, "quest_hook": "mystery", "duration_days": 20,
             "chance": 0.15, "triggers": {"min_level": 7, "min_skill": {"willpower": 3}}},
            {"id": "T7_LOVE_INTEREST", "name": "Романтический интерес",
             "text": "Кто-то проявляет к вам интерес — и это не похоже на обычное знакомство.",
             "effects": {"social_bond": True}, "quest_hook": "social", "duration_days": 14,
             "chance": 0.20, "triggers": {"min_level": 3, "min_skill": {"charisma": 3}}},
            {"id": "T7_BILLIONAIRE_POWER", "name": "Власть денег",
             "text": "С вашим состоянием можно купить армию. Наёмники, корпорации и политики ждут ваших приказов.",
             "effects": {"power_play": True, "war_option": True}, "quest_hook": "conquest",
             "duration_days": 60, "chance": 0.30,
             "triggers": {"min_credits": 1000000000, "min_level": 15}},
        ]
    },
    # ═══ TIER 8: МЕЛОЧИ / АТМОСФЕРА ═══
    8: {
        "name": "Мелочи",
        "events": [
            {"id": "T8_RAIN", "name": "Конденсат", "text": "Капли конденсата падают с потолка — система климата барахлит.",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.70, "triggers": {}},
            {"id": "T8_MUSIC", "name": "Музыка", "text": "Из бара доносится старая земная мелодия. Кто-то подпевает.",
             "effects": {"morale": 2}, "quest_hook": None, "duration_days": 1, "chance": 0.70, "triggers": {}},
            {"id": "T8_CAT", "name": "Станционный кот", "text": "Рыжий кот трётся о ваши ноги. На станции говорят, он приносит удачу.",
             "effects": {"morale": 3}, "quest_hook": None, "duration_days": 1, "chance": 0.50, "triggers": {}},
            {"id": "T8_NEON", "name": "Неоновая вывеска", "text": "Вывеска «УДАЧА» мигает, половина букв не горит. Теперь читается «УДА».",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_SMELL", "name": "Запах готовки", "text": "Запах настоящей жареной еды — редкость на станции. У кого-то хороший день.",
             "effects": {"morale": 1}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_NEWSFLASH", "name": "Экстренные новости", "text": "Экран на стене мигает: «СРОЧНО: {f1} объявляет о...» — экран гаснет.",
             "effects": {"curiosity": True}, "quest_hook": None, "duration_days": 1, "chance": 0.50, "triggers": {}},
            {"id": "T8_STARS", "name": "Вид из окна", "text": "Через иллюминатор видны звёзды. Секунда покоя в хаотичной жизни.",
             "effects": {"morale": 3, "stress_relief": True}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_DRONE", "name": "Пролетевший дрон", "text": "Грузовой дрон чуть не задел вашу голову. Нужно смотреть вверх.",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_POSTER", "name": "Рекламный плакат", "text": "Плакат: «ПРОТОГЕН — заботимся о вашем будущем». Кто-то приписал маркером: «...уничтожая настоящее».",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.50, "triggers": {}},
            {"id": "T8_CHILD_GAME", "name": "Играющие дети", "text": "Дети гоняются друг за другом в коридоре, смеясь. Обычная жизнь продолжается.",
             "effects": {"morale": 2}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_COFFEE", "name": "Кофе", "text": "Автомат с кофе выдал вам двойную порцию вместо одинарной. Сегодня хороший день.",
             "effects": {"morale": 1}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_ARGUMENT", "name": "Ссора", "text": "Двое кричат друг на друга из-за парковочного места для дронов.",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_COUGH", "name": "Кашель в толпе", "text": "Человек рядом закашлялся. На станции шепчутся о новом вирусе.",
             "effects": {"unease": True}, "quest_hook": None, "duration_days": 1, "chance": 0.40, "triggers": {}},
            {"id": "T8_FLICKER", "name": "Мерцание", "text": "Свет в коридоре мигнул. Один раз. Два. Потом всё нормально. Наверное.",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
            {"id": "T8_SHIP_ARRIVAL", "name": "Прибытие корабля", "text": "Транспорт пристыковался к станции. Пассажиры выходят — усталые лица, тяжёлые сумки.",
             "effects": {}, "quest_hook": None, "duration_days": 1, "chance": 0.60, "triggers": {}},
        ]
    },
}


# ════════════════════════════════════════════════════════════
#  TRIGGER CHECKER — проверяет все условия события
# ════════════════════════════════════════════════════════════

def check_triggers(triggers: dict, player: dict) -> bool:
    """
    Проверяет ВСЕ условия триггера. Все должны быть выполнены.
    player = {level, credits, skills: {}, faction_rep: {}, inventory: [], ...}
    """
    if not triggers:
        return True

    level = player.get("level", 1)
    credits = player.get("credits", 0)
    skills = player.get("skills", {})
    attrs = player.get("attributes", {})
    faction_rep = player.get("faction_rep", {})

    # min_level
    if "min_level" in triggers and level < triggers["min_level"]:
        return False

    # min_credits / max_credits
    if "min_credits" in triggers and credits < triggers["min_credits"]:
        return False
    if "max_credits" in triggers and credits > triggers["max_credits"]:
        return False

    # min_skill: {"combat": 3, "hacking": 5} — ALL must be met
    if "min_skill" in triggers:
        for skill_name, min_val in triggers["min_skill"].items():
            actual = skills.get(skill_name, attrs.get(skill_name, 0))
            if actual < min_val:
                return False

    # min_any_faction_rep: at least one faction >= value
    if "min_any_faction_rep" in triggers:
        threshold = triggers["min_any_faction_rep"]
        if not any(v >= threshold for v in faction_rep.values()):
            return False

    # min_any_faction_rep_negative: at least one faction <= value (for enemies)
    if "min_any_faction_rep_negative" in triggers:
        threshold = triggers["min_any_faction_rep_negative"]
        if not any(v <= threshold for v in faction_rep.values()):
            return False

    # min_faction_rep: {"Earth UN": 30} — specific faction check
    if "min_faction_rep" in triggers:
        for fname, min_val in triggers["min_faction_rep"].items():
            if faction_rep.get(fname, 0) < min_val:
                return False

    # has_implants
    if "has_implants" in triggers and triggers["has_implants"]:
        inventory = player.get("inventory", [])
        has = any("имплант" in str(i).lower() or "implant" in str(i).lower()
                   for i in inventory)
        if not has:
            return False

    return True


def get_total_tiered_events():
    """Count all tiered events."""
    return sum(len(d["events"]) for d in TIERED_EVENTS.values())


class TieredEventManager:
    """
    Manages tiered events based on game time and trigger conditions.
    Tracks cooldowns per tier to prevent spam.
    """

    def __init__(self):
        self.last_event_hours: dict = {}  # Lazily initialized on first call
        self._initialized = False
        self.recent_events: list = []
        self.max_recent = 30

    def _lazy_init(self, current_hours: int):
        """Initialize cooldowns relative to actual game start time."""
        if self._initialized:
            return
        for t in range(1, 9):
            cd = TIER_COOLDOWNS.get(t, (24, 72))
            # Set "last fired" to current time minus random partial cooldown
            # So each tier needs to wait a partial cooldown before first fire
            wait = random.randint(cd[0] // 3, cd[0])
            self.last_event_hours[t] = current_hours - (cd[0] - wait)
        self._initialized = True

    def try_generate_event(self, game_time: dict, player: dict) -> dict | None:
        """
        Try to generate ONE tiered event based on game time and player state.
        Returns event dict or None if nothing fires.
        """
        current_hours = _game_time_to_hours(game_time)
        self._lazy_init(current_hours)

        # Try tiers from 8 (most frequent) to 1 (rarest)
        # But shuffle within to add variety
        tier_order = list(range(8, 0, -1))

        for tier in tier_order:
            cooldown = TIER_COOLDOWNS.get(tier, (24, 72))
            last = self.last_event_hours.get(tier, 0)
            min_cd, max_cd = cooldown

            # Check if enough game time has passed
            elapsed = current_hours - last
            # Use random threshold within the cooldown range
            threshold = random.randint(min_cd, max_cd)

            if elapsed < threshold:
                continue  # Cooldown not ready

            # Get eligible events for this tier
            tier_data = TIERED_EVENTS.get(tier)
            if not tier_data:
                continue

            eligible = []
            for event in tier_data["events"]:
                # Skip recently fired
                if event["id"] in self.recent_events:
                    continue
                # Check triggers
                if not check_triggers(event.get("triggers", {}), player):
                    continue
                # Check chance
                if random.random() > event.get("chance", 0.5):
                    continue
                eligible.append(event)

            if not eligible:
                continue

            # Pick one
            chosen = random.choice(eligible)

            # Record
            self.last_event_hours[tier] = current_hours
            self.recent_events.append(chosen["id"])
            if len(self.recent_events) > self.max_recent:
                self.recent_events = self.recent_events[-self.max_recent:]

            return {
                **chosen,
                "tier": tier,
                "tier_name": tier_data["name"],
                "fired_at": dict(game_time),
            }

        return None  # Nothing fired this tick
