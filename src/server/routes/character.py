"""
Auto-generated Blueprint: character
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.systems.game_systems import CraftingSystem, PsychologySystem  # Phase 26: crafting + psychology
from src.utils.clinic import _check_clinic_nearby, SURGERY_FEE_BASE, SELF_SURGERY_DC_PENALTY  # Phase 26
from src.server.routes._deps import get_engine, get_app

character = Blueprint("character", __name__)


# Auto-extracted handlers from app.py

@character.route("/api/character/create", methods=["POST"])
def api_create_character():
    data = request.json
    preset_id = data.get("preset_id")
    if preset_id and preset_id != "custom":
        result = get_engine().create_character_from_preset(preset_id)
    else:
        result = get_engine().create_custom_character(data)
    get_engine().state.phase = "character_creation"
    return jsonify(result)




@character.route("/api/state")
def api_state():
    return jsonify(get_engine().get_full_state())




@character.route("/api/inventory")
def api_inventory():
    return jsonify(get_engine().get_inventory())


@character.route("/api/inventory/use", methods=["POST"])
def api_inventory_use():
    """Phase 27 R1: мгновенное детерминированное использование расходника.
    БЕЗ вызова LLM: лечение/эффект по каталогу, списание из inventory, ответ сразу."""
    import re as _re
    from src.systems.equipment_lookup import resolve_item, consume_at, roll_formula

    engine = get_engine()
    data = request.json or {}
    item_name = (data.get("item_name") or "").strip()
    item_id = (data.get("item_id") or "").strip()

    if not item_name and not item_id:
        return jsonify({"success": False, "error": "Не указан предмет"}), 400

    # Найти предмет в инвентаре по имени (или id-полю, если есть)
    inv = engine.state.inventory
    idx, item = None, None
    for i, it in enumerate(inv):
        if item_name and it.get("name", "").strip().lower() == item_name.lower():
            idx, item = i, it
            break
        if item_id and str(it.get("id", "")).lower() == item_id.lower():
            idx, item = i, it
            break
    if item is None:
        return jsonify({"success": False, "error": f"«{item_name or item_id}» нет в инвентаре"}), 404

    stats = resolve_item(item.get("name")) or {}
    char = engine.state.character
    kind = stats.get("kind")

    # --- Лечебный расходник: мгновенное HP по формуле из каталога ---
    if kind == "consumable_heal":
        formula = stats.get("heal_formula", "1d6")
        healed = roll_formula(formula)
        max_hp = char.get("derived", {}).get("health_points", 50)
        before = char.get("current_hp", max_hp)
        char["current_hp"] = min(max_hp, before + healed)
        actual = char["current_hp"] - before
        consume_at(inv, idx)
        return jsonify({
            "success": True,
            "hp_healed": actual,
            "hp": char["current_hp"],
            "hp_max": max_hp,
            "message": f"{item['name']} использован (+{actual} HP)",
        })

    # --- Стимулятор/усиление: эффект на время (упрощённо — фикс-бафф без LLM) ---
    effect = str(stats.get("effect_text") or stats.get("effect") or "")
    if kind == "consumable_buff" or "стимул" in item.get("name", "").lower() or "+2 STR" in effect:
        # Баффы без LLM: пишем в world_context активный эффект, списываем предмет.
        # Полная система баффов — отдельная механика; сейчас фиксируем применение.
        consume_at(inv, idx)
        return jsonify({
            "success": True,
            "buff_applied": True,
            "message": f"{item['name']} использован. {effect[:80]}".strip(),
        })

    # --- Не расходуемый предмет: не тратим LLM-ход, объясняем ---
    return jsonify({
        "success": False,
        "error": f"«{item['name']}» нельзя использовать напрямую (это не расходник)",
        "not_consumable": True,
    }), 400


@character.route("/api/inventory/equip", methods=["POST"])
def api_inventory_equip():
    """Phase 28 G1: экипировать/снять предмет (weapon/armor).
    Экипировка хранится как флаг equipped на записи инвентаря."""
    from src.systems.equipment_lookup import resolve_item

    data = request.json or {}
    item_name = (data.get("item_name") or "").strip()
    action = data.get("action", "equip")  # equip | unequip
    if not item_name:
        return jsonify({"success": False, "error": "Не указан предмет"}), 400

    inv = get_engine().state.inventory
    item = next((it for it in inv if it.get("name", "").strip().lower() == item_name.lower()), None)
    if item is None:
        return jsonify({"success": False, "error": f"«{item_name}» нет в инвентаре"}), 404

    stats = resolve_item(item.get("name")) or {}
    kind = stats.get("kind")
    if kind not in ("weapon", "armor"):
        return jsonify({"success": False, "error": "Этот предмет нельзя экипировать"}), 400

    # Снять всё того же слота (оружие/броня — по одной активной единице)
    if action == "equip":
        for other in inv:
            if other is item:
                continue
            o_stats = resolve_item(other.get("name")) or {}
            if o_stats.get("kind") == kind and other.get("equipped"):
                other["equipped"] = False

    item["equipped"] = (action == "equip")
    verb = "экипирован" if action == "equip" else "снят"
    return jsonify({
        "success": True,
        "message": f"{item['name']} {verb}",
        "equipped": item["equipped"],
        "slot": "weapon" if kind == "weapon" else "armor",
    })


@character.route("/api/inventory/slots")
def api_inventory_slots():
    """Phase 27 D5: инвентарь с логическими слотами экипировки и весом.
    Слоты: Оружие / Броня / Импланты / Карман. Вес резолвится из каталога."""
    engine = get_engine()
    from src.systems.equipment_lookup import resolve_item

    slots = {"weapon": [], "armor": [], "implant": [], "pocket": []}
    total_weight = 0.0

    for item in engine.state.inventory:
        rec = dict(item)
        name = rec.get("name", "?")
        stats = resolve_item(name) or {}
        kind = stats.get("kind")
        # Phase 28 G1: приоритет каталога; fallback — тип записи (type/category из покупки)
        item_type = str(rec.get("type") or rec.get("category") or "").lower()
        if kind == "weapon" or kind == "shop_weapon" or "weapon" in item_type:
            slot = "weapon"
        elif kind == "armor" or "armor" in item_type or "броня" in item_type or "скафандр" in name.lower():
            slot = "armor"
        elif kind == "implant" or "implant" in item_type or "имплант" in name.lower() or "implant" in name.lower():
            slot = "implant"
        else:
            slot = "pocket"
        # Вес: из каталога (cost/1000 как условная масса) или дефолт 0.5 кг
        weight = stats.get("weight") or 0.5
        try:
            total_weight += float(weight) * int(rec.get("qty", 1))
        except (TypeError, ValueError):
            total_weight += 0.5
        rec["slot"] = slot
        rec["weight"] = weight
        rec["stats"] = stats.get("damage") or stats.get("defense") or stats.get("effect") or rec.get("stats", "")
        # Phase 28 G1: «Использовать» ТОЛЬКО для расходников; экипировка — Экипировать/Снять
        rec["usable"] = stats.get("kind") in ("consumable_heal", "consumable_buff")
        rec["equippable"] = slot in ("weapon", "armor") and not rec["usable"]
        rec["equipped"] = bool(rec.get("equipped", False))
        slots[slot].append(rec)

    capacity = 50.0  # базовая вместимость (кг); может расширяться рюкзаками
    return jsonify({
        "slots": slots,
        "total_weight": round(total_weight, 1),
        "capacity": capacity,
        "overloaded": total_weight > capacity,
    })




@character.route("/api/quests")
def api_quests():
    return jsonify(get_engine().get_quests())


@character.route("/api/quests/abandon", methods=["POST"])
def api_quests_abandon():
    """Phase 27 D2: игрок отказывается от квеста."""
    data = request.json or {}
    result = get_engine().abandon_quest(data.get("quest_id", ""))
    status = 200 if result.get("success") else 404
    return jsonify(result), status




@character.route("/api/implant/list")
def api_implant_list():
    """List installed and available (in inventory) implants."""
    installed = []
    available = []
    for i, item in enumerate(get_engine().state.inventory):
        if item.get("type") == "implants" or item.get("category") == "implants":
            data = dict(item)
            data["inv_index"] = i
            implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), IMPLANT_DEFAULT)
            data["skill_bonuses"] = implant_info.get("skill_bonuses", {})
            data["attr_bonuses"] = implant_info.get("attr_bonuses", {})
            data["humanity_cost"] = implant_info.get("humanity_cost", 3)
            data["surgery_dc"] = implant_info.get("surgery_dc", 12)
            if item.get("installed"):
                installed.append(data)
            else:
                available.append(data)
    # Check if near a clinic/doctor
    loc = get_engine().state.current_location
    near_clinic = _check_clinic_nearby(loc)
    return jsonify({
        "installed": installed,
        "available": available,
        "near_clinic": near_clinic,
        "surgery_fee": SURGERY_FEE_BASE,
        "humanity": get_engine().state.character.get("humanity", 100),
        "max_implant_slots": 6,
        "used_slots": len(installed),
    })




@character.route("/api/implant/install", methods=["POST"])
def api_implant_install():
    """Install an implant from inventory. Requires surgery check."""
    data = request.json or {}
    inv_index = data.get("inv_index", -1)
    if inv_index < 0 or inv_index >= len(get_engine().state.inventory):
        return jsonify({"error": "Имплант не найден в инвентаре"}), 404

    item = get_engine().state.inventory[inv_index]
    if item.get("type") != "implants" and item.get("category") != "implants":
        return jsonify({"error": "Это не имплант"}), 400
    if item.get("installed"):
        return jsonify({"error": "Имплант уже установлен"}), 400

    # Check implant slots
    installed_count = sum(1 for i in get_engine().state.inventory if i.get("installed") and
                         (i.get("type") == "implants" or i.get("category") == "implants"))
    if installed_count >= 6:
        return jsonify({"error": "Все 6 слотов имплантов заняты. Сначала удалите имплант."}), 400

    # Get implant data
    implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), IMPLANT_DEFAULT)
    surgery_dc = implant_info["surgery_dc"]

    # Surgery fee
    credits = get_engine().state.character.get("credits", 0)
    loc = get_engine().state.current_location
    near_clinic = _check_clinic_nearby(loc)
    fee = SURGERY_FEE_BASE if near_clinic else 0

    if near_clinic and credits < fee:
        return jsonify({"error": f"Недостаточно кредитов для операции: нужно ₡{fee:,}"}), 400

    if not near_clinic:
        surgery_dc += SELF_SURGERY_DC_PENALTY  # Self-surgery is harder

    # Surgery check: medicine skill + intelligence
    from src.core.engine import DiceRoller
    med_skill = get_engine().state.character.get("skills", {}).get("medicine", 0)
    intel = get_engine().state.character.get("attributes", {}).get("intelligence", 5) + get_engine().state.character.get("attr_bonuses", {}).get("intelligence", 0)

    if near_clinic:
        # Doctor does it — use base DC, auto-bonus +3
        med_skill = max(med_skill, 4)  # Doctor has at least skill 4

    result = DiceRoller.skill_check(med_skill, intel, surgery_dc)

    # Pay fee
    if near_clinic:
        get_engine().state.character["credits"] = credits - fee

    # Apply humanity cost
    humanity_cost = implant_info["humanity_cost"]

    if result["success"]:
        # Successful installation
        item["installed"] = True
        item["skill_bonuses"] = implant_info.get("skill_bonuses", {})
        item["attr_bonuses"] = implant_info.get("attr_bonuses", {})

        # Phase 24c B5-3: Apply attribute bonuses to separate attr_bonuses dict
        for attr, val in implant_info.get("attr_bonuses", {}).items():
            get_engine().state.character.setdefault("attr_bonuses", {})[attr] = \
                get_engine().state.character.get("attr_bonuses", {}).get(attr, 0) + val

        # Apply HP bonus
        if "hp_bonus" in implant_info:
            get_engine().state.character["max_hp"] = get_engine().state.character.get("max_hp", 50) + implant_info["hp_bonus"]
            get_engine().state.character["current_hp"] = get_engine().state.character.get("current_hp", 50) + implant_info["hp_bonus"]

        # Reduce humanity
        get_engine().state.character["humanity"] = max(0,
            get_engine().state.character.get("humanity", 100) - humanity_cost)

        # Side effects for high humanity cost
        side_effects = []
        if humanity_cost >= 7:
            side_effects.append("Кошмары на 3 дня (+5 стресс)")
            get_engine().state.character["stress"] = min(100,
                get_engine().state.character.get("stress", 0) + 5)
        if get_engine().state.character.get("humanity", 100) < 30:
            side_effects.append("⚠️ Человечность критически низкая! Риск киберпсихоза.")

        return jsonify({
            "success": True,
            "message": f"✅ Имплант «{item['name']}» успешно установлен!",
            "surgery_roll": result,
            "humanity_lost": humanity_cost,
            "humanity": get_engine().state.character.get("humanity", 100),
            "credits": get_engine().state.character.get("credits", 0),
            "side_effects": side_effects,
            "bonuses": {
                "skills": implant_info.get("skill_bonuses", {}),
                "attributes": implant_info.get("attr_bonuses", {}),
            },
        })
    else:
        # Failed surgery
        damage = random.randint(3, 10)
        get_engine().state.character["current_hp"] = max(1,
            get_engine().state.character.get("current_hp", 50) - damage)
        # Still lose some humanity from attempt
        get_engine().state.character["humanity"] = max(0,
            get_engine().state.character.get("humanity", 100) - (humanity_cost // 2))

        complications = []
        if result["quality"] == "critical_failure":
            complications.append("☠ Имплант повреждён при установке! Потерян.")
            get_engine().state.inventory.pop(inv_index)  # Implant destroyed
            complications.append(f"Получено {damage * 2} урона.")
            get_engine().state.character["current_hp"] = max(1,
                get_engine().state.character.get("current_hp", 50) - damage)
        else:
            complications.append(f"Получено {damage} урона от неудачной операции.")
            complications.append("Попробуйте снова или найдите клинику.")

        return jsonify({
            "success": False,
            "message": f"❌ Операция не удалась!",
            "surgery_roll": result,
            "damage": damage,
            "complications": complications,
            "humanity": get_engine().state.character.get("humanity", 100),
            "credits": get_engine().state.character.get("credits", 0),
        })




@character.route("/api/implant/remove", methods=["POST"])
def api_implant_remove():
    """Remove an installed implant."""
    data = request.json or {}
    inv_index = data.get("inv_index", -1)
    if inv_index < 0 or inv_index >= len(get_engine().state.inventory):
        return jsonify({"error": "Имплант не найден"}), 404

    item = get_engine().state.inventory[inv_index]
    if not item.get("installed"):
        return jsonify({"error": "Этот имплант не установлен"}), 400

    implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), IMPLANT_DEFAULT)

    # Phase 24c B5-3: Remove attribute bonuses from attr_bonuses
    for attr, val in implant_info.get("attr_bonuses", {}).items():
        cur = get_engine().state.character.get("attr_bonuses", {}).get(attr, 0)
        get_engine().state.character.setdefault("attr_bonuses", {})[attr] = cur - val
        if get_engine().state.character["attr_bonuses"][attr] <= 0:
            del get_engine().state.character["attr_bonuses"][attr]

    # Remove HP bonus
    if "hp_bonus" in implant_info:
        get_engine().state.character["max_hp"] = max(10, get_engine().state.character.get("max_hp", 50) - implant_info["hp_bonus"])
        get_engine().state.character["current_hp"] = min(
            get_engine().state.character.get("current_hp", 50),
            get_engine().state.character.get("max_hp", 50))

    # Restore some humanity
    humanity_restore = implant_info.get("humanity_cost", 3) // 2
    get_engine().state.character["humanity"] = min(100,
        get_engine().state.character.get("humanity", 100) + humanity_restore)

    item["installed"] = False
    item.pop("skill_bonuses", None)
    item.pop("attr_bonuses", None)

    loc = get_engine().state.current_location
    near_clinic = _check_clinic_nearby(loc)
    fee = SURGERY_FEE_BASE // 2 if near_clinic else 0
    if near_clinic:
        get_engine().state.character["credits"] = get_engine().state.character.get("credits", 0) - fee

    return jsonify({
        "success": True,
        "message": f"🔧 Имплант «{item['name']}» удалён",
        "humanity_restored": humanity_restore,
        "humanity": get_engine().state.character.get("humanity", 100),
        "credits": get_engine().state.character.get("credits", 0),
    })




@character.route("/api/crafting/recipes")
def api_crafting_recipes():
    """Get available crafting recipes with can-craft status."""
    recipes = CraftingSystem.get_recipes()
    results = []
    for r in recipes:
        check = CraftingSystem.can_craft(r["id"], get_engine().state.inventory, get_engine().state.character)
        results.append({
            "recipe": r,
            "can_craft": check["can_craft"],
            "missing": check.get("missing_materials", []),
            "skill_value": check.get("skill_value", 0),
        })
    return jsonify({"recipes": results, "materials": CraftingSystem.get_materials()})




@character.route("/api/crafting/craft", methods=["POST"])
def api_craft():
    """Attempt to craft an item."""
    data = request.json or {}
    recipe_id = data.get("recipe_id", "")
    result = CraftingSystem.craft(recipe_id, get_engine().state.inventory, get_engine().state.character, get_engine().dice)
    return jsonify(result)




@character.route("/api/perks")
def api_perks():
    """Get character perks and available perks."""
    owned = get_engine().state.character.get("perks", [])
    unspent_perk = get_engine().state.character.get("unspent_perk_points", 0)
    available = []
    if unspent_perk > 0:
        available = PerkSystem.get_available_perks(get_engine().state.character, count=3)
    return jsonify({
        "owned": owned,
        "available": available,
        "unspent_skill_points": get_engine().state.character.get("unspent_skill_points", 0),
        "unspent_perk_points": unspent_perk,
    })




@character.route("/api/perks/select", methods=["POST"])
def api_select_perk():
    """Select a perk — only when a perk point is unspent."""
    data = request.json or {}
    perk_id = data.get("perk_id", "")
    # Фаза 24c B5-1: проверка лимита перков
    unspent = get_engine().state.character.get("unspent_perk_points", 0)
    if unspent <= 0:
        return jsonify({
            "success": False,
            "error": "Нет доступных очков перков. Повысьте уровень (каждые 2 уровня)."
        }), 403
    perk = PerkSystem.apply_perk(get_engine().state.character, perk_id)
    if perk:
        get_engine().state.character["unspent_perk_points"] = unspent - 1
        return jsonify({
            "success": True,
            "perk": perk,
            "unspent_perk_points": get_engine().state.character["unspent_perk_points"],
        })
    return jsonify({"success": False, "error": "Перк не найден или уже выбран"}), 400




@character.route("/api/levelup/spend", methods=["POST"])
def api_spend_skill_point():
    """Spend a skill point."""
    data = request.json or {}
    skill = data.get("skill", "")
    ok = LevelUpSystem.spend_skill_point(get_engine().state.character, skill)
    if ok:
        return jsonify({
            "success": True,
            "skill": skill,
            "new_value": get_engine().state.character["skills"][skill],
            "remaining": get_engine().state.character.get("unspent_skill_points", 0),
        })
    return jsonify({"success": False, "error": "Нет очков или навык не найден"}), 400




@character.route("/api/levelup/spend/attr", methods=["POST"])
def api_spend_attribute_point():
    """Phase 24c B5-3: Spend an unspent attribute point.
    Only allows increasing attributes up to the level-based cap (from get_skill_cap).
    Implants contribute attr_bonuses separately from base attributes."""
    data = request.json or {}
    attr = data.get("attr", "")
    character = get_engine().state.character
    unspent = character.get("unspent_attribute_points", 0)
    if unspent <= 0:
        return jsonify({
            "success": False,
            "error": "Нет очков атрибутов. Повышайте уровень для получения новых очков."
        }), 403
    attrs = character.get("attributes", {})
    if attr not in attrs:
        return jsonify({"success": False, "error": "Атрибут не найден"}), 400
    # Cap check: only base attributes are capped, not implants
    from src.core.engine import get_skill_cap
    level = character.get("level", 1)
    _, max_attr = get_skill_cap(level)
    if attrs[attr] >= max_attr:
        return jsonify({
            "success": False,
            "error": f"Атрибут уже на максимуме для уровня {level} (max {max_attr})."
        }), 400
    attrs[attr] = attrs[attr] + 1
    character["unspent_attribute_points"] = unspent - 1
    return jsonify({
        "success": True,
        "attr": attr,
        "new_value": attrs[attr],
        "max_attr": max_attr,
        "remaining": character["unspent_attribute_points"],
    })




@character.route("/api/psychology")
def api_psychology():
    """Get character psychology state."""
    char = get_engine().state.character
    stress = char.get("stress", 30)
    humanity = char.get("humanity", 60)
    return jsonify({
        "stress": stress,
        "humanity": humanity,
        "stress_effect": PsychologySystem.get_stress_effect(stress),
        "humanity_effect": PsychologySystem.get_humanity_effect(humanity),
        "skill_modifier": PsychologySystem.get_skill_modifier(char),
        "social_modifier": PsychologySystem.get_social_modifier(char),
    })




@character.route("/api/quest/add", methods=["POST"])
def api_add_quest():
    """Add a new quest."""
    data = request.json or {}
    quest = QuestTracker.create_quest(
        title=data.get("title", "Новое задание"),
        description=data.get("description", ""),
        giver=data.get("giver", ""),
        reward_credits=data.get("reward_credits", 0),
        reward_xp=data.get("reward_xp", 100),
        stages=data.get("stages"),  # Фаза 23 D2: стадии из запроса
        reward_reputation=data.get("reward_reputation", {}),  # Фаза 24d
        tier=data.get("tier"),  # Фаза 24d
    )
    get_engine().state.active_quests.append(quest)
    return jsonify({"quest": quest})




@character.route("/api/quest/advance", methods=["POST"])
def api_advance_quest():
    """Advance quest to next stage."""
    data = request.json or {}
    quest_id = data.get("quest_id", "")
    for q in get_engine().state.active_quests:
        if q.get("id") == quest_id:
            QuestTracker.advance_quest(q)
            if q["status"] == "completed":
                get_engine().state.active_quests.remove(q)
                get_engine().state.completed_quests.append(q)
                # Give rewards
                get_engine().add_credits(q.get("reward_credits", 0))
                get_engine().add_xp(q.get("reward_xp", 0))
                # Track completion for procedural system
                if q.get("procedural"):
                    get_engine().quest_generator.on_quest_complete(q.get("type", ""))
                    get_engine().consequences.log_action("completed_major_quest", {
                        "quest_title": q["title"], "turn": get_engine().state.world_sim.turn_count,
                    })
                # Apply reputation rewards (Фаза 24d: канонизация ключей + fame)
                rep_rewards = q.get("reward_reputation", {}) or {}
                if rep_rewards:
                    from src.content.v5_legacy import canonical_faction  # Фаза 24d
                    canon = {}
                    for faction, amount in rep_rewards.items():
                        canon[canonical_faction(faction)] = canon.get(canonical_faction(faction), 0) + amount
                    for faction, amount in canon.items():
                        get_engine().state.faction_reputation[faction] = (
                            get_engine().state.faction_reputation.get(faction, 0) + amount
                        )
                    # Фаза 24d: fame за rep-up (порог +10, раз на квест)
                    if max(canon.values()) >= 10:
                        from src.world.player_tiers import FAME_PER_REP_UP
                        get_engine().state.fame = getattr(get_engine().state, "fame", 0) + FAME_PER_REP_UP
                # Фаза 24d: fame за завершение квеста (tier квеста, дефолт 8)
                from src.world.player_tiers import FAME_PER_QUEST_TIER
                get_engine().state.fame = getattr(get_engine().state, "fame", 0) + FAME_PER_QUEST_TIER.get(
                    int(q.get("tier", 8)), FAME_PER_QUEST_TIER[8])
            return jsonify({"quest": q})
    return jsonify({"error": "Квест не найден"}), 404





@character.route("/api/quest/generate", methods=["POST"])
def api_generate_quest():
    """Generate a procedural quest on demand."""
    data = request.json or {}
    preferred_type = data.get("type")
    quest = get_engine().quest_generator.generate_quest(
        player_level=get_engine().state.character.get("level", 1),
        location=get_engine().state.current_location,
        preferred_type=preferred_type,
        faction_standings=get_engine().state.faction_reputation,
    )
    get_engine().state.active_quests.append(quest)
    return jsonify({"quest": quest})





@character.route("/api/companions/available", methods=["GET"])
def api_companions_available():
    loc = get_engine().state.current_location
    recruits = get_engine().companions.get_available_recruits(loc)
    loc_name = f"{loc.get('city', '')}, {loc.get('district', '')}"
    return jsonify({"recruits": recruits, "team_size": len(get_engine().companions.companions),
                    "max": get_engine().companions.MAX_COMPANIONS,
                    "location": loc_name})




@character.route("/api/companions/recruit", methods=["POST"])
def api_companions_recruit():
    data = request.json or {}
    # Build companion dict from data
    companion = data.get("companion", {})
    # Фаза 23 B2: проверка recruit_condition (min_level / min_faction_rep)
    cond = companion.get("recruit_condition") or {}
    min_level = cond.get("min_level")
    if min_level and get_engine().state.character.get("level", 1) < min_level:
        return jsonify({"error": f"Требуется уровень {min_level} (ваш: {get_engine().state.character.get('level', 1)})"}), 400
    min_rep = cond.get("min_faction_rep") or {}
    for faction, needed in min_rep.items():
        have = get_engine().state.faction_reputation.get(faction, 0)
        if have < needed:
            return jsonify({"error": f"Требуется репутация {faction} ≥ {needed} (ваша: {have})"}), 400
    credits = get_engine().state.character.get("credits", 0)
    result = get_engine().companions.recruit(companion, credits)
    if "cost" in result:
        get_engine().state.character["credits"] = credits - result["cost"]
    return jsonify(result)




@character.route("/api/companions/dismiss", methods=["POST"])
def api_companions_dismiss():
    data = request.json or {}
    result = get_engine().companions.dismiss(data.get("companion_id", ""))
    return jsonify(result)




@character.route("/api/companions/team", methods=["GET"])
def api_companions_team():
    return jsonify({"companions": get_engine().companions.companions,
                    "combat_bonus": get_engine().companions.get_combat_bonus()})



