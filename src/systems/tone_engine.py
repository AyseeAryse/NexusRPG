"""
src/systems/tone_engine.py — сервис построения ToneProfile из game_data.

Phase 26: подключает 599 вхождений 4D-вектора, 42 речевых паттерна,
18 жанровых списков и атмосферные дескрипторы к реальному движку.

Источники:
- 09_MEGA_NARRATIVE_THEMES_COMPLETE.json (new_origins, new_specializations, atmosphere_components)
- THEME_TONE.json (origin_genre_mappings, formative_years_genre_modifiers)
- CHARACTER_LIFEPATH.json (theme_tone_integration)
- DIALOGUE_INTEGRATED_WITH_LIFEPATH.json (social_castes, speech_patterns)
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.core.tone_model import (
    ToneProfile, DEFAULT_4D, EMOTIONAL_DEPTH_TAGS,
    load_tone_modifiers_from_origin, clamp_4d,
)


# Тиры P0..P7 для масштаба (Phase 16 Player Tiers)
TIER_ORDER = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]


class ToneEngine:
    """Загружает правила тональности из game_data и формирует ToneProfile."""

    def __init__(self, kb_files: Dict[str, Any]):
        self.kb = kb_files
        self._origins: Dict[str, Dict] = {}
        self._specs: Dict[str, Dict] = {}
        self._fy_modifiers: Dict[str, Dict] = {}
        self._atmo_components: Dict[str, Any] = {}
        self._genome_mappings: Dict[str, Dict] = {}
        self._social_castes: List[Dict] = []
        self._dialogue_tags_by_origin: Dict[str, List[str]] = {}
        self._speech_patterns_by_origin: Dict[str, List[str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Один раз при init: парсит все тональные источники из KB."""
        # 1) 09_MEGA_NARRATIVE_THEMES_COMPLETE.json
        themes = self.kb.get("09_MEGA_NARRATIVE_THEMES_COMPLETE.json", {}) or {}
        # 1a) new origins/specs
        prof = themes.get("expanded_lifepath_tone_profiles", {})
        self._origins.update(prof.get("new_origins_tone_profiles", {}) or {})
        self._specs.update(prof.get("new_specializations_tone_profiles", {}) or {})
        # 1b) atmosphere_components → mood_descriptors по умолчанию
        self._atmo_components = themes.get("dynamic_atmosphere_engine", {}).get("atmosphere_components", {}) or {}
        # 1c) lifepath integration: speech_patterns_by_origin, dialogue_tags
        li = themes.get("advanced_dialogue_system_lifepath", {}).get("lifepath_integration", {}) or {}
        self._speech_patterns_by_origin = dict(li.get("speech_patterns_by_origin", {}) or {})
        self._dialogue_tags_by_origin = dict(li.get("dialogue_tags_by_origin", {}) or {})

        # 2) THEME_TONE.json
        tt = self.kb.get("THEME_TONE.json", {}) or {}
        lgi = tt.get("lifepath_genre_influence", {}) or {}
        self._genome_mappings = dict(lgi.get("origin_genre_mappings", {}) or {})
        self._fy_modifiers = dict(lgi.get("formative_years_genre_modifiers", {}) or {})

        # 3) CHARACTER_LIFEPATH.json
        clp = self.kb.get("CHARACTER_LIFEPATH.json", {}) or {}
        # theme_tone_integration может лежать здесь

        # 4) DIALOGUE_INTEGRATED_WITH_LIFEPATH.json
        dlg = self.kb.get("DIALOGUE_INTEGRATED_WITH_LIFEPATH.json", {}) or {}
        self._social_castes = list(dlg.get("social_castes", []) or [])

    # ===================== Public API =====================

    def build_character_tone(self, character: Dict) -> ToneProfile:
        """Собирает стартовый ToneProfile из Origin + Formative Years + Specialization."""
        profile = ToneProfile()
        origin_id = character.get("origin", "")
        spec_id = character.get("specialization", "")
        fy_id = character.get("formative_years", "")

        profile.origin_id = origin_id
        profile.specialization_id = spec_id
        profile.formative_year_id = fy_id

        # 1) Origin tone (4D + жанры + voice + dialogue)
        origin_data = self._lookup_origin(origin_id)
        if origin_data:
            mods = load_tone_modifiers_from_origin(origin_data)
            mods = clamp_4d(mods)
            profile.cynicism = mods.get("cynicism", 5)
            profile.sophistication = mods.get("sophistication", 5)
            profile.violence = mods.get("violence", 5)
            profile.hope = mods.get("hope", 5)

            # Жанровый бленд 60/30/10
            genres = origin_data.get("preferred_genres", []) or []
            if genres:
                profile.primary_genre = genres[0]
                profile.secondary_genre = genres[1] if len(genres) > 1 else "noir_mystery"
                profile.flavor_tags = genres[2:5]

            profile.narrative_voice = origin_data.get("narrative_voice", "")
            profile.dialogue_style = origin_data.get("dialogue_style", "")

        # 2) Specialization tone (дополнительные модификаторы, additive)
        spec_data = self._lookup_spec(spec_id)
        if spec_data:
            spec_mods = spec_data.get("tone_modifiers", {}) or {}
            spec_mods = clamp_4d(spec_mods)
            for axis in ("cynicism", "sophistication", "violence", "hope"):
                if axis in spec_mods:
                    profile.apply_delta(axis, spec_mods[axis] - 5)
            # Жанры: если есть — сливаем с origin
            spec_genres = spec_data.get("preferred_genres", []) or []
            if spec_genres and not profile.flavor_tags:
                profile.flavor_tags = spec_genres[:3]
            if not profile.narrative_voice and spec_data.get("narrative_voice"):
                profile.narrative_voice = spec_data["narrative_voice"]

        # 3) Formative Years adjustment (delta по 4D)
        if fy_id and fy_id in self._fy_modifiers:
            tone_adj = self._fy_modifiers[fy_id].get("tone_adjustment", {}) or {}
            for axis, delta in tone_adj.items():
                if axis in DEFAULT_4D:
                    profile.apply_delta(axis, int(delta))

        # 4) Dialogue tags & speech patterns (по origin)
        if origin_id in self._dialogue_tags_by_origin:
            profile.unique_dialogue_tags = list(self._dialogue_tags_by_origin[origin_id])
        if origin_id in self._speech_patterns_by_origin:
            profile.speech_patterns = list(self._speech_patterns_by_origin[origin_id])

        # 5) Default mood_descriptors из atmosphere_components
        self._apply_default_mood(profile)

        # 6) Phase 26: эвристический fallback для непокрытых origin/spec
        # Если narrative_voice или dialogue_style пусты — генерируем из атрибутов
        self._apply_heuristic_fallback(profile, character)

        return profile

    def _apply_heuristic_fallback(self, profile: ToneProfile, character: Dict) -> None:
        """Phase 26 Step 3: генерирует voice/dialogue/tags, если JSON не покрывает origin/spec.

        Логика:
        - Высокая Сила/Бой → "Прямолинейный, тактический, нацеленный на угрозы"
        - Высокий Интеллект → "Аналитический, методичный"
        - Высокая Харизма → "Манипулятивный, обаятельный"
        - dialogue_tags по ключевым навыкам: combat→[Бой], stealth→[Скрытность] и т.д.
        """
        attrs = character.get("attributes", {}) or {}
        skills = character.get("skills", {}) or {}

        # === narrative_voice fallback ===
        if not profile.narrative_voice:
            # Сортируем атрибуты по убыванию
            top_attrs = sorted(attrs.items(), key=lambda kv: -kv[1])[:2]
            if top_attrs:
                primary_attr, primary_val = top_attrs[0]
                if primary_attr in ("strength", "endurance", "reflexes", "dexterity") and primary_val >= 6:
                    profile.narrative_voice = "Прямолинейный, тактический, нацеленный на угрозы"
                elif primary_attr in ("intelligence", "tech_empathy", "willpower") and primary_val >= 6:
                    profile.narrative_voice = "Аналитический, методичный, расчётливый"
                elif primary_attr == "charisma" and primary_val >= 6:
                    profile.narrative_voice = "Обаятельный, манипулятивный, социально-грамотный"
                else:
                    profile.narrative_voice = "Сбалансированный, прагматичный, адаптивный"

        # === dialogue_style fallback ===
        if not profile.dialogue_style:
            # Берём top-2 навыка
            top_skills = sorted(skills.items(), key=lambda kv: -kv[1])[:2]
            if top_skills:
                skill_names = [s[0] for s in top_skills if s[1] > 0]
                if "hacking" in skill_names or "technology" in skill_names:
                    profile.dialogue_style = "Технический жаргон, точные формулировки, отсылки к протоколам"
                elif "combat" in skill_names or "firearms" in skill_names:
                    profile.dialogue_style = "Краткий, императивный, фокус на действии и угрозе"
                elif "negotiation" in skill_names or "leadership" in skill_names:
                    profile.dialogue_style = "Дипломатичный, с подтекстом, ориентация на компромисс"
                elif "stealth" in skill_names or "streetwise" in skill_names:
                    profile.dialogue_style = "Осторожный, недомолвки, проверка собеседника"
                elif "medicine" in skill_names or "science" in skill_names:
                    profile.dialogue_style = "Аналитический, с оговорками, профессиональная лексика"
                else:
                    profile.dialogue_style = "Нейтральный, общий стиль, адаптивный к собеседнику"

        # === unique_dialogue_tags fallback (по навыкам) ===
        if not profile.unique_dialogue_tags:
            tag_map = {
                "combat": "[Бой]",
                "firearms": "[Огнестрел]",
                "melee": "[Ближний бой]",
                "stealth": "[Скрытность]",
                "hacking": "[Взлом]",
                "technology": "[Техника]",
                "negotiation": "[Переговоры]",
                "leadership": "[Лидерство]",
                "medicine": "[Медицина]",
                "science": "[Наука]",
                "survival": "[Выживание]",
                "streetwise": "[Улица]",
                "investigation": "[Расследование]",
                "intimidation": "[Запугивание]",
                "piloting": "[Пилот]",
            }
            tags = []
            for skill_name, skill_val in skills.items():
                if skill_val >= 2 and skill_name in tag_map:
                    tags.append(tag_map[skill_name])
            if not tags:
                # fallback: 1 тег по top attribute
                top_attr = max(attrs.items(), key=lambda kv: kv[1], default=("", 0))
                if top_attr[0]:
                    attr_tag_map = {
                        "strength": "[Сила]", "endurance": "[Стойкость]", "dexterity": "[Ловкость]",
                        "intelligence": "[Аналитика]", "charisma": "[Харизма]", "reflexes": "[Реакция]",
                        "willpower": "[Воля]", "tech_empathy": "[Технолог]",
                    }
                    if top_attr[0] in attr_tag_map:
                        tags.append(attr_tag_map[top_attr[0]])
            profile.unique_dialogue_tags = tags[:4]  # max 4 тега

    def apply_scene_context(self, profile: ToneProfile, location: Optional[Dict], tier_info: Optional[Dict]) -> ToneProfile:
        """Накладывает сенсорные маркеры локации + масштаб тира.

        location: {planet, city, district, place}
        tier_info: {tier: 'P0'..'P7', name: '...'}
        """
        if location:
            district = (location.get("district") or "").lower()
            place = (location.get("place") or "").lower()
            # Подбираем модификатор по ключевым словам
            if any(w in district + place for w in ["трущоб", "slums", "нижний"]):
                profile.add_mood_descriptor("scent", "переработанный воздух, уличная гарь")
                profile.add_mood_descriptor("lighting", "тусклый неон, мерцающие вывески")
            elif any(w in district + place for w in ["корпоратив", "верхний", "деловой"]):
                profile.add_mood_descriptor("scent", "стерильный воздух с лёгким ароматом озон")
                profile.add_mood_descriptor("lighting", "холодный LED, зеркальный бетон")
            elif any(w in district + place for w in ["порт", "док", "космопорт"]):
                profile.add_mood_descriptor("scent", "машинное масло, ионизированный воздух")
                profile.add_mood_descriptor("audio", "гул двигателей, объявления по громкой связи")
            elif any(w in district + place for w in ["шахт", "рудник"]):
                profile.add_mood_descriptor("scent", "металлическая пыль, смазки")
                profile.add_mood_descriptor("audio", "работа буров, скрежет металла")

        if tier_info:
            tier = tier_info.get("tier") or tier_info.get("name") or "P0"
            # Нормализуем: P0..P7
            if tier not in TIER_ORDER:
                for t in TIER_ORDER:
                    if t in str(tier):
                        tier = t
                        break
                else:
                    tier = "P0"
            profile.scale_level = tier

        return profile

    def apply_event_delta(self, profile: ToneProfile, event_name: str) -> ToneProfile:
        """Динамическая эволюция шкал при ключевых триггерах.

        События:
          - heat_up, betrayal, defeat, first_kill, save_lives
          - lose_innocence, gain_power, romantic_event
        """
        deltas = {
            "heat_up": {"cynicism": 1, "hope": -1},
            "betrayal": {"cynicism": 3, "hope": -2, "sophistication": 1},
            "defeat": {"cynicism": 1, "hope": -1, "violence": 1},
            "first_kill": {"cynicism": 2, "violence": 1, "hope": -1},
            "save_lives": {"hope": 2, "cynicism": -1, "sophistication": 1},
            "lose_innocence": {"cynicism": 2, "hope": -1, "weirdness": 1},
            "gain_power": {"cynicism": 1, "violence": 1, "sophistication": 1, "hope": -1},
            "romantic_event": {"hope": 1, "cynicism": -1, "violence": -1},
            "discover_conspiracy": {"cynicism": 2, "sophistication": 2, "hope": -1},
        }
        for axis, delta in deltas.get(event_name, {}).items():
            profile.apply_delta(axis, int(delta))
        return profile

    # ===================== Internal helpers =====================

    def _lookup_origin(self, origin_id: str) -> Optional[Dict]:
        """Ищет origin в new_origins, fallback на lifepath_genre_mappings."""
        if origin_id in self._origins:
            return self._origins[origin_id]
        if origin_id in self._genome_mappings:
            # genome mapping содержит base_cyn и т.д., но не narrative_voice
            return self._genome_mappings[origin_id]
        return None

    def _lookup_spec(self, spec_id: str) -> Optional[Dict]:
        return self._specs.get(spec_id)

    def _apply_default_mood(self, profile: ToneProfile) -> None:
        """Применяет дефолтные mood_descriptors из atmosphere_components.visual_style
        (только если они не были переопределены в apply_scene_context)."""
        vs = self._atmo_components.get("visual_style", {}) or {}
        audio = self._atmo_components.get("audio_landscape", {}) or {}

        if "lighting" not in profile.mood_descriptors and vs.get("lighting"):
            profile.mood_descriptors["lighting"] = vs["lighting"]
        if "environmental_details" not in profile.mood_descriptors and vs.get("environmental_details"):
            profile.mood_descriptors["environmental_details"] = vs["environmental_details"]
        if "audio" not in profile.mood_descriptors and audio.get("ambient_sounds"):
            profile.mood_descriptors["audio"] = audio["ambient_sounds"]
        # scent — дефолт не предусмотрен в atmosphere_components, остаётся пустым


def make_tone_engine_from_kb(kb_files: Dict[str, Any]) -> ToneEngine:
    """Фабрика для удобного создания из существующего KnowledgeBase."""
    return ToneEngine(kb_files)
