"""Фаза 20b: генерация 72 новых навыков для CHARACTER_SKILLS.json (итого 87).
Категории: социальные, технические, боевые нишевые, науки, ремёсла, выживание.
Формат записи идентичен существующим. Ноль нового кода в движке."""
import json, os
os.chdir(r"D:\NexusRPG-main")

sk = json.load(open("game_data/CHARACTER_SKILLS.json", encoding="utf-8"))
existing = {s["skill_id"] for s in sk["skills"]}

# (skill_id, name, base_attribute, starting_value) — 72 шт.
NEW = [
    # === СОЦИАЛЬНЫЕ (12) ===
    ("deception","Обман","charisma",0),
    ("intimidation","Запугивание","strength",0),
    ("streetwise","Уличная интуиция","charisma",0),
    ("etiquette","Этикет высшего общества","charisma",0),
    ("leadership","Лидерство","willpower",0),
    ("instruction","Обучение других","charisma",0),
    ("interrogation","Допрос","willpower",0),
    ("performance","Выступление","charisma",0),
    ("seduction","Обольщение","charisma",0),
    ("empathy_read","Чтение людей","intelligence",0),
    ("rumor_network","Сеть слухов","charisma",0),
    ("public_speaking","Публичные выступления","charisma",0),
    # === ТЕХНИЧЕСКИЕ / ХАКИНГ (14) ===
    ("electronics_repair","Ремонт электроники","tech_empathy",0),
    ("drones","Дроны и рой","tech_empathy",0),
    ("network_security","Сетевая безопасность","intelligence",0),
    ("crypto_analysis","Криптоанализ","intelligence",0),
    ("ai_interface","Интерфейсы ИИ","tech_empathy",0),
    ("robotics","Робототехника","tech_empathy",0),
    ("demolition","Подрывное дело","intelligence",0),
    ("vehicle_maintenance","Обслуживание транспорта","tech_empathy",0),
    ("ship_systems","Корабельные системы","tech_empathy",0),
    ("weapon_smithing","Оружейное дело","tech_empathy",0),
    ("implant_surgery_calibration","Калибровка имплантов","tech_empathy",0),
    ("sensor_operations","Работа с сенсорами","intelligence",0),
    ("comms_jamming","Радиоперехват и глушение","intelligence",0),
    ("fabrication_3d","3D-фабрикация","tech_empathy",0),
    # === БОЕВЫЕ НИШЕВЫЕ (10) ===
    ("heavy_weapons","Тяжёлое оружие","strength",0),
    ("explosives_ordnance","Взрывчатка и боеприпасы","dexterity",0),
    ("sniping","Снайперская стрельба","reflexes",0),
    ("close_quarters","Ближний бой CQB","strength",0),
    ("thrown_weapons","Метательное оружие","dexterity",0),
    ("turret_gunnery","Турельные установки","reflexes",0),
    ("zero_g_combat","Нуль-G бой","endurance",0),
    ("boarding_tactics","Абордажная тактика","strength",0),
    ("first_aid_combat","Боевая медицина","dexterity",0),
    ("armor_operation","Тяжёлая броня","endurance",0),
    # === НАУКИ (12) ===
    ("physics","Физика","intelligence",0),
    ("chemistry","Химия","intelligence",0),
    ("astrophysics","Астрофизика","intelligence",0),
    ("xenobiology","Ксенобиология","intelligence",0),
    ("genetics","Генетика","intelligence",0),
    ("mathematics","Математика и криптография теории","intelligence",0),
    ("archaeology","Археология (доколонизация)","intelligence",0),
    ("pharmacology","Фармакология","intelligence",0),
    ("protomolecule_theory","Теория Протомолекулы","intelligence",0),
    ("planetology","Планетология","intelligence",0),
    ("quantum_theory","Квантовая теория","intelligence",0),
    ("research_method","Научный метод","intelligence",0),
    # === РЕМЁСЛА / ПРОФЕССИОНАЛЬНЫЕ (12) ===
    ("cooking","Кулинария","tech_empathy",0),
    ("tailoring_gear","Снаряжение и экипировка","dexterity",0),
    ("mining","Горное дело","strength",0),
    ("salvage_ops","Салваж и разборка","strength",0),
    ("agriculture_hydro","Гидропоника","tech_empathy",0),
    ("brewing_chem_synthesis","Химический синтез","intelligence",0),
    ("art_design","Искусство и дизайн","charisma",0),
    ("music_instrument","Музыка","dexterity",0),
    ("writing_journalism","Журналистика и тексты","education" if False else "charisma",0),
    ("accounting_finance","Финансы и учёт","intelligence",0),
    ("logistics_planning","Логистика","intelligence",0),
    ("forgery_docs","Подделка документов","dexterity",0),
    # === ВЫЖИВАНИЕ / ФИЗИЧЕСКИЕ (12) ===
    ("vacuum_ops","Работа в вакууме EVA","endurance",0),
    ("navigation_astrogation","Навигация и астрогация","intelligence",0),
    ("tracking","Следопытство","intelligence",0),
    ("foraging","Поиск еды и воды","endurance",0),
    ("radiation_handling","Радиационная защита","endurance",0),
    ("climbing","Скалолазание","strength",0),
    ("swimming_diving","Плавание и дайвинг","endurance",0),
    ("cold_survival","Холодовое выживание","endurance",0),
    ("heat_survival","Тепловое выживание","endurance",0),
    ("piloting_atmospheric","Пилотирование в атмосфере","reflexes",0),
    ("evasion","Уклонение","reflexes",0),
    ("pain_tolerance","Болевая стойкость","willpower",0),
]

assert len(NEW) == 72, len(NEW)
# Уникальность id
ids = [n[0] for n in NEW]
assert len(set(ids)) == 72, "дубликаты id"
overlap = set(ids) & existing
assert not overlap, f"пересечение с существующими: {overlap}"

def make_record(sid, name, attr, sv):
    return {
        "skill_id": sid,
        "name": name,
        "base_attribute": attr,
        "min": 0, "max": 10,
        "starting_value": sv,
        "xp_to_level": 100,
        "training_methods": [
            {"type":"usage","description":f"Практическое применение: {name.lower()}","xp_gain":0.5},
            {"type":"training","description":f"Тренировка у наставника: {name.lower()}","xp_gain":5},
            {"type":"study","description":f"Самостоятельное изучение: {name.lower()}","xp_gain":3},
        ],
    }

new_records = [make_record(*t) for t in NEW]
sk["skills"].extend(new_records)
sk["version"] = "2.0_87_SKILLS"
sk["description"] = (sk.get("description") or "") + " | Фаза 20b: расширено до 87 навыков."

json.dump(sk, open("game_data/CHARACTER_SKILLS.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)

check = json.load(open("game_data/CHARACTER_SKILLS.json", encoding="utf-8"))
print(f"Итого навыков: {len(check['skills'])} (было 15, добавлено {len(new_records)})")
by_attr = {}
for s in check["skills"]:
    by_attr[s["base_attribute"]] = by_attr.get(s["base_attribute"],0)+1
print("Распределение по атрибутам:", json.dumps(by_attr, ensure_ascii=False))