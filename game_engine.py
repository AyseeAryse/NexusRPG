"""Compatibility shim: canonical implementation lives in src.core.engine.

Root-level import kept for backward compatibility with external tooling.
All game code must import from src.core.engine directly.
"""
from src.core.engine import *  # noqa: F401,F403
from src.core.engine import (  # noqa: F401  (explicit re-export)
    GameEngine, GameState, DiceRoller, get_skill_cap, get_player_tier,
)
