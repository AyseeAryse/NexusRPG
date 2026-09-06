# AST-инвентаризация GameEngine — сгенерировано scripts/ast_inventory.py

## 1. Сводка

- Классов в engine.py с именем GameEngine: 1
- Методов GameEngine: **62**
- Суммарный объём тел методов: **2322 строк**
- Subsystem-полей в __init__: **26** (+0 data-полей)

## 2. Subsystem-поля __init__ (Задача 2)

| Поле | Класс/тип | Модуль импорта | Методов-пользователей | Методы |
|---|---|---|---|---|
| self.state | GameState | — (локальный/встроенный) | 45 | __init__, create_character_from_preset, _grant_starting_equipment, create_custom_character, _set_starting_location, process_player_action, _check_mechanical_action, _get_implant_bonus … |
| self.world_effects | WorldEffectsManager | src.content.v5_legacy | 8 | __init__, process_player_action, _build_system_prompt, _world_tick, save_game, load_game, get_shop_price_modifier, get_world_effects_summary |
| self.property | PropertySystem | src.systems.subsystems | 7 | __init__, process_player_action, _build_system_prompt, _get_client_state, _world_tick, save_game, load_game |
| self.combat_engine | CombatEngine | src.systems.combat | 7 | __init__, process_player_action, _build_system_prompt, _handle_mechanical_action, _process_combat_turn, _handle_subsystem_trigger, save_game |
| self.kb | KnowledgeBase | src.ai | 6 | __init__, get_presets, universal_skill_check, _build_system_prompt, _get_regional_faction_relations, _assign_starting_quests |
| self.hacking | HackingSystem | src.systems.subsystems | 6 | __init__, _build_system_prompt, _handle_subsystem_trigger, _get_client_state, save_game, load_game |
| self.investigation | InvestigationSystem | src.systems.subsystems | 6 | __init__, _build_system_prompt, _handle_subsystem_trigger, _get_client_state, save_game, load_game |
| self.ship | ShipSystem | src.systems.subsystems | 6 | __init__, _build_system_prompt, _handle_mechanical_action, _get_client_state, save_game, load_game |
| self.saves_dir | BoolOp(op=Or(), values=[Name(id='saves_d | — (локальный/встроенный) | 5 | __init__, save_game, load_game, list_saves, delete_save |
| self.companions | CompanionSystem | src.systems.subsystems | 5 | __init__, _build_system_prompt, _get_client_state, save_game, load_game |
| self.property_income | PropertyIncomeManager | src.systems.mechanics | 5 | __init__, process_player_action, _world_tick, save_game, load_game |
| self.tone_engine | ToneEngine | src.systems.tone_engine | 5 | __init__, create_custom_character, start_game, load_game, _apply_tone_to_current_location |
| self.dice | DiceRoller | — (локальный/встроенный) | 4 | __init__, universal_skill_check, _check_mechanical_action, start_combat |
| self.galaxy_map | GalaxyMap | src.world | 4 | __init__, _check_mechanical_action, _build_system_prompt, _handle_mechanical_action |
| self.expenses | ExpenseCycle | src.systems.expenses | 4 | __init__, _world_tick, save_game, load_game |
| self.quest_generator | ProceduralQuestGenerator | src.world.procedural | 3 | __init__, process_player_action, generate_quest_from_hook |
| self.prompt_builder | SystemPromptBuilder | src.ai.prompt_builder | 3 | __init__, process_player_action, start_game |
| self.ai | AIConnector | src.ai | 2 | __init__, process_player_action |
| self.world_ticker | WorldTicker | src.world.procedural | 2 | __init__, _world_tick |
| self.consequences | ConsequenceTracker | src.world.procedural | 2 | __init__, _world_tick |
| self.profession_abilities | ProfessionAbilityManager | src.systems.profession_abilities | 2 | __init__, process_player_action |
| self.faction_sim | FactionConflictSimulator | src.world.faction_conflict_sim | 2 | __init__, _world_tick |
| self.contract_gen | ContractGenerator | src.systems.contract_generator | 2 | __init__, accept_contract |
| self._creation_data | Constant(value=None) | — (локальный/встроенный) | 2 | __init__, get_creation_data |
| self.data_dir | BoolOp(op=Or(), values=[Name(id='data_di | — (локальный/встроенный) | 1 | __init__ |
| self.db_dir | BoolOp(op=Or(), values=[Name(id='db_dir' | — (локальный/встроенный) | 1 | __init__ |

## 3. Методы, трогающие 3+ подсистем — «God methods»

Найдено: **11**

| Метод | Строк | Подсистемы | Вызывается из routes |
|---|---|---|---|
| `_build_system_prompt` | 227 | 10: combat_engine, companions, galaxy_map, hacking, investigation, kb, property, ship, state, world_effects | gameplay.py |
| `process_player_action` | 170 | 9: ai, combat_engine, profession_abilities, prompt_builder, property, property_income, quest_generator, state, world_effects | gameplay.py |
| `_check_mechanical_action` | 141 | 3: dice, galaxy_map, state | gameplay.py |
| `_handle_mechanical_action` | 113 | 4: combat_engine, galaxy_map, ship, state | gameplay.py |
| `_handle_subsystem_trigger` | 101 | 4: combat_engine, hacking, investigation, state | gameplay.py |
| `_world_tick` | 78 | 8: consequences, expenses, faction_sim, property, property_income, state, world_effects, world_ticker | — |
| `load_game` | 56 | 11: companions, expenses, hacking, investigation, property, property_income, saves_dir, ship, state, tone_engine, world_effects | system.py |
| `__init__` | 49 | 26: _creation_data, ai, combat_engine, companions, consequences, contract_gen, data_dir, db_dir, dice, expenses, faction_sim, galaxy_map, hacking, investigation, kb, profession_abilities, prompt_builder, property, property_income, quest_generator, saves_dir, ship, state, tone_engine, world_effects, world_ticker | — |
| `_get_client_state` | 49 | 6: companions, hacking, investigation, property, ship, state | gameplay.py |
| `save_game` | 45 | 11: combat_engine, companions, expenses, hacking, investigation, property, property_income, saves_dir, ship, state, world_effects | system.py |
| `start_game` | 42 | 3: prompt_builder, state, tone_engine | system.py |

## 4. Группировка методов по набору подсистем

### Группа `state` — 24 методов, 606 строк

| Метод | Строк | routes |
|---|---|---|
| `_parse_ai_response` | 170 | gameplay.py |
| `complete_contract` | 75 | gameplay.py |
| `_grant_starting_equipment` | 65 | — |
| `create_character_from_preset` | 45 | character.py |
| `_migrate_attr_bonuses` | 42 | — |
| `_set_starting_location` | 30 | — |
| `_get_origin_traits` | 29 | — |
| `advance_quest_chain` | 21 | — |
| `abandon_quest` | 20 | character.py |
| `_enforce_skill_caps` | 15 | — |
| `get_player_influence_tier` | 15 | economy.py, gameplay.py |
| `recruit_companion` | 14 | — |
| `_advance_time` | 13 | gameplay.py, world.py |
| `add_xp` | 12 | character.py |
| `_get_implant_bonus` | 9 | — |
| `get_available_companions_list` | 9 | — |
| `get_available_quest_chains` | 6 | — |
| `_format_game_time` | 3 | — |
| `heal` | 3 | — |
| `apply_damage` | 2 | — |
| `add_credits` | 2 | character.py |
| `add_item` | 2 | — |
| `get_inventory` | 2 | character.py |
| `get_quests` | 2 | character.py |

### Группа `combat_engine+companions+galaxy_map+hacking+investigation+kb+property+ship+state+world_effects` — 1 методов, 227 строк

| Метод | Строк | routes |
|---|---|---|
| `_build_system_prompt` | 227 | gameplay.py |

### Группа `ai+combat_engine+profession_abilities+prompt_builder+property+property_income+quest_generator+state+world_effects` — 1 методов, 170 строк

| Метод | Строк | routes |
|---|---|---|
| `process_player_action` | 170 | gameplay.py |

### Группа `dice+galaxy_map+state` — 1 методов, 141 строк

| Метод | Строк | routes |
|---|---|---|
| `_check_mechanical_action` | 141 | gameplay.py |

### Группа `(none)` — 12 методов, 127 строк

| Метод | Строк | routes |
|---|---|---|
| `_canonicalize_location` | 35 | — |
| `_planet_hook_factions` | 16 | — |
| `_compute_derived_stats` | 13 | — |
| `_strip_telemetry` | 13 | — |
| `get_companion_bonuses` | 12 | — |
| `start_quest_chain` | 11 | — |
| `change_companion_loyalty` | 10 | — |
| `_background_catch_up` | 6 | — |
| `_region_matches` | 4 | — |
| `dismiss_companion` | 3 | — |
| `combat_action` | 2 | — |
| `get_full_state` | 2 | character.py |

### Группа `state+tone_engine` — 2 методов, 121 строк

| Метод | Строк | routes |
|---|---|---|
| `create_custom_character` | 101 | character.py |
| `_apply_tone_to_current_location` | 20 | world.py |

### Группа `combat_engine+galaxy_map+ship+state` — 1 методов, 113 строк

| Метод | Строк | routes |
|---|---|---|
| `_handle_mechanical_action` | 113 | gameplay.py |

### Группа `combat_engine+hacking+investigation+state` — 1 методов, 101 строк

| Метод | Строк | routes |
|---|---|---|
| `_handle_subsystem_trigger` | 101 | gameplay.py |

### Группа `kb+state` — 2 методов, 99 строк

| Метод | Строк | routes |
|---|---|---|
| `_assign_starting_quests` | 57 | — |
| `_get_regional_faction_relations` | 42 | — |

### Группа `contract_gen+state` — 1 методов, 88 строк

| Метод | Строк | routes |
|---|---|---|
| `accept_contract` | 88 | gameplay.py |

### Группа `consequences+expenses+faction_sim+property+property_income+state+world_effects+world_ticker` — 1 методов, 78 строк

| Метод | Строк | routes |
|---|---|---|
| `_world_tick` | 78 | — |

### Группа `combat_engine+state` — 1 методов, 76 строк

| Метод | Строк | routes |
|---|---|---|
| `_process_combat_turn` | 76 | gameplay.py |

### Группа `companions+expenses+hacking+investigation+property+property_income+saves_dir+ship+state+tone_engine+world_effects` — 1 методов, 56 строк

| Метод | Строк | routes |
|---|---|---|
| `load_game` | 56 | system.py |

### Группа `_creation_data+ai+combat_engine+companions+consequences+contract_gen+data_dir+db_dir+dice+expenses+faction_sim+galaxy_map+hacking+investigation+kb+profession_abilities+prompt_builder+property+property_income+quest_generator+saves_dir+ship+state+tone_engine+world_effects+world_ticker` — 1 методов, 49 строк

| Метод | Строк | routes |
|---|---|---|
| `__init__` | 49 | — |

### Группа `companions+hacking+investigation+property+ship+state` — 1 методов, 49 строк

| Метод | Строк | routes |
|---|---|---|
| `_get_client_state` | 49 | gameplay.py |

### Группа `_creation_data` — 1 методов, 48 строк

| Метод | Строк | routes |
|---|---|---|
| `get_creation_data` | 48 | system.py |

### Группа `combat_engine+companions+expenses+hacking+investigation+property+property_income+saves_dir+ship+state+world_effects` — 1 методов, 45 строк

| Метод | Строк | routes |
|---|---|---|
| `save_game` | 45 | system.py |

### Группа `prompt_builder+state+tone_engine` — 1 методов, 42 строк

| Метод | Строк | routes |
|---|---|---|
| `start_game` | 42 | system.py |

### Группа `dice+kb` — 1 методов, 26 строк

| Метод | Строк | routes |
|---|---|---|
| `universal_skill_check` | 26 | — |

### Группа `saves_dir` — 2 методов, 24 строк

| Метод | Строк | routes |
|---|---|---|
| `list_saves` | 18 | system.py |
| `delete_save` | 6 | system.py |

### Группа `dice+state` — 1 методов, 15 строк

| Метод | Строк | routes |
|---|---|---|
| `start_combat` | 15 | — |

### Группа `quest_generator+state` — 1 методов, 10 строк

| Метод | Строк | routes |
|---|---|---|
| `generate_quest_from_hook` | 10 | world.py |

### Группа `state+world_effects` — 2 методов, 9 строк

| Метод | Строк | routes |
|---|---|---|
| `get_shop_price_modifier` | 5 | — |
| `get_world_effects_summary` | 4 | — |

### Группа `kb` — 1 методов, 2 строк

| Метод | Строк | routes |
|---|---|---|
| `get_presets` | 2 | system.py |

## 5. Полный список методов (Задача 1)

| Метод | строки | объём | подсистемы | routes |
|---|---|---|---|---|
| `__init__` | 205–253 | 49 | _creation_data, ai, combat_engine, companions, consequences, contract_gen, data_dir, db_dir, dice, expenses, faction_sim, galaxy_map, hacking, investigation, kb, profession_abilities, prompt_builder, property, property_income, quest_generator, saves_dir, ship, state, tone_engine, world_effects, world_ticker | — |
| `get_creation_data` | 257–304 | 48 | _creation_data | system.py |
| `get_presets` | 306–307 | 2 | kb | system.py |
| `create_character_from_preset` | 309–353 | 45 | state | character.py |
| `_grant_starting_equipment` | 438–502 | 65 | state | — |
| `create_custom_character` | 504–604 | 101 | state, tone_engine | character.py |
| `_compute_derived_stats` | 606–618 | 13 | — | — |
| `_set_starting_location` | 620–649 | 30 | state | — |
| `process_player_action` | 653–822 | 170 | ai, combat_engine, profession_abilities, prompt_builder, property, property_income, quest_generator, state, world_effects | gameplay.py |
| `universal_skill_check` | 824–849 | 26 | dice, kb | — |
| `_check_mechanical_action` | 852–992 | 141 | dice, galaxy_map, state | gameplay.py |
| `_get_implant_bonus` | 994–1002 | 9 | state | — |
| `_build_system_prompt` | 1004–1230 | 227 | combat_engine, companions, galaxy_map, hacking, investigation, kb, property, ship, state, world_effects | gameplay.py |
| `_handle_mechanical_action` | 1232–1344 | 113 | combat_engine, galaxy_map, ship, state | gameplay.py |
| `_process_combat_turn` | 1348–1423 | 76 | combat_engine, state | gameplay.py |
| `_handle_subsystem_trigger` | 1427–1527 | 101 | combat_engine, hacking, investigation, state | gameplay.py |
| `_canonicalize_location` | 1535–1569 | 35 | — | — |
| `_strip_telemetry` | 1612–1624 | 13 | — | — |
| `_parse_ai_response` | 1626–1795 | 170 | state | gameplay.py |
| `_advance_time` | 1797–1809 | 13 | state | gameplay.py, world.py |
| `_format_game_time` | 1811–1813 | 3 | state | — |
| `_get_origin_traits` | 1815–1843 | 29 | state | — |
| `_get_regional_faction_relations` | 1845–1886 | 42 | kb, state | — |
| `_get_client_state` | 1888–1936 | 49 | companions, hacking, investigation, property, ship, state | gameplay.py |
| `start_game` | 1940–1981 | 42 | prompt_builder, state, tone_engine | system.py |
| `_assign_starting_quests` | 1983–2039 | 57 | kb, state | — |
| `_planet_hook_factions` | 2041–2056 | 16 | — | — |
| `_region_matches` | 2058–2061 | 4 | — | — |
| `generate_quest_from_hook` | 2063–2072 | 10 | quest_generator, state | world.py |
| `accept_contract` | 2074–2161 | 88 | contract_gen, state | gameplay.py |
| `complete_contract` | 2163–2237 | 75 | state | gameplay.py |
| `_world_tick` | 2239–2316 | 78 | consequences, expenses, faction_sim, property, property_income, state, world_effects, world_ticker | — |
| `_background_catch_up` | 2318–2323 | 6 | — | — |
| `save_game` | 2327–2371 | 45 | combat_engine, companions, expenses, hacking, investigation, property, property_income, saves_dir, ship, state, world_effects | system.py |
| `load_game` | 2373–2428 | 56 | companions, expenses, hacking, investigation, property, property_income, saves_dir, ship, state, tone_engine, world_effects | system.py |
| `list_saves` | 2430–2447 | 18 | saves_dir | system.py |
| `delete_save` | 2449–2454 | 6 | saves_dir | system.py |
| `start_combat` | 2458–2472 | 15 | dice, state | — |
| `combat_action` | 2474–2475 | 2 | — | — |
| `get_full_state` | 2479–2480 | 2 | — | character.py |
| `apply_damage` | 2482–2483 | 2 | state | — |
| `heal` | 2485–2487 | 3 | state | — |
| `add_xp` | 2489–2500 | 12 | state | character.py |
| `_apply_tone_to_current_location` | 2502–2521 | 20 | state, tone_engine | world.py |
| `_enforce_skill_caps` | 2523–2537 | 15 | state | — |
| `_migrate_attr_bonuses` | 2539–2580 | 42 | state | — |
| `get_player_influence_tier` | 2582–2596 | 15 | state | economy.py, gameplay.py |
| `add_credits` | 2598–2599 | 2 | state | character.py |
| `add_item` | 2601–2602 | 2 | state | — |
| `get_inventory` | 2604–2605 | 2 | state | character.py |
| `get_quests` | 2607–2608 | 2 | state | character.py |
| `abandon_quest` | 2610–2629 | 20 | state | character.py |
| `get_available_companions_list` | 2633–2641 | 9 | state | — |
| `recruit_companion` | 2643–2656 | 14 | state | — |
| `dismiss_companion` | 2658–2660 | 3 | — | — |
| `change_companion_loyalty` | 2662–2671 | 10 | — | — |
| `get_companion_bonuses` | 2673–2684 | 12 | — | — |
| `get_available_quest_chains` | 2688–2693 | 6 | state | — |
| `start_quest_chain` | 2695–2705 | 11 | — | — |
| `advance_quest_chain` | 2707–2727 | 21 | state | — |
| `get_shop_price_modifier` | 2731–2735 | 5 | state, world_effects | — |
| `get_world_effects_summary` | 2737–2740 | 4 | state, world_effects | — |

## 6. app.js — оглавление top-level (Задача 3)

Функций/секций: **175**, охвачено строк: 3315 из 3318

| строки | тип | имя | объём |
|---|---|---|---|
| 5–5 | section | `Toast Notification System` | 1 |
| 6–27 | function | `showToast` | 22 |
| 28–28 | section | `Safe API fetch wrapper` | 1 |
| 29–43 | function | `apiFetch` | 15 |
| 44–57 | section | `State` | 14 |
| 58–84 | section | `Skill/Attr names` | 27 |
| 85–85 | function | `attrLabel` | 1 |
| 86–87 | function | `skillLabel` | 2 |
| 88–88 | section | `Screen Management` | 1 |
| 89–98 | function | `showScreen` | 10 |
| 99–99 | section | `Boot Sequence` | 1 |
| 100–149 | function | `bootSequence` | 50 |
| 150–157 | function | `addBootLine` | 8 |
| 158–159 | function | `sleep` | 2 |
| 160–160 | section | `AI Status` | 1 |
| 161–178 | function | `checkAIStatus` | 18 |
| 179–180 | section | `=` | 2 |
| 181–193 | section | `=` | 13 |
| 194–205 | function | `onCloudProviderChange` | 12 |
| 206–240 | function | `refreshModels` | 35 |
| 241–276 | function | `saveSettings` | 36 |
| 277–298 | function | `testConnection` | 22 |
| 299–339 | function | `loadSettings` | 41 |
| 340–341 | section | `=` | 2 |
| 342–343 | section | `=` | 2 |
| 344–356 | function | `initCharCreation` | 13 |
| 357–362 | function | `setCreationMode` | 6 |
| 363–389 | function | `goCreationStep` | 27 |
| 390–390 | section | `Presets` | 1 |
| 391–422 | function | `loadPresets` | 32 |
| 423–446 | function | `startGamePreset` | 24 |
| 447–447 | section | `Custom Creation Steps` | 1 |
| 448–488 | function | `renderOrigins` | 41 |
| 489–578 | function | `renderFormativeYears` | 90 |
| 579–615 | function | `renderSpecializations` | 37 |
| 616–628 | function | `renderModBadges` | 13 |
| 629–634 | function | `truncate` | 6 |
| 635–647 | function | `renderPointAllocation` | 13 |
| 648–669 | function | `renderAttrSliders` | 22 |
| 670–682 | function | `changeAttr` | 13 |
| 683–704 | function | `renderSkillSliders` | 22 |
| 705–716 | function | `changeSkill` | 12 |
| 717–733 | function | `renderCharSummary` | 17 |
| 734–744 | function | `updateAge` | 11 |
| 745–780 | function | `startGameCustom` | 36 |
| 781–782 | section | `=` | 2 |
| 783–784 | section | `=` | 2 |
| 785–816 | function | `showSaves` | 32 |
| 817–859 | function | `loadGame` | 43 |
| 860–867 | function | `isSystemPrompt` | 8 |
| 868–878 | function | `quickSave` | 11 |
| 879–887 | function | `deleteSave` | 9 |
| 888–889 | section | `=` | 2 |
| 890–891 | section | `=` | 2 |
| 892–1003 | function | `sendAction` | 112 |
| 1004–1008 | function | `quickAction` | 5 |
| 1009–1010 | section | `═` | 2 |
| 1011–1012 | section | `═` | 2 |
| 1013–1067 | function | `handlePostActionEvents` | 55 |
| 1068–1086 | function | `showLevelUpNotification` | 19 |
| 1087–1103 | function | `showDefeatNotification` | 17 |
| 1104–1113 | function | `updateCombatUI` | 10 |
| 1114–1130 | function | `handleMechanicalResult` | 17 |
| 1131–1148 | function | `handleSubsystemResult` | 18 |
| 1149–1150 | section | `=` | 2 |
| 1151–1152 | section | `=` | 2 |
| 1153–1179 | function | `updateGameUI` | 27 |
| 1180–1193 | function | `addNarrativeMessage` | 14 |
| 1194–1203 | function | `createNarrativeElement` | 10 |
| 1204–1212 | function | `addSystemMessage` | 9 |
| 1213–1221 | function | `addErrorMessage` | 9 |
| 1222–1263 | function | `addDiceResult` | 42 |
| 1264–1275 | function | `diceOutcomeNarrative` | 12 |
| 1276–1286 | function | `toggleDiceDetails` | 11 |
| 1287–1423 | function | `formatNarrative` | 137 |
| 1424–1429 | function | `choiceSelect` | 6 |
| 1430–1435 | function | `choiceCustom` | 6 |
| 1436–1449 | function | `formatNarrativeRaw` | 14 |
| 1450–1450 | function | `clearNarrative` | 1 |
| 1451–1455 | function | `scrollNarrative` | 5 |
| 1456–1467 | function | `showTypingIndicator` | 12 |
| 1468–1472 | function | `removeTypingIndicator` | 5 |
| 1473–1473 | section | `Side Panels — FIXED: Russian skill names` | 1 |
| 1474–1502 | function | `togglePanel` | 29 |
| 1503–1504 | function | `closeSidePanel` | 2 |
| 1505–1590 | function | `renderCharacterPanel` | 86 |
| 1591–1654 | function | `renderInventoryPanel` | 64 |
| 1655–1673 | function | `sellItemByName` | 19 |
| 1674–1676 | function | `sellItem` | 3 |
| 1677–1682 | function | `enterAndShop` | 6 |
| 1683–1702 | function | `enterPlace` | 20 |
| 1703–1722 | function | `equipItem` | 20 |
| 1723–1747 | function | `useItem` | 25 |
| 1748–1749 | section | `═` | 2 |
| 1750–1750 | section | `═` | 1 |
| 1751–1826 | function | `renderImplantPanel` | 76 |
| 1827–1851 | function | `installImplant` | 25 |
| 1852–1868 | function | `removeImplant` | 17 |
| 1869–1949 | function | `renderShopPanel` | 81 |
| 1950–1958 | function | `filterShop` | 9 |
| 1959–1977 | function | `buyItem` | 19 |
| 1978–1981 | function | `updateCreditsUI` | 4 |
| 1982–2017 | function | `renderWorldPanel` | 36 |
| 2018–2035 | function | `showWorldEvent` | 18 |
| 2036–2079 | function | `renderQuestsPanel` | 44 |
| 2080–2080 | section | `MAP PANEL` | 1 |
| 2081–2189 | function | `renderMapPanel` | 109 |
| 2190–2206 | function | `moveToDistrict` | 17 |
| 2207–2221 | function | `moveToCity` | 15 |
| 2222–2240 | function | `moveToPlanet` | 19 |
| 2241–2244 | function | `visitPlace` | 4 |
| 2245–2245 | section | `NPC PANEL` | 1 |
| 2246–2314 | function | `renderNPCPanel` | 69 |
| 2315–2319 | function | `npcCall` | 5 |
| 2320–2325 | function | `npcRoute` | 6 |
| 2326–2361 | function | `renderCraftingPanel` | 36 |
| 2362–2381 | function | `doCraft` | 20 |
| 2382–2382 | section | `ENHANCED CHARACTER PANEL (with psychology, perks, property)` | 1 |
| 2383–2429 | function | `renderCharacterPanelExtras` | 47 |
| 2430–2453 | function | `loadAvailablePerks` | 24 |
| 2454–2466 | function | `selectPerk` | 13 |
| 2467–2471 | function | `openLevelUpPanel` | 5 |
| 2472–2492 | function | `spendSkillPoint` | 21 |
| 2493–2514 | function | `spendAttributePoint` | 22 |
| 2515–2515 | section | `TRAVEL EVENT HANDLING` | 1 |
| 2516–2521 | function | `handleTravelEvent` | 6 |
| 2522–2523 | section | `═` | 2 |
| 2524–2524 | section | `═` | 1 |
| 2525–2588 | function | `renderCompanionsPanel` | 64 |
| 2589–2602 | function | `recruitCompanion` | 14 |
| 2603–2613 | function | `dismissCompanion` | 11 |
| 2614–2615 | section | `═` | 2 |
| 2616–2616 | section | `═` | 1 |
| 2617–2711 | function | `renderShipPanel` | 95 |
| 2712–2725 | function | `buyShip` | 14 |
| 2726–2738 | function | `buyShipModel` | 13 |
| 2739–2748 | function | `refuelShip` | 10 |
| 2749–2756 | function | `repairShip` | 8 |
| 2757–2769 | function | `loadCargoPrompt` | 13 |
| 2770–2782 | function | `upgradeShipPrompt` | 13 |
| 2783–2784 | section | `═` | 2 |
| 2785–2785 | section | `═` | 1 |
| 2786–2831 | function | `renderPropertyPanel` | 46 |
| 2832–2852 | function | `loadPropertyTypes` | 21 |
| 2853–2867 | function | `buyProperty` | 15 |
| 2868–2880 | function | `storeItemInProperty` | 13 |
| 2881–2882 | section | `═` | 2 |
| 2883–2883 | section | `═` | 1 |
| 2884–2940 | function | `renderHackingPanel` | 57 |
| 2941–2969 | function | `loadHackTargets` | 29 |
| 2970–2982 | function | `startHack` | 13 |
| 2983–3006 | function | `doHackAction` | 24 |
| 3007–3008 | section | `═` | 2 |
| 3009–3009 | section | `═` | 1 |
| 3010–3078 | function | `renderInvestigationPanel` | 69 |
| 3079–3092 | function | `concludeCase` | 14 |
| 3093–3114 | function | `openNewCase` | 22 |
| 3115–3142 | function | `chooseFromList` | 28 |
| 3143–3156 | function | `addClueToCase` | 14 |
| 3157–3170 | function | `addSuspectToCase` | 14 |
| 3171–3172 | section | `═` | 2 |
| 3173–3173 | section | `═` | 1 |
| 3174–3244 | function | `renderFactionsPanel` | 71 |
| 3245–3255 | function | `startHookQuest` | 11 |
| 3256–3256 | section | `Helpers` | 1 |
| 3257–3257 | function | `setText` | 1 |
| 3258–3258 | function | `formatNum` | 1 |
| 3259–3262 | function | `formatDate` | 4 |
| 3263–3264 | function | `showLoading` | 2 |
| 3265–3267 | section | `Init` | 3 |
| 3268–3269 | section | `═` | 2 |
| 3270–3270 | section | `═` | 1 |
| 3271–3288 | function | `showModal` | 18 |
| 3289–3294 | function | `closeModal` | 6 |
| 3295–3319 | function | `showShipDatasheet` | 25 |