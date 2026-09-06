import re
from pathlib import Path
ROOT = Path('D:/NexusRPG-main')

# engine.py imports
print("=== engine.py imports (non-local) ===")
eng = (ROOT/'src/core/engine.py').read_text(encoding='utf-8')
imports = re.findall(r'^(?:from\s+([\w.]+)|import\s+([\w.]+))', eng, re.MULTILINE)
for src, imp in imports:
    if src:
        if not src.startswith('src.') and not src.startswith('.'):
            continue
        if 'src.core' in src or src.startswith('.'):
            continue
        print(f"  from {src}")
    if imp and ('src.systems' in imp or 'src.world' in imp or 'src.content' in imp or 'src.ai' in imp or 'src.utils' in imp):
        print(f"  import {imp}")

print()
print("=== app.py structure ===")
app_text = (ROOT/'src/server/app.py').read_text(encoding='utf-8')
route_pat = re.compile(r'@app\.route')
print(f"  app.py: {sum(1 for _ in (ROOT/'src/server/app.py').open('rb'))} lines, {len(route_pat.findall(app_text))} routes")

print()
print("=== routes/ blueprints ===")
for f in sorted((ROOT/'src/server/routes').glob('*.py')):
    if f.name in ['__init__.py', '_deps.py']: continue
    t = f.read_text(encoding='utf-8')
    bp_routes = len(re.findall(r'@\w+\.route', t))
    lines = sum(1 for _ in f.open('rb'))
    print(f"  {f.name}: {lines} lines, {bp_routes} routes")

print()
print("=== Step 1: IMPLANT_SKILL_MAP location ===")
for f in (ROOT/'src').rglob('*.py'):
    if '__pycache__' in str(f): continue
    t = f.read_text(encoding='utf-8')
    if re.search(r'^IMPLANT_SKILL_MAP\s*=', t, re.MULTILINE):
        m = re.search(r'^IMPLANT_SKILL_MAP\s*=\s*\{', t, re.MULTILINE)
        line = t[:m.start()].count('\n')+1
        print(f"  DEFINED in {f.relative_to(ROOT)}:{line}")
