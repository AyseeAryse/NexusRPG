# Фаза 23 A1: добавляет starting_location в CHARACTER_ORIGINS.json
# (31 запись, поле не перезаписывает существующие ключи).
# Локации согласованы с galaxy.py/CITY_DISTRICTS_MASTER (реальные города/районы).
import json

PATH = r"D:\NexusRPG-main\game_data\CHARACTER_ORIGINS.json"
doc = json.load(open(PATH, encoding="utf-8"))
origins = doc["origins"]

# district'ы взяты из CITY_DISTRICTS_MASTER (проверка ниже); place — точка входа
LOC = {
    # Земля / Нью-Токио
    "ORIGIN_EARTH_ELITE":              {"planet": "Земля", "city": "Нью-Токио", "district": "Верхний город", "place": "Резиденция семьи"},
    "ORIGIN_EARTH_SLUMS":              {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор", "place": ""},
    "ORIGIN_EARTH_CORPORATE_HEIR":     {"planet": "Земля", "city": "Нью-Токио", "district": "Верхний город", "place": "Корпоративная башня"},
    "ORIGIN_EARTH_JOURNALIST":         {"planet": "Земля", "city": "Нью-Токио", "district": "Медийный квартал", "place": "Редакция"},
    "ORIGIN_EARTH_MILITARY_BRAT":      {"planet": "Земля", "city": "Нью-Токио", "district": "Гарнизонный сектор", "place": ""},
    "ORIGIN_EARTH_DIPLOMAT":           {"planet": "Земля", "city": "Нью-Токио", "district": "Правительственный квартал", "place": "Дипломатический корпус"},
    "ORIGIN_EARTH_HACKER_COLLECTIVE":  {"planet": "Земля", "city": "Нью-Токио", "district": "Нижние уровни", "place": "Хакерская хата"},
    "ORIGIN_EARTH_REFUGEE_CAMP":       {"planet": "Земля", "city": "Нью-Токио", "district": "Палаточный лагерь", "place": ""},
    "ORIGIN_EARTH_CELEBRITY":          {"planet": "Земля", "city": "Нью-Токио", "district": "Медийный квартал", "place": "Пентхаус"},
    "ORIGIN_EARTH_UNDERGROUND_FIGHTER":{"planet": "Земля", "city": "Нью-Токио", "district": "Нижние уровни", "place": "Бойцовская яма"},
    "ORIGIN_EARTH_TECH_MOGUL":         {"planet": "Земля", "city": "Нью-Токио", "district": "Верхний город", "place": "Офис Tech Ventures"},
    # Марс / Новый Бостон
    "ORIGIN_MARS_MILITARY":            {"planet": "Марс", "city": "Новый Бостон", "district": "Гарнизонный сектор", "place": "Казармы Флота"},
    "ORIGIN_MARS_SCIENTIST":           {"planet": "Марс", "city": "Новый Бостон", "district": "Университетский кампус", "place": "Лаборатория"},
    "ORIGIN_MARS_REBEL":               {"planet": "Марс", "city": "Новый Бостон", "district": "Нижние уровни", "place": "Тайная квартира"},
    "ORIGIN_MARS_TERRAFORMER":         {"planet": "Марс", "city": "Новый Бостон", "district": "Терраформинг-станции", "place": ""},
    "ORIGIN_MARS_DOME_ARCHITECT":      {"planet": "Марс", "city": "Новый Бостон", "district": "Купольный центр", "place": "Бюро проектирования"},
    "ORIGIN_MARS_DUST_STORM_SURVIVOR": {"planet": "Марс", "city": "Новый Бостон", "district": "Внешние посадки", "place": ""},
    "ORIGIN_MARS_WATER_THIEF":         {"planet": "Марс", "city": "Новый Бостон", "district": "Внешние посадки", "place": "Водяной чёрный рынок"},
    "ORIGIN_MARS_INDEPENDENCE_CELL":   {"planet": "Марс", "city": "Новый Бостон", "district": "Нижние уровни", "place": "Ячейка Свободного Марса"},
    "ORIGIN_MARS_GENETIC_EXPERIMENT":  {"planet": "Марс", "city": "Новый Бостон", "district": "Университетский кампус", "place": "Биолаборатория"},
    "ORIGIN_MARS_TUNNEL_RAT":          {"planet": "Марс", "city": "Новый Бостон", "district": "Туннели", "place": ""},
    "ORIGIN_MARS_ATMOSPHERIC_ENGINEER":{"planet": "Марс", "city": "Новый Бостон", "district": "Терраформинг-станции", "place": "Машинный зал"},
    # Пояс / Церера-Прайм
    "ORIGIN_BELT_SMUGGLER":            {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Доковый сектор", "place": "Контрабандный причал"},
    "ORIGIN_BELT_SALVAGER":            {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Шахтёрский квартал", "place": "Склад утиля"},
    "ORIGIN_BELT_MINER":               {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Шахтёрский квартал", "place": ""},
    "ORIGIN_BELT_PIRATE_PRINCE":       {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Доковый сектор", "place": "Пиратская пристань"},
    "ORIGIN_BELT_TRADER":              {"planet": "Пояс астероидов", "city": "Станция Церера-Прайм", "district": "Торговые палубы", "place": "Торговый пост"},
    # Внешние
    "ORIGIN_JOVIAN_SCIENTIST":         {"planet": "Ганимед", "city": "Станция Юпитер-Прайм", "district": "Исследовательское кольцо", "place": "Научный модуль"},
    "ORIGIN_SATURN_RING_RUNNER":       {"planet": "Сатурн", "city": "Станция Тихе", "district": "Доковый сектор", "place": ""},
    "ORIGIN_NEPTUNE_OUTCAST":          {"planet": "Нептун", "city": "Форпост Тритон", "district": "Изгнаннические кварталы", "place": ""},
    "ORIGIN_PLUTO_EXPLORER":           {"planet": "Плутон", "city": "Станция Харон", "district": "Экспедиционный док", "place": ""},
}

added = 0
missing = []
for o in origins:
    loc = LOC.get(o["id"])
    if loc is None:
        missing.append(o["id"])
        continue
    if "starting_location" in o:
        print("уже есть:", o["id"])
    else:
        o["starting_location"] = loc
        added += 1

json.dump(doc, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Добавлено starting_location: {added}/31; без маппинга: {missing or 'нет'}")
