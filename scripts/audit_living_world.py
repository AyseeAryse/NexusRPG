"""
Аудит Living World: game_data/ + src/world/ + src/systems/.
Сканирует JSON, src-файлы (через grep/AST), выводит структурированный отчёт.
"""
import json, os, re, ast
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path('D:/NexusRPG-main')
GD = ROOT / 'game_data'
SRC = ROOT / 'src'

# =============================================================
# 1. Реестр KB: какие JSON-файлы, размеры
# =============================================================
print('=' * 78)
print('1. РЕЕСТР game_data/ JSON-ФАЙЛОВ')
print('=' * 78)

kb_files = []
for f in sorted(GD.glob('*.json')):
    if f.name.startswith('_'): continue
    size = f.stat().st_size
    lines = sum(1 for _ in open(f, 'rb'))
    kb_files.append((f.name, size, lines))

for name, size, lines in kb_files:
    print(f'  {name:55s} {size//1024:4d}K  {lines:4d} lines')
print(f'\n  Total files: {len(kb_files)}')
print(f'  Total size: {sum(s for _,s,_ in kb_files)//1024}K')

# =============================================================
# 2. Анализ FACTIONS_MASTER.json
# =============================================================
print('\n' + '=' * 78)
print('2. ФРАКЦИИ (FACTIONS_MASTER.json)')
print('=' * 78)

with open(GD/'FACTIONS_MASTER.json', 'r', encoding='utf-8') as f:
    fm = json.load(f)
factions = fm.get('factions', [])
print(f'  Factions: {len(factions)}')

# Поля
all_keys = Counter()
for f in factions:
    for k in f.keys():
        all_keys[k] += 1
print(f'  Top fields:')
for k, n in all_keys.most_common(10):
    print(f'    {k}: {n} factions have it')

# plot_hooks статистика
hooks_total = sum(len(f.get('plot_hooks', [])) for f in factions)
factions_with_hooks = sum(1 for f in factions if f.get('plot_hooks'))
print(f'\n  Factions with plot_hooks: {factions_with_hooks}/{len(factions)}')
print(f'  Total plot_hooks: {hooks_total}')

# Типы hooks
hook_types = Counter()
for f in factions:
    for h in f.get('plot_hooks', []):
        hook_types[h.get('type', '?')] += 1
print(f'  Hook types: {dict(hook_types.most_common())}')

# Influence regions
regions = Counter()
for f in factions:
    r = f.get('influence_region', '')
    if r: regions[r] += 1
print(f'  Unique influence_regions: {len(regions)}')
print(f'  Top 5 regions: {dict(regions.most_common(5))}')

# Allies/Enemies
total_allies = sum(len(f.get('allies', [])) for f in factions)
total_enemies = sum(len(f.get('enemies', [])) for f in factions)
print(f'  Total allies references: {total_allies}')
print(f'  Total enemies references: {total_enemies}')

# =============================================================
# 3. Анализ POLITICS.json
# =============================================================
print('\n' + '=' * 78)
print('3. POLITICS.json (government, propaganda, events)')
print('=' * 78)

with open(GD/'POLITICS.json', 'r', encoding='utf-8') as f:
    pol = json.load(f)
print(f'  Top-level keys: {list(pol.keys())}')

# Event generator (кризисы)
eg = pol.get('event_generator', {})
if isinstance(eg, dict):
    print(f'  event_generator keys: {list(eg.keys())[:10]}')

# Media templates
mt = pol.get('media_templates', {})
if isinstance(mt, dict):
    print(f'  media_templates keys: {list(mt.keys())[:10]}')
    if 'templates' in mt:
        print(f'    templates: {len(mt["templates"])} items')

# Mission templates
mst = pol.get('mission_templates', {})
if isinstance(mst, list):
    print(f'  mission_templates: {len(mst)} items')

# Government types
gt = pol.get('government_types', [])
if isinstance(gt, list):
    print(f'  government_types: {len(gt)}')
    for g in gt[:5]:
        if isinstance(g, dict):
            print(f'    {g.get("name", g.get("type", "?"))}: {list(g.keys())[:5]}')

# =============================================================
# 4. Анализ событий и кризисов
# =============================================================
print('\n' + '=' * 78)
print('4. СОБЫТИЯ И КРИЗИСЫ')
print('=' * 78)

# ENHANCED_EVENT_GENERATOR_V2.json
eeg2_path = GD/'ENHANCED_EVENT_GENERATOR_V2.json'
if eeg2_path.exists():
    with open(eeg2_path, 'r', encoding='utf-8') as f:
        eeg2 = json.load(f)
    print(f'  ENHANCED_EVENT_GENERATOR_V2.json keys: {list(eeg2.keys())}')
    # Chains
    chains = eeg2.get('event_chains', {})
    if isinstance(chains, dict):
        print(f'    event_chains: {len(chains)} chains')
        for ck, cv in list(chains.items())[:3]:
            if isinstance(cv, list):
                print(f'      {ck}: {len(cv)} events')
    # Locations
    locs = eeg2.get('new_location_events', {})
    if isinstance(locs, dict):
        print(f'    new_location_events keys: {list(locs.keys())}')

# 07_MEGA_WORLD_SIMULATION_COMPLETE.json
wsm_path = GD/'07_MEGA_WORLD_SIMULATION_COMPLETE.json'
if wsm_path.exists():
    with open(wsm_path, 'r', encoding='utf-8') as f:
        wsm = json.load(f)
    print(f'\n  07_MEGA_WORLD_SIMULATION_COMPLETE.json top keys:')
    for k in wsm.keys():
        v = wsm[k]
        if isinstance(v, dict):
            print(f'    {k}: dict ({len(v)} keys)')
        elif isinstance(v, list):
            print(f'    {k}: list ({len(v)} items)')

# =============================================================
# 5. Новости и слухи
# =============================================================
print('\n' + '=' * 78)
print('5. НОВОСТИ И СЛУХИ')
print('=' * 78)

news_path = GD/'NEWS_AND_RUMORS_GENERATOR.json'
if news_path.exists():
    with open(news_path, 'r', encoding='utf-8') as f:
        news = json.load(f)
    print(f'  news keys: {list(news.keys())}')
    cats = news.get('news_categories', {})
    if isinstance(cats, dict):
        print(f'    news_categories: {list(cats.keys())[:10]}')
    rumors = news.get('rumors_d20', [])
    if isinstance(rumors, list):
        print(f'    rumors_d20: {len(rumors)} rumors')
    media_eco = news.get('media_ecosystem', [])
    if isinstance(media_eco, list):
        print(f'    media_ecosystem: {len(media_eco)} outlets')
    elif isinstance(media_eco, dict):
        print(f'    media_ecosystem: dict ({len(media_eco)} keys)')

# =============================================================
# 6. Космос и торговля
# =============================================================
print('\n' + '=' * 78)
print('6. КОСМОС И ТОРГОВЛЯ')
print('=' * 78)

space_path = GD/'SPACE_ENCOUNTER_GENERATOR.json'
if space_path.exists():
    with open(space_path, 'r', encoding='utf-8') as f:
        sp = json.load(f)
    encounters = sp.get('encounters_d20', [])
    if isinstance(encounters, list):
        print(f'  SPACE_ENCOUNTER_GENERATOR: {len(encounters)} d20 encounters')
    freq = sp.get('encounter_frequency', {})
    if isinstance(freq, dict):
        print(f'    frequency keys: {list(freq.keys())}')

trade_path = GD/'TRADE_ROUTES_MASTER.json'
if trade_path.exists():
    with open(trade_path, 'r', encoding='utf-8') as f:
        tr = json.load(f)
    routes = tr.get('routes', [])
    if isinstance(routes, list):
        print(f'\n  TRADE_ROUTES_MASTER: {len(routes)} routes')
        for r in routes[:5]:
            if isinstance(r, dict):
                print(f'    {r.get("name", r.get("id", "?"))}: {list(r.keys())[:5]}')

# =============================================================
# 7. Code-side: что src/world/* использует
# =============================================================
print('\n' + '=' * 78)
print('7. SRC/WORLD/ — что реально читает код')
print('=' * 78)

world_dir = SRC/'world'
for src_file in sorted(world_dir.glob('*.py')):
    if src_file.name == '__init__.py': continue
    text = src_file.read_text(encoding='utf-8', errors='ignore')
    lines = text.count('\n') + 1
    # Найти обращения к game_data
    refs = re.findall(r'["\']([A-Z_]+\.json|[a-z_]+\.json)["\']', text)
    print(f'  {src_file.name}: {lines} lines')
    if refs:
        unique = set(refs)
        print(f'    refs to game_data: {sorted(unique)}')
    # Найти классы и методы
    classes = re.findall(r'^class\s+(\w+)', text, re.MULTILINE)
    funcs = re.findall(r'    def\s+(\w+)', text)
    if classes:
        print(f'    classes: {classes}')
    print(f'    methods: {len(funcs)}')

# =============================================================
# 8. Системы: world_tick и WorldSimulator.tick
# =============================================================
print('\n' + '=' * 78)
print('8. МЕХАНИКА ТИКА МИРА (ЧТО СЕЙЧАС РЕАЛЬНО РАБОТАЕТ)')
print('=' * 78)

# src/world/simulation.py — WorldSimulator
sim_text = (SRC/'world/simulation.py').read_text(encoding='utf-8', errors='ignore')
tick_match = re.search(r'def tick\(self[^)]*\):[^"]*?(?=\n    def |\nclass )', sim_text, re.DOTALL)
if tick_match:
    snippet = tick_match.group(0)[:1500]
    print(f'  WorldSimulator.tick signature & first 1500 chars:')
    for line in snippet.split('\n')[:30]:
        print(f'    {line[:90]}')

# src/core/engine.py — _world_tick
eng_text = (SRC/'core/engine.py').read_text(encoding='utf-8', errors='ignore')
wt_match = re.search(r'def _world_tick\(self[^)]*\):[^"]*?(?=\n    def [a-z])', eng_text, re.DOTALL)
if wt_match:
    snippet = wt_match.group(0)[:2500]
    print(f'\n  GameEngine._world_tick (first 2500 chars):')
    for line in snippet.split('\n')[:50]:
        print(f'    {line[:90]}')

# =============================================================
# 9. "Мёртвый груз": JSON-файлы с factions/news, которые НЕ читаются кодом
# =============================================================
print('\n' + '=' * 78)
print('9. МЁРТВЫЙ ГРУЗ: JSON, КОТОРЫЕ НЕ ЧИТАЮТСЯ КОДОМ')
print('=' * 78)

# Сканируем весь src/ на упоминания JSON-файлов game_data
code_refs = set()
for f in SRC.rglob('*.py'):
    if '__pycache__' in str(f): continue
    t = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'["\']([A-Z][A-Z0-9_]+\.json)["\']', t):
        code_refs.add(m.group(1))
    for m in re.finditer(r'["\']([a-z][a-z0-9_]+\.json)["\']', t):
        code_refs.add(m.group(1))

print(f'  Total JSON-файлов в game_data/: {len(kb_files)}')
print(f'  JSON-файлов, упоминаемых в src/: {len(code_refs)}')

referenced = set(name for name, _, _ in kb_files if name in code_refs)
not_referenced = set(name for name, _, _ in kb_files) - referenced
print(f'\n  ССЫЛАЮТСЯ в коде ({len(referenced)}):')
for n in sorted(referenced):
    print(f'    ✓ {n}')
print(f'\n  НЕ ссылаются ({len(not_referenced)}):')
for n in sorted(not_referenced):
    print(f'    ✗ {n}')

# =============================================================
# 10. systems/mechanics.py
# =============================================================
print('\n' + '=' * 78)
print('10. SRC/SYSTEMS/MECHANICS.PY — что внутри')
print('=' * 78)

mech_text = (SRC/'systems/mechanics.py').read_text(encoding='utf-8', errors='ignore')
print(f'  lines: {mech_text.count(chr(10)) + 1}')
classes = re.findall(r'^class\s+(\w+)', mech_text, re.MULTILINE)
funcs = re.findall(r'    def\s+(\w+)', mech_text)
print(f'  classes: {classes}')
print(f'  methods: {funcs[:15]}{"..." if len(funcs) > 15 else ""}')
refs = re.findall(r'["\']([A-Z_]+\.json|[a-z_]+\.json)["\']', mech_text)
if refs:
    print(f'  refs to game_data: {sorted(set(refs))}')

# world/procedural.py
print('\n  src/world/procedural.py:')
proc_text = (SRC/'world/procedural.py').read_text(encoding='utf-8', errors='ignore')
classes = re.findall(r'^class\s+(\w+)', proc_text, re.MULTILINE)
funcs = re.findall(r'    def\s+(\w+)', proc_text)
print(f'    classes: {classes}')
print(f'    methods: {funcs[:10]}{"..." if len(funcs) > 10 else ""}')
refs = re.findall(r'["\']([A-Z_]+\.json|[a-z_]+\.json)["\']', proc_text)
if refs:
    print(f'    refs: {sorted(set(refs))}')

# world/event_roles.py
print('\n  src/world/event_roles.py:')
er_text = (SRC/'world/event_roles.py').read_text(encoding='utf-8', errors='ignore')
classes = re.findall(r'^class\s+(\w+)', er_text, re.MULTILINE)
funcs = re.findall(r'    def\s+(\w+)', er_text)
print(f'    classes: {classes}, methods: {funcs[:8]}')
refs = re.findall(r'["\']([A-Z_]+\.json|[a-z_]+\.json)["\']', er_text)
if refs:
    print(f'    refs: {sorted(set(refs))}')

# world/galaxy.py
print('\n  src/world/galaxy.py:')
gal_text = (SRC/'world/galaxy.py').read_text(encoding='utf-8', errors='ignore')
classes = re.findall(r'^class\s+(\w+)', gal_text, re.MULTILINE)
funcs = re.findall(r'    def\s+(\w+)', gal_text)
print(f'    classes: {classes}, methods: {funcs[:8]}')

# systems/combat.py — для контекста
print('\n  src/systems/combat.py:')
cmb_text = (SRC/'systems/combat.py').read_text(encoding='utf-8', errors='ignore')
print(f'    lines: {cmb_text.count(chr(10)) + 1}')
classes = re.findall(r'^class\s+(\w+)', cmb_text, re.MULTILINE)
print(f'    classes: {classes}')

# =============================================================
# 11. Конфликты данных
# =============================================================
print('\n' + '=' * 78)
print('11. КОНФЛИКТЫ ДАННЫХ')
print('=' * 78)

# Сравним ID фракций между FACTIONS_MASTER и NAMED_NPCS
npc_path = GD/'NAMED_NPCS.json'
npcs = json.loads(npc_path.read_text(encoding='utf-8')) if npc_path.exists() else {"npcs": []}
npc_factions = set()
for n in npcs.get("npcs", []):
    f = n.get("faction")
    if f: npc_factions.add(f)
faction_names = set(f.get("name", "") for f in factions)
overlap = npc_factions & faction_names
npc_only = npc_factions - faction_names
print(f'  Faction names in NAMED_NPCS that match FACTIONS_MASTER: {len(overlap)}')
print(f'  Faction names in NAMED_NPCS missing from FACTIONS_MASTER: {len(npc_only)}')
if npc_only:
    for n in sorted(npc_only)[:10]:
        print(f'    - "{n}"')

# ID локаций: planet/city/district в разных файлах
planets_in_factions = set()
for f in factions:
    r = (f.get("influence_region") or "").lower()
    for p in ["земля", "марс", "церера", "ганимед", "юпитер", "пояс", "венера", "сатурн"]:
        if p in r:
            planets_in_factions.add(p)

trade_routes_planets = set()
if trade_path.exists():
    tr_data = json.loads(trade_path.read_text(encoding='utf-8'))
    for r in tr_data.get('routes', []):
        fr = r.get('from', r.get('from_planet', ''))
        to = r.get('to', r.get('to_planet', ''))
        if fr: trade_routes_planets.add(fr.lower())
        if to: trade_routes_planets.add(to.lower())
print(f'\n  Planets in FACTIONS_MASTER (influence_region): {sorted(planets_in_factions)}')
print(f'  Planets in TRADE_ROUTES_MASTER: {sorted(trade_routes_planets)}')

# =============================================================
# 12. plot_hooks формат — все ли имеют одинаковые поля?
# =============================================================
print('\n' + '=' * 78)
print('12. plot_hooks: РАЗНООБРАЗИЕ ФОРМАТА')
print('=' * 78)

hook_field_signatures = Counter()
hook_field_examples = {}
for f in factions:
    for h in f.get('plot_hooks', []):
        sig = tuple(sorted(h.keys()))
        hook_field_signatures[sig] += 1
        if sig not in hook_field_examples:
            hook_field_examples[sig] = (f.get("name", "?"), h)

print(f'  Уникальных структур plot_hooks: {len(hook_field_signatures)}')
for sig, count in hook_field_signatures.most_common(5):
    print(f'    {count}x: {sig}')

# Поканы
print('\n' + '=' * 78)
print('13. ПЛАН ИНТЕГРАЦИИ (предложения для Phase 3)')
print('=' * 78)
print('  - faction_sim.tick() подключён в _world_tick (Phase 3 done)')
print('  - contract_gen → /api/contracts/available (Phase 3 done)')
print('  - Хвосты: NEWS_AND_RUMORS_GENERATOR, POLITICS.event_generator, SPACE_ENCOUNTER — мёртвый груз')
print('  - Приоритет Phase 3.1: news_generator (D4 backlog), event-chain каскады (D3 backlog)')
