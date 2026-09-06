# -*- coding: utf-8 -*-
"""
Тесты выноса GameEngine.process_player_action → PlayerActionService
(Phase 30 шаг 3). Метод недетерминирован (LLM + random.randint), поэтому
применяем:

1. Mock self.ai с фиксированным текстом.
2. random.seed(SEED) в обоих путях.
3. Baseline = тело метода из git show af7d7c0:src/core/engine.py (ДО выноса
   PlayerActionService), извлечённое через AST и исполненное с тем же
   моком и тем же self.state.
4. Сравниваем 9 точек state + 4 ранних return (где ai.generate не вызывается).
5. world_events/consequences сравниваются ЦЕЛИКОМ (random.seed зафиксирован).
6. Дополнительные условия владельца:
   A. world_context — точное сравнение целиком.
   B. Тест на инвариант "сбой LLM = откат без частичных мутаций".
   C. Spy, фиксирующий ПОРЯДОК _world_tick → property_income.tick.
"""
import ast
import inspect
import random
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASELINE_COMMIT = "af7d7c0"
SERVICE_FILE = ROOT / "src" / "systems" / "player_action_service.py"


# ═══════════════════════════════════════════════════════════════
# Фикстуры
# ═══════════════════════════════════════════════════════════════

FIXTURE_AI_TEXT = (
    '[STATE]{"hp_change":-3,"credits_change":0,"stress_change":0,'
    '"humanity_change":0,"time_minutes":15,"xp_gained":10}[/STATE]\n\n'
    'Кинематографичная сцена в четыре абзаца. '
    'Сенсорные детали: неон, шум вентиляции, запах машинного масла. '
    'Фоновое действие: техники ремонтируют обшивку. '
    'Что будешь делать?\n'
    '1. [ХАКЕР] Подключиться к терминалу\n'
    '2. [УЛИЦА] Уйти через чёрный ход\n'
    '7. Свой вариант'
)
SEED = 3030


class FakeAI:
    def __init__(self, text=FIXTURE_AI_TEXT, fail=False):
        self.text = text
        self.fail = fail
        self.calls = 0

    def generate(self, **kw):
        self.calls += 1
        if self.fail:
            raise RuntimeError("LLM timeout (test mock)")
        return self.text


def _make_engine():
    """Свежий GameEngine с детерминированным персонажем."""
    from src.core.engine import GameEngine
    random.seed(SEED)
    eng = GameEngine()
    eng.create_custom_character({
        "name": "PactTest", "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER", "age": 25,
    })
    eng.state.faction_reputation["Earth UN"] = 5
    eng.state.faction_reputation["Star Helix"] = -2
    return eng


def _git_baseline_engine_source() -> str:
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:src/core/engine.py"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0
    return result.stdout


def _extract_method_body(source: str, method_name: str) -> str:
    tree = ast.parse(source)
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "GameEngine")
    method = next(n for n in cls.body
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and n.name == method_name)
    lines = source.splitlines(keepends=True)
    first = method.body[0]
    start = method.body[0].lineno - 1
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
            and isinstance(first.value.value, str):
        start = first.end_lineno
    return "".join(lines[start:method.end_lineno])


def _baseline_reference_for_engine(eng):
    """Собрать из git-блоба функцию, исполняемую с eng в качестве self.
    В baseline-теле есть СВОИ локальные импорты: from src.content.v4_legacy,
    import random. Эти имена при exec остаются в local namespace, поэтому
    НЕ инжектируются сюда. Но имена из глобальных импортов engine.py
    (ConversationManager, detect_subsystem_trigger, process_xp_gain и т.д.)
    — при exec не доступны; инжектируем их явно как глобальные."""
    body = _extract_method_body(_git_baseline_engine_source(), "process_player_action")
    wrapper = (
        "def _reference(self, action):\n"
        + _indent_body(body, 4)
    )
    from src.systems.mechanics import ConversationManager, detect_mechanical_action
    from src.systems.combat import (
        detect_subsystem_trigger, process_xp_gain, apply_defeat,
    )
    from src.content.v5_legacy import (
        calculate_auto_reputation, apply_reputation_changes, get_reputation_summary,
    )
    from src.systems.quests import get_available_chains
    import random as _random
    ns = {
        "random": _random,
        "ConversationManager": ConversationManager,
        "detect_subsystem_trigger": detect_subsystem_trigger,
        "detect_mechanical_action": detect_mechanical_action,
        "process_xp_gain": process_xp_gain,
        "apply_defeat": apply_defeat,
        "calculate_auto_reputation": calculate_auto_reputation,
        "apply_reputation_changes": apply_reputation_changes,
        "get_reputation_summary": get_reputation_summary,
        "get_available_chains": get_available_chains,
    }
    exec(compile(wrapper, "<baseline ppa>", "exec"), ns)
    return ns["_reference"].__get__(eng)


def _indent_body(body: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line
                     for line in body.split("\n"))


def _state_snapshot(eng) -> dict:
    """Срез state, не зависящий от AI-текста. 9 точек идентичности."""
    return {
        "conversation_history_len": len(eng.state.conversation_history),
        "conversation_history_user": eng.state.conversation_history[0]
            if eng.state.conversation_history else None,
        "game_time": dict(eng.state.game_time),
        "active_quests_len": len(eng.state.active_quests),
        "faction_reputation": dict(eng.state.faction_reputation),
        "world_context": deepcopy(eng.state.world_context),
        "character_xp": eng.state.character.get("xp"),
        "character_hp": eng.state.character.get("current_hp"),
        "last_karmic_roll": eng.state.last_karmic_roll,
    }


def _state_right_before_ai(eng) -> dict:
    """Срез state в точке, где стоит вызов ai.generate. Все мутации до LLM."""
    return {
        "conversation_history_len": len(eng.state.conversation_history),
        "active_quests_len": len(eng.state.active_quests),
        "faction_reputation": dict(eng.state.faction_reputation),
        "world_context": deepcopy(eng.state.world_context),
        "character_hp_before_ai": eng.state.character.get("current_hp"),
        "game_time": dict(eng.state.game_time),
        "character_xp_before_ai": eng.state.character.get("xp"),
    }


# ═══════════════════════════════════════════════════════════════
# 1. Сигнатура не изменилась (routes-контракт)
# ═══════════════════════════════════════════════════════════════

def test_process_player_action_signature_preserved():
    from src.core.engine import GameEngine
    sig = inspect.signature(GameEngine.process_player_action)
    assert [p.name for p in sig.parameters.values()] == ["self", "action"], \
        f"Сигнатура изменилась: {[p.name for p in sig.parameters.values()]}"


# ═══════════════════════════════════════════════════════════════
# 2. Идентичность: новый путь vs baseline-тело из git
# ═══════════════════════════════════════════════════════════════

def test_process_player_action_identical_to_baseline():
    """9 точек идентичности + world_context целиком, с одинаковым mock ai
    и одинаковым random.seed."""
    eng_new = _make_engine()
    eng_old = _make_engine()
    fake_new, fake_old = FakeAI(), FakeAI()
    eng_new.ai = fake_new
    eng_old.ai = fake_old

    # Прокидываем baseline-тело как метод на eng_old
    baseline_fn = _baseline_reference_for_engine(eng_old)

    random.seed(SEED)
    out_new = eng_new.process_player_action("осматриваюсь в баре")
    random.seed(SEED)
    out_old = baseline_fn("осматриваюсь в баре")

    snap_new = _state_snapshot(eng_new)
    snap_old = _state_snapshot(eng_old)

    # 9 точек
    for k in ("conversation_history_len", "conversation_history_user",
              "game_time", "active_quests_len", "faction_reputation",
              "character_xp", "character_hp", "last_karmic_roll"):
        assert snap_new[k] == snap_old[k], (
            f"Точка {k!r} разошлась: new={snap_new[k]!r} vs old={snap_old[k]!r}"
        )

    # world_context — ЦЕЛИКОМ (требование A владельца)
    assert snap_new["world_context"] == snap_old["world_context"], (
        f"world_context разошёлся. Только new: "
        f"{set(snap_new['world_context']) - set(snap_old['world_context'])}. "
        f"Только old: {set(snap_old['world_context']) - set(snap_new['world_context'])}."
    )

    # Возвращаемые структуры — помимо narrative, time_mins, AI-текста,
    # которые зависят от AI, остальные ключи должны совпадать по форме.
    for k in ("dice_results", "state_changes", "new_quest", "rep_changes",
              "chain_offer", "mechanical_action", "property_income",
              "defeat", "level_up", "subsystem"):
        assert (out_new.get(k) is None) == (out_old.get(k) is None), (
            f"Возврат {k!r}: None-ness разошёлся (new={out_new.get(k)} old={out_old.get(k)})"
        )

    # ai.generate вызван РОВНО ОДИН раз в обоих путях
    assert fake_new.calls == 1, f"New: ai.generate вызван {fake_new.calls} раз"
    assert fake_old.calls == 1, f"Old: ai.generate вызван {fake_old.calls} раз"


# ═══════════════════════════════════════════════════════════════
# 3. Доп. условие B: сбой LLM = откат без частичных мутаций
# ═══════════════════════════════════════════════════════════════

def test_llm_failure_rolls_back_post_ai_mutations():
    """Если self.ai бросает исключение, post-LLM мутации НЕ выполняются,
    pre-LLM мутации выполняются идентично в новом и baseline-путях."""
    eng_new = _make_engine()
    eng_old = _make_engine()
    eng_new.ai = FakeAI(fail=True)
    eng_old.ai = FakeAI(fail=True)
    baseline_fn = _baseline_reference_for_engine(eng_old)

    pre_new = _state_right_before_ai(eng_new)
    pre_old = _state_right_before_ai(eng_old)

    random.seed(SEED)
    with pytest.raises(RuntimeError, match="LLM timeout"):
        eng_new.process_player_action("осмотреться")
    random.seed(SEED)
    with pytest.raises(RuntimeError, match="LLM timeout"):
        baseline_fn("осмотреться")

    post_new = _state_snapshot(eng_new)
    post_old = _state_snapshot(eng_old)

    # conversation_history: только user-сообщение (1 запись, без assistant)
    assert post_new["conversation_history_len"] == 1, (
        f"post-LLM: assistant-запись добавилась (len={post_new['conversation_history_len']})"
    )
    assert post_old["conversation_history_len"] == 1

    # session_events: НЕ добавлен (тоже post-LLM)
    assert len(eng_new.state.session_events) == 0
    assert len(eng_old.state.session_events) == 0

    # game_time: НЕ продвинут (advance_time — post-LLM)
    assert post_new["game_time"] == pre_new["game_time"]
    assert post_old["game_time"] == pre_old["game_time"]

    # character.xp: НЕ добавлен (process_xp_gain — post-LLM)
    assert post_new["character_xp"] == pre_new["character_xp_before_ai"]
    assert post_old["character_xp"] == pre_old["character_xp_before_ai"]

    # character.current_hp: НЕ изменён через apply_defeat (post-LLM)
    # (HP-изменение через STATE-блок невозможно, т.к. _parse_ai_response не выполнен)
    assert post_new["character_hp"] == pre_new["character_hp_before_ai"]
    assert post_old["character_hp"] == pre_old["character_hp_before_ai"]

    # pre-LLM мутации идентичны в обоих путях
    assert post_new["active_quests_len"] == post_old["active_quests_len"]
    assert post_new["faction_reputation"] == post_old["faction_reputation"]
    assert post_new["world_context"] == post_old["world_context"]


# ═══════════════════════════════════════════════════════════════
# 4. Доп. условие C: порядок _world_tick → property_income.tick
# ═══════════════════════════════════════════════════════════════

def test_order_world_tick_before_property_income():
    """Spy с таймстампом индекса: world_tick_service.tick должен
    вызываться СТРОГО ДО property_income.tick в обоих путях."""
    eng_new = _make_engine()
    eng_old = _make_engine()
    eng_new.ai = FakeAI()
    eng_old.ai = FakeAI()
    baseline_fn = _baseline_reference_for_engine(eng_old)

    new_log = []
    old_log = []
    counter = [0]

    def _spy(log, orig, name):
        def wrapper(*a, **kw):
            counter[0] += 1
            log.append((name, counter[0]))
            return orig(*a, **kw)
        return wrapper

    orig_wt_new = eng_new.world_tick_service.tick
    orig_pi_new = eng_new.property_income.tick
    orig_wt_old = eng_old.world_tick_service.tick
    orig_pi_old = eng_old.property_income.tick
    eng_new.world_tick_service.tick = _spy(new_log, orig_wt_new, "world_tick")
    eng_new.property_income.tick = _spy(new_log, orig_pi_new, "property_income")
    eng_old.world_tick_service.tick = _spy(old_log, orig_wt_old, "world_tick")
    eng_old.property_income.tick = _spy(old_log, orig_pi_old, "property_income")

    random.seed(SEED)
    eng_new.process_player_action("осмотреться")
    random.seed(SEED)
    baseline_fn("осмотреться")

    new_seq = [name for name, _ in new_log]
    old_seq = [name for name, _ in old_log]

    assert "world_tick" in new_seq and "property_income" in new_seq
    assert "world_tick" in old_seq and "property_income" in old_seq

    assert new_seq.index("world_tick") < new_seq.index("property_income"), (
        f"New: world_tick не раньше property_income: {new_seq}"
    )
    assert old_seq.index("world_tick") < old_seq.index("property_income"), (
        f"Old: world_tick не раньше property_income: {old_seq}"
    )


# ═══════════════════════════════════════════════════════════════
# 5. Ранние return: combat/ability/subsystem-combat — ai.generate не вызывается
# ═══════════════════════════════════════════════════════════════

def test_early_return_combat_no_ai_call():
    """Если combat_engine.in_combat=True, _process_combat_turn вызывается, ai.generate — нет.
    Сервис захватил self._process_combat_turn в __init__ — подменяем
    на сервисе, не на движке."""
    eng = _make_engine()
    eng.ai = FakeAI()
    eng.combat_engine.combat = {"status": "active", "round": 1, "enemies": []}
    fake_combat = lambda action: {"narrative": "[БОЕВОЙ ХОД]", "from_combat": True}
    eng.player_action_service._process_combat_turn = fake_combat

    result = eng.process_player_action("атакую")

    assert result["from_combat"] is True
    assert eng.ai.calls == 0, f"ai.generate вызван {eng.ai.calls} раз при in_combat"


def test_early_return_ability_no_ai_call():
    """Если profession_abilities.detect вернул id, ai.generate — нет.
    Action НЕ должен триггерить detect_subsystem_trigger (hacking/investigation/crafting).
    Подменяем ability на сервисе, не на движке."""
    eng = _make_engine()
    eng.ai = FakeAI()

    class FakeAbilities:
        def detect(self, action): return "OVERRIDE_TEST"
        def execute(self, owner, aid, ctx):
            return {"text": "Ability executed", "not_applicable": False}

    eng.player_action_service.profession_abilities = FakeAbilities()

    result = eng.process_player_action("осмотреться")

    assert "ability_result" in result, (
        f"Ранний return через ability не сработал. result keys: {sorted(result.keys())}"
    )
    assert eng.ai.calls == 0, f"ai.generate вызван {eng.ai.calls} раз при ability"


def test_early_return_subsystem_combat_started_no_ai_call():
    """Если _handle_subsystem_trigger вернул combat_started=True, ai.generate — нет.
    Action должен триггерить detect_subsystem_trigger -> combat (COMBAT_KEYWORDS).
    Статический захват callback'ов: сервис захватил ссылку в __init__.
    Переопределяем на сервисе, не на движке (документированное поведение)."""
    eng = _make_engine()
    eng.ai = FakeAI()
    eng.player_action_service._handle_subsystem_trigger = lambda sub, act: {"combat_started": True, "narrative": "subs"}

    # "атаковать врага" -> detect_subsystem_trigger вернёт {"system": "combat"}
    # Прим.: патчим _handle_subsystem_trigger на СЕРВИСЕ, не на движке — это
    # документированное поведение статического захвата callback'ов (см. докстроку
    # PlayerActionService.__init__, Static capture note; ROADMAP Technical Debt).
    result = eng.process_player_action("атаковать врага")

    assert result.get("combat_started") is True, (
        f"Early return по combat_started не сработал. result: {result}"
    )
    assert eng.ai.calls == 0


# ═══════════════════════════════════════════════════════════════
# 6. Красная линия: src.server не импортируется
# ═══════════════════════════════════════════════════════════════

def test_service_does_not_import_server():
    source = SERVICE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
    offenders = [m for m in imported if m.startswith("src.server")]
    assert offenders == [], f"Сервис импортирует src.server: {offenders}"
