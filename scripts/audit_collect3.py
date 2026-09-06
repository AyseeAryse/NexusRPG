import os, re
from pathlib import Path
ROOT = Path('D:/NexusRPG-main')

# Engine subsystems
print("=" * 60)
print("ENGINE SUBSYSTEMS (in GameEngine.__init__)")
print("=" * 60)
engine = (ROOT / 'src/core/engine.py').read_text(encoding='utf-8')
pat = re.compile(r'self\.(\w+)\s*=\s*(\w+)\(')
seen = set()
for m in pat.finditer(engine):
    name, cls = m.group(1), m.group(2)
    if (name, cls) not in seen:
        seen.add((name, cls))
        print(f"  self.{name} = {cls}(...)")

# API -> JS
print()
print("=" * 60)
print("FRONT-BACK SYNC")
print("=" * 60)
js = (ROOT / 'static/js/app.js').read_text(encoding='utf-8')
api_used = set(re.findall(r"['\"](/api/[^'\"]+)['\"]", js))
api_defined = set(re.findall(r"@app\.route\(['\"]([^'\"]+)['\"]", (ROOT / 'src/server/app.py').read_text(encoding='utf-8')))
# Normalize dynamic segments
def norm(p):
    import re as r
    return r.sub(r'<[^>]+>', '<X>', p)
api_def_norm = {norm(p) for p in api_defined}
api_use_norm = {norm(p) for p in api_used}
print(f"  API defined: {len(api_defined)}, normalized: {len(api_def_norm)}")
print(f"  API used in JS: {len(api_used)}")
unused = api_def_norm - api_use_norm
print(f"  Unused (backend-only/CDP/AI-direct): {len(unused)}")
for u in sorted(unused)[:30]:
    print(f"    - {u}")
print()
print(f"  Used in JS but NOT in app.py: {len(api_use_norm - api_def_norm)}")
for u in sorted(api_use_norm - api_def_norm)[:20]:
    print(f"    ! {u}")

# Specific subsystem readiness check
print()
print("=" * 60)
print("SUBSYSTEM READINESS (API endpoint presence)")
print("=" * 60)
subs = {
    'Combat': ['/api/action', '/api/world/events'],
    'Hacking': ['/api/hacking/targets', '/api/hacking/start', '/api/hacking/action'],
    'Investigation': ['/api/investigation/open', '/api/investigation/clue', '/api/investigation/suspect', '/api/investigation/conclude'],
    'Crafting': ['/api/crafting/recipes', '/api/crafting/craft'],
    'Companions': ['/api/companions/available', '/api/companions/recruit', '/api/companions/dismiss'],
    'Ships': [],  # search
    'Property': [],
    'Implant': ['/api/implant/list', '/api/implant/install', '/api/implant/remove'],
    'Shop': ['/api/shop', '/api/shop/buy', '/api/shop/sell', '/api/shop/blackmarket'],
    'Quests': ['/api/quests', '/api/quest/add', '/api/quest/advance', '/api/quest/generate'],
    'Factions': ['/api/factions', '/api/factions/catalog'],
    'Perks': ['/api/perks', '/api/perks/select', '/api/levelup/spend', '/api/levelup/spend/attr'],
    'Map': ['/api/map', '/api/map/move', '/api/map/location'],
    'NPCs': ['/api/npcs', '/api/npc/generate', '/api/npcs/catalog'],
    'KB': ['/api/kb/files', '/api/kb/file'],
    'Saves': ['/api/saves', '/api/save', '/api/load', '/api/save/delete'],
}
for name, eps in subs.items():
    found = [e for e in eps if e in api_defined]
    print(f"  {name}: {len(found)}/{len(eps)} ({', '.join(found) if found else 'none'})")
