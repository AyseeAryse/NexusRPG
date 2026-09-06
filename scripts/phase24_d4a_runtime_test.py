# -*- coding: utf-8 -*-
"""D4a рантайм-тест: контракты хакинга/расследования через flask test_client.

Проверяет живой бэкенд (не моки): улики с UI-контрактом, лиды в /list,
вывод дела с точностью, лут→кредиты и sanity-урон через API-роуты.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.server.app import app, engine, init_engine

BASE_HINTS = []


def post(client, url, payload):
    r = client.post(url, json=payload)
    return json.loads(r.data.decode("utf-8")), r.status_code


def get(client, url):
    r = client.get(url)
    return json.loads(r.data.decode("utf-8"))


def main():
    init_engine()  # engine создаётся только в __main__-потоке сервера
    # from-import захватил None до init_engine() — перечитываем актуальную ссылку
    global engine
    engine = sys.modules["src.server.app"].engine
    app.config["TESTING"] = True
    with app.test_client() as c:
        print("=== РАССЛЕДОВАНИЕ ===")

        # I4: канонический тип открытия (theft существует в шаблонах)
        resp, code = post(c, "/api/investigation/open",
                          {"type": "theft", "name": "Дело о пропавшем прототипе"})
        assert code == 200 and "error" not in resp, resp
        case_id = resp["id"]
        print(f"open theft -> id={case_id}, name={resp['name']!r}")

        # I2: list отдаёт UI-поля + leads
        data = get(c, "/api/investigation/list")
        case = next(x for x in data["active"] if x["id"] == case_id)
        assert case["required_clues"] == 4, case
        assert isinstance(case["clues"], list) and len(case["clues"]) == 0
        assert len(case["leads"]) >= 3, case["leads"]
        print(f"list -> required_clues={case['required_clues']}, "
              f"leads={case['leads']}")

        # I1: ТОЧНЫЙ контракт UI (type/description) — текст доходит до clue.text
        ui_payloads = [
            {"case_id": case_id, "type": "physical",
             "description": "Взломанный замок склада"},
            {"case_id": case_id, "type": "witness",
             "description": "Свидетель видел человека в корпоративной куртке"},
            {"case_id": case_id, "type": "digital",
             "description": "Логи камер стёрты в 03:00"},
        ]
        for p in ui_payloads:
            resp, code = post(c, "/api/investigation/clue", p)
            assert code == 200 and "error" not in resp, resp
            assert resp["clue"]["text"] == p["description"], resp["clue"]
            assert resp["clue"]["source"] == p["type"], resp["clue"]
        last = resp
        print("clue x3 (UI-контракт): тексты и источники дошли ✅")
        print(f"после 3-й улики: progress={last['progress']}, "
              f"can_conclude={last['can_conclude']}")
        assert last["can_conclude"] is False  # бэк: вывод только при полном наборе

        # 4-я улика -> кейс готов к заключению
        resp, code = post(c, "/api/investigation/clue",
                          {"case_id": case_id, "type": "document",
                           "description": "Заказ на вывоз прототипа с подделанной печатью"})
        assert resp["can_conclude"] is True, resp
        print("clue x4 -> can_conclude=True ✅")

        # I2 повторно: прогресс виден в list для UI
        data = get(c, "/api/investigation/list")
        case = next(x for x in data["active"] if x["id"] == case_id)
        assert len(case["clues"]) == 4 and case["required_clues"] == 4
        print(f"list -> Улики: {len(case['clues'])}/{case['required_clues']} ✅")

        # Вывод дела (механика надёжности Ф17C не тронута)
        resp, code = post(c, "/api/investigation/conclude",
                          {"case_id": case_id, "suspect": "Вито Маркини",
                           "conclusion": "Кража по заказу конкурента"})
        assert code == 200 and resp.get("case_closed"), resp
        print(f"conclude -> correct={resp['correct']}, "
              f"accuracy={resp['accuracy']}, rel_mod={resp['reliability_modifier']}")

        # I3: suspect с ключом UI
        resp, _ = post(c, "/api/investigation/open", {"type": "murder"})
        cid2 = resp["id"]
        resp, _ = post(c, "/api/investigation/suspect",
                       {"case_id": cid2, "name": "Подозреваемый N", "motive": "зависть"})
        assert "error" not in resp, resp
        data = get(c, "/api/investigation/list")
        c2 = next(x for x in data["active"] if x["id"] == cid2)
        assert c2["suspects"][0]["name"] == "Подозреваемый N", c2["suspects"]
        print("suspect (ключ name из UI) -> имя не пустое ✅")

        print("\n=== ХАКИНГ ===")
        # state появляется после создания персонажа (как в реальной игре)
        presets = engine.get_presets()
        engine.create_character_from_preset(presets[0]["id"])
        assert engine.state is not None and engine.state.character, "state не создан"
        char = engine.state.character
        char["credits"] = 100
        char["current_sanity"] = 50

        # Старт через API (как делает панель)
        resp, code = post(c, "/api/hacking/start", {"target_type": "terminal"})
        assert code == 200 and resp.get("status") == "active", resp
        print(f"start terminal -> nodes={len(resp['nodes'])}, "
              f"turns_left={resp['turns_left']}")

        # H2: Чёрный лёд через API — урон реально в character
        from src.systems.subsystems import ICE_TYPES
        h = engine.hacking.active_hack
        bi = next(i for i in ICE_TYPES if i["type"] == "black_ice")
        h["nodes"][0]["ice"] = dict(bi)
        h["nodes"][0]["ice"]["active"] = True
        h["turns_left"] = 99  # чтобы таймер не мешал сценарию

        resp, _ = post(c, "/api/hacking/action", {"action": "crack_ice"})
        assert resp["success"] is False and resp["sanity_damage"] >= 2, resp
        assert char["current_sanity"] == 50 - resp["sanity_damage"], char
        print(f"black_ice fail -> sanity_damage={resp['sanity_damage']}, "
              f"current_sanity={char['current_sanity']} (было 50) ✅")

        # H1: лут через API — кошелёк конвертируется в кредиты персонажа
        h = engine.hacking.active_hack
        h["nodes"][-1]["ice"] = None
        h["current_node"] = len(h["nodes"]) - 1
        resp, _ = post(c, "/api/hacking/action", {"action": "extract_data"})
        assert resp["success"], resp
        loot = resp["loot"]
        m = re.search(r"кошел[её]к:\s*(\d+)-(\d+)₡", loot)
        if m:
            delta = char["credits"] - 100
            assert int(m.group(1)) <= delta <= int(m.group(2)), (loot, delta)
            assert resp["credits_gained"] == delta
            print(f"extract_data -> лут-кошелёк: {delta}₡ зачислено ✅")
        else:
            assert char["credits"] == 100
            print(f"extract_data -> не-кошелёчный лут ({loot[:40]}...), "
                  f"кредиты не тронуты ✅")
        assert engine.hacking.loot_log[-1]["text"] == loot
        print(f"loot_log в state: {[e['text'][:30] for e in engine.hacking.loot_log]} ✅")

    print("\nD4a RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
