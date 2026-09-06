# -*- coding: utf-8 -*-
"""
tests/test_world_tick_extraction.py — Phase 30 шаг 1: вынос _world_tick.

Доказывает идентичность поведения до и после переноса:
  1. Делегат engine._world_tick() сохраняет сигнатуру () -> Dict.
  2. Делегат реально идёт через WorldTickService.tick().
  3. Побитовое сравнение: путь A (делегат) vs путь B (дословная копия
     pre-refactor тела _world_tick) на deep-copy state с одинаковым seed.
  4. Красная линия: world_tick_service не импортирует src.server.*

Тесты работают с реальным движком и реальными подсистемами.
"""
import ast
import importlib
import inspect
import random
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

SERVICE_PATH = ROOT / "src" / "world" / "world_tick_service.py"


@pytest.fixture
def engine_a():
    """Движок пути A (делегат). Seed фиксирован до создания."""
    from src.core.engine import GameEngine

    random.seed(4242)
    engine = GameEngine()
    engine.create_custom_character({
        "name": "TickExtraction",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER",
        "age": 25,
    })
    # Гарантируем ветку backlog#5: rep>=40 у фракции
    engine.state.faction_reputation["Genesis Bioworks"] = 55
    return engine


@pytest.fixture
def state_before_a(engine_a):
    """Deepcopy state ДО тика — точка отсчёта обоих путей."""
    return deepcopy(engine_a.state)


# ═══════════════════════════════════════════════════════════════
# 1. Сигнатура и делегирование
# ═══════════════════════════════════════════════════════════════

def test_world_tick_signature_preserved():
    """Сигнатура _world_tick() в API GameEngine не изменилась:
    без аргументов (кроме self), возвращает Dict."""
    from src.core.engine import GameEngine

    sig = inspect.signature(GameEngine._world_tick)
    params = [p.name for p in sig.parameters.values() if p.name != "self"]
    assert params == [], f"У _world_tick появились аргументы: {params}"
    ann = sig.return_annotation
    ann_name = getattr(ann, "__name__", None) or str(ann)
    assert "Dict" in ann_name or "dict" in ann_name, (
        f"Аннотация возврата изменилась: {ann_name}"
    )


def test_delegate_uses_service(engine_a):
    """engine._world_tick() делегирует в WorldTickService.tick()."""
    from src.world.world_tick_service import WorldTickService

    assert isinstance(engine_a.world_tick_service, WorldTickService)

    calls = {"n": 0}
    orig = engine_a.world_tick_service.tick

    def counting_tick():
        calls["n"] += 1
        return orig()

    engine_a.world_tick_service.tick = counting_tick
    random.seed(4242)
    engine_a._world_tick()
    assert calls["n"] == 1, "_world_tick не делегирует в сервис"


# ═══════════════════════════════════════════════════════════════
# 2. Побитовая идентичность с pre-refactor логикой
# ═══════════════════════════════════════════════════════════════

def _legacy_world_tick(engine):
    """Дословная копия тела GameEngine._world_tick ДО выноса
    (engine.py@Phase29, строки 2239-2316). Эталон старого поведения."""
    tier = engine.get_player_influence_tier()["tier"]
    engine.state.world_sim.world_effects_ref = engine.world_effects
    engine.state.world_sim._last_game_time = dict(engine.state.game_time)
    notable = [name for name, rep in engine.state.faction_reputation.items()
               if isinstance(rep, (int, float)) and rep >= 40]
    wc = engine.state.world_sim.tick(
        engine.state.game_time, engine.state.current_location, tier,
        notable_factions=notable,
        character=engine.state.character
    )
    mentioned = wc.pop("news_mention", None)
    if mentioned:
        from src.world.player_tiers import FAME_PER_NEWS_MENTION
        engine.state.fame = getattr(engine.state, "fame", 0) + FAME_PER_NEWS_MENTION
        wc["news_mention"] = {"faction": mentioned,
                              "fame_gained": FAME_PER_NEWS_MENTION}

    world_events = engine.world_ticker.tick(engine.state)
    if world_events:
        wc["world_events"] = world_events
        from src.content.v4_legacy import _game_time_to_hours
        current_h = _game_time_to_hours(engine.state.game_time)
        for we in world_events:
            engine.world_effects.apply_event_effects(we, current_h)

    turn = engine.state.world_sim.turn_count
    triggered_consequences = engine.consequences.check_consequences(turn)
    if triggered_consequences:
        wc["consequences"] = triggered_consequences

    tier_for_conflict = engine.get_player_influence_tier().get("tier", 0)
    conflict_events = engine.faction_sim.tick(
        player_tier=tier_for_conflict,
        current_location=engine.state.current_location,
    )
    if conflict_events:
        wc["conflict_events"] = conflict_events
        total_delta = sum(e.get("price_modifier_delta", 0) for e in conflict_events)
        if total_delta > 0:
            engine.state.world_sim.price_modifier = min(
                1.5, engine.state.world_sim.price_modifier + total_delta
            )
        total_heat = sum(e.get("heat_delta", 0) for e in conflict_events)
        if total_heat > 0:
            engine.state.character["heat"] = engine.state.character.get("heat", 0) + total_heat
        engine.state.world_context["local_event"] = engine.faction_sim.get_last_event_summary()
    else:
        engine.state.world_context.pop("local_event", None)

    try:
        from src.content.v4_legacy import _game_time_to_hours as _gth
        current_hours = _gth(engine.state.game_time)
        income_result = engine.property_income.tick(current_hours, engine.property,
                                                    engine.state.character)
        if income_result:
            wc["property_income"] = income_result
        tier_n = engine.get_player_influence_tier()["tier"]
        expense_record = engine.expenses.tick(current_hours, engine.property,
                                              getattr(engine, "ship", None),
                                              engine.state.character, tier_n)
        if expense_record:
            wc["expenses"] = expense_record
    except Exception:
        pass
    return wc


def test_service_tick_output_identical_to_legacy(engine_a, state_before_a):
    """Путь A: WorldTickService.tick() (новый код) на engine_a.
    Путь B: _legacy_world_tick (дословный pre-refactor) на deep-copy state.
    Один seed на каждый путь → результат и мутированное state идентичны."""
    # Снимки симуляторов ДО пути A (иначе cooldown/throttling после тика A
    # переносится в путь B и ветки wc расходятся)
    sim_before = {
        k: deepcopy(getattr(engine_a, k))
        for k in ("world_effects", "world_ticker", "consequences",
                  "faction_sim", "property_income", "property", "expenses")
    }
    # ── Путь A: новый сервис ──
    random.seed(9001)
    wc_a = engine_a.world_tick_service.tick()
    state_a = deepcopy(engine_a.state)

    # ── Путь B: старая логика на копии исходного state ──
    from src.core.engine import GameEngine
    engine_b = GameEngine.__new__(GameEngine)
    # Инъекция: state — независимая копия, симуляторы — их deep-copy СОСТОЯНИЯ
    # на момент до тика (иначе throttling/cooldown/turn_count переносятся из пути A
    # и путь B теряет ветки conflict_events/world_events/expenses)
    engine_b.state = deepcopy(state_before_a)
    for k, snap in sim_before.items():
        setattr(engine_b, k, deepcopy(snap))
    engine_b.get_player_influence_tier = engine_a.get_player_influence_tier

    random.seed(9001)
    wc_b = _legacy_world_tick(engine_b)
    state_b = deepcopy(engine_b.state)

    # Ключи wc совпадают
    assert set(wc_a.keys()) == set(wc_b.keys()), (
        f"Набор ключей wc различается: A={sorted(wc_a)}, B={sorted(wc_b)}"
    )
    # Категориальные поля (детерминированы при одинаковом seed)
    for key in ("news_mention", "world_events", "consequences",
                "conflict_events", "property_income", "expenses"):
        assert wc_a.get(key) == wc_b.get(key), f"wc[{key}] расходится"

    # Мутированное состояние
    assert state_a.fame == state_b.fame, "fame разошёлся"
    assert state_a.character.get("heat") == state_b.character.get("heat")
    assert state_a.world_sim.price_modifier == state_b.world_sim.price_modifier
    assert state_a.world_sim.turn_count == state_b.world_sim.turn_count
    assert state_a.world_context.get("local_event") == state_b.world_context.get("local_event")
    assert state_a.faction_reputation == state_b.faction_reputation
    # game_time тик не двигает (это делает _advance_time, не tick) — но у обоих путей должно совпасть
    assert state_a.game_time == state_b.game_time


def test_delegate_returns_service_result_verbatim(engine_a):
    """Делегат возвращает РОВНО то, что вернул WorldTickService.tick() —
    не фильтрует, не дополняет, не пересобирает результат."""
    sentinel = {"atmosphere": "x", "news": [], "rumors": [], "sentinel": True}
    captured = {}

    def fake_tick():
        captured.update(sentinel)
        return sentinel

    engine_a.world_tick_service.tick = fake_tick
    result = engine_a._world_tick()
    assert result is sentinel, "Делегат пересобрал/скопировал результат сервиса"
    assert captured == sentinel


# ═══════════════════════════════════════════════════════════════
# 4. Красная линия: нет импортов src.server
# ═══════════════════════════════════════════════════════════════

def test_world_tick_service_does_not_import_server():
    """Красная линия: core/systems никогда не импортируют server.
    Статический AST-разбор импортов модуля (docstring не считается)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)

    offenders = [m for m in imported_modules if m.startswith("src.server")]
    assert offenders == [], (
        f"world_tick_service импортирует src.server: {offenders}"
    )
    # И в строках модуля не должно быть from src.server импортов в рантайме
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(source, node) or ""
            assert "src.server" not in seg
