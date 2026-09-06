"""
Auto-generated Blueprint: gameplay
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
import json
import random
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.server.routes._deps import get_engine, get_app

gameplay = Blueprint("gameplay", __name__)


# Auto-extracted handlers from app.py

@gameplay.route("/api/action", methods=["POST"])
def api_action():
    data = request.json
    action = data.get("action", "")
    if not action:
        return jsonify({"error": "Действие не указано"}), 400
    result = get_engine().process_player_action(action)
    return jsonify(result)




@gameplay.route("/api/action/stream", methods=["POST"])
def api_action_stream():
    # Phase 26 fix: bind local 'engine' alias so subsequent code uses
    # the same GameEngine singleton instead of calling get_engine()
    # repeatedly. Without this, NameError fires on lines that reference
    # bare 'engine' (e.g. hasattr(engine, '_last_chain_offer_h')).
    engine = get_engine()
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




@gameplay.route("/api/consequence/log", methods=["POST"])
def api_log_consequence():
    """Log a player action for consequence tracking."""
    data = request.json or {}
    action_type = data.get("action_type", "")
    details = data.get("details", {})
    details["turn"] = get_engine().state.world_sim.turn_count
    get_engine().consequences.log_action(action_type, details)
    return jsonify({"success": True, "pending": len(get_engine().consequences.pending)})





@gameplay.route("/api/hacking/targets")
def api_hack_targets():
    """Location-aware hacking targets."""
    loc = get_engine().state.current_location
    district = loc.get("district", "")
    place = loc.get("place", "")
    dist_data = get_engine().galaxy_map.get_district(
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




@gameplay.route("/api/hacking/start", methods=["POST"])
def api_hack_start():
    data = request.json or {}
    target = data.get("target_type", "terminal")
    char = get_engine().state.character
    hacking = char.get("skills", {}).get("hacking", 0)
    stealth = char.get("skills", {}).get("stealth", 0)
    result = get_engine().hacking.start_hack(target, hacking, stealth)
    # D4a (H3): ответ старта в UI-форме (имя цели строкой + снимок узлов).
    # ВАЖНО: start_hack возвращает САМ active_hack — мутировать его нельзя,
    # иначе движок остаётся со снимками вместо реальных узлов. Собираем отдельный payload.
    payload = {
        **result,
        "target": result["target"].get("name", "?")
                  if isinstance(result.get("target"), dict) else result.get("target", "?"),
        "nodes": HackingSystem.nodes_snapshot(result),
    }
    return jsonify(payload)




@gameplay.route("/api/hacking/action", methods=["POST"])
def api_hack_action():
    data = request.json or {}
    action = data.get("action", "crack_ice")
    # D4a (H1/H2): персонаж передаётся — лут и sanity-урон применяются реально
    result = get_engine().hacking.hack_action(action, character=get_engine().state.character)
    return jsonify(result)




@gameplay.route("/api/investigation/open", methods=["POST"])
def api_investigation_open():
    data = request.json or {}
    result = get_engine().investigation.open_case(
        case_type=data.get("type"),
        custom_name=data.get("name")
    )
    return jsonify(result)




@gameplay.route("/api/investigation/clue", methods=["POST"])
def api_investigation_clue():
    data = request.json or {}
    # D4a (I1): совместимость с UI — панель шлёт description/type, бэк ждёт text/source
    clue_text = data.get("text") or data.get("description", "")
    result = get_engine().investigation.add_clue(
        case_id=data.get("case_id", ""),
        clue_text=clue_text,
        source=data.get("source") or data.get("type", ""),
        reliability=data.get("reliability", "medium"),
    )
    # D4a (I1): UI ждёт флаг success для подтверждения и перерисовки
    result["success"] = True
    return jsonify(result)




@gameplay.route("/api/investigation/suspect", methods=["POST"])
def api_investigation_suspect():
    data = request.json or {}
    # D4a (I3): UI шлёт name, бэк ждёт suspect_name — принимаем оба ключа
    result = get_engine().investigation.add_suspect(
        case_id=data.get("case_id", ""),
        suspect_name=data.get("suspect_name") or data.get("name", ""),
        motive=data.get("motive", ""),
        evidence=data.get("evidence", ""),
    )
    result["success"] = True  # D4a: тот же контрактный флаг для UI
    return jsonify(result)




@gameplay.route("/api/investigation/conclude", methods=["POST"])
def api_investigation_conclude():
    data = request.json or {}
    # D4b: персонаж передаётся — fame за верный вывод начисляется реально
    result = get_engine().investigation.conclude_case(
        case_id=data.get("case_id", ""),
        conclusion=data.get("conclusion", ""),
        suspect_name=data.get("suspect", ""),
        character=get_engine().state.character,
    )
    return jsonify(result)




@gameplay.route("/api/investigation/list", methods=["GET"])
def api_investigation_list():
    # D4a (I2): маппинг полей под UI (clues/required_clues) + leads для контекстных подсказок
    cases_ui = []
    for c in get_engine().investigation.active_cases:
        cases_ui.append({
            **c,
            "clues": c.get("clues_found", []),
            "required_clues": c.get("clues_needed", 5),
            "leads": c.get("leads", []),
        })
    return jsonify({
        "active": cases_ui,
        "closed_count": len(get_engine().investigation.closed_cases),
    })






@gameplay.route("/api/contracts/available", methods=["GET"])
def api_contracts_available():
    """Phase 3: Living World — список доступных контрактов текущей локации/тира."""
    engine = get_engine()
    tier = engine.get_player_influence_tier().get("tier", 0)
    contracts = engine.contract_gen.get_available_contracts(
        location=engine.state.current_location,
        player_tier=tier,
    )
    return jsonify({
        "tier": tier,
        "location": engine.state.current_location,
        "count": len(contracts),
        "contracts": contracts,
    })


@gameplay.route("/api/contracts/accept", methods=["POST"])
def api_contracts_accept():
    """Phase 3 loop (шаг 2): взять процедурный контракт в работу.

    Принимает JSON {"contract_id": "<id>"}.
    Возвращает {"success": True, "quest": {...}} при успехе (HTTP 200),
    либо {"success": False, "error": "...", "code": "..."} (HTTP 400/404).
    """
    data = request.json or {}
    contract_id = data.get("contract_id", "")
    if not contract_id:
        return jsonify({
            "success": False,
            "error": "contract_id обязателен",
            "code": "invalid_id",
        }), 400

    engine = get_engine()
    result = engine.accept_contract(contract_id)

    # Phase 4: фронтенд-доска обновляет HUD из game_state
    if result.get("success"):
        result["game_state"] = engine._get_client_state()
        return jsonify(result), 200

    code = result.get("code", "")
    if code in ("not_found", "no_contracts", "no_location"):
        status = 404
    elif code == "already_accepted":
        status = 409  # Conflict — квест уже взят
    elif code == "invalid_id":
        status = 400
    else:
        status = 400

    return jsonify(result), status


@gameplay.route("/api/contracts/complete", methods=["POST"])
def api_contracts_complete():
    """Phase 3 final close (шаг 1): успешно завершить процедурный контракт.

    Принимает JSON {"contract_id": "<id>"}.
    Возвращает {"success": True, "reward_credits", "reward_xp", "quest"} при успехе (HTTP 200),
    либо {"success": False, "error": "...", "code": "..."} (HTTP 400/404).
    """
    data = request.json or {}
    contract_id = data.get("contract_id", "")
    if not contract_id:
        return jsonify({
            "success": False,
            "error": "contract_id обязателен",
            "code": "invalid_id",
        }), 400

    engine = get_engine()
    result = engine.complete_contract(contract_id)

    if result.get("success"):
        # Phase 4: фронтенд обновляет HUD (кредиты/XP) из game_state
        result["game_state"] = engine._get_client_state()
        return jsonify(result), 200

    code = result.get("code", "")
    if code == "not_found":
        status = 404
    elif code == "invalid_id":
        status = 400
    else:
        status = 400

    return jsonify(result), status
