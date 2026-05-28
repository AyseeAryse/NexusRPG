# 📝 Руководство по созданию контента

Это руководство поможет вам добавить новый контент в NexusRPG: персонажей, предметы, квесты, локации и многое другое.

---

## 📋 Оглавление

1. [Структура данных](#структура-данных)
2. [Добавление происхождения (Origin)](#добавление-происхождения)
3. [Добавление перков](#добавление-перков)
4. [Добавление предметов](#добавление-предметов)
5. [Добавление NPC](#добавление-npc)
6. [Добавление квестов](#добавление-квестов)
7. [Тестирование контента](#тестирование-контента)

---

## Структура данных

### Вариант A: Python-модули (рекомендуется для логики)

Файлы в `src/content/`:

```python
# src/content/origins.py
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Origin:
    id: str
    name: str
    description: str
    bonuses: Dict[str, int]
    skills: List[str]
    starting_items: List[str]

ORIGINS: List[Origin] = [
    Origin(
        id="techno_priest",
        name="Техно-жрец",
        description="Служитель машин из храма Марса",
        bonuses={"intelligence": 2, "wisdom": 1},
        skills=["tech_use", "lore_machine"],
        starting_items=["mechadendrite", "blessed_toolkit"]
    ),
    # ... другие истоки
]
```

### Вариант B: JSON-файлы (рекомендуется для данных)

Файлы в `game_data/active/`:

```json
{
  "id": "plasma_rifle",
  "name": "Плазменная винтовка",
  "type": "weapon",
  "damage": "3d8+energy",
  "range": "long",
  "price": 500,
  "requirements": {
    "strength": 12,
    "tech_skill": 3
  }
}
```

---

## Добавление происхождения (Origin)

### Шаг 1: Создайте файл

```python
# src/content/origins.py (или добавьте в существующий)
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Origin:
    id: str
    name: str
    description: str
    bonuses: Dict[str, int]
    skills: List[str]
    starting_items: List[str]
    formative_events: List[str] = field(default_factory=list)
```

### Шаг 2: Добавьте новое происхождение

```python
NEW_ORIGIN = Origin(
    id="void_nomad",
    name="Кочевник Пустоты",
    description="""
        Рождённый в глубинах космоса, вы никогда не ступали на планету.
        Корабль — ваш дом, звёзды — ваша семья.
    """,
    bonuses={
        "dexterity": 1,
        "constitution": 1,
        "charisma": -1
    },
    skills=[
        "zero_g_movement",
        "ship_maintenance",
        "navigation"
    ],
    starting_items=[
        "vacuum_suit",
        "magnetic_boots",
        "ration_pack"
    ],
    formative_events=[
        "first_spacewalk",
        "asteroid_mining",
        "alien_contact"
    ]
)

# Добавьте в список
ORIGINS.append(NEW_ORIGIN)
```

### Шаг 3: Обновите `__init__.py`

```python
# src/content/__init__.py
from .origins import ORIGINS, Origin

__all__ = ['ORIGINS', 'Origin']
```

---

## Добавление перков

### Структура перка

```python
# src/content/perks.py
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class Perk:
    id: str
    name: str
    description: str
    requirements: dict
    effect: Callable  # Функция эффекта
    tier: int = 1  # 1=basic, 2=advanced, 3=master

def calculate_damage_bonus(character, amount):
    """Пример эффекта перка"""
    return amount * 1.5

SHARP_SHOOTER = Perk(
    id="sharp_shooter",
    name="Меткий стрелок",
    description="+50% урона от критических попаданий",
    requirements={
        "dexterity": 14,
        "skills": ["ranged_weapons"]
    },
    effect=calculate_damage_bonus,
    tier=2
)
```

---

## Добавление предметов

### Через JSON (рекомендуется)

```json
{
  "_comment": "game_data/active/items_new.json",
  "items": [
    {
      "id": "quantum_blade",
      "name": "Квантовый клинок",
      "type": "melee_weapon",
      "rarity": "legendary",
      "damage": "4d6+energy",
      "properties": [
        "ignores_armor",
        "phase_shift"
      ],
      "description": "Клинок из нестабильной материи",
      "price": 2500,
      "requirements": {
        "strength": 16,
        "tech_level": 4
      }
    }
  ]
}
```

### Загрузка предметов

```python
# В game_engine.py или отдельном модуле
import json

def load_items_from_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('items', [])

ALL_ITEMS = load_items_from_json('game_data/active/items_new.json')
```

---

## Добавление NPC

### Уникальные NPC

```python
# src/content/npcs.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class NPC:
    id: str
    name: str
    role: str
    location: str
    personality: str
    dialogue_tree: str
    quests_given: List[str]
    faction: Optional[str] = None
    is_unique: bool = True

CAPTAIN_VALEX = NPC(
    id="captain_valex",
    name="Капитан Валекс",
    role="quest_giver",
    location="station_alpha",
    personality="gruff_but_fair",
    dialogue_tree="valex_dialogue.json",
    quests_given=["first_mission", "smuggler_hunt"],
    faction="system_defense_force",
    is_unique=True
)

UNIQUE_NPCS.append(CAPTAIN_VALEX)
```

---

## Добавление квестов

### Структура квеста

```python
# src/systems/quests.py
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

class QuestState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QuestStage:
    id: str
    description: str
    objectives: List[dict]
    rewards: dict

@dataclass
class Quest:
    id: str
    name: str
    description: str
    giver_npc: str
    stages: List[QuestStage]
    prerequisites: List[str] = field(default_factory=list)
    faction_required: Optional[str] = None

FIRST_CONTACT = Quest(
    id="first_contact",
    name="Первый контакт",
    description="Установите связь с неизвестной цивилизацией",
    giver_npc="captain_valex",
    stages=[
        QuestStage(
            id="stage_1",
            description="Исследуйте аномалию",
            objectives=[
                {"type": "travel", "location": "anomaly_sector"},
                {"type": "scan", "target": "unknown_signal"}
            ],
            rewards={"xp": 500, "credits": 1000}
        ),
        QuestStage(
            id="stage_2",
            description="Вступите в контакт",
            objectives=[
                {"type": "dialogue", "choices": ["peaceful", "aggressive"]},
                {"type": "skill_check", "skill": "xeno_linguistics", "dc": 15}
            ],
            rewards={"xp": 1000, "reputation": {"alien_race": 50}}
        )
    ]
)

QUEST_CHAINS.append(FIRST_CONTACT)
```

---

## Тестирование контента

### 1. Проверка загрузки

```bash
python -c "from src.content import ORIGINS; print(len(ORIGINS))"
python -c "from src.content import UNIQUE_NPCS; print(len(UNIQUE_NPCS))"
```

### 2. Юнит-тесты

```python
# tests/test_content.py
import pytest
from src.content.origins import ORIGINS

def test_all_origins_have_required_fields():
    for origin in ORIGINS:
        assert origin.id is not None
        assert origin.name is not None
        assert len(origin.description) > 0
        assert isinstance(origin.bonuses, dict)

def test_no_duplicate_origin_ids():
    ids = [o.id for o in ORIGINS]
    assert len(ids) == len(set(ids)), "Duplicate origin IDs found"
```

### 3. Интеграционный тест

```python
# tests/test_integration.py
def test_character_creation_with_new_origin(client):
    response = client.post('/api/character/create', json={
        'name': 'Test',
        'origin': 'void_nomad'  # Новый исток
    })
    assert response.status_code == 200
```

---

## Советы по балансу

### Бонусы характеристик
| Сумма бонусов | Рекомендуемый уровень |
|---------------|----------------------|
| +1/-1 | Базовый исток |
| +2/0 | Продвинутый исток |
| +3/-1 | Специализированный |
| +4/-2 | Экспертный (редко) |

### Цены предметов
| Редкость | Диапазон цен | Уровень |
|----------|-------------|---------|
| Common | 10-100 | 1-3 |
| Uncommon | 100-500 | 4-7 |
| Rare | 500-2000 | 8-12 |
| Legendary | 2000+ | 13+ |

### Наград за квесты
| Тип квеста | XP | Кредиты | Репутация |
|------------|-----|---------|-----------|
| Side quest | 100-300 | 50-200 | 5-15 |
| Main quest | 500-1000 | 500-2000 | 20-50 |
| Epic quest | 2000+ | 5000+ | 100+ |

---

## Чеклист перед коммитом

- [ ] Все ID уникальны
- [ ] Нет дублирующихся названий
- [ ] Требования перков достижимы
- [ ] Баланс цен соответствует гайдам
- [ ] Тексты проверены на опечатки
- [ ] Добавлены тесты (если применимо)
- [ ] Контент загружается без ошибок

---

<div align="center">

**Готово?** Создайте Pull Request с вашим контентом!

Нужна помощь? См. [ARCHITECTURE.md](ARCHITECTURE.md) или откройте [Issue](https://github.com/AyseeAryse/NexusRPG/issues).

</div>
