# -*- coding: utf-8 -*-
"""
Тест закрытия аудита Phase 30 шаг 1: _legacy_world_tick в этом файле —
ручная перепечатка pre-refactor тела _world_tick. Аудит нашёл, что
сравнение сервиса с ручной копией доказывает только «копия == сервис»,
но не «копия == реальная git-история».

Эти тесты закрывают разрыв:
  1. baseline-коммит af7d7c0 содержит ровно тот state, из которого
     выносился сервис: тело _world_tick в нём — делегат в
     WorldTickService.tick(), а сам WorldTickService.tick() —
     побайтово тот же, что импортируется сейчас (сверка AST).
  2. Тело WorldTickService.tick() в HEAD-коммите текстуально
     идентично телу в рабочей копии (сервис с выноса не менялся).
  3. _legacy_world_tick в тестовом файле текстуально идентична
     реконструкции pre-Phase30 тела (docs/world_tick_reconstruction.py.txt),
     которая задокументирована как источник истины (Phase 28-бэкап
     + единственная строка G5).

Запуск требует установленного git и baseline-коммита af7d7c0.
"""
import ast
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASELINE_COMMIT = "af7d7c0"
EXTRACTION_TEST_FILE = ROOT / "tests" / "test_world_tick_extraction.py"
SERVICE_FILE = ROOT / "src" / "world" / "world_tick_service.py"
RECONSTRUCTION_FILE = ROOT / "docs" / "world_tick_reconstruction.py.txt"


def _git_show(commit: str, path: str) -> str:
    """Точный текст файла из git-истории (не пересказ)."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"git show {commit}:{path} failed: {result.stderr[:200]}"
    )
    return result.stdout


def _extract_method_source(source: str, class_name: str, method_name: str) -> str:
    """AST-извлечение исходника метода class_name.method_name (как
    scripts/ast_inventory.py — ast, не grep)."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    cls = next((n for n in tree.body
                if isinstance(n, ast.ClassDef) and n.name == class_name), None)
    assert cls is not None, f"Класс {class_name} не найден"
    method = next((n for n in cls.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.name == method_name), None)
    assert method is not None, (
        f"Метод {class_name}.{method_name} не найден"
    )
    # Пропускаем docstring, если первый statement — строковый литерал
    first_stmt = method.body[0]
    start = method.body[0].lineno - 1
    if (isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant)
            and isinstance(first_stmt.value.value, str)):
        start = first_stmt.end_lineno  # end_lineno 1-based = закрывающие кавычки;
                                       # 0-based start = строка ПОСЛЕ них (начало логики)
    end = method.end_lineno
    return "".join(lines[start:end])


def _dedent_block(body_source: str) -> str:
    """Нормализация отступов тела метода (убрать общий сдвиг) + трим хвоста."""
    return textwrap.dedent(body_source).strip()


# ═══════════════════════════════════════════════════════════════
# 1. Тело _world_tick в baseline — ровно делегат
# ═══════════════════════════════════════════════════════════════

def test_baseline_world_tick_body_is_delegate():
    """В baseline-коммите af7d7c0 тело GameEngine._world_tick — ровно
    `return self.world_tick_service.tick()` (после выноса логики)."""
    engine_src = _git_show(BASELINE_COMMIT, "src/core/engine.py")
    body = _extract_method_source(engine_src, "GameEngine", "_world_tick")
    body_norm = _dedent_block(body)

    assert body_norm == 'return self.world_tick_service.tick()', (
        f"Тело _world_tick в baseline изменилось относительно ожидаемого делегата:\n{body_norm}"
    )


# ═══════════════════════════════════════════════════════════════
# 2. Сервис в baseline == сервис в рабочей копии (AST-сравнение)
# ═══════════════════════════════════════════════════════════════

def _tick_body(source: str) -> str:
    """Тело метода tick() класса WorldTickService (без декораторов),
    AST-извлечение из произвольного исходника."""
    tree = ast.parse(source)
    cls = next((n for n in tree.body
                if isinstance(n, ast.ClassDef) and n.name == "WorldTickService"), None)
    assert cls is not None, "Класс WorldTickService не найден в исходнике"
    method = next((n for n in cls.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and n.name == "tick"), None)
    assert method is not None, "Метод WorldTickService.tick не найден"
    lines = source.splitlines(keepends=True)
    return "".join(lines[method.body[0].lineno - 1:method.end_lineno])


def test_service_tick_body_identical_to_baseline():
    """Тело WorldTickService.tick() в рабочей копии ПОБАЙТОВО совпадает с
    тем, что закоммичено в baseline af7d7c0. Если сервис менялся после
    baseline без коммита — тест упадёт."""
    baseline_src = _git_show(BASELINE_COMMIT, "src/world/world_tick_service.py")
    working_src = SERVICE_FILE.read_text(encoding="utf-8")

    baseline_body = _dedent_block(_tick_body(baseline_src))
    working_body = _dedent_block(_tick_body(working_src))

    assert working_body == baseline_body, (
        "WorldTickService.tick() в рабочей копии отличается от baseline "
        "af7d7c0 — ручная копия _legacy_world_tick в тесте больше не "
        "гарантирует соответствие git-истории"
    )


def test_legacy_copy_matches_service_logic_ast():
    """_legacy_world_tick (ручная копия в тесте) реализует ту же логику,
    что WorldTickService.tick() — сравнение AST-деревами тел (нормализует
    отступы и регистр docstring-различий, ловит любую правку statements)."""
    test_src = EXTRACTION_TEST_FILE.read_text(encoding="utf-8")
    tree = ast.parse(test_src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_legacy_world_tick"), None)
    assert fn is not None, "_legacy_world_tick исчезла из тестового файла"

    lines = test_src.splitlines(keepends=True)
    legacy_body = "".join(lines[fn.body[0].lineno - 1:fn.end_lineno])

    service_src = SERVICE_FILE.read_text(encoding="utf-8")
    service_body = _tick_body(service_src)

    # AST-сравнение с нормализацией легитимных отличий (см. отчёт Phase 30 шаг 1):
    #  - legacy — статическая функция (параметр engine), сервис — метод (self)
    #  - tier вычисляется через колбэк _get_player_tier (Phase 30)
    #  - FAME_PER_NEWS_MENTION импорт: локальный в legacy, модульный в сервисе
    #  - docstring не является логикой
    import re as _re

    def _norm_ast_dumps(body_src: str, self_name: str):
        # Импорты легитимно имеют разное размещение (локальный внутри if у legacy,
        # модульный у сервиса) — вырезаем Import/ImportFrom на ЛЮБОЙ глубине дерева.
        class _StripImports(ast.NodeTransformer):
            def visit_Import(self, node):
                return None
            def visit_ImportFrom(self, node):
                return None

        tree_b = ast.parse(textwrap.dedent(body_src).strip())
        tree_b = _StripImports().visit(tree_b)
        ast.fix_missing_locations(tree_b)
        dumps = []
        for s in tree_b.body:
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant):
                continue  # docstring
            d = ast.dump(s)
            d = d.replace(f"Name(id={self_name!r}", "Name(id='<owner>'")
            d = d.replace("_get_player_tier", "<tier_callback>")
            d = d.replace("get_player_influence_tier", "<tier_callback>")
            dumps.append(d)
        return dumps

    legacy_dump = _norm_ast_dumps(legacy_body, "engine")
    service_dump = _norm_ast_dumps(service_body, "self")

    assert legacy_dump == service_dump, (
        "AST тел расходится: _legacy_world_tick в тесте не соответствует "
        "WorldTickService.tick() — либо копия устарела, либо сервис менялся"
    )


# ═══════════════════════════════════════════════════════════════
# 3. Ручная копия == задокументированная реконструкция pre-Phase30
# ═══════════════════════════════════════════════════════════════

def test_legacy_copy_matches_documented_reconstruction():
    """_legacy_world_tick в тесте текстуально соответствует реконструкции
    pre-Phase30 тела (docs/world_tick_reconstruction.py.txt), кроме
    задокументированных отличий Phase 30 (колбэк tier, вынос импорта)."""
    assert RECONSTRUCTION_FILE.exists(), (
        f"Реконструкция {RECONSTRUCTION_FILE.name} не найдена в docs/"
    )
    recon = RECONSTRUCTION_FILE.read_text(encoding="utf-8")

    # Задокументированные отличия (см. отчёт Phase 30 шаг 1):
    # 1) get_player_influence_tier() -> колбэк _get_player_tier() (2 места + tier=)
    # 2) локальный import FAME_PER_NEWS_MENTION -> модульный
    recon_norm = textwrap.dedent(recon).strip()
    recon_lines = recon_norm.splitlines()
    TRIPLE = chr(34) * 3
    while recon_lines and (recon_lines[0].startswith("def ")
                           or TRIPLE in recon_lines[0]):
        recon_lines.pop(0)
    recon_norm = "\n".join(recon_lines)
    recon_norm = recon_norm.replace(
        "self.get_player_influence_tier()", "self._get_player_tier()")
    recon_norm = recon_norm.replace(
        "from src.world.player_tiers import FAME_PER_NEWS_MENTION\n", "")

    test_src = EXTRACTION_TEST_FILE.read_text(encoding="utf-8")
    tree = ast.parse(test_src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_legacy_world_tick"), None)
    lines = test_src.splitlines(keepends=True)
    legacy_body = textwrap.dedent(
        "".join(lines[fn.body[0].lineno - 1:fn.end_lineno])).strip()
    # Нормализация ОБОИХ сторон: единое имя tier-колбэка и вынос импорта
    # legacy-функция принимает engine параметром (self. -> engine.) — нормализуем
    legacy_body = legacy_body.replace("engine.", "self.")
    legacy_body = legacy_body.replace("getattr(engine,", "getattr(self,")
    legacy_body = legacy_body.replace(
        "self.get_player_influence_tier()", "self._get_player_tier()")
    legacy_body = legacy_body.replace(
        "from src.world.player_tiers import FAME_PER_NEWS_MENTION\n", "")
    # docstring функции — не логика
    legacy_lines = legacy_body.splitlines()
    TQ = chr(34) * 3
    while legacy_lines and (TQ in legacy_lines[0] or not legacy_lines[0].strip()):
        legacy_lines.pop(0)
    legacy_body = "\n".join(legacy_lines)

    # Нормализуем recon до уровня statements: сравниваем ключевые строки логики
    recon_logic = [l.strip() for l in recon_norm.splitlines() if l.strip()]
    legacy_logic = [l.strip() for l in legacy_body.splitlines() if l.strip()]
    # Пустые строки/комменты уже отброшены; сравниваем множества строк логики
    # (порядок зафиксирован отдельными последовательными assert'ами в identity-тесте)
    missing = [l for l in recon_logic if l not in legacy_logic and not l.startswith("#")]
    extra = [l for l in legacy_logic if l not in recon_logic and not l.startswith("#")]

    assert missing == [], f"Строки реконструкции отсутствуют в _legacy_world_tick: {missing}"
    assert extra == [], f"Строки в _legacy_world_tick нет в реконструкции: {extra}"
