# NexusRPG cleanup audit — 2026-08

## 1. Точка входа и рабочая кодовая ветка

`launcher.py` в dev-режиме вычисляет `server_path = os.path.join(game_dir, "server.py")`, проверяет наличие именно корневого `server.py`, затем запускает `subprocess.run([sys.executable, server_path], cwd=game_dir)`. В `.exe`-режиме он также загружает тот же корневой `server.py` через `importlib.util.spec_from_file_location("server", server_path)` и вызывает `server_module.app.run(...)`.

Итог: `launcher.py` запускает `server.py`, значит рабочая кодовая ветка для запуска игры — корень репозитория. Пакет `src/` содержит параллельную/модульную копию большей части логики и используется тестами/документацией, поэтому файлы `src/` не архивировались автоматически без ручного решения владельца проекта.

## 2. Файлы-зомби по статическому графу импортов

Статический AST-граф импортов был построен для `.py` файлов, кроме `tests/`, `archive/`, `_internal/`, `.git/`, `venv/`, `.venv/` и `__pycache__/`. Следующие файлы не импортируются другими production-файлами и не являются entrypoint-файлами:

| Файл | Статус | Решение |
|---|---|---|
| `setup.py` | зомби-кандидат | Требует ручной проверки: packaging entrypoint может использоваться внешними командами. |
| `src/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker, используется импортами `src.*` и тестами. |
| `src/ai/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker/export layer. |
| `src/ai/knowledge_base.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль корневого `knowledge_base.py`, но нужен `src`-ветке. |
| `src/config.py` | зомби-кандидат по AST | Требует ручной проверки: `src`-вариант отличается путями от корневого config. |
| `src/content/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker/export layer. |
| `src/content/base.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль `content_expansion.py`, но нужен `src.content`. |
| `src/content/creation_data.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль корневого `creation_data.py`. |
| `src/content/v2_legacy.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль `content_expansion_v2.py`. |
| `src/core/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker. |
| `src/server/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker. |
| `src/systems/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker/export layer. |
| `src/systems/game_systems.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль корневого `game_systems.py`, но нужен `src`-ветке. |
| `src/utils/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker. |
| `src/world/__init__.py` | зомби-кандидат по AST | Не архивировать: package marker/export layer. |
| `src/world/npc_registry.py` | зомби-кандидат по AST | Требует ручной проверки: 100% дубль корневого `npc_registry.py`, но нужен `src.world`. |

## 3. Таблица дубликатов Python-кода

| Корневой файл | Файл в `src/` | Совпадение | Группа | Решение |
|---|---:|---:|---|---|
| `world_sim.py` | `src/world/simulation.py` | 100.0% | идентичны | Требует ручной проверки: корень используется launcher/server, `src` используется тестами. |
| `subsystems.py` | `src/systems/subsystems.py` | 100.0% | идентичны | Требует ручной проверки. |
| `server.py` | `src/server/app.py` | 100.0% | идентичны | Не архивировать автоматически: `server.py` — entrypoint, `src/server/app.py` — документированная модульная копия. |
| `quest_chains.py` | `src/systems/quests.py` | 100.0% | идентичны | Требует ручной проверки. |
| `procedural_engine.py` | `src/world/procedural.py` | 100.0% | идентичны | Требует ручной проверки. |
| `npc_registry.py` | `src/world/npc_registry.py` | 100.0% | идентичны | Требует ручной проверки. |
| `mechanics.py` | `src/systems/mechanics.py` | 100.0% | идентичны | Требует ручной проверки. |
| `knowledge_base.py` | `src/ai/knowledge_base.py` | 100.0% | идентичны | Требует ручной проверки. |
| `game_systems.py` | `src/systems/game_systems.py` | 100.0% | идентичны | Требует ручной проверки. |
| `galaxy_map.py` | `src/world/galaxy.py` | 100.0% | идентичны | Требует ручной проверки. |
| `creation_data.py` | `src/content/creation_data.py` | 100.0% | идентичны | Требует ручной проверки. |
| `content_expansion_v5.py` | `src/content/v5_legacy.py` | 100.0% | идентичны | Требует ручной проверки. |
| `content_expansion_v4.py` | `src/content/v4_legacy.py` | 100.0% | идентичны | Требует ручной проверки. |
| `content_expansion_v3.py` | `src/content/v3_legacy.py` | 100.0% | идентичны | Требует ручной проверки. |
| `content_expansion_v2.py` | `src/content/v2_legacy.py` | 100.0% | идентичны | Требует ручной проверки. |
| `content_expansion.py` | `src/content/base.py` | 100.0% | идентичны | Требует ручной проверки. |
| `companions.py` | `src/systems/companions.py` | 100.0% | идентичны | Требует ручной проверки. |
| `combat_engine.py` | `src/systems/combat.py` | 100.0% | идентичны | Требует ручной проверки. |
| `ai_connector.py` | `src/ai/connector.py` | 99.5% | почти-дубликат | Отличие: импорт config (`import config` vs `from src import config`). Не архивировать без решения о целевой ветке кода. |
| `game_engine.py` | `src/core/engine.py` | 99.1% | почти-дубликат | Отличия: только import-пути root-модулей vs `src.*`; в root есть compat import `get_all_shop_items`. Не архивировать без решения о целевой ветке кода. |
| `config.py` | `src/config.py` | 90.6% | почти-дубликат | Отличия: `src/config.py` вычисляет `PROJECT_ROOT`, root config использует `os.path.dirname(__file__)`. Не архивировать без решения о целевой ветке кода. |

## 4. Аудит JSON в `game_data/`

Реально используемый при запуске `KnowledgeBase` — корневой `knowledge_base.py`, потому что рабочий `server.py` импортирует корневой `game_engine.py`, а он импортирует `KnowledgeBase` из корневого `knowledge_base.py`.

`KnowledgeBase._load_all()` загружает только JSON-файлы первого уровня `game_data/`, группирует их по базовому имени, затем выбирает один файл из каждой группы через `PREFERRED_FILES` или version/size score. На момент аудита: 101 JSON-файл первого уровня, 80 загруженных, 21 пропущенный как дубликаты версий.

Файлы, пропущенные `KnowledgeBase` и перемещённые в архив как неиспользуемые версионные дубли:

| Файл | Реально загружаемый/предпочтённый вариант |
|---|---|
| `03_MEGA_DIALOGUE_SOCIAL_SYSTEM_COMPLETE.json` | другой файл группы `DIALOGUE/SOCIAL` выбран KB; файл не попал в `kb.files`. |
| `06_MEGA_ECONOMY_CRAFTING_COMPLETE.json` | другой файл группы `ECONOMY/CRAFTING` выбран KB; файл не попал в `kb.files`. |
| `10_MEGA_PLAYER_INTERFACE_COMPLETE.json` | `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `10_MEGA_PLAYER_INTERFACE_ENHANCED.json` | `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `12_MEGA_NARRATIVE_INTERFACE_COMPLETE.json` | `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`. |
| `AI_RPG_CORE.json` | `AI_RPG_CORE_V2_ENHANCED.json`. |
| `AUTOMATION.json` | `AUTOMATION_V2_COMPREHENSIVE.json`. |
| `ENHANCED_EVENT_GENERATOR.json` | `ENHANCED_EVENT_GENERATOR_V2.json`. |
| `GM_TOOLKIT.json` | `GM_TOOLKIT_V2_COMPREHENSIVE.json`. |
| `HACKING.json` | `HACKING_V2_QUANTUM_AGE.json`. |
| `INVESTIGATION.json` | `INVESTIGATION_V2_GALACTIC_DETECTIVE.json`. |
| `MECHANICS.json` | `MECHANICS_V2_INTEGRATED_SYSTEMS.json`. |
| `MODIFICATION.json` | `MODIFICATION_V2_QUANTUM_BIOTECH.json`. |
| `NARRATIVE_INTERFACE.json` | `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`. |
| `PLAYER_INTERFACE.json` | `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `PLAYER_INTERFACE_V2.json` | `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `PROGRESSION_V2.json` | `PROGRESSION.json` по explicit preference. |
| `THEME_TONE.json` | `THEME_TONE_V2_ADDITIONS.json` выбран KB; файл не попал в `kb.files`. |
| `WORLD_SIM.json` | `WORLD_SIM_V2_LIVING_UNIVERSE.json`. |

Файлы `CHARACTER_LIFEPATH_V3_MASSIVE_PART1.json` и `STARTING_QUESTS.json` также не попали в `kb.files`, но не архивировались: первый напрямую читается `content_expansion_v4.py`, второй используется как fallback в `game_engine.py`.

## 5. Итоговая сводная таблица

| Файл | Статус | Куда переместить | Обоснование |
|---|---|---|---|
| `_internal/**` | PyInstaller artifact | `archive/_internal_pyinstaller_artifact/**` | Содержит `.dll`, `.pyd`, bundled dist-info и runtime-файлы; не является исходным кодом. |
| `game_data/03_MEGA_DIALOGUE_SOCIAL_SYSTEM_COMPLETE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/03_MEGA_DIALOGUE_SOCIAL_SYSTEM_COMPLETE.json` | Не выбран `KnowledgeBase` при resolve conflicts. |
| `game_data/06_MEGA_ECONOMY_CRAFTING_COMPLETE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/06_MEGA_ECONOMY_CRAFTING_COMPLETE.json` | Не выбран `KnowledgeBase` при resolve conflicts. |
| `game_data/10_MEGA_PLAYER_INTERFACE_COMPLETE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/10_MEGA_PLAYER_INTERFACE_COMPLETE.json` | Вместо него выбран `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `game_data/10_MEGA_PLAYER_INTERFACE_ENHANCED.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/10_MEGA_PLAYER_INTERFACE_ENHANCED.json` | Вместо него выбран `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `game_data/12_MEGA_NARRATIVE_INTERFACE_COMPLETE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/12_MEGA_NARRATIVE_INTERFACE_COMPLETE.json` | Вместо него выбран `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`. |
| `game_data/AI_RPG_CORE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/AI_RPG_CORE.json` | Вместо него выбран `AI_RPG_CORE_V2_ENHANCED.json`. |
| `game_data/AUTOMATION.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/AUTOMATION.json` | Вместо него выбран `AUTOMATION_V2_COMPREHENSIVE.json`. |
| `game_data/ENHANCED_EVENT_GENERATOR.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/ENHANCED_EVENT_GENERATOR.json` | Вместо него выбран `ENHANCED_EVENT_GENERATOR_V2.json`. |
| `game_data/GM_TOOLKIT.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/GM_TOOLKIT.json` | Вместо него выбран `GM_TOOLKIT_V2_COMPREHENSIVE.json`. |
| `game_data/HACKING.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/HACKING.json` | Вместо него выбран `HACKING_V2_QUANTUM_AGE.json`. |
| `game_data/INVESTIGATION.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/INVESTIGATION.json` | Вместо него выбран `INVESTIGATION_V2_GALACTIC_DETECTIVE.json`. |
| `game_data/MECHANICS.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/MECHANICS.json` | Вместо него выбран `MECHANICS_V2_INTEGRATED_SYSTEMS.json`; кодовые упоминания — комментарии/docstrings. |
| `game_data/MODIFICATION.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/MODIFICATION.json` | Вместо него выбран `MODIFICATION_V2_QUANTUM_BIOTECH.json`. |
| `game_data/NARRATIVE_INTERFACE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/NARRATIVE_INTERFACE.json` | Вместо него выбран `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`. |
| `game_data/PLAYER_INTERFACE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/PLAYER_INTERFACE.json` | Вместо него выбран `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `game_data/PLAYER_INTERFACE_V2.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/PLAYER_INTERFACE_V2.json` | Вместо него выбран `PLAYER_INTERFACE_V2_ENHANCED.json`. |
| `game_data/PROGRESSION_V2.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/PROGRESSION_V2.json` | Explicit preference выбирает `PROGRESSION.json`. |
| `game_data/THEME_TONE.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/THEME_TONE.json` | Не выбран `KnowledgeBase`; упоминания остаются только в метаданных/описаниях JSON. |
| `game_data/WORLD_SIM.json` | неиспользуемый JSON | `archive/game_data_unused_by_kb/WORLD_SIM.json` | Вместо него выбран `WORLD_SIM_V2_LIVING_UNIVERSE.json`. |

## 6. Требует ручной проверки

- Дубли `root` vs `src/`: почти вся логика продублирована. Корневая ветка является рабочей для launcher/server, но `src/` используется тестами и документацией. Архивировать одну сторону без решения о целевой архитектуре рискованно.
- `CHARACTER_LIFEPATH_V3_MASSIVE_PART1.json`: не выбран `KnowledgeBase`, но напрямую читается `content_expansion_v4.py`, поэтому оставлен на месте.
- `STARTING_QUESTS.json`: не выбран `KnowledgeBase`, но используется `game_engine.py` как fallback после `STARTING_QUESTS_COMPLETE.json`, поэтому оставлен на месте.
- `game_data/archive/*.json`: уже находятся в архивной папке и не трогались.
