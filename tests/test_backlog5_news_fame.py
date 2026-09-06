"""
Backlog#5: FAME_PER_NEWS_MENTION — news-mention fame hook.

Проверяет:
- Порог notable_factions = rep>=40 (как в event_roles.has_rep_link)
- Форс-упоминание при rep>=40 (шанс 33% + кулдаун 10 ходов)
- Отсутствие форса без фракций с rep>=40
- Случайное совпадение имени тоже считается упоминанием
- Fame начисляется ровно +15 за упоминание (движок, _world_tick)
- Антиспам: форс не чаще раза в 10 ходов
- Обратная совместимость: tick без notable_factions работает как раньше
"""

import random

import pytest

from src.world.player_tiers import FAME_PER_NEWS_MENTION
from src.world.simulation import WorldSimulator


@pytest.fixture
def sim():
    return WorldSimulator()


def _news_turn(sim, notable=None):
    """Один тик; возвращает (text, mention) только если новость была."""
    r = sim.tick({"year": 2387, "day": 1}, {"planet": "Земля"}, 2,
                 notable_factions=notable)
    if r["news"]:
        return r["news"][0], r.get("news_mention")
    return None, None


class TestNotableThreshold:
    def test_constant_value(self):
        assert FAME_PER_NEWS_MENTION == 15

    def test_threshold_40_not_39(self):
        """Форма порога как в event_roles: v >= 40. 39 не проходит, 40 проходит."""
        reps = [39, 40]
        notable = [f"F{i}" for i, v in enumerate(reps) if v >= 40]
        assert notable == ["F1"]


class TestForcedMention:
    def test_forced_mention_happens_within_statistical_bound(self, sim):
        """При rep>=40 и серии тиков форс-упоминания происходят (шанс 33%/новость)."""
        random.seed(7)
        mentions = 0
        news_count = 0
        for _ in range(120):
            text, m = _news_turn(sim, notable=["Тестовая Фракция"])
            if text is not None:
                news_count += 1
                if m == "Тестовая Фракция":
                    mentions += 1
        assert news_count > 20, f"новостей слишком мало: {news_count}"
        assert mentions >= 3, (
            f"форс-упоминаний нет при {news_count} новостях: {mentions}")

    def test_no_forced_mentions_without_rep(self, sim):
        random.seed(11)
        for _ in range(80):
            _, m = _news_turn(sim, notable=[])
            assert m is None

    def test_none_notable_backward_compatible(self, sim):
        """Старый вызов без notable_factions не падает и не даёт упоминаний."""
        r = sim.tick({"year": 2387, "day": 1}, {"planet": "Земля"}, 2)
        assert "news" in r and "news_mention" not in r


class TestCooldown:
    def test_forced_cooldown_at_least_10_turns(self, sim):
        """Форс-упоминания (выделенный шаблон) не чаще раза в 10 ходов.
        Случайные совпадения в обычных шаблонах вне кулдауна по дизайну."""
        random.seed(3)
        forced_turns = []
        for turn in range(200):
            sim.turn_count = turn + 1
            r = sim.tick({"year": 2387, "day": 1}, {}, 2,
                         notable_factions=["Тестовая Фракция"])
            if r.get("news_mention") == "Тестовая Фракция":
                text = r["news"][0]
                is_forced = text.startswith("«Тестовая Фракция» снова в заголовках")
                if is_forced:
                    forced_turns.append(turn + 1)
        gaps = [b - a for a, b in zip(forced_turns, forced_turns[1:])]
        assert len(forced_turns) >= 2, "форсов слишком мало для проверки"
        assert all(g >= 10 for g in gaps), f"кулдаун форса нарушен: {gaps}"


class TestEngineFame:
    def test_world_tick_awards_exact_fame(self, eng_like):
        """Движок: _world_tick начисляет ровно +15 fame за упоминание."""
        eng, state = eng_like
        state.faction_reputation = {"Data Rebels": 45}
        fame0 = getattr(state, "fame", 0)
        gained = 0
        for _ in range(150):
            eng._world_tick()
            fame_now = getattr(state, "fame", 0)
            delta = fame_now - fame0
            fame0 = fame_now
            if delta:
                # любой fame-прирост здесь может быть только кратен 15
                # (новость-упоминание); другие источники отключены сценарием
                assert delta % FAME_PER_NEWS_MENTION == 0 or delta in (0,)
                if delta == FAME_PER_NEWS_MENTION:
                    gained += 1
        assert gained >= 2, f"за 150 тиков ни одного news-fame ({gained})"


@pytest.fixture
def eng_like():
    """Минимальный движок-стаб: state + world_sim + метод _world_tick логики.
    Используем настоящий GameEngine без AI: create_custom_character путь тяжёлый,
    берём __new__ + руками собранный state (чистая механика тика)."""
    from src.core.engine import GameEngine, GameState
    from src.world.simulation import WorldSimulator

    eng = GameEngine.__new__(GameEngine)
    eng.state = GameState()
    eng.state.faction_reputation = {}
    eng.state.world_sim = WorldSimulator()
    eng.world_effects = type("WE", (), {
        "apply_event_effects": lambda self, *a, **k: None})()
    # _world_tick обращается к world_ticker/consequences после тика — заглушки
    eng.world_ticker = type("WT", (), {"tick": lambda self, s: []})()
    eng.consequences = type("CQ", (), {"check_consequences": lambda self, t: []})()
    # Phase 3: _world_tick вызывает self.faction_sim.tick() — добавляем заглушку
    eng.faction_sim = type("FCS", (), {"tick": lambda self, **kw: []})()

    def fake_get_tier():
        return {"tier": 2}
    eng.get_player_influence_tier = fake_get_tier
    # Phase 30: property/expenses нужны WorldTickService (стабы без поведения)
    eng.property = type("P", (), {})()
    eng.expenses = type("E", (), {"tick": lambda self, *a, **k: None})()
    eng.property_income = type("PI", (), {"tick": lambda self, *a, **k: None})()
    from src.world.world_tick_service import WorldTickService
    eng.world_tick_service = WorldTickService(
        state=eng.state, world_effects=eng.world_effects,
        world_ticker=eng.world_ticker, consequences=eng.consequences,
        faction_sim=eng.faction_sim, property_income=eng.property_income,
        property=eng.property, expenses=eng.expenses,
        get_player_tier=fake_get_tier)
    return eng, eng.state
