"""
tests/test_integration_acceptance.py — Phase 2.1: интеграционные тесты приёмки.

Проверяют реальное подключение ToneEngine + SystemPromptBuilder к engine:
- start_game вызывает prompt_builder.build_intro_action()
- process_player_action вызывает prompt_builder.build() с Director's Notes
- Karmic Dice маркер присутствует в промпте
- tone_profile сериализуется 1:1 через save/load
- /api/action эндпоинт возвращает 200 (с моком LLM)

LLM замокирован через monkeypatch — тесты проверяют ИНТЕГРАЦИЮ, не качество LLM.
"""
import json
import os
import time
import socket
import threading
import urllib.request
import urllib.error
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure src importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _free_port() -> int:
    """Возвращает свободный TCP-порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_port(host: str, port: int, timeout_s: float = 10.0) -> bool:
    """Поллинг порта до готовности или таймаута."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


@pytest.fixture
def fresh_engine():
    """Создаёт свежий GameEngine с минимальным персонажем L1."""
    from src.core.engine import GameEngine
    engine = GameEngine()
    engine.create_custom_character({
        "name": "TestHero",
        "origin": "ORIGIN_EARTH_TECH_MOGUL",
        "formative_years": "FY_CORP_INTERNSHIP",
        "specialization": "SPEC_CORPORATE_ASSASSIN",
        "age": 30,
    })
    # start_game требует ai.generate — замокируем
    return engine


@pytest.fixture
def mock_ai(fresh_engine, monkeypatch):
    """Мок AI-коннектора: возвращает фиктивный narrative без сетевых вызовов.

    Мокаем НА ИНСТАНСЕ engine.ai, чтобы избежать конфликта self-bounding
    при monkeypatch на уровне класса AIConnector.
    """
    def fake_generate(system_prompt=None, messages=None, temperature=None, max_tokens=None, **kwargs):
        return "NARRATIVE: Тестовый ответ от мока.\nOPTIONS:\n1. [Бой] Драться\n2. [Скрытность] Спрятаться"

    def fake_stream(*args, **kwargs):
        yield "data: stub"

    # Mock on instance (bypasses self auto-bounding)
    monkeypatch.setattr(fresh_engine.ai, "generate", fake_generate)
    if hasattr(fresh_engine.ai, "generate_stream"):
        monkeypatch.setattr(fresh_engine.ai, "generate_stream", fake_stream)
    return fake_generate


# ========== Test 1: start_game вызывает prompt_builder.build_intro_action ==========

def test_start_game_uses_prompt_builder(fresh_engine, mock_ai, monkeypatch):
    """Phase 2.1: start_game должен вызвать prompt_builder.build_intro_action.

    Мы monkeypatch'им build_intro_action и проверяем, что он был вызван
    с правильным character + location. После вызова start_game мы
    вызываем self.process_player_action с фиктивным intro_prompt, чтобы
    пройти весь pipeline без падения на LLM (mock_ai).
    """
    from src.core.tone_model import ToneProfile

    # Замокируем process_player_action, чтобы не вызывать AI на фиктивном prompt
    called_with = {}

    def fake_process(action_text):
        called_with["action"] = action_text
        return {"narrative": "mocked", "options": []}

    monkeypatch.setattr(fresh_engine, "process_player_action", fake_process)

    # Замокируем build_intro_action чтобы поймать аргументы
    captured = {}

    def fake_build_intro(tone_profile, character, location, quest_hints=""):
        captured["tone_profile"] = tone_profile
        captured["character"] = character
        captured["location"] = location
        captured["quest_hints"] = quest_hints
        return "FAKE_INTRO_PROMPT"

    monkeypatch.setattr(fresh_engine.prompt_builder, "build_intro_action", fake_build_intro)

    # Запускаем start_game (tone_profile уже должен быть в state)
    result = fresh_engine.start_game("TestHero")

    # Проверяем что build_intro_action был вызван
    assert "tone_profile" in captured, "prompt_builder.build_intro_action не вызван"
    assert captured["character"]["name"] == "TestHero"
    assert captured["character"]["origin"] == "ORIGIN_EARTH_TECH_MOGUL"
    assert isinstance(captured["location"], dict)
    assert "planet" in captured["location"]

    # Проверяем что tone_profile передан (Phase 2.1 critical)
    tp = captured["tone_profile"]
    assert isinstance(tp, ToneProfile), f"tone_profile не передан, тип={type(tp)}"
    assert tp.primary_genre == "technological_singularity"

    # Проверяем что process_player_action вызван с результатом build_intro
    assert "FAKE_INTRO_PROMPT" in called_with["action"]


# ========== Test 2: process_player_action формирует промпт с Director's Notes ==========

def test_action_prompt_contains_director_notes(fresh_engine, mock_ai, monkeypatch):
    """Phase 2.1 + микрошаг 2a: system_prompt, формируемый в process_player_action,
    должен содержать Director's Notes из tone_profile. С 2a промпт собирает
    SystemPromptService, читая state.tone_profile напрямую (механизм тот же)."""
    # tone_profile обязан существовать до хода
    tp = fresh_engine.state.tone_profile
    assert tp is not None, "state.tone_profile is None — Director's Notes не из чего собрать"
    assert hasattr(tp, "to_director_notes"), "tone_profile не имеет to_director_notes"

    director_notes = tp.to_director_notes()
    assert len(director_notes) > 0, "Director's Notes пусты"
    assert "ТОНАЛЬНОСТЬ ПЕРСОНАЖА" in director_notes
    assert "Жанровый бленд" in director_notes

    # Захват финального system_prompt через AI-коннектор (единая точка для обоих режимов)
    captured_prompt = {}

    real_generate = fresh_engine.ai.generate

    def capture_ai(system_prompt=None, messages=None, **kwargs):
        captured_prompt["system_prompt"] = system_prompt
        return "NARRATIVE: ok\nOPTIONS:\n1. action"

    monkeypatch.setattr(fresh_engine.ai, "generate", capture_ai)
    fresh_engine.process_player_action("тестовое действие")

    sp = captured_prompt.get("system_prompt", "")
    # Director's Notes дошли до финального промпта (через SystemPromptService)
    assert "РЕЖИССЁРСКИЙ БРИФ" in sp, "Director's Notes-секция отсутствует в финальном промпте"
    assert "ТОНАЛЬНОСТЬ ПЕРСОНАЖА" in sp, "тоны не дошли до финального промпта"
    assert "Жанровый бленд" in sp

    # scene_meta (build_action_meta) по-прежнему готовит karmic_roll
    sm = fresh_engine.prompt_builder.build_action_meta("тестовое действие")
    assert "karmic_roll" in sm, "scene_meta не содержит karmic_roll"
    assert 1 <= sm["karmic_roll"] <= 6, f"karmic_roll вне диапазона 1-6: {sm['karmic_roll']}"
    assert sm.get("current_action") == "тестовое действие"


# ========== Test 3: Karmic Dice маркер в промпте ==========

def test_karmic_dice_in_prompt(fresh_engine, mock_ai, monkeypatch):
    """Phase 2.1: скрытый бросок 1d6 оставляет маркер в system_prompt."""
    # Захватываем system_prompt, который ушёл бы в LLM
    captured_prompt = {}

    real_ai_generate = fresh_engine.ai.generate

    def capture_ai(system_prompt=None, messages=None, **kwargs):
        captured_prompt["system_prompt"] = system_prompt
        return "NARRATIVE: ok\nOPTIONS:\n1. action"

    monkeypatch.setattr(fresh_engine.ai, "generate", capture_ai)

    # Запускаем action (real flow)
    fresh_engine.process_player_action("осмотреться")

    # Проверяем что в system_prompt есть секция Karmic Dice
    sp = captured_prompt.get("system_prompt", "")
    assert "Karmic Dice" in sp, f"В промпте нет секции Karmic Dice:\n{sp[:500]}"
    assert "Бросок (1d6):" in sp, "Нет маркера броска 1d6"
    # Маркер содержит число от 1 до 6
    import re
    m = re.search(r"Бросок \(1d6\): (\d+)", sp)
    assert m, "Не найден результат броска"
    roll = int(m.group(1))
    assert 1 <= roll <= 6, f"karmic_roll вне диапазона: {roll}"
    # Маркер описывает исход
    assert "Тревожная" in sp or "Нейтрально" in sp or "Удачная" in sp, "Нет описания исхода"


# ========== Test 4: tone_profile save/load roundtrip ==========

def test_tone_profile_save_load_roundtrip(fresh_engine):
    """Phase 2.1: сохранение и загрузка восстанавливают tone_profile 1:1."""
    from src.core.engine import GameEngine

    # 1. Установить tone_profile через build_character_tone
    original_profile = fresh_engine.tone_engine.build_character_tone(fresh_engine.state.character)
    fresh_engine.state.tone_profile = original_profile

    # 2. Save
    slot = "test_tone_roundtrip"
    save_result = fresh_engine.save_game(slot)
    assert save_result["success"], f"save_game failed: {save_result}"

    try:
        # 3. Загрузить в новый engine
        new_engine = GameEngine()
        load_result = new_engine.load_game(slot)
        assert load_result.get("success"), f"load_game failed: {load_result}"

        # 4. Сравнить все 15 полей
        assert new_engine.state.tone_profile is not None, "tone_profile не загружен"
        loaded = new_engine.state.tone_profile
        orig_dict = original_profile.to_dict()
        loaded_dict = loaded.to_dict()
        assert orig_dict == loaded_dict, (
            f"tone_profile не 1:1.\nORIG: {orig_dict}\nLOADED: {loaded_dict}"
        )
    finally:
        # cleanup
        try:
            fresh_engine.delete_save(slot)
        except Exception:
            pass


# ========== Test 6: scene_context updates on movement ==========

def test_scene_context_updates_on_movement(fresh_engine, mock_ai):
    """Phase 3 Blocker: при смене локации (move) mood_descriptors в
    tone_profile должны обновляться, соответствовать новой точке.

    Проверяется реальный pipeline: state.current_location изменяется,
    вызывается _apply_tone_to_current_location(), mood_descriptors
    обновляются (lighting/scent/audio отличаются для разных районов).
    """
    # 1. Убеждаемся, что tone_profile собран
    assert fresh_engine.state.tone_profile is not None, "tone_profile должен быть после create_custom_character"
    profile = fresh_engine.state.tone_profile

    # 2. Применяем scene_context для стартовой локации (Корпоративный центр на Земле)
    fresh_engine.state.current_location = {
        "planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр", "place": ""
    }
    fresh_engine._apply_tone_to_current_location()
    initial_mood = dict(profile.mood_descriptors)
    initial_lighting = initial_mood.get("lighting", "")
    assert initial_lighting, "После apply_scene_context lighting должен быть заполнен"
    assert "холодный" in initial_lighting.lower() or "LED" in initial_lighting, \
        f"Корпоративный центр → должен быть холодный LED/бетон, получено: {initial_lighting!r}"

    # 3. Перемещаемся в Шахтёрский уровень (Церера) — должен быть другой mood
    fresh_engine.state.current_location = {
        "planet": "Церера", "city": "Станция Бельт-7", "district": "Шахтёрский уровень", "place": ""
    }
    fresh_engine._apply_tone_to_current_location()
    new_mood = dict(profile.mood_descriptors)
    new_scent = new_mood.get("scent", "")
    new_audio = new_mood.get("audio", "")

    # 4. Asserts: mood_descriptors изменились
    assert new_scent, "После перемещения scent должен быть заполнен"
    assert new_audio, "После перемещения audio должен быть заполнен"
    # Шахты → металл/масло/буры
    assert "металл" in new_scent.lower() or "смазк" in new_scent.lower(), \
        f"Шахтёрский уровень → должен быть металл/смазки, получено: {new_scent!r}"
    assert "бур" in new_audio.lower() or "скрежет" in new_audio.lower(), \
        f"Шахтёрский уровень → должен быть работа буров/скрежет, получено: {new_audio!r}"

    # 5. Mood_descriptors реально изменились между двумя точками
    assert initial_mood != new_mood, "mood_descriptors не изменился после перемещения"
    # Конкретные поля различаются
    assert initial_mood.get("scent") != new_mood.get("scent"), "scent не изменился"
    assert initial_mood.get("audio") != new_mood.get("audio"), "audio не изменился"

    # 6. Прямой вызов _apply_tone_to_current_location через API-путь (process_movement)
    #    перемещаемся обратно в Корпоративный центр — mood должен вернуться
    fresh_engine.state.current_location = {
        "planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр", "place": ""
    }
    fresh_engine._apply_tone_to_current_location()
    third_mood = dict(profile.mood_descriptors)
    # Возврат к corporate → scent должен быть снова "стерильный воздух"
    assert "стерильн" in third_mood.get("scent", "").lower() or "озон" in third_mood.get("scent", "").lower(), \
        f"Возврат в corporate → должен быть стерильный/озон, получено: {third_mood.get('scent')!r}"


# ========== Test 5: end-to-end /api/action ==========

def test_api_action_end_to_end(fresh_engine, mock_ai, monkeypatch):
    """Phase 2.1: POST /api/action → 200 через app.test_client() (без subprocess).

    Используем Flask test_client для устранения flaky-теста с занятыми портами.
    В engine уже мокнут AI через фикстуру mock_ai, поэтому ответ приходит
    сразу (без реального ollama-вызова).
    """
    from src.server.app import app

    # Подключаем наш engine (с тон-профилем и мокнутым AI) к Flask blueprints
    app.engine = fresh_engine
    client = app.test_client()

    # Создаём персонажа
    create_resp = client.post(
        "/api/character/create",
        json={
            "name": "E2EHero",
            "origin": "ORIGIN_EARTH_SLUMS",
            "formative_years": "FY_SLUMS_GANGWAR",
            "specialization": "SPEC_CQB_MASTER",
            "age": 22,
        },
    )
    assert create_resp.status_code == 200, (
        f"POST /api/character/create вернул {create_resp.status_code}: {create_resp.data[:200]}"
    )
    created = create_resp.get_json()
    assert "name" in created, f"В ответе нет name: {list(created.keys()) if created else None}"

    # POST /api/action — через мок AI вернётся stub-narrative
    action_resp = client.post(
        "/api/action",
        json={"action": "осмотреть окрестности"},
    )
    assert action_resp.status_code == 200, (
        f"POST /api/action вернул {action_resp.status_code}: {action_resp.data[:200]}"
    )
    result = action_resp.get_json()
    assert result is not None, "Ответ не является валидным JSON"
    # Структура ответа: narrative + options
    assert "narrative" in result or "error" not in result, f"Action error: {result}"
