# Фаза 24c B5: поле legality (legal|restricted|illegal) в обоих каталогах.
# Авторазметка по одобренным правилам:
#   illegal: криминальные теги (Underworld/Criminal/Improvised), кустарное/самодельное
#            (обрезы, заточки, игломёты), Military-тяжёлое (Плазменное, Power Armor)
#   restricted: Military/Stealth, энергетическое/снайперское оружие, эпик+ импланты,
#            стимуляторы (Адреналин-X)
#   legal: остальное
import json, re

ROOT = r"D:\NexusRPG-main"

def classify_tech(it):
    tags = set(it.get("context_tags", []))
    t = it.get("type", "")
    name = it.get("name", "")
    if tags & {"Underworld", "Criminal", "Improvised"} or re.search(
            r"кустарн|самодельн|заточк|обрез", name, re.I):
        return "illegal"
    if "Military" in tags and (tags & {"Heavy", "Power_Armor"} or "Плазменное" in t):
        return "illegal"
    if tags & {"Military", "Stealth"} or "Энергетическое" in t or "Снайперская" in t:
        return "restricted"
    if it.get("type") == "Имплант" and it.get("rarity") in (
            "эпический", "легендарный", "уникальный", "артефакт"):
        return "restricted"
    return "legal"

def classify_shop(it, cat):
    name = it.get("name", "")
    if re.search(r"(кустарн|самодельн|заточк|обрез|подпольн|контрабанд|нелегаль)", name, re.I):
        return "illegal"
    if "нелегальн" in name.lower() or "нелегальный" in name.lower():
        return "illegal"
    if cat == "weapons" and re.search(
            r"(плазм|лазер|снайпер|электромагнит|рельсов|гранатомёт|гранатомет|пулемёт|пулемет)", name, re.I):
        return "restricted"
    if cat == "implants" and it.get("rarity") in ("epic", "legendary"):
        return "restricted"
    if re.search(r"адреналин|стимулятор", name, re.I) and cat == "consumables":
        return "restricted"
    return "legal"

# ── TECH_EQUIPMENT.json ──
p1 = rf"{ROOT}\game_data\TECH_EQUIPMENT.json"
te = json.load(open(p1, encoding="utf-8"))
cnt = {"legal": 0, "restricted": 0, "illegal": 0}
for cat in ("weapons", "armor", "gadgets", "implants"):
    for it in te[cat]:
        it["legality"] = classify_tech(it)
        cnt[it["legality"]] += 1
json.dump(te, open(p1, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"TECH_EQUIPMENT: размечено {sum(cnt.values())} → {cnt}")

# ── BASE_SHOP_ITEMS: живёт в коде (simulation.py), но витрина продаётся из данных?
# Проверка: у shop-предметов нет JSON-источника — они собираются в simulation.py.
# Значит разметка должна жить в коде рядом с определением. Ищем источник.
import subprocess
code = r'''
import sys; sys.path.insert(0, r"D:\NexusRPG-main")
import os; os.chdir(r"D:\NexusRPG-main")
from src.world.simulation import BASE_SHOP_ITEMS, EXPANDED_SHOP_ITEMS
print("EXPANDED is BASE:", EXPANDED_SHOP_ITEMS is BASE_SHOP_ITEMS)
import inspect, src.world.simulation as s
src = inspect.getsource(s)
for name in ("V2_SHOP_ITEMS", "V3_SHOP_ITEMS", "EXPANDED_SHOP_ITEMS"):
    i = src.find(f"{name} = ")
    print(name, "->", src[i:i+80].replace(chr(10), " ") if i >= 0 else "не найдено")
'''
r = subprocess.run([r"C:\Users\Aryse\AppData\Local\Programs\Python\Python311\python.exe", "-c", code],
                   capture_output=True, text=True, timeout=120)
print(r.stdout)
print(r.stderr[-200:] if r.returncode else "")
