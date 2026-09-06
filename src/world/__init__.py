"""Генерация мира — галактика, симуляция, процедурная генерация, NPC."""

from .galaxy import GalaxyMap
from .simulation import WorldSimulator
from .procedural import ProceduralQuestGenerator, WorldTicker, ConsequenceTracker
from .npc_registry import NPCRegistry, SPEECH_STYLES

__all__ = [
    "GalaxyMap",
    "WorldSimulator",
    "ProceduralQuestGenerator",
    "WorldTicker",
    "ConsequenceTracker",
    "NPCRegistry",
    "SPEECH_STYLES",
]
