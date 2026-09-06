"""
Генератор новых фракций NexusRPG (Мастер-план Б1).
Канон: FACTIONS_MASTER.json. Правила:
  - уникальность имени и лора против 157 существующих;
  - без синтаксической рамки «основана в <год> для <цель>»;
  - у каждой фракции механические крючки с реальными target-полями
    (skill_bonus/combat_check/stealth/negotiation и т.п. — словарь движка);
  - у каждой — хотя бы один играбельный plot hook;
  - tie to TieredEventManager через поле event_tiers (какие тиры событий фракция порождает).
"""
import json, random, os

CANON = os.path.join(os.path.dirname(__file__), "..", "game_data", "FACTIONS_MASTER.json")

# Механические таргеты, которые реально читает движок/системы (Фаза 12: только эти слои живые)
VALID_MECH_TARGETS = {
    "combat_check", "stealth", "negotiation", "hacking", "investigation",
    "survival_check", "medicine", "piloting", "technology", "trade_margin",
}

def load_canon():
    with open(CANON, encoding="utf-8") as fh:
        return json.load(fh)

def check_unique(name, canon_data):
    existing = {f["name"] for f in canon_data["factions"] if "canonical_duplicate_of" not in f}
    return name not in existing

def make_faction(fid, name, ftype, history, legends, leaders, influence_region,
                 business_area, allies, enemies, mechanics, plot_hooks, event_tiers):
    for m in mechanics:
        if m.get("target") not in VALID_MECH_TARGETS:
            raise ValueError(f"{fid}: mechanic target {m.get('target')!r} не читается движком")
    return {
        "id": fid, "name": name, "type": ftype,
        "history": history, "legends": legends, "leaders": leaders,
        "influence_region": influence_region, "business_area": business_area,
        "allies": allies, "enemies": enemies,
        "mechanics": mechanics, "plot_hooks": plot_hooks,
        "event_tiers": event_tiers,   # связь с TieredEventManager
    }
