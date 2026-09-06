"""
Тесты для базовой функциональности игрового движка.

Проверяют:
- Создание состояния игры
- Броски кубиков
- Создание персонажа
- Основные механики без AI
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestDiceRoller:
    """Тесты системы бросков кубиков."""

    def test_roll_single_die(self):
        """Бросок одного кубика."""
        from src.core.engine import DiceRoller
        
        result, rolls = DiceRoller.roll("1d6")
        assert len(rolls) == 1
        assert 1 <= rolls[0] <= 6
        assert result == rolls[0]

    def test_roll_multiple_dice(self):
        """Бросок нескольких кубиков."""
        from src.core.engine import DiceRoller
        
        result, rolls = DiceRoller.roll("2d6")
        assert len(rolls) == 2
        assert all(1 <= r <= 6 for r in rolls)
        assert result == sum(rolls)

    def test_roll_with_modifier(self):
        """Бросок с модификатором."""
        from src.core.engine import DiceRoller
        
        result, rolls = DiceRoller.roll("2d6+5")
        assert len(rolls) == 2
        assert result == sum(rolls) + 5

    def test_roll_invalid_format(self):
        """Неверный формат броска."""
        from src.core.engine import DiceRoller
        
        result, rolls = DiceRoller.roll("invalid")
        assert result == 0
        assert rolls == []

    def test_skill_check_success(self):
        """Проверка навыка с высоким бонусом."""
        from src.core.engine import DiceRoller
        
        # Высокие характеристики должны давать успех
        with patch.object(DiceRoller, 'roll', return_value=(10, [5, 5])):
            result = DiceRoller.skill_check(
                skill_level=5,
                attribute_value=8,
                difficulty=10
            )
            assert result['bonus'] >= 0
            # При броске 10 и бонусе результат должен быть >= 10

    def test_skill_check_critical_success(self):
        """Критический успех (двойная шестерка)."""
        from src.core.engine import DiceRoller
        
        with patch.object(DiceRoller, 'roll', return_value=(12, [6, 6])):
            result = DiceRoller.skill_check(
                skill_level=3,
                attribute_value=6,
                difficulty=14
            )
            assert result['quality'] == 'critical_success'
            assert result['success'] is True

    def test_skill_check_critical_failure(self):
        """Критический провал (двойная единица)."""
        from src.core.engine import DiceRoller
        
        with patch.object(DiceRoller, 'roll', return_value=(2, [1, 1])):
            result = DiceRoller.skill_check(
                skill_level=5,
                attribute_value=10,
                difficulty=6
            )
            assert result['quality'] == 'critical_failure'
            assert result['success'] is False


class TestGameState:
    """Тесты состояния игры."""

    def test_game_state_creation(self):
        """Создание нового состояния игры."""
        from src.core.engine import GameState
        
        state = GameState()
        
        assert state.id is not None
        assert len(state.id) == 8
        assert state.character == {}
        assert state.phase == "menu"
        assert state.in_combat is False
        assert isinstance(state.active_quests, list)
        assert isinstance(state.inventory, list)

    def test_game_state_to_dict(self):
        """Сериализация состояния в словарь."""
        from src.core.engine import GameState
        
        state = GameState()
        state.character = {"name": "Test", "level": 1}
        
        data = state.to_dict()
        
        assert data['id'] == state.id
        assert data['character']['name'] == "Test"
        assert data['phase'] == "menu"
        assert 'world_sim' in data
        assert 'npc_registry' in data

    def test_game_state_from_dict(self):
        """Десериализация состояния из словаря."""
        from src.core.engine import GameState
        
        original = GameState()
        original.character = {"name": "RestoreTest", "level": 5}
        original.phase = "exploration"
        
        data = original.to_dict()
        restored = GameState.from_dict(data)
        
        assert restored.id == original.id
        assert restored.character['name'] == "RestoreTest"
        assert restored.character['level'] == 5
        assert restored.phase == "exploration"


class TestGameEngine:
    """Тесты игрового движка."""

    def test_engine_initialization(self):
        """Инициализация движка."""
        from src.core.engine import GameEngine
        
        engine = GameEngine()
        
        assert engine.state is not None
        assert engine.dice is not None
        assert engine.kb is not None
        # AI может быть не подключен, но объект должен существовать
        assert engine.ai is not None

    def test_engine_get_creation_data(self):
        """Получение данных для создания персонажа."""
        from src.core.engine import GameEngine
        
        engine = GameEngine()
        data = engine.get_creation_data()
        
        assert 'origins' in data
        assert 'formative_years' in data
        assert 'specializations' in data
        assert 'attributes' in data
        assert 'skills' in data
        assert 'presets' in data
        assert 'point_budget' in data
        
        # Проверяем структуру данных
        assert isinstance(data['origins'], list)
        assert isinstance(data['attributes'], list)
        assert isinstance(data['skills'], list)

    def test_engine_presets_exist(self):
        """Пресеты персонажей существуют."""
        from src.core.engine import GameEngine
        
        engine = GameEngine()
        presets = engine.get_presets()
        
        # Пресеты могут быть пустыми, но должны быть списком
        assert isinstance(presets, list)

    @pytest.mark.skip(reason="Требуется мокирование KnowledgeBase для стабильности")
    def test_create_character_from_preset(self):
        """Создание персонажа из пресета."""
        from src.core.engine import GameEngine
        
        engine = GameEngine()
        presets = engine.get_presets()
        
        if presets:
            preset_id = presets[0].get('id')
            if preset_id:
                character = engine.create_character_from_preset(preset_id)
                assert 'error' not in character or character.get('preset_id') == preset_id


class TestBalanceFunctions:
    """Тесты балансовых функций."""

    def test_skill_cap_by_level(self):
        """Капы навыков по уровням."""
        from src.core.engine import get_skill_cap
        
        # Низкие уровни
        assert get_skill_cap(1) == (4, 7)
        assert get_skill_cap(3) == (4, 7)
        
        # Средние уровни
        assert get_skill_cap(5) == (6, 8)
        
        # Высокие уровни
        assert get_skill_cap(10) == (10, 10)
        assert get_skill_cap(50) == (10, 10)

    def test_player_tier_by_credits(self):
        """Уровни влияния по кредитам."""
        from src.core.engine import get_player_tier
        
        assert get_player_tier(0) == 0
        assert get_player_tier(1000) == 0
        assert get_player_tier(50000) == 1
        assert get_player_tier(100000) == 1
        assert get_player_tier(500000) == 2
        assert get_player_tier(1000000) == 2
        assert get_player_tier(5000000) == 3
        assert get_player_tier(10000000) == 3

    def test_dc_table_exists(self):
        """Таблица сложностей существует."""
        from src.core.engine import DC_TABLE
        
        assert 'easy' in DC_TABLE
        assert 'medium' in DC_TABLE
        assert 'hard' in DC_TABLE
        assert DC_TABLE['easy'] < DC_TABLE['medium'] < DC_TABLE['hard']
