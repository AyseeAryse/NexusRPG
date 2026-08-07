"""
Knowledge Base - Loads and manages game data JSON files.
Handles version conflicts by preferring newer/enhanced versions.
"""
import json
import os
import re
from typing import Dict, List, Optional

# Version priority: higher = preferred
# V3 > V2 > MEGA > base
VERSION_PRIORITY = {
    'V3_MASSIVE': 50,
    'V2_ENHANCED': 45,
    'V2_COMPREHENSIVE': 45,
    'V2': 40,
    'ENHANCED': 35,
    'MEGA': 30,
    'COMPLETE': 25,
    'STANDARDIZED': 20,
    'base': 10,
}

# Explicit override map: base_name -> preferred file
PREFERRED_FILES = {
    'CHARACTER_LIFEPATH': 'CHARACTER_LIFEPATH.json',  # base has the stages we need
    'CHARACTER_CORE': 'CHARACTER_CORE.json',
    'COMBAT': 'COMBAT.json',
    'ECONOMY': 'ECONOMY.json',
    'HACKING': 'HACKING_V2_QUANTUM_AGE.json',
    'INVESTIGATION': 'INVESTIGATION_V2_GALACTIC_DETECTIVE.json',
    'MECHANICS': 'MECHANICS_V2_INTEGRATED_SYSTEMS.json',
    'MODIFICATION': 'MODIFICATION_V2_QUANTUM_BIOTECH.json',
    'NARRATIVE_INTERFACE': 'NARRATIVE_INTERFACE_V2_ADAPTIVE.json',
    'GM_TOOLKIT': 'GM_TOOLKIT_V2_COMPREHENSIVE.json',
    'AI_RPG_CORE': 'AI_RPG_CORE_V2_ENHANCED.json',
    'AUTOMATION': 'AUTOMATION_V2_COMPREHENSIVE.json',
    'WORLD_SIM': 'WORLD_SIM_V2_LIVING_UNIVERSE.json',
    'ENHANCED_EVENT_GENERATOR': 'ENHANCED_EVENT_GENERATOR_V2.json',
    'PROGRESSION': 'PROGRESSION.json',  # base has more content
    'PLAYER_INTERFACE': 'PLAYER_INTERFACE_V2_ENHANCED.json',
    'NPC_RELATIONS': 'NPC_RELATIONS_REPUTATION_STANDARDIZED_FINAL.json',
    'POLITICS': 'POLITICS.json',
    'PSYCHOLOGY': 'PSYCHOLOGY.json',
}

# Category mapping for context retrieval
CATEGORY_MAP = {
    'CHARACTER': ['CHARACTER_CORE', 'CHARACTER_ATTRIBUTES', 'CHARACTER_SKILLS',
                  'CHARACTER_LIFEPATH', 'CHARACTER_PERKS', 'CHARACTER_CREATION_V2',
                  'CHARACTER_SPECIALIZATIONS', 'PSYCHOLOGY', 'PROGRESSION'],
    'COMBAT': ['COMBAT', 'HACKING', 'TECH_EQUIPMENT', 'MODIFICATION'],
    'NARRATIVE': ['NARRATIVE_INTERFACE', 'THEME_TONE', 'AI_NARRATOR', 'VISUALS_ENGINE'],
    'SOCIAL': ['NPC_RELATIONS', 'NPC_ARCHETYPES', 'NPC_NAME_GENERATOR', 'DIALOGUE', 'DIPLOMACY'],
    'ECONOMY': ['ECONOMY', 'CRAFTING_BLUEPRINTS', 'TRADE_ROUTES', 'MARKET_EVENT'],
    'WORLD': ['WORLDBUILD', 'WORLD_SIM', 'DYNAMIC_WORLD', 'ENVIRONMENT_SURVIVAL',
              'FACTIONS_MASTER', 'FACTIONS_LIFEPATH'],
    'QUEST': ['QUEST_SYSTEM', 'INVESTIGATION', 'STARTING_QUESTS', 'SPACE_ENCOUNTER'],
    'MECHANICS': ['MECHANICS', 'RULEBOOK', 'GM_TOOLKIT', 'AUTOMATION'],
    'AI': ['AI_RPG_CORE', 'AI_NARRATOR', 'META_ENGINE'],
    'POLITICS': ['POLITICS', 'STRATEGIC_COMMAND'],
    'VEHICLES': ['VEHICLES'],
    'INTERFACE': ['PLAYER_INTERFACE', 'PLAYER_VIEW_ADAPTER', 'TIME_DISPLAY'],
}


class KnowledgeBase:
    def __init__(self, data_dir: str, db_dir: str = None):
        self.data_dir = data_dir
        self.db_dir = db_dir
        self.files: Dict[str, dict] = {}
        self.file_categories: Dict[str, str] = {}
        self._load_all(data_dir)
        if db_dir and os.path.exists(db_dir):
            self._load_database(db_dir)

    def _load_all(self, data_dir: str):
        """Load all JSON files, resolving version conflicts."""
        if not os.path.exists(data_dir):
            print(f"[KB] Data dir not found: {data_dir}")
            return

        # First pass: load everything
        all_files = {}
        errors = 0
        for fname in sorted(os.listdir(data_dir)):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_files[fname] = data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                errors += 1

        # Second pass: resolve conflicts
        # Group by base name
        groups = {}
        for fname in all_files:
            base = self._get_base_name(fname)
            if base not in groups:
                groups[base] = []
            groups[base].append(fname)

        # Pick best version for each group
        for base, fnames in groups.items():
            if len(fnames) == 1:
                self.files[fnames[0]] = all_files[fnames[0]]
            else:
                # Check explicit preference
                if base in PREFERRED_FILES and PREFERRED_FILES[base] in fnames:
                    chosen = PREFERRED_FILES[base]
                else:
                    # Auto-pick: prefer larger, newer files
                    chosen = max(fnames, key=lambda f: (self._version_score(f), len(json.dumps(all_files[f]))))
                self.files[chosen] = all_files[chosen]

        # Also load any standalone files not in conflict groups
        # (they're already handled above since groups with 1 file get loaded)

        # Categorize files
        for fname in self.files:
            self.file_categories[fname] = self._categorize(fname)

        print(f"[KB] Loaded {len(self.files)} files ({errors} errors, {len(all_files) - len(self.files)} duplicates skipped) from {data_dir}")

    def _get_base_name(self, fname: str) -> str:
        """Extract base name for grouping: COMBAT.json -> COMBAT, COMBAT_V2.json -> COMBAT."""
        name = fname.replace('.json', '')
        # Remove numbered prefixes like 01_, 03_ etc
        name = re.sub(r'^\d+_MEGA_', '', name)
        name = re.sub(r'^\d+_', '', name)
        # Remove version suffixes
        name = re.sub(r'_V\d+.*$', '', name)
        name = re.sub(r'_COMPLETE$', '', name)
        name = re.sub(r'_ENHANCED$', '', name)
        name = re.sub(r'_COMPREHENSIVE$', '', name)
        name = re.sub(r'_STANDARDIZED.*$', '', name)
        name = re.sub(r'_MASSIVE.*$', '', name)
        name = re.sub(r'_UNIFIED$', '', name)
        return name

    def _version_score(self, fname: str) -> int:
        """Score a filename for version priority."""
        for key, score in VERSION_PRIORITY.items():
            if key in fname.upper():
                return score
        return VERSION_PRIORITY['base']

    def _categorize(self, fname: str) -> str:
        """Assign a category to a file."""
        upper = fname.upper()
        for cat, keywords in CATEGORY_MAP.items():
            for kw in keywords:
                if kw in upper:
                    return cat
        return 'OTHER'

    def _load_database(self, db_dir: str):
        """Load user database files from subdirectories."""
        cat_map = {
            'factions': 'WORLD', 'skills': 'CHARACTER', 'lore': 'WORLD',
            'npcs': 'SOCIAL', 'locations': 'WORLD', 'items': 'ECONOMY',
            'quests': 'QUEST',
        }
        count = 0
        for subdir in os.listdir(db_dir):
            sub_path = os.path.join(db_dir, subdir)
            if not os.path.isdir(sub_path):
                continue
            for fname in os.listdir(sub_path):
                if not fname.endswith('.json'):
                    continue
                fpath = os.path.join(sub_path, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    key = f"db_{subdir}_{fname}"
                    self.files[key] = data
                    self.file_categories[key] = cat_map.get(subdir, 'OTHER')
                    count += 1
                except:
                    pass
        if count:
            print(f"[KB] Loaded {count} user database files from {db_dir}")

    def get_file(self, fname: str) -> Optional[dict]:
        """Get a specific file by name."""
        if fname in self.files:
            return self.files[fname]
        # Try partial match
        for key in self.files:
            if fname.replace('.json', '') in key:
                return self.files[key]
        return None

    def list_files(self) -> List[Dict]:
        """List all loaded files with metadata."""
        result = []
        for fname, data in self.files.items():
            result.append({
                "filename": fname,
                "category": self.file_categories.get(fname, 'OTHER'),
                "module_name": data.get("module_name", data.get("library_name", "")),
                "version": data.get("version", ""),
                "description": data.get("description", "")[:100],
            })
        return sorted(result, key=lambda x: (x["category"], x["filename"]))

    def get_relevant_context(self, action: str, max_tokens: int = 2500) -> str:
        """Get relevant context from knowledge base for AI prompt."""
        action_lower = action.lower()

        # Determine relevant categories
        relevant_cats = set()
        keyword_map = {
            'CHARACTER': ['персонаж', 'характер', 'навык', 'атрибут', 'уровень', 'опыт', 'перк'],
            'COMBAT': ['бой', 'атак', 'стрел', 'оружие', 'защит', 'урон', 'хак', 'взлом'],
            'SOCIAL': ['npc', 'разговор', 'диалог', 'убед', 'уговор', 'торг', 'репутац'],
            'ECONOMY': ['купить', 'продать', 'кредит', 'магазин', 'крафт', 'торг', 'рынок'],
            'WORLD': ['мир', 'планет', 'город', 'фракц', 'локац', 'район', 'станци'],
            'QUEST': ['квест', 'задание', 'миссия', 'расслед', 'контракт', 'работа'],
            'MECHANICS': ['правил', 'бросок', 'кубик', 'проверк', 'механик'],
            'VEHICLES': ['корабль', 'транспорт', 'пилот', 'полёт', 'машин'],
            'POLITICS': ['полит', 'власть', 'выбор', 'стратег', 'правительств'],
        }

        for cat, keywords in keyword_map.items():
            for kw in keywords:
                if kw in action_lower:
                    relevant_cats.add(cat)

        # Always include some base context
        if not relevant_cats:
            relevant_cats = {'WORLD', 'NARRATIVE'}

        # Gather context
        context_parts = []
        budget = max_tokens * 4  # rough char-to-token ratio

        for fname, data in self.files.items():
            cat = self.file_categories.get(fname, 'OTHER')
            if cat not in relevant_cats:
                continue

            snippet = self._extract_snippet(data, action_lower, budget // len(relevant_cats))
            if snippet:
                context_parts.append(f"[{fname}]\n{snippet}")

        result = "\n\n".join(context_parts)
        return result[:budget] if len(result) > budget else result

    def _extract_snippet(self, data: dict, query: str, max_chars: int = 1000) -> str:
        """Extract the most relevant snippet from a data file."""
        text = json.dumps(data, ensure_ascii=False, indent=None)
        if len(text) <= max_chars:
            return text

        # Try to find relevant sections
        parts = []
        if isinstance(data, dict):
            for key, val in data.items():
                key_lower = key.lower()
                val_str = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
                # Include small values and relevant-looking keys
                if len(val_str) < 500 or any(q in key_lower for q in query.split()):
                    parts.append(f'"{key}": {val_str[:400]}')
                if sum(len(p) for p in parts) > max_chars:
                    break

        return "\n".join(parts)[:max_chars] if parts else text[:max_chars]

    def get_character_presets(self) -> List[Dict]:
        """Get character presets from balanced_character_presets.json."""
        data = self.get_file("balanced_character_presets.json")
        if not data:
            return []
        return data.get("presets", data.get("characters", []))

    def get_files_by_category(self, category: str) -> List[Dict]:
        """Get all files in a category."""
        return [
            {"filename": fn, "data": data}
            for fn, data in self.files.items()
            if self.file_categories.get(fn) == category
        ]
