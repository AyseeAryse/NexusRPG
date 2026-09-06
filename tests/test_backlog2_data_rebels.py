"""
Backlog#2: Data Rebels — 167-я каноническая фракция (SC52).

Проверяет:
- FACTIONS_MASTER содержит 167 канонических фракций, SC52/Data Rebels среди них
- Профиль полон: ровно те же 12 обязательных полей, что у остальных
- Костыль 24d снят: canonical_faction("Data Rebels") == "Data Rebels"
  (не «Клан «Теневые Пальцы»»)
- Регион SC52 матчится _region_matches для Земли И Луны (карта D3 не путается)
- Квестовая ветка «передатчик — сеть Data Rebels» отдаёт rep в "Data Rebels"
"""

import json

import pytest

from src.content.v5_legacy import canonical_faction
from src.world.galaxy import GALAXY_MAP

REQUIRED_FIELDS = ["id", "name", "type", "history", "legends", "leaders",
                   "influence_region", "business_area", "allies", "enemies",
                   "mechanics", "plot_hooks"]


def load_master():
    with open("game_data/FACTIONS_MASTER.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def master():
    return load_master()


@pytest.fixture(scope="module")
def canon(master):
    return [f for f in master["factions"]
            if "canonical_duplicate_of" not in f]


class TestCatalog:
    def test_167_canonical_factions(self, canon):
        assert len(canon) == 167

    def test_total_factions_counter_updated(self, master):
        assert master["total_factions"] == 167

    def test_sc52_present_and_complete(self, canon):
        sc52 = next((f for f in canon if f["id"] == "SC52"), None)
        assert sc52 is not None, "SC52 отсутствует"
        assert sc52["name"] == "Data Rebels"
        missing = [k for k in REQUIRED_FIELDS if k not in sc52 or sc52[k] in (None, "", [])]
        assert not missing, f"пустые/отсутствующие поля: {missing}"

    def test_sc52_not_poor_vs_average_profile_size(self, canon):
        """SC52 не беднее среднего профиля по числу непустых полей."""
        sizes = sorted(
            sum(1 for k in REQUIRED_FIELDS
                if f.get(k) not in (None, "", []))
            for f in canon)
        median = sizes[len(sizes) // 2]
        sc52 = next(f for f in canon if f["id"] == "SC52")
        sc52_size = sum(1 for k in REQUIRED_FIELDS if sc52.get(k) not in (None, "", []))
        assert sc52_size >= median


class TestAliasRemoved:
    def test_canonical_faction_passes_through(self):
        assert canonical_faction("Data Rebels") == "Data Rebels"

    def test_shadow_clan_no_longer_receives_dr_rep(self):
        assert canonical_faction("Data Rebels") != "Клан «Теневые Пальцы»"

    def test_other_aliases_intact(self):
        """Соседние alias'ы 24d не задеты удалением."""
        assert canonical_faction("Clan") == "Mars Grey Syndicate"
        assert canonical_faction("ООН Земли") == "Earth UN"


class TestRegionFilter:
    def test_region_matches_earth_and_moon(self):
        from src.server.app import _region_matches
        region = "Земля (Нью-Токио, Нижний город), Луна (Лунные туннели)"
        assert _region_matches(region, "Земля")
        assert _region_matches(region, "Луна")

    def test_region_does_not_leak_to_other_planets(self):
        from src.server.app import _region_matches
        region = "Земля (Нью-Токио, Нижний город), Луна (Лунные туннели)"
        assert not _region_matches(region, "Марс")
        assert not _region_matches(region, "Пояс астероидов")


class TestQuestBranch:
    def test_branch_rep_targets_data_rebels(self):
        with open("game_data/STARTING_QUESTS_COMPLETE.json", encoding="utf-8") as f:
            data = json.load(f)

        def find_branch(o):
            if isinstance(o, dict):
                for b in o.get("branches", []) or []:
                    if "Data Rebels" in b.get("if", ""):
                        return b
                for v in o.values():
                    r = find_branch(v)
                    if r is not None:
                        return r
            elif isinstance(o, list):
                for v in o:
                    r = find_branch(v)
                    if r is not None:
                        return r
            return None

        branch = find_branch(data)
        assert branch is not None, "ветка Data Rebels не найдена"
        assert branch["rep"] == {"Data Rebels": 8}, branch["rep"]

    def test_galaxy_map_references_now_resolvable(self):
        """Имя из galaxy.py совпадает с каноничным именем каталога."""
        names = {f["name"] for f in load_master()["factions"]}
        # ссылки из galaxy.py / npc_registry / simulation
        for ref in ("Data Rebels", "OPA", "Black Lotus Triad"):
            assert ref in names, ref

    def test_planet_names_in_galaxy_map(self):
        assert set(GALAXY_MAP.keys()) >= {"Земля", "Марс", "Луна"}
