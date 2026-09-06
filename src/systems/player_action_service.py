# -*- coding: utf-8 -*-
"""
PlayerActionService — Phase 30 шаг 3: вынесена внешняя оркестрация хода игрока
из GameEngine.process_player_action (170 строк, 9 подсистем + self.ai).

ВАЖНО: это не поглощение логики. Сервис ДЕЛЕГИРУЕТ внутреннюю механику
(combat/mechanical/subsystem-триггеры/world-tick/property-income) уже
существующим объектам и callback-методам движка. Внутри-игровые шаги
(как именно работает _process_combat_turn или _handle_mechanical_action)
остаются в engine.py как 8 callback-методов — отдельный долг для будущих
шагов рефакторинга, не закрыт в этом шаге.

Dependency Injection: получает через конструктор ссылки на объекты,
созданные в GameEngine.__init__, и НИЧЕГО не инстанцирует сам.

Красная линия: модуль не импортирует src.server.*
"""
from typing import Dict, Optional

from src.systems.mechanics import ConversationManager
from src.content.v4_legacy import _game_time_to_hours
from src.systems.combat import (
    detect_subsystem_trigger, process_xp_gain, apply_defeat
)
from src.systems.mechanics import detect_mechanical_action
from src.content.v5_legacy import (
    calculate_auto_reputation, apply_reputation_changes, get_reputation_summary
)
from src.systems.quests import get_available_chains


class PlayerActionService:
    """Оркестрация хода игрока. Логика 1:1 перенесена из
    GameEngine.process_player_action (Phase 30 шаг 3, поведение не менялось)."""

    def __init__(self, state, get_ai, prompt_builder, combat_engine,
                 profession_abilities, quest_generator, property_income,
                 property, world_effects, world_tick_service,
                 # callback-методы engine (не выносятся в этом шаге — долг):
                 process_combat_turn, handle_subsystem_trigger,
                 check_mechanical_action, handle_mechanical_action,
                 parse_ai_response, get_client_state, advance_time,
                 planet_hook_factions,
                 # callback-поля engine (read/write через callable — сохраняют
                 # хранение на движке, см. property_active_chain/completed_chains):
                 get_active_chain, get_completed_chains,
                 build_system_prompt):
        """
        Args:
            state: GameState.
            get_ai: callable() -> AIConnector. Возвращает текущий AI-коннектор
                (lambda: self.ai). Сервис НЕ хранит ссылку на ai напрямую,
                чтобы monkeypatch атрибута движка подхватывался мгновенно.
            prompt_builder: SystemPromptBuilder (build, build_action_meta).
            combat_engine: CombatEngine (in_combat, combat).
            profession_abilities: ProfessionAbilityManager (detect, execute).
            quest_generator: ProceduralQuestGenerator (generate_quest, generate_quest_from_hook).
            property_income: PropertyIncomeManager (tick).
            property: PropertySystem.
            world_effects: WorldEffectsManager (get_active_effects_summary).
            world_tick_service: WorldTickService (tick) — уже вынесен в Phase 30 шаг 1.
            process_combat_turn: callable(action) -> Dict.
            handle_subsystem_trigger: callable(subsystem, action) -> Dict|None.
            check_mechanical_action: callable(action) -> Dict|None.
            handle_mechanical_action: callable(mech_action) -> Dict|None.
            parse_ai_response: callable(response) -> {"narrative", "state_changes"}.
            get_client_state: callable() -> Dict.
            advance_time: callable(minutes) -> None.
            planet_hook_factions: callable(planet) -> list[dict].
            get_active_chain: callable() -> dict|None. Возвращает engine.active_chain.
            get_completed_chains: callable() -> list. Возвращает engine.completed_chains.
            build_system_prompt: callable(action, dice_result, mech_result, subsystem_result) -> str.
                Делегат engine._build_system_prompt (SystemPromptService, шаг 2);
                используется stream-веткой run_stream_iter (ВРЕМЕННО до микрошага 2a).

        Cooldown-state (_last_chain_offer_h / _last_quest_gen_h) — атрибуты
        сервиса: в baseline они тоже `self.X` на том же self, что и весь метод,
        значит при exec baseline-тела с self=сервис (а не движок) поведение
        совпадёт побитово. Кулдауны логически принадлежат оркестратору, а не
        состоянию игрока, и не сериализуются.

        Static capture note (осознанное архитектурное решение, аналог
        get_player_tier в WorldTickService — Phase 30 шаг 1):
        все callback-методы и поля (process_combat_turn, handle_subsystem_trigger,
        check_mechanical_action, handle_mechanical_action, parse_ai_response,
        get_client_state, advance_time, planet_hook_factions, active_chain,
        completed_chains) захватываются ПО ЗНАЧЕНИЮ в момент создания сервиса.
        Переопределение engine.<method> после __init__ НЕ подхватывается
        (в отличие от ai, который резолвится динамически через get_ai/@property).
        Grep по tests/, src/, src/server/routes/ перед решением: ноль мест,
        где эти атрибуты переопределяются на экземпляре движка после init.
        Если появится код, полагающийся на динамическую переопределяемость,
        — потребуется единообразный рефакторинг на паттерн get_X (зафиксировано
        в ROADMAP.md, Technical Debt Register).
        """
        self.state = state
        self._get_ai = get_ai
        self.prompt_builder = prompt_builder
        self.combat_engine = combat_engine
        self.profession_abilities = profession_abilities
        self.quest_generator = quest_generator
        self.property_income = property_income
        self.property = property
        self.world_effects = world_effects
        self.world_tick_service = world_tick_service

        self._process_combat_turn = process_combat_turn
        self._handle_subsystem_trigger = handle_subsystem_trigger
        self._check_mechanical_action = check_mechanical_action
        self._handle_mechanical_action = handle_mechanical_action
        self._parse_ai_response = parse_ai_response
        self._get_client_state = get_client_state
        self._advance_time = advance_time
        self._planet_hook_factions = planet_hook_factions
        # Read-only callable-мосты к атрибутам engine. baseline-тело при exec
        # с self=сервис не должно упасть на self.active_chain — поэтому сервис
        # ЭКСПОНИРУЕТ эти имена как property, делегирующие на engine.
        self._get_active_chain = get_active_chain
        self._get_completed_chains = get_completed_chains
        # Phase 31 Этап 1: сборщик системного промпта stream-ветки.
        # Через DI-callback (не статический захват ai-стиля): в движке это
        # делегат _build_system_prompt → SystemPromptService (шаг 2).
        self._build_system_prompt = build_system_prompt

    @property
    def active_chain(self):
        return self._get_active_chain()

    @property
    def completed_chains(self):
        return self._get_completed_chains()

    @property
    def ai(self):
        """Прокси к engine.ai — для совместимости с baseline-телом
        (где self.ai.generate(...) идёт напрямую). Позволяет monkeypatch
        `engine.ai = FakeAI()` подхватываться в обоих путях."""
        return self._get_ai()

    def run(self, action: str) -> Dict:
        """Оркестрация одного хода игрока (sync-режим). Семантика 1:1 с
        GameEngine.process_player_action до выноса.

        Phase 31 Этап 1: run() — тонкий потребитель run_stream_iter(stream=False):
        pre- и post-LLM логика существует РОВНО В ОДНОМ экземпляре. Все
        промежуточные кортежи (("pre", ...), ("token", ...)) молча потребляются,
        возвращается payload последнего ("done", result).
        """
        result = None
        for kind, payload in self.run_stream_iter(action, stream=False):
            if kind == "done":
                result = payload
        return result

    def run_stream_iter(self, action: str, *, stream: bool = True):
        """Оркестрация одного хода игрока как генератор событий.

        Единственная реализация pre-LLM и post-LLM логики (Phase 31 Этап 1 —
        унификация api_action_stream). Порядок кортежей:
          ("pre", {"type": "dice"|"mechanical"|"subsystem"|"world_event", "data": ...})
          ("token", str)                          — только в stream-режиме
          ("done", <финальный Dict>)              — ВСЕГДА последний кортеж

        Ранние выходы (combat / ability / subsystem combat_started) отдают
        ("done", <результат раннего возврата>) и завершают генератор —
        routes-адаптер конвертирует это в jsonify без открытия SSE.

        stream=True → ai.generate_stream() с yield-ом токенов;
        stream=False → ai.generate() синхронно, без token-событий.
        Полный текст ответа в обоих режимах идёт в один и тот же
        _parse_ai_response.
        """
        import random

        self.state.conversation_history.append({"role": "user", "content": action})

        # === V7: COMBAT ROUTING — if in combat, handle combat turn ===
        if self.combat_engine.in_combat:
            yield ("done", self._process_combat_turn(action))
            return

        # === ФАЗА 20d: активные способности семейств профессий ===
        ability_id = self.profession_abilities.detect(action)
        if ability_id:
            ctx = {"location_name": self.state.current_location.get("district"),
                   "allies": (self.combat_engine.combat or {}).get("allies", [])
                              if self.combat_engine.in_combat else [],
                   "in_combat": self.combat_engine.in_combat}
            ability_result = self.profession_abilities.execute(self, ability_id, ctx)
            if ability_result and not ability_result.get("not_applicable"):
                yield ("done", {"narrative": ability_result.get("text", ""),
                                "ability_result": ability_result,
                                "in_combat": self.state.in_combat})
                return

        # === V7: SUBSYSTEM TRIGGER — detect hacking/investigation/crafting/combat ===
        subsystem = detect_subsystem_trigger(action)
        subsystem_result = None
        if subsystem:
            subsystem_result = self._handle_subsystem_trigger(subsystem, action)
            # If combat was started, route to combat
            if subsystem_result and subsystem_result.get("combat_started"):
                yield ("done", subsystem_result)
                return

        mechanical_result = self._check_mechanical_action(action)

        # === V6: DETECT BUY/SELL/TRAVEL MECHANICAL ACTIONS ===
        mech_action = detect_mechanical_action(action)
        mech_action_result = None
        if mech_action:
            mech_action_result = self._handle_mechanical_action(mech_action)

        # === V6: CONVERSATION MANAGEMENT — compress old history ===
        ConversationManager.manage_history(self.state.conversation_history)

        # === WORLD SIMULATION TICK (А2: единый метод, вызывается и фоново) ===
        self.state.world_context = self.world_tick_service.tick()

        # Phase 31 Этап 1: world_event (news/rumors/economic) — pre-событие SSE,
        # как в прежнем stream-пути (routes L152-154). Только если есть что показать.
        _wc = self.state.world_context
        if _wc.get("news") or _wc.get("rumors") or _wc.get("economic_event"):
            yield ("pre", {"type": "world_event", "data": _wc})

        # === V5: AUTO-REPUTATION — analyze action for faction impact ===
        rep_changes = calculate_auto_reputation(action, self.state.faction_reputation)
        if rep_changes:
            apply_reputation_changes(self.state.faction_reputation, rep_changes)
            self.state.world_context["rep_changes"] = get_reputation_summary(rep_changes)

        # === V5: WORLD EFFECTS CONTEXT — active price mods, lockdowns ===
        active_fx = self.world_effects.get_active_effects_summary(_game_time_to_hours(self.state.game_time))
        if active_fx:
            self.state.world_context["active_world_effects"] = active_fx

        # === V5: QUEST CHAIN — check if player should be offered one ===
        current_hours = _game_time_to_hours(self.state.game_time)
        # Offer every 5-10 game-days (120-240 hours)
        if not hasattr(self, '_last_chain_offer_h'):
            self._last_chain_offer_h = current_hours - random.randint(100, 200)
        chain_cooldown = random.randint(120, 240)
        if not self.active_chain and (current_hours - self._last_chain_offer_h) >= chain_cooldown:
            available = get_available_chains(
                self.state.character.get("level", 1),
                self.state.character.get("credits", 0),
                self.state.faction_reputation)
            # Filter out completed chains
            available = [c for c in available if c["id"] not in self.completed_chains]
            if available:
                offer = random.choice(available)
                self.state.world_context["chain_offer"] = offer
                self._last_chain_offer_h = current_hours

        # === Maybe generate procedural quest (every 2-5 game-days) ===
        if not hasattr(self, '_last_quest_gen_h'):
            self._last_quest_gen_h = current_hours - random.randint(30, 80)
        quest_cooldown_h = random.randint(48, 120)  # 2-5 days
        if (current_hours - self._last_quest_gen_h) >= quest_cooldown_h and len(self.state.active_quests) < 5:
            # Backlog#3: ~25% — квест из plot_hook случайной фракции текущей планеты
            hook_quest = None
            if random.random() < 0.25:
                planet = self.state.current_location.get("planet", "")
                candidates = [
                    f["name"] for f in
                    getattr(self.quest_generator, "_hook_factions_cache", None)
                    or self._planet_hook_factions(planet)]
                if not hasattr(self.quest_generator, "_hook_factions_cache"):
                    self.quest_generator._hook_factions_cache = candidates
                if candidates:
                    hook_quest = self.quest_generator.generate_quest_from_hook(
                        random.choice(candidates),
                        player_level=self.state.character.get("level", 1))
                    if "error" in hook_quest:
                        hook_quest = None
            pq = hook_quest or self.quest_generator.generate_quest(
                player_level=self.state.character.get("level", 1),
                location=self.state.current_location,
                faction_standings=self.state.faction_reputation,
            )
            self.state.active_quests.append(pq)
            self._last_quest_gen_h = current_hours
            self.state.world_context["new_quest"] = pq

        # === V6: PROPERTY INCOME — collect rent on time tick ===
        income_result = self.property_income.tick(current_hours, self.property,
                                                   self.state.character)
        if income_result:
            self.state.world_context["property_income"] = income_result

        # Phase 26: собираем scene_meta с Karmic Dice + Director's Notes через prompt_builder
        scene_meta = self.prompt_builder.build_action_meta(
            action=action,
            dice_result=mechanical_result,
            mechanical_changes=subsystem_result,
        )
        if self.state.current_location:
            scene_meta["location"] = self.state.current_location
        # Сохраняем последний karmic roll для отладки/тестов
        self.state.last_karmic_roll = scene_meta.get("karmic_roll")

        # Системный промпт. ВРЕМЕННО до микрошага 2a — см. ROADMAP:
        # sync-путь = prompt_builder.build (с Karmic Dice, как в Phase 2.1),
        # stream-путь = engine._build_system_prompt → SystemPromptService
        # (с [STATE]-шаблоном и place). После 2a обе ветки будут на одном билдере.
        if not stream:
            system_prompt = self.prompt_builder.build(
                tone_profile=self.state.tone_profile,
                scene_meta=scene_meta,
            )
        else:
            system_prompt = self._build_system_prompt(
                action,
                dice_result=mechanical_result,
                mech_result=mech_action_result,
                subsystem_result=subsystem_result,
            )

        # ═══ LLM-фаза: единственное ветвление — источник полного текста ═══
        if stream:
            buf = []
            for token in self.ai.generate_stream(
                system_prompt=system_prompt,
                messages=self.state.conversation_history[-12:],
            ):
                buf.append(token)
                yield ("token", token)
            ai_response = "".join(buf)
        else:
            ai_response = self.ai.generate(
                system_prompt=system_prompt,
                messages=self.state.conversation_history[-12:],
            )

        # ═══ POST-LLM фаза (одна копия) ═══
        parsed = self._parse_ai_response(ai_response)
        self.state.conversation_history.append({"role": "assistant", "content": parsed["narrative"]})
        self.state.session_events.append({
            "time": dict(self.state.game_time),
            "action": action[:100], "result": parsed["narrative"][:100],
        })
        # Use AI-determined time if available, else random
        time_mins = parsed.get("state_changes", {}).get("_custom_time", random.randint(5, 30))
        self._advance_time(minutes=time_mins)

        # === V7: PROPER XP → LEVEL UP ===
        xp_to_add = parsed.get("state_changes", {}).get("_xp_to_add", 0)
        level_up_info = None
        if xp_to_add and xp_to_add > 0:
            level_up_info = process_xp_gain(self.state.character, xp_to_add)

        # === V7: HP=0 DEFEAT CHECK (fail-forward, no permadeath) ===
        defeat_result = None
        if self.state.character.get("current_hp", 1) <= 0:
            defeat_result = apply_defeat(
                self.state.character, self.state.inventory,
                self.state.game_time, self.state.current_location
            )

        yield ("done", {
            "narrative": parsed["narrative"],
            "dice_results": mechanical_result,
            "state_changes": parsed.get("state_changes", {}),
            "game_state": self._get_client_state(),
            "world_events": [e.get("text","") for e in (self.state.world_context.get("world_events") or [])],
            "consequences": [c.get("text","") for c in (self.state.world_context.get("consequences") or [])],
            "new_quest": self.state.world_context.get("new_quest"),
            "rep_changes": self.state.world_context.get("rep_changes", ""),
            "chain_offer": self.state.world_context.get("chain_offer"),
            "mechanical_action": mech_action_result,
            "property_income": self.state.world_context.get("property_income"),
            "defeat": defeat_result,
            "level_up": level_up_info,
            "subsystem": subsystem_result,
        })
