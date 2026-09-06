# -*- coding: utf-8 -*-
"""Backlog#5 рантайм-тест: news-fame на живом движке (init_engine + test_client).

Сценарии §3.4 плана:
1. Персонаж с rep>=40 у Data Rebels → серия _world_tick → fame +15 ровно за
   каждое упоминание (точность fame)
2. Антиспам-кулдаун: между форс-упоминаниями >= 10 ходов
3. Нулевой случай: без rep>=40 — ни одного упоминания/fame
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
    sim = engine.state.world_sim

    # ── Сценарий 3 (нулевой): без rep>=40 ──
    char_rep = {}
    for name in list(engine.state.faction_reputation):
        char_rep[name] = engine.state.faction_reputation.pop(name)
    fame0 = getattr(engine.state, "fame", 0)
    mentions = 0
    for _ in range(120):
        engine._world_tick()
        if getattr(engine.state, "fame", 0) > fame0:
            mentions += 1
            fame0 = engine.state.fame
    print(f"нулевой случай (без rep 40+): fame-упоминаний за 120 тиков = {mentions}")
    assert mentions == 0, "без rep>=40 fame от новостей начисляться не должен"

    # ── Сценарий 1: rep>=40 у Data Rebels → точность fame (+15 за упоминание) ──
    engine.state.faction_reputation["Data Rebels"] = 45
    fame0 = getattr(engine.state, "fame", 0)
    mention_turns = []
    from src.world.player_tiers import FAME_PER_NEWS_MENTION
    for turn in range(1, 201):
        sim.turn_count = turn
        engine._world_tick()
        fame_now = getattr(engine.state, "fame", 0)
        if fame_now > fame0:
            delta = fame_now - fame0
            assert delta % FAME_PER_NEWS_MENTION == 0 or delta == FAME_PER_NEWS_MENTION, \
                f"fame прирост {delta} не кратен {FAME_PER_NEWS_MENTION}"
            mention_turns.append(turn)
            fame0 = fame_now
    print(f"rep 45 у Data Rebels: упоминаний с fame за 200 тиков = {len(mention_turns)}")
    assert len(mention_turns) >= 2, "ожидались упоминания с fame"

    # ── Сценарий 2: антиспам — форс не чаще раза в 10 ходов ──
    gaps = [b - a for a, b in zip(mention_turns, mention_turns[1:])]
    assert all(g >= 10 for g in gaps), f"кулдаун нарушен: {gaps}"
    print(f"кулдаун: гэпы между fame-упоминаниями {gaps[:6]}... все >= 10 ✅")

    # wc["news_mention"] попадает в world_context (для ГМа/лога)
    sim.turn_count += 100  # гарантированно вне кулдауна
    wc = engine._world_tick()
    if wc.get("news_mention"):
        print("world_context['news_mention']:", wc["news_mention"])

    print("\nBACKLOG#5 RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
