"""Игровые системы — бой, репутация, крафт, квесты, спутники."""

from .combat import CombatEngine
from .game_systems import (
    QuestTracker,
    FactionSystem,
    PsychologySystem,
    PerkSystem,
    LevelUpSystem,
    CraftingSystem,
    LocationEvents,
)
from .subsystems import HackingSystem, InvestigationSystem, CompanionSystem, ShipSystem, PropertySystem
from .mechanics import ShopMechanics, TravelSystem, PropertyIncomeManager, ConversationManager
from .quests import QUEST_CHAINS, get_available_chains, get_chain_stage
from .companions import COMPANIONS, get_available_companions, get_companion_by_id, get_loyalty_level, get_companion_combat_bonus

__all__ = [
    "CombatEngine",
    "QuestTracker",
    "FactionSystem",
    "PsychologySystem",
    "PerkSystem",
    "LevelUpSystem",
    "CraftingSystem",
    "LocationEvents",
    "HackingSystem",
    "InvestigationSystem",
    "CompanionSystem",
    "ShipSystem",
    "PropertySystem",
    "ShopMechanics",
    "TravelSystem",
    "PropertyIncomeManager",
    "ConversationManager",
    "QUEST_CHAINS",
    "get_available_chains",
    "get_chain_stage",
    "COMPANIONS",
    "get_available_companions",
    "get_companion_by_id",
    "get_loyalty_level",
    "get_companion_combat_bonus",
]
