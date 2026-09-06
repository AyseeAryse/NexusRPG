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
    """Phase 31 Этап 1: тонкий SSE-адаптер над PlayerActionService.run_stream_iter.

    Оркестрация хода (pre/post-LLM мутации, тик мира, квесты, property income)
    теперь существует в ОДНОМ экземпляре — в сервисе. Здесь только SSE-обвязка:
      ("pre", ev)   → yield {"type": "dice"|"mechanical"|"subsystem"|"world_event", "data": ev}
      ("token", t)  → yield {"type": "token", "data": t}
      ("done", res) → ранний выход без токенов (combat/ability/subsystem-combat)
                      конвертируется в jsonify(result) БЕЗ открытия SSE — фронт-ветка
                      L964 (resp.json()) читает его, как и раньше; обычный ход —
                      {"type": "done", "data": res} последним SSE-событием.
    SSE-контракт клиента (app.js L924-953) не изменён.

    Механика peek: первый кортеж достаётся из генератора ДО выбора формата ответа.
    Если это сразу ("done", ...) — ход завершился без LLM (combat/ability/
    subsystem-combat): возвращаем jsonify, как делал старый код. Иначе — SSE.
    """
    engine = get_engine()
    data = request.json
    action = data.get("action", "")
    if not action:
        return jsonify({"error": "Действие не указано"}), 400

    service = engine.player_action_service
    it = service.run_stream_iter(action, stream=True)

    def sse(obj) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    first = next(it, None)
    if first is None:
        # Теоретически недостижимо: run_stream_iter всегда отдаёт done.
        return jsonify({"error": "Пустой ход"}), 500
    kind, payload = first

    if kind == "done":
        # Ранний выход без LLM: combat / ability / subsystem-combat.
        # Формат ответа идентичен прежнему jsonify(result) — фронт-ветка L964.
        return jsonify(payload)

    def stream_from(first_kind, first_payload, rest):
        if first_kind == "pre":
            yield sse({"type": first_payload["type"], "data": first_payload["data"]})
        elif first_kind == "token":
            yield sse({"type": "token", "data": first_payload})
        for kind, payload in rest:
            if kind == "pre":
                yield sse({"type": payload["type"], "data": payload["data"]})
            elif kind == "token":
                yield sse({"type": "token", "data": payload})
            elif kind == "done":
                yield sse({"type": "done", "data": payload})
                return

    return Response(
        stream_with_context(stream_from(kind, payload, it)),
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
