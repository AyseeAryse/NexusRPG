"""
Shared helpers for route blueprints.

Phase 24c B5-3 refactor: в app.py engine/app были модульными синглтонами.
Чтобы blueprints могли жить в отдельных файлах и не циркулировать импорты,
создан этот модуль-обёртка: get_engine() и get_app() возвращают runtime
синглтоны, инициализированные в app.py.

Паттерн: routes/*.py импортируют только `from src.server.routes._deps import get_engine, get_app`,
а сами синглтоны регистрируются из app.py при импорте routes-модулей.
"""
from typing import Any, Optional

_engine_ref: Any = None
_app_ref: Any = None


def set_engine(engine) -> None:
    """Установить ссылку на runtime engine singleton. Вызывается из app.py."""
    global _engine_ref
    _engine_ref = engine


def set_app(app) -> None:
    """Установить ссылку на runtime Flask app. Вызывается из app.py."""
    global _app_ref
    _app_ref = app


def get_engine():
    """Получить runtime engine singleton (lazy import fallback)."""
    if _engine_ref is None:
        # Fallback: импортируем напрямую из app (используется в тестах)
        from src.server import app as _app_module
        return _app_module.engine
    return _engine_ref


def get_app():
    """Получить runtime Flask app singleton."""
    if _app_ref is None:
        from src.server import app as _app_module
        return _app_module.app
    return _app_ref
