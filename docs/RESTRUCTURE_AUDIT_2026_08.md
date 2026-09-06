# NexusRPG restructure audit — 2026-08

## Preparation notes

- Requested branch: `restructure-2026-08`.
- `git fetch origin main` could not be completed in this environment because the GitHub remote requires credentials. The branch was created from the local pre-cleanup base commit `8375eff`, which is the parent of the previous cleanup commit available in local history.
- Previous audit was read from local commit `b6ad470:docs/REPO_CLEANUP_AUDIT_2026_08.md` because the file is not present on the local base commit.
- Existing `archive/` contents were not used as a source for new decisions; new moves go to `archive/legacy_dupes_2026_08/`.

## Entry point decision

`launcher.py` used to start root `server.py`. This restructure switches the launcher to start `src.server.app` instead, while keeping `launcher.py` as the root entry point. The Flask app in `src/server/app.py` now uses absolute template/static paths based on the project root, so it works when run as a module under `src`.

## Two-check inventory method

For each moved file, at least two checks were used:

1. Static/diff check: AST/import scan and root-vs-`src` duplicate similarity check.
2. Text/dynamic check: `rg` over code/templates/static/tests plus KnowledgeBase loader analysis for JSON groups.
3. Runtime gate after moves: `compileall`, `KnowledgeBase` load-count check, `pytest`, and root route HTTP check.

## Python duplicate consolidation

Runtime imports were switched to `src` modules before archiving 100% identical root copies. Near-duplicates were not merged.

| File | Status | Action | Where | Evidence / two checks |
|---|---|---|---|---|
| `server.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/server.py` | Same as `src/server/app.py`; launcher now starts `src.server.app`, grep no remaining runtime import. |
| `combat_engine.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/combat_engine.py` | Same as `src/systems/combat.py`; all imports changed to `src.systems.combat`. |
| `companions.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/companions.py` | Same as `src/systems/companions.py`; imports changed to `src.systems.companions`. |
| `content_expansion.py` | 100% duplicate/legacy root copy | archived | `archive/legacy_dupes_2026_08/content_expansion.py` | Same as `src/content/base.py`; imports changed to `src.content.base`. |
| `content_expansion_v2.py` | 100% duplicate/legacy root copy | archived | `archive/legacy_dupes_2026_08/content_expansion_v2.py` | Same as `src/content/v2_legacy.py`; imports changed to `src.content.v2_legacy`. |
| `content_expansion_v3.py` | 100% duplicate/legacy root copy | archived | `archive/legacy_dupes_2026_08/content_expansion_v3.py` | Same as `src/content/v3_legacy.py`; imports changed to `src.content.v3_legacy`. |
| `content_expansion_v4.py` | 100% duplicate/current content loader root copy | archived | `archive/legacy_dupes_2026_08/content_expansion_v4.py` | Same as `src/content/v4_legacy.py`; direct JSON reads now remain in `src/content/v4_legacy.py`. |
| `content_expansion_v5.py` | 100% duplicate/current content loader root copy | archived | `archive/legacy_dupes_2026_08/content_expansion_v5.py` | Same as `src/content/v5_legacy.py`; imports changed to `src.content.v5_legacy`. |
| `creation_data.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/creation_data.py` | Same as `src/content/creation_data.py`; imports changed to `src.content.creation_data`. |
| `galaxy_map.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/galaxy_map.py` | Same as `src/world/galaxy.py`; imports changed to `src.world.galaxy`. |
| `game_systems.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/game_systems.py` | Same as `src/systems/game_systems.py`; imports changed to `src.systems.game_systems`. |
| `knowledge_base.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/knowledge_base.py` | Same as `src/ai/knowledge_base.py`; runtime now uses `src.ai.knowledge_base`. |
| `mechanics.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/mechanics.py` | Same as `src/systems/mechanics.py`; imports changed to `src.systems.mechanics`. |
| `npc_registry.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/npc_registry.py` | Same as `src/world/npc_registry.py`; imports changed to `src.world.npc_registry`. |
| `procedural_engine.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/procedural_engine.py` | Same as `src/world/procedural.py`; imports changed to `src.world.procedural`. |
| `quest_chains.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/quest_chains.py` | Same as `src/systems/quests.py`; imports changed to `src.systems.quests`. |
| `subsystems.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/subsystems.py` | Same as `src/systems/subsystems.py`; imports changed to `src.systems.subsystems`. |
| `world_sim.py` | 100% duplicate | archived | `archive/legacy_dupes_2026_08/world_sim.py` | Same as `src/world/simulation.py`; imports changed to `src.world.simulation`. |

## Near-duplicates requiring manual review

| File pair | Similarity | Status | Reason |
|---|---:|---|---|
| `game_engine.py` / `src/core/engine.py` | 99.1% before import cleanup | requires manual review | Differences are import paths and a root compatibility import; logic was not merged. Root `game_engine.py` was left as a compatibility module with imports pointed at `src`. |
| `ai_connector.py` / `src/ai/connector.py` | 99.5% | requires manual review | Difference is config import style; root copy left in place. |
| `config.py` / `src/config.py` | 90.6% | requires manual review | Path handling differs; root copy left in place. |
| `setup.py` | zombie candidate | requires manual review | May be used by packaging commands outside import graph. |

## game_data consolidation

Active loader: `src/ai/knowledge_base.py` after runtime switch to `src`. It keeps top-level JSON only, groups versions by base name, and chooses a file via `PREFERRED_FILES` or version/size score.

Baseline before moves: 80 loaded JSON files from 101 top-level JSON files.
After moving old versions: 80 loaded JSON files from 82 top-level JSON files.

Moved old/non-selected JSON versions:

| File | Status | Action | Where | Evidence / two checks |
|---|---|---|---|---|
| `game_data/03_MEGA_DIALOGUE_SOCIAL_SYSTEM_COMPLETE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/03_MEGA_DIALOGUE_SOCIAL_SYSTEM_COMPLETE.json` | Not selected by loader; grep only metadata/project-map references. |
| `game_data/06_MEGA_ECONOMY_CRAFTING_COMPLETE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/06_MEGA_ECONOMY_CRAFTING_COMPLETE.json` | Not selected by loader; grep only metadata/project-map references. |
| `game_data/10_MEGA_PLAYER_INTERFACE_COMPLETE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/10_MEGA_PLAYER_INTERFACE_COMPLETE.json` | Superseded by `PLAYER_INTERFACE_V2_ENHANCED.json`; no direct code load. |
| `game_data/10_MEGA_PLAYER_INTERFACE_ENHANCED.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/10_MEGA_PLAYER_INTERFACE_ENHANCED.json` | Superseded by `PLAYER_INTERFACE_V2_ENHANCED.json`; no direct code load. |
| `game_data/12_MEGA_NARRATIVE_INTERFACE_COMPLETE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/12_MEGA_NARRATIVE_INTERFACE_COMPLETE.json` | Superseded by `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`; no direct code load. |
| `game_data/AI_RPG_CORE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/AI_RPG_CORE.json` | Superseded by `AI_RPG_CORE_V2_ENHANCED.json`; no direct code load. |
| `game_data/AUTOMATION.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/AUTOMATION.json` | Superseded by `AUTOMATION_V2_COMPREHENSIVE.json`; no direct code load. |
| `game_data/ENHANCED_EVENT_GENERATOR.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/ENHANCED_EVENT_GENERATOR.json` | Superseded by `ENHANCED_EVENT_GENERATOR_V2.json`; no direct code load. |
| `game_data/GM_TOOLKIT.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/GM_TOOLKIT.json` | Superseded by `GM_TOOLKIT_V2_COMPREHENSIVE.json`; no direct code load. |
| `game_data/HACKING.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/HACKING.json` | Superseded by `HACKING_V2_QUANTUM_AGE.json`; no direct code load. |
| `game_data/INVESTIGATION.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/INVESTIGATION.json` | Superseded by `INVESTIGATION_V2_GALACTIC_DETECTIVE.json`; no direct code load. |
| `game_data/MECHANICS.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/MECHANICS.json` | Superseded by `MECHANICS_V2_INTEGRATED_SYSTEMS.json`; code mentions were comments/docstrings. |
| `game_data/MODIFICATION.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/MODIFICATION.json` | Superseded by `MODIFICATION_V2_QUANTUM_BIOTECH.json`; no direct code load. |
| `game_data/NARRATIVE_INTERFACE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/NARRATIVE_INTERFACE.json` | Superseded by `NARRATIVE_INTERFACE_V2_ADAPTIVE.json`; no direct code load. |
| `game_data/PLAYER_INTERFACE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/PLAYER_INTERFACE.json` | Superseded by `PLAYER_INTERFACE_V2_ENHANCED.json`; no direct code load. |
| `game_data/PLAYER_INTERFACE_V2.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/PLAYER_INTERFACE_V2.json` | Superseded by `PLAYER_INTERFACE_V2_ENHANCED.json`; no direct code load. |
| `game_data/PROGRESSION_V2.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/PROGRESSION_V2.json` | Explicit preference keeps `PROGRESSION.json`; no direct code load. |
| `game_data/THEME_TONE.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/THEME_TONE.json` | Not selected by loader; grep showed only JSON metadata references. |
| `game_data/WORLD_SIM.json` | old JSON version | archived | `archive/legacy_dupes_2026_08/game_data/WORLD_SIM.json` | Superseded by `WORLD_SIM_V2_LIVING_UNIVERSE.json`; no direct code load. |

Kept despite loader skip:

- `game_data/CHARACTER_LIFEPATH_V3_MASSIVE_PART1.json`: directly loaded by `src/content/v4_legacy.py`.
- `game_data/STARTING_QUESTS.json`: fallback used by `src/core/engine.py`/compat `game_engine.py`.

## Build artifact consolidation

| File | Status | Action | Where | Evidence / two checks |
|---|---|---|---|---|
| `_internal/**` | PyInstaller artifact | archived | `archive/legacy_dupes_2026_08/_internal/**` | Contains `.dll`, `.pyd`, Python runtime and `.dist-info`; launcher now checks `src` source files, not `_internal`. |

`_internal/` was also added to `.gitignore`.

## Verification gates

| Gate | Result |
|---|---|
| `python -m compileall -q *.py src tests` after import/launcher switch | pass |
| `KnowledgeBase` after JSON/root duplicate archive | pass: 80 loaded files, unchanged from baseline |
| `python -m pytest -q` after final moves | allowed known failure only: `tests/test_server_smoke.py::TestServerRoutes::test_health_endpoint` |
| `python -m src.server.app` + `curl -I --max-time 10 http://127.0.0.1:8080/` | pass: HTTP 200 |

## PR publication status

A PR could not be opened from this environment because `origin` requires GitHub credentials and no `GH_TOKEN`/GitHub CLI auth is available. The branch and commits are left locally for publication through the GitHub UI.
