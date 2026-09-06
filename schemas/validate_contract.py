#!/usr/bin/env python3
"""NexusRPG contract validator.

Usage:
  python schemas/validate_contract.py            # check all game_data/*.json (top level)
  python schemas/validate_contract.py --fix      # auto-fix missing priority (domain defaults) and bad version strings
Exit codes: 0 = all valid, 1 = violations found.
"""
import sys, os, json, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GD = os.path.join(ROOT, "game_data")

# --- priority defaults by module domain (used only with --fix, only when priority is absent) ---
DOMAIN_PRIORITY = [
    (re.compile(r"^(AI_RPG_CORE|META_ENGINE)$"), 45),
    (re.compile(r"^(CHARACTER_LIFEPATH|CHARACTER_SPECIALIZATIONS|STARTING_QUESTS_COMPLETE|TECH_EQUIPMENT|THEME_TONE)$"), 40),
    (re.compile(r"(REPUTATION|STANDARDIZED|PSYCHOLOGY$)"), 35),
    (re.compile(r"^(ECONOMY|COMBAT|POLITICS|VEHICLES|QUEST_SYSTEM|NPC_RELATIONS|CRAFTING_BLUEPRINTS)"), 30),
    (re.compile(r"(_V2_|_GENERATOR|_COORDINATOR|PROTOCOL|INDEX)"), 25),
    (re.compile(r"^(RULEBOOK|SESSION_LOG|WORLD_TIME|TIME_DISPLAY|PLAYER_VIEW|VISUALS|TECHNOLOGY|STRATEGIC|TRADE_ROUTES|MARKET_EVENT|NEWS_AND|SPACE_ENCOUNTER|TECH_MALFUNCTION|NPC_NAME)"), 20),
    (re.compile(r"^(lore_chronology|balanced_character_presets|module_examples)"), 10),
]

BAD_VERSION_FIX = {
    "FINAL_1.0_COMPLETE_ENFORCEMENT": "1.0_FINAL_ENFORCEMENT",
}

PRIORITY_STRING_MAP = {
    "ABSOLUTE_CRITICAL": 25,
    "CRITICAL": 30,
    "HIGH": 25,
    "MEDIUM": 20,
    "LOW": 10,
}

def default_priority(stem):
    for rx, p in DOMAIN_PRIORITY:
        if rx.search(stem):
            return p
    return 15

def validate_file(path, fix=False):
    rel = os.path.relpath(path, ROOT)
    errs = []
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"{rel}: JSON parse error: {e}"]
    if not isinstance(d, dict):
        return [f"{rel}: top-level не объект"]

    changed = False
    # module_name (цифровые префиксы бандлов вида 01_ разрешены)
    mn = d.get("module_name")
    if not isinstance(mn, str) or not re.fullmatch(r"(\d{2}_)?[A-Z][A-Z0-9_]{2,63}", mn):
        lib = d.get("library_name")
        if isinstance(lib, str) and re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", lib):
            if fix:
                d["module_name"] = d.pop("library_name") if "library_name" in d else lib
                changed = True
                errs.append(f"{rel}: FIX library_name -> module_name")
            else:
                errs.append(f"{rel}: нет module_name (есть library_name={lib!r}) — нужен перенос поля")
        elif fix:
            stem0 = os.path.splitext(os.path.basename(path))[0]
            guess = re.sub(r"[^A-Za-z0-9_]", "", stem0).upper()
            if re.fullmatch(r"(\d{2}_)?[A-Z][A-Z0-9_]{2,63}", guess):
                d["module_name"] = guess; changed = True
                errs.append(f"{rel}: FIX module_name -> {guess!r} (из имени файла)")
            else:
                errs.append(f"{rel}: module_name отсутствует и не выводим из имени файла: {stem0!r}")
        else:
            errs.append(f"{rel}: module_name отсутствует или не SCREAMING_SNAKE_CASE: {mn!r}")
    else:
        stem = os.path.splitext(os.path.basename(path))[0]
        norm = lambda s: re.sub(r"[^A-Z0-9]", "", s.upper())
        n_mn, n_stem = norm(mn), norm(stem)
        if n_mn != n_stem and not (n_mn in n_stem or n_stem in n_mn):
            errs.append(f"{rel}: module_name={mn!r} расходится с именем файла {stem!r}")

    # version
    v = d.get("version")
    if not isinstance(v, str) or not re.fullmatch(r"\d+\.\d+(_[A-Z0-9_]+)?", v):
        if fix and isinstance(v, str):
            nv = BAD_VERSION_FIX.get(v)
            if nv is None:
                m = re.match(r"^(\d+\.\d+)", v)
                nv = m.group(1) if m else None
            if nv:
                d["version"] = nv; changed = True
                errs.append(f"{rel}: FIX version {v!r} -> {nv!r}")
                v = nv
        if not isinstance(v, str) or not re.fullmatch(r"\d+\.\d+(_[A-Z0-9_]+)?", v):
            errs.append(f"{rel}: version отсутствует/не нормализована: {v!r}")

    # priority
    p = d.get("priority")
    if isinstance(p, str) and p in PRIORITY_STRING_MAP:
        if fix:
            d["priority"] = PRIORITY_STRING_MAP[p]; changed = True
            errs.append(f"{rel}: FIX priority {p!r} -> {d['priority']}")
            p = d["priority"]
        else:
            errs.append(f"{rel}: priority строкой ({p!r}) — должен быть int 1..50")
    if not isinstance(p, int) or not (1 <= p <= 50):
        if fix:
            stem = os.path.splitext(os.path.basename(path))[0]
            np_ = default_priority(stem)
            d["priority"] = np_; changed = True
            errs.append(f"{rel}: FIX priority -> {np_} (домейн по умолчанию)")
        elif not (isinstance(p, str) and p in PRIORITY_STRING_MAP):
            errs.append(f"{rel}: priority отсутствует или вне 1..50: {p!r}")

    if changed and fix:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    return errs

def main():
    fix = "--fix" in sys.argv
    files = sorted(f for f in os.listdir(GD) if f.endswith(".json"))
    all_errs = []
    for fn in files:
        all_errs += validate_file(os.path.join(GD, fn), fix=fix)
    print(f"Проверено файлов: {len(files)} | нарушений: {len(all_errs)} {'(исправлено на месте)' if fix else ''}")
    for e in all_errs:
        print(" -", e)
    sys.exit(1 if all_errs else 0)

if __name__ == "__main__":
    main()
