"""
Configuration for AI RPG Game
Supports Ollama and LMStudio backends
"""
import os

# ============================================================
# AI BACKEND CONFIGURATION
# ============================================================

# Choose backend: "ollama" or "lmstudio"
AI_BACKEND = os.environ.get("AI_BACKEND", "ollama")

# Ollama settings
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "hf.co/mradermacher/MN-Violet-Lotus-12B-GGUF:Q4_K_M")

# LMStudio settings (OpenAI-compatible API)
LMSTUDIO_BASE_URL = os.environ.get("LMSTUDIO_URL", "http://localhost:1234/v1")
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", "local-model")

# Cloud API settings (OpenAI GPT, Google Gemini, Anthropic Claude, etc.)
# Any OpenAI-compatible API endpoint works here
CLOUD_API_URL = os.environ.get("CLOUD_API_URL", "https://api.openai.com/v1")
CLOUD_API_KEY = os.environ.get("CLOUD_API_KEY", "")
CLOUD_API_MODEL = os.environ.get("CLOUD_API_MODEL", "gpt-4o-mini")
# Popular provider URLs:
# OpenAI:      https://api.openai.com/v1
# Google:      https://generativelanguage.googleapis.com/v1beta/openai
# Anthropic:   https://api.anthropic.com/v1  (нужен отдельный формат)
# OpenRouter:  https://openrouter.ai/api/v1  (мультипровайдер, рекомендуется)

# Generation parameters
AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", "0.8"))
AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "6048"))
AI_CONTEXT_WINDOW = int(os.environ.get("AI_CONTEXT_WINDOW", "8192"))

# ============================================================
# GAME CONFIGURATION
# ============================================================
GAME_DATA_DIR = os.environ.get("GAME_DATA_DIR", os.path.join(os.path.dirname(__file__), "game_data"))
DATABASE_DIR = os.environ.get("DATABASE_DIR", os.path.join(os.path.dirname(__file__), "database"))
SAVES_DIR = os.environ.get("SAVES_DIR", os.path.join(os.path.dirname(__file__), "saves"))

# Server
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

# Language
GAME_LANGUAGE = os.environ.get("GAME_LANGUAGE", "ru")
