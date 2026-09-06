"""
Auto-generated Blueprint: system
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.server.routes._deps import get_engine, get_app
from src import config  # Phase 26 fix: импорт для /api/settings (AI_BACKEND и др.)

system = Blueprint("system", __name__)


# Auto-extracted handlers from app.py

@system.route("/")
def index():
    return render_template("index.html")




@system.route("/api/status")
def api_status():
    ai_status = get_engine().ai.check_connection()
    ai_status["current_model"] = get_engine().ai.model  # выбранная модель
    return jsonify({
        "ai": ai_status,
        "game_files": len(get_engine().kb.files),
        "saves": len(get_engine().list_saves()),
    })




@system.route("/api/models")
def api_models():
    """List available AI models from the current backend."""
    models = get_engine().ai.list_models()
    return jsonify({"models": models, "current": get_engine().ai.model, "backend": get_engine().ai.backend})




@system.route("/api/settings", methods=["GET", "POST"])
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
    get_engine().ai = AIConnector()
    return jsonify({"status": "ok"})




@system.route("/api/presets")
def api_presets():
    return jsonify(get_engine().get_presets())




@system.route("/api/creation-data")
def api_creation_data():
    """Return all data needed for enhanced character creation."""
    return jsonify(get_engine().get_creation_data())




@system.route("/api/game/start", methods=["POST"])
def api_start_game():
    data = request.json
    name = data.get("name", "Путник")
    result = get_engine().start_game(name)
    return jsonify(result)




@system.route("/api/saves")
def api_list_saves():
    return jsonify(get_engine().list_saves())




@system.route("/api/save", methods=["POST"])
def api_save():
    data = request.json
    result = get_engine().save_game(data.get("slot_name"))
    return jsonify(result)




@system.route("/api/load", methods=["POST"])
def api_load():
    data = request.json
    slot_name = data.get("slot_name")
    if not slot_name:
        return jsonify({"error": "Имя сохранения не указано"}), 400
    result = get_engine().load_game(slot_name)
    return jsonify(result)




@system.route("/api/save/delete", methods=["POST"])
def api_delete_save():
    data = request.json
    return jsonify(get_engine().delete_save(data.get("slot_name")))




@system.route("/api/kb/files")
def api_kb_files():
    return jsonify(get_engine().kb.list_files())




@system.route("/api/kb/file/<filename>")
def api_kb_file(filename):
    data = get_engine().kb.get_file(filename)
    if data is None:
        return jsonify({"error": "Файл не найден"}), 404
    return jsonify(data)




@system.route("/api/content/stats", methods=["GET"])
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




