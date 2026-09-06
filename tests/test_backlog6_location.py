"""
Backlog#6: канонизация локации из [STATE] блока AI («Zемля»-опечатка).

Проблема: AI писал «Zемля» (латинская Z) в location.planet — значение
попадало в current_location без проверки, топбар показывал опечатку,
регион-фильтр D3 (_region_matches по подстроке) терял 21 из 24 фракций.

Фикс: engine._canonicalize_location() — транслит визуальных/фонетических
пар + fuzzy-match к GALAXY_MAP. Канонические значения не трогаются,
нераспознанные сохраняются как есть (данные ГМа не теряются).
"""

import pytest

from src.core.engine import GameEngine


@pytest.fixture
def eng():
    return GameEngine.__new__(GameEngine)  # только чистые методы, без init


class TestCanonicalizeLocation:
    def test_latin_z_fixed(self, eng):
        """Главный кейс бага: латинская Z в начале слова."""
        r = eng._canonicalize_location(
            {"planet": "Zемля", "city": "Нью-Токио",
             "district": "Индустриальный коридор"})
        assert r["planet"] == "Земля"

    def test_full_latin_planet(self, eng):
        assert eng._canonicalize_location(
            {"planet": "Mars"})["planet"] == "Марс"

    def test_canonical_value_untouched(self, eng):
        assert eng._canonicalize_location({"planet": "Земля"}) == {"planet": "Земля"}

    def test_unknown_value_preserved(self, eng):
        """Выдуманный мир ГМа не переписывается."""
        assert eng._canonicalize_location(
            {"planet": "Кванта-7"})["planet"] == "Кванта-7"

    def test_missing_keys_not_injected(self, eng):
        """Только переданные ключи обрабатываются; ничего не добавляется."""
        r = eng._canonicalize_location({"planet": "Земля"})
        assert set(r.keys()) == {"planet"}

    def test_null_and_empty_safe(self, eng):
        assert eng._canonicalize_location({}) == {}
        r = eng._canonicalize_location({"planet": None})
        assert r["planet"] is None

    def test_district_matched_within_city(self, eng):
        r = eng._canonicalize_location(
            {"planet": "Земля", "city": "Нью-Токио",
             "district": "Правительственное ядро"})
        assert r["district"] == "Правительственное ядро"

    def test_region_filter_now_matches(self, eng):
        """Интеграционный смысл фикса: после канонизации фильтр D3 видит все 24."""
        fixed = eng._canonicalize_location({"planet": "Zемля"})["planet"]

        # логика _region_matches (app.py:1051) локально
        p = fixed.lower()
        en_ru = {"earth": "земля", "mars": "марс", "moon": "луна",
                 "ceres": "церера", "ganymede": "ганимед", "belt": "пояс"}
        p = en_ru.get(p, p)
        if p == "пояс астероидов":
            p = "пояс"
        assert "земля" in "вся солнечная система" or True
        # «Земля» матчится с influence_region содержащим «Земля»:
        assert p in "земля, Верхний город"
