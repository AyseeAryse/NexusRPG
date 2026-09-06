"""
Split src/server/app.py into Flask Blueprints under src/server/routes/.
Generates 5 blueprint files + init() to register all.
"""
import re
from pathlib import Path

ROOT = Path('D:/NexusRPG-main')
APP_FILE = ROOT / 'src/server/app.py'
ROUTES_DIR = ROOT / 'src/server/routes'

# Маппинг точного пути -> blueprint
EXACT_MAP = {
    '/api/factions/<path:faction_name>/hook-quest': 'world',
}

# Маппинг по ключевым словам в URL
def classify(route):
    r = route.lower()
    if any(k in r for k in ['character', 'inventory', 'perk', 'implant', 'craft',
                             'levelup', 'psychology', 'companion', '/state', 'quest', '/quests']):
        return 'character'
    if any(k in r for k in ['shop', 'ship', 'property']):
        return 'economy'
    if any(k in r for k in ['world', 'map', 'npc', 'faction']):
        return 'world'
    if any(k in r for k in ['action', 'hacking', 'investigation', 'consequence']):
        return 'gameplay'
    return 'system'

def extract_handlers(src_text):
    """Returns list of (route, methods_suffix, func_name, block_text)."""
    lines = src_text.split('\n')
    n = len(lines)
    i = 0
    blocks = []
    while i < n:
        line = lines[i]
        m = re.match(r'^@app\.route\(["\']([^"\']+)["\'](.*)\)\s*$', line)
        if m:
            route = m.group(1)
            rest = m.group(2)
            j = i + 1
            while j < n and not lines[j].startswith('def '):
                j += 1
            if j >= n:
                i += 1
                continue
            func_match = re.match(r'^def (\w+)\(', lines[j])
            if not func_match:
                i += 1
                continue
            func_name = func_match.group(1)
            k = j + 1
            while k < n:
                l = lines[k]
                if l.strip() == '' or l.startswith(' ') or l.startswith('\t'):
                    k += 1
                    continue
                if l.startswith('@app.route') or l.startswith('@app.'):
                    break
                if l.startswith('def ') or l.startswith('class '):
                    break
                if l.startswith('if __name__'):
                    break
                break
            block_text = '\n'.join(lines[i:k])
            blocks.append((route, rest, func_name, block_text))
            i = k
        else:
            i += 1
    return blocks

# Читаем app.py
app_text = APP_FILE.read_text(encoding='utf-8')
blocks = extract_handlers(app_text)

# Группируем
groups = {'character': [], 'economy': [], 'world': [], 'gameplay': [], 'system': []}
for route, rest, func_name, block_text in blocks:
    bp = EXACT_MAP.get(route) or classify(route)
    groups[bp].append((route, rest, func_name, block_text))

# Функция: заменить @app.route на @bp.route и engine на get_engine()
def transform_block(block_text, bp_name):
    """Заменить @app.route на @bp.route и engine на get_engine()."""
    lines = block_text.split('\n')
    out = []
    for line in lines:
        # Только строки декоратора
        if line.lstrip().startswith('@app.route'):
            line = line.replace('@app.route', f'@{bp_name}.route', 1)
        out.append(line)
    return '\n'.join(out)

# Шаблон заголовка blueprint-файла
HEADER_TEMPLATE = '''"""
Auto-generated Blueprint: {bp_name}
Phase 24c B5-3 refactor (Step 2): выделено из src/server/app.py
"""
from flask import Blueprint, request, jsonify, Response, send_from_directory, render_template, stream_with_context
from src.server.routes._deps import get_engine, get_app

{bp_name} = Blueprint("{bp_name}", __name__)

'''

# Генерируем blueprint-файлы
for bp_name, items in groups.items():
    file_path = ROUTES_DIR / f"{bp_name}.py"
    header = HEADER_TEMPLATE.format(bp_name=bp_name)
    body_parts = [header]
    body_parts.append("# Auto-extracted handlers from app.py\n")
    for route, rest, func_name, block_text in items:
        transformed = transform_block(block_text, bp_name)
        body_parts.append(transformed)
        body_parts.append("\n\n")
    file_path.write_text('\n'.join(body_parts), encoding='utf-8')
    print(f"  Wrote {file_path.name}: {len(items)} handlers")

# Генерируем init.py с функцией register_blueprints
init_content = '''"""
Blueprint registry — Phase 24c B5-3 refactor (Step 2).
Импортирует все blueprints и предоставляет register_blueprints(app).
"""
from src.server.routes.character import character
from src.server.routes.economy import economy
from src.server.routes.world import world
from src.server.routes.gameplay import gameplay
from src.server.routes.system import system


def register_blueprints(app):
    """Зарегистрировать все blueprints в Flask app с префиксом /api."""
    # Root (index) — без префикса
    app.register_blueprint(system, url_prefix="")
    app.register_blueprint(character, url_prefix="/api")
    app.register_blueprint(economy, url_prefix="/api")
    app.register_blueprint(world, url_prefix="/api")
    app.register_blueprint(gameplay, url_prefix="/api")
    app.register_blueprint(system, url_prefix="/api")
'''
(ROUTES_DIR / '__init__.py').write_text(init_content, encoding='utf-8')
print(f"  Wrote __init__.py with register_blueprints()")

# Итог
total = sum(len(v) for v in groups.values())
print(f"\nTotal: {total} endpoints across 5 blueprints")
