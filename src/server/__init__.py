"""Веб-сервер на Flask — API и интерфейс игры."""

from .app import app, init_engine

__all__ = ["app", "init_engine"]
