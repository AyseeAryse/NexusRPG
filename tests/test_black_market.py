"""Unit tests for Black Market (Вариант I) mechanics."""
import pytest
from unittest.mock import MagicMock

from src.world.simulation import WorldSimulator, local_legality, BASE_SHOP_ITEMS, REGIONAL_LEGALITY_MAP


class TestBlackMarketAccess:
    """Tests for black market access conditions (Комбо А+В)."""

    def setup_method(self):
        self.sim = WorldSimulator()
        self.loc = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}
        self.tier = 0

    def test_regular_shop_hides_illegal_items(self):
        """Regular shop must never show illegal items."""
        items = self.sim.get_shop_items(self.loc, self.tier)
        illegal = [i for i in items if i.get("local_legality") == "illegal"
                   or i.get("legality") == "illegal"]
        assert len(illegal) == 0, "Regular shop should not show illegal items"

    def test_black_market_accessible_without_criminal_rep(self):
        """Вариант В: black market always accessible (with risk), no rep required."""
        character = {"faction_reputation": {"Data Rebels": 10}}
        items = self.sim.get_shop_items(self.loc, self.tier,
                                        include_black_market=True, character=character)
        assert len(items) > 0, "Black market should be accessible without criminal rep"
        # All items should have risk flag since no criminal rep
        risk_items = [i for i in items if i.get("black_market_risk")]
        assert len(risk_items) == len(items), "All BM items should have risk flag without rep"

    def test_black_market_access_with_criminal_rep(self):
        """Комбо А: rep ≥ 25 with criminal faction grants safe access."""
        character = {"faction_reputation": {"Black Lotus Triad": 30}}
        items = self.sim.get_shop_items(self.loc, self.tier,
                                        include_black_market=True, character=character)
        risk_items = [i for i in items if i.get("black_market_risk")]
        assert len(risk_items) == 0, "No risk flag when player has criminal rep"

    def test_black_market_without_character_returns_empty(self):
        """When character is None and include_black_market=True, should return empty."""
        items = self.sim.get_shop_items(self.loc, self.tier,
                                        include_black_market=True, character=None)
        assert len(items) == 0


class TestBlackMarketMarkup:
    """Tests for black market price markup (×1.5 illegal, ×1.25 restricted)."""

    def setup_method(self):
        self.sim = WorldSimulator()
        self.loc = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}
        self.tier = 0
        self.character = {"faction_reputation": {"Black Lotus Triad": 30}}

    def test_illegal_items_marked_up_1_5x(self):
        """Illegal items in black market should have ×1.5 markup."""
        # Find an item with legality='illegal' that isn't filtered by rarity
        illegal_items = []
        for cat, items in BASE_SHOP_ITEMS.items():
            for item in items:
                if item.get("legality") == "illegal" and item["rarity"] != "rare":
                    illegal_items.append(item)
                    if len(illegal_items) >= 1:
                        break
            if illegal_items:
                break

        if not illegal_items:
            pytest.skip("No illegal items (non-rare) in catalog")

        test_item = illegal_items[0]
        planet_mod = 1.0  # Земля
        expected_base = int(test_item["base_price"] * planet_mod * self.sim.price_modifier)
        expected_bm = int(expected_base * 1.5)

        items = self.sim.get_shop_items(self.loc, self.tier,
                                        include_black_market=True, character=self.character)
        bm_illegal = [i for i in items if i["id"] == test_item["id"]]
        assert len(bm_illegal) == 1
        assert bm_illegal[0]["price"] == expected_bm, \
            f"Expected {expected_bm}, got {bm_illegal[0]['price']} for {test_item['name']}"

    def test_restricted_items_marked_up_1_25x(self):
        """Restricted items in black market should have ×1.25 markup."""
        # Find a restricted item that isn't filtered by rarity at tier 0
        restricted_items = []
        for cat, items in BASE_SHOP_ITEMS.items():
            for item in items:
                if item.get("legality") == "restricted" and item["rarity"] != "rare":
                    restricted_items.append(item)
                    if len(restricted_items) >= 1:
                        break
            if restricted_items:
                break

        if not restricted_items:
            pytest.skip("No restricted items (non-rare) in catalog")

        test_item = restricted_items[0]
        planet_mod = 1.0  # Земля
        expected_base = int(test_item["base_price"] * planet_mod * self.sim.price_modifier)
        expected_bm = int(expected_base * 1.25)

        items = self.sim.get_shop_items(self.loc, self.tier,
                                        include_black_market=True, character=self.character)
        bm_restricted = [i for i in items if i["id"] == test_item["id"]]
        assert len(bm_restricted) == 1
        assert bm_restricted[0]["price"] == expected_bm, \
            f"Expected {expected_bm}, got {bm_restricted[0]['price']} for {test_item['name']}"


class TestHeatThresholds:
    """Tests for Heat thresholds (Вариант I)."""

    def test_heat_constants(self):
        """Verify heat threshold constants."""
        from src.systems.expenses import HEAT_RAID_THRESHOLD, HEAT_LOCKOUT_THRESHOLD, HEAT_DECAY_PER_WEEK
        assert HEAT_RAID_THRESHOLD == 5
        assert HEAT_LOCKOUT_THRESHOLD == 10
        assert HEAT_DECAY_PER_WEEK == 1


class TestHeatDecay:
    """Tests for heat decay (-1 per week via ExpenseCycle)."""

    def setup_method(self):
        from src.systems.expenses import ExpenseCycle
        self.engine = MagicMock()
        self.expenses = ExpenseCycle()
        self.character = {"credits": 100000, "heat": 10, "debt": 0}

        # Mock property_system and ship_system
        self.property_system = MagicMock()
        self.property_system.properties = []
        self.ship_system = MagicMock()
        self.ship_system.ship = None

    def test_heat_decays_exactly_one_per_week(self):
        """heat should decrease by exactly 1 per weekly cycle."""
        self.character["heat"] = 10
        result = self.expenses.tick(168, self.property_system, self.ship_system, self.character, 0)
        assert result is not None
        assert self.character["heat"] == 9, f"Expected 9, got {self.character['heat']}"
        assert result["heat_decayed"] == 1

    def test_heat_does_not_go_negative(self):
        """heat should not go below 0."""
        self.character["heat"] = 0
        result = self.expenses.tick(168, self.property_system, self.ship_system, self.character, 0)
        assert result is not None
        assert self.character["heat"] == 0
        assert result["heat_decayed"] == 0

    def test_heat_decay_multiple_weeks(self):
        """Verify heat decays by 1 each week, not 2."""
        self.character["heat"] = 10
        # Week 1
        result1 = self.expenses.tick(168, self.property_system, self.ship_system, self.character, 0)
        assert self.character["heat"] == 9
        # Week 2
        result2 = self.expenses.tick(336, self.property_system, self.ship_system, self.character, 0)
        assert self.character["heat"] == 8, f"Expected 8, got {self.character['heat']}"
        # Week 3
        result3 = self.expenses.tick(504, self.property_system, self.ship_system, self.character, 0)
        assert self.character["heat"] == 7


class TestCriminalFactionNames:
    """Verify all criminal faction names exist in FACTIONS_MASTER.json."""

    def test_all_criminal_factions_exist_in_catalog(self):
        """All names in FACTION_CATEGORIES['криминал'] must exist in FACTIONS_MASTER."""
        import json, os
        from src.systems.game_systems import FACTION_CATEGORIES

        fm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "game_data", "FACTIONS_MASTER.json")
        with open(fm_path, encoding="utf-8") as f:
            catalog = json.load(f)

        canonical_names = {f["name"] for f in catalog["factions"] if "canonical_duplicate_of" not in f}
        criminals = FACTION_CATEGORIES.get("криминал", [])

        missing = [name for name in criminals if name not in canonical_names]
        assert len(missing) == 0, f"Criminal factions not in catalog: {missing}"
