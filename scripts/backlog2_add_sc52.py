# -*- coding: utf-8 -*-
"""Backlog#2: точечная вставка SC52 Data Rebels в FACTIONS_MASTER.json + валидация."""
import io
import json

PATH = "game_data/FACTIONS_MASTER.json"

NEW_FACTION = """    {
      "id": "SC52",
      "name": "Data Rebels",
      "type": "SME",
      "history": "Родились из утёкших архивов «Квантового Диссонанса» (2230): журналисты, инженеры и белые хакеры, отказавшиеся забыть. Ячейки-«ретрансляторы» держат независимую сеть связи между Землёй и Луной.",
      "legends": "Говорят, у них есть «Архив Правды» — полная неотредактированная история Системы, и однажды они выложат его целиком.",
      "leaders": [
        "Совет ретрансляторов",
        "спикер под псевдонимом «Чистый Сигнал»"
      ],
      "influence_region": "Земля (Нью-Токио, Нижний город), Луна (Лунные туннели)",
      "business_area": "Независимая связь, защита данных, утечки",
      "allies": [
        "OPA",
        "ByteHack Collective"
      ],
      "enemies": [
        "Earth UN",
        "Конгломерат «МедиаСфера»",
        "Shadow Consortium"
      ],
      "mechanics": [
        {
          "type": "info_trade",
          "target": "data_leaks",
          "value": 1,
          "operator": "add"
        },
        {
          "type": "heat_reduction",
          "value": 1
        }
      ],
      "plot_hooks": [
        {
          "id": "sc52_hook_1",
          "type": "conspiracy",
          "description": "Ретранслятор в Нижнем городе передал обрывок «Архива Правды» — за ним уже охотятся те, кто хочет, чтобы правда осталась похороненной.",
          "involved_factions": [
            "Shadow Consortium"
          ]
        },
        {
          "id": "sc52_hook_2",
          "type": "alliance",
          "description": "Совет ретрансляторов ищет курьера для передачи данных между Нью-Токио и Лунными туннелями — маршрут проходит мимо слишком многих ушей.",
          "involved_factions": []
        }
      ]
    }"""

ANCHOR = '      ]\r\n    }\r\n  ],\r\n  "total_factions": 166,'
REPLACEMENT = ('      ]\r\n    },\r\n' + NEW_FACTION.replace("\n", "\r\n") +
               '\r\n  ],\r\n  "total_factions": 167,')

text = io.open(PATH, encoding="utf-8", newline="").read()
assert text.count(ANCHOR) == 1, f"anchor count = {text.count(ANCHOR)}"
new_text = text.replace(ANCHOR, REPLACEMENT)

json.loads(new_text)  # валидация ДО записи
canon = [f for f in json.loads(new_text)["factions"]
         if "canonical_duplicate_of" not in f]
assert len(canon) == 167, len(canon)
assert canon[-1]["id"] == "SC52" and canon[-1]["name"] == "Data Rebels"

io.open(PATH, "w", encoding="utf-8", newline="").write(new_text)
print("FACTIONS_MASTER.json обновлён: 167 канонических фракций, последняя SC52 Data Rebels")
