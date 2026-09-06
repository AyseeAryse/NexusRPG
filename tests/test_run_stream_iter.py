# -*- coding: utf-8 -*-
"""
Phase 31 Этап 1: тесты унификации оркестрации (run_stream_iter).

Ключевые гарантии:
1. run() == тонкий потребитель run_stream_iter(stream=False): идентичность
   state и результата с прямым вызовом.
2. Sync/stream идентичность pre/post-мутаций на одном моке AI.
3. Профспособности в стриме: ранний done без токенов, LLM не вызывается.
4. Порядок событий: done всегда последний; токены конкатенируются в ai_response.
5. Независимость фронт-обработчиков pre-событий (проверка кода app.js).
"""
import ast
import random
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SEED = 4141


class FakeAI:
    """Детерминированный мок: generate возвращает текст, generate_stream —
    тот же текст кусочками (равный конкатенации)."""
    TEXT = ('[STATE]{"hp_change":-2,"credits_change":0,"stress_change":0,'
            '"humanity_change":0,"time_minutes":15,"xp_gained":5}[/STATE]\n\n'
            'Сцена разворачивается. Неон дрожит.')

    def __init__(self):
        self.generate_calls = 0
        self.stream_calls = 0

    def generate(self, **kw):
        self.generate_calls += 1
        return self.TEXT

    def generate_stream(self, **kw):
        self.stream_calls += 1
        # 3 куска, конкатенация == TEXT
        yield self.TEXT[:20]
        yield self.TEXT[20:60]
        yield self.TEXT[60:]


def _make_engine():
    from src.core.engine import GameEngine
    random.seed(SEED)
    eng = GameEngine()
    eng.create_custom_character({
        "name": "Unify", "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER", "age": 25,
    })
    return eng


def _pair():
    """Два независимых движка с одинаковым seed."""
    eng_a = _make_engine()
    eng_b = _make_engine()
    a, b = FakeAI(), FakeAI()
    eng_a.ai = a
    eng_b.ai = b
    return eng_a, eng_b


def _state_snapshot(eng):
    return {
        "hp": eng.state.character.get("current_hp"),
        "xp": eng.state.character.get("xp"),
        "game_time": dict(eng.state.game_time),
        "conv_len": len(eng.state.conversation_history),
        "conv_last": eng.state.conversation_history[-1]["content"][:80] if eng.state.conversation_history else None,
        "session_events": len(eng.state.session_events),
        "world_context": deepcopy(eng.state.world_context),
        "active_quests": len(eng.state.active_quests),
        "last_karmic_roll": eng.state.last_karmic_roll,
    }


# ═══════════════════════════════════════════════════════════════
# 1. run() == потребитель run_stream_iter (sync)
# ═══════════════════════════════════════════════════════════════

def test_run_equals_stream_iter_sync_state():
    """run() и run_stream_iter(stream=False) мутируют state идентично."""
    eng_a, eng_b = _pair()
    random.seed(SEED)
    r_run = eng_a.process_player_action("осмотреться")
    random.seed(SEED)
    r_iter = None
    for kind, payload in eng_b.player_action_service.run_stream_iter("осмотреться", stream=False):
        if kind == "done":
            r_iter = payload
    snap_a, snap_b = _state_snapshot(eng_a), _state_snapshot(eng_b)
    for k in snap_a:
        assert snap_a[k] == snap_b[k], f"state[{k!r}] разошёлся: {snap_a[k]!r} vs {snap_b[k]!r}"
    # Результат тоже идентичен
    for k in ("narrative", "state_changes", "game_state", "rep_changes"):
        assert r_run[k] == r_iter[k], f"result[{k!r}] разошёлся"


def test_run_consumes_intermediate_tuples_silently():
    """run() не должен возвращать промежуточные кортежи наружу — только Dict."""
    eng = _make_engine()
    eng.ai = FakeAI()
    result = eng.process_player_action("осмотреться")
    assert isinstance(result, dict)
    assert "narrative" in result and "game_state" in result


# ═══════════════════════════════════════════════════════════════
# 2. Sync/stream идентичность мутаций + форма событий
# ═══════════════════════════════════════════════════════════════

def test_stream_and_sync_same_mutations():
    """Одинаковый seed: stream-путь (generate_stream) и sync (generate) —
    state после хода идентичен, включая world_context (random-зависимый)."""
    eng_a, eng_b = _pair()
    random.seed(SEED)
    for kind, payload in eng_a.player_action_service.run_stream_iter("хожу по рынку", stream=True):
        if kind == "done":
            done_stream = payload
    random.seed(SEED)
    done_sync = eng_b.process_player_action("хожу по рынку")

    sa, sb = _state_snapshot(eng_a), _state_snapshot(eng_b)
    for k in sa:
        assert sa[k] == sb[k], f"stream/sync state[{k!r}] разошёлся"


def test_stream_event_sequence_contract():
    """Контракт событий: done — ВСЕГДА последний; token-куски конкатенируются
    в текст, из которого сделан done.narrative (через общий _parse_ai_response)."""
    eng = _make_engine()
    fake = FakeAI()
    eng.ai = fake
    kinds = []
    tokens = []
    done = None
    for kind, payload in eng.player_action_service.run_stream_iter("иду в бар", stream=True):
        kinds.append(kind)
        if kind == "token":
            tokens.append(payload)
        elif kind == "done":
            done = payload
    assert kinds[-1] == "done", f"последнее событие {kinds[-1]!r}, не done"
    assert kinds.count("done") == 1
    assert tokens, "stream-режим должен давать токены"
    assert "".join(tokens) == fake.TEXT
    # done.narrative == нарратив из того же текста (парсер режет STATE-блок)
    assert "[STATE]" not in done["narrative"]
    assert "Сцена разворачивается." in done["narrative"]
    # generate_stream использован, generate — нет
    assert fake.stream_calls == 1 and fake.generate_calls == 0


def test_world_event_pre_event_when_news_present():
    """Контракт SSE: если тик мира дал news/rumors/economic_event — в поток уходит
    ("pre", {"type": "world_event", "data": wc}) ДО токенов (как в прежнем
    stream-пути routes L152-154). news форсируются на первом тике (turn_count==1)."""
    eng = _make_engine()
    fake = FakeAI()
    eng.ai = fake
    pre_types = []
    for kind, payload in eng.player_action_service.run_stream_iter("первый ход", stream=True):
        if kind == "pre":
            pre_types.append(payload["type"])
        elif kind == "done":
            break
    # Первый тик мира форс-генерирует news (turn_count == 1) — world_event обязан быть
    assert "world_event" in pre_types, (
        f"world_event не ушёл; pre-типы: {pre_types}"
    )


def test_sync_mode_yields_no_tokens():
    """sync-режим: нет token-событий (иначе SSE-адаптер /api/action слал бы фейк)."""
    eng = _make_engine()
    fake = FakeAI()
    eng.ai = fake
    kinds = [k for k, _ in eng.player_action_service.run_stream_iter("шаг", stream=False)]
    assert "token" not in kinds
    assert kinds[-1] == "done"
    assert fake.generate_calls == 1 and fake.stream_calls == 0


# ═══════════════════════════════════════════════════════════════
# 3. Профспособности в стриме (ранний done без токенов)
# ═══════════════════════════════════════════════════════════════

def test_ability_early_done_in_stream_no_tokens_no_llm():
    """Профспособность: в stream-режиме поток = единственный ("done", ...),
    generate_stream НЕ вызывается. Сценарий из уточнения 3 владельца."""
    eng = _make_engine()
    fake = FakeAI()
    eng.ai = fake

    class FakeAbilities:
        def detect(self, action): return "OVERRIDE_TEST"
        def execute(self, owner, aid, ctx):
            return {"text": "Способность применена мгновенно.", "not_applicable": False}

    eng.player_action_service.profession_abilities = FakeAbilities()

    events = list(eng.player_action_service.run_stream_iter("осмотреться", stream=True))
    kinds = [k for k, _ in events]
    assert kinds == ["done"], f"ожидался единственный done, получено: {kinds}"
    result = events[0][1]
    assert result["narrative"] == "Способность применена мгновенно."
    assert "ability_result" in result
    assert fake.stream_calls == 0 and fake.generate_calls == 0


def test_ability_early_done_stream_matches_sync():
    """Идентичность раннего выхода между режимами."""
    eng_a, eng_b = _pair()

    class FakeAbilities:
        def detect(self, action): return "OVERRIDE_TEST"
        def execute(self, owner, aid, ctx):
            return {"text": "Быстрый результат", "not_applicable": False}

    for eng in (eng_a, eng_b):
        eng.player_action_service.profession_abilities = FakeAbilities()

    events_a = list(eng_a.player_action_service.run_stream_iter("act", stream=True))
    r_sync = eng_b.process_player_action("act")
    assert [k for k, _ in events_a] == ["done"]
    assert events_a[0][1]["narrative"] == r_sync["narrative"] == "Быстрый результат"


# ═══════════════════════════════════════════════════════════════
# 4. Combat early-return в stream-режиме (done без токенов)
# ═══════════════════════════════════════════════════════════════

def test_combat_early_done_in_stream():
    eng = _make_engine()
    fake = FakeAI()
    eng.ai = fake
    eng.combat_engine.combat = {"status": "active", "round": 1, "enemies": []}
    eng.player_action_service._process_combat_turn = lambda action: {
        "narrative": "[БОЕВОЙ ХОД]", "from_combat": True}
    events = list(eng.player_action_service.run_stream_iter("атакую", stream=True))
    assert [k for k, _ in events] == ["done"]
    assert events[0][1]["from_combat"] is True
    assert fake.stream_calls == 0


# ═══════════════════════════════════════════════════════════════
# 5. Независимость фронт-обработчиков pre-событий (grep-проверка)
# ═══════════════════════════════════════════════════════════════

def test_frontend_handlers_order_independent():
    """Требование владельца: addDiceResult/showWorldEvent/handleMechanicalResult/
    handleSubsystemResult не должны иметь скрытой зависимости по порядку.
    Проверка по коду: каждый обработчик читает только свой payload и не пишет
    в общее состояние, которое читает другой."""
    js = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")

    handlers = {
        "addDiceResult": ("function addDiceResult", "function addDiceResult("),
        "showWorldEvent": ("function showWorldEvent", None),
        "handleMechanicalResult": ("function handleMechanicalResult", None),
        "handleSubsystemResult": ("function handleSubsystemResult", None),
    }

    def body_of(name):
        i = js.find(f"function {name}")
        assert i > 0, f"{name} не найден в app.js"
        j = js.find("\nfunction ", i + 5)
        return js[i:j if j > i else i + 2000]

    bodies = {name: body_of(name) for name in handlers}
    # Каждый обработчик не вызывает ни один из других
    for name, body in bodies.items():
        for other in handlers:
            if other != name:
                assert f"{other}(" not in body, (
                    f"{name} вызывает {other} — скрытая зависимость по порядку"
                )
    # Ни один не пишет в game_state / HUD-стейт, читаемый другим
    for name, body in bodies.items():
        assert "gameState =" not in body, f"{name} мутирует глобальный gameState"
    # Dice-обработчик работает с форматом DiceRoller-результата (dice-событие
    # приходит из _check_mechanical_action — тот же формат, что и раньше)


# ═══════════════════════════════════════════════════════════════
# 6. Адаптер routes: ранний done → jsonify, обычный ход → SSE
# ═══════════════════════════════════════════════════════════════

def test_adapter_source_pinns_contract():
    """Адаптер api_action_stream: источник содержит peek-паттерн (первый done
    без токенов → jsonify) и sse-обвязку. Фиксация контракта на уровне кода."""
    gp = (ROOT / "src" / "server" / "routes" / "gameplay.py").read_text(encoding="utf-8")
    i = gp.find('def api_action_stream')
    j = gp.find('@gameplay.route("/api/consequence/log"')
    src = gp[i:j if j > i else len(gp)]
    assert 'run_stream_iter(action, stream=True)' in src, "адаптер должен идти через сервис"
    assert 'next(it, None)' in src, "peek первого кортежа обязателен"
    assert 'mimetype="text/event-stream"' in src
    # Старая дублирующая оркестрация удалена
    for legacy in ('world_sim.tick', '_last_chain_offer_h = current_hours',
                   'property_income.tick(current_hours', 'generate_stream(\n'):
        assert legacy not in src, f"в адаптере остался кусок старой оркестрации: {legacy!r}"


def test_service_is_single_orchestration_source():
    """Сводная гарантия этапа 1: routes больше не содержит собственную копию
    pre/post-LLM шагов (тик мира, chain offer, quest gen, property income)."""
    gp = (ROOT / "src" / "server" / "routes" / "gameplay.py").read_text(encoding="utf-8")
    i = gp.find('def api_action_stream')
    j = gp.find('@gameplay.route("/api/consequence/log"')
    src = gp[i:j if j > i else len(gp)]
    for legacy in ('ConversationManager.manage_history',
                   'calculate_auto_reputation', 'get_available_chains',
                   'quest_generator.generate_quest', 'process_xp_gain', 'apply_defeat'):
        assert legacy not in src, f"дубль оркестрации остался в routes: {legacy!r}"
