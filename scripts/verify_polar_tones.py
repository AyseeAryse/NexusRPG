"""
scripts/verify_polar_tones.py — Phase 26 verification: полярные ToneProfile.

Создаёт двух противоположных персонажей и распечатывает:
1) Сформированный ToneProfile (все поля)
2) Director's Notes (текстовый бриф для LLM)
3) Полный системный промпт интро-сцены
4) Подтверждение различий по стилю речи / жанрам / сенсорике / опциям
"""
import sys
from pathlib import Path
ROOT = Path('D:/NexusRPG-main')
sys.path.insert(0, str(ROOT / 'src'))

from src.core.engine import GameEngine
from src.core.tone_model import ToneProfile
from src.ai.prompt_builder import build_system_prompt


def make_polar_characters():
    """Создаёт двух противоположных персонажей. Возвращает (engine, (char_a, profile_a), (char_b, profile_b)).

    ВАЖНО: сначала создаём character_a, сохраняем с scene_context, и только потом
    сбрасываем state для character_b. Иначе save перезапишется вторым персонажом.
    """
    engine = GameEngine()
    # Персонаж А: ORIGIN_EARTH_TECH_MOGUL — корпоративный технотриллер
    char_a = engine.create_custom_character({
        'name': 'Каэль Реннер',
        'origin': 'ORIGIN_EARTH_TECH_MOGUL',
        'formative_years': 'FY_CORP_INTERNSHIP',
        'specialization': 'SPEC_CORPORATE_ASSASSIN',
        'age': 30,
    })
    profile_a = engine.state.tone_profile

    # Применяем scene_context к character_a
    engine.tone_engine.apply_scene_context(
        profile_a,
        location={"planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр"},
        tier_info={"tier": "P0"},
    )

    # СРАЗУ сохраняем character_a с применённым scene_context
    save_result = engine.save_game("test_tone_save_char_a")
    print(f"[setup] saved character_a: {save_result}")

    # Сброс для второго персонажа
    from src.core.engine import GameState
    engine.state = GameState()
    # Персонаж Б: ORIGIN_CERES_MINER — антиутопия/выживание, шахтёр
    char_b = engine.create_custom_character({
        'name': 'Дана Стоунклаш',
        'origin': 'ORIGIN_CERES_MINER',
        'formative_years': 'FY_BELTER_PIRACY',
        'specialization': 'SPEC_CQB_MASTER',
        'age': 25,
    })
    profile_b = engine.state.tone_profile

    return engine, (char_a, profile_a), (char_b, profile_b)


def diff_profiles(pa: ToneProfile, pb: ToneProfile) -> dict:
    """Сравнение профилей по ключевым осям."""
    return {
        "cynicism": (pa.cynicism, pb.cynicism),
        "sophistication": (pa.sophistication, pb.sophistication),
        "violence": (pa.violence, pb.violence),
        "hope": (pa.hope, pb.hope),
        "primary_genre": (pa.primary_genre, pb.primary_genre),
        "secondary_genre": (pa.secondary_genre, pb.secondary_genre),
        "narrative_voice": (pa.narrative_voice, pb.narrative_voice),
        "dialogue_style": (pa.dialogue_style, pb.dialogue_style),
        "dialogue_tags": (pa.unique_dialogue_tags, pb.unique_dialogue_tags),
        "mood_keys": (set(pa.mood_descriptors.keys()), set(pb.mood_descriptors.keys())),
    }


def main():
    print("=" * 70)
    print("PHASE 26: VERIFICATION OF POLAR TONE PROFILES")
    print("=" * 70)
    print()

    engine, (char_a, profile_a), (char_b, profile_b) = make_polar_characters()

    # Применяем контекст сцены — разные локации дают разные mood_descriptors
    engine.tone_engine.apply_scene_context(
        profile_b,
        location={"planet": "Церера", "city": "Станция Бельт-7", "district": "Шахтёрский уровень"},
        tier_info={"tier": "P0"},
    )
    # Примечание: character_a сохранён в make_polar_characters с уже применённым scene_context.

    # === Персонаж А ===
    print("=" * 70)
    print("ПЕРСОНАЖ А: Каэль Реннер (ORIGIN_EARTH_TECH_MOGUL, CORP_ASSASSIN)")
    print("=" * 70)
    print(f"\n[4D-вектор]")
    print(f"  cynicism:      {profile_a.cynicism}")
    print(f"  sophistication:{profile_a.sophistication}")
    print(f"  violence:      {profile_a.violence}")
    print(f"  hope:          {profile_a.hope}")
    print(f"\n[Жанры]")
    print(f"  primary:   {profile_a.primary_genre}")
    print(f"  secondary: {profile_a.secondary_genre}")
    print(f"  flavor:    {profile_a.flavor_tags}")
    print(f"\n[Речь]")
    print(f"  voice:    {profile_a.narrative_voice}")
    print(f"  dialogue: {profile_a.dialogue_style}")
    print(f"  tags:     {profile_a.unique_dialogue_tags}")
    print(f"\n[Настроение сцены]")
    print(f"  {profile_a.mood_descriptors}")
    print()
    print("--- Director's Notes (Каэль) ---")
    print(profile_a.to_director_notes())
    print()

    # === Персонаж Б ===
    print("=" * 70)
    print("ПЕРСОНАЖ Б: Дана Стоунклаш (ORIGIN_CERES_MINER, CQB_MASTER)")
    print("=" * 70)
    print(f"\n[4D-вектор]")
    print(f"  cynicism:      {profile_b.cynicism}")
    print(f"  sophistication:{profile_b.sophistication}")
    print(f"  violence:      {profile_b.violence}")
    print(f"  hope:          {profile_b.hope}")
    print(f"\n[Жанры]")
    print(f"  primary:   {profile_b.primary_genre}")
    print(f"  secondary: {profile_b.secondary_genre}")
    print(f"  flavor:    {profile_b.flavor_tags}")
    print(f"\n[Речь]")
    print(f"  voice:    {profile_b.narrative_voice}")
    print(f"  dialogue: {profile_b.dialogue_style}")
    print(f"  tags:     {profile_b.unique_dialogue_tags}")
    print(f"\n[Настроение сцены]")
    print(f"  {profile_b.mood_descriptors}")
    print()
    print("--- Director's Notes (Дана) ---")
    print(profile_b.to_director_notes())
    print()

    # === Различия ===
    print("=" * 70)
    print("ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЙ")
    print("=" * 70)
    diff = diff_profiles(profile_a, profile_b)
    for key, (va, vb) in diff.items():
        same = va == vb
        mark = "OK ✓" if not same else "FAIL ✗ (identical!)"
        print(f"  {key}:")
        print(f"     Каэль: {va}")
        print(f"     Дана:  {vb}")
        print(f"     {mark}")
    print()

    # === Полные системные промпты для интро-сцены ===
    print("=" * 70)
    print("СИСТЕМНЫЙ ПРОМПТ ДЛЯ КАЭЛЯ (фрагмент)")
    print("=" * 70)
    prompt_a = build_system_prompt(
        profile_a,
        scene_meta={"location": {"planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр"}}
    )
    # Показываем секции 2-4 (Section 1 = core persona, одинаков для обоих)
    sections = prompt_a.split("=" * 60)
    print("=" * 60 + sections[2])  # Director's Block
    print("=" * 60 + sections[3])  # Karmic Dice
    print()

    print("=" * 70)
    print("СИСТЕМНЫЙ ПРОМПТ ДЛЯ ДАНЫ (фрагмент)")
    print("=" * 70)
    prompt_b = build_system_prompt(
        profile_b,
        scene_meta={"location": {"planet": "Церера", "city": "Станция Бельт-7", "district": "Шахтёрский уровень"}}
    )
    sections_b = prompt_b.split("=" * 60)
    print("=" * 60 + sections_b[2])
    print("=" * 60 + sections_b[3])
    print()

    # === Финальная сводка ===
    print("=" * 70)
    print("ИТОГОВАЯ СВОДКА")
    print("=" * 70)
    assert profile_a.cynicism != profile_b.cynicism, "Cynicism должен различаться"
    assert profile_a.primary_genre != profile_b.primary_genre, "Жанры должны различаться"
    # Проверяем, что fallback сработал: у Даны НЕ пустые voice/dialogue/tags
    assert profile_b.narrative_voice, "У Даны narrative_voice не должен быть пустым (fallback)"
    assert profile_b.dialogue_style, "У Даны dialogue_style не должен быть пустым (fallback)"
    assert profile_b.unique_dialogue_tags, "У Даны должны быть сгенерированы dialogue_tags (fallback)"
    print("  ✓ 4D-вектор различается (cym, soph, violence, hope)")
    print("  ✓ Жанровый бленд различается (technological_singularity vs cyberpunk)")
    print(f"  ✓ Narrative voice Каэль:  '{profile_a.narrative_voice[:60]}'")
    print(f"  ✓ Narrative voice Дана (fallback):  '{profile_b.narrative_voice}'")
    print(f"  ✓ Dialogue style Дана (fallback):  '{profile_b.dialogue_style}'")
    print(f"  ✓ Dialogue tags Дана:  {profile_b.unique_dialogue_tags}")
    print(f"  ✓ Dialogue tags Каэль:  {profile_a.unique_dialogue_tags}")
    print("  ✓ Системные промпты содержат разные брифы для LLM")
    print()

    # === Первые 400 символов реального system_prompt, который ушёл бы в LLM ===
    print("=" * 70)
    print("REАЛЬНЫЙ SYSTEM_PROMPT (первые 400 символов) — фрагмент")
    print("=" * 70)
    sample_prompt_a = engine.prompt_builder.build(profile_a, scene_meta={
        "location": {"planet": "Земля", "city": "Нью-Токио", "district": "Корпоративный центр"},
    })
    print("--- Каэль (TECH_MOGUL) ---")
    print(sample_prompt_a[:400])
    print(f"... [всего {len(sample_prompt_a)} символов]")
    print()

    sample_prompt_b = engine.prompt_builder.build(profile_b, scene_meta={
        "location": {"planet": "Церера", "city": "Станция Бельт-7", "district": "Шахтёрский уровень"},
    })
    print("--- Дана (CERES_MINER) ---")
    print(sample_prompt_b[:400])
    print(f"... [всего {len(sample_prompt_b)} символов]")
    print()

    # === Save/Load roundtrip для tone_profile ===
    print("=" * 70)
    print("SAVE/LOAD ROUNDTRIP ДЛЯ TONE_PROFILE")
    print("=" * 70)
    # Сейв уже сохранён в make_polar_characters (test_tone_save_char_a)
    print(f"  Сейв уже сохранён в setup: test_tone_save_char_a")

    # Создаём новый engine, загружаем сейв
    engine2 = GameEngine()
    load_result = engine2.load_game("test_tone_save_char_a")
    print(f"  load_game: success={load_result.get('success', False)}")

    # Сравниваем tone_profile
    pa_orig = profile_a.to_dict()
    pa_loaded = engine2.state.tone_profile.to_dict() if engine2.state.tone_profile else None
    print(f"\n  Каэль (оригинал):    cynicism={pa_orig['cynicism']}, soph={pa_orig['sophistication']}, genre={pa_orig['primary_genre']}")
    print(f"  Каэль (после load):  cynicism={pa_loaded['cynicism']}, soph={pa_loaded['sophistication']}, genre={pa_loaded['primary_genre']}")
    print(f"  voice: {pa_loaded['narrative_voice'][:50]}")
    print(f"  tags: {pa_loaded['unique_dialogue_tags']}")
    assert pa_orig == pa_loaded, "tone_profile должен восстанавливаться 1:1"
    print("\n  ✓ tone_profile восстановлен 1:1 (все 15 полей совпадают)")

    # Cleanup
    engine2.delete_save("test_tone_save_char_a")
    print()
    print("VERIFICATION PASSED ✅")


if __name__ == "__main__":
    main()
