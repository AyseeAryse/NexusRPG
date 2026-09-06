import os, ast, json, re
from pathlib import Path

ROOT = Path('D:/NexusRPG-main')

print("=" * 60)
print("1. ENTRYPOINTS")
print("=" * 60)
for entry in ['START.bat', 'launcher.py', 'setup.py']:
    p = ROOT / entry
    if p.exists():
        print(f"  {entry}: {p.stat().st_size}B")

# Requirements
reqs = (ROOT / 'requirements.txt').read_text() if (ROOT/'requirements.txt').exists() else ''
print(f"\n  requirements.txt ({len(reqs.splitlines())} deps):")
for line in reqs.splitlines()[:15]:
    if line.strip() and not line.startswith('#'):
        print(f"    {line.strip()}")

# Top-level dirs
print("\n  Top-level dirs:")
for item in sorted(ROOT.iterdir()):
    if item.is_dir() and not item.name.startswith('__pycache__') and item.name not in ['.git']:
        n_files = sum(1 for _ in item.rglob('*') if _.is_file() and '__pycache__' not in str(_))
        print(f"    {item.name}/: {n_files} files")

# 2. Sizes
print()
print("=" * 60)
print("2. KEY FILE SIZES")
print("=" * 60)
for f in ['src/core/engine.py', 'src/server/app.py', 'static/js/app.js',
          'src/systems/combat.py', 'src/world/simulation.py',
          'src/content/v4_legacy.py', 'src/content/v5_legacy.py',
          'src/content/v3_legacy.py', 'src/content/v2_legacy.py',
          'src/content/creation_data.py', 'src/content/base.py']:
    p = ROOT / f
    if p.exists():
        lines = sum(1 for _ in open(p, 'rb'))
        print(f"  {f}: {lines} lines")

# 3. API endpoints
app_text = (ROOT / 'src/server/app.py').read_text(encoding='utf-8')
route_pat = re.compile(r"@app\.route\(['\"]([^'\"]+)['\"]")
routes = route_pat.findall(app_text)
print(f"\n  app.py endpoints: {len(routes)}")
for r in routes[:60]:
    print(f"    {r}")
if len(routes) > 60:
    print(f"    ... and {len(routes)-60} more")

# 4. TODO/FIXME/XXX
print()
print("=" * 60)
print("3. TODO/FIXME MARKERS")
print("=" * 60)
todo_count = {}
for src_file in (ROOT / 'src').rglob('*.py'):
    if '__pycache__' in str(src_file):
        continue
    txt = src_file.read_text(encoding='utf-8', errors='ignore')
    for marker in ['TODO', 'FIXME', 'XXX', 'HACK', 'WIP']:
        for m in re.finditer(rf'\b{marker}\b', txt):
            line = txt[:m.start()].count('\n') + 1
            todo_count.setdefault((src_file.relative_to(ROOT), marker), []).append(line)

for (f, marker), lines in sorted(todo_count.items()):
    print(f"  {f}: {marker} x{len(lines)} (lines {lines[:5]}{'...' if len(lines)>5 else ''})")
print(f"\n  Total markers: {sum(len(v) for v in todo_count.values())}")

# 5. Content counts
print()
print("=" * 60)
print("4. CONTENT POOL (game_data/)")
print("=" * 60)
gd = ROOT / 'game_data'
if gd.exists():
    files = [f for f in gd.iterdir() if f.suffix == '.json' and not f.name.startswith('_')]
    print(f"  KB files: {len(files)}")

# Count entities in key files
import json
for name in ['FACTIONS.json', 'CHARACTER_SKILLS.json', 'DISTRICTS.json',
             'QUESTS.json', 'IMPLANTS.json', 'SPECIALIZATIONS.json', 'NPCS.json']:
    f = gd / name
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, list):
                        print(f"  {name}.{k}: {len(v)}")
                    elif isinstance(v, dict):
                        print(f"  {name}.{k}: dict with {len(v)} keys")
            elif isinstance(d, list):
                print(f"  {name}: {len(d)} items")
        except Exception as e:
            print(f"  {name}: ERROR {e}")

# 6. Tests
print()
print("=" * 60)
print("5. TESTS & VALIDATION")
print("=" * 60)
import subprocess
result = subprocess.run(['C:/Users/Aryse/AppData/Local/Programs/Python/Python311/python.exe', '-m', 'pytest', 'tests/', '-q'],
                       capture_output=True, text=True, timeout=60, cwd=str(ROOT))
print(f"  pytest: {result.stdout.splitlines()[-1] if result.stdout else 'N/A'}")

# Contract
result2 = subprocess.run(['C:/Users/Aryse/AppData/Local/Programs/Python/Python311/python.exe', 'schemas/validate_contract.py'],
                        capture_output=True, text=True, timeout=30, cwd=str(ROOT))
print(f"  contract: {result2.stdout.strip()}")
