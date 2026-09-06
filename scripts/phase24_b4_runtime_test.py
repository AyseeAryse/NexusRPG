# -*- coding: utf-8 -*-
"""B4 рантайм-тест: платная недвижимость через flask test_client.

Вырожденные сценарии плана §3 на живом движке (не моки):
1. Беженец/нищий → отказ «Недостаточно кредитов»
2. Магнат → покупает всё, остаток корректен, доход начисляется
3. Контрабандист → осознанный выбор одного актива
4. Upkeep-симметрия: expense-цикл не сломан ценой покупки
"""
import json
import sys

sys.path.insert(0, "D:/NexusRPG-main")

from src.server.app import app, engine, init_engine


def post(c, url, payload):
    r = c.post(url, json=payload)
    return json.loads(r.data.decode("utf-8")), r.status_code


def get(c, url):
    r = c.get(url)
    return json.loads(r.data.decode("utf-8"))


def main():
    init_engine()
    engine = sys.modules["src.server.app"].engine  # from-import захватил None
    app.config["TESTING"] = True

    with app.test_client() as c:
        # Персонаж через пресет (state появляется после создания)
        presets = engine.get_presets()
        engine.create_character_from_preset(presets[0]["id"])
        char = engine.state.character
        print(f"персонаж: {char.get('name')} | старт ₡{char.get('credits', 0):,}")

        # Каталог типов для UI
        types = get(c, "/api/property/types")["types"]
        assert len(types) == 6 and all("price" in t for t in types)
        prices = {t["id"]: t["price"] for t in types}
        assert prices == {"apartment": 12000, "bar": 9000, "shop": 11000,
                          "warehouse": 22000, "office": 17000, "hideout": 30000}
        print(f"каталог /types: 6 типов, цены == утверждённой таблице ✅")

        # ── Сценарий 1: нищий → честный отказ ──
        saved = char["credits"]
        char["credits"] = 500  # Беженец Земли
        resp, code = post(c, "/api/property/buy",
                          {"type": "apartment", "location": "Нью-Токио"})
        assert code == 200 and "error" in resp, resp
        assert "12,000" in resp["error"] and "500" in resp["error"], resp
        assert char["credits"] == 500, "кредиты изменились при отказе!"
        assert get(c, "/api/property/list")["properties"] == []
        print(f"сценарий 1 (беженец ₡500): отказ '{resp['error']}' ✅")

        # ── Сценарий 3: контрабандист ₡25k → один осознанный актив ──
        char["credits"] = 25_000
        resp, _ = post(c, "/api/property/buy", {"type": "bar", "location": "Нью-Токио"})
        assert "acquired" in resp, resp
        assert resp["cost"] == 9000 and resp["credits_left"] == 16_000
        assert char["credits"] == 16_000, "списание не дошло до character!"
        props = get(c, "/api/property/list")["properties"]
        assert len(props) == 1 and props[0]["price_paid"] == 9000
        # второй актив уже не по карману — выбор был осознанным
        resp, _ = post(c, "/api/property/buy", {"type": "warehouse", "location": "?"})
        assert "error" in resp and "22,000" in resp["error"], resp
        print(f"сценарий 3 (контрабандист ₡25k): бар куплен за ₡9 000, "
              f"остаток ₡16 000, склад недоступен ✅")
        # чистка перед сценарием магната
        engine.property.properties.clear()

        # ── Сценарий 2: магнат покупает ВСЁ ──
        char["credits"] = 500_000
        total_spent = 0
        for tid in ["apartment", "bar", "shop", "warehouse", "office", "hideout"]:
            resp, _ = post(c, "/api/property/buy", {"type": tid,
                                                    "location": "Верхний город"})
            assert "acquired" in resp, (tid, resp)
            total_spent += resp["cost"]
        assert char["credits"] == 399_000, char["credits"]
        assert total_spent == 101_000
        props = get(c, "/api/property/list")["properties"]
        assert len(props) == 6
        income = get(c, "/api/property/income")["total_income"]
        assert income == 1700, income  # 500+400+800
        print(f"сценарий 2 (магнат ₡500k): все 6 куплено за ₡101 000, "
              f"остаток ₡399 000, доход ₡1 700/цикл ✅")

        # ── Сценарий 4: upkeep-цикл не задет ──
        nxt = engine.expenses.last_cycle_hours + engine.expenses.income_interval_hours
        ticked = engine.expenses.tick(nxt, engine.property, engine.ship, char,
                                      player_tier=0)
        assert ticked, "expense cycle не сработал"
        # контракт record: {cycle_hours, paid, debt_added, total_due, **breakdown}
        prop_upkeep = ticked["property_upkeep"]
        # upkeep = ставка × БРУТТО-доход: apartment 50 + shop 500×0.30=150 +
        # bar 400×0.35=140 + warehouse 100 + office 800×0.30=240 + hideout 150
        assert prop_upkeep == 830, prop_upkeep
        print(f"сценарий 4: expense tick → upkeep недвижимости ₡{prop_upkeep} "
              f"(ожидаемо 830), total_due ₡{ticked['total_due']}, "
              f"paid ₡{ticked['paid']}, debt +₡{ticked['debt_added']} ✅")

    print("\nB4 RUNTIME VERDICT: PASS")


if __name__ == "__main__":
    main()
