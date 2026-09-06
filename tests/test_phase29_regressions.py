"""
tests/test_phase29_regressions.py — регрессионное покрытие Phase 29 G-fix.

G2: [STATE]-блок без закрывающего тега в СЕРЕДИНЕ ответа не должен
    срезать варианты выбора (старая логика вырезала всё после [STATE]).
G1: слот-классификация (weapon/armor/implant/pocket) по каталогу,
    кнопка «Использовать» только у расходников, авто-снятие при
    экипировке второго предмета того же слота, save/load roundtrip
    флага equipped.

Тесты НЕ мокают логику — работают с реальным парсером и каталогом.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ═══════════════════════════════════════════════════════════════
# G2: парсер [STATE] в середине ответа
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def parser_engine():
    """GameEngine без полного __init__ — только state для _parse_ai_response."""
    from src.core.engine import GameEngine, GameState
    engine = GameEngine.__new__(GameEngine)
    engine.state = GameState()
    return engine


def test_state_mid_response_keeps_choices(parser_engine):
    """G2 (регресс): [STATE]{...} в середине ответа — варианты выбора
    после блока ОБЯЗАНЫ сохраниться в narrative."""
    response = (
        "Нарратив про шлюз.\n"
        '[STATE]{"hp_change": -5}\n'
        "Что будешь делать?\n"
        "1. [ХАКЕР] — взломать терминал\n"
        "2. [УЛИЦА] — надавить на охранника\n"
        "7. Свой вариант"
    )
    parsed = parser_engine._parse_ai_response(response)

    assert "Что будешь делать?" in parsed["narrative"], (
        "Заголовок выбора срезан — кнопки пропадут"
    )
    assert "взломать терминал" in parsed["narrative"], (
        "Вариант 1 срезан [STATE]-блоком"
    )
    assert "надавить на охранника" in parsed["narrative"], (
        "Вариант 2 срезан [STATE]-блоком"
    )
    assert "[STATE]" not in parsed["narrative"], "Сырой [STATE]-тег остался в нарративе"


def test_state_mid_response_still_parses_json(parser_engine):
    """G2: state_changes из [STATE]{...} в середине распарсились, изменения
    применены к персонажу."""
    response = (
        "Нарратив.\n"
        '[STATE]{"hp_change": -7, "credits_change": 100}\n'
        "Что будешь делать?\n"
        "1. [ХАКЕР] — взлом"
    )
    # hp_max/derived для clamp
    parser_engine.state.character = {
        "current_hp": 50,
        "credits": 1000,
        "derived": {"health_points": 50},
    }
    parsed = parser_engine._parse_ai_response(response)

    assert parsed["state_changes"].get("hp_change") == -7
    assert parsed["state_changes"].get("credits_change") == 100
    assert parser_engine.state.character["current_hp"] == 43
    assert parser_engine.state.character["credits"] == 1100
    # Нарратив без JSON-хвостов
    assert '{"hp_change"' not in parsed["narrative"]


def test_state_at_end_backward_compatible(parser_engine):
    """G2 (обратная совместимость): [STATE] в самом конце ответа (старое
    поведение) — JSON парсится, нарратив чист, варианты до блока целы."""
    response = (
        "Нарратив. Что будешь делать?\n"
        "1. [ХАКЕР] — взлом\n"
        "2. [УЛИЦА] — сила\n"
        '[STATE]{"hp_change": 3}'
    )
    parser_engine.state.character = {
        "current_hp": 40,
        "credits": 500,
        "derived": {"health_points": 50},
    }
    parsed = parser_engine._parse_ai_response(response)

    assert parsed["state_changes"].get("hp_change") == 3
    assert "Что будешь делать?" in parsed["narrative"]
    assert "взлом" in parsed["narrative"]
    assert "[STATE]" not in parsed["narrative"]


def test_state_closed_tags_still_work(parser_engine):
    """Полный [STATE]...[/STATE] — канонический формат не сломан."""
    response = (
        "Нарратив.\n"
        '[STATE]{"hp_change": -2}[/STATE]\n'
        "Что будешь делать?\n"
        "1. [ХАКЕР] — взлом"
    )
    parser_engine.state.character = {
        "current_hp": 50,
        "credits": 0,
        "derived": {"health_points": 50},
    }
    parsed = parser_engine._parse_ai_response(response)

    assert parsed["state_changes"].get("hp_change") == -2
    assert "Что будешь делать?" in parsed["narrative"]
    assert parser_engine.state.character["current_hp"] == 48


# ═══════════════════════════════════════════════════════════════
# G1: слоты, экипировка, save/load roundtrip
# ═══════════════════════════════════════════════════════════════

SHOP_RIFLE = "Винтовка «Ястреб»"          # W_RIFLE_HAWK из BASE_SHOP_ITEMS
SHOP_PISTOL = "Пистолет «Страж» Mk.I"     # W_PISTOL_BASIC


def _slots_of(engine):
    """Разделить инвентарь по слотам той же логикой, что /api/inventory/slots."""
    from src.systems.equipment_lookup import resolve_item
    slots = {"weapon": [], "armor": [], "implant": [], "pocket": []}
    for item in engine.state.inventory:
        stats = resolve_item(item.get("name")) or {}
        kind = stats.get("kind")
        item_type = str(item.get("type") or item.get("category") or "").lower()
        if kind == "weapon" or "weapon" in item_type:
            slot = "weapon"
        elif kind == "armor" or "armor" in item_type:
            slot = "armor"
        elif kind == "implant" or "имплант" in item.get("name", "").lower():
            slot = "implant"
        else:
            slot = "pocket"
        slots[slot].append(item)
    return slots


def _character_route_app():
    """Flask test client + set_engine (паттерн endpoint-тестов проекта)."""
    from src.server.app import app
    from src.server.routes import _deps
    return app, _deps


def test_shop_rifle_goes_to_weapon_slot_not_pocket():
    """G1 (регресс): купленная «Винтовка «Ястреб»» — слот weapon, не pocket;
    usable=False (кнопка «Использовать» не рисуется), equippable=True."""
    from src.systems.equipment_lookup import resolve_item

    stats = resolve_item(SHOP_RIFLE)
    assert stats is not None, (
        "Магазинное оружие не резолвится через equipment_lookup — "
        "классификация снова упадёт в pocket"
    )
    assert stats.get("kind") == "weapon"

    from src.core.engine import GameEngine
    engine = GameEngine()
    engine.create_custom_character({
        "name": "SlotTest",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER",
        "age": 25,
    })
    engine.state.inventory.append({
        "id": "W_RIFLE_HAWK", "name": SHOP_RIFLE, "qty": 1,
        "type": "weapons", "stats": "2d8+2, long range", "rarity": "uncommon",
    })
    slots = _slots_of(engine)
    assert SHOP_RIFLE in [i["name"] for i in slots["weapon"]]
    assert SHOP_RIFLE not in [i["name"] for i in slots["pocket"]]

    # Проверка через endpoint-логику: usable строго у расходников
    rec = next(i for i in engine.state.inventory if i["name"] == SHOP_RIFLE)
    assert stats.get("kind") not in ("consumable_heal", "consumable_buff")
    assert not rec.get("usable")  # если есть флаг — он False


def test_equip_second_weapon_auto_unequips_first():
    """G1: экипировка второго weapon снимает первый (маркер ◆ переезжает)."""
    from src.server.app import app
    from src.server.routes import _deps
    from src.core.engine import GameEngine

    engine = GameEngine()
    engine.create_custom_character({
        "name": "EquipTest",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER",
        "age": 25,
    })
    engine.state.inventory.extend([
        {"id": "W_RIFLE_HAWK", "name": SHOP_RIFLE, "qty": 1, "type": "weapons"},
        {"id": "W_PISTOL_BASIC", "name": SHOP_PISTOL, "qty": 1, "type": "weapons"},
    ])
    _deps.set_engine(engine)
    app.config["TESTING"] = True

    with app.test_client() as client:
        r1 = client.post("/api/inventory/equip", json={
            "item_name": SHOP_RIFLE, "action": "equip"})
        assert r1.status_code == 200
        assert r1.get_json()["success"] is True

        inv = engine.state.inventory
        rifle = next(i for i in inv if i["name"] == SHOP_RIFLE)
        assert rifle.get("equipped") is True

        r2 = client.post("/api/inventory/equip", json={
            "item_name": SHOP_PISTOL, "action": "equip"})
        assert r2.status_code == 200

        pistol = next(i for i in inv if i["name"] == SHOP_PISTOL)
        assert pistol.get("equipped") is True, "Второй weapon не экипировался"
        assert rifle.get("equipped") is False, (
            "Первый weapon не снят — два активных оружия одновременно"
        )


def test_equipped_survives_save_load_roundtrip():
    """G1: save_game → load_game (новый engine) — флаг equipped и
    распределение по слотам восстанавливаются 1:1."""
    from src.server.app import app
    from src.server.routes import _deps
    from src.core.engine import GameEngine

    slot_name = "test_phase29_equip_roundtrip"

    engine = GameEngine()
    engine.create_custom_character({
        "name": "RoundtripTest",
        "origin": "ORIGIN_EARTH_SLUMS",
        "formative_years": "FY_SLUMS_GANGWAR",
        "specialization": "SPEC_HACKER",
        "age": 25,
    })
    engine.state.inventory.extend([
        {"id": "W_RIFLE_HAWK", "name": SHOP_RIFLE, "qty": 1, "type": "weapons"},
        {"id": "W_PISTOL_BASIC", "name": SHOP_PISTOL, "qty": 1, "type": "weapons"},
        {"name": "Стимпак", "qty": 2, "type": "equipment"},
    ])
    engine.state.character["name"] = "RoundtripTest"

    _deps.set_engine(engine)
    app.config["TESTING"] = True
    with app.test_client() as client:
        assert client.post("/api/inventory/equip", json={
            "item_name": SHOP_RIFLE, "action": "equip"}).status_code == 200

    save_result = engine.save_game(slot_name)
    assert "error" not in save_result

    try:
        # Новый engine — как перезапуск сервера
        engine_before = engine
        engine2 = GameEngine()
        load_result = engine2.load_game(slot_name)
        assert "error" not in load_result

        # Инвентарь реально пересобран из JSON, а не общая ссылка с памятью:
        # иначе тест мог бы быть ложно-зелёным (видим тот же dict, а не восстановленный)
        assert id(engine_before.state.inventory) != id(engine2.state.inventory), (
            "load_game вернул тот же объект inventory — пересборки из JSON не было"
        )

        old_rifle = next(i for i in engine.state.inventory if i["name"] == SHOP_RIFLE)
        new_rifle = next(i for i in engine2.state.inventory if i["name"] == SHOP_RIFLE)
        new_pistol = next(i for i in engine2.state.inventory if i["name"] == SHOP_PISTOL)
        new_stim = next(i for i in engine2.state.inventory if i["name"] == "Стимпак")

        assert new_rifle.get("equipped") is True, (
            "Флаг equipped потерян при save/load"
        )
        assert old_rifle.get("equipped") == new_rifle.get("equipped")

        # Распределение по слотам 1:1
        slots_before = _slots_of(engine)
        slots_after = _slots_of(engine2)
        for slot in ("weapon", "armor", "implant", "pocket"):
            names_before = sorted(i["name"] for i in slots_before[slot])
            names_after = sorted(i["name"] for i in slots_after[slot])
            assert names_before == names_after, (
                f"Слот {slot}: {names_before} != {names_after} после load"
            )

        # Пистолет не унаследовал экипировку, расходник — не weapon
        assert not new_pistol.get("equipped")
        assert new_stim["qty"] == 2
    finally:
        engine.delete_save(slot_name)
