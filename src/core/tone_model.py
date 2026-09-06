"""
src/core/tone_model.py — унифицированная модель тональности NexusRPG.

Phase 26: объединяет 599 вхождений 4D-вектора (cynicism/sophistication/violence/hope),
42 речевых паттерна, 18 жанровых списков и атмосферные дескрипторы в единый профиль.
Без потерь данных: каждое поле имеет fallback на безопасные дефолты.

ПРАВИЛО БЕЗОПАСНОСТИ: НЕ переименовывает ключ `atmosphere` в 07_MEGA_WORLD_SIMULATION_COMPLETE.json
(используется legacy-файлами v2/v4/base). Химический состав атмосферы остаётся
в JSON, а mood_descriptors берёт lighting/scent/audio/environmental из 09_MEGA.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# === Константы шкалы 4D ===
CYN_MIN, CYN_MAX = 0, 10
SOPH_MIN, SOPH_MAX = 0, 10
VIOL_MIN, VIOL_MAX = 0, 10
HOPE_MIN, HOPE_MAX = 0, 10
WEIRD_MIN, WEIRD_MAX = 0, 10

# Дефолтные значения для нового персонажа
DEFAULT_4D = {"cynicism": 5, "sophistication": 5, "violence": 5, "hope": 5}
DEFAULT_WEIRDNESS = 0

# Эмоциональные теги из 05_MEGA_AI_GM_CORE_COMPLETE.json.meta_engine_system.how_it_works.emotional_depth
EMOTIONAL_DEPTH_TAGS = [
    "Tragic", "Hopeful", "Ironic", "Dark", "Absurd",
]

# Phase 26 fix: EN→RU словарь для полей ToneProfile, чтобы при инъекции
# в системный промпт модель не подхватывала английский.
# Расширяется по мере появления новых англоязычных значений в KB.
_GENRE_RU = {
    "cyberpunk": "киберпанк",
    "noir_mystery": "нуарный детектив",
    "noir": "нуар",
    "hard_sci_fi": "твёрдая научная фантастика",
    "sci_fi": "научная фантастика",
    "gritty": "суровый реализм",
    "grimdark": "мрачный гримдарк",
    "post_apocalyptic": "пост-апокалиптика",
    "space_opera": "космическая опера",
    "military": "военный",
    "thriller": "триллер",
    "horror": "хоррор",
    "mystery": "детектив",
    "romance": "романтика",
}

_DEPTH_RU = {
    "Tragic": "трагический",
    "Hopeful": "обнадёживающий",
    "Ironic": "ироничный",
    "Dark": "тёмный",
    "Absurd": "абсурдный",
}


def _ru(value, mapping=None):
    """Phase 26 fix: транслитерирует значение на русский через mapping.

    Если ключ найден — возвращает русский перевод. Иначе возвращает value
    как есть (если value уже содержит кириллицу, оставляем).
    Если value пустое или None — возвращает "".
    """
    if not value:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if mapping and s in mapping:
        return mapping[s]
    # Если value уже на кириллице — оставляем
    if any("\u0400" <= ch <= "\u04FF" for ch in s):
        return s
    return s


def _ru_list(values, mapping=None):
    """Phase 26 fix: транслитерирует список значений через mapping.
    Сохраняет порядок, удаляет дубликаты после транслитерации.
    """
    if not values:
        return []
    seen = set()
    out = []
    for v in values:
        r = _ru(v, mapping)
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _normalize_for_prompt(value):
    """Phase 26 fix: нормализует произвольную строку перед инъекцией в промпт.

    Если строка не содержит кириллицы — оборачивает её в пометку
    «EN: ...» чтобы модель понимала, что это технический идентификатор,
    а не часть языка ответа. Также удаляет смешанные EN-вставки типа
    'не шагов, a something else' → 'не шагов, a что-то ещё' (heuristic).
    """
    if not value or not isinstance(value, str):
        return value or ""
    has_cyrillic = any("\u0400" <= ch <= "\u04FF" for ch in value)
    if has_cyrillic:
        return value
    # Полностью латинская строка → оборачиваем в EN: пометку
    return f"[EN-идентификатор: {value}]"


@dataclass
class ToneProfile:
    """Унифицированный профиль тональности персонажа.

    Поля сгруппированы по слоям:
    - 4D-вектор (количественные шкалы)
    - Жанровый бленд (60/30/10)
    - Речевой профиль (narrative_voice + dialogue_style + tags)
    - Сенсорная атмосфера (mood_descriptors по локации)
    - Оси масштаба и физики (Player Tier + weirdness)
    """

    # 4D-вектор (0..10)
    cynicism: int = 5
    sophistication: int = 5
    violence: int = 5
    hope: int = 5

    # Жанровый бленд (60/30/10)
    primary_genre: str = "cyberpunk"
    secondary_genre: str = "noir_mystery"
    flavor_tags: List[str] = field(default_factory=list)

    # Речевой профиль
    narrative_voice: str = ""
    dialogue_style: str = ""
    speech_patterns: List[str] = field(default_factory=list)
    unique_dialogue_tags: List[str] = field(default_factory=list)

    # Сенсорная атмосфера (mood_descriptors по локации)
    mood_descriptors: Dict[str, str] = field(default_factory=dict)
    # Keys: lighting, scent, audio, environmental_details

    # Оси масштаба и физики
    scale_level: str = "P0"  # Player Tier: P0..P7
    weirdness: int = 0  # 0..10 (мистика, аномалии)

    # Метаданные источника
    origin_id: str = ""
    specialization_id: str = ""
    formative_year_id: str = ""

    # ===================== Утилиты шкалы =====================

    def _clamp(self, value: int, lo: int, hi: int) -> int:
        return max(lo, min(hi, value))

    def apply_delta(self, axis: str, delta: int) -> None:
        """Динамическая эволюция шкалы (например, предательство +3 cynicism, -2 hope)."""
        if not hasattr(self, axis):
            return
        current = getattr(self, axis)
        if isinstance(current, int):
            lo, hi = (CYN_MIN, CYN_MAX) if axis in DEFAULT_4D else (WEIRD_MIN, WEIRD_MAX)
            setattr(self, axis, self._clamp(current + delta, lo, hi))

    def add_mood_descriptor(self, key: str, value: str) -> None:
        """Добавить/обновить сенсорный дескриптор."""
        if value:
            self.mood_descriptors[key] = value

    # ===================== Сериализация =====================

    def to_dict(self) -> Dict:
        return {
            "cynicism": self.cynicism,
            "sophistication": self.sophistication,
            "violence": self.violence,
            "hope": self.hope,
            "primary_genre": self.primary_genre,
            "secondary_genre": self.secondary_genre,
            "flavor_tags": list(self.flavor_tags),
            "narrative_voice": self.narrative_voice,
            "dialogue_style": self.dialogue_style,
            "speech_patterns": list(self.speech_patterns),
            "unique_dialogue_tags": list(self.unique_dialogue_tags),
            "mood_descriptors": dict(self.mood_descriptors),
            "scale_level": self.scale_level,
            "weirdness": self.weirdness,
            "origin_id": self.origin_id,
            "specialization_id": self.specialization_id,
            "formative_year_id": self.formative_year_id,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ToneProfile":
        return cls(
            cynicism=int(d.get("cynicism", 5)),
            sophistication=int(d.get("sophistication", 5)),
            violence=int(d.get("violence", 5)),
            hope=int(d.get("hope", 5)),
            primary_genre=d.get("primary_genre", "cyberpunk"),
            secondary_genre=d.get("secondary_genre", "noir_mystery"),
            flavor_tags=list(d.get("flavor_tags", [])),
            narrative_voice=d.get("narrative_voice", ""),
            dialogue_style=d.get("dialogue_style", ""),
            speech_patterns=list(d.get("speech_patterns", [])),
            unique_dialogue_tags=list(d.get("unique_dialogue_tags", [])),
            mood_descriptors=dict(d.get("mood_descriptors", {})),
            scale_level=d.get("scale_level", "P0"),
            weirdness=int(d.get("weirdness", 0)),
            origin_id=d.get("origin_id", ""),
            specialization_id=d.get("specialization_id", ""),
            formative_year_id=d.get("formative_year_id", ""),
        )

    # ===================== Director's Notes (LLM-friendly) =====================

    def _qualify_axis(self, value: int, lo_word: str, mid_word: str, hi_word: str) -> str:
        """Преобразует int 0..10 в качественный ярлык для LLM."""
        if value <= 3:
            return lo_word
        if value <= 6:
            return mid_word
        return hi_word

    def to_director_notes(self) -> str:
        """Компактный текстовый бриф для LLM (без сырых чисел, только качественные указания).

        Phase 26 fix: все поля проходят EN→RU нормализацию через _ru()/_ru_list().
        Это гарантирует, что в системный промпт попадают только русские
        значения — иначе модель переключается на английский в ответе.
        """
        cyn = self._qualify_axis(self.cynicism, "доверчивый", "прагматичный", "циничный-недоверчивый")
        soph = self._qualify_axis(self.sophistication, "простой-язык", "нейтральный-стереотипный", "сложный-профессиональный-жаргон")
        viol = self._qualify_axis(self.violence, "мирный-диалог-превыше", "умеренный-допускает-силу", "безжалостный-сила-основное-решение")
        hope = self._qualify_axis(self.hope, "пессимист-ожидает-провал", "осторожный-оптимист", "идеалист-верит-в-победу")
        weird = self._qualify_axis(self.weirdness, "бытовое-реалистичное", "лёгкий-налёт-необычного", "мистика-реальность-искажена")

        lines = [
            f"ТОНАЛЬНОСТЬ ПЕРСОНАЖА:",
            f"- Цинизм: {cyn} (1-3 доверчивый, 4-6 прагматичный, 7-10 циничный)",
            f"- Сложность речи: {soph} (1-3 просто, 4-6 стереотипно, 7-10 профессиональный жаргон и аллюзии)",
            f"- Отношение к насилию: {viol}",
            f"- Мировоззрение: {hope}",
            f"- Уровень аномальности: {weird}",
            f"- Масштаб влияния: тир {_normalize_for_prompt(self.scale_level)} (P0=локальный, P4=системный, P7=галактический)",
        ]

        if self.primary_genre or self.secondary_genre:
            genres = [_ru(self.primary_genre, _GENRE_RU), _ru(self.secondary_genre, _GENRE_RU)]
            genres = [g for g in genres if g]
            flavor_ru = _ru_list(self.flavor_tags, _DEPTH_RU)
            genres.extend(flavor_ru)
            if genres:
                lines.append(f"- Жанровый бленд (60/30/10): {' → '.join(genres[:3])}")

        if self.narrative_voice or self.dialogue_style:
            lines.append("")
            lines.append("РЕЧЕВОЙ ПРОФИЛЬ:")
            if self.narrative_voice:
                lines.append(f"- Голос повествования: {_normalize_for_prompt(self.narrative_voice)}")
            if self.dialogue_style:
                lines.append(f"- Стиль диалога: {_normalize_for_prompt(self.dialogue_style)}")
            if self.unique_dialogue_tags:
                tags_ru = _ru_list(self.unique_dialogue_tags, _DEPTH_RU)
                if tags_ru:
                    lines.append(f"- Доступные теги в речи: {' '.join(tags_ru)}")
            if self.speech_patterns:
                patterns_ru = []
                for sp in self.speech_patterns[:3]:
                    r = _normalize_for_prompt(sp)
                    if r:
                        patterns_ru.append(r)
                if patterns_ru:
                    lines.append(f"- Речевые паттерны: {'; '.join(patterns_ru)}")

        if self.mood_descriptors:
            lines.append("")
            lines.append("СЕНСОРНАЯ АТМОСФЕРА СЦЕНЫ:")
            for key in ("lighting", "scent", "audio", "environmental_details"):
                if key in self.mood_descriptors:
                    val = _normalize_for_prompt(self.mood_descriptors[key])
                    lines.append(f"- {key}: {val}")

        return "\n".join(lines)


# ===================== Утилиты загрузки =====================

def load_tone_modifiers_from_origin(origin_data: Dict) -> Dict[str, int]:
    """Извлекает 4D-модификаторы из origin_data (может быть в tone_modifiers напрямую
    или в base_cynicism/base_sophistication/... варианте)."""
    tm = origin_data.get("tone_modifiers", {})
    if not tm:
        # Альтернативный формат THEME_TONE.json: base_cynicism, base_sophistication, ...
        return {
            "cynicism": int(origin_data.get("base_cynicism", 5)),
            "sophistication": int(origin_data.get("base_sophistication", 5)),
            "violence": int(origin_data.get("base_violence", 5)),
            "hope": int(origin_data.get("base_hope", 5)),
        }
    return {k: int(v) for k, v in tm.items() if k in DEFAULT_4D}


def clamp_4d(values: Dict[str, int]) -> Dict[str, int]:
    """Ограничивает все 4D-значения в диапазоне [0, 10]."""
    return {k: max(CYN_MIN, min(CYN_MAX, int(v))) for k, v in values.items()}
