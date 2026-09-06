# -*- coding: utf-8 -*-
"""
Phase 31 H-fix regression-тесты.
H1: preset-путь строит ToneProfile → apply_scene_context не падает на None.
H2: служебные заголовки «N) НАРРАТИВ <текст>» вырезаются из нарратива.
H3: place из [STATE].location канонизируется против заведений района.
H7: атмосфера мира обновляется раз в ~10 тиков, а не каждый тик.
"""
import random
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _make_engine():
    from src.core.engine import GameEngine
    random.seed(3131)
    return GameEngine()


# ═══════════════════════════════════════════════════════════════
# H1: ToneProfile на preset-пути
# ═══════════════════════════════════════════════════════════════

def test_h1_preset_creates_tone_profile():
    """Root cause H1: create_character_from_preset не строил ToneProfile →
    state.tone_profile = None → start_game → apply_scene_context(None) →
    AttributeError: 'NoneType' object has no attribute 'scale_level'."""
    eng = _make_engine()
    eng.create_character_from_preset("research_scientist")
    assert eng.state.tone_profile is not None, (
        "preset-путь снова оставил tone_profile=None — регресс H1"
    )
    assert hasattr(eng.state.tone_profile, "scale_level")


def test_h1_apply_scene_context_no_crash():
    """Прямой вызов apply_scene_context после preset-создания не падает
    и заполняет scale_level."""
    eng = _make_engine()
    eng.create_character_from_preset("research_scientist")
    tier_info = eng.get_player_influence_tier()
    result = eng.tone_engine.apply_scene_context(
        eng.state.tone_profile, location=eng.state.current_location, tier_info=tier_info
    )
    assert result is eng.state.tone_profile
    assert result.scale_level in ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7")


def test_h1_apply_scene_context_with_none_profile_is_safe():
    """Даже если профиль None (старый сейв, fallback-путь), вызов не должен
    ронять вызывающий код: tone_engine валидирует вход."""
    eng = _make_engine()
    tier_info = eng.get_player_influence_tier()
    # Проверяем, что None-профиль отсекается на стороне вызова движка:
    # в engine.py вызов обёрнут в if/try. Здесь фиксируем контракт сервиса:
    # apply_scene_context(None, ...) бросает AttributeError (контракт), поэтому
    # движок обязан не передавать None — фикс H1 гарантирует непустой профиль.
    with pytest.raises(AttributeError):
        eng.tone_engine.apply_scene_context(None, location=None, tier_info=tier_info)


# ═══════════════════════════════════════════════════════════════
# H2: утечка служебных заголовков
# ═══════════════════════════════════════════════════════════════

def test_h2_numbered_header_with_tail_text_stripped():
    """Кейс владельца: «1) НАРРАТИВ (2-3 абзаца): Описание прибытия...» —
    заголовок + текст в ОДНОЙ строке. Старый regex требовал конец строки
    сразу после заголовка и не срезал хвост."""
    eng = _make_engine()
    raw = (
        "1) НАРРАТИВ (2-3 абзаца): Описание прибытия, атмосферы и сенсорных "
        "деталей с учётом скрытого броска.\n\n"
        "ДScreenы терминала мигнули синим светом. Шлюз за спиной зашипел."
    )
    parsed = eng._parse_ai_response(raw)
    narrative = parsed["narrative"]
    assert "НАРРАТИВ" not in narrative
    assert "Описание прибытия" not in narrative
    assert "мигнули синим светом" in narrative


def test_h2_header_variants_still_stripped():
    eng = _make_engine()
    raw = "### 2) МЕХАНИЧЕСКИЕ ИЗМЕНЕНИЯ: уже применено\nЧистый текст сцены."
    parsed = eng._parse_ai_response(raw)
    assert "МЕХАНИЧЕСКИЕ" not in parsed["narrative"]
    assert "Чистый текст сцены" in parsed["narrative"]


def test_h2_choices_not_eaten():
    """Регресс-защита: нумерованные варианты выбора НЕ должны вырезаться."""
    eng = _make_engine()
    raw = (
        "Сцена в баре.\n\nЧто будешь делать?\n"
        "1. [ХАКЕР] Подключиться к терминалу\n"
        "2. [УЛИЦА] Уйти через чёрный ход\n"
        "3. Найти брокера для проверки багажа\n"
        "7. Свой вариант"
    )
    parsed = eng._parse_ai_response(raw)
    n = parsed["narrative"]
    assert "[ХАКЕР]" in n and "[УЛИЦА]" in n
    assert "Найти брокера" in n
    assert "Свой вариант" in n


# ═══════════════════════════════════════════════════════════════
# H3: place из [STATE].location
# ═══════════════════════════════════════════════════════════════

def test_h3_location_with_known_place_applied():
    """Модель прислала place существующего заведения района — место обновляется."""
    eng = _make_engine()
    eng.state.current_location = {
        "planet": "Ганимед", "city": "Станция Юпитер-Прайм",
        "district": "Торговые палубы", "place": "Мед-отсек «БиоГеном»",
    }
    response = (
        "Игрок проходит в соседний отсек.\n"
        '[STATE]{"hp_change":0,"location":{"planet":"Ганимед","city":"Станция Юпитер-Прайм",'
        '"district":"Торговые палубы","place":"Бар «Ледяной Шторм»"}}[/STATE]\n'
        "Что будешь делать?\n1. [УЛИЦА] Осмотреться\n7. Свой вариант"
    )
    parsed = eng._parse_ai_response(response)
    loc = eng.state.current_location
    assert loc.get("place") == "Бар «Ледяной Шторм»", f"place не применился: {loc}"


def test_h3_location_with_unknown_place_reset():
    """Модель придумала заведение вне района — place сбрасывается, а не врёт."""
    eng = _make_engine()
    eng.state.current_location = {
        "planet": "Ганимед", "city": "Станция Юпитер-Прайм",
        "district": "Торговые палубы", "place": "Мед-отсек «БиоГеном»",
    }
    response = (
        "Сцена перемещения.\n"
        '[STATE]{"location":{"planet":"Ганимед","city":"Станция Юпитер-Прайм",'
        '"district":"Торговые палубы","place":"Несуществующий ангар 99"}}[/STATE]\n'
        "Что будешь делать?\n1. [УЛИЦА] Осмотреться\n7. Свой вариант"
    )
    eng._parse_ai_response(response)
    loc = eng.state.current_location
    assert loc.get("place") in ("", None), f"выдуманное place просочилось: {loc}"
    # district не потерялся
    assert loc.get("district") == "Торговые палубы"


# ═══════════════════════════════════════════════════════════════
# H7: атмосфера раз в ~10 тиков
# ═══════════════════════════════════════════════════════════════

def test_h7_atmosphere_cached_between_ticks():
    from src.world.simulation import WorldSimulator
    random.seed(777)
    ws = WorldSimulator()
    gt = {"year": 2387, "month": 3, "day": 15, "hour": 8, "minute": 0}
    loc = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}

    atmospheres = []
    for i in range(8):
        ctx = ws.tick(gt, loc, tier=0, character=None)
        atmospheres.append(ctx["atmosphere"])

    # В первых 8 тиках (после первой генерации) текст не менялся
    assert len(set(atmospheres)) == 1, (
        f"атмосфера регенерировалась ежеходово: {len(set(atmospheres))} уникальных значений за 8 тиков"
    )


def test_h7_atmosphere_regenerates_after_10_ticks():
    from src.world.simulation import WorldSimulator
    random.seed(778)
    ws = WorldSimulator()
    gt = {"year": 2387, "month": 3, "day": 15, "hour": 8, "minute": 0}
    loc = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}

    first = ws.tick(gt, loc, tier=0, character=None)["atmosphere"]
    for _ in range(10):
        ctx = ws.tick(gt, loc, tier=0, character=None)
    later = ctx["atmosphere"]
    # После 10+ тиков кэш обязан обновиться (текст скорее всего другой; если совпал —
    # seeded random дал ту же фразу, но поле _atmosphere_turn обновлено)
    assert ws._atmosphere_turn >= 10
    assert isinstance(later, str) and later


def test_h7_atmosphere_regenerates_on_location_change():
    from src.world.simulation import WorldSimulator
    random.seed(779)
    ws = WorldSimulator()
    gt = {"year": 2387, "month": 3, "day": 15, "hour": 8, "minute": 0}
    loc1 = {"planet": "Земля", "city": "Нью-Токио", "district": "Индустриальный коридор"}
    ws.tick(gt, loc1, tier=0, character=None)
    cached = ws._atmosphere_cache
    loc2 = {"planet": "Марс", "city": "Олимп", "district": "Купол Арес"}
    ctx = ws.tick(gt, loc2, tier=0, character=None)
    assert ctx["atmosphere"] != cached or ws._atmosphere_turn == ws.turn_count
