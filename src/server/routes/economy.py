"""
Auto-generated Blueprint: economy
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
import uuid
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.systems.game_systems import FactionSystem  # Phase 26: shop price modifier
from src.server.routes._deps import get_engine, get_app

economy = Blueprint("economy", __name__)


# Auto-extracted handlers from app.py

def _location_shop_context() -> dict:
    """Phase 27 R3: контекст торговли текущей локации.
    Торговля разрешена только при наличии торгового заведения в месте/районе."""
    engine = get_engine()
    loc = engine.state.current_location
    establishments = engine.galaxy_map.list_establishments(
        loc.get("planet", ""), loc.get("city", ""), loc.get("district", ""))
    place = (loc.get("place") or "").lower()

    TRADE_TYPES = ("market", "shop", "black_market", "commercial", "logistics")
    TRADE_SERVICES = ("оружие", "броня", "импланты", "товары", "снаряжение", "боеприпасы",
                      "электроника", "лекарства", "стимуляторы", "скупка", "чёрный рынок",
                      "запчасти", "модификации", "б/у снаряжение", "б/у товары", "наркотики",
                      "контрабанда", "нелегальный товар", "редкости", "скупка краденого",
                      "военная химия", "боевая химия", "прототипы оружия", "секретные образцы")
    trade_estabs = []
    for e in establishments:
        etype = str(e.get("type", "")).lower()
        services = [str(s).lower() for s in (e.get("services") or [])]
        is_trade = (etype in TRADE_TYPES
                    or any(ts in s for s in services for ts in TRADE_SERVICES))
        if is_trade:
            trade_estabs.append(e)

    # Игрок стоит прямо в торговом заведении или торговое есть в районе
    standing_in_trade = any(e.get("name", "").lower() == place for e in trade_estabs)
    return {
        "allowed": bool(trade_estabs),
        "standing_in_trade": standing_in_trade,
        "trade_establishments": trade_estabs,
        "place": place,
    }


@economy.route("/api/shop")
def api_shop():
    """Get available shop items filtered by location type.
    Phase 27 R3: доступ только при наличии торгового заведения поблизости."""
    ctx = _location_shop_context()
    if not ctx["allowed"]:
        nearest = ", ".join(e.get("name", "?") for e in
                            get_engine().galaxy_map.list_establishments(
                                get_engine().state.current_location.get("planet", ""),
                                get_engine().state.current_location.get("city", ""),
                                get_engine().state.current_location.get("district", ""))) or "—"
        return jsonify({
            "allowed": False,
            "items": [],
            "credits": get_engine().state.character.get("credits", 0),
            "shop_name": "Нет торгового терминала",
            "hint": "Поблизости нет торговых терминалов. Посетите торговую зону района.",
            "nearby_establishments": nearest,
            "location": get_engine().state.current_location,
        })

    tier = get_engine().get_player_influence_tier()["tier"]
    items = get_engine().state.world_sim.get_shop_items(get_engine().state.current_location, tier)
    credits = get_engine().state.character.get("credits", 0)

    # Phase 28 G3: ассортимент зависит от КОНКРЕТНОГО заведения, в котором стоит игрок.
    # Не вошёл в торговую точку → витрина-подсказка вместо свалки из 191 предмета.
    place = (get_engine().state.current_location.get("place") or "").strip()
    shop_name = place or "Торговая зона"
    if not place:
        trade_names = [e.get("name", "?") for e in ctx["trade_establishments"]]
        return jsonify({
            "allowed": True,
            "needs_place_selection": True,
            "items": [],
            "credits": credits,
            "shop_name": "Выберите торговую точку",
            "hint": "Вы в торговой зоне района, но не вошли в конкретное заведение. Выберите точку на радаре (вкладка ЛОКАЦИЯ):",
            "trade_establishments": trade_names,
            "location": get_engine().state.current_location,
        })

    # Профиль заведения: какие категории он продаёт
    est = next((e for e in ctx["trade_establishments"]
                if e.get("name", "").strip() == place), None)
    services_l = [str(s).lower() for s in ((est or {}).get("services") or [])]
    est_type = str((est or {}).get("type", "")).lower()
    place_l = place.lower()

    def _sells(cat: str) -> bool:
        """Продаёт ли это заведение категорию cat."""
        if cat == "weapons" or cat == "armor":
            return ("оружие" in services_l or "броня" in services_l or "боеприпасы" in services_l
                    or "прототипы оружия" in services_l or "чёрный рынок оружия" in services_l
                    or "военный" in est_type or est_type in ("shop", "market") and "оруж" in " ".join(services_l)
                    or "оруж" in place_l or "военторг" in place_l)
        if cat == "implants":
            return ("импланты" in services_l or "модификации" in services_l
                    or "мед" in place_l or "биогеном" in place_l or "клиника" in place_l
                    or "медицин" in est_type)
        if cat == "consumables":
            return ("лекарства" in services_l or "стимуляторы" in services_l
                    or "аптек" in place_l or "мед" in place_l or "крио" in place_l
                    or "биогеном" in place_l
                    or est_type in ("market", "black_market"))
        if cat == "gadgets":
            return ("электроника" in services_l or "научное оборудование" in services_l
                    or "снаряжение" in services_l or "техно" in place_l
                    or est_type in ("shop", "market"))
        if cat == "craft_materials":
            return ("компоненты" in services_l or "запчасти" in services_l
                    or "снаряжение" in services_l or est_type in ("market", "workshop"))
        return est_type in ("market", "black_market")  # «всё на свете»

    before = len(items)
    items = [it for it in items
             if _sells(str(it.get("category", "")).lower()) or it.get("category") == "misc"]
    log_note = f"[Shop] {place}: {len(items)}/{before} предметов по профилю заведения"
    loc = get_engine().state.current_location
    dist_data = get_engine().galaxy_map.get_district(
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
    faction_mod = FactionSystem.get_price_modifier(get_engine().state.faction_reputation, local_factions)
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
        "allowed": True,
        "items": filtered,
        "credits": credits,
        "price_modifier": round(get_engine().state.world_sim.price_modifier * faction_mod, 2),
        "faction_modifier": faction_mod,
        "location": loc,
        "shop_name": shop_name,
        "security": security,
        "standing_in_trade": ctx["standing_in_trade"],
    })




@economy.route("/api/shop/buy", methods=["POST"])
def api_shop_buy():
    """Buy an item from the shop."""
    data = request.json
    item_id = data.get("item_id", "")
    tier = get_engine().get_player_influence_tier()["tier"]
    items = get_engine().state.world_sim.get_shop_items(get_engine().state.current_location, tier)
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Предмет не найден или недоступен"}), 404
    credits = get_engine().state.character.get("credits", 0)
    if credits < item["price"]:
        return jsonify({"error": f"Недостаточно кредитов. Нужно: ₡{item['price']:,}, у вас: ₡{credits:,}"}), 400
    # Фаза 24c B5: heat-риск за нелегальные/ограниченные покупки (Вариант II)
    # Backlog#4 (III): считаем по МЕСТНОМУ статусу, не глобальной метке
    legality = item.get("local_legality") or local_legality(
        item.get("legality", "legal"),
        get_engine().state.current_location.get("planet", ""))
    item["legality"] = legality  # витрина/лог показывают местный статус
    heat_penalty = {"illegal": 3, "restricted": 1}.get(legality, 0)
    # Backlog#4 (III): heat_survival >= 5 снижает штраф на −1 (минимум 1)
    if heat_penalty > 1:
        hs_skill = (get_engine().state.character.get("skills", {}) or {}).get(
            "heat_survival", 0)
        if isinstance(hs_skill, dict):
            hs_skill = hs_skill.get("level", 0)
        if (hs_skill or 0) >= 5:
            reduced = max(1, heat_penalty - 1)
            result_note = f" 🛡 Тепловое выживание {hs_skill}: штраф смягчён."
            heat_penalty = reduced
        else:
            result_note = ""
    else:
        result_note = ""
    if heat_penalty:
        get_engine().state.character["heat"] = get_engine().state.character.get("heat", 0) + heat_penalty
    # Deduct credits and add to inventory
    get_engine().state.character["credits"] = credits - item["price"]
    get_engine().state.inventory.append({
        "id": item["id"], "name": item["name"], "qty": 1,
        "type": item["category"], "stats": item["stats"],
        "rarity": item["rarity"],
    })
    return jsonify({
        "success": True,
        "message": (f"Куплено: {item['name']} за ₡{item['price']:,}"
                    + (f" ⚠ {legality.upper()}: внимание возросло (+{heat_penalty} heat)"
                       if heat_penalty else "") + result_note),
        "credits": get_engine().state.character["credits"],
        "item": item,
        "heat_gained": heat_penalty,
        "local_legality": legality,
    })




@economy.route("/api/shop/sell", methods=["POST"])
def api_shop_sell():
    """Sell an item from inventory (50% of base price).
    Phase 27 R2: принимает name (надёжно) или index (обратно-совместимо)."""
    data = request.json or {}
    inv = get_engine().state.inventory
    item_name = (data.get("name") or "").strip()
    inv_index = data.get("index", -1)
    if item_name:
        idx = next((i for i, it in enumerate(inv)
                    if it.get("name", "").strip().lower() == item_name.lower()), None)
        if idx is None:
            return jsonify({"error": f"«{item_name}» нет в инвентаре"}), 404
        inv_index = idx
    if inv_index < 0 or inv_index >= len(inv):
        return jsonify({"error": "Предмет не найден в инвентаре"}), 404
    item = inv[inv_index]
    # Find base price: first check BASE_SHOP_ITEMS (by id), then STARTING_EQUIPMENT_PRICES (by name)
    from src.world.simulation import BASE_SHOP_ITEMS
    base_price = 5
    item_id = item.get("id", "")
    if item_id:
        for cat, items in BASE_SHOP_ITEMS.items():
            for bi in items:
                if bi["id"] == item_id:
                    base_price = bi["base_price"]
                    break
    if base_price == 5 and item.get("name", "") in STARTING_EQUIPMENT_PRICES:
        base_price = STARTING_EQUIPMENT_PRICES[item["name"]]
    # Фаза 24c B1: floor ₡100 → ₡1 (floor 100 завышал дешёвые материалы в ~14 раз)
    sell_price = max(1, int(base_price * 0.5 * get_engine().state.world_sim.price_modifier))
    get_engine().state.character["credits"] = get_engine().state.character.get("credits", 0) + sell_price
    removed = inv.pop(inv_index)
    return jsonify({
        "success": True,
        "message": f"Продано: {removed['name']} за ₡{sell_price:,}",
        "credits": get_engine().state.character["credits"],
    })





@economy.route("/api/shop/blackmarket")
def api_black_market():
    """Black market shop — illegal/restricted items at markup, requires criminal rep."""
    tier = get_engine().get_player_influence_tier()["tier"]
    # Merge faction_reputation into character dict for black market access check
    bm_character = dict(get_engine().state.character)
    bm_character["faction_reputation"] = get_engine().state.faction_reputation
    items = get_engine().state.world_sim.get_shop_items(
        get_engine().state.current_location, tier,
        include_black_market=True,
        character=bm_character
    )
    credits = get_engine().state.character.get("credits", 0)
    loc = get_engine().state.current_location
    dist_data = get_engine().galaxy_map.get_district(
        loc.get("planet", ""), loc.get("city", ""), loc.get("district", ""))
    local_factions = dist_data.get("factions", []) if dist_data else []
    security = dist_data.get("security", "medium") if dist_data else "medium"
    faction_mod = FactionSystem.get_price_modifier(get_engine().state.faction_reputation, local_factions)

    # Check heat lockout
    heat = get_engine().state.character.get("heat", 0)
    from src.systems.expenses import HEAT_LOCKOUT_THRESHOLD
    lockout = heat >= HEAT_LOCKOUT_THRESHOLD

    # Apply faction price modifier (on top of black market markup)
    if faction_mod != 1.0:
        for item in items:
            item["price"] = int(item["price"] * faction_mod)

    # Generate black market name
    shop_name = "Чёрный Рынок"
    if lockout:
        shop_name += " (ЗАКРЫТ — heat lockout)"

    return jsonify({
        "items": items if not lockout else [],
        "credits": credits,
        "price_modifier": round(get_engine().state.world_sim.price_modifier * faction_mod, 2),
        "faction_modifier": faction_mod,
        "location": loc,
        "shop_name": shop_name,
        "security": security,
        "heat_lockout": lockout,
        "heat": heat,
        "lockout_threshold": HEAT_LOCKOUT_THRESHOLD,
    })





@economy.route("/api/shop/blackmarket/buy", methods=["POST"])
def api_black_market_buy():
    """Buy an item from the black market."""
    data = request.json
    item_id = data.get("item_id", "")
    tier = get_engine().get_player_influence_tier()["tier"]
    # Merge faction_reputation into character dict for black market access check
    bm_character = dict(get_engine().state.character)
    bm_character["faction_reputation"] = get_engine().state.faction_reputation
    items = get_engine().state.world_sim.get_shop_items(
        get_engine().state.current_location, tier,
        include_black_market=True,
        character=bm_character
    )
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return jsonify({"error": "Предмет не найден или недоступен на чёрном рынке"}), 404

    # Check heat lockout
    heat = get_engine().state.character.get("heat", 0)
    from src.systems.expenses import HEAT_LOCKOUT_THRESHOLD
    if heat >= HEAT_LOCKOUT_THRESHOLD:
        return jsonify({"error": "Чёрный рынок временно недоступен: heat lockout (heat ≥ 10)"}), 403

    credits = get_engine().state.character.get("credits", 0)
    if credits < item["price"]:
        return jsonify({"error": f"Недостаточно кредитов. Нужно: ₡{item['price']:,}, у вас: ₡{credits:,}"}), 400

    # Heat penalty for black market purchase (additional risk)
    legality = item.get("local_legality") or item.get("legality", "legal")
    heat_penalty = {"illegal": 3, "restricted": 1}.get(legality, 0)
    
    # If player has criminal rep, no extra risk; otherwise add risk penalty
    from src.systems.game_systems import FACTION_CATEGORIES
    criminal_factions = FACTION_CATEGORIES.get("криминал", [])
    player_rep = get_engine().state.faction_reputation  # rep is on GameState, not character dict
    has_criminal_rep = any(player_rep.get(f, 0) >= 25 for f in criminal_factions)
    
    if not has_criminal_rep:
        # Вариант В: always accessible with risk — extra heat for no criminal ties
        heat_penalty += 1  # additional risk penalty
    
    if heat_penalty:
        get_engine().state.character["heat"] = get_engine().state.character.get("heat", 0) + heat_penalty

    # Deduct credits and add to inventory
    get_engine().state.character["credits"] = credits - item["price"]
    get_engine().state.inventory.append({
        "id": item["id"], "name": item["name"], "qty": 1,
        "type": item["category"], "stats": item["stats"],
        "rarity": item["rarity"],
    })

    from src.systems.expenses import HEAT_RAID_THRESHOLD
    raid_warning = ""
    new_heat = get_engine().state.character["heat"]
    if new_heat >= HEAT_RAID_THRESHOLD and (new_heat - heat_penalty) < HEAT_RAID_THRESHOLD:
        raid_warning = f" ⚠ ВНИМАНИЕ: heat {new_heat} ≥ {HEAT_RAID_THRESHOLD} — возможен рейд!"

    return jsonify({
        "success": True,
        "message": (f"Куплено на чёрном рынке: {item['name']} за ₡{item['price']:,}"
                    + (f" ⚠ {legality.upper()}: +{heat_penalty} heat" if heat_penalty else "")
                    + raid_warning),
        "credits": get_engine().state.character["credits"],
        "item": item,
        "heat_gained": heat_penalty,
        "heat": new_heat,
        "local_legality": legality,
    })






def _load_vehicles_catalog() -> list:
    """Phase 27 D4: реальные корабли из VEHICLES.json (191 КБ, 137 космических судов).
    Возвращает плоский список моделей с полями name/class/category/price/engine/range/..."""
    import json as _json, os as _os
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "..", "..", "..", "game_data", "VEHICLES.json")
    try:
        data = _json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] VEHICLES.json not loaded: {e}")
        return []
    subtypes = (data.get("transportation_types", {}).get("spacecraft", {}) or {}).get("subtypes", {})
    result = []
    for st, models in subtypes.items():
        if not isinstance(models, list):
            continue
        for m in models:
            if not isinstance(m, dict) or not m.get("name"):
                continue
            result.append({
                "name": m.get("name", "?"),
                "ship_class": m.get("class", st),
                "category": m.get("category", st),
                "price": m.get("price", 0),
                "engine": m.get("power_source", ""),
                "range": m.get("range", m.get("operation_range", "")),
                "max_speed": m.get("max_speed", ""),
                "hull": m.get("hull"),
                "armor": m.get("armor"),
                "shields": m.get("shields"),
                "cargo_capacity": m.get("cargo_capacity", m.get("cargo_bays", "")),
                "capacity": m.get("capacity", ""),
                "crew": m.get("crew", ""),
                "features": m.get("features", []),
                "note": m.get("note", ""),
                "condition": m.get("condition", ""),
            })
    return result


@economy.route("/api/ship/catalog", methods=["GET"])
def api_ship_catalog():
    """Phase 27 D4: реальный каталог кораблей из VEHICLES.json."""
    ships = _load_vehicles_catalog()
    # Фильтр/сортировка по категории и цене
    category = request.args.get("category", "").strip().lower()
    if category:
        ships = [s for s in ships if category in (s.get("category") or "").lower()]
    ships.sort(key=lambda s: s.get("price") or 0)
    return jsonify({"ships": ships, "total": len(ships)})


@economy.route("/api/ship/info", methods=["GET"])
def api_ship_info():
    if get_engine().ship.ship:
        return jsonify({"ship": get_engine().ship.ship})
    return jsonify({"ship": None})




@economy.route("/api/ship/buy", methods=["POST"])
def api_ship_buy():
    data = request.json or {}
    credits = get_engine().state.character.get("credits", 0)
    ship_class = data.get("class", "shuttle")
    model_price = data.get("model_price")

    # Phase 27 D4: если класс — имя модели из VEHICLES.json, покупаем по реальной цене
    if ship_class not in ("shuttle", "trader", "fighter", "corvette", "freighter", "gunship"):
        ships = _load_vehicles_catalog()
        model = next((s for s in ships if s["name"] == ship_class), None)
        if not model:
            return jsonify({"error": f"Модель «{ship_class}» не найдена в каталоге"}), 404
        price = int(model_price) if model_price else (model.get("price") or 0)
        if credits < price:
            return jsonify({"error": f"Недостаточно кредитов: нужно ₡{price:,}, у вас ₡{credits:,}"}), 400
        hull = model.get("hull") or 40
        ship_obj = {
            "id": str(uuid.uuid4())[:8],
            "name": data.get("name") or model["name"],
            "class": "model",
            "class_name": model["name"],
            "model_name": model["name"],
            "engine": model.get("engine", ""),
            "range": model.get("range", ""),
            "max_speed": model.get("max_speed", ""),
            "hull": hull, "max_hull": hull,
            "shield_hp": model.get("shields") or 0,
            "max_shield": model.get("shields") or 0,
            "cargo_capacity": model.get("cargo_capacity") or 20,
            "cargo": [],
            "crew_capacity": model.get("crew") or 2,
            "weapon_slots": 2,
            "weapons": [],
            "upgrades": [],
            "speed": 3, "stealth": 1,
            "fuel": 150, "fuel_max": 150, "fuel_per_jump": 15,
            "condition": 100,
        }
        get_engine().ship.ship = ship_obj
        get_engine().state.character["credits"] = credits - price
        return jsonify({"ship_acquired": ship_obj, "cost": price, "credits_left": credits - price})

    result = get_engine().ship.buy_ship(ship_class, data.get("name"),
                                  player_credits=credits)
    # Фаза 23 B3: списание кредитов при успешной покупке
    if result.get("ship_acquired") and "cost" in result:
        get_engine().state.character["credits"] = credits - result["cost"]
    return jsonify(result)




@economy.route("/api/ship/upgrade", methods=["POST"])
def api_ship_upgrade():
    data = request.json or {}
    result = get_engine().ship.install_upgrade(data.get("upgrade_id", ""))
    return jsonify(result)




@economy.route("/api/ship/cargo/load", methods=["POST"])
def api_ship_cargo_load():
    data = request.json or {}
    result = get_engine().ship.load_cargo(data.get("item", ""), data.get("qty", 1))
    return jsonify(result)




@economy.route("/api/ship/refuel", methods=["POST"])
def api_ship_refuel():
    if not get_engine().ship.ship:
        return jsonify({"error": "Нет корабля"})
    s = get_engine().ship.ship
    needed = s["fuel_max"] - s["fuel"]
    cost = needed * 5  # 5₡ per unit
    credits = get_engine().state.character.get("credits", 0)
    if credits < cost:
        return jsonify({"error": f"Нужно {cost}₡, у вас {credits}₡"})
    get_engine().state.character["credits"] = credits - cost
    s["fuel"] = s["fuel_max"]
    return jsonify({"refueled": True, "cost": cost, "fuel": s["fuel"]})




@economy.route("/api/ship/repair", methods=["POST"])
def api_ship_repair():
    result = get_engine().ship.repair()
    if "cost" in result:
        get_engine().state.character["credits"] = get_engine().state.character.get("credits", 0) - result["cost"]
    return jsonify(result)




@economy.route("/api/property/buy", methods=["POST"])
def api_property_buy():
    data = request.json or {}
    credits = get_engine().state.character.get("credits", 0)
    result = get_engine().property.buy_property(
        data.get("type", "apartment"),
        data.get("location", get_engine().state.current_location),
        data.get("name"),
        player_credits=credits,
    )
    # B4: списание кредитов при успешной покупке (паттерн Фазы 23 B3)
    if result.get("acquired") and "cost" in result:
        get_engine().state.character["credits"] = credits - result["cost"]
        result["credits"] = get_engine().state.character["credits"]
    return jsonify(result)




@economy.route("/api/property/types", methods=["GET"])
def api_property_types():
    """B4: каталог типов недвижимости с реальными ценами для UI."""
    from src.systems.subsystems import PROPERTY_TYPES
    types = [{"id": tid, "name": t["name"], "price": t["price"],
              "income": t["income"], "storage": t["storage"],
              "features": t["features"]}
             for tid, t in PROPERTY_TYPES.items()]
    return jsonify({"types": types})




@economy.route("/api/property/list", methods=["GET"])
def api_property_list():
    return jsonify({"properties": get_engine().property.properties})




@economy.route("/api/property/income", methods=["GET"])
def api_property_income():
    return jsonify(get_engine().property.collect_income())




@economy.route("/api/property/store", methods=["POST"])
def api_property_store():
    data = request.json or {}
    result = get_engine().property.store_item(data.get("property_id", ""), data.get("item", ""))
    return jsonify(result)




