"""
D4a-тесты: контекстные подсказки хакинг/расследование — контрактные фиксы.

Проверяет:
- Лут взлома применяется к персонажу (кошелёк → credits) и пишется в loot_log (H1)
- Sanity-урон Чёрного льда реально списывает current_sanity (H2)
- Снимок узлов отдаётся с UI-ключами и входит в hack_state (H3)
- Контракт улик: description/type из UI доходит до clue.text/source (I1)
- /api/investigation/list маппит clues/required_clues/leads для UI (I2)
- suspect_name ← name fallback (I3)
- loot_log переживает save/load roundtrip (state-персистентность)

Не требуют запуска реального сервера или AI-бэкенда.
"""

import re

import pytest

from src.systems.subsystems import HackingSystem, ICE_TYPES


def _char():
    return {"credits": 100, "current_sanity": 50}


class TestHackingLoot:
    """H1: лут сохраняется в state.loot_log, кошельки конвертируются в кредиты."""

    def test_wallet_credits_parsed_and_applied(self):
        hs = HackingSystem()
        char = _char()
        applied = hs.apply_loot(char, "Электронный кошелёк: 200-500₡")
        assert 200 <= applied["credits"] <= 500
        assert char["credits"] == 100 + applied["credits"]
        assert len(hs.loot_log) == 1
        assert hs.loot_log[0]["credits"] == applied["credits"]

    def test_non_wallet_loot_logged_without_credits(self):
        hs = HackingSystem()
        char = _char()
        applied = hs.apply_loot(char, "Схема охранной системы здания")
        assert applied["credits"] == 0
        assert char["credits"] == 100
        assert len(hs.loot_log) == 1
        assert hs.loot_log[0]["text"].startswith("Схема")

    def test_extract_data_applies_loot_end_to_end(self):
        """Полный цикл: старт терминала → форс последнего узла без ICE → extract_data."""
        hs = HackingSystem()
        char = _char()
        hs.start_hack("terminal", 5, 3)
        h = hs.active_hack
        h["nodes"][-1]["ice"] = None
        h["current_node"] = len(h["nodes"]) - 1

        result = hs.hack_action("extract_data", character=char)
        assert result["success"] is True
        assert h["status"] == "success"

        loot = result["loot"]
        assert isinstance(loot, str) and loot
        assert len(hs.loot_log) == 1
        assert hs.loot_log[0]["text"] == loot

        m = re.search(r"кошел[её]к:\s*(\d+)-(\d+)₡", loot)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            delta = char["credits"] - 100
            assert lo <= delta <= hi
            assert result["credits_gained"] == delta
        else:
            assert char["credits"] == 100
            assert result.get("credits_gained", 0) == 0

    def test_loot_log_survives_save_roundtrip(self):
        hs = HackingSystem()
        hs.apply_loot({"credits": 0}, "Электронный кошелёк: 200-500₡")
        hs2 = HackingSystem.from_dict(hs.to_dict())
        assert hs2.loot_log == hs.loot_log


class TestBlackIceSanity:
    """H2: урон рассудку применяется к character, а не только к тексту."""

    def test_sanity_damage_applied_to_character(self):
        hs = HackingSystem()
        char = _char()
        # skill 0: бросок 2..12 < DC 14 Чёрного льда → гарантированный провал
        hs.start_hack("terminal", 0, 0)
        h = hs.active_hack
        black_ice = next(i for i in ICE_TYPES if i["type"] == "black_ice")
        h["nodes"][0]["ice"] = dict(black_ice)
        h["nodes"][0]["ice"]["active"] = True

        result = hs.hack_action("crack_ice", character=char)
        assert result["success"] is False
        assert result["sanity_damage"] >= 2
        assert char["current_sanity"] == 50 - result["sanity_damage"]
        assert result["sanity_after"] == char["current_sanity"]

    def test_no_character_arg_keeps_old_behaviour(self):
        """Обратная совместимость: без character урон только в ответе (старые вызовы)."""
        hs = HackingSystem()
        hs.start_hack("terminal", 0, 0)
        h = hs.active_hack
        black_ice = next(i for i in ICE_TYPES if i["type"] == "black_ice")
        h["nodes"][0]["ice"] = dict(black_ice)
        h["nodes"][0]["ice"]["active"] = True

        result = hs.hack_action("crack_ice")
        assert result["success"] is False
        assert "sanity_damage" in result
        assert "sanity_after" not in result  # применять некому


class TestNodesSnapshot:
    """H3: снимок узлов с ключами UI, входит в hack_state каждого действия."""

    def test_snapshot_keys_match_ui_contract(self):
        hs = HackingSystem()
        hs.start_hack("security", 3, 3)  # 3 узла, 2 ICE
        snap = hs.nodes_snapshot(hs.active_hack)
        assert len(snap) == 3
        expected = {"idx", "current", "cleared", "ice_type", "data"}
        assert all(expected <= set(n.keys()) for n in snap)
        assert snap[0]["current"] is True
        assert isinstance(snap[0]["cleared"], bool)
        assert snap[0]["data"] is None       # не-последний узел без метки данных
        assert snap[-1]["data"] is not None  # последний узел помечен данными

    def test_hack_action_includes_snapshot(self):
        hs = HackingSystem()
        hs.start_hack("terminal", 5, 5)
        result = hs.hack_action("disconnect")
        nodes = result["hack_state"]["nodes"]
        assert nodes and "cleared" in nodes[0]
