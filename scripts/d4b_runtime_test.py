# -*- coding: utf-8 -*-
"""D4b рантайм-тест: последствия хака и награды вывода на живом движке.

Сценарии:
1. Хак с гарантированным detected → character.heat +2 (сквозной через API)
2. conclude_case с correct=True → fame +20 в character (через API)
3. Suspect с faction → faction_rep_hit; без — только fame
"""
import json
import sys

sys.path.insert(0, "D:/NexusRPG-main")

from src.server.app import app, init_engine


def main():
    init_engine()
    engine = sys.modules["src.server.app"].engine

    presets = engine.get_presets()
    engine.create_character_from_preset(presets[0]["id"])
    char = engine.state.character
    char["heat"] = 1  # базовый уровень для проверки аккумуляции
    c = app.test_client()

    # ── Сценарий 1: detected → heat +2 ──
    r = c.post("/api/hacking/start", json={"target_type": "terminal"})
    assert r.status_code == 200, r.data
    # доводим alert до максимума и провоцируем fail
    hs = engine.hacking
    hs.active_hack["alert_level"] = hs.active_hack["max_alert"]
    heat_before = char["heat"]
    r = c.post("/api/hacking/action", json={"action": "crack_ice"})
    data = json.loads(r.data.decode("utf-8"))
    assert char["heat"] == heat_before + 2, \
        f"heat {char['heat']} != {heat_before}+2"
    assert data.get("heat_gained") == 2
    print(f"сценарий 1: detected → heat +2 ({heat_before}→{char['heat']}) ✅")

    # disconnect не добавляет heat
    r = c.post("/api/hacking/start", json={"target_type": "terminal"})
    r = c.post("/api/hacking/action", json={"action": "disconnect"})
    assert char["heat"] == heat_before + 2, "disconnect не должен давать heat"
    print("сценарий 1b: disconnect → +0 heat ✅")

    # ── Сценарий 2: верный вывод → fame +20 ──
    fame_before = char.get("fame", 0)
    case = engine.investigation.open_case("theft", "Дело D4b")
    for _ in range(case["clues_needed"]):
        engine.investigation.add_clue(case["id"], "улика", "камеры",
                                      reliability="high")
    engine.investigation.add_suspect(case["id"], "Виктор Моррис",
                                     motive="долги", evidence="отпечатки")
    case["suspects"][0]["faction"] = "Black Lotus Triad"

    import src.systems.subsystems as subsys
    orig_random = subsys.random.random
    subsys.random.random = lambda: 0.0  # гарантируем correct=True
    r = c.post("/api/investigation/conclude", json={
        "case_id": case["id"], "conclusion": "вор — Моррис",
        "suspect": "Виктор Моррис"})
    subsys.random.random = orig_random
    data = json.loads(r.data.decode("utf-8"))
    assert data["correct"] is True, data
    assert char.get("fame", 0) == fame_before + 20, \
        f"fame {char.get('fame')} != {fame_before}+20"
    assert data["fame_gained"] == 20
    assert data["faction_rep_hit"] == {"Black Lotus Triad": -5}
    print(f"сценарий 2: correct → fame +20 ({fame_before}→{char['fame']}), "
          f"rep-hit Black Lotus Triad −5 ✅")

    # ── Сценарий 3: suspect без faction — только fame ──
    fame_before = char["fame"]
    case2 = engine.investigation.open_case("murder", "Дело D4b-2")
    for _ in range(case2["clues_needed"]):
        engine.investigation.add_clue(case2["id"], "улика", "свидетели",
                                      reliability="high")
    engine.investigation.add_suspect(case2["id"], "Шакал", motive="месть")
    subsys.random.random = lambda: 0.0
    r = c.post("/api/investigation/conclude", json={
        "case_id": case2["id"], "conclusion": "убийца — Шакал",
        "suspect": "Шакал"})
    subsys.random.random = orig_random
    data = json.loads(r.data.decode("utf-8"))
    assert data["correct"] is True and data["fame_gained"] == 20
    assert "faction_rep_hit" not in data, "фракцию выдумывать нельзя"
    assert char["fame"] == fame_before + 20
    print("сценарий 3: suspect без faction → только fame ✅")

    print("\nD4b RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
