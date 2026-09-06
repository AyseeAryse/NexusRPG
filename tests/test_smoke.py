"""
Smoke-тесты для основных модулей NexusRPG.

Проверяют, что все ключевые модули импортируются без ошибок.
Не требуют AI-бэкенда или внешних зависимостей.
"""

import pytest


class TestImports:
    """Тесты на импорт основных модулей."""

    def test_import_src(self):
        """Основной пакет src импортируется."""
        import src
        assert hasattr(src, '__version__')

    def test_import_config(self):
        """Модуль конфигурации импортируется."""
        from src import config
        assert hasattr(config, 'AI_BACKEND')
        assert hasattr(config, 'GAME_DATA_DIR')

    def test_import_ai_connector(self):
        """AIConnector импортируется."""
        from src.ai import AIConnector
        assert AIConnector is not None

    def test_import_knowledge_base(self):
        """KnowledgeBase импортируется."""
        from src.ai import KnowledgeBase
        assert KnowledgeBase is not None

    def test_import_game_engine(self):
        """GameEngine и GameState импортируются."""
        from src.core.engine import GameEngine, GameState, DiceRoller
        assert GameEngine is not None
        assert GameState is not None
        assert DiceRoller is not None

    def test_import_combat(self):
        """Боевая система импортируется."""
        from src.systems import CombatEngine
        assert CombatEngine is not None

    def test_import_world(self):
        """Модули мира импортируются."""
        from src.world import GalaxyMap, WorldSimulator, NPCRegistry
        assert GalaxyMap is not None
        assert WorldSimulator is not None
        assert NPCRegistry is not None

    def test_import_systems(self):
        """Игровые системы импортируются."""
        from src.systems import (
            QuestTracker, FactionSystem, PsychologySystem,
            PerkSystem, LevelUpSystem, CraftingSystem
        )
        assert QuestTracker is not None
        assert FactionSystem is not None

    def test_import_content(self):
        """Контентные данные импортируются."""
        from src.content import ORIGINS, FORMATIVE_YEARS, SPECIALIZATIONS
        assert isinstance(ORIGINS, list)
        assert isinstance(FORMATIVE_YEARS, list)
        assert isinstance(SPECIALIZATIONS, list)


class TestConfig:
    """Тесты конфигурации."""

    def test_config_defaults(self):
        """Конфигурация имеет значения по умолчанию."""
        from src import config
        
        # Проверяем основные настройки
        assert hasattr(config, 'DEBUG')
        assert isinstance(config.DEBUG, bool)
        
        # Проверяем пути
        assert hasattr(config, 'GAME_DATA_DIR')
        assert hasattr(config, 'SAVES_DIR')
        
    def test_config_no_api_keys(self):
        """API ключи не захардкожены в конфиге."""
        from src import config
        
        # Убеждаемся, что ключи пустые или берутся из env
        api_key = getattr(config, 'CLOUD_API_KEY', '')
        assert api_key == '' or api_key.startswith('${')
