"""
Глубокий аудит тональности/атмосферы/жанров в game_data/ и src/.
Использует чистый AST/JSON-обход без загрузки всего в контекст.
"""
import json, re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path('D:/NexusRPG-main')
GD = ROOT / 'game_data'

# === 1. Реестр тональных ключей ===
TONE_KEYS = {
    # 4D-вектор
    'cynicism', 'violence', 'hope', 'sophistication',
    # tone_modifiers
    'precision', 'secrecy', 'curiosity', 'darkness', 'irony',
    'empathy', 'aggression', 'nostalgia', 'defiance',
    # meta
    'tone', 'tone_modifiers', 'tone_dynamics', 'tone_axes',
    'mood', 'emotional_palette', 'emotional_register',
    # жанры/темы
    'genre', 'genres', 'preferred_genres', 'subgenre', 'genre_blending',
    'theme', 'themes', 'theme_integration', 'thematic_focus',
    # речь
    'dialogue_style', 'dialogue_patterns', 'narrative_voice',
    'speech_patterns', 'unique_dialogue_tags', 'speech_markers',
    'social_status', 'castes', 'social_castes',
    # атмосфера
    'atmosphere', 'atmospheric', 'lighting', 'scent', 'audio_landscape',
    'environmental_details', 'environmental_narrative',
    'soundscape', 'olfactory', 'visual_cues', 'mood_descriptors',
    # психология
    'stress', 'humanity', 'ideology', 'trauma', 'karmic_dice',
    'psychological_profile', 'psychological_dimensions',
}

# Где в коде эти ключи читаются
code_reads = defaultdict(set)  # key -> set of files
for src_file in (ROOT / 'src').rglob('*.py'):
    if '__pycache__' in str(src_file): continue
    t = src_file.read_text(encoding='utf-8', errors='ignore')
    for k in TONE_KEYS:
        # word boundary match
        if re.search(rf'\b{re.escape(k)}\b', t):
            code_reads[k].add(str(src_file.relative_to(ROOT)))

# Сканируем JSON-файлы
def walk_json(obj, path, found):
    """Рекурсивно обходит JSON, собирает вхождения интересующих ключей."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in TONE_KEYS:
                # Собираем пример
                sample = v
                if isinstance(v, dict):
                    sample = {kk: ('...' if isinstance(vv, (dict, list)) and len(str(vv))>50 else vv) for kk, vv in v.items()}
                elif isinstance(v, list) and v:
                    sample = v[:3] if len(v) <= 3 else f'[{len(v)} items]'
                found.append((path, k, type(v).__name__, sample))
            walk_json(v, f"{path}.{k}", found)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:50]):  # limit depth
            walk_json(item, f"{path}[{i}]", found)

# Сканируем
results = []
for json_file in sorted(GD.glob('*.json')):
    if json_file.name.startswith('_'): continue
    try:
        d = json.loads(json_file.read_text(encoding='utf-8'))
        walk_json(d, json_file.name, results)
    except Exception as e:
        print(f"  ERR {json_file.name}: {e}")

# === Сводная статистика ===
print("=" * 80)
print("1. РЕЕСТР ТОНАЛЬНЫХ КЛЮЧЕЙ В game_data/")
print("=" * 80)
by_file = defaultdict(list)
for path, key, typ, sample in results:
    by_file[path].append((key, typ, sample))

for fname in sorted(by_file.keys()):
    entries = by_file[fname]
    print(f"\n  {fname}  ({len(entries)} ключей)")
    for key, typ, sample in entries[:6]:
        # Сокращаем sample
        s = str(sample)
        if len(s) > 90: s = s[:87] + '...'
        print(f"    .{key} [{typ}]: {s}")
    if len(entries) > 6:
        print(f"    ... and {len(entries)-6} more")

# === Статистика по системам ===
print()
print("=" * 80)
print("2. СИСТЕМЫ ТОНАЛЬНОСТИ (4D vs кастомные vs жанры)")
print("=" * 80)
sys_4d = []  # cynicism/violence/hope/sophistication
sys_custom = []  # tone_modifiers с кастомными чертами
sys_genre = []
sys_text = []  # текстовые дескрипторы

for path, key, typ, sample in results:
    if key in {'cynicism', 'violence', 'hope', 'sophistication'}:
        sys_4d.append((path, key, sample))
    elif key in {'tone_modifiers', 'tone_dynamics', 'tone_axes'}:
        sys_custom.append((path, key, sample))
    elif key in {'genre', 'genres', 'preferred_genres', 'subgenre'}:
        sys_genre.append((path, key, sample))
    elif key in {'tone', 'mood', 'atmosphere', 'emotional_palette'}:
        sys_text.append((path, key, sample))

print(f"\n  4D-вектор (cyn/vio/hop/soph): {len(sys_4d)} вхождений")
for p, k, s in sys_4d[:10]:
    print(f"    {p}: .{k} = {str(s)[:60]}")
if len(sys_4d) > 10: print(f"    ... +{len(sys_4d)-10}")

print(f"\n  tone_modifiers/dynamics (кастомные черты): {len(sys_custom)} вхождений")
for p, k, s in sys_custom[:10]:
    print(f"    {p}: .{k} = {str(s)[:80]}")

print(f"\n  Жанровая система: {len(sys_genre)} вхождений")
for p, k, s in sys_genre[:10]:
    print(f"    {p}: .{k} = {str(s)[:80]}")

print(f"\n  Текстовые дескрипторы (tone/mood/atmosphere): {len(sys_text)} вхождений")
for p, k, s in sys_text[:10]:
    print(f"    {p}: .{k} = {str(s)[:80]}")

# === Атмосфера локаций ===
print()
print("=" * 80)
print("3. АТМОСФЕРА ЛОКАЦИЙ (звук, свет, запах)")
print("=" * 80)
atmo_keys = {'atmosphere', 'lighting', 'scent', 'audio_landscape',
             'soundscape', 'olfactory', 'visual_cues', 'environmental_details',
             'environmental_narrative', 'mood_descriptors'}
atmo_results = [(p,k,s) for p,k,_,s in results if k in atmo_keys]
print(f"  Найдено {len(atmo_results)} вхождений:")
for p, k, s in atmo_results[:15]:
    print(f"    {p}: .{k} = {str(s)[:90]}")

# === Речевые паттерны ===
print()
print("=" * 80)
print("4. РЕЧЕВЫЕ ПАТТЕРНЫ И ДИАЛОГИ")
print("=" * 80)
speech_keys = {'dialogue_style', 'dialogue_patterns', 'narrative_voice',
               'speech_patterns', 'unique_dialogue_tags', 'speech_markers',
               'castes', 'social_castes', 'social_status'}
speech_results = [(p,k,s) for p,k,_,s in results if k in speech_keys]
print(f"  Найдено {len(speech_results)} вхождений:")
for p, k, s in speech_results[:15]:
    print(f"    {p}: .{k} = {str(s)[:100]}")

# === Использование в коде ===
print()
print("=" * 80)
print("5. ИСПОЛЬЗОВАНИЕ КЛЮЧЕЙ В src/ (живой код vs мертвый груз)")
print("=" * 80)
all_json_keys = set(k for _,k,_,_ in results)
used_keys = set(code_reads.keys())
dead_keys = all_json_keys - used_keys
alive_keys = all_json_keys & used_keys

print(f"\n  Ключей в JSON: {len(all_json_keys)}")
print(f"  Ключей, читаемых кодом: {len(used_keys)}")
print(f"  Ключей-зомби (в JSON, но НЕ читаются): {len(dead_keys)}")

print(f"\n  ЖИВЫЕ ключи (читаются кодом):")
for k in sorted(alive_keys):
    files = sorted(code_reads[k])
    print(f"    ✓ {k}  → {len(files)} files: {', '.join(f.replace('src/', '') for f in files[:3])}{'...' if len(files)>3 else ''}")

print(f"\n  МЕРТВЫЕ ключи (есть в JSON, не читаются):")
for k in sorted(dead_keys):
    files_in_json = sorted({p for p,_,_,_ in results if _})
    where = sorted({p for p,k2,_,_ in results if k2==k})
    print(f"    ✗ {k}  → JSON: {', '.join(where)[:100]}")

# === Рекомендации ===
print()
print("=" * 80)
print("6. СВОДНАЯ СТАТИСТИКА")
print("=" * 80)
print(f"  Всего JSON-файлов в game_data/: {len(list(GD.glob('*.json')))}")
print(f"  Файлов с тональными ключами: {len(by_file)}")
print(f"  Всего тональных вхождений: {len(results)}")
print(f"  Уникальных тональных ключей: {len(all_json_keys)}")
print(f"  Живых ключей: {len(alive_keys)} ({100*len(alive_keys)//max(1,len(all_json_keys))}%)")
print(f"  Мертвых ключей: {len(dead_keys)} ({100*len(dead_keys)//max(1,len(all_json_keys))}%)")
