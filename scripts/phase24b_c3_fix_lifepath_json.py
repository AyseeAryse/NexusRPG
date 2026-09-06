# Фаза 24b C3: чинит 17 записей formative_years_expansion в CHARACTER_LIFEPATH.json
# (призрачные *_skill → реальные id 86-пула, служебные поля → flavor/heat),
# добавляет flavor в description для снятых модов.
import json

PATH = r"D:\NexusRPG-main\game_data\CHARACTER_LIFEPATH.json"
doc = json.load(open(PATH, encoding="utf-8"))
nfy = doc["formative_years_expansion"]["new_formative_years"]

# Одобренные эффекты: attr_mods остаются как были (реальные), *_skill → реальные id,
# heat остаётся отдельным полем heat_mods (дешёвая привязка), остальное — flavor в description.
FIX = {
    "FY_LOVE_TRIANGLE": {"effects": {"charisma": 2, "willpower": 1, "empathy_read": 1}},
    "FY_FAMILY_BANKRUPTCY": {"effects": {"endurance": 2, "survival": 2}},
    "FY_ALIEN_CONTACT": {"effects": {"intelligence": 3, "willpower": 2, "protomolecule_theory": 3}},
    "FY_CORPORATE_HEIR_TRAINING": {"effects": {"charisma": 2, "intelligence": 2, "negotiation": 2}},
    "FY_UNDERGROUND_RACING": {"effects": {"dexterity": 2, "piloting": 3}, "heat": 2},
    "FY_RELIGIOUS_AWAKENING": {"effects": {"willpower": 3, "charisma": 1, "empathy_read": 2}},
    "FY_MEMORY_WIPE": {"effects": {"intelligence": -1, "willpower": 2},
                       "flavor": "Часть воспоминаний стёрта — по какой-то причине. Иногда это спасает."},
    "FY_GENIUS_DISCOVERY": {"effects": {"intelligence": 3, "tech_empathy": 2, "research_method": 3}},
    "FY_GANG_INITIATION": {"effects": {"combat": 2, "criminal": 2}, "heat": 3},
    "FY_ARTISTIC_PRODIGY": {"effects": {"charisma": 3, "intelligence": 1, "performance": 3}},
    "FY_SURVIVAL_TRAINING": {"effects": {"endurance": 3, "survival": 3, "willpower": 1}},
    "FY_FIRST_KILL": {"effects": {"combat": 2, "willpower": 1},
                      "flavor": "Это воспоминание не отпускает — и меняет человека."},
    "FY_MENTOR_DEATH": {"effects": {"willpower": 2, "education": 2},
                        "flavor": "Уроки наставника — теперь ваша ноша и наследие. Стресс не проходит бесследно."},
    "FY_HACKER_PRODIGY_ADVANCED": {"effects": {"intelligence": 3, "hacking": 4}, "heat": 4},
    "FY_POLITICAL_ASSASSINATION": {"effects": {"stealth": 2, "law": 1}, "heat": 3},
    "FY_SPACE_MADNESS": {"effects": {"willpower": 3, "empathy_read": 2},
                         "flavor": "То, что вы увидели в себе во время того эпизода, осталось с вами."},
    "FY_GENETIC_ENHANCEMENT": {"effects": {"endurance": 2, "medicine": 2}, "heat": 2},
}

changed = 0
for fid, fix in FIX.items():
    rec = nfy.get(fid)
    if rec is None:
        print("НЕТ ЗАПИСИ:", fid)
        continue
    rec["effects"] = fix["effects"]
    if "heat" in fix:
        rec["heat_mods"] = fix.pop("heat") if False else fix["heat"]
    if "flavor" in fix:
        desc = rec.get("description", "")
        if fix["flavor"] not in desc:
            rec["description"] = desc.rstrip(".") + ". " + fix["flavor"]
    changed += 1

json.dump(doc, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"Обновлено записей: {changed}/17")

# Контроль: призраков не осталось
GHOSTS = ("psychology_skill", "occult_skill", "entertainment_skill", "hacking_skill",
          "combat_skill", "criminal_skill", "medicine_skill", "survival_skill",
          "negotiation_skill", "stealth_skill", "law_skill", "science_skill",
          "piloting_skill", "mystery_bonus", "one_chosen_skill", "choose_attribute",
          "humanity", "stress", "credits")
bad = []
for fid, rec in nfy.items():
    for k in rec.get("effects", {}):
        if k in GHOSTS:
            bad.append((fid, k))
print("Осталось призрачных ключей:", bad if bad else "0 ✅")
print("heat_mods у записей:", [f for f, r in nfy.items() if "heat_mods" in r])
