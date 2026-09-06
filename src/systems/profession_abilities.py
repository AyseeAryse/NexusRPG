"""Фаза 20d — активные способности 12 семейств профессий.

Паттерн: реестр ABILITY_REGISTRY = {ability_id: {name, family, cooldown, keywords, fn}}.
fn(engine, context) -> dict(text=..., effects=...) | None (условие не выполнено).

Cooldown хранится в GameState: state.ability_cooldowns[ability_id] = счётчик/маркер.
Триггер: process_player_action через ключевые слова (без UI, без автотриггера).
"""
import random

# ─────────────────────────────────────────────────────────────
# 1. «Слово директора» — Корпоративный блок (1/сессия)
#    Переброс проваленного negotiation/diplomacy/bureaucracy.
#    context: {"failed_skill": str, "last_dice_result": dict}
def _word_of_director(engine, ctx):
    ch = engine.state.character
    skill = ctx.get("skill_id") or "negotiation"
    dc = int(ctx.get("dc", 10))
    av = ch.get("attributes", {}).get("charisma", 5)
    sv = ch.get("skills", {}).get(skill, 0)
    result = engine.dice.skill_check(sv, av, dc)
    result["skill"] = skill
    ok = bool(result["success"])
    return {
        "text": (f"🗣 Слово директора: вы бросаете весь вес корпоративной репутации на стол. "
                 f"Бросок {result['rolls']} → {'успех' if ok else 'и это не спасает'} "
                 f"(margin {result['margin']:+d})."),
        "reroll_result": result,
        "success": ok,
    }

# ─────────────────────────────────────────────────────────────
# 2. «Пилотаж» — Пилотский корпус (1 бой или −25% travel)
def _pilot_maneuver(engine, ctx):
    if ctx.get("in_combat"):
        return {"text": "✈ Пилотаж: +3 к первому piloting/evasion броску этого боя.",
                "combat_buff": {"piloting": 3, "evasion": 3}}
    travel_min = int(ctx.get("travel_minutes", 0))
    if travel_min > 0:
        saved = max(5, travel_min // 4)
        return {"text": f"✈ Пилотаж: срезали маршрут — время полёта сокращено на {saved} мин.",
                "travel_reduction": saved}
    return None

# ─────────────────────────────────────────────────────────────
# 3. «Бэкдор» — Кибер-блок (1 взлом/сессия, −2 DC)
def _backdoor(engine, ctx):
    # Фаза 20d: dc_override СОХРАНЯЕТСЯ в state и применяется к следующему хакинг-чеку
    engine.state.backdoor_dc_override = max(2, int(ctx.get("dc", 10)) - 2)
    new_dc = engine.state.backdoor_dc_override
    return {"text": f"🔓 Бэкдор: заранее встроенный лаз снижает сложность следующего взлома DC→{new_dc}.",
            "dc_override": new_dc}

# ─────────────────────────────────────────────────────────────
# 4. «Стальные руки» — Медицинский блок (1/бой подъём; вне боя лечение)
def _steel_hands(engine, ctx):
    ch = engine.state.character
    sv = ch.get("skills", {}).get("medicine", 0)
    av = ch.get("attributes", {}).get("intelligence", 5)
    heal = sum([random.randint(1, 6) for _ in range(2)]) + sv // 2
    if ctx.get("ally_down"):
        target = ctx.get("target_name", "союзник")
        return {"text": f"💉 Стальные руки: {target} поднят с нуля ({heal} HP).",
                "revive_hp": min(heal, 10)}
    return {"text": f"💉 Стальные руки: полевая медицина восстановила {heal} HP.",
            "heal": heal}

# ─────────────────────────────────────────────────────────────
# 5. «Импровизация» — Инженерный блок (1/сессия, одноразовый предмет)
def _improvise(engine, ctx):
    roll = random.randint(1, 6) + random.randint(1, 6)
    item = "Одноразовая хитрая штуковина" if roll >= 7 else "Хлипкая самоделка"
    quality = "работает как надо" if roll >= 7 else "сработает... наверное, один раз"
    return {"text": f"🔧 Импровизация: собран «{item}» ({quality}).",
            "grant_item": {"name": item, "qty": 1, "type": "equipment",
                           "_single_use": True}}

# ─────────────────────────────────────────────────────────────
# 6. «Слепая зона» — Разведка (1/сессия, автоуспех наблюдения)
def _blind_spot(engine, ctx):
    loc = ctx.get("location_name") or engine.state.current_location.get("district", "текущая локация")
    return {"text": (f"👁 Слепая зона: вы читаете {loc} как открытую книгу — "
                     f"патрули, слепые углы, кто куда ходит."),
            "auto_observe": True}

# ─────────────────────────────────────────────────────────────
# 7. «Обещание» — Дипломатический корпус (1/переговоры, +4 и долг)
def _promise(engine, ctx):
    return {"text": "🤝 Обещание: вы даёте слово — и оно работает (+4 к чеку). "
                    "Теперь за вами должок.",
            "check_bonus": 4,
            "narrative_debt": "обещание влиятельной стороне"}

# ─────────────────────────────────────────────────────────────
# 8. «Второе дыхание» — Выживальщики (advantage на survival-чеке)
def _second_wind(engine, ctx):
    sv = engine.state.character.get("skills", {}).get(ctx.get("skill_id", "survival"), 0)
    av = engine.state.character.get("attributes", {}).get("endurance", 5)
    bonus = sv + (av - 4) // 2
    r1 = [random.randint(1, 6), random.randint(1, 6)]
    r2 = [random.randint(1, 6), random.randint(1, 6)]
    best = max(sum(r1), sum(r2))
    total = best + bonus
    return {"text": f"🌿 Второе дыхание: две пары костей {[sum(r1), sum(r2)]} → берёте лучшую "
                    f"({best}) +{bonus} = {total}.",
            "rolls_total": total, "bonus_used": bonus}

# ─────────────────────────────────────────────────────────────
# 9. «Тёмная сделка» — Криминальный синдикат (+3 чек, heat+1)
def _dark_deal(engine, ctx):
    heat = engine.state.character.get("heat", 0)
    engine.state.character["heat"] = heat + 1
    return {"text": f"🕶 Тёмная сделка: нужные люди вспомнили нужные слова (+3 к чеку). "
                    f"Слухи расходятся: Heat +1 (теперь {heat+1}).",
            "check_bonus": 3, "heat_gain": 1}

# ─────────────────────────────────────────────────────────────
# 10. «Озарение» — Научный консилиум (честный ответ ГМа по KB)
def _insight(engine, ctx):
    topic = ctx.get("topic") or "предмет вашего исследования"
    kb_ctx = ""
    try:
        kb_ctx = engine.kb.get_relevant_context(topic, max_tokens=400)
    except Exception:
        pass
    found = bool(kb_ctx.strip())
    return {"text": ("💡 Озарение: сопоставив факты, вы вспоминаете важное "
                     "(ГМ получает релевантный контекст по теме).")
                     if found else
            "💡 Озарение: данных в ваших архивах нет — тема остаётся тёмной.",
            "kb_context": kb_ctx[:1200] if found else "", "kb_found": found}

# ─────────────────────────────────────────────────────────────
# 11. «Строй» — Военный устав (союзники +2, сам −1)
def _formation(engine, ctx):
    n_allies = len(ctx.get("allies") or [])
    if n_allies == 0:
        return None  # некого координировать
    return {"text": f"🛡 Строй: вы координируете {n_allies} союзник(ов) — их следующая атака +2, "
                    f"ваша −1 (вы заняты командованием).",
            "allies_buff": 2, "self_penalty": 1}

# ─────────────────────────────────────────────────────────────
# 12. «Публика» — Артисты/медиа (DC14 → толпа как ресурс)
def _the_crowd(engine, ctx):
    ch = engine.state.character
    sv = max(ch.get("skills", {}).get("performance", 0),
             ch.get("skills", {}).get("public_speaking", 0))
    av = ch.get("attributes", {}).get("charisma", 5)
    result = engine.dice.skill_check(sv, av, 14)
    ok = bool(result["success"])
    return {"text": (f"🎭 Публика: зал ваш! Толпа готова отвлечь, внушить или укрыть "
                     f"(бросок {result['rolls']}, margin {result['margin']:+d}).")
                     if ok else
            f"🎭 Публика: выступление сорвалось аплодисментами зевак — толпа разошлась "
            f"(бросок {result['rolls']}).",
            "crowd_resource": ok}

# ═════════════════════════════════════════════════════════════
# РЕЕСТР: ability_id → параметры. cooldown = использований за сессию (1).
ABILITY_REGISTRY = {
    "word_of_director": {"name": "Слово директора",   "family": "Корпоративный блок",
                         "cooldown": 1, "keywords": ["слово директора"],
                         "fn": _word_of_director},
    "pilot_maneuver":   {"name": "Пилотаж",           "family": "Пилотский корпус",
                         "cooldown": 1, "keywords": ["пилотаж", "маневр пилотаж"],
                         "fn": _pilot_maneuver},
    "backdoor":         {"name": "Бэкдор",             "family": "Кибер-блок",
                         "cooldown": 1, "keywords": ["бэкдор", "backdoor"],
                         "fn": _backdoor},
    "steel_hands":      {"name": "Стальные руки",      "family": "Медицинский блок",
                         "cooldown": 1, "keywords": ["стальные руки", "подними раненого"],
                         "fn": _steel_hands},
    "improvise":        {"name": "Импровизация",       "family": "Инженерный блок",
                         "cooldown": 1, "keywords": ["импровизиру", "смастери"],
                         "fn": _improvise},
    "blind_spot":       {"name": "Слепая зона",        "family": "Разведка",
                         "cooldown": 1, "keywords": ["слепая зона", "читаю локацию"],
                         "fn": _blind_spot},
    "promise":          {"name": "Обещание",           "family": "Дипломатический корпус",
                         "cooldown": 1, "keywords": ["даю обещание", "слово офицера"],
                         "fn": _promise},
    "second_wind":      {"name": "Второе дыхание",     "family": "Выживальщики",
                         "cooldown": 1, "keywords": ["второе дыхание"],
                         "fn": _second_wind},
    "dark_deal":        {"name": "Тёмная сделка",      "family": "Криминальный синдикат",
                         "cooldown": 1, "keywords": ["тёмная сделка","темная сделка","тёмную сделку"],
                         "fn": _dark_deal},
    "insight":          {"name": "Озарение",           "family": "Научный консилиум",
                         "cooldown": 1, "keywords": ["озарение"],
                         "fn": _insight},
    "formation":        {"name": "Строй",              "family": "Военный устав",
                         "cooldown": 1, "keywords": ["строй", "координируй отряд"],
                         "fn": _formation},
    "the_crowd":        {"name": "Публика",            "family": "Артисты/медиа",
                         "cooldown": 1, "keywords": ["к публике", "выступлю перед толпой"],
                         "fn": _the_crowd},
}


class ProfessionAbilityManager:
    """Диспетчер активных способностей. Cooldown per session через GameState."""

    def __init__(self):
        self.registry = ABILITY_REGISTRY

    def detect(self, action: str):
        """Найти способность по ключевым словам. Возвращает ability_id или None."""
        a = (action or "").lower()
        for aid, spec in self.registry.items():
            if any(kw in a for kw in spec["keywords"]):
                return aid
        return None

    def check_cooldown(self, state, ability_id: str) -> bool:
        """True = способность доступна (не использована в этой сессии)."""
        used = getattr(state, "ability_used", None)
        if used is None:
            used = {}
            setattr(state, "ability_used", used)
        return ability_id not in used

    def mark_used(self, state, ability_id: str):
        used = getattr(state, "ability_used", None)
        if used is None:
            used = {}
            setattr(state, "ability_used", used)
        used[ability_id] = True

    def execute(self, engine, ability_id: str, ctx: dict):
        """Выполнить способность с проверкой cooldown. Возвращает результат или ошибку."""
        spec = self.registry.get(ability_id)
        if not spec:
            return {"error": f"Неизвестная способность: {ability_id}"}
        if not self.check_cooldown(engine.state, ability_id):
            return {"text": f"⚠ «{spec['name']}» уже использована в этой сессии.",
                    "on_cooldown": True}
        result = spec["fn"](engine, ctx or {})
        if result is None:
            # условие не выполнено — cooldown не тратится
            return {"text": f"«{spec['name']}»: сейчас не к чему применить.",
                    "not_applicable": True}
        self.mark_used(engine.state, ability_id)
        result["ability"] = ability_id
        result["ability_name"] = spec["name"]
        result["family"] = spec["family"]
        # Фаза 20d: применение материальных эффектов к состоянию
        gi = result.get("grant_item")
        if gi:
            engine.state.inventory.append({"name": gi["name"], "qty": gi.get("qty", 1),
                                           "type": gi.get("type", "equipment"),
                                           "_single_use": gi.get("_single_use", False)})
            result["item_added_to_inventory"] = True
        heal = result.get("heal")
        if heal:
            ch = engine.state.character
            max_hp = ch.get("max_hp", 50) if isinstance(ch, dict) else 50
            cur = (ch.get("current_hp") if isinstance(ch, dict) else None) or max_hp
            ch["current_hp"] = min(max_hp, cur + heal)
            result["hp_after"] = ch["current_hp"]
        return result
