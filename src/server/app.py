"""
AI RPG Server - Flask web application.
"""
import json
import os
import random
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from jinja2 import TemplateNotFound
from src.core.engine import GameEngine
from src.systems.game_systems import (QuestTracker, FactionSystem, PsychologySystem,
                                      PerkSystem, LevelUpSystem, CraftingSystem,
                                      LocationEvents)
from src.systems.subsystems import HackingSystem  # D4a: снимок узлов в ответе старта
from src.world.simulation import local_legality  # Backlog#4 (III): местный статус
from src.utils.region import region_matches as _region_matches  # backward-compat re-export
from src import config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)

import logging, traceback
logging.basicConfig(filename="server_errors.log", level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler — catch all unhandled exceptions."""
    tb = traceback.format_exc()
    logging.error(f"Unhandled exception: {e}\n{tb}")
    # Return JSON for API routes, HTML for pages
    if request.path.startswith("/api/"):
        return jsonify({"error": f"Внутренняя ошибка сервера: {type(e).__name__}: {str(e)[:200]}"}), 500
    return f"<h1>500 Internal Server Error</h1><pre>{type(e).__name__}: {str(e)[:200]}</pre>", 500

@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": f"Маршрут не найден: {request.path}"}), 404
    # Статику не маскируем: браузер должен видеть настоящий 404,
    # иначе отсутствующие css/js «притворяются» HTML и ломают отладку
    if request.path.startswith("/static/"):
        return f"<h1>404 Not Found</h1><pre>{request.path}</pre>", 404
    try:
        return render_template("index.html")
    except TemplateNotFound:
        return "<h1>404 Not Found</h1>", 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": f"Метод {request.method} не разрешён для {request.path}"}), 405

engine: GameEngine = None

# Фаза 24c B5-2: цены на стартовое снаряжение (имену, а не ID —
# стартовое снаряжение идёт из creation_data.py и не попадает в BASE_SHOP_ITEMS)
STARTING_EQUIPMENT_PRICES = {
    # Пилоты
    "Доступ к личному кораблю": 50000,
    "Навигационный компьютер": 15000,
    "Лётная куртка": 8000,
    "Быстрый корабль с тайником": 120000,
    "Сканер патрулей": 12000,
    "Фальшивые накладные": 3000,
    # Хакеры
    "Портативный хакерский комплект": 25000,
    "Зашифрованный коммлик": 20000,
    "Нейроинтерфейс": 35000,
    "Квантовый компьютер": 80000,
    "Шифровальные ключи": 15000,
    "Нейроинтерфейс v2": 60000,
    # Инженеры
    "Инженерный набор": 18000,
    "Диагностический сканер": 12000,
    "Ремкомплект": 5000,
    # Учёные
    "Лабораторный набор": 25000,
    "Анализатор данных": 18000,
    "Научный журнал": 3000,
    # Воины
    "Штурмовая винтовка": 22000,
    "Бронежилет": 15000,
    "Медкит": 5000,
    # Теневые
    "Бесшумное оружие": 28000,
    "Корпоративные документы": 10000,
    "Набор ядов": 15000,
    "Камуфляж": 8000,
    "Жучки-прослушки": 6000,
    "Поддельные документы": 8000,
    "Плазменный пистолет": 35000,
    "Трекер-маяк": 12000,
    "Наручники": 7000,
    # Социальные
    "Дипимунитет": 30000,
    "Переводчик": 15000,
    "Элитный костюм": 25000,
    "Торговая лицензия": 40000,
    "Кредитная карта VIP": 5000,
    "Каталог товаров": 10000,
    # Корпорации
    "Сценический костюм": 10000,
    "Аудио-система": 18000,
    "Фан-база": 25000,
    "Зашифрованный телефон": 12000,
    "Сеть контактов": 20000,
    # Медики
    "Медицинский сканер": 20000,
    "Хирургический набор": 30000,
    "Стимпаки x5": 5000,
    # Генетики
    "Генетический сканер": 50000,
    "Био-лаборатория": 100000,
    "Образцы генов": 15000,
    # Детективы
    "Детективный набор": 18000,
    "Базы данных": 12000,
    "Замаскированная камера": 8000,
    # Религия
    "Религиозные артефакты": 50000,
    "Ритуальные одеяния": 15000,
    "Медитативные препарата": 10000,
    # Кибернетика
    "Экстрактор памяти": 60000,
    "Нейро-препараты": 20000,
    "Мозговой сканер": 45000,
}


def init_engine():
    """Инициализировать движок один раз (идемпотентно).

    При `python -m src.server.app` runpy импортирует пакет src.server
    (__init__ -> app), затем исполняет app.py заново как __main__ — модуль
    живёт в sys.modules под двумя именами. Без guard'а GameEngine (и KB на
    74 файла) создавался бы дважды.
    """
    global engine
    if engine is not None:
        return engine
    engine = GameEngine()
    return engine

# ══════════════════════════════════════════════════════════════════
#  BLUEPRINT REGISTRATION (Phase 24c B5-3 refactor, Step 2)
# ══════════════════════════════════════════════════════════════════
# 73 endpoint'а распиты по 5 blueprints:
#   - system (13): /, status, models, settings, presets, creation-data,
#                  saves, save, load, save/delete, kb, content/stats
#   - character (21): character/create, game/start, state, inventory, quests,
#                     implant/*, crafting/*, perks, levelup/*, psychology,
#                     companions/*, quest/*
#   - economy (16): shop/*, ship/*, property/*
#   - world (11): world, map/*, npcs/*, npc/generate, factions/*, world/events
#   - gameplay (11): action, action/stream, hacking/*, investigation/*,
#                    consequence/log

# Зарегистрировать singletons для routes
from src.server.routes._deps import set_engine, set_app
# Phase 26: init engine на module load, чтобы blueprints получали непустой engine
# (раньше set_engine(engine) вызывался с None, т.к. engine инициализировался
# только в if __name__ == '__main__' → все blueprints падали с AttributeError)
init_engine()
set_engine(engine)
set_app(app)

# Импорт blueprints и их регистрация
from src.server.routes import register_blueprints
register_blueprints(app)

# ---- Run ----
if __name__ == "__main__":
    init_engine()
    print(f"\n{'='*60}")
    print(f"  NEXUS RPG Server")
    print(f"  http://localhost:{config.PORT}")
    print(f"  Backend: {config.AI_BACKEND} | Model: {engine.ai.model}")
    print(f"  Game files: {len(engine.kb.files)}")
    print(f"{'='*60}\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
