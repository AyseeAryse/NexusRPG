"""
D4b: механика последствий хака и наград за вывод дела (без GM-парсера).

Проверяет:
- Heat при провале: detected → +2, timeout → +1, disconnect → 0
- Heat реально пишется в character dict (как sanity в D4a)
- conclude_case correct=True → fame +20 (FAME_PER_CORRECT_CONCLUSION)
- Suspect с faction → faction_rep_hit в результате (−5); без faction — нет
- Неверный вывод → никаких наград
- character=None → старое поведение (без падений)
"""

import pytest

from src.systems.subsystems import HackingSystem, InvestigationSystem
from src.world.player_tiers import FAME_PER_CORRECT_CONCLUSION


def make_char():
    return {"name": "Тест", "credits": 100, "heat": 0, "fame": 0}


class TestHeatOnFail:
    def test_detected_gives_2_heat(self):
        hs = HackingSystem()
        char = make_char()
        hs.start_hack("terminal", player_hacking=3, player_stealth=3)
        hack = hs.active_hack
        hack["alert_level"] = hack["max_alert"]  # гарантированный detected
        hs.hack_action("crack_ice", character=char)
        assert char["heat"] == 2

    def test_timeout_gives_1_heat(self):
        hs = HackingSystem()
        char = make_char()
        hs.start_hack("terminal", player_hacking=99, player_stealth=99)
        hs.active_hack["turns_left"] = 1  # истечёт после любого действия
        hs.hack_action("stealth_bypass", character=char)
        # timeout может сочетаться с detected — heat берётся от финального статуса;
        # здесь alert не на максимуме, значит чистый timeout
        assert char["heat"] == 1

    def test_disconnect_gives_0_heat(self):
        hs = HackingSystem()
        char = make_char()
        hs.start_hack("terminal", player_hacking=3, player_stealth=3)
        hs.hack_action("disconnect", character=char)
        assert char["heat"] == 0

    def test_heat_accumulates_with_existing(self):
        hs = HackingSystem()
        char = make_char()
        char["heat"] = 3  # уже есть с B5-покупок
        hs.start_hack("terminal", player_hacking=3, player_stealth=3)
        hs.active_hack["alert_level"] = hs.active_hack["max_alert"]
        hs.hack_action("crack_ice", character=char)
        assert char["heat"] == 5


class TestConclusionReward:
    @pytest.fixture
    def full_case(self):
        """Дело с полным набором надёжных улик и двумя подозреваемыми."""
        inv = InvestigationSystem()
        case = inv.open_case("theft", "Дело о краже")
        for _ in range(case["clues_needed"]):
            inv.add_clue(case["id"], "улика", "камеры", reliability="high")
        inv.add_suspect(case["id"], "Виктор Моррис", motive="долги",
                        evidence="отпечатки")
        # подозреваемый с привязкой к фракции
        case["suspects"][0]["faction"] = "Black Lotus Triad"
        return inv, case

    def test_correct_conclusion_fame_and_rep_hit(self, full_case, monkeypatch):
        inv, case = full_case
        monkeypatch.setattr("src.systems.subsystems.random.random",
                            lambda: 0.0)  # гарантируем correct=True
        char = make_char()
        r = inv.conclude_case(case["id"], "вор — Моррис",
                              suspect_name="Виктор Моррис", character=char)
        assert r["correct"] is True
        assert char["fame"] == FAME_PER_CORRECT_CONCLUSION == 20
        assert r["fame_gained"] == 20
        assert r["faction_rep_hit"] == {"Black Lotus Triad": -5}

    def test_no_faction_on_suspect_only_fame(self, full_case, monkeypatch):
        inv, case = full_case
        del case["suspects"][0]["faction"]
        monkeypatch.setattr("src.systems.subsystems.random.random",
                            lambda: 0.0)
        char = make_char()
        r = inv.conclude_case(case["id"], "вор — Моррис",
                              suspect_name="Виктор Моррис", character=char)
        assert r["correct"] is True
        assert char["fame"] == 20
        assert "faction_rep_hit" not in r  # не выдумываем фракцию

    def test_wrong_conclusion_no_rewards(self, full_case, monkeypatch):
        inv, case = full_case
        # точность 100% (все high-улики) не может дать wrong — режем набор:
        # 2/4 medium-улики → accuracy ~0.5; random=0.99 → correct=False
        case["clues_found"] = case["clues_found"][:2]
        for clue in case["clues_found"]:
            clue["reliability"] = "medium"
        monkeypatch.setattr("src.systems.subsystems.random.random",
                            lambda: 0.99)
        char = make_char()
        r = inv.conclude_case(case["id"], "неверно",
                              suspect_name="Виктор Моррис", character=char)
        assert r["correct"] is False
        assert char["fame"] == 0
        assert "fame_gained" not in r and "faction_rep_hit" not in r

    def test_character_none_backward_compatible(self, full_case, monkeypatch):
        inv, case = full_case
        monkeypatch.setattr("src.systems.subsystems.random.random",
                            lambda: 0.0)
        r = inv.conclude_case(case["id"], "вывод")  # без character
        assert r["correct"] is True  # логика точности работает как раньше
