"""Compatibility shim: canonical implementation lives in src.ai.connector."""
from src.ai.connector import *  # noqa: F401,F403
from src.ai.connector import AIConnector  # noqa: F401  (explicit re-export)
