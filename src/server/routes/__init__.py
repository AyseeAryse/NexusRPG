"""
Blueprint registry — Phase 24c B5-3 refactor (Step 2).
Импортирует все blueprints и предоставляет register_blueprints(app).

Поскольку все blueprint-роуты уже содержат полный путь (/api/...),
регистрация идёт с пустым url_prefix — это сохраняет точные пути API.
"""
from src.server.routes.character import character
from src.server.routes.economy import economy
from src.server.routes.world import world
from src.server.routes.gameplay import gameplay
from src.server.routes.system import system


def register_blueprints(app):
    """Зарегистрировать все blueprints в Flask app.

    Все роуты внутри blueprints имеют ПОЛНЫЕ пути (/api/...),
    поэтому регистрация идёт без дополнительного url_prefix.
    """
    app.register_blueprint(system, url_prefix="")
    app.register_blueprint(character, url_prefix="")
    app.register_blueprint(economy, url_prefix="")
    app.register_blueprint(world, url_prefix="")
    app.register_blueprint(gameplay, url_prefix="")
