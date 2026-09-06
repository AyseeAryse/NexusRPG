"""
Auto-generated Blueprint: world
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.server.routes._deps import get_engine, get_app
from src.utils.region import region_matches as _region_matches
from src.systems.game_systems import FactionSystem  # Phase 23 D3: faction catalog (standing)
from src.systems import LocationEvents  # Phase 27 R-fix: /api/map/move (on_district_change)

world = Blueprint("world", __name__)


# Auto-extracted handlers from app.py

@world.route("/api/world")
def api_world():
    """Get current world state — news, rumors, economy."""
    return jsonify({
        "news_history": get_engine().state.world_sim.news_history[-5:],
        "price_modifier": get_engine().state.world_sim.price_modifier,
        "instability": get_engine().state.world_sim.instability,
        "turn_count": get_engine().state.world_sim.turn_count,
        "last_context": get_engine().state.world_context,
    })




@world.route("/api/map")
def api_map():
    """Get galaxy map overview — planets, routes."""
    planets = get_engine().galaxy_map.list_planets()
    loc = get_engine().state.current_location
    routes = get_engine().galaxy_map.get_routes_from(loc.get("planet", ""))
    return jsonify({
        "planets": planets,
        "current_location": loc,
        "routes": routes,
    })




@world.route("/api/map/location")
def api_map_location():
    """Get current location details — districts, establishments."""
    loc = get_engine().state.current_location
    planet = loc.get("planet", "")
    city = loc.get("city", "")
    district = loc.get("district", "")

    districts = get_engine().galaxy_map.list_districts(planet, city)
    establishments = get_engine().galaxy_map.list_establishments(planet, city, district)
    description = get_engine().galaxy_map.get_location_description(planet, city, district)
    routes = get_engine().galaxy_map.get_routes_from(planet)
    cities = get_engine().galaxy_map.list_cities(planet)

    # Phase 27 D7: карточка района — безопасность/цены/погода/контроль
    district_card = {}
    try:
        dist_data = get_engine().galaxy_map.get_district(planet, city, district) or {}
        # Статус безопасности: нормализация к High/Med/Low
        security_raw = str(dist_data.get("security", ""))
        sec_low = security_raw.lower()
        if any(k in sec_low for k in ("макс", "высок", "high")):
            security_level = "High"
        elif any(k in sec_low for k in ("низк", "low", "опасн")):
            security_level = "Low"
        else:
            security_level = "Med"
        # Модификаторы цен: из типа района + income (богатый район дороже)
        income = str(dist_data.get("income", ""))
        price_mod = 1.0
        if income.lower() in ("высокий", "high", "элитный"):
            price_mod = 1.25
        elif income.lower() in ("низкий", "low", "нищий"):
            price_mod = 0.85
        district_type = dist_data.get("type", "")
        if "corp" in str(district_type).lower() or "корпор" in str(district_type).lower():
            price_mod = max(price_mod, 1.2)
        # Погода/атмосфера: детерминированный рол от даты и локации (без ГСЧ-дёрганья)
        import hashlib as _hashlib
        seed = _hashlib.md5(f"{planet}|{city}|{district}".encode()).hexdigest()
        weathers = {"Земля": ["Дождь, кислотная дымка", "Пасмурно, смог", "Ясно, ветер с океана"],
                    "Марс": ["Пылевая буря на подходе", "Морозная ясность", "Слабая пыль"],
                    "Луна": ["Пыльная мгла", "Стабильный купольный климат", "Метеорный дождь за куполом"],
                    "Пояс астероидов": ["Вакуум, солнечная вспышка", "Вакуум, обломочная тень"],
                    "Ганимед": ["Ледяной шторм", "Тихий холод", "Подлёдное солнце"]}
        weather_list = weathers.get(planet, ["Стабильная атмосфера"])
        weather = weather_list[int(seed[:4], 16) % len(weather_list)]
        district_card = {
            "name": district,
            "type": district_type,
            "security_raw": security_raw or "Средний",
            "security_level": security_level,
            "price_mod": price_mod,
            "weather": weather,
            "control": dist_data.get("control", ""),
            "factions": dist_data.get("factions", []),
            "income": income,
        }
    except Exception as e:
        print(f"[WARN] district card: {e}")

    return jsonify({
        "location": loc,
        "description": description,
        "districts": districts,
        "establishments": establishments,
        "cities": cities,
        "routes": routes,
        "district_card": district_card,
    })




@world.route("/api/map/enter", methods=["POST"])
def api_map_enter():
    """Phase 28 G4: войти в конкретное заведение внутри текущего района.
    Фиксирует current_location.place и возвращает короткую реакцию окружения."""
    import random as _random
    data = request.json or {}
    place = (data.get("place") or "").strip()
    if not place:
        return jsonify({"success": False, "error": "Не указано заведение"}), 400

    engine = get_engine()
    loc = engine.state.current_location
    # Заведение должно существовать в текущем районе
    estabs = engine.galaxy_map.list_establishments(
        loc.get("planet", ""), loc.get("city", ""), loc.get("district", ""))
    est = next((e for e in estabs if e.get("name", "").strip() == place), None)
    if est is None:
        return jsonify({"success": False, "error": f"«{place}» нет в районе {loc.get('district', '?')}"}), 404

    loc["place"] = place
    engine.state.current_location = loc

    # Короткая реакция окружения (без LLM, детерминированно-случайная)
    services = [str(s).lower() for s in (est.get("services") or [])]
    ambience_pool = [
        f"Вы входите в «{place}». {'Запах ' + services[0] if services else 'Привычный шум'} встречает вас у порога.",
        f"Двери «{place}» расходятся с шипением пневматики. Внутри — деловитая суета.",
        f"«{place}» встречает вас полумраком и гулом разговоров постоянных клиентов.",
        f"Вы шагаете в «{place}». Пару взглядов бросают на вас, но интерес быстро гаснет.",
    ]
    ambience = _random.choice(ambience_pool)
    if services:
        ambience += f" Услуги: {', '.join(est.get('services', [])[:4])}."

    return jsonify({
        "success": True,
        "location": loc,
        "place": place,
        "services": est.get("services", []),
        "ambience": ambience,
    })


@world.route("/api/map/move", methods=["POST"])
def api_map_move():
    """Move to a new district, city, or place."""
    data = request.json or {}
    district = data.get("district")
    city = data.get("city")
    planet = data.get("planet")
    place = data.get("place", "")

    engine = get_engine()
    loc = engine.state.current_location
    location_changed = False

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
        location_changed = True
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
        location_changed = True
        travel_event = LocationEvents.on_district_change("Средний")
    elif district and district != loc.get("district"):
        engine._advance_time(30)
        # Get district security for event chance
        dist_data = engine.galaxy_map.get_district(loc.get("planet",""), loc.get("city",""), district)
        security = dist_data.get("security", "Средний") if dist_data else "Средний"
        loc["district"] = district
        location_changed = True
        travel_event = LocationEvents.on_district_change(security)

    loc["place"] = place
    if place != data.get("place", ""):
        location_changed = True
    engine.state.current_location = loc

    if location_changed:
        engine._apply_tone_to_current_location()

    # Maybe auto-spawn NPC in new district (30% chance)
    import random
    new_npc_name = None
    if random.random() < 0.3:
        npc = get_engine().state.npc_registry.generate_npc(
            planet=loc.get("planet", "Земля"), importance="minor"
        )
        new_npc_name = npc.get("name")

    return jsonify({
        "success": True,
        "location": loc,
        "game_time": get_engine().state.game_time,
        "travel_event": travel_event,
        "new_npc": new_npc_name,
    })




@world.route("/api/npcs")
def api_npcs():
    """Get known NPCs from registry."""
    npcs = get_engine().state.npc_registry.get_known_npcs(limit=20)
    return jsonify({
        "npcs": npcs,
        "total": len(get_engine().state.npc_registry.npcs),
    })




@world.route("/api/npcs/catalog")
def api_npcs_catalog():
    """Phase 27 D3: категоризация вместо вываливания всех 168 NPC в кучу.
    Возвращает: contacts (с кем игрок уже говорил), here (только текущая планета/город),
    others (остальной мир, свёрнуто). Все фракции прогнаны через FactionResolver:
    сырые коды CL10/MC1 -> каноничные названия («Кровавый Лотос», ...)."""
    engine = get_engine()
    reg = engine.state.npc_registry
    named = reg._load_named_npcs()
    resolver = getattr(reg, "faction_resolver", None)

    loc = engine.state.current_location or {}
    cur_planet = (loc.get("planet") or "").strip().lower()
    cur_city = (loc.get("city") or "").strip().lower()

    def _faction_name(raw: str) -> str:
        """CL10 -> «Кровавый Лотос»; валидное имя остаётся именем."""
        if not raw:
            return ""
        if resolver:
            try:
                canon = resolver.canonical(raw)
                if canon:
                    rec = resolver.by_id(canon) or resolver.by_name(canon)
                    if rec:
                        return rec.get("name", raw)
            except Exception:
                pass
        return raw

    contacts, here, others = [], [], []
    for nid, rec in sorted(named.items()):
        item = {
            "id": nid,
            "name": rec.get("name", nid),
            "role": rec.get("role", rec.get("title", "")),
            "faction": _faction_name(rec.get("faction", "")),
            "importance": rec.get("importance", ""),
            "location": rec.get("location", rec.get("influence_region", "")),
            "description": rec.get("description", ""),
            "met": nid in reg.npcs,
            "can_call": nid in reg.npcs,   # Phase 27 R6: Вызов активен только для контактов
        }
        item_loc = str(item.get("location") or "")
        loc_low = item_loc.lower()
        # Контакты — с кем уже говорил (зарегистрирован в реестре встреч)
        if item["met"]:
            contacts.append(item)
        elif cur_planet and (cur_planet in loc_low or cur_city and cur_city in loc_low):
            # Phase 27 R6: VIP (major/critical) не сваливаются в уличный список.
            # В локации они видны ТОЛЬКО если их база прямо указана в этом районе.
            cur_district = (loc.get("district") or "").strip().lower()
            base_here = cur_district and cur_district in loc_low
            is_vip = item.get("importance") in ("major", "critical")
            if is_vip and not base_here:
                others.append(item)
            else:
                here.append(item)
        else:
            others.append(item)

    # Контакты отсортируем по важности
    imp_rank = {"critical": 0, "major": 1, "notable": 2, "minor": 3}
    for lst in (contacts, here, others):
        lst.sort(key=lambda x: imp_rank.get(x.get("importance", ""), 9))

    return jsonify({
        "npcs": here,           # обратно-совместимо: старый фронтенд ждёт npcs
        "contacts": contacts,
        "here": here,
        "others_count": len(others),
        "total": len(named),
    })




@world.route("/api/npc/generate", methods=["POST"])
def api_npc_generate():
    """Generate a new NPC."""
    data = request.json or {}
    planet = data.get("planet", get_engine().state.current_location.get("planet", "Земля"))
    role = data.get("role")
    faction = data.get("faction")
    importance = data.get("importance", "minor")

    npc = get_engine().state.npc_registry.generate_npc(
        planet=planet, role=role, faction=faction, importance=importance
    )
    return jsonify({"npc": npc})




@world.route("/api/factions")
def api_factions():
    """Get faction reputation."""
    reps = get_engine().state.faction_reputation
    result = []
    for faction, rep in sorted(reps.items(), key=lambda x: -abs(x[1])):
        result.append({
            "faction": faction,
            "reputation": rep,
            "standing": FactionSystem.get_standing(rep),
        })
    return jsonify({"factions": result})





@world.route("/api/factions/catalog")
def api_factions_catalog():
    """Фаза 23 D3: каталог фракций — контакты (rep) + силы региона (без rep).

    ?planet=Земля — планета игрока для регионального фильтра.
    Прогрессивное раскрытие: full_details только при rep >= 20.
    """
    planet = request.args.get("planet", "")
    reps = get_engine().state.faction_reputation
    catalog = get_engine().kb.files.get("FACTIONS_MASTER.json", {}).get("factions", [])
    factions = [f for f in catalog if "canonical_duplicate_of" not in f]

    # Лидеры из NAMED_NPCS (faction = id фракции)
    leaders_by_fac = {}
    try:
        named = get_engine().state.npc_registry._load_named_npcs()
        for nid, rec in named.items():
            fid = rec.get("faction", "")
            if fid:
                leaders_by_fac.setdefault(fid, []).append({
                    "name": rec.get("name", nid),
                    "role": rec.get("role", rec.get("title", "")),
                })
    except Exception:
        pass

    contacts, regional = [], []
    for f in factions:
        name = f.get("name", "")
        rep = reps.get(name)
        entry = {
            "id": f.get("id", ""),
            "name": name,
            "type": f.get("type", ""),
            "business_area": f.get("business_area", ""),
            "influence_region": f.get("influence_region", ""),
        }
        if rep is not None:
            entry["reputation"] = rep
            entry["standing"] = FactionSystem.get_standing(rep)
            if rep >= 20:  # полная карточка: секреты фракции
                entry["full_details"] = {
                    "history": f.get("history", ""),
                    "legends": f.get("legends", ""),
                    "leaders": leaders_by_fac.get(f.get("id", ""), []),
                    "allies": (f.get("allies") or [])[:3],
                    "enemies": (f.get("enemies") or [])[:3],
                    "mechanics": [
                        f"{m.get('type', '?')}: +{m.get('value', '?')} {m.get('unit', '')}".strip()
                        for m in (f.get("mechanics") or [])
                    ],
                    "plot_hooks": [
                        h.get("description", "") for h in (f.get("plot_hooks") or [])
                    ],
                    "hook_owner": f.get("name", ""),
                }
            contacts.append(entry)
        elif _region_matches(f.get("influence_region", ""), planet):
            regional.append(entry)

    contacts.sort(key=lambda x: -abs(x.get("reputation", 0)))
    return jsonify({"contacts": contacts, "regional": regional, "planet": planet})




@world.route("/api/factions/<path:faction_name>/hook-quest", methods=["POST"])
def api_faction_hook_quest(faction_name):
    """Backlog#3: ручная генерация квеста из plot_hook фракции."""
    quest = get_engine().generate_quest_from_hook(faction_name)
    return jsonify(quest)




@world.route("/api/world/events")
def api_world_events():
    """Get active world events, crises, and consequences."""
    return jsonify({
        "active_crises": [
            {"text": c["text"], "category": c["category"], "severity": c["severity"]}
            for c in get_engine().world_ticker.active_crises if not c.get("resolved")
        ],
        "recent_events": [
            {"text": e["text"], "category": e["category"]}
            for e in get_engine().world_ticker.event_history[-10:]
        ],
        "locked_areas": getattr(get_engine().world_ticker, 'locked_areas', []),
        "pending_consequences": len(get_engine().consequences.pending),
        "triggered_consequences": [
            {"text": c["text"], "severity": c["severity"]}
            for c in get_engine().consequences.triggered[-5:]
        ],
    })




