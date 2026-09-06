import os, ast, json, re, subprocess
from pathlib import Path
ROOT = Path('D:/NexusRPG-main')

# Content counts (FACTIONS, DISTRICTS, QUESTS, IMPLANTS, etc.)
print("=" * 60)
print("CONTENT POOL - DEEP DIVE")
print("=" * 60)
gd = ROOT / 'game_data'
for name in sorted(gd.glob('*.json')):
    if name.name.startswith('_'):
        continue
    try:
        d = json.loads(name.read_text(encoding='utf-8'))
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, list):
                    print(f"  {name.name}.{k}: {len(v)} items")
                elif isinstance(v, dict):
                    print(f"  {name.name}.{k}: dict {len(v)} keys")
        elif isinstance(d, list):
            print(f"  {name.name}: {len(d)} items (list)")
    except Exception as e:
        print(f"  {name.name}: ERR {e}")

# TODO/FIXME — broader scan including 'XXX', 'NOTE', 'BUG'
print()
print("=" * 60)
print("TODO/FIXME/XXX/NOTE/BUG/HACK")
print("=" * 60)
patterns = ['TODO', 'FIXME', 'XXX', 'NOTE:', 'BUG', 'HACK', 'WIP', 'FUTURE']
total = 0
for src_file in (ROOT / 'src').rglob('*.py'):
    if '__pycache__' in str(src_file):
        continue
    txt = src_file.read_text(encoding='utf-8', errors='ignore')
    for marker in patterns:
        for m in re.finditer(rf'\b{re.escape(marker)}\b', txt):
            line = txt[:m.start()].count('\n') + 1
            rel = src_file.relative_to(ROOT)
            print(f"  {rel}:{line} [{marker}]")
            total += 1
print(f"\n  Total: {total}")

# Legacy dependencies
print()
print("=" * 60)
print("LEGACY DEPENDENCIES")
print("=" * 60)
for legacy in ['v2_legacy', 'v3_legacy', 'v4_legacy', 'v5_legacy']:
    legacy_path = ROOT / 'src/content' / f'{legacy}.py'
    if legacy_path.exists():
        lines = sum(1 for _ in open(legacy_path, 'rb'))
        # Find imports of this legacy module
        importers = []
        for f in (ROOT / 'src').rglob('*.py'):
            if '__pycache__' in str(f):
                continue
            try:
                t = f.read_text(encoding='utf-8', errors='ignore')
                if f'from .{legacy}' in t or f'from src.content.{legacy}' in t or f'from src.content import {legacy}' in t or f'from .{legacy} import' in t:
                    importers.append(f.relative_to(ROOT))
            except: pass
        print(f"  {legacy}.py: {lines} lines, imported by {len(importers)} files")
        for imp in importers[:8]:
            print(f"    -> {imp}")

# Engine internals - subsystems
print()
print("=" * 60)
print("ENGINE SUBSYSTEMS (in GameEngine)")
print("=" * 60)
engine = (ROOT / 'src/core/engine.py').read_text(encoding='utf-8')
# Find self.xxx = YyySystem() lines
init_pattern = re.compile(r'self\.(\w+)\s*=\s*(\w+)\(', engine)
seen = set()
for m in init_pattern.finditer(engine):
    name, cls = m.group(1), m.group(2)
    if (name, cls) not in seen and name not in ['dice', 'state', 'combat_engine', 'companions', 'ship', 'property', 'investigation', 'hacking', 'expenses', 'galaxy_map', 'kb', 'property_income', 'npc_registry', 'world_effects']:
        pass
    if (name, cls) not in seen:
        seen.add((name, cls))
        if not name.startswith('_'):
            print(f"  self.{name} = {cls}()")

# API -> JS mapping
print()
print("=" * 60)
print("FRONT-BACK SYNC (api endpoints called from JS)")
print("=" * 60)
js = (ROOT / 'static/js/app.js').read_text(encoding='utf-8')
api_used = set(re.findall(r"['\"](/api/[^'\"]+)['\"]", js))
api_defined = set(routes)
print(f"  API defined in app.py: {len(api_defined)}")
print(f"  API used in app.js: {len(api_used)}")
unused = api_defined - api_used
missing = api_used - api_defined
print(f"  Unused (backend-only, called from CDP/tests/AI): {len(unused)}")
for u in sorted(unused)[:15]:
    print(f"    - {u}")
print(f"  Missing in app.py (404 in JS): {len(missing)}")
for m in sorted(missing)[:15]:
    print(f"    ! {m}")
