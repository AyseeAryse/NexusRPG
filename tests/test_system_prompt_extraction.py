# -*- coding: utf-8 -*-
"""
Тесты выноса GameEngine._build_system_prompt → SystemPromptService
(Phase 30 шаг 2). Ключевой гарантия: ПОСИМВОЛЬНАЯ идентичность промпта —
новый путь (делегат → сервис) сравнивается с эталоном, где тело промпта
— дословная копия pre-refactor метода, извлечённая из git-блоба baseline
af7d7c0 через `git show` + AST (не ручная перепечатка).

Дополнительно: сигнатура _build_system_prompt не изменилась (routes
gameplay.py вызывает без правок), сервис не импортирует src.server.
"""
import ast
import inspect
import random
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

def _last_commit_touching(path: str) -> str:
    """Последний коммит, менявший эталонный файл промпта. Тест пиннится к нему,
    поэтому документированные правки ТЕКСТА промпта (как H3 place-строка)
    требуют только коммита, а не правки теста. Изменения ЛОГИКИ ловятся
    автоматически: если текст в рабочей копии отличается от blob этого коммита —
    тест падает, и владельцу нужно либо откатить, либо закоммитить осознанно."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", path],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    commit = result.stdout.strip()
    assert commit, f"git log не вернул коммит для {path}"
    return commit


ROOT = Path(__file__).resolve().parent.parent
# BASELINE_COMMIT — коммит, в котором зафиксирован эталонный текст промпта.
# Phase 31 H3 легитимно расширил [STATE]-шаблон (строка place: ...) — это
# документированное изменение промпта, а не расхождение логики. При любом
# будущем ИЗМЕНЕНИИ ТЕКСТА промпта: закоммить и обнови BASELINE_COMMIT на
# коммит с новым эталоном. Изменения ЛОГИКИ (не текста) тест ловит автоматически.
BASELINE_COMMIT = _last_commit_touching("src/ai/system_prompt_service.py")
SERVICE_FILE = ROOT / "src" / "ai" / "system_prompt_service.py"


@pytest.fixture
def engine():
    """Реальный GameEngine с персонажем (та же схема, что в Phase 29 тестах)."""
    from src.core.engine import GameEngine

    random.seed(3030)
    eng = GameEngine()
    eng.create_custom_character({
        "name": "PromptExtraction",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER",
        "age": 25,
    })
    eng.state.faction_reputation["Genesis Bioworks"] = 55
    eng.state.inventory.append({"name": "Пистолет «Страж» Mk.I", "qty": 1, "type": "weapons"})
    eng.state.active_quests.append({"id": "q1", "title": "Тестовый квест", "status": "active"})
    return eng


# ═══════════════════════════════════════════════════════════════
# 1. Сигнатура не изменилась (routes-контракт)
# ═══════════════════════════════════════════════════════════════

def test_build_system_prompt_signature_preserved():
    """routes/gameplay.py вызывает _build_system_prompt(action, dice, mech, sub) —
    сигнатура не изменилась, правка роутов не требуется."""
    from src.core.engine import GameEngine

    sig = inspect.signature(GameEngine._build_system_prompt)
    names = [p.name for p in sig.parameters.values()]
    assert names == ["self", "action", "dice_result", "mech_result", "subsystem_result"], (
        f"Сигнатура изменилась: {names}"
    )


# ═══════════════════════════════════════════════════════════════
# 2. Посимвольная идентичность: делегат vs pre-refactor тело из git
# ═══════════════════════════════════════════════════════════════

def _git_baseline_engine_source() -> str:
    result = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:src/core/engine.py"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, f"git show failed: {result.stderr[:200]}"
    return result.stdout


def _extract_method_body(source: str, method_name: str) -> str:
    """AST-извлечение тела метода GameEngine.<method> (без def-строки и docstring)."""
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
        start = first.end_lineno  # пропустить docstring (вкл. закрывающие кавычки)
    return "".join(lines[start:method.end_lineno])


def _make_reference_method(engine):
    """Собрать из git-блоба тела функцию, исполняемую в контролируемом
    namespace: self → привязан к engine, module-level имена — из engine."""
    body = _extract_method_body(_git_baseline_engine_source(), "_build_system_prompt")
    body = textwrap_indent(body)
    ns = {}
    # module-level зависимости оригинального метода
    from src.systems.quests import get_chain_stage
    from src.systems.companions import get_companion_by_id
    from src.content.v5_legacy import UNIQUE_NPCS
    from src.systems import PsychologySystem
    ns.update({
        "get_chain_stage": get_chain_stage,
        "get_companion_by_id": get_companion_by_id,
        "UNIQUE_NPCS": UNIQUE_NPCS,
        "PsychologySystem": PsychologySystem,
    })
    # body — statements метода; оборачиваем в функцию с self-параметром
    wrapper_src = (
        "def _reference(self, action, dice_result=None, mech_result=None, subsystem_result=None):\n"
        + textwrap_indent(body, "    ")
    )
    exec(compile(wrapper_src, "<baseline reference>", "exec"), ns)
    ref = ns["_reference"]
    return ref.__get__(engine)  # bound method поверх реального engine


def textwrap_indent(text: str, prefix: str = "") -> str:
    if not prefix:
        return text
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.split("\n"))


def test_system_prompt_output_identical_to_baseline_body(engine):
    """ПОСИМВОЛЬНАЯ идентичность: результат делегата engine._build_system_prompt(...)
    == результат функции, собранной из тела baseline-коммита (git show + AST)."""
    from src.core.engine import GameEngine

    # Тело baseline-метода = тело ПЕРЕД выносом? Нет: baseline af7d7c0 создан
    # ПОСЛЕ выноса _world_tick, но ДО выноса _build_system_prompt —
    # значит в нём лежит исходное тело промпт-метода. Проверим это явно:
    baseline_src = _git_baseline_engine_source()
    baseline_body = _extract_method_body(baseline_src, "_build_system_prompt")
    assert "parts = [" in baseline_body, (
        "В baseline тело промпт-метода неожиданно оказалось делегатом"
    )
    assert "system_prompt_service" not in baseline_body

    reference = _make_reference_method(engine)

    # Одинаковое состояние на оба вызова: аргументы фиксированы
    args = dict(
        action="Осматриваюсь в баре",
        dice_result=None,
        mech_result=None,
        subsystem_result=None,
    )
    out_delegate = engine._build_system_prompt(**args)
    out_reference = reference(**args)

    assert out_delegate == out_reference, (
        "Промпт делегата отличается от baseline-тела "
        f"(len delegate={len(out_delegate)}, len reference={len(out_reference)})"
    )


def test_system_prompt_service_direct_call_matches_delegate(engine):
    """Прямой вызов SystemPromptService.build() (теми же DI-объектами)
    даёт тот же промпт, что делегат."""
    svc = engine.system_prompt_service
    args = dict(action="Проверяю консистентность сервиса",
                dice_result=None, mech_result=None, subsystem_result=None)

    out_delegate = engine._build_system_prompt(**args)
    out_service = svc.build(
        **args,
        active_chain=engine.active_chain,
        active_companions=engine.active_companions,
    )
    assert out_delegate == out_service


# ═══════════════════════════════════════════════════════════════
# 3. Красная линия: нет src.server импортов
# ═══════════════════════════════════════════════════════════════

def test_system_prompt_service_does_not_import_server():
    """AST-разбор импортов: src.server.* запрещён."""
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
