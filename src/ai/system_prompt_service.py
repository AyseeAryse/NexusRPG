# -*- coding: utf-8 -*-
"""
SystemPromptService — Phase 30 шаг 2: вынос GameEngine._build_system_prompt
(227 строк, 10+ подсистем — крупнейший God-method по AST-инвентаризации
docs/engine_inventory.md).

Dependency Injection: сервис получает через конструктор ссылки на объекты,
созданные в GameEngine.__init__, и НИЧЕГО не инстанцирует сам. Метод-level
зависимости engine (get_player_influence_tier, _format_game_time, active_chain,
active_companions) передаются как read-only снапшоты/колбэки в build().

Красная линия: модуль не импортирует src.server.*
"""
from typing import Dict, Optional

from src.systems.quests import get_chain_stage
from src.systems.companions import get_companion_by_id
from src.content.v5_legacy import UNIQUE_NPCS
from src.systems import PsychologySystem


class SystemPromptService:
    """Сборка системного промпта LLM. Логика 1:1 перенесена из
    GameEngine._build_system_prompt (Phase 30 шаг 2, поведение не менялось)."""

    def __init__(self, state, kb, combat_engine, galaxy_map,
                 hacking, investigation, companions, ship, property,
                 world_effects, get_player_tier, format_game_time):
        """
        Args:
            state: GameState (владелец — GameEngine).
            kb: KnowledgeBase (kb.get_relevant_context).
            combat_engine: CombatEngine.
            galaxy_map: GalaxyMap (get_prompt_context).
            hacking / investigation / companions / ship / property: subsystem-объекты
                с get_prompt_context().
            world_effects: WorldEffectsManager (is_martial_law).
            get_player_tier: callable() -> dict (GameEngine.get_player_influence_tier).
            format_game_time: callable() -> str (GameEngine._format_game_time).
        """
        self.state = state
        self.kb = kb
        self.combat_engine = combat_engine
        self.galaxy_map = galaxy_map
        self.hacking = hacking
        self.investigation = investigation
        self.companions = companions
        self.ship = ship
        self.property = property
        self.world_effects = world_effects
        self._get_player_tier = get_player_tier
        self._format_game_time = format_game_time

    def build(self, action: str, dice_result: Optional[Dict] = None,
              mech_result: Optional[Dict] = None,
              subsystem_result: Optional[Dict] = None,
              active_chain: Optional[Dict] = None,
              active_companions: Optional[list] = None) -> str:
        char = self.state.character
        loc = self.state.current_location
        kb_context = self.kb.get_relevant_context(action, max_tokens=1200)
        wc = self.state.world_context  # world sim tick results

        # ─── CORE IDENTITY (always included, ~400 chars) ───
        parts = [
            "# ТЫ — ИИ ГМ текстовой RPG «NEXUS». Sci-fi нуар, 2387г.",
            "The Expanse+Cyberpunk+MGS. БЕЗ FTL/пришельцев/магии. Протомолекула=нанотех.",
            "",
            "## ПРАВИЛА ПИСЬМА:",
            "МИНИМУМ 3-4 АБЗАЦА текста в КАЖДОМ ответе. Пиши ПОДРОБНО и КИНЕМАТОГРАФИЧНО.",
            "Каждый абзац: 3+ предложения. Описывай окружение, атмосферу, звуки, запахи.",
            "ОБЯЗАТЕЛЬНО: 3+ сенсорных деталей (свет/звук/запах/тактильность/температура/вкус воздуха), "
            "2+ конкретных названий из мира (бренды/вывески/модели техники), "
            "1 фоновое действие (что делают другие вокруг), 1 неожиданная деталь.",
            "NPC: ВСЕГДА имя+внешность+манера речи+одежда. НЕ «мужчина сказал», А «Кэнджи Ито — худой, за 50, кибернетический глаз "
            "Zeiss-Mitsui мерцает синим, хриплый белтерский акцент, засаленный комбинезон с нашивкой OPA».",
            "Диалоги NPC: 2-3 фразы минимум, с характерной речью и эмоциями. Не одна строчка!",
            "СТИЛЬ: как будто описываешь сцену для фильма. Тёмные тона, неоновые блики, тяжёлая атмосфера.",
            "ЗАПРЕЩЕНО: короткие ответы менее 3 абзацев, сухие описания, безымянные NPC, мысли/чувства игрока, повтор вариантов.",
            "",
        ]

        # ─── WORLD CONTEXT (conditional, ~200 chars) ───
        if wc:
            wc_parts = []
            if wc.get("atmosphere"): wc_parts.append(f"Атмосфера: {wc['atmosphere']}")
            if wc.get("background_npcs"): wc_parts.append(f"Фон: {wc['background_npcs']}")
            if wc.get("news"): wc_parts.append(f"Новость: {wc['news'][0]}")
            if wc.get("rumors"): wc_parts.append(f"Слух: {wc['rumors'][0]}")
            if wc_parts:
                parts.append("## МИР СЕЙЧАС (впиши в сцену!):")
                parts.extend(wc_parts)
                parts.append("")

        # ─── CHARACTER + LOCATION (always, ~500 chars) ───
        attrs_compact = ", ".join(f"{k[:3]}:{v}" for k, v in char.get("attributes", {}).items())
        skills_compact = ", ".join(f"{k}:{v}" for k, v in char.get("skills", {}).items() if v > 0)
        parts += [
            f"## ПЕРСОНАЖ: {char.get('name','?')} | Lv{char.get('level',1)} | HP:{char.get('current_hp',50)}/{char.get('derived',{}).get('health_points',50)} | ₡{char.get('credits',0):,}",
            f"Рассудок:{char.get('current_sanity',50)} Стресс:{char.get('stress',0)} Человечность:{char.get('humanity',50)}",
            f"Атр: {attrs_compact}",
            f"Навыки: {skills_compact}",
            f"Происхождение: {char.get('origin_name', char.get('origin', '?'))} | Спец: {char.get('specialization_name', char.get('specialization', '?'))}",
            f"## ГДЕ: {loc.get('planet','?')} > {loc.get('city','?')} > {loc.get('district','')} | {self._format_game_time()}",
        ]
        # Galaxy map context (short)
        gm_ctx = self.galaxy_map.get_prompt_context(loc)
        if gm_ctx:
            parts.append(gm_ctx[:300])
        parts.append("")

        # ─── DICE RESULT (conditional, ~200 chars) ───
        if dice_result:
            result_word = "УСПЕХ" if dice_result['success'] else "ПРОВАЛ"
            parts.append(f"## 🎲 БРОСОК: {dice_result['skill']}+{dice_result['attribute']} = {dice_result['result']} vs DC{dice_result['difficulty']} → **{result_word}** ({dice_result['quality']})")
            parts.append("")

        # ─── MECHANICAL RESULT (conditional, ~200 chars) ───
        if mech_result:
            parts.append("## ⚙️ МЕХАНИКА (уже применено):")
            mt = mech_result.get("type", "")
            if mt == "buy" and mech_result.get("success"):
                parts.append(f"✅ Купил: {mech_result['bought']} за ₡{mech_result['price']}. Осталось: ₡{mech_result['credits_left']}")
            elif mt == "buy":
                parts.append(f"❌ Не купил: {mech_result.get('error','?')}")
            elif mt == "sell" and mech_result.get("success"):
                parts.append(f"✅ Продал: {mech_result['sold']} за ₡{mech_result['earned']}")
            elif mt in ("travel", "travel_planet") and mech_result.get("success"):
                parts.append(f"✅ Перемещение: → {mech_result.get('to', mech_result.get('to_planet','?'))}")
                enc = mech_result.get("encounter")
                if enc: parts.append(f"⚠️ Встреча: {enc.get('text','')[:80]}")
            elif mech_result.get("error"):
                parts.append(f"❌ {mech_result['error']}")
            parts.append("НЕ дублируй цифры в [STATE]!")
            parts.append("")

        # ─── SUBSYSTEM (conditional, ~100 chars) ───
        if subsystem_result:
            parts.append(f"## 🔧 {subsystem_result.get('system','').upper()}: {subsystem_result.get('narrative','')[:120]}")
            parts.append("")

        # ─── COMBAT (conditional, ~200 chars) ───
        combat_ctx = self.combat_engine.get_prompt_context()
        if combat_ctx:
            parts.append(combat_ctx)
            parts.append("")

        # ─── QUESTS (conditional, ~200 chars) ───
        all_quests = self.state.active_quests
        if all_quests:
            parts.append("## КВЕСТЫ: " + " | ".join(f"{q.get('title','?')}" for q in all_quests[:4]))

        # ─── QUEST CHAIN (conditional, ~200 chars) ───
        if active_chain:
            chain_id = active_chain.get("chain_id")
            stage_idx = active_chain.get("current_stage", 0)
            stage = get_chain_stage(chain_id, stage_idx)
            if stage:
                parts.append(f"## СЮЖЕТ: «{stage['chain_name']}» ({stage['stage_num']}/{stage['total_stages']}): {stage['title']}")
                parts.append(f"Цели: {', '.join(stage.get('objectives', []))}")
                if stage.get("branching"): parts.append("⚠️ КЛЮЧЕВОЙ ВЫБОР!")
                parts.append("")

        # ─── NPC CONTEXT (conditional, ~400 chars) ───
        npc_context = self.state.npc_registry.get_prompt_context(limit=5)
        if npc_context:
            parts.append(npc_context)
            parts.append("")

        # ─── UNIQUE NEARBY NPCs (conditional, ~300 chars) ───
        current_planet = loc.get("planet", "")
        current_city = loc.get("city", "")
        nearby_npcs = [n for n in UNIQUE_NPCS
                       if current_planet in n.get("location", "") or current_city in n.get("location", "")
                       or "Любой" in n.get("location", "") or "Меняет" in n.get("location", "")]
        if nearby_npcs:
            hour = self.state.game_time.get("hour", 12)
            time_period = "day" if 6 <= hour < 22 else "night"
            parts.append(f"## NPC РЯДОМ ({hour:02d}:00):")
            for npc in nearby_npcs[:3]:
                activity = npc.get("schedule", {}).get(time_period, "?")
                parts.append(f"• {npc['name']} ({npc['role']}): {activity}")
            parts.append("")

        # ─── COMPANIONS (conditional, ~200 chars) ───
        if active_companions:
            parts.append("## ГРУППА:")
            for cs in active_companions[:3]:
                comp = get_companion_by_id(cs["id"])
                if comp:
                    parts.append(f"• {comp['name']} «{comp['nickname']}» — {comp['type']}, лояльность {cs.get('loyalty',50)}%")
            parts.append("Компаньоны КОММЕНТИРУЮТ и РЕАГИРУЮТ!")
            parts.append("")

        # ─── INVENTORY (always, ~200 chars) ───
        if self.state.inventory:
            inv_compact = ", ".join(f"{i.get('name','?')}x{i.get('qty',1)}" for i in self.state.inventory[:8])
            parts.append(f"## ИНВЕНТАРЬ: {inv_compact}")
            parts.append("")

        # ─── REPUTATION / PSYCHOLOGY (conditional, ~150 chars) ───
        if self.state.faction_reputation:
            rep_compact = ", ".join(f"{k}:{v:+d}" for k, v in self.state.faction_reputation.items() if v != 0)
            if rep_compact:
                parts.append(f"## РЕПУТАЦИЯ: {rep_compact}")

        rep_summary = self.state.world_context.get("rep_changes", "")
        if rep_summary:
            parts.append(f"Изменение: {rep_summary}")

        psych_ctx = PsychologySystem.get_prompt_context(self.state.character)
        if psych_ctx:
            parts.append(psych_ctx[:200])
        parts.append("")

        # ─── WORLD EFFECTS (conditional, ~150 chars) ───
        active_fx = self.state.world_context.get("active_world_effects", [])
        if active_fx:
            parts.append("## МИРОВЫЕ ЭФФЕКТЫ: " + "; ".join(f"{fx['effect']}:{fx['value']}" for fx in active_fx[:3]))
            if self.world_effects.is_martial_law(): parts.append("⚠️ ВОЕННОЕ ПОЛОЖЕНИЕ!")
            parts.append("")

        # ─── KB REFERENCE (conditional, reduced to 1500 chars) ───
        if kb_context:
            parts += ["## СПРАВКА:", kb_context[:1500], ""]

        # ─── INFLUENCE TIER (always, ~60 chars) ───
        tier_info = self._get_player_tier()
        parts.append(f"Тир влияния: {tier_info['tier']} — {tier_info['name']}")

        # ─── RECENT EVENTS (conditional, ~200 chars) ───
        if self.state.session_events:
            recent = " | ".join(e.get("action", "?")[:30] for e in self.state.session_events[-4:])
            parts.append(f"Недавно: {recent} — НЕ ПОВТОРЯЙ, двигай вперёд!")

        # ─── SUBSYSTEM STATUS (conditional, ~200 chars) ───
        for sys in [self.hacking, self.investigation, self.companions, self.ship, self.property]:
            ctx = sys.get_prompt_context()
            if ctx:
                parts.append(ctx)

        # ─── CHAIN OFFER / NEW QUEST (conditional) ───
        chain_offer = self.state.world_context.get("chain_offer")
        if chain_offer:
            parts.append(f"🆕 Доступна линия: «{chain_offer['name']}» — намекни через NPC")

        new_q = self.state.world_context.get("new_quest")
        if new_q:
            parts.append(f"🆕 Квест: «{new_q['title']}» — намекни")

        # ─── NEWS (conditional, ~100 chars) ───
        if self.state.world_sim.news_history:
            _ln = self.state.world_sim.news_history[-1] if self.state.world_sim.news_history else ""
            _lt = _ln.get("text", "") if isinstance(_ln, dict) else str(_ln)
            parts.append(f"Фон-новости: {_lt[:80]}")

        parts.append("")
        parts.append("Пиши на русском. ПОДРОБНАЯ кинематографичная сцена МИНИМУМ 3-4 абзаца + варианты.")
        parts.append("Каждый абзац — 3+ предложений. Описывай обстановку, людей, звуки, свет, атмосферу.")

        # ─── ВАРИАНТЫ ДЕЙСТВИЙ (always, ~250 chars) ───
        parts += [
            "",
            "## В КОНЦЕ — 6 вариантов + свободный:",
            "**Что будешь делать?**",
            "1.[конкретное] 2.[агрессивное] 3.[социальное] 4.[рискованное] 5.[скрытное] 6.[креативное] 7.Свой вариант",
            "",
        ]

        # ─── STATE BLOCK FORMAT (always, ~600 chars) ───
        parts += [
            "## [STATE] БЛОК (после вариантов, скрыт от игрока):",
            '[STATE]{"hp_change":0,"credits_change":0,"stress_change":0,"humanity_change":0,',
            '"location":null,"add_items":[],"remove_items":[],',
            '"npc_met":null,"quest_complete":null,"quest_advance":false,',
            '"combat_started":false,"combat_ended":false,"time_minutes":15,"xp_gained":0}[/STATE]',
            "hp_change: урон отрицат./лечение полож. | credits_change: +получил/-потратил",
            'location: {"planet":"X","city":"Y","district":"Z"} если перешёл, null если нет',
            'place: "название заведения" если игрок вошёл в конкретное место района (магазин, бар, таможня), иначе null. Пример: {"planet":"Ганимед","city":"Станция Юпитер-Прайм","district":"Торговые палубы","place":"Таможенный пост"}',
            'add_items: [{"name":"X","qty":1}] | remove_items: ["X"] | npc_met: "Имя" | time: 5-120мин | xp: 0-50',
        ]

        return "\n".join(parts)
