# -*- coding: utf-8 -*-
"""Backlog#4 (III) рантайм-тест: региональная легальность на живом движке.

Сценарии:
1. Один и тот же restricted-предмет (I_ADRENALINE) покупается на Земле
   (+1 heat) и на Ганимеде (+0 heat — местный legal)
2. На Марсе restricted = illegal → +3 heat
3. heat_survival >= 5 смягчает штраф illegal 3→2 (и restricted 1→0... нет:
   минимум 1, поэтому restricted не меняется; проверяем на illegal)
"""
import json
import sys

sys.path.insert(0, "D:/NexusRPG-main")

from src.server.app import app, init_engine


def setup_planet(engine, planet):
    engine.state.current_location["planet"] = planet
    engine.state.current_location.setdefault("city", "Столица")
    engine.state.current_location.setdefault("district", "Центр")


def main():
    init_engine()
    engine = sys.modules["src.server.app"].engine

    presets = engine.get_presets()
    engine.create_character_from_preset(presets[0]["id"])
    char = engine.state.character
    char["credits"] = 100_000
    c = app.test_client()
    item_id = "I_ADRENALINE"  # restricted в каталоге

    # ── Сценарий 1: Земля → restricted → +1 ──
    setup_planet(engine, "Земля")
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("heat_gained") == 1, d.get("heat_gained")
    assert d.get("local_legality") == "restricted"
    print(f"Земля: I_ADRENALINE → local=restricted, heat +1 ✅")

    # ── Сценарий 2: Ганимед → legal → +0 ──
    setup_planet(engine, "Ганимед")
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("heat_gained") == 0, d
    assert d.get("local_legality") == "legal"
    print("Ганимед: тот же предмет → local=legal, heat +0 ✅")

    # ── Сценарий 3: Марс → illegal → +3 ──
    setup_planet(engine, "Марс")
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("local_legality") == "illegal", d
    assert d.get("heat_gained") == 3, d
    print(f"Марс: тот же предмет → local=illegal, heat +3 ✅")

    # ── Сценарий 4: Пояс астероидов → legal → +0 ──
    setup_planet(engine, "Пояс астероидов")
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("local_legality") == "legal" and d.get("heat_gained") == 0
    print("Пояс астероидов: local=legal, heat +0 ✅")

    total_heat = char["heat"]
    assert total_heat == 1 + 3, f"итого heat {total_heat}, ожидалось 4"
    print(f"аккумуляция heat за 4 покупки: {total_heat} ✅")

    # ── Сценарий 5: heat_survival >= 5 смягчает illegal 3→2 ──
    char["skills"]["heat_survival"] = 5
    setup_planet(engine, "Марс")
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("heat_gained") == 2, d
    assert "Тепловое выживание" in d.get("message", "")
    print(f"heat_survival=5: illegal-штраф 3→2, сообщение со щитом ✅")

    # skill < 5 — без смягчения
    char["skills"]["heat_survival"] = 4
    char["credits"] += 50_000  # пополнение: серия покупок дорога
    r = c.post("/api/shop/buy", json={"item_id": item_id})
    d = json.loads(r.data.decode("utf-8"))
    assert d.get("heat_gained") == 3, d
    print("heat_survival=4: без смягчения (+3) ✅")

    print("\nBACKLOG#4(III) RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
