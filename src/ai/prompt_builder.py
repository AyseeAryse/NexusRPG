"""
src/ai/prompt_builder.py — построитель системного промпта для AI-GM.

Phase 26: интегрирует ToneProfile (Phase 26 Step 1-2) в финальный системный промпт.

Структура промпта:
  1. CORE PERSONA       — канонические рамки (Hard Sci-Fi/Cyberpunk/Grimdark, fail-forward, 166 фракций)
  2. DIRECTOR'S BLOCK   — ToneProfile.to_director_notes() + речевые теги
  3. KARMIC DICE 1d6    — скрытый бросок, передаваемый в сцену
  4. RESPONSE FORMAT    — 2-3 абзаца → механика → 5-6 опций + свободный ввод
"""
from __future__ import annotations
import random
from typing import Dict, List, Optional

from src.core.tone_model import ToneProfile, EMOTIONAL_DEPTH_TAGS


# Karmic Dice (1d6): скрытый бросок в драматических узлах
# 1-2: тревожная деталь / 3-4: нейтрально / 5-6: неожиданная зацепка или удача
KARMIC_DICE_OUTCOMES = {
    1: "Тревожная деталь: в сцене появляется тонкий намёк на опасность (неясный шёпот, странный запах, мимолётная тень).",
    2: "Тревожная деталь: окружение слегка искажается (мерцание света, эхо из небытия, искажение времени).",
    3: "Нейтрально: сцена развивается без скрытых подсказок.",
    4: "Нейтрально: сцена развивается без скрытых подсказок.",
    5: "Удачная деталь: персонаж замечает полезную мелочь (открытый терминал, забытый предмет, лазейка).",
    6: "Удачная деталь: благоприятное стечение обстоятельств (старый знакомый, неожиданный союзник, шанс на выгоду).",
}


class SystemPromptBuilder:
    """Строит системный промпт для AI-GM на основе ToneProfile и метаданных сцены."""

    def __init__(self, core_persona: Optional[str] = None):
        self.core_persona = core_persona or self._default_core_persona()

    @staticmethod
    def _default_core_persona() -> str:
        return (
            "Ты — AI-игровой мастер (GM) в текстовой киберпанк-песочнице NexusRPG. "
            "Жанр: Hard Sci-Fi / Cyberpunk / Grimdark. Сеттинг 2387, Солнечная система. "
            "Ключевые принципы:\n"
            "1) FAIL-FORWARD: провал на кубиках не блокирует игру, а УСЛОЖНЯЕТ ситуацию. "
            "Персонаж не умирает от неудачи, но получает осложнения (потеря времени, "
            "травма, рост heat, потеря ресурсов, нежелательное внимание).\n"
            "2) КАНОНИЧЕСКИЕ РАМКИ: 166 уникальных фракций, 86 навыков, 5 базовых миров, "
            "31 origin и ~10 специализаций. Не выдумывай NPC или локации вне game_data — "
            "если нужно новое, опирайся на паттерны существующих.\n"
            "3) ЖЁСТКАЯ НАУЧНАЯ ФАНТАСТИКА: технологии подчиняются физике, квантовые эффекты "
            "влияют на психику, киберпсихоз реальна (низкая humanity → риск срыва).\n"
            "4) НЕОПРЕДЕЛЁННОСТЬ: не раскрывай все карты сразу. Оставляй зацепки, "
            "которые игрок может развить или проигнорировать.\n"
            "\n"
            "═══════════════════════════════════════════════════════════════════════\n"
            "ЯЗЫКОВОЙ БАРЬЕР (ЖЁСТКОЕ ПРАВИЛО, Phase 26 fix):\n"
            "═══════════════════════════════════════════════════════════════════════\n"
            "• Весь генерируемый текст — нарратив, описания, диалоги NPC, названия, "
            "варианты действий, речевые теги — ОБЯЗАН быть СТРОГО на русском языке.\n"
            "• ЗАПРЕЩЕНО использовать отдельные английские слова, фразы или "
            "аббревиатуры внутри русских предложений (исключение: ролевые теги "
            "вариантов действий в квадратных скобках [ХАКЕР], [УЛИЦА] и т.п. — "
            "это КИРИЛЛИЧЕСКИЕ теги, не латиница).\n"
            "• ЗАПРЕЩЕНО вставлять конструкции типа «не шагов, a something else», "
            "«let's go», «no way» — если не уверен в русском эквиваленте, "
            "опиши действие русскими словами.\n"
            "• Если в контексте попали английские идентификаторы (например, "
            "технические метки вроде [EN-идентификатор: foo]), НЕ копируй их в "
            "ответ — это служебные метки, а не часть нарратива.\n"
            "• Имена собственные из сеттинга (LunarTech, Protogen, Ceres, Mars) "
            "допустимы БЕЗ перевода, но в окружении русского текста.\n"
            "═══════════════════════════════════════════════════════════════════════\n"
        )

    def build(self, tone_profile: Optional[ToneProfile], scene_meta: Optional[Dict] = None) -> str:
        """Возвращает полный системный промпт для текущей сцены.

        scene_meta: {location, tier, recent_events, karmic_roll}
        """
        parts: List[str] = []

        # 1. CORE PERSONA
        parts.append("=" * 60)
        parts.append("СЕКЦИЯ 1: КАНОНИЧЕСКОЕ ЯДРО")
        parts.append("=" * 60)
        parts.append(self.core_persona)
        parts.append("")

        # 2. DIRECTOR'S BLOCK
        parts.append("=" * 60)
        parts.append("СЕКЦИЯ 2: РЕЖИССЁРСКИЙ БРИФ (тон, голос, атмосфера)")
        parts.append("=" * 60)
        if tone_profile:
            parts.append(tone_profile.to_director_notes())
        else:
            parts.append("(нейтральный тон, generic GM)")

        if scene_meta:
            loc = scene_meta.get("location")
            if loc:
                parts.append("")
                parts.append(f"Текущая сцена: {loc.get('planet', '?')}, {loc.get('city', '?')}, {loc.get('district', '?')}")
            recent = scene_meta.get("recent_events") or []
            if recent:
                parts.append(f"Недавние события: {', '.join(str(e) for e in recent[-3:])}")

        parts.append("")

        # 3. KARMIC DICE
        parts.append("=" * 60)
        parts.append("СЕКЦИЯ 3: СКРЫТЫЕ БРОСКИ (Karmic Dice 1d6)")
        parts.append("=" * 60)
        karmic_roll = (scene_meta or {}).get("karmic_roll")
        if karmic_roll is None:
            karmic_roll = random.randint(1, 6)
        outcome = KARMIC_DICE_OUTCOMES.get(karmic_roll, "")
        parts.append(f"Бросок (1d6): {karmic_roll} → {outcome}")
        parts.append("Используй этот скрытый маркер для тонкой детали в сцене, не объясняя игроку.")
        parts.append("")

        # 4. RESPONSE FORMAT
        parts.append("=" * 60)
        parts.append("СЕКЦИЯ 4: ФОРМАТ ОТВЕТА")
        parts.append("=" * 60)
        parts.append(self._format_instructions(tone_profile))

        return "\n".join(parts)

    def _format_instructions(self, profile: Optional[ToneProfile]) -> str:
        """Инструкции по формату ответа: нарратив → механика → варианты действий.

        Phase 26 fix: формат строго синхронизирован с парсером в static/js/app.js
        (function formatNarrative). Парсер ищет заголовок "Что будешь делать?"
        (или эквивалент: "Выбери действие:", "Доступные действия:") и затем
        нумерованные строки "1. ...", "2. ...", "7. Свой вариант".
        """
        lines = [
            "Структура каждого ответа (СТРОГО в этом порядке):",
            "",
            "1) НАРРАТИВ (2-3 абзаца): описание последствий действия игрока,",
            "   с учётом тона и сенсорной атмосферы из секции 2.",
            "   Минимум 2 органа чувств (зрение + слух ИЛИ обоняние + осязание).",
            "",
            "2) МЕХАНИЧЕСКИЕ ИЗМЕНЕНИЯ — ТОЛЬКО через скрытый [STATE] JSON-блок (см. секцию [STATE] ниже).",
            "   ЗАПРЕЩЕНО выводить в открытом тексте теги вида [HP: ...], [HEAT: ...], [TIME: ...],",
            "   [CREDITS: ...], [STRESS: ...], [HUMANITY: ...] — игрок их видит как мусор.",
            "   Все числовые изменения передавай исключительно внутри [STATE]{...}.",
            "",
            "3) ЗАГОЛОВОК ВЫБОРА — ОБЯЗАТЕЛЬНО одна строка:",
            '   "Что будешь делать?"',
            "   (без вариаций типа «Что будешь делать дальше?» — парсер ищет точную формулировку)",
            "",
            "4) 5-6 ПРОНУМЕРОВАННЫХ ВАРИАНТОВ ДЕЙСТВИЙ:",
            "   СТРОГО в формате: \"<номер>. [<РОЛЕВОЙ_ТЕГ>] <описание>\"",
            "   Примеры:",
            "   1. [ХАКЕР] — использовать терминал для обхода системы",
            "   2. [КОРПОРАТ] — позвонить по связям в элите",
            "   3. [УЛИЦА] — применить грубую силу или угрозу",
            "   4. [ИНТРИГА] — попытаться договориться или обмануть",
            "   5. [АНАЛИТИК] — собрать информацию и оценить ситуацию",
            "   6. [СВОЙ] — описать свой вариант действия",
            "   Ролевые теги ВСЕГДА на русском и В КВАДРАТНЫХ СКОБКАХ.",
            "   После тега — пробел и короткое тире \" — \" перед описанием.",
            "",
            "5) 7-й ВАРИАНТ — СВОБОДНЫЙ ВВОД:",
            "   7. Свой вариант — игрок может описать любое действие",
            "",
            "ВАЖНО: заголовок \"Что будешь делать?\" и нумерованные варианты ДОЛЖНЫ быть",
            "в ответе ВСЕГДА, даже если действие игрока не предполагает выбора",
            "(парсер frontend'а парсит именно этот формат для рендера кнопок).",
            "",
            "ЗАПРЕЩЕНО (Phase 31 H2): НЕ включай в ответ служебные заголовки-названия пунктов",
            "(«1) НАРРАТИВ», «2) МЕХАНИЧЕСКИЕ ИЗМЕНЕНИЯ», «3) ЗАГОЛОВОК ВЫБОРА»,",
            "«4) ПРОНУМЕРОВАННЫХ ВАРИАНТОВ», «5) 7-Й ВАРИАНТ») и их текст-описания.",
            "Это названия секций ИНСТРУКЦИИ, а не шаблон ответа. Ответ = чистый нарратив,",
            "затем строка «Что будешь делать?», затем варианты, затем [STATE]{...}.",
        ]
        if profile and profile.unique_dialogue_tags:
            lines.append("")
            lines.append("Доступные речевые теги для этого персонажа: " + " ".join(profile.unique_dialogue_tags))
        return "\n".join(lines)

    def roll_karmic_dice(self) -> int:
        """Публичный метод для отладки/тестов: бросить кубик."""
        return random.randint(1, 6)

    # ===================== Action-text builders (user message) =====================

    def build_intro_action(self, tone_profile: Optional[ToneProfile], character: Dict, location: Dict, quest_hints: str = "") -> str:
        """Генерирует user-action текст для первой сцены (start_game).

        Это не system_prompt — это action-сообщение, которое отправляется как
        ход игрока. System_prompt собирается отдельно через build().
        """
        char_name = character.get("name", "Безымянный")
        origin_name = character.get("origin_name", "")
        spec_name = character.get("specialization_name", "") or character.get("preset_name", "")
        backstory = character.get("description", "")
        fy_name = character.get("formative_years_name", "")
        credits = character.get("credits", 0)
        influence = character.get("influence", 0)
        equipment = character.get("starting_equipment", []) or []

        # Богатый контекст для AI (Phase 23)
        wealth_hint = (
            f"Статус: очень богат — стартовый капитал ₡{credits:,}. Сцена и окружение должны отражать богатство и статус. "
            if credits >= 100000 else
            (f"Стартовый капитал: ₡{credits:,}. " if credits else "")
        )
        influence_hint = f"Влияние в обществе: {influence}. " if influence else ""
        equip_hint = f"При себе имеет: {', '.join(equipment)}. " if equipment else ""
        fy_hint = f"Годы становления: {fy_name}. " if fy_name else ""

        loc_str = f"{location.get('city', '?')} на планете {location.get('planet', '?')}"
        if location.get("district"):
            loc_str += f", {location['district']}"
        if location.get("place"):
            loc_str += f", {location['place']}"

        # Karmic Dice для первой сцены
        karmic = self.roll_karmic_dice()
        karmic_hint = f"\n[Скрытая подсказка для GM: исход {karmic} — {KARMIC_DICE_OUTCOMES[karmic]}]"

        # Речевая интонация из профиля
        voice_hint = ""
        if tone_profile and tone_profile.dialogue_style:
            voice_hint = f"\n[Голос персонажа в сцене: {tone_profile.dialogue_style}]"

        return (
            f"Начни игру! ПЕРВАЯ сцена. Персонаж {char_name}, "
            f"происхождение: {origin_name}, специализация: {spec_name}. "
            f"{'Предыстория: ' + backstory + '. ' if backstory else ''}"
            f"{fy_hint}{wealth_hint}{influence_hint}{equip_hint}"
            f"Прибыл в {loc_str}. "
            f"{quest_hints}"
            f"Опиши атмосферное начало. Представь окружение, намекни на возможные приключения и контакты. "
            f"В конце ОБЯЗАТЕЛЬНО: строка 'Что будешь делать?' и ровно 6 пронумерованных вариантов "
            f"('1. [ТЕГ] описание' … '6. [ТЕГ] описание') + '7. Свой вариант'. "
            f"НЕ размещай [STATE]-блок между заголовком выбора и вариантами — только в самом конце ответа."
            f"{voice_hint}{karmic_hint}"
        )

    def build_action_meta(self, action: str, dice_result: Optional[Dict] = None, mechanical_changes: Optional[str] = None) -> Dict:
        """Собирает scene_meta для action-промпта на основе текущего действия.

        Возвращает dict, который можно передать в build() для system_prompt.
        """
        return {
            "current_action": action,
            "dice_result": dice_result,
            "mechanical_changes": mechanical_changes,
            "karmic_roll": self.roll_karmic_dice(),
        }


# === Фабрика для удобного вызова ===
def build_system_prompt(
    tone_profile: Optional[ToneProfile],
    scene_meta: Optional[Dict] = None,
    core_persona: Optional[str] = None,
) -> str:
    """Короткая обёртка: создаёт SystemPromptBuilder и возвращает промпт."""
    return SystemPromptBuilder(core_persona=core_persona).build(tone_profile, scene_meta)
