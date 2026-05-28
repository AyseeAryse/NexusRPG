# 🧪 Тестирование NexusRPG

## Запуск тестов

### Базовый запуск
```bash
pip install pytest
python -m pytest tests/ -v
```

### С покрытием кода
```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

Отчёт откроется в `htmlcov/index.html`.

---

## Существующие тесты

| Файл | Описание | Статус |
|------|----------|--------|
| `tests/test_combat.py` | Тесты боевой системы | 🟡 В разработке |
| `tests/test_generation.py` | Тесты генерации контента | 🟡 В разработке |

---

## Написание новых тестов

### Структура теста

```python
# tests/test_example.py
import pytest
from src.core.engine import GameState, DiceRoller

class TestDiceRoller:
    def test_roll_d20_returns_value_between_1_and_20(self):
        roller = DiceRoller()
        result = roller.roll("1d20")
        assert 1 <= result <= 20
    
    def test_roll_with_modifier(self):
        roller = DiceRoller()
        result = roller.roll("1d20+5")
        assert 6 <= result <= 25
```

### Запуск конкретного теста
```bash
pytest tests/test_example.py::TestDiceRoller::test_roll_d20_returns_value_between_1_and_20 -v
```

---

## Моки для AI-бэкендов

Для тестов без реальных API вызовов используйте моки:

```python
# tests/test_ai.py
import pytest
from unittest.mock import Mock, patch
from src.ai.connector import AIConnector

@patch('src.ai.connector.requests.post')
def test_ai_connector_ollama(mock_post):
    # Настройка мока
    mock_response = Mock()
    mock_response.json.return_value = {'response': 'Hello!'}
    mock_post.return_value = mock_response
    
    connector = AIConnector(backend='ollama')
    result = connector.generate("test prompt", [])
    
    assert result == 'Hello!'
    mock_post.assert_called_once()
```

---

## Интеграционные тесты

Для тестирования полного цикла используйте тестовый клиент Flask:

```python
# tests/test_integration.py
import pytest
from src.server.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_character_creation(client):
    response = client.post('/api/character/create', json={
        'name': 'Test Character',
        'origin': 'techno_priest'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'character_id' in data
```

---

## CI/CD (GitHub Actions)

Пример workflow для автоматического тестирования:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=src
```

---

## Отладка тестов

### Режим отладки
```bash
pytest tests/ -v -s  # Показать print выводы
pytest tests/ --pdb  # Остановиться при ошибке
```

### Логирование в тестах
```python
import logging

def test_with_logging(caplog):
    caplog.set_level(logging.INFO)
    # ... код теста
    assert "Expected log message" in caplog.text
```

---

## Покрытие кода

### Минимальные требования
- Core модули: >80%
- Systems: >70%
- AI connector: >90%
- Server routes: >60%

### Проверка покрытия
```bash
pytest tests/ --cov=src --cov-fail-under=70
```

---

## Производительность тестов

### Запуск бенчмарков
```bash
pip install pytest-benchmark
pytest tests/ --benchmark-only
```

### Профилирование
```bash
pytest tests/ --profile-svg=profile.svg
```

---

<div align="center">

**Документация находится в разработке.** Помоги улучшить тесты — создай [Pull Request](https://github.com/AyseeAryse/NexusRPG/pulls)!

</div>
