"""
tests/test_living_world.py — Phase 3: Living World приёмочные тесты.

Покрывает:
- FactionConflictSimulator (throttling + Catastrophe Ceiling)
- ContractGenerator (dual-path, tier-based rewards, regional separation)
- Интеграцию с GameEngine._world_tick

Тесты НЕ мокают логику — проверяют реальное поведение на реальных данных.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def fresh_engine():
    """Создаёт GameEngine с минимальным персонажем L1, P0 tier."""
    from src.core.engine import GameEngine
    engine = GameEngine()
    engine.create_custom_character({
        "name": "LivingWorldTest",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_CORP_INFILTRATOR",
        "age": 25,
    })
    return engine


# ========== Test 1: throttling — 10 тиков подряд не дают непрерывных кризисов ==========

def test_faction_conflict_throttling(fresh_engine):
    """Phase 3: Pacing Guard. 10 последовательных тиков не должны генерировать
    кризис в одной локации чаще, чем раз в 4 тика."""
    sim = fresh_engine.faction_sim
    location = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}
    all_events = []
    for tick in range(10):
        events = sim.tick(player_tier=0, current_location=location)
        all_events.extend(events)

    # Подсчитываем количество кризисов по локации.
    # За тик может быть до 2 событий (2 пары фракций), поэтому лимит — max_pairs=2 на локацию за 10 тиков.
    from collections import Counter
    crisis_per_location = Counter(e["location_key"] for e in all_events)

    # Pacing Guard: между тиками с кризисом должно быть ≥4 тика зазор.
    # Проверяем, что ТИКИ с кризисами идут с зазором ≥4 (внутри тика может быть 2 events).
    from collections import Counter
    crisis_ticks_with_count = sorted(Counter(e["tick"] for e in all_events).items())
    for i in range(1, len(crisis_ticks_with_count)):
        prev_tick = crisis_ticks_with_count[i-1][0]
        curr_tick = crisis_ticks_with_count[i][0]
        gap = curr_tick - prev_tick
        assert gap >= 4, (
            f"Pacing Guard нарушен: кризисы на тиках {prev_tick} и {curr_tick} (зазор={gap}, лимит=4)"
        )

    # Если кризисы были — проверим, что между ними есть зазор
    if all_events:
        for event in all_events:
            assert "location_key" in event
            assert "tick" in event
            assert event["tick"] >= 1


# ========== Test 2: Catastrophe Ceiling на P0 — нет системных катастроф ==========

def test_catastrophe_ceiling_tier0(fresh_engine):
    """Phase 3: Catastrophe Ceiling. На тирах P0–P1 запрещены planetary катастрофы
    (blockade/fleet_war/orbital_bombardment/regime_change). За 20 тиков — ни одной."""
    sim = fresh_engine.faction_sim
    location = {"planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр"}
    planetary_types = {"blockade", "fleet_war", "orbital_bombardment", "regime_change"}

    planetary_count = 0
    for tick in range(20):
        events = sim.tick(player_tier=0, current_location=location)
        for e in events:
            if e["type"] in planetary_types:
                planetary_count += 1

    assert planetary_count == 0, (
        f"Catastrophe Ceiling нарушен: {planetary_count} planetary events на P0 за 20 тиков"
    )

    # Также проверяем, что ВСЕ события на P0 имеют scope=local
    for tick in range(20):
        events = sim.tick(player_tier=0, current_location=location)
        for e in events:
            assert e["scope"] == "local", (
                f"Событие {e['type']} имеет scope={e['scope']} (должен быть local на P0)"
            )


def test_catastrophe_ceiling_tier_allowance():
    """Phase 3: на P3+ planetary events РАЗРЕШЕНЫ (проверяем, что tier allowed не запрещает)."""
    from src.world.faction_conflict_sim import FactionConflictSimulator, PLANETARY_INCIDENTS
    sim = FactionConflictSimulator({})  # пустой KB, тестируем только _tier_allowed
    for tier in [0, 1, 2]:
        for inc in PLANETARY_INCIDENTS:
            assert not sim._tier_allowed(tier, inc), (
                f"P{tier} должен блокировать {inc}"
            )
    for tier in [3, 4, 5, 6, 7]:
        for inc in PLANETARY_INCIDENTS:
            assert sim._tier_allowed(tier, inc), (
                f"P{tier} должен РАЗРЕШАТЬ {inc}"
            )


# ========== Test 3: Contract generation — разные контракты для Земли и Цереры ==========

def test_contract_generation_from_hooks(fresh_engine):
    """Phase 3: ContractGenerator — для Земли и Цереры возвращаются разные контракты
    местных фракций с двумя альтернативными путями решения (Dual-Path)."""
    gen = fresh_engine.contract_gen
    tier = 0  # P0

    # Контракты для Земли
    earth_contracts = gen.get_available_contracts(
        location={"planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр"},
        player_tier=tier,
    )
    # Контракты для Цереры
    ceres_contracts = gen.get_available_contracts(
        location={"planet": "Церера", "city": "Станция Бельт-7", "district": "Шахтёрский уровень"},
        player_tier=tier,
    )

    # 1) Оба набора непусты (фракции с plot_hooks есть в обоих регионах)
    assert len(earth_contracts) > 0, "Для Земли не найдено контрактов"
    assert len(ceres_contracts) > 0, "Для Цереры не найдено контрактов"

    # 2) Каждый контракт имеет ≥2 путей (Dual-Path Requirement)
    for c in earth_contracts + ceres_contracts:
        assert "paths" in c, f"Контракт {c.get('id')} не имеет поля paths"
        assert len(c["paths"]) >= 2, (
            f"Контракт {c.get('id')} имеет {len(c['paths'])} путей (нужно ≥2)"
        )
        for path in c["paths"]:
            assert "description" in path, f"Путь без описания в {c.get('id')}"

    # 3) Награды соответствуют tier 0 (1500–4500 ₡)
    for c in earth_contracts + ceres_contracts:
        assert 1500 <= c["reward_credits"] <= 4500, (
            f"Контракт {c['id']} имеет reward_credits={c['reward_credits']} (должно 1500-4500 для Tier 0)"
        )
        assert c["reward_xp"] == 50, (
            f"Контракт {c['id']} имеет reward_xp={c['reward_xp']} (должно 50 для Tier 0)"
        )

    # 4) Контракты Земли и Цереры ПРИНЦИПИАЛЬНО РАЗНЫЕ (разные giver)
    earth_givers = {c["giver"] for c in earth_contracts}
    ceres_givers = {c["giver"] for c in ceres_contracts}
    # Нет полного пересечения (максимум 1 общий giver допустим, но обычно 0)
    overlap = earth_givers & ceres_givers
    assert len(overlap) < min(len(earth_givers), len(ceres_givers)), (
        f"Givers полностью пересекаются между Землёй и Церерой: {overlap}. "
        f"Должны быть разные региональные фракции."
    )
    # Контракты содержат разные ID (стабильные, на основе faction_id + hook_id)
    earth_ids = {c["id"] for c in earth_contracts}
    ceres_ids = {c["id"] for c in ceres_contracts}
    assert not (earth_ids & ceres_ids), (
        f"Контракты Земли и Цереры пересекаются по ID: {earth_ids & ceres_ids}"
    )

    # 5) Каждый контракт имеет стандартную структуру
    required_fields = {"id", "title", "description", "giver", "type",
                       "reward_credits", "reward_xp", "stages", "requirements", "paths"}
    for c in earth_contracts + ceres_contracts:
        missing = required_fields - set(c.keys())
        assert not missing, f"Контракт {c.get('id')} не имеет полей: {missing}"


def test_contract_tier_scaling():
    """Phase 3: TIER_REWARD_RANGES — награды масштабируются по тиру."""
    from src.systems.contract_generator import ContractGenerator, TIER_REWARD_RANGES
    gen = ContractGenerator({})

    # Генерируем 30 контрактов на каждом тире, проверяем диапазон credits и xp
    for tier in [0, 1, 2, 3, 4]:
        rng = TIER_REWARD_RANGES[tier]
        credits_samples = []
        for _ in range(30):
            c, _ = gen._reward_for_tier(tier)
            credits_samples.append(c)
        # credits должны попадать в [rng[0], rng[1]] для данного тира
        assert all(rng[0] <= c <= rng[1] for c in credits_samples), (
            f"Tier {tier}: credits вне диапазона [{rng[0]}, {rng[1]}]: {set(credits_samples)}"
        )

    # Tier 0: 1500-4500 (требование из задания)
    rng0 = TIER_REWARD_RANGES[0]
    assert rng0 == (1500, 4500), f"Tier 0 range должен быть (1500, 4500), получен {rng0}"

    # Tier масштабируется: каждый следующий tier имеет min ≥ предыдущего
    for tier in range(1, 5):
        prev_min = TIER_REWARD_RANGES[tier - 1][0]
        curr_min = TIER_REWARD_RANGES[tier][0]
        assert curr_min > prev_min, (
            f"Tier {tier} min {curr_min} <= Tier {tier-1} min {prev_min}"
        )


# ========== Test 4: Интеграция — _world_tick подключает faction_sim ==========

def test_world_tick_integrates_conflict_sim(fresh_engine, monkeypatch):
    """Phase 3: _world_tick() вызывает faction_sim.tick() и обновляет world_context.local_event.

    Не мокаем faction_sim — проверяем реальную интеграцию после тика.
    """
    # Подавляем долгий AI-вызов, если случайно сработает _world_tick
    # (в данном тесте _world_tick НЕ вызывает AI, но защищаемся)
    import src.core.engine as eng_mod
    monkeypatch.setattr(eng_mod.AIConnector, "generate", lambda **kw: "NARRATIVE: stub\nOPTIONS:\n1. test")

    fresh_engine.state.current_location = {
        "planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр", "place": ""
    }
    fresh_engine._world_tick()

    # world_context должен содержать результат conflict_sim
    # (либо conflict_events, либо нет — зависит от throttling/random)
    # Главное: local_event либо None, либо str
    local_event = fresh_engine.state.world_context.get("local_event")
    assert local_event is None or isinstance(local_event, str), (
        f"local_event должен быть str или None, получен: {type(local_event).__name__}"
    )

    # Проверяем, что faction_sim был вызван (current_tick увеличился)
    assert fresh_engine.faction_sim._current_tick >= 1, (
        f"faction_sim не вызван после _world_tick (current_tick={fresh_engine.faction_sim._current_tick})"
    )


# ========== Test 5: HTTP endpoint /api/contracts/available ==========

def test_api_contracts_available_endpoint(fresh_engine):
    """Phase 3 Blocker #3: GET /api/contracts/available через Flask test_client.

    Проверяет:
    - HTTP-статус строго 200
    - Ответ содержит список контрактов
    - Каждый контракт имеет обязательные поля: title, reward_credits, stages, requirements
    """
    from src.server.app import app

    # Создаём реального персонажа в engine (engine уже инициализирован в fresh_engine)
    app.engine = fresh_engine  # гарантируем, что blueprints используют наш engine

    client = app.test_client()
    # GET /api/contracts/available с location в query-string (если поддерживается)
    # или просто GET — endpoint берёт location из engine.state.current_location
    resp = client.get("/api/contracts/available")
    assert resp.status_code == 200, (
        f"Ожидался HTTP 200, получен {resp.status_code}: {resp.data[:200]}"
    )

    data = resp.get_json()
    assert data is not None, "Ответ не является валидным JSON"
    assert "contracts" in data, f"В ответе нет поля 'contracts': {list(data.keys())}"
    assert "count" in data, f"В ответе нет поля 'count': {list(data.keys())}"
    assert "tier" in data, f"В ответе нет поля 'tier': {list(data.keys())}"

    contracts = data["contracts"]
    assert isinstance(contracts, list), f"contracts должен быть list, получен {type(contracts).__name__}"

    # Каждый контракт имеет обязательные поля
    required_fields = {"title", "reward_credits", "stages", "requirements"}
    for c in contracts:
        missing = required_fields - set(c.keys())
        assert not missing, f"Контракт {c.get('id', '?')} не имеет полей: {missing}"

        # Проверяем типы полей
        assert isinstance(c["title"], str) and c["title"], "title должен быть непустой строкой"
        assert isinstance(c["reward_credits"], (int, float)), "reward_credits должен быть числом"
        assert c["reward_credits"] > 0, f"reward_credits должен быть > 0, получено {c['reward_credits']}"
        assert isinstance(c["stages"], list) and len(c["stages"]) > 0, "stages должен быть непустым list"
        assert isinstance(c["requirements"], dict), "requirements должен быть dict"

        # Dual-Path Requirement: ≥2 paths (Phase 3 задание)
        if "paths" in c:
            assert len(c["paths"]) >= 2, (
                f"Контракт {c.get('id')} имеет {len(c['paths'])} путей (требуется ≥2)"
            )

    # count в ответе соответствует длине списка
    assert data["count"] == len(contracts), (
        f"count={data['count']} не соответствует len(contracts)={len(contracts)}"
    )


# ========== Test 6: NPC↔Faction binding (Phase 3 P0 fix) ==========

def test_named_npc_faction_resolves_to_factions_master():
    """Phase 3 P0 fix: faction у КАЖДОЙ записи NAMED_NPCS.json (с непустым
    faction) после прогона через реестр (NPCRegistry.get_named_npc) должен
    резолвиться в существующую запись в FACTIONS_MASTER.json.

    Полная проверка каталога (100%) — НЕ выборочная.

    Закрывает долг: «Разрыв связывания NAMED_NPCS (CL{i}/MC{i}/SME{i}…) и FACTIONS_MASTER».

    NB: некоторые NPC из NPC_RELATIONS.json (например NPC_002..NPC_004) НЕ имеют
    поля faction — это лайфпат-связи без привязки к конкретной фракции. Тест
    пропускает таких NPC (faction=None/"" → не проверяется).
    """
    from src.world.npc_registry import NPCRegistry
    from src.world.faction_resolver import FactionResolver

    reg = NPCRegistry()
    resolver = FactionResolver()
    assert resolver.is_loaded(), "FactionResolver не смог загрузить FACTIONS_MASTER.json"

    named = reg._load_named_npcs()
    assert len(named) >= 10, f"В NAMED_NPCS.json должно быть ≥10 NPC, найдено {len(named)}"

    # Полный прогон ВСЕХ записей с непустым faction
    with_faction = {k: v for k, v in named.items() if v.get("faction")}
    no_faction = {k: v for k, v in named.items() if not v.get("faction")}
    assert len(with_faction) > 0, "Не найдено ни одного NPC с faction"

    invalid = []
    for npc_id, raw_npc in with_faction.items():
        npc = reg.get_named_npc(npc_id)
        assert npc is not None, f"get_named_npc({npc_id!r}) вернул None"

        # 1) faction непустой после нормализации
        faction_value = npc.get("faction")
        assert faction_value, (
            f"NPC {npc_id} ({npc.get('name')}) потерял faction после normalize"
        )

        # 2) faction резолвится в существующую запись FACTIONS_MASTER
        rec = reg.resolve_npc_faction(npc)
        if rec is None:
            invalid.append((npc_id, npc.get("name"), faction_value))
            continue

        # 3) id записи == нормализованный faction (round-trip 1:1)
        assert rec["id"] == npc["faction"], (
            f"NPC {npc_id}: resolver вернул id={rec['id']!r}, но npc.faction={npc['faction']!r}"
        )

        # 4) faction_valid=True
        assert npc.get("faction_valid") is True, (
            f"NPC {npc_id} ({npc.get('name')}) faction_valid должно быть True"
        )

        # 5) faction_name (человекочитаемое имя) есть
        assert npc.get("faction_name"), (
            f"NPC {npc_id} ({npc.get('name')}) не имеет faction_name после нормализации"
        )

    assert not invalid, (
        f"{len(invalid)} из {len(with_faction)} NPC имеют невалидный faction:\n"
        + "\n".join(f"  - {nid} ({name}): faction={fv!r}" for nid, name, fv in invalid[:20])
        + (f"\n  ... и ещё {len(invalid) - 20}" if len(invalid) > 20 else "")
    )

    # Дополнительно: должно быть НЕ слишком мало записей с faction
    # (валидация каталога). Если 0 — данные сломаны.
    assert len(with_faction) >= 10, (
        f"Должно быть ≥10 NPC с faction, найдено {len(with_faction)}. "
        f"Каталог возможно повреждён."
    )


def test_named_npc_without_faction_does_not_crash():
    """Phase 3 P0 fix: NPC без поля faction (например, NPC_002 из NPC_RELATIONS.json)
    корректно обрабатывается: get_named_npc возвращает NPC, faction_valid=False,
    resolve_npc_faction возвращает None — без падения."""
    from src.world.npc_registry import NPCRegistry

    reg = NPCRegistry()
    named = reg._load_named_npcs()

    no_faction_ids = [k for k, v in named.items() if not v.get("faction")]
    assert len(no_faction_ids) >= 1, (
        f"Ожидался хотя бы 1 NPC без faction (из NPC_RELATIONS.json), найдено {len(no_faction_ids)}"
    )

    npc_id = no_faction_ids[0]
    npc = reg.get_named_npc(npc_id)
    assert npc is not None
    # faction_valid=False (нет faction), но NPC возвращается без падения
    assert npc.get("faction_valid") is False
    assert reg.resolve_npc_faction(npc) is None


def test_faction_resolver_canonical_aliases():
    """Phase 3 P0 fix: FactionResolver нормализует разные формы к одному id."""
    from src.world.faction_resolver import FactionResolver

    r = FactionResolver()
    assert r.is_loaded()

    # id → id (round-trip)
    assert r.canonical("MC1") == "MC1"
    assert r.canonical("CL21") == "CL21"
    assert r.canonical("SME52") == "SME52"

    # name → id
    cid = r.canonical("LunarTech Industries")
    assert cid == "MC1", f"LunarTech Industries должна резолвиться в MC1, получено {cid!r}"

    # case-insensitive по name
    assert r.canonical("lunartech industries") == "MC1"
    assert r.canonical("LUNARTECH INDUSTRIES") == "MC1"

    # resolve по name и id возвращает ту же запись
    a = r.resolve("MC1")
    b = r.resolve("LunarTech Industries")
    assert a is not None and b is not None
    assert a["id"] == b["id"] == "MC1"

    # невалидные значения
    assert r.canonical("НесуществующаяФракция") is None
    assert r.is_valid("") is False
    assert r.is_valid(None) is False


def test_generate_npc_faction_is_always_valid_id():
    """Phase 3 P0 fix: generate_npc() ВСЕГДА нормализует faction к валидному id.

    Проверяет четыре сценария входа:
      - None (рандом) → id
      - name ("LunarTech Industries") → id ("MC1")
      - id ("MC1") → id ("MC1")
      - невалидное значение → fallback к случайному валидному id
    """
    from src.world.npc_registry import NPCRegistry

    reg = NPCRegistry()

    # 1) None → валидный id
    np = reg.generate_npc()
    assert np["faction_valid"] is True, (
        f"random faction {np['faction']!r} не резолвится"
    )
    rec = reg.resolve_npc_faction(np)
    assert rec is not None, f"random faction невалиден: {np['faction']!r}"

    # 2) name → id
    np = reg.generate_npc(faction="LunarTech Industries")
    assert np["faction"] == "MC1", (
        f"name 'LunarTech Industries' должен нормализоваться к 'MC1', получено {np['faction']!r}"
    )
    assert np["faction_name"] == "LunarTech Industries"
    assert np["faction_valid"] is True

    # 3) id → id (round-trip)
    np = reg.generate_npc(faction="MC1")
    assert np["faction"] == "MC1"
    assert np["faction_valid"] is True

    # 4) Невалидное значение → fallback к случайному валидному id
    np = reg.generate_npc(faction="СовсемНеИзвестнаяФракция_ХХХ")
    assert np["faction_valid"] is True, (
        f"Fallback должен быть валидным id, получено {np['faction']!r}"
    )
    rec = reg.resolve_npc_faction(np)
    assert rec is not None, (
        f"Fallback faction невалиден: {np['faction']!r}"
    )


# ========== Test 7: Contract accept loop (Phase 3 loop, шаг 2) ==========

def test_accept_contract_success(fresh_engine):
    """Phase 3 loop (шаг 2): engine.accept_contract() берёт процедурный
    контракт в работу и добавляет его в state.active_quests.

    Проверяет:
      - список доступных контрактов непустой
      - accept_contract() возвращает {"success": True, "quest": {...}}
      - квест появился в engine.state.active_quests
      - поля наград (credits/xp) сохранены и валидны
      - статус = "active", source = "contract_generator"
    """
    # 1) Список доступных контрактов для текущей локации
    contracts = fresh_engine.contract_gen.get_available_contracts(
        location=fresh_engine.state.current_location,
        player_tier=fresh_engine.get_player_influence_tier().get("tier", 0),
    )
    assert len(contracts) > 0, "Нет доступных контрактов — тест не может работать"

    # 2) Берём первый контракт
    target_id = contracts[0]["id"]
    result = fresh_engine.accept_contract(target_id)

    # 3) Структура успешного результата
    assert result.get("success") is True, (
        f"accept_contract вернул success=False: {result}"
    )
    quest = result.get("quest")
    assert quest is not None, "В успешном результате нет поля quest"
    assert quest.get("id") == target_id, (
        f"id квеста {quest.get('id')!r} != {target_id!r}"
    )
    assert quest.get("status") == "active"
    assert quest.get("source") == "contract_generator"

    # 4) Награды — credits/xp в двух форматах (вложенный rewards и плоские дубликаты)
    rewards = quest.get("rewards", {})
    assert isinstance(rewards, dict), "rewards должен быть dict"
    assert "credits" in rewards and "xp" in rewards, \
        f"rewards должны содержать credits и xp, получено: {rewards}"
    assert rewards["credits"] > 0, f"credits должны быть > 0, получено {rewards['credits']}"
    assert rewards["xp"] > 0, f"xp должно быть > 0, получено {rewards['xp']}"
    # Плоские дубликаты для обратной совместимости
    assert quest.get("reward_credits") == rewards["credits"], \
        "reward_credits должен дублировать rewards.credits"
    assert quest.get("reward_xp") == rewards["xp"], \
        "reward_xp должен дублировать rewards.xp"

    # 5) stages, requirements, paths (структура)
    assert isinstance(quest.get("stages"), list) and len(quest["stages"]) > 0, \
        "stages должен быть непустым list"
    assert isinstance(quest.get("paths"), list) and len(quest["paths"]) >= 2, \
        "paths должен быть ≥2 (Dual-Path Requirement)"

    # 6) Квест появился в active_quests
    active_ids = [q.get("id") for q in fresh_engine.state.active_quests]
    assert target_id in active_ids, (
        f"Квест {target_id!r} не появился в active_quests. "
        f"Текущие id: {active_ids}"
    )

    # 7) Повторный accept того же id возвращает already_accepted
    result2 = fresh_engine.accept_contract(target_id)
    assert result2.get("success") is False, \
        "Повторный accept должен вернуть success=False"
    assert result2.get("code") == "already_accepted", \
        f"Ожидался code='already_accepted', получено {result2.get('code')!r}"


def test_accept_contract_not_found(fresh_engine):
    """Phase 3 loop (шаг 2): accept_contract() для несуществующего id
    возвращает code='not_found' без падения."""
    result = fresh_engine.accept_contract("contract_definitely_not_exist_xyz_12345")
    assert result.get("success") is False
    assert result.get("code") == "not_found"


def test_accept_contract_invalid_id(fresh_engine):
    """Phase 3 loop (шаг 2): accept_contract() с пустым/невалидным id
    возвращает code='invalid_id'."""
    # Пустая строка
    r1 = fresh_engine.accept_contract("")
    assert r1.get("success") is False
    assert r1.get("code") == "invalid_id"
    # None
    r2 = fresh_engine.accept_contract(None)
    assert r2.get("success") is False
    assert r2.get("code") == "invalid_id"


def test_api_contracts_accept_endpoint(fresh_engine):
    """Phase 3 loop (шаг 2): POST /api/contracts/accept через Flask test_client.

    Проверяет:
      - HTTP 200 при успешном принятии контракта
      - ответ содержит структуру активного квеста
      - повторный POST с тем же id → HTTP 409 (already_accepted)
      - несуществующий id → HTTP 404 (not_found)
      - пустой body → HTTP 400 (invalid_id)
    """
    from src.server.app import app

    # Гарантируем, что blueprints используют наш engine
    app.engine = fresh_engine
    client = app.test_client()

    # 1) Получаем список доступных контрактов
    resp_avail = client.get("/api/contracts/available")
    assert resp_avail.status_code == 200
    avail_data = resp_avail.get_json()
    assert avail_data.get("count", 0) > 0, "Нет доступных контрактов"
    target_id = avail_data["contracts"][0]["id"]

    # 2) Успешный POST → HTTP 200 + структура квеста
    resp_accept = client.post(
        "/api/contracts/accept",
        json={"contract_id": target_id},
    )
    assert resp_accept.status_code == 200, (
        f"Ожидался HTTP 200, получен {resp_accept.status_code}: "
        f"{resp_accept.data[:200]}"
    )
    body = resp_accept.get_json()
    assert body.get("success") is True
    quest = body.get("quest")
    assert quest is not None
    assert quest.get("id") == target_id
    assert quest.get("status") == "active"
    # Структура наград
    assert "rewards" in quest
    assert quest["rewards"].get("credits", 0) > 0
    assert quest["rewards"].get("xp", 0) > 0
    # stages и paths (Dual-Path)
    assert len(quest.get("stages", [])) > 0
    assert len(quest.get("paths", [])) >= 2

    # 3) Повторный POST → HTTP 409 (conflict)
    resp_repeat = client.post(
        "/api/contracts/accept",
        json={"contract_id": target_id},
    )
    assert resp_repeat.status_code == 409, (
        f"Повторный accept должен дать HTTP 409, получено {resp_repeat.status_code}"
    )
    body_repeat = resp_repeat.get_json()
    assert body_repeat.get("success") is False
    assert body_repeat.get("code") == "already_accepted"

    # 4) Несуществующий id → HTTP 404
    resp_404 = client.post(
        "/api/contracts/accept",
        json={"contract_id": "contract_definitely_not_exist_xyz_12345"},
    )
    assert resp_404.status_code == 404, (
        f"Несуществующий id должен дать HTTP 404, получено {resp_404.status_code}"
    )
    assert resp_404.get_json().get("code") == "not_found"

    # 5) Пустой body → HTTP 400
    resp_400 = client.post("/api/contracts/accept", json={})
    assert resp_400.status_code == 400, (
        f"Пустой body должен дать HTTP 400, получено {resp_400.status_code}"
    )
    assert resp_400.get_json().get("code") == "invalid_id"


# ========== Test 8: Contract complete loop (Phase 3 final close) ==========

def test_complete_contract_flow(fresh_engine):
    """Phase 3 final close: engine.complete_contract() успешно завершает
    процедурный контракт: начисляет награды, переносит в completed_quests.

    Проверяет:
      - награды (credits/xp) начислены корректно
      - квест исчез из active_quests
      - квест появился в completed_quests с status="completed" и completed_at
      - повторный complete возвращает not_found
    """
    # 1) Принимаем контракт
    contracts = fresh_engine.contract_gen.get_available_contracts(
        location=fresh_engine.state.current_location,
        player_tier=fresh_engine.get_player_influence_tier().get("tier", 0),
    )
    assert len(contracts) > 0, "Нет доступных контрактов — тест не может работать"
    target_id = contracts[0]["id"]
    expected_credits = contracts[0]["reward_credits"]
    expected_xp = contracts[0]["reward_xp"]
    assert expected_credits > 0
    assert expected_xp > 0

    acc = fresh_engine.accept_contract(target_id)
    assert acc["success"] is True

    # 2) Фиксируем стартовые значения
    credits_before = fresh_engine.state.character.get("credits", 0)
    xp_before = fresh_engine.state.character.get("xp", 0)

    # 3) Завершаем контракт
    result = fresh_engine.complete_contract(target_id)
    assert result["success"] is True, (
        f"complete_contract вернул success=False: {result}"
    )
    assert result["reward_credits"] == expected_credits, (
        f"reward_credits={result['reward_credits']}, ожидалось {expected_credits}"
    )
    assert result["reward_xp"] == expected_xp

    # 4) Кредиты выросли на сумму награды
    credits_after = fresh_engine.state.character.get("credits", 0)
    xp_after = fresh_engine.state.character.get("xp", 0)
    assert credits_after == credits_before + expected_credits, (
        f"credits: {credits_before} -> {credits_after}, ожидалось +{expected_credits}"
    )
    assert xp_after == xp_before + expected_xp, (
        f"xp: {xp_before} -> {xp_after}, ожидалось +{expected_xp}"
    )

    # 5) Квест исчез из active_quests
    active_ids = [q.get("id") for q in fresh_engine.state.active_quests]
    assert target_id not in active_ids, (
        f"Квест {target_id!r} остался в active_quests: {active_ids}"
    )

    # 6) Квест появился в completed_quests с правильными полями
    completed = [q for q in fresh_engine.state.completed_quests
                 if q.get("id") == target_id]
    assert len(completed) == 1, (
        f"В completed_quests должен быть 1 квест с id={target_id!r}, "
        f"найдено {len(completed)}"
    )
    done = completed[0]
    assert done.get("status") == "completed", \
        f"status={done.get('status')}, ожидалось 'completed'"
    assert done.get("completed_at"), "completed_at не установлен"
    assert done.get("reward_credits_awarded") == expected_credits
    assert done.get("reward_xp_awarded") == expected_xp

    # 7) Повторный complete возвращает not_found
    repeat = fresh_engine.complete_contract(target_id)
    assert repeat["success"] is False
    assert repeat["code"] == "not_found"


def test_complete_contract_invalid_id(fresh_engine):
    """Phase 3 final close: complete_contract() с пустым/None id → invalid_id."""
    r1 = fresh_engine.complete_contract("")
    assert r1["success"] is False
    assert r1["code"] == "invalid_id"
    r2 = fresh_engine.complete_contract(None)
    assert r2["success"] is False
    assert r2["code"] == "invalid_id"


def test_complete_contract_not_in_active(fresh_engine):
    """Phase 3 final close: complete_contract() для несуществующего в
    active_quests id → not_found (без падения)."""
    result = fresh_engine.complete_contract("contract_definitely_not_active_xyz_12345")
    assert result["success"] is False
    assert result["code"] == "not_found"


# ========== Test 9: Save/load roundtrip для контракта ==========

def test_contract_save_load_roundtrip(fresh_engine):
    """Phase 3 final close: принятый контракт сохраняется в сейв и
    восстанавливается в новом экземпляре engine с полным набором полей.

    Проверяет:
      - accept_contract + save_game → файл сейва создан
      - engine2 = GameEngine(); engine2.load_game(slot) → квест в active_quests
      - все вложенные поля квеста (id, title, rewards, stages, paths, ...) на месте
      - delete_save → файл удалён (cleanup)
    """
    import os
    from src.core.engine import GameEngine

    slot_name = "test_contract_save_roundtrip"
    engine2 = None  # declare for finally cleanup

    # 1) Принимаем контракт
    contracts = fresh_engine.contract_gen.get_available_contracts(
        location=fresh_engine.state.current_location,
        player_tier=fresh_engine.get_player_influence_tier().get("tier", 0),
    )
    assert len(contracts) > 0, "Нет доступных контрактов"
    target_id = contracts[0]["id"]
    accepted_quest = fresh_engine.accept_contract(target_id)["quest"]
    expected_rewards = accepted_quest["rewards"]
    expected_title = accepted_quest["title"]

    try:
        # 2) Сохраняем
        save_result = fresh_engine.save_game(slot_name)
        assert save_result.get("success") is True, save_result
        save_path = os.path.join(fresh_engine.saves_dir, f"{slot_name}.json")
        assert os.path.exists(save_path), f"Сейв не создан: {save_path}"

        # 3) Загружаем в новый экземпляр
        engine2 = GameEngine()
        load_result = engine2.load_game(slot_name)
        # load_game возвращает либо {"error": "..."}, либо dict (без явного success)
        if load_result.get("error"):
            # Это OK — load_game не возвращает success, возвращает dict с state
            assert False, f"load_game вернул ошибку: {load_result}"

        # 4) Квест присутствует в engine2.state.active_quests
        restored = [q for q in engine2.state.active_quests
                    if q.get("id") == target_id]
        assert len(restored) == 1, (
            f"В active_quests engine2 должен быть 1 квест с id={target_id!r}, "
            f"найдено {len(restored)}. Все id: "
            f"{[q.get('id') for q in engine2.state.active_quests]}"
        )
        restored_quest = restored[0]

        # 5) Проверяем ключевые поля
        assert restored_quest["id"] == target_id
        assert restored_quest["title"] == expected_title
        assert restored_quest["status"] == "active"
        assert restored_quest["source"] == "contract_generator"
        assert restored_quest["contract_id"] == target_id
        # rewards (вложенный dict)
        assert isinstance(restored_quest.get("rewards"), dict)
        assert restored_quest["rewards"] == expected_rewards
        # Плоские дубликаты для обратной совместимости
        assert restored_quest["reward_credits"] == expected_rewards["credits"]
        assert restored_quest["reward_xp"] == expected_rewards["xp"]
        # stages и paths (списки)
        assert isinstance(restored_quest.get("stages"), list)
        assert len(restored_quest["stages"]) > 0
        assert isinstance(restored_quest.get("paths"), list)
        assert len(restored_quest["paths"]) >= 2

        # 6) Завершаем контракт в engine2, чтобы убедиться что load
        # восстановил state в пригодном для complete состоянии.
        comp = engine2.complete_contract(target_id)
        assert comp["success"] is True
        assert engine2.state.character["credits"] > 0

    finally:
        # 7) Cleanup: удаляем тестовый сейв
        if os.path.exists(os.path.join(fresh_engine.saves_dir, f"{slot_name}.json")):
            os.remove(os.path.join(fresh_engine.saves_dir, f"{slot_name}.json"))
        # engine2.saves_dir может быть тем же
        if hasattr(engine2, "saves_dir"):
            alt_path = os.path.join(engine2.saves_dir, f"{slot_name}.json")
            if alt_path != os.path.join(fresh_engine.saves_dir, f"{slot_name}.json"):
                if os.path.exists(alt_path):
                    os.remove(alt_path)


# ========== Test 10: HTTP endpoint /api/contracts/complete ==========

def test_api_contracts_complete_endpoint(fresh_engine):
    """Phase 3 final close: POST /api/contracts/complete через Flask test_client.

    Проверяет:
      - полный цикл accept → complete через HTTP
      - HTTP 200 при успехе с reward_credits/reward_xp/quest в ответе
      - квест перенесён из active_quests в completed_quests в engine
      - повторный POST → HTTP 404 (not_found)
      - пустой body → HTTP 400 (invalid_id)
    """
    from src.server.app import app
    from src.server.routes._deps import set_engine

    # Сбрасываем active_quests (на случай если previous test оставил квесты)
    fresh_engine.state.active_quests.clear()
    fresh_engine.state.completed_quests.clear()
    # Регистрируем fresh_engine через set_engine() (правильный API),
    # а не через app.engine = ... (это присваивает Flask app, а не модулю).
    set_engine(fresh_engine)
    client = app.test_client()

    # 1) Получаем контракт и принимаем
    avail = client.get("/api/contracts/available").get_json()
    target_id = avail["contracts"][0]["id"]
    expected_credits = avail["contracts"][0]["reward_credits"]

    accept_resp = client.post("/api/contracts/accept",
                              json={"contract_id": target_id})
    assert accept_resp.status_code == 200

    # 2) Завершаем через endpoint
    complete_resp = client.post("/api/contracts/complete",
                                json={"contract_id": target_id})
    assert complete_resp.status_code == 200, (
        f"Ожидался HTTP 200, получен {complete_resp.status_code}: "
        f"{complete_resp.data[:200]}"
    )
    body = complete_resp.get_json()
    assert body["success"] is True
    assert body["reward_credits"] == expected_credits
    assert body["reward_xp"] > 0
    assert body.get("quest")
    assert body["quest"]["status"] == "completed"
    assert body["quest"]["completed_at"]

    # 3) Состояние engine изменилось
    active_ids = [q.get("id") for q in fresh_engine.state.active_quests]
    assert target_id not in active_ids
    completed_ids = [q.get("id") for q in fresh_engine.state.completed_quests]
    assert target_id in completed_ids

    # 4) Повторный POST → HTTP 404
    repeat = client.post("/api/contracts/complete",
                         json={"contract_id": target_id})
    assert repeat.status_code == 404
    assert repeat.get_json()["code"] == "not_found"

    # 5) Пустой body → HTTP 400
    empty = client.post("/api/contracts/complete", json={})
    assert empty.status_code == 400
    assert empty.get_json()["code"] == "invalid_id"
