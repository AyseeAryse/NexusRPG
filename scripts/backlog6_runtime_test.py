# -*- coding: utf-8 -*-
"""Backlog#6 рантайм-тест: [STATE].location с опечаткой канонизируется сквозным путём.

Проверяет _parse_ai_response → _canonicalize_location → current_location
на живом движке (init_engine), включая интеграцию с фильтром D3.
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
    assert engine.state is not None

    # Симулируем ответ AI с классической миной (латинская Z + EN город)
    fake_response = (
        "Ты спускаешься в шумный квартал.\n\n"
        '[STATE]{"hp_change":0,"credits_change":0,"stress_change":0,'
        '"humanity_change":0,"location":{"planet":"Zемля","city":"Нью-Токио",'
        '"district":"Индустриальный коридор"},"add_items":[],"remove_items":[],'
        '"npc_met":null,"quest_complete":null,"quest_advance":false,'
        '"combat_started":false,"combat_ended":false,"time_minutes":15,'
        '"xp_gained":5}[/STATE]'
    )
    engine._parse_ai_response(fake_response)
    loc = engine.state.current_location
    print("current_location после [STATE]:", loc)
    assert loc["planet"] == "Земля", loc  # было бы 'Zемля' до фикса
    assert loc["city"] == "Нью-Токио"
    assert loc["district"] == "Индустриальный коридор"

    # Интеграция D3: фильтр региона теперь матчит планету
    with app.test_client() as c:
        r = c.get("/api/factions/catalog?planet=Земля")
        data = json.loads(r.data.decode("utf-8"))
    regional = data.get("regional", [])
    print(f"D3 каталог для 'Земля': {len(regional)} фракций региона")
    assert len(regional) >= 20, f"ожидали ~24, получили {len(regional)}"

    # Незнакомый мир ГМа проходит без искажения
    fake2 = ('Сцена.\n[STATE]{"location":{"planet":"Кванта-7","city":"Руины"},'
             '"time_minutes":10}[/STATE]')
    engine._parse_ai_response(fake2)
    loc2 = engine.state.current_location
    print("незнакомый мир сохранён:", loc2["planet"], "/", loc2["city"])
    assert loc2["planet"] == "Кванта-7" and loc2["city"] == "Руины"

    print("\nBACKLOG#6 RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
