# -*- coding: utf-8 -*-
"""
WorldTickService — Phase 30 шаг 1: вынос GameEngine._world_tick (78 строк).

Dependency Injection: сервис получает через конструктор уже существующие
объекты, созданные в GameEngine.__init__, и НЕ создаёт/не импортирует
их классы для инстанцирования. GameEngine остаётся единственным владельцем.

Красная линия: этот модуль не импортирует ничего из src.server.*
(core и systems никогда не импортируют server).
"""
from typing import Dict

from src.world.player_tiers import compute_player_tier, FAME_PER_NEWS_MENTION


class WorldTickService:
    """Один мировой тик: news/weather (world_sim), world_ticker, consequences,
    faction_sim, property income, expenses. Логика перенесена 1:1 из
    GameEngine._world_tick (Phase 30, без изменения поведения)."""

    def __init__(self, state, world_effects, world_ticker, consequences,
                 faction_sim, property_income, property, expenses,
                 get_player_tier):
        """
        Args:
            state: GameState (единственный владелец — GameEngine).
            world_effects: WorldEffectsManager (engine.world_effects).
            world_ticker: WorldTicker (engine.world_ticker).
            consequences: ConsequenceTracker (engine.consequences).
            faction_sim: FactionConflictSimulator (engine.faction_sim).
            property_income: PropertyIncomeManager (engine.property_income).
            property: PropertySystem (engine.property).
            expenses: ExpenseCycle (engine.expenses).
            get_player_tier: callable() -> dict — делегат к
                GameEngine.get_player_influence_tier (tier нужен в трёх местах
                старой логики; вычисляется от state/property/ship, которые
                принадлежат engine — поэтому передаётся колбэком, а не дублируется).
        """
        self.state = state
        self.world_effects = world_effects
        self.world_ticker = world_ticker
        self.consequences = consequences
        self.faction_sim = faction_sim
        self.property_income = property_income
        self.property = property
        self.expenses = expenses
        self._get_player_tier = get_player_tier

    def tick(self) -> Dict:
        """А2: один мировой тик. Вызывается из process_player_action И фоново
        (_background_catch_up). Логика тиков не менялась — только источник вызова."""
        tier = self._get_player_tier()["tier"]
        # А4: новости получают механическое влияние через WorldEffectsManager
        self.state.world_sim.world_effects_ref = self.world_effects
        self.state.world_sim._last_game_time = dict(self.state.game_time)
        # backlog#5: фракции игрока с rep>=40 — кандидат на упоминание в новостях
        # (порог и форма проверки — как в event_roles.has_rep_link)
        notable = [name for name, rep in self.state.faction_reputation.items()
                   if isinstance(rep, (int, float)) and rep >= 40]
        wc = self.state.world_sim.tick(
            self.state.game_time, self.state.current_location, tier,
            notable_factions=notable,
            character=self.state.character
        )
        mentioned = wc.pop("news_mention", None)
        if mentioned:
            self.state.fame = getattr(self.state, "fame", 0) + FAME_PER_NEWS_MENTION
            wc["news_mention"] = {"faction": mentioned,
                                  "fame_gained": FAME_PER_NEWS_MENTION}

        world_events = self.world_ticker.tick(self.state)
        if world_events:
            wc["world_events"] = world_events
            from src.content.v4_legacy import _game_time_to_hours
            current_h = _game_time_to_hours(self.state.game_time)
            for we in world_events:
                self.world_effects.apply_event_effects(we, current_h)

        turn = self.state.world_sim.turn_count
        triggered_consequences = self.consequences.check_consequences(turn)
        if triggered_consequences:
            wc["consequences"] = triggered_consequences

        # Phase 3: Living World — межфракционные конфликты (с throttling + tier ceiling)
        # Маскировка ошибок убрана (Phase 3 prep) — сбой симулятора обязан падать с трейсбеком.
        tier_for_conflict = self._get_player_tier().get("tier", 0)
        conflict_events = self.faction_sim.tick(
            player_tier=tier_for_conflict,
            current_location=self.state.current_location,
        )
        if conflict_events:
            wc["conflict_events"] = conflict_events
            # Применяем ценовой модификатор к world_sim (локальный инкремент)
            total_delta = sum(e.get("price_modifier_delta", 0) for e in conflict_events)
            if total_delta > 0:
                self.state.world_sim.price_modifier = min(
                    1.5, self.state.world_sim.price_modifier + total_delta
                )
            # Heat delta применяется к глобальному heat игрока
            total_heat = sum(e.get("heat_delta", 0) for e in conflict_events)
            if total_heat > 0:
                self.state.character["heat"] = self.state.character.get("heat", 0) + total_heat
            # Короткое summary для scene_meta (≤1 предложение)
            self.state.world_context["local_event"] = self.faction_sim.get_last_event_summary()
        else:
            self.state.world_context.pop("local_event", None)

        # А3: доход недвижимости тоже привязан к тику времени
        try:
            from src.content.v4_legacy import _game_time_to_hours as _gth
            current_hours = _gth(self.state.game_time)
            income_result = self.property_income.tick(current_hours, self.property,
                                                      self.state.character)
            if income_result:
                wc["property_income"] = income_result
            # А3: симметричный цикл расходов — upkeep/жизнь/корабль
            tier_n = self._get_player_tier()["tier"]
            expense_record = self.expenses.tick(current_hours, self.property,
                                                getattr(self, "ship", None),
                                                self.state.character, tier_n)
            if expense_record:
                wc["expenses"] = expense_record
        except Exception:
            pass
        return wc
