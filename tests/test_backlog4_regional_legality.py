"""
Backlog#4 (Вариант III): региональная легальность.

Проверяет:
- local_legality: полная и однозначная карта по всем 5 планетам
  (Пояс смягчает, Марс жёстчает, Ганимед освобождает, Земля/Луна = база)
- Чистота функции: без побочных эффектов, неизвестные входы → база
- Витрина отдаёт local_legality по планете местоположения
"""

import pytest

from src.world.simulation import (
    BASE_SHOP_ITEMS, REGIONAL_LEGALITY_MAP, WorldSimulator, local_legality)

PLANETS = ["Земля", "Марс", "Луна", "Пояс астероидов", "Ганимед"]
LEGACY_LEVELS = ["legal", "restricted", "illegal"]


class TestRegionalMap:
    def test_map_covers_only_non_base_planets(self):
        """Земля/Луна сознательно не в карте (база)."""
        assert set(REGIONAL_LEGALITY_MAP.keys()) == {
            "Пояс астероидов", "Марс", "Ганимед"}

    def test_belt_softens(self):
        assert local_legality("illegal", "Пояс астероидов") == "restricted"
        assert local_legality("restricted", "Пояс астероидов") == "legal"

    def test_mars_hardens(self):
        assert local_legality("restricted", "Марс") == "illegal"

    def test_ganymede_frees(self):
        assert local_legality("restricted", "Ганимед") == "legal"

    def test_earth_moon_unchanged(self):
        for lvl in LEGACY_LEVELS:
            assert local_legality(lvl, "Земля") == lvl
            assert local_legality(lvl, "Луна") == lvl

    def test_legal_never_changes_anywhere(self):
        """legal не модифицируется ни на одной планете."""
        for p in PLANETS:
            assert local_legality("legal", p) == "legal"

    def test_unknown_planet_returns_base(self):
        assert local_legality("restricted", "Кванта-7") == "restricted"

    def test_none_and_empty_inputs(self):
        assert local_legality(None, None) == "legal"
        assert local_legality("", "") == "legal"

    def test_purity_no_side_effects(self):
        """Чистая функция: повторный вызов даёт тот же результат,
        карта не мутируется."""
        snapshot = {k: dict(v) for k, v in REGIONAL_LEGALITY_MAP.items()}
        for _ in range(3):
            local_legality("illegal", "Марс")
        assert REGIONAL_LEGALITY_MAP == snapshot

    def test_transitions_are_single_step(self):
        """Переходы только на соседний уровень строгости
        (legal↔restricted↔illegal), без перескоков legal→illegal."""
        allowed = {"legal": {"legal", "restricted"},
                   "restricted": {"legal", "restricted", "illegal"},
                   "illegal": {"restricted", "illegal"}}
        for planet, mods in REGIONAL_LEGALITY_MAP.items():
            for base, local in mods.items():
                assert local in allowed.get(base, set()), \
                    f"{planet}: {base}→{local} — перескок уровней"


class TestShopShowcasesLocalStatus:
    def test_get_shop_items_includes_local_legality(self):
        sim = WorldSimulator()
        items_belt = sim.get_shop_items({"planet": "Пояс астероидов"}, 2)
        restricted = [i for i in items_belt if i["legality"] == "restricted"]
        assert restricted, "нет restricted на Поясе для проверки"
        # все restricted на Поясе должны показывать local=legal
        for it in restricted:
            assert it["local_legality"] == "legal"

    def test_same_item_different_status_by_planet(self):
        sim = WorldSimulator()
        # Адреналиновый насос — restricted в каталоге
        base_id = "I_ADRENALINE"
        found = {}
        for planet in ("Земля", "Пояс астероидов", "Ганимед"):
            items = sim.get_shop_items({"planet": planet}, 5)
            it = next((i for i in items if i["id"] == base_id), None)
            if it:
                found[planet] = it["local_legality"]
        assert found.get("Земля") == "restricted"
        assert found.get("Пояс астероидов") == "legal"
        assert found.get("Ганимед") == "legal"

    def test_all_catalog_items_have_local_field(self):
        sim = WorldSimulator()
        items = sim.get_shop_items({"planet": "Марс"}, 9)
        assert items and all("local_legality" in i for i in items)

    def test_data_source_counts(self):
        """Санити данных: в витрине есть и restricted, и illegal."""
        total_restricted = sum(
            1 for cat in BASE_SHOP_ITEMS.values() for i in cat
            if i.get("legality") == "restricted")
        total_illegal = sum(
            1 for cat in BASE_SHOP_ITEMS.values() for i in cat
            if i.get("legality") == "illegal")
        assert total_restricted >= 10 and total_illegal >= 1
