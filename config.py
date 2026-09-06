"""Compatibility shim: canonical configuration lives in src.config.

Path defaults in src.config resolve relative to the project root,
so behaviour is identical to the previous root-level copy.
"""
from src.config import *  # noqa: F401,F403
from src.config import (  # noqa: F401  (explicit re-export)
    AI_BACKEND, OLLAMA_BASE_URL, OLLAMA_MODEL, LMSTUDIO_BASE_URL, LMSTUDIO_MODEL,
    CLOUD_API_URL, CLOUD_API_KEY, CLOUD_API_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS,
    AI_CONTEXT_WINDOW, GAME_DATA_DIR, DATABASE_DIR, SAVES_DIR, HOST, PORT,
    DEBUG, GAME_LANGUAGE,
)
