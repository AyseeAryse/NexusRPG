"""WSGI entrypoint for standard tooling (`flask run`, `gunicorn app:app`, verify recipes).

Canonical launch remains `python -m src.server.app` (or launcher.py).
"""
from src.server.app import app, init_engine

init_engine()

if __name__ == "__main__":
    from src import config
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
