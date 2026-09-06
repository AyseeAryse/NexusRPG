# -*- coding: utf-8 -*-
"""Backlog#2 рантайм-тест: Data Rebels как полноценная фракция на живом движке.

Особый фокус пользователя:
1. rep за квестовую ветку «сеть Data Rebels» идёт в "Data Rebels",
   а НЕ в ByteHack/Теневые Пальцы (сквозной advance_quest с canonical_faction)
2. регион-фильтр D3 не путает Data Rebels с соседями Нижнего города/Лунных туннелей
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

    # ── ФОКУС 1: сквозной rep-поток квеста в Data Rebels ──
    # Квест с reward_reputation {"Data Rebels": 8} — как теперь даёт ветка
    engine.state.active_quests.append({
        "id": "test_dr", "title": "Ночной эфир (ветка DR)",
        "status": "active", "stages": [], "current_stage": 0,
        "reward_credits": 0, "reward_xp": 0,
        "reward_reputation": {"Data Rebels": 8},
        "tier": 5,
    })
    fame_before = getattr(engine.state, "fame", 0)
    c = app.test_client()
    r = c.post("/api/quest/advance", json={"quest_id": "test_dr"})
    assert r.status_code == 200, r.data

    reps = engine.state.faction_reputation
    print("faction_reputation после advance:", reps)
    assert reps.get("Data Rebels") == 8, (
        f"rep должен уйти в Data Rebels, факт: {reps}")
    assert "Клан «Теневые Пальцы»" not in reps or \
        reps.get("Клан «Теневые Пальцы»", 0) == 0, "костыльный получатель получил rep!"
    assert reps.get("ByteHack Collective", 0) == 0, "ByteHack не должен получать"
    assert getattr(engine.state, "fame", 0) > fame_before, "fame за квест не начислен"
    print("ФОКУС 1: rep +8 → 'Data Rebels' ✅ (не ByteHack, не Теневые Пальцы), fame растёт ✅")

    # ── ФОКУС 2: регион-фильтр D3 не путает Data Rebels с соседями ──
    # Дизайн D3a: regional = планетный фильтр (фракции без rep);
    # contacts = глобальные (rep>0). Сначала — ЧИСТЫЙ персонаж (rep нет):
    # SC52 должна быть в regional Земли и Луны, и НЕ быть на Марсе/Поясе.
    engine.state.faction_reputation.pop("Data Rebels", None)
    for planet, expect in (("Земля", True), ("Луна", True),
                           ("Марс", False), ("Пояс астероидов", False)):
        r = c.get(f"/api/factions/catalog?planet={planet}")
        data = json.loads(r.data.decode("utf-8"))
        regional_names = [f["name"] for f in data.get("regional", [])]
        has_dr = "Data Rebels" in regional_names
        assert has_dr == expect, \
            f"{planet}: DR в regional = {has_dr}, ожидалось {expect}"
        if planet == "Земля":
            neighbors = [n for n in regional_names
                         if n in ("OPA", "Black Lotus Triad")]
            print(f"  {planet}: DR в regional ✅ (соседи: {neighbors})")
        else:
            print(f"  {planet}: DR в regional = {has_dr} ✅")

    # ── Теперь rep 8 (ФОКУС 1 уже дал) → DR переезжает в contacts глобально ──
    engine.state.faction_reputation["Data Rebels"] = 8  # вернули после pop
    r = c.get("/api/factions/catalog?planet=Марс")
    data = json.loads(r.data.decode("utf-8"))
    contact_names = [f["name"] for f in data.get("contacts", [])]
    regional_names = [f["name"] for f in data.get("regional", [])]
    assert "Data Rebels" in contact_names, "DR с rep должна быть в контактах"
    assert "Data Rebels" not in regional_names, \
        "DR с rep не должна остаться в региональных Марса"
    print("  Марс при rep 8: DR в КОНТАКТАХ (глобально) ✅, "
          "в regional Марса её нет ✅")

    # Земля: rep уже есть (ФОКУС 1) → DR обязана быть в contacts, не в regional
    r = c.get("/api/factions/catalog?planet=Земля")
    data = json.loads(r.data.decode("utf-8"))
    contact_names = [f["name"] for f in data.get("contacts", [])]
    regional_names = [f["name"] for f in data.get("regional", [])]
    assert "Data Rebels" in contact_names, (
        f"DR должна быть в контактах Земли (rep 8)")
    assert "Data Rebels" not in regional_names
    print(f"  Земля: Data Rebels в КОНТАКТАХ (rep 8) ✅, "
          f"в региональных — соседи: "
          f"{[n for n in regional_names if n in ('OPA', 'Black Lotus Triad')]}" )

    # Полная карточка при rep>=20 содержит механики и hooks
    engine.state.faction_reputation["Data Rebels"] = 25
    r = c.get("/api/factions/catalog?planet=Земля")
    contacts = json.loads(r.data.decode("utf-8")).get("contacts", [])
    dr = next((x for x in contacts if x["name"] == "Data Rebels"), None)
    assert dr and dr.get("full_details"), "полная карточка не раскрылась при rep 25"
    fd = dr["full_details"]
    assert fd["history"].startswith("Родились из утёкших архивов")
    assert any("info_trade" in m for m in fd["mechanics"])
    assert len(fd["plot_hooks"]) == 2
    print("полная карточка (rep 25): история + info_trade механика + 2 хука ✅")
    engine.state.faction_reputation["Data Rebels"] = 8  # вернуть состояние

    print("\nBACKLOG#2 RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
