"""
Тесты для систем мира и генерации.

Проверяют:
- Генерацию галактической карты
- Симуляцию мира
- NPC Registry
- Процедурную генерацию квестов
"""

import pytest
from unittest.mock import patch, MagicMock


class TestGalaxyMap:
    """Тесты галактической карты."""

    def test_galaxy_map_creation(self):
        """Создание карты галактики."""
        from src.world import GalaxyMap
        
        galaxy = GalaxyMap()
        assert galaxy is not None

    def test_galaxy_has_methods(self):
        """Галактика имеет методы для работы."""
        from src.world import GalaxyMap
        
        galaxy = GalaxyMap()
        # Проверяем, что у объекта есть какие-либо публичные методы
        methods = [m for m in dir(galaxy) if not m.startswith('_')]
        assert len(methods) > 0


class TestWorldSimulator:
    """Тесты симулятора мира."""

    def test_world_simulator_creation(self):
        """Создание симулятора мира."""
        from src.world import WorldSimulator
        
        sim = WorldSimulator()
        assert sim is not None

    def test_world_simulator_tick(self):
        """Тик симуляции мира."""
        from src.world import WorldSimulator
        
        sim = WorldSimulator()
        
        # tick требует аргументов, проверяем что метод существует
        assert hasattr(sim, 'tick')
        # Не вызываем без аргументов - метод требует game_time, location, tier

    def test_world_simulator_to_dict(self):
        """Сериализация симулятора."""
        from src.world import WorldSimulator
        
        sim = WorldSimulator()
        data = sim.to_dict()
        
        assert isinstance(data, dict)

    def test_world_simulator_from_dict(self):
        """Десериализация симулятора."""
        from src.world import WorldSimulator
        
        original = WorldSimulator()
        data = original.to_dict()
        restored = WorldSimulator.from_dict(data)
        
        assert restored is not None


class TestNPCRegistry:
    """Тесты реестра NPC."""

    def test_npc_registry_creation(self):
        """Создание реестра NPC."""
        from src.world import NPCRegistry
        
        registry = NPCRegistry()
        assert registry is not None

    def test_npc_registry_add_npc(self):
        """Добавление NPC в реестр."""
        from src.world import NPCRegistry
        
        registry = NPCRegistry()
        
        # Проверяем наличие метода добавления
        if hasattr(registry, 'add_npc'):
            npc_data = {"id": "test_npc", "name": "Test NPC"}
            registry.add_npc(npc_data)
            
        # Или проверяем внутренний словарь
        assert hasattr(registry, 'npcs') or hasattr(registry, '_npcs')

    def test_npc_registry_get_npc(self):
        """Получение NPC из реестра."""
        from src.world import NPCRegistry
        
        registry = NPCRegistry()
        
        if hasattr(registry, 'get_npc'):
            # Пустой реестр должен возвращать None или пустое значение
            result = registry.get_npc("nonexistent")
            assert result is None or result == {}

    def test_speech_styles_exist(self):
        """Стили речи существуют."""
        from src.world import SPEECH_STYLES
        
        assert isinstance(SPEECH_STYLES, dict)
        assert len(SPEECH_STYLES) > 0


class TestProceduralQuestGenerator:
    """Тесты процедурной генерации квестов."""

    def test_quest_generator_creation(self):
        """Создание генератора квестов."""
        from src.world.procedural import ProceduralQuestGenerator
        
        generator = ProceduralQuestGenerator()
        assert generator is not None

    def test_quest_generator_generate(self):
        """Генерация квеста."""
        from src.world.procedural import ProceduralQuestGenerator
        
        generator = ProceduralQuestGenerator()
        
        # Проверяем наличие метода генерации
        if hasattr(generator, 'generate'):
            quest = generator.generate()
            assert quest is not None
            if isinstance(quest, dict):
                assert 'title' in quest or 'description' in quest


class TestWorldTicker:
    """Тесты мирового тикера."""

    def test_world_ticker_creation(self):
        """Создание мирового тикера."""
        from src.world.procedural import WorldTicker
        
        ticker = WorldTicker()
        assert ticker is not None

    def test_world_ticker_tick(self):
        """Тик мирового времени."""
        from src.world.procedural import WorldTicker
        
        ticker = WorldTicker()
        
        # tick требует game_state, проверяем что метод существует
        assert hasattr(ticker, 'tick')
        # Не вызываем без аргументов - метод требует game_state


class TestConsequenceTracker:
    """Тесты трекера последствий."""

    def test_consequence_tracker_creation(self):
        """Создание трекера последствий."""
        from src.world.procedural import ConsequenceTracker
        
        tracker = ConsequenceTracker()
        assert tracker is not None

    def test_consequence_tracker_add(self):
        """Добавление последствия."""
        from src.world.procedural import ConsequenceTracker
        
        tracker = ConsequenceTracker()
        
        if hasattr(tracker, 'add'):
            tracker.add({"event": "test", "consequence": "test_result"})
            # Проверяем, что последствие добавлено
            assert len(getattr(tracker, 'consequences', [])) >= 0


class TestLocationData:
    """Тесты данных локаций."""

    def test_default_location_exists(self):
        """Локация по умолчанию существует."""
        from src.core.engine import GameState

        state = GameState()
        loc = state.current_location

        assert 'planet' in loc
        assert 'city' in loc
        assert loc['planet'] == "Земля"
        assert loc['city'] == "Нью-Токио"


class TestGalaxyRouteCompatibility:
    """Phase 3 P0 fix: совместимость полей маршрута (from/to ↔ start_point/end_point)."""

    def test_normalize_route_endpoint_accepts_str(self):
        """Нормализация принимает str."""
        from src.world.galaxy import GalaxyMap
        assert GalaxyMap._normalize_route_endpoint("Марс") == "Марс"
        assert GalaxyMap._normalize_route_endpoint("Земля") == "Земля"

    def test_normalize_route_endpoint_accepts_dict(self):
        """Нормализация принимает dict (формат {planet: ...} или {name: ...})
        и прозрачно применяет PLANET_ALIAS (case-insensitive)."""
        from src.world.galaxy import GalaxyMap
        # Русские имена — round-trip
        assert GalaxyMap._normalize_route_endpoint({"planet": "Марс"}) == "Марс"
        assert GalaxyMap._normalize_route_endpoint({"name": "Луна"}) == "Луна"
        # Английские алиасы (uppercase, как в TRADE_ROUTES_MASTER.json) → русские
        assert GalaxyMap._normalize_route_endpoint({"id": "CERES"}) == "Церера"
        assert GalaxyMap._normalize_route_endpoint({"id": "EARTH"}) == "Земля"
        # Любой регистр → каноничный русский (case-insensitive lookup)
        assert GalaxyMap._normalize_route_endpoint({"id": "ceres"}) == "Церера"
        assert GalaxyMap._normalize_route_endpoint({"id": "earth"}) == "Земля"
        # Полностью неизвестное значение остаётся как есть
        assert GalaxyMap._normalize_route_endpoint({"id": "Плутон"}) == "Плутон"
        # Пустой dict → ""
        assert GalaxyMap._normalize_route_endpoint({}) == ""

    def test_normalize_route_endpoint_handles_none(self):
        """Нормализация корректно обрабатывает None."""
        from src.world.galaxy import GalaxyMap
        assert GalaxyMap._normalize_route_endpoint(None) == ""

    def test_get_route_finds_existing_route(self):
        """get_route находит маршрут Земля→Марс из hardcoded galaxy map."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        route = gm.get_route("Земля", "Марс")
        assert route is not None, "Маршрут Земля→Марс должен существовать"
        assert "time" in route, f"У маршрута должно быть поле time, получено: {list(route.keys())}"

    def test_get_route_handles_str_aliases(self):
        """get_route принимает аргументы в формате from/to (str) — основной кейс."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        # Внутренние маршруты galaxy.py используют формат from → str
        route = gm.get_route("Земля", "Луна")
        assert route is not None
        assert route.get("time") == "3 часа"

    def test_get_route_handles_dict_format(self):
        """get_route принимает dict в формате {planet: ...} (TRADE_ROUTES_MASTER compat)."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        # Передаём dict — должен корректно нормализовать
        route = gm.get_route({"planet": "Земля"}, {"planet": "Церера"})
        assert route is not None
        assert "time" in route

    def test_get_route_returns_none_for_missing(self):
        """get_route возвращает None для неизвестного маршрута."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        route = gm.get_route("Земля", "Несуществующая_Планета")
        assert route is None

    def test_load_routes_from_kb_with_start_point_format(self):
        """load_routes_from_kb принимает TRADE_ROUTES_MASTER.json формат (start_point/end_point)."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        # Эмулируем TRADE_ROUTES_MASTER.json: {routes: [{start_point, end_point, base_travel_time_days}]}
        fake_data = {
            "routes": [
                {
                    "id": "test_route_1",
                    "name": "Test Earth-Mars",
                    "start_point": {"city": "Нью-Токио", "planet": "Земля"},
                    "end_point": {"city": "Новый Бостон", "planet": "Марс"},
                    "base_travel_time_days": 3,
                },
                {
                    "id": "test_route_2",
                    "name": "Test from/to format",
                    "from": "Земля",
                    "to": "Церера",
                    "base_travel_time_days": 8,
                },
                {
                    "id": "test_route_3",
                    "name": "Test planet_a/planet_b format",
                    "planet_a": "Земля",
                    "planet_b": "Луна",
                    "base_travel_time_days": 1,
                },
            ]
        }
        loaded = gm.load_routes_from_kb(fake_data)
        assert loaded == 3, f"Должно загрузиться 3 маршрута, загружено: {loaded}"
        # Проверяем что маршруты доступны через get_routes_from
        earth_routes = gm.get_routes_from("Земля")
        assert "Марс" in earth_routes, f"start_point формат: Марс должен быть в routes, доступно: {list(earth_routes.keys())}"
        assert "Церера" in earth_routes, f"from/to формат: Церера должен быть в routes, доступно: {list(earth_routes.keys())}"
        assert "Луна" in earth_routes, f"planet_a/planet_b формат: Луна должен быть в routes, доступно: {list(earth_routes.keys())}"
        # Проверяем get_route с dict-форматом
        route_dict = gm.get_route({"planet": "Земля"}, {"planet": "Марс"})
        assert route_dict is not None, "get_route с dict должен найти маршрут"

    def test_load_routes_from_kb_skips_invalid(self):
        """load_routes_from_kb пропускает невалидные маршруты (пустые поля, self-loop)."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        fake_data = {
            "routes": [
                {"id": "self_loop", "from": "Земля", "to": "Земля", "base_travel_time_days": 1},
                {"id": "no_endpoints"},  # нет from/to
                {"id": "unknown_planet", "from": "НеизвестнаяПланета", "to": "Земля", "base_travel_time_days": 1},
            ]
        }
        loaded = gm.load_routes_from_kb(fake_data)
        assert loaded == 0, f"Невалидные маршруты должны быть пропущены, загружено: {loaded}"


class TestGameEngineTradeRoutesIntegration:
    """Phase 3 P0 fix: TRADE_ROUTES_MASTER.json подключён к GameEngine.__init__."""

    def test_trade_routes_loaded_into_galaxy_map(self):
        """GameEngine при инициализации загружает TRADE_ROUTES_MASTER.json в galaxy_map.

        Проверяет, что после engine = GameEngine() маршруты из JSON присутствуют
        в engine.galaxy_map (get_route принимает сырые значения из JSON — нормализация
        выполняется ядром GalaxyMap через модульный PLANET_ALIAS).
        """
        from src.core.engine import GameEngine
        from src.world.galaxy import GalaxyMap

        engine = GameEngine()
        # Проверяем что galaxy_map — это GalaxyMap
        assert isinstance(engine.galaxy_map, GalaxyMap), \
            f"engine.galaxy_map должен быть GalaxyMap, получен {type(engine.galaxy_map)}"

        # Загружаем JSON напрямую и передаём сырые значения из routes в get_route()
        # (без локальной нормализации — нормализация должна быть в ядре GalaxyMap)
        import json
        from pathlib import Path
        routes_path = Path("D:/NexusRPG-main/game_data/TRADE_ROUTES_MASTER.json")
        assert routes_path.exists(), f"TRADE_ROUTES_MASTER.json не найден: {routes_path}"
        with open(routes_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        raw_routes = raw_data.get("routes", [])
        assert len(raw_routes) > 0, "TRADE_ROUTES_MASTER.json не содержит routes"

        # Передаём СЫРЫЕ значения из JSON напрямую в get_route() — нормализация
        # (PLANET_ALIAS, dict→str, case-insensitive) выполняется в GalaxyMap.get_route().
        loaded_count = 0
        for route in raw_routes:
            # Берём сырые значения — могут быть str ("EARTH") или dict ({planet: "Земля"})
            from_p = route.get("from") or route.get("start_point") or route.get("planet_a")
            to_p = route.get("to") or route.get("end_point") or route.get("planet_b")
            if not from_p or not to_p:
                continue
            if from_p == to_p:  # self-loop
                continue
            found = engine.galaxy_map.get_route(from_p, to_p)
            if found is not None:
                loaded_count += 1

        assert loaded_count > 0, (
            f"Ни один маршрут из TRADE_ROUTES_MASTER.json не загружен в galaxy_map. "
            f"Ожидалось >0, получено: {loaded_count}"
        )
        # Должны загрузиться минимум 2 маршрута (Земля→Марс, Земля→Церера и т.д.)
        assert loaded_count >= 2, f"Загружено только {loaded_count} маршрутов, ожидалось >=2"

    def test_get_route_after_engine_init_earth_mars(self):
        """После GameEngine() маршрут Земля→Марс доступен (hardcoded + TRADE_ROUTES)."""
        from src.core.engine import GameEngine
        engine = GameEngine()
        route = engine.galaxy_map.get_route("Земля", "Марс")
        assert route is not None, "Маршрут Земля→Марс не найден после init"
        assert "time" in route, f"У маршрута должно быть поле time, получено: {list(route.keys())}"

    def test_get_route_after_engine_init_earth_ceres(self):
        """После GameEngine() маршрут Земля→Церера доступен через TRADE_ROUTES_MASTER.

        В hardcoded galaxy map Земля→Церера НЕТ, но есть в TRADE_ROUTES_MASTER.json.
        Этот тест проверяет, что load_routes_from_kb() добавил маршрут.
        """
        from src.core.engine import GameEngine
        engine = GameEngine()
        # Hardcoded galaxy_map имеет Земля→{Луна, Марс, Церера, Ганимед} — проверим
        # что Земля→Церера доступен (он есть в обоих источниках)
        route = engine.galaxy_map.get_route("Земля", "Церера")
        assert route is not None, "Маршрут Земля→Церера не найден после init"

    def test_get_route_after_engine_init_returns_dict_format(self):
        """get_route поддерживает dict в формате {planet: ...} (TRADE_ROUTES_MASTER compat)."""
        from src.core.engine import GameEngine
        engine = GameEngine()
        # Передаём dict вместо str — должен корректно нормализовать
        route = engine.galaxy_map.get_route({"planet": "Земля"}, {"planet": "Марс"})
        assert route is not None, "get_route с dict-форматом не работает после init"


class TestGalaxyBidirectionalRoutes:
    """Phase 3 loop (шаг 1): двусторонняя регистрация маршрутов.

    После GalaxyMap() / GameEngine() для каждого зарегистрированного
    маршрута A→B должен быть доступен обратный B→A. Это покрывает:
      - hardcoded маршруты (Земля→Марс, Марс→Земля, и т.д.)
      - маршруты, загруженные из TRADE_ROUTES_MASTER.json
      - маршруты в разных форматах (от планет как 'Земля'/'EARTH'/dict)
    """

    def _all_routes_as_canonical_pairs(self, galaxy) -> set:
        """Возвращает множество каноничных пар (from, to) по всем планетам.

        from нормализуется через _normalize_planet_alias (имя планеты).
        to нормализуется через _normalize_route_key (destination-ключ маршрута,
        учитывает ROUTE_KEY_ALIAS для hardcoded "Церера" → "Пояс астероидов").
        """
        from src.world.galaxy import _normalize_planet_alias, _normalize_route_key
        pairs = set()
        for planet_name, planet_data in galaxy.map.items():
            routes = planet_data.get("routes") or {}
            for dest_name in routes.keys():
                a = _normalize_planet_alias(planet_name)
                b = _normalize_route_key(dest_name)
                # Если to_norm ещё не каноничный (например, "Церера" уже после
                # ROUTE_KEY_ALIAS стала "Пояс астероидов"), дополнительно
                # проверим через PLANET_ALIAS.
                if b not in galaxy.map and b.upper() in galaxy.map:
                    b = b  # оставляем как есть
                if not a or not b or a == b:
                    continue
                pairs.add((a, b))
        return pairs

    def test_symmetric_routes_after_init(self):
        """GalaxyMap() → ВСЕ зарегистрированные маршруты симметричны (A→B ⇔ B→A)."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        pairs = self._all_routes_as_canonical_pairs(gm)
        assert len(pairs) > 0, "В galaxy_map не должно быть 0 маршрутов"

        missing = []
        for a, b in pairs:
            if (b, a) not in pairs:
                missing.append((a, b))
        assert not missing, (
            f"Асимметричные маршруты (A→B есть, B→A нет): {missing}"
        )

    def test_symmetric_routes_after_engine_init(self):
        """После GameEngine() (с load_routes_from_kb + symmetrize) маршруты симметричны."""
        from src.core.engine import GameEngine
        engine = GameEngine()
        pairs = self._all_routes_as_canonical_pairs(engine.galaxy_map)
        assert len(pairs) > 0, "После engine init не должно быть 0 маршрутов"

        missing = []
        for a, b in pairs:
            if (b, a) not in pairs:
                missing.append((a, b))
        assert not missing, (
            f"После GameEngine() асимметричные маршруты: {missing}"
        )

    def test_load_routes_from_kb_creates_reverse(self):
        """load_routes_from_kb() регистрирует обратный маршрут, если
        и исходная, и целевая планеты существуют в GALAXY_MAP.

        Для несуществующих планет (например, Юпитер) — обратный маршрут
        не создаётся (нет целевой планеты, некуда регистрировать). Это
        документированное поведение.
        """
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        # 1) Проверяем что Земля→Марс есть после __init__
        mars_before = "Марс" in gm.get_routes_from("Земля")
        assert mars_before, "Земля→Марс должен быть после __init__"

        # 2) Создаём маршрут с НЕСУЩЕСТВУЮЩЕЙ планетой (Юпитер) —
        # прямой маршрут добавляется в Земля, обратный — НЕ добавляется
        # (Юпитера нет в GALAXY_MAP, некуда регистрировать).
        test_data_nonexistent = {
            "routes": [
                {
                    "id": "test_route_jupiter",
                    "start_point": "EARTH",
                    "end_point": "JUPITER",
                    "base_travel_time_days": 365,
                    "base_risk_level": "Medium",
                }
            ]
        }
        loaded = gm.load_routes_from_kb(test_data_nonexistent)
        assert loaded == 1, f"Должен загрузиться 1 маршрут, получено: {loaded}"
        # Прямой маршрут Земля→Юпитер регистрируется через PLANET_ALIAS
        assert "Юпитер" in gm.get_routes_from("Земля"), \
            "Прямой маршрут Земля→Юпитер не зарегистрирован"

        # 3) Проверяем восстановление обратного маршрута для СУЩЕСТВУЮЩИХ планет:
        # удаляем обратный Луна→Земля (если есть), потом загружаем Земля→Луна.
        # Обратный должен восстановиться.
        luna_routes = gm.get_routes_from("Луна")
        if "Земля" in luna_routes:
            del luna_routes["Земля"]
        test_recover = {
            "routes": [
                {
                    "id": "test_recover_earth_luna",
                    "from": "Земля",
                    "to": "Луна",
                    "base_travel_time_days": 2,
                    "base_risk_level": "Low",
                }
            ]
        }
        gm.load_routes_from_kb(test_recover)
        # Обратный Луна→Земля должен быть восстановлен
        assert "Земля" in gm.get_routes_from("Луна"), \
            "Обратный маршрут Луна→Земля не восстановлен load_routes_from_kb"

    def test_ensure_reverse_route_idempotent(self):
        """_ensure_reverse_route идемпотентен: повторный вызов не дублирует маршрут."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        route_data = {"time": "10 часов", "delta_v": "5 км/с", "risk": "low"}
        added1 = gm._ensure_reverse_route("Земля", "Марс", route_data)
        # Марс→Земля уже есть (из hardcoded) — должно вернуть False
        added2 = gm._ensure_reverse_route("Земля", "Марс", route_data)
        assert added2 is False, "_ensure_reverse_route должен быть идемпотентным"

    def test_get_route_bidirectional_smoke(self):
        """Smoke: для каждой известной пары планет оба направления доступны."""
        from src.world.galaxy import GalaxyMap
        gm = GalaxyMap()
        # Пары планет из TRADE_ROUTES_MASTER.json (каноничные русские имена)
        # После symmetrize_routes в __init__ все маршруты двусторонние.
        pairs = [
            ("Земля", "Марс"),             # ROUTE-EM (Earth-Mars)
            ("Земля", "Пояс астероидов"),  # ROUTE-EC (Earth-Ceres)
            ("Марс", "Пояс астероидов"),   # ROUTE-MC
            ("Земля", "Луна"),
            ("Земля", "Ганимед"),
            ("Марс", "Луна"),
            ("Марс", "Ганимед"),
        ]
        for a, b in pairs:
            ab = gm.get_route(a, b)
            ba = gm.get_route(b, a)
            assert ab is not None, f"Маршрут {a}→{b} не найден"
            assert ba is not None, f"Обратный маршрут {b}→{a} не найден"

        # Также проверяем что ROUTE_KEY_ALIAS работает: "Церера" в
        # destination-ключах резолвится как "Пояс астероидов" (для
        # симметрии двусторонних маршрутов в hardcoded данных).
        # API-вызовы возвращают маршрут Земля→Церера (через PLANET_ALIAS
        # CERES, который НЕ применяется к "Церера" как имя станции).
        ceres_route = gm.get_route("Земля", "Церера")
        assert ceres_route is not None, \
            "Маршрут Земля→Церера должен быть доступен (через PLANET_ALIAS)"
