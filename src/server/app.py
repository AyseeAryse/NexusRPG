"""
AI RPG Server - Flask web application.
"""
import json
import os
import random
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from src.core.engine import GameEngine
from src.systems.game_systems import (QuestTracker, FactionSystem, PsychologySystem,
                                      PerkSystem, LevelUpSystem, CraftingSystem,
                                      LocationEvents)
from src import config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)

import logging, traceback
logging.basicConfig(filename="server_errors.log", level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler — catch all unhandled exceptions."""
    tb = traceback.format_exc()
    logging.error(f"Unhandled exception: {e}\n{tb}")
    # Return JSON for API routes, HTML for pages
    if request.path.startswith("/api/"):
        return jsonify({"error": f"Внутренняя ошибка сервера: {type(e).__name__}: {str(e)[:200]}"}), 500
    return f"<h1>500 Internal Server Error</h1><pre>{type(e).__name__}: {str(e)[:200]}</pre>", 500

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": f"Маршрут не найден: {request.path}"}), 404
    return render_template("index.html")

@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": f"Метод {request.method} не разрешён для {request.path}"}), 405

engine: GameEngine = None

def init_engine():
    global engine
    engine = GameEngine()
    return engine

# ---- Pages ----
@app.route("/")
def index():
    return render_template("index.html")

# ---- API: Status & Settings ----
@app.route("/api/status")
def api_status():
    ai_status = engine.ai.check_connection()
    ai_status["current_model"] = engine.ai.model  # выбранная модель
    return jsonify({
        "ai": ai_status,
        "game_files": len(engine.kb.files),
        "saves": len(engine.list_saves()),
    })

@app.route("/api/models")
def api_models():
    """List available AI models from the current backend."""
    models = engine.ai.list_models()
    return jsonify({"models": models, "current": engine.ai.model, "backend": engine.ai.backend})

@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        return jsonify({
            "backend": config.AI_BACKEND,
            "ollama_url": config.OLLAMA_BASE_URL,
            "ollama_model": config.OLLAMA_MODEL,
            "lmstudio_url": config.LMSTUDIO_BASE_URL,
            "lmstudio_model": config.LMSTUDIO_MODEL,
            "cloud_url": getattr(config, 'CLOUD_API_URL', ''),
            "cloud_model": getattr(config, 'CLOUD_API_MODEL', ''),
            "temperature": config.AI_TEMPERATURE,
            "max_tokens": config.AI_MAX_TOKENS,
        })

    data = request.json
    if "backend" in data:
        config.AI_BACKEND = data["backend"]
    if "model" in data and data["model"]:
        if config.AI_BACKEND == "ollama":
            config.OLLAMA_MODEL = data["model"]
        elif config.AI_BACKEND == "cloud_api":
            config.CLOUD_API_MODEL = data["model"]
        else:
            config.LMSTUDIO_MODEL = data["model"]
    if "ollama_url" in data:
        config.OLLAMA_BASE_URL = data["ollama_url"]
    if "lmstudio_url" in data:
        config.LMSTUDIO_BASE_URL = data["lmstudio_url"]
    if "cloud_url" in data and data["cloud_url"]:
        config.CLOUD_API_URL = data["cloud_url"]
    if "cloud_key" in data and data["cloud_key"]:
        config.CLOUD_API_KEY = data["cloud_key"]
    if "temperature" in data:
        config.AI_TEMPERATURE = float(data["temperature"])
    if "max_tokens" in data:
        config.AI_MAX_TOKENS = int(data["max_tokens"])

    from src.ai.connector import AIConnector
    engine.ai = AIConnector()
    return jsonify({"status": "ok"})

# ---- API: Character Creation ----
@app.route("/api/presets")
def api_presets():
    return jsonify(engine.get_presets())

@app.route("/api/creation-data")
def api_creation_data():
    """Return all data needed for enhanced character creation."""
    return jsonify(engine.get_creation_data())

@app.route("/api/character/create", methods=["POST"])
def api_create_character():
    data = request.json
    preset_id = data.get("preset_id")
    if preset_id and preset_id != "custom":
        result = engine.create_character_from_preset(preset_id)
    else:
        result = engine.create_custom_character(data)
    engine.state.phase = "character_creation"
    return jsonify(result)

@app.route("/api/game/start", methods=["POST"])
def api_start_game():
    data = request.json
    name = data.get("name", "Путник")
    result = engine.start_game(name)
    return jsonify(result)

# ---- API: Gameplay ----
@app.route("/api/action", methods=["POST"])
def api_action():
    data = request.json
    action = data.get("action", "")
    if not action:
        return jsonify({"error": "Действие не указано"}), 400
    result = engine.process_player_action(action)
    return jsonify(result)

@app.route("/api/action/stream", methods=["POST"])
def api_action_stream():
    data = request.json
    action = data.get("action", "")
    if not action:
        return jsonify({"error": "Действие не указано"}), 400

    engine.state.conversation_history.append({"role": "user", "content": action})

    # === V7: COMBAT ROUTING — no AI streaming needed for combat ===
    if engine.combat_engine.in_combat:
        result = engine._process_combat_turn(action)
        return jsonify(result)

    # === V7: SUBSYSTEM TRIGGER (hacking/investigation/crafting/combat) ===
    from src.systems.combat import detect_subsystem_trigger
    subsystem = detect_subsystem_trigger(action)
    subsystem_result = None
    if subsystem:
        subsystem_result = engine._handle_subsystem_trigger(subsystem, action)
        if subsystem_result and subsystem_result.get("combat_started"):
            return jsonify(subsystem_result)

    # === V6: MECHANICAL ACTIONS (buy/sell/travel) ===
    from src.systems.mechanics import detect_mechanical_action
    mech_action = detect_mechanical_action(action)
    mech_action_result = None
    if mech_action:
        mech_action_result = engine._handle_mechanical_action(mech_action)

    # === DICE CHECK ===
    dice_result = engine._check_mechanical_action(action)

    # === CONVERSATION MANAGEMENT ===
    from src.systems.mechanics import ConversationManager
    ConversationManager.manage_history(engine.state.conversation_history)

    # === WORLD SIMULATION TICK ===
    tier = engine.get_player_influence_tier()["tier"]
    engine.state.world_context = engine.state.world_sim.tick(
        engine.state.game_time, engine.state.current_location, tier
    )

    # === WORLD TICKER — major events ===
    world_events = engine.world_ticker.tick(engine.state)
    if world_events:
        engine.state.world_context["world_events"] = world_events
        from src.content.v4_legacy import _game_time_to_hours
        current_h = _game_time_to_hours(engine.state.game_time)
        for we in world_events:
            engine.world_effects.apply_event_effects(we, current_h)

    # === CONSEQUENCES ===
    turn = engine.state.world_sim.turn_count
    triggered_consequences = engine.consequences.check_consequences(turn)
    if triggered_consequences:
        engine.state.world_context["consequences"] = triggered_consequences

    # === V5: AUTO-REPUTATION ===
    from src.content.v5_legacy import calculate_auto_reputation, apply_reputation_changes, get_reputation_summary
    rep_changes = calculate_auto_reputation(action, engine.state.faction_reputation)
    if rep_changes:
        apply_reputation_changes(engine.state.faction_reputation, rep_changes)
        engine.state.world_context["rep_changes"] = get_reputation_summary(rep_changes)

    # === V5: WORLD EFFECTS ===
    from src.content.v4_legacy import _game_time_to_hours as _gth
    active_fx = engine.world_effects.get_active_effects_summary(_gth(engine.state.game_time))
    if active_fx:
        engine.state.world_context["active_world_effects"] = active_fx

    # === V5: QUEST CHAIN OFFER ===
    from src.content.v4_legacy import _game_time_to_hours as _gth2
    current_hours = _gth2(engine.state.game_time)
    if not hasattr(engine, '_last_chain_offer_h'):
        engine._last_chain_offer_h = current_hours - random.randint(100, 200)
    chain_cooldown = random.randint(120, 240)
    if not engine.active_chain and (current_hours - engine._last_chain_offer_h) >= chain_cooldown:
        from src.systems.quests import get_available_chains
        available = get_available_chains(
            engine.state.character.get("level", 1),
            engine.state.character.get("credits", 0),
            engine.state.faction_reputation)
        available = [c for c in available if c["id"] not in engine.completed_chains]
        if available:
            engine.state.world_context["chain_offer"] = random.choice(available)
            engine._last_chain_offer_h = current_hours

    # === PROCEDURAL QUEST GEN ===
    if not hasattr(engine, '_last_quest_gen_h'):
        engine._last_quest_gen_h = current_hours - random.randint(30, 80)
    quest_cooldown_h = random.randint(48, 120)
    if (current_hours - engine._last_quest_gen_h) >= quest_cooldown_h and len(engine.state.active_quests) < 5:
        pq = engine.quest_generator.generate_quest(
            player_level=engine.state.character.get("level", 1),
            location=engine.state.current_location,
            faction_standings=engine.state.faction_reputation)
        engine.state.active_quests.append(pq)
        engine._last_quest_gen_h = current_hours
        engine.state.world_context["new_quest"] = pq

    # === V6: PROPERTY INCOME ===
    income_result = engine.property_income.tick(current_hours, engine.property, engine.state.character)
    if income_result:
        engine.state.world_context["property_income"] = income_result

    # === BUILD SYSTEM PROMPT WITH ALL CONTEXT ===
    system_prompt = engine._build_system_prompt(action, dice_result, mech_action_result, subsystem_result)

    def generate():
        full_response = []

        # Send pre-AI events to UI
        if dice_result:
            yield f"data: {json.dumps({'type': 'dice', 'data': dice_result}, ensure_ascii=False)}\n\n"
        if mech_action_result:
            yield f"data: {json.dumps({'type': 'mechanical', 'data': mech_action_result}, ensure_ascii=False)}\n\n"
        if subsystem_result:
            yield f"data: {json.dumps({'type': 'subsystem', 'data': subsystem_result}, ensure_ascii=False)}\n\n"

        wc = engine.state.world_context
        if wc.get("news") or wc.get("rumors") or wc.get("economic_event"):
            yield f"data: {json.dumps({'type': 'world_event', 'data': wc}, ensure_ascii=False)}\n\n"

        # Stream AI response
        for token in engine.ai.generate_stream(
            system_prompt=system_prompt,
            messages=engine.state.conversation_history[-10:],
        ):
            full_response.append(token)
            yield f"data: {json.dumps({'type': 'token', 'data': token}, ensure_ascii=False)}\n\n"

        # === POST-AI: Parse [STATE] block and apply changes ===
        raw_response = "".join(full_response)
        parsed = engine._parse_ai_response(raw_response)
        narrative = parsed["narrative"]

        engine.state.conversation_history.append({"role": "assistant", "content": narrative})
        engine.state.session_events.append({
            "time": dict(engine.state.game_time),
            "action": action[:100], "result": narrative[:100],
        })

        # Time advance (AI-determined or random)
        time_mins = parsed.get("state_changes", {}).get("_custom_time", random.randint(5, 30))
        engine._advance_time(minutes=time_mins)

        # === V7: XP → LEVEL UP ===
        from src.systems.combat import process_xp_gain
        xp_to_add = parsed.get("state_changes", {}).get("_xp_to_add", 0)
        level_up_info = None
        if xp_to_add and xp_to_add > 0:
            level_up_info = process_xp_gain(engine.state.character, xp_to_add)

        # === V7: HP=0 DEFEAT (fail-forward) ===
        from src.systems.combat import apply_defeat
        defeat_result = None
        if engine.state.character.get("current_hp", 1) <= 0:
            defeat_result = apply_defeat(
                engine.state.character, engine.state.inventory,
                engine.state.game_time, engine.state.current_location)

        # === Send final state with ALL info ===
        done_data = {
            "game_state": engine._get_client_state(),
            "state_changes": parsed.get("state_changes", {}),
            "defeat": defeat_result,
            "level_up": level_up_info,
            "rep_changes": engine.state.world_context.get("rep_changes", ""),
            "new_quest": engine.state.world_context.get("new_quest"),
            "chain_offer": engine.state.world_context.get("chain_offer"),
            "mechanical_action": mech_action_result,
            "subsystem": subsystem_result,
            "property_income": income_result,
        }
        yield f"data: {json.dumps({'type': 'done', 'data': done_data}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.route("/api/state")
def api_state():
    return jsonify(engine.get_full_state())

@app.route("/api/inventory")
def api_inventory():
    return jsonify(engine.get_inventory())

@app.route("/api/quests")
def api_quests():
    return jsonify(engine.get_quests())

# ---- API: Save / Load ----
@app.route("/api/saves")
def api_list_saves():
    return jsonify(engine.list_saves())

@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.json
    result = engine.save_game(data.get("slot_name"))
    return jsonify(result)

@app.route("/api/load", methods=["POST"])
def api_load():
    data = request.json
    slot_name = data.get("slot_name")
    if not slot_name:
        return jsonify({"error": "Имя сохранения не указано"}), 400
    result = engine.load_game(slot_name)
    return jsonify(result)

@app.route("/api/save/delete", methods=["POST"])
def api_delete_save():
    data = request.json
    return jsonify(engine.delete_save(data.get("slot_name")))

# ---- API: Shop & Economy ----
@app.route("/api/shop")
def api_shop():
    """Get available shop items filtered by location type."""
    tier = engine.get_player_influence_tier()["tier"]
    items = engine.state.world_sim.get_shop_items(engine.state.current_location, tier)
    credits = engine.state.character.get("credits", 0)
    loc = engine.state.current_location
    dist_data = engine.galaxy_map.get_district(
        loc.get("planet",""), loc.get("city",""), loc.get("district",""))
    local_factions = dist_data.get("factions", []) if dist_data else []
    security = dist_data.get("security", "medium") if dist_data else "medium"
    dist_type = (dist_data.get("type", "") if dist_data else "").lower()
    place = loc.get("place", "")

    # Location-based shop filtering
    filtered = []
    for item in items:
        cat = item.get("category", "")
        rarity = item.get("rarity", "common")
        # Military/rare weapons only in military or low-security districts
        if cat == "weapons" and rarity == "rare":
            if security not in ("none", "low") and "военн" not in dist_type:
                continue
        # Implants only near medical/lab facilities
        if cat == "implants" and rarity == "rare":
            if not any(s in dist_type for s in ["лаборатор","медиц","науч","технолог"]):
                continue
        # Black market items only in low security
        if item.get("price", 0) > 20000 and rarity == "rare":
            if security in ("high", "very_high", "maximum"):
                continue
        filtered.append(item)

    # Apply faction price modifier
    faction_mod = FactionSystem.get_price_modifier(engine.state.faction_reputation, local_factions)
    if faction_mod != 1.0:
        for item in filtered:
            item["price"] = int(item["price"] * faction_mod)

    # Generate location-aware shop name
    shop_name = "Магазин"
    if place:
        shop_name = place
    elif "торгов" in dist_type or "коммерч" in dist_type:
        shop_name = "Торговый центр"
    elif security in ("none", "low"):
        shop_name = "Чёрный рынок"
    elif "военн" in dist_type:
        shop_name = "Военторг"
    elif "производств" in dist_type or "промышл" in dist_type:
        shop_name = "Технолавка"

    return jsonify({
        "items": filtered,
        "credits": credits,
        "price_modifier": round(engine.state.world_sim.price_modifier * faction_mod, 2),
        "faction_modifier": faction_mod,
        "location": loc,
        "shop_name": shop_name,
        "security": security,
    })

@app.route("/api/shop/buy", methods=["POST"])
def api_shop_buy():
    """Buy an item from the shop."""
    data = request.json
    item_id = data.get("item_id", "")
    tier = engine.get_player_influence_tier()["tier"]
    items = engine.state.world_sim.get_shop_items(engine.state.current_location, tier)
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Предмет не найден или недоступен"}), 404
    credits = engine.state.character.get("credits", 0)
    if credits < item["price"]:
        return jsonify({"error": f"Недостаточно кредитов. Нужно: ₡{item['price']:,}, у вас: ₡{credits:,}"}), 400
    # Deduct credits and add to inventory
    engine.state.character["credits"] = credits - item["price"]
    engine.state.inventory.append({
        "id": item["id"], "name": item["name"], "qty": 1,
        "type": item["category"], "stats": item["stats"],
        "rarity": item["rarity"],
    })
    return jsonify({
        "success": True,
        "message": f"Куплено: {item['name']} за ₡{item['price']:,}",
        "credits": engine.state.character["credits"],
        "item": item,
    })

@app.route("/api/shop/sell", methods=["POST"])
def api_shop_sell():
    """Sell an item from inventory (50% of base price)."""
    data = request.json
    inv_index = data.get("index", -1)
    if inv_index < 0 or inv_index >= len(engine.state.inventory):
        return jsonify({"error": "Предмет не найден в инвентаре"}), 404
    item = engine.state.inventory[inv_index]
    # Find base price
    from src.world.simulation import BASE_SHOP_ITEMS
    base_price = 0
    for cat, items in BASE_SHOP_ITEMS.items():
        for bi in items:
            if bi["id"] == item.get("id", ""):
                base_price = bi["base_price"]
                break
    sell_price = max(100, int(base_price * 0.5 * engine.state.world_sim.price_modifier))
    engine.state.character["credits"] = engine.state.character.get("credits", 0) + sell_price
    removed = engine.state.inventory.pop(inv_index)
    return jsonify({
        "success": True,
        "message": f"Продано: {removed['name']} за ₡{sell_price:,}",
        "credits": engine.state.character["credits"],
    })

# ═══════════════════════════════════════════════════
# IMPLANT INSTALLATION SYSTEM
# ═══════════════════════════════════════════════════

# Structured skill bonuses for all implants (parsed from stats text)
IMPLANT_SKILL_MAP = {
    "I_NEURO_BASIC":  {"skill_bonuses": {"hacking": 1}, "humanity_cost": 2, "surgery_dc": 8},
    "I_OPTICS":       {"skill_bonuses": {"education": 1}, "humanity_cost": 3, "surgery_dc": 10},
    "I_ARM_CYBER":    {"skill_bonuses": {"combat": 1}, "attr_bonuses": {"strength": 2}, "humanity_cost": 5, "surgery_dc": 12},
    "I_REFLEX_BOOST": {"skill_bonuses": {}, "attr_bonuses": {"reflexes": 1}, "humanity_cost": 4, "surgery_dc": 14},
    "I_NANOBLOOD":    {"skill_bonuses": {}, "hp_regen": 2, "humanity_cost": 6, "surgery_dc": 15},
    "I_NEURO_ADV":    {"skill_bonuses": {"hacking": 2, "technology": 1}, "humanity_cost": 4, "surgery_dc": 12},
    "I_LEGS_CYBER":   {"skill_bonuses": {"stealth": 1}, "attr_bonuses": {"dexterity": 2}, "humanity_cost": 5, "surgery_dc": 13},
    "I_SKIN_ARMOR":   {"skill_bonuses": {}, "defense_bonus": 4, "humanity_cost": 7, "surgery_dc": 16},
    "I_LUNG_FILTER":  {"skill_bonuses": {"survival": 1}, "attr_bonuses": {"endurance": 1}, "humanity_cost": 3, "surgery_dc": 10},
    "I_BONE_LACING":  {"skill_bonuses": {}, "attr_bonuses": {"strength": 1, "endurance": 1}, "hp_bonus": 15, "humanity_cost": 8, "surgery_dc": 16},
    "I_EMOTION_CHIP": {"skill_bonuses": {"diplomacy": 2}, "attr_bonuses": {"willpower": -1}, "humanity_cost": 4, "surgery_dc": 14},
    "I_COMBAT_CHIP":  {"skill_bonuses": {"combat": 2}, "attr_bonuses": {"reflexes": 1}, "humanity_cost": 5, "surgery_dc": 14},
    "I_MEMORY_BANK":  {"skill_bonuses": {"education": 1}, "attr_bonuses": {"intelligence": 1}, "humanity_cost": 3, "surgery_dc": 11},
    "I_THERMAL_EYES": {"skill_bonuses": {"education": 1}, "humanity_cost": 3, "surgery_dc": 11},
    "I_SUBVOCAL":     {"skill_bonuses": {}, "humanity_cost": 1, "surgery_dc": 7},
    # v3 implants
    "v3_cyber_eyes_upgrade": {"skill_bonuses": {"education": 2}, "humanity_cost": 4, "surgery_dc": 12},
    "v3_subdermal_armor":    {"skill_bonuses": {}, "defense_bonus": 3, "humanity_cost": 6, "surgery_dc": 15},
    "v3_reflex_booster":     {"skill_bonuses": {}, "attr_bonuses": {"reflexes": 2}, "humanity_cost": 5, "surgery_dc": 14},
    "v3_cortex_bomb":        {"skill_bonuses": {}, "humanity_cost": 10, "surgery_dc": 18},
    "v3_synth_blood":        {"skill_bonuses": {"survival": 1}, "hp_regen": 1, "humanity_cost": 4, "surgery_dc": 13},
    "v3_muscle_wire":        {"skill_bonuses": {"combat": 1}, "attr_bonuses": {"strength": 2}, "humanity_cost": 6, "surgery_dc": 14},
}
# Default for unknown implants
IMPLANT_DEFAULT = {"skill_bonuses": {}, "humanity_cost": 3, "surgery_dc": 12}

SURGERY_FEE_BASE = 5000  # Base surgery cost
SELF_SURGERY_DC_PENALTY = 4  # Extra DC if no doctor nearby

@app.route("/api/implant/list")
def api_implant_list():
    """List installed and available (in inventory) implants."""
    installed = []
    available = []
    for i, item in enumerate(engine.state.inventory):
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
    loc = engine.state.current_location
    near_clinic = _check_clinic_nearby(loc)
    return jsonify({
        "installed": installed,
        "available": available,
        "near_clinic": near_clinic,
        "surgery_fee": SURGERY_FEE_BASE,
        "humanity": engine.state.character.get("humanity", 100),
        "max_implant_slots": 6,
        "used_slots": len(installed),
    })

def _check_clinic_nearby(loc):
    """Check if current location has medical services."""
    place = loc.get("place", "").lower()
    district = loc.get("district", "").lower()
    medical_words = ["клиник", "госпиталь", "больниц", "медик", "лаборатор", "doctor", "медцентр"]
    if any(w in place for w in medical_words) or any(w in district for w in medical_words):
        return True
    # Check district services
    dist_data = engine.galaxy_map.get_district(
        loc.get("planet",""), loc.get("city",""), loc.get("district",""))
    if dist_data:
        for est in dist_data.get("establishments", []):
            services = est.get("services", [])
            if any(s in services for s in ["healing", "surgery", "implant_install", "implant_check"]):
                return True
    return False

@app.route("/api/implant/install", methods=["POST"])
def api_implant_install():
    """Install an implant from inventory. Requires surgery check."""
    data = request.json or {}
    inv_index = data.get("inv_index", -1)
    if inv_index < 0 or inv_index >= len(engine.state.inventory):
        return jsonify({"error": "Имплант не найден в инвентаре"}), 404

    item = engine.state.inventory[inv_index]
    if item.get("type") != "implants" and item.get("category") != "implants":
        return jsonify({"error": "Это не имплант"}), 400
    if item.get("installed"):
        return jsonify({"error": "Имплант уже установлен"}), 400

    # Check implant slots
    installed_count = sum(1 for i in engine.state.inventory if i.get("installed") and
                         (i.get("type") == "implants" or i.get("category") == "implants"))
    if installed_count >= 6:
        return jsonify({"error": "Все 6 слотов имплантов заняты. Сначала удалите имплант."}), 400

    # Get implant data
    implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), IMPLANT_DEFAULT)
    surgery_dc = implant_info["surgery_dc"]

    # Surgery fee
    credits = engine.state.character.get("credits", 0)
    loc = engine.state.current_location
    near_clinic = _check_clinic_nearby(loc)
    fee = SURGERY_FEE_BASE if near_clinic else 0

    if near_clinic and credits < fee:
        return jsonify({"error": f"Недостаточно кредитов для операции: нужно ₡{fee:,}"}), 400

    if not near_clinic:
        surgery_dc += SELF_SURGERY_DC_PENALTY  # Self-surgery is harder

    # Surgery check: medicine skill + intelligence
    from src.core.engine import DiceRoller
    med_skill = engine.state.character.get("skills", {}).get("medicine", 0)
    intel = engine.state.character.get("attributes", {}).get("intelligence", 5)

    if near_clinic:
        # Doctor does it — use base DC, auto-bonus +3
        med_skill = max(med_skill, 4)  # Doctor has at least skill 4

    result = DiceRoller.skill_check(med_skill, intel, surgery_dc)

    # Pay fee
    if near_clinic:
        engine.state.character["credits"] = credits - fee

    # Apply humanity cost
    humanity_cost = implant_info["humanity_cost"]

    if result["success"]:
        # Successful installation
        item["installed"] = True
        item["skill_bonuses"] = implant_info.get("skill_bonuses", {})
        item["attr_bonuses"] = implant_info.get("attr_bonuses", {})

        # Apply attribute bonuses permanently
        for attr, val in implant_info.get("attr_bonuses", {}).items():
            engine.state.character.setdefault("attributes", {})[attr] = \
                engine.state.character.get("attributes", {}).get(attr, 5) + val

        # Apply HP bonus
        if "hp_bonus" in implant_info:
            engine.state.character["max_hp"] = engine.state.character.get("max_hp", 50) + implant_info["hp_bonus"]
            engine.state.character["current_hp"] = engine.state.character.get("current_hp", 50) + implant_info["hp_bonus"]

        # Reduce humanity
        engine.state.character["humanity"] = max(0,
            engine.state.character.get("humanity", 100) - humanity_cost)

        # Side effects for high humanity cost
        side_effects = []
        if humanity_cost >= 7:
            side_effects.append("Кошмары на 3 дня (+5 стресс)")
            engine.state.character["stress"] = min(100,
                engine.state.character.get("stress", 0) + 5)
        if engine.state.character.get("humanity", 100) < 30:
            side_effects.append("⚠️ Человечность критически низкая! Риск киберпсихоза.")

        return jsonify({
            "success": True,
            "message": f"✅ Имплант «{item['name']}» успешно установлен!",
            "surgery_roll": result,
            "humanity_lost": humanity_cost,
            "humanity": engine.state.character.get("humanity", 100),
            "credits": engine.state.character.get("credits", 0),
            "side_effects": side_effects,
            "bonuses": {
                "skills": implant_info.get("skill_bonuses", {}),
                "attributes": implant_info.get("attr_bonuses", {}),
            },
        })
    else:
        # Failed surgery
        damage = random.randint(3, 10)
        engine.state.character["current_hp"] = max(1,
            engine.state.character.get("current_hp", 50) - damage)
        # Still lose some humanity from attempt
        engine.state.character["humanity"] = max(0,
            engine.state.character.get("humanity", 100) - (humanity_cost // 2))

        complications = []
        if result["quality"] == "critical_failure":
            complications.append("☠ Имплант повреждён при установке! Потерян.")
            engine.state.inventory.pop(inv_index)  # Implant destroyed
            complications.append(f"Получено {damage * 2} урона.")
            engine.state.character["current_hp"] = max(1,
                engine.state.character.get("current_hp", 50) - damage)
        else:
            complications.append(f"Получено {damage} урона от неудачной операции.")
            complications.append("Попробуйте снова или найдите клинику.")

        return jsonify({
            "success": False,
            "message": f"❌ Операция не удалась!",
            "surgery_roll": result,
            "damage": damage,
            "complications": complications,
            "humanity": engine.state.character.get("humanity", 100),
            "credits": engine.state.character.get("credits", 0),
        })

@app.route("/api/implant/remove", methods=["POST"])
def api_implant_remove():
    """Remove an installed implant."""
    data = request.json or {}
    inv_index = data.get("inv_index", -1)
    if inv_index < 0 or inv_index >= len(engine.state.inventory):
        return jsonify({"error": "Имплант не найден"}), 404

    item = engine.state.inventory[inv_index]
    if not item.get("installed"):
        return jsonify({"error": "Этот имплант не установлен"}), 400

    implant_info = IMPLANT_SKILL_MAP.get(item.get("id", ""), IMPLANT_DEFAULT)

    # Remove attribute bonuses
    for attr, val in implant_info.get("attr_bonuses", {}).items():
        engine.state.character.setdefault("attributes", {})[attr] = \
            engine.state.character.get("attributes", {}).get(attr, 5) - val

    # Remove HP bonus
    if "hp_bonus" in implant_info:
        engine.state.character["max_hp"] = max(10, engine.state.character.get("max_hp", 50) - implant_info["hp_bonus"])
        engine.state.character["current_hp"] = min(
            engine.state.character.get("current_hp", 50),
            engine.state.character.get("max_hp", 50))

    # Restore some humanity
    humanity_restore = implant_info.get("humanity_cost", 3) // 2
    engine.state.character["humanity"] = min(100,
        engine.state.character.get("humanity", 100) + humanity_restore)

    item["installed"] = False
    item.pop("skill_bonuses", None)
    item.pop("attr_bonuses", None)

    loc = engine.state.current_location
    near_clinic = _check_clinic_nearby(loc)
    fee = SURGERY_FEE_BASE // 2 if near_clinic else 0
    if near_clinic:
        engine.state.character["credits"] = engine.state.character.get("credits", 0) - fee

    return jsonify({
        "success": True,
        "message": f"🔧 Имплант «{item['name']}» удалён",
        "humanity_restored": humanity_restore,
        "humanity": engine.state.character.get("humanity", 100),
        "credits": engine.state.character.get("credits", 0),
    })

@app.route("/api/world")
def api_world():
    """Get current world state — news, rumors, economy."""
    return jsonify({
        "news_history": engine.state.world_sim.news_history[-5:],
        "price_modifier": engine.state.world_sim.price_modifier,
        "instability": engine.state.world_sim.instability,
        "turn_count": engine.state.world_sim.turn_count,
        "last_context": engine.state.world_context,
    })

# ---- API: Knowledge Base ----
@app.route("/api/kb/files")
def api_kb_files():
    return jsonify(engine.kb.list_files())

@app.route("/api/kb/file/<filename>")
def api_kb_file(filename):
    data = engine.kb.get_file(filename)
    if data is None:
        return jsonify({"error": "Файл не найден"}), 404
    return jsonify(data)

# ---- API: Galaxy Map ----
@app.route("/api/map")
def api_map():
    """Get galaxy map overview — planets, routes."""
    planets = engine.galaxy_map.list_planets()
    loc = engine.state.current_location
    routes = engine.galaxy_map.get_routes_from(loc.get("planet", ""))
    return jsonify({
        "planets": planets,
        "current_location": loc,
        "routes": routes,
    })

@app.route("/api/map/location")
def api_map_location():
    """Get current location details — districts, establishments."""
    loc = engine.state.current_location
    planet = loc.get("planet", "")
    city = loc.get("city", "")
    district = loc.get("district", "")

    districts = engine.galaxy_map.list_districts(planet, city)
    establishments = engine.galaxy_map.list_establishments(planet, city, district)
    description = engine.galaxy_map.get_location_description(planet, city, district)
    routes = engine.galaxy_map.get_routes_from(planet)
    cities = engine.galaxy_map.list_cities(planet)

    return jsonify({
        "location": loc,
        "description": description,
        "districts": districts,
        "establishments": establishments,
        "cities": cities,
        "routes": routes,
    })

@app.route("/api/map/move", methods=["POST"])
def api_map_move():
    """Move to a new district, city, or place."""
    data = request.json or {}
    district = data.get("district")
    city = data.get("city")
    planet = data.get("planet")
    place = data.get("place", "")

    loc = engine.state.current_location

    # If moving to another planet — check routes, advance time
    if planet and planet != loc.get("planet"):
        routes = engine.galaxy_map.get_routes_from(loc.get("planet", ""))
        if planet not in routes:
            return jsonify({"error": f"Нет маршрута до {planet}"}), 400
        route = routes[planet]
        try:
            hours = int(route["time"].split("-")[0].split()[0])
        except (ValueError, IndexError, AttributeError):
            hours = 72
        for _ in range(hours):
            engine._advance_time(60)
        cities = engine.galaxy_map.list_cities(planet)
        new_city = city or (cities[0] if cities else "?")
        new_districts = engine.galaxy_map.list_districts(planet, new_city)
        new_district = district or (new_districts[0]["name"] if new_districts else "?")
        engine.state.current_location = {
            "planet": planet, "city": new_city,
            "district": new_district, "place": place,
        }
        # Space travel event
        space_event = LocationEvents.on_planet_travel()
        # Auto-spawn NPC at new location
        new_npc = engine.state.npc_registry.generate_npc(planet=planet, importance="minor")
        return jsonify({
            "success": True,
            "travel_hours": hours,
            "message": f"Перелёт до {planet} занял {hours} часов. Прибытие: {new_city}, {new_district}.",
            "location": engine.state.current_location,
            "game_time": engine.state.game_time,
            "travel_event": space_event,
            "new_npc": new_npc.get("name"),
        })

    # Moving within same planet
    travel_event = None
    if city and city != loc.get("city"):
        engine._advance_time(120)
        loc["city"] = city
        districts = engine.galaxy_map.list_districts(loc["planet"], city)
        loc["district"] = district or (districts[0]["name"] if districts else "?")
        travel_event = LocationEvents.on_district_change("Средний")
    elif district and district != loc.get("district"):
        engine._advance_time(30)
        # Get district security for event chance
        dist_data = engine.galaxy_map.get_district(loc.get("planet",""), loc.get("city",""), district)
        security = dist_data.get("security", "Средний") if dist_data else "Средний"
        loc["district"] = district
        travel_event = LocationEvents.on_district_change(security)

    loc["place"] = place
    engine.state.current_location = loc

    # Maybe auto-spawn NPC in new district (30% chance)
    import random
    new_npc_name = None
    if random.random() < 0.3:
        npc = engine.state.npc_registry.generate_npc(
            planet=loc.get("planet", "Земля"), importance="minor"
        )
        new_npc_name = npc.get("name")

    return jsonify({
        "success": True,
        "location": loc,
        "game_time": engine.state.game_time,
        "travel_event": travel_event,
        "new_npc": new_npc_name,
    })

# ---- API: NPC Registry ----
@app.route("/api/npcs")
def api_npcs():
    """Get known NPCs from registry."""
    npcs = engine.state.npc_registry.get_known_npcs(limit=20)
    return jsonify({
        "npcs": npcs,
        "total": len(engine.state.npc_registry.npcs),
    })

@app.route("/api/npc/generate", methods=["POST"])
def api_npc_generate():
    """Generate a new NPC."""
    data = request.json or {}
    planet = data.get("planet", engine.state.current_location.get("planet", "Земля"))
    role = data.get("role")
    faction = data.get("faction")
    importance = data.get("importance", "minor")

    npc = engine.state.npc_registry.generate_npc(
        planet=planet, role=role, faction=faction, importance=importance
    )
    return jsonify({"npc": npc})

# ---- API: Crafting ----
@app.route("/api/crafting/recipes")
def api_crafting_recipes():
    """Get available crafting recipes with can-craft status."""
    recipes = CraftingSystem.get_recipes()
    results = []
    for r in recipes:
        check = CraftingSystem.can_craft(r["id"], engine.state.inventory, engine.state.character)
        results.append({
            "recipe": r,
            "can_craft": check["can_craft"],
            "missing": check.get("missing_materials", []),
            "skill_value": check.get("skill_value", 0),
        })
    return jsonify({"recipes": results, "materials": CraftingSystem.get_materials()})

@app.route("/api/crafting/craft", methods=["POST"])
def api_craft():
    """Attempt to craft an item."""
    data = request.json or {}
    recipe_id = data.get("recipe_id", "")
    result = CraftingSystem.craft(recipe_id, engine.state.inventory, engine.state.character, engine.dice)
    return jsonify(result)

# ---- API: Perks & Level Up ----
@app.route("/api/perks")
def api_perks():
    """Get character perks and available perks."""
    owned = engine.state.character.get("perks", [])
    available = PerkSystem.get_available_perks(engine.state.character, count=3)
    return jsonify({
        "owned": owned,
        "available": available,
        "unspent_skill_points": engine.state.character.get("unspent_skill_points", 0),
    })

@app.route("/api/perks/select", methods=["POST"])
def api_select_perk():
    """Select a perk."""
    data = request.json or {}
    perk_id = data.get("perk_id", "")
    perk = PerkSystem.apply_perk(engine.state.character, perk_id)
    if perk:
        return jsonify({"success": True, "perk": perk})
    return jsonify({"success": False, "error": "Перк не найден или уже выбран"}), 400

@app.route("/api/levelup/spend", methods=["POST"])
def api_spend_skill_point():
    """Spend a skill point."""
    data = request.json or {}
    skill = data.get("skill", "")
    ok = LevelUpSystem.spend_skill_point(engine.state.character, skill)
    if ok:
        return jsonify({
            "success": True,
            "skill": skill,
            "new_value": engine.state.character["skills"][skill],
            "remaining": engine.state.character.get("unspent_skill_points", 0),
        })
    return jsonify({"success": False, "error": "Нет очков или навык не найден"}), 400

# ---- API: Psychology ----
@app.route("/api/psychology")
def api_psychology():
    """Get character psychology state."""
    char = engine.state.character
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

# ---- API: Factions ----
@app.route("/api/factions")
def api_factions():
    """Get faction reputation."""
    reps = engine.state.faction_reputation
    result = []
    for faction, rep in sorted(reps.items(), key=lambda x: -abs(x[1])):
        result.append({
            "faction": faction,
            "reputation": rep,
            "standing": FactionSystem.get_standing(rep),
        })
    return jsonify({"factions": result})

# ---- API: Quest Management ----
@app.route("/api/quest/add", methods=["POST"])
def api_add_quest():
    """Add a new quest."""
    data = request.json or {}
    quest = QuestTracker.create_quest(
        title=data.get("title", "Новое задание"),
        description=data.get("description", ""),
        giver=data.get("giver", ""),
        reward_credits=data.get("reward_credits", 0),
        reward_xp=data.get("reward_xp", 100),
    )
    engine.state.active_quests.append(quest)
    return jsonify({"quest": quest})

@app.route("/api/quest/advance", methods=["POST"])
def api_advance_quest():
    """Advance quest to next stage."""
    data = request.json or {}
    quest_id = data.get("quest_id", "")
    for q in engine.state.active_quests:
        if q.get("id") == quest_id:
            QuestTracker.advance_quest(q)
            if q["status"] == "completed":
                engine.state.active_quests.remove(q)
                engine.state.completed_quests.append(q)
                # Give rewards
                engine.add_credits(q.get("reward_credits", 0))
                engine.add_xp(q.get("reward_xp", 0))
                # Track completion for procedural system
                if q.get("procedural"):
                    engine.quest_generator.on_quest_complete(q.get("type", ""))
                    engine.consequences.log_action("completed_major_quest", {
                        "quest_title": q["title"], "turn": engine.state.world_sim.turn_count,
                    })
                # Apply reputation rewards
                for faction, amount in q.get("reward_reputation", {}).items():
                    engine.state.faction_reputation[faction] = (
                        engine.state.faction_reputation.get(faction, 0) + amount
                    )
            return jsonify({"quest": q})
    return jsonify({"error": "Квест не найден"}), 404


@app.route("/api/quest/generate", methods=["POST"])
def api_generate_quest():
    """Generate a procedural quest on demand."""
    data = request.json or {}
    preferred_type = data.get("type")
    quest = engine.quest_generator.generate_quest(
        player_level=engine.state.character.get("level", 1),
        location=engine.state.current_location,
        preferred_type=preferred_type,
        faction_standings=engine.state.faction_reputation,
    )
    engine.state.active_quests.append(quest)
    return jsonify({"quest": quest})


@app.route("/api/world/events")
def api_world_events():
    """Get active world events, crises, and consequences."""
    return jsonify({
        "active_crises": [
            {"text": c["text"], "category": c["category"], "severity": c["severity"]}
            for c in engine.world_ticker.active_crises if not c.get("resolved")
        ],
        "recent_events": [
            {"text": e["text"], "category": e["category"]}
            for e in engine.world_ticker.event_history[-10:]
        ],
        "locked_areas": getattr(engine.world_ticker, 'locked_areas', []),
        "pending_consequences": len(engine.consequences.pending),
        "triggered_consequences": [
            {"text": c["text"], "severity": c["severity"]}
            for c in engine.consequences.triggered[-5:]
        ],
    })


@app.route("/api/consequence/log", methods=["POST"])
def api_log_consequence():
    """Log a player action for consequence tracking."""
    data = request.json or {}
    action_type = data.get("action_type", "")
    details = data.get("details", {})
    details["turn"] = engine.state.world_sim.turn_count
    engine.consequences.log_action(action_type, details)
    return jsonify({"success": True, "pending": len(engine.consequences.pending)})


# ════════════════════════════════════════════════════════════
#  SUBSYSTEM ENDPOINTS — Hacking, Investigation, Companions, Ship, Property
# ════════════════════════════════════════════════════════════

@app.route("/api/hacking/targets")
def api_hack_targets():
    """Location-aware hacking targets."""
    loc = engine.state.current_location
    district = loc.get("district", "")
    place = loc.get("place", "")
    dist_data = engine.galaxy_map.get_district(
        loc.get("planet",""), loc.get("city",""), district)
    security = dist_data.get("security", "medium") if dist_data else "medium"
    dist_type = dist_data.get("type", "") if dist_data else ""
    services = []
    if dist_data:
        for est in dist_data.get("establishments", []):
            services.extend(est.get("services", []))

    targets = []
    # Basic terminal — always available where there's tech
    has_tech = any(s in str(services).lower() for s in ["торговля","ремонт","информация","заказ","наём","банк","сервер","данные","лаборатория"])
    if has_tech or place:
        targets.append({"id":"terminal","name":"Терминал","desc":"Простой терминал, мало данных","difficulty":"Простой","requires_skill":0})
    # Security — in secured areas
    if security in ("high","very_high","maximum") or any(s in dist_type.lower() for s in ["правительств","военн","лаборатор","корпоратив"]):
        targets.append({"id":"security","name":"Охранная система","desc":"Камеры, замки, сигнализация","difficulty":"Средний","requires_skill":2})
    # Corporate — in corporate/commercial districts
    if any(s in dist_type.lower() for s in ["корпоратив","торгов","коммерч","финанс"]) or any(s in str(services).lower() for s in ["банк","корпорац","биржа"]):
        targets.append({"id":"corporate","name":"Корпоративная сеть","desc":"Ценные данные, высокая защита","difficulty":"Сложный","requires_skill":4})
    # Military — only in military/government zones
    if any(s in dist_type.lower() for s in ["военн","правительств"]) or security in ("maximum","very_high"):
        targets.append({"id":"military","name":"Военная система","desc":"Секретные данные, опасно","difficulty":"Экстремальный","requires_skill":6})
    # Black market data — in underworld/criminal areas
    if security in ("none","low") or any(s in dist_type.lower() for s in ["крим","подпол","нижн","чёрн"]):
        targets.append({"id":"blacknet","name":"Чёрная сеть","desc":"Нелегальные данные, контакты","difficulty":"Средний","requires_skill":3})

    # Fallback: at least show terminal in any establishment
    if not targets and place:
        targets.append({"id":"terminal","name":"Местный терминал","desc":"Базовый доступ","difficulty":"Простой","requires_skill":0})

    location_name = f"{district}" + (f" → {place}" if place else "")
    return jsonify({"targets": targets, "location_name": location_name, "security": security})

@app.route("/api/hacking/start", methods=["POST"])
def api_hack_start():
    data = request.json or {}
    target = data.get("target_type", "terminal")
    char = engine.state.character
    hacking = char.get("skills", {}).get("hacking", 0)
    stealth = char.get("skills", {}).get("stealth", 0)
    result = engine.hacking.start_hack(target, hacking, stealth)
    return jsonify(result)

@app.route("/api/hacking/action", methods=["POST"])
def api_hack_action():
    data = request.json or {}
    action = data.get("action", "crack_ice")
    result = engine.hacking.hack_action(action)
    return jsonify(result)

@app.route("/api/investigation/open", methods=["POST"])
def api_investigation_open():
    data = request.json or {}
    result = engine.investigation.open_case(
        case_type=data.get("type"),
        custom_name=data.get("name")
    )
    return jsonify(result)

@app.route("/api/investigation/clue", methods=["POST"])
def api_investigation_clue():
    data = request.json or {}
    result = engine.investigation.add_clue(
        case_id=data.get("case_id", ""),
        clue_text=data.get("text", ""),
        source=data.get("source", ""),
        reliability=data.get("reliability", "medium"),
    )
    return jsonify(result)

@app.route("/api/investigation/suspect", methods=["POST"])
def api_investigation_suspect():
    data = request.json or {}
    result = engine.investigation.add_suspect(
        case_id=data.get("case_id", ""),
        suspect_name=data.get("name", ""),
        motive=data.get("motive", ""),
        evidence=data.get("evidence", ""),
    )
    return jsonify(result)

@app.route("/api/investigation/conclude", methods=["POST"])
def api_investigation_conclude():
    data = request.json or {}
    result = engine.investigation.conclude_case(
        case_id=data.get("case_id", ""),
        conclusion=data.get("conclusion", ""),
        suspect_name=data.get("suspect", ""),
    )
    return jsonify(result)

@app.route("/api/investigation/list", methods=["GET"])
def api_investigation_list():
    return jsonify({
        "active": engine.investigation.active_cases,
        "closed_count": len(engine.investigation.closed_cases),
    })

@app.route("/api/companions/available", methods=["GET"])
def api_companions_available():
    loc = engine.state.current_location
    recruits = engine.companions.get_available_recruits(loc)
    loc_name = f"{loc.get('city', '')}, {loc.get('district', '')}"
    return jsonify({"recruits": recruits, "team_size": len(engine.companions.companions),
                    "max": engine.companions.MAX_COMPANIONS,
                    "location": loc_name})

@app.route("/api/companions/recruit", methods=["POST"])
def api_companions_recruit():
    data = request.json or {}
    # Build companion dict from data
    companion = data.get("companion", {})
    credits = engine.state.character.get("credits", 0)
    result = engine.companions.recruit(companion, credits)
    if "cost" in result:
        engine.state.character["credits"] = credits - result["cost"]
    return jsonify(result)

@app.route("/api/companions/dismiss", methods=["POST"])
def api_companions_dismiss():
    data = request.json or {}
    result = engine.companions.dismiss(data.get("companion_id", ""))
    return jsonify(result)

@app.route("/api/companions/team", methods=["GET"])
def api_companions_team():
    return jsonify({"companions": engine.companions.companions,
                    "combat_bonus": engine.companions.get_combat_bonus()})

@app.route("/api/ship/info", methods=["GET"])
def api_ship_info():
    if engine.ship.ship:
        return jsonify({"ship": engine.ship.ship})
    return jsonify({"ship": None})

@app.route("/api/ship/buy", methods=["POST"])
def api_ship_buy():
    data = request.json or {}
    result = engine.ship.buy_ship(data.get("class", "shuttle"), data.get("name"))
    return jsonify(result)

@app.route("/api/ship/upgrade", methods=["POST"])
def api_ship_upgrade():
    data = request.json or {}
    result = engine.ship.install_upgrade(data.get("upgrade_id", ""))
    return jsonify(result)

@app.route("/api/ship/cargo/load", methods=["POST"])
def api_ship_cargo_load():
    data = request.json or {}
    result = engine.ship.load_cargo(data.get("item", ""), data.get("qty", 1))
    return jsonify(result)

@app.route("/api/ship/refuel", methods=["POST"])
def api_ship_refuel():
    if not engine.ship.ship:
        return jsonify({"error": "Нет корабля"})
    s = engine.ship.ship
    needed = s["fuel_max"] - s["fuel"]
    cost = needed * 5  # 5₡ per unit
    credits = engine.state.character.get("credits", 0)
    if credits < cost:
        return jsonify({"error": f"Нужно {cost}₡, у вас {credits}₡"})
    engine.state.character["credits"] = credits - cost
    s["fuel"] = s["fuel_max"]
    return jsonify({"refueled": True, "cost": cost, "fuel": s["fuel"]})

@app.route("/api/ship/repair", methods=["POST"])
def api_ship_repair():
    result = engine.ship.repair()
    if "cost" in result:
        engine.state.character["credits"] = engine.state.character.get("credits", 0) - result["cost"]
    return jsonify(result)

@app.route("/api/property/buy", methods=["POST"])
def api_property_buy():
    data = request.json or {}
    result = engine.property.buy_property(
        data.get("type", "apartment"),
        data.get("location", engine.state.current_location),
        data.get("name"),
    )
    return jsonify(result)

@app.route("/api/property/list", methods=["GET"])
def api_property_list():
    return jsonify({"properties": engine.property.properties})

@app.route("/api/property/income", methods=["GET"])
def api_property_income():
    return jsonify(engine.property.collect_income())

@app.route("/api/property/store", methods=["POST"])
def api_property_store():
    data = request.json or {}
    result = engine.property.store_item(data.get("property_id", ""), data.get("item", ""))
    return jsonify(result)


@app.route("/api/content/stats", methods=["GET"])
def api_content_stats():
    """Return total content counts for debugging/display."""
    from src.systems.game_systems import PERK_DATABASE, CRAFTING_RECIPES, TRAVEL_EVENTS, SPACE_EVENTS
    from src.world.simulation import BASE_SHOP_ITEMS
    from src.world.procedural import QUEST_TEMPLATES, WORLD_EVENT_TEMPLATES
    from src.content.v4_legacy import (
        get_all_origins_v4, get_all_formative_years_v4,
        get_all_specializations_v4, get_total_tiered_events,
    )
    from src.systems.quests import QUEST_CHAINS
    from src.systems.companions import COMPANIONS
    from src.content.v5_legacy import UNIQUE_NPCS
    total_shop = sum(len(v) for v in BASE_SHOP_ITEMS.values())
    chain_stages = sum(len(c["stages"]) for c in QUEST_CHAINS)
    return jsonify({
        "origins": len(get_all_origins_v4()),
        "formative_years": len(get_all_formative_years_v4()),
        "specializations": len(get_all_specializations_v4()),
        "perks": len(PERK_DATABASE),
        "recipes": len(CRAFTING_RECIPES),
        "travel_events": len(TRAVEL_EVENTS),
        "space_events": len(SPACE_EVENTS),
        "shop_items": total_shop,
        "shop_categories": {k: len(v) for k, v in BASE_SHOP_ITEMS.items()},
        "quest_templates": len(QUEST_TEMPLATES),
        "world_event_types": len(WORLD_EVENT_TEMPLATES),
        "tiered_events": get_total_tiered_events(),
        "tiered_events_tiers": 8,
        "quest_chains": len(QUEST_CHAINS),
        "quest_chain_stages": chain_stages,
        "companions": len(COMPANIONS),
        "unique_npcs": len(UNIQUE_NPCS),
        "subsystems": ["hacking", "investigation", "companions", "ship", "property",
                       "quest_chains", "world_effects", "auto_reputation"],
    })


# ---- Run ----
if __name__ == "__main__":
    init_engine()
    print(f"\n{'='*60}")
    print(f"  NEXUS RPG Server")
    print(f"  http://localhost:{config.PORT}")
    print(f"  Backend: {config.AI_BACKEND} | Model: {engine.ai.model}")
    print(f"  Game files: {len(engine.kb.files)}")
    print(f"{'='*60}\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
