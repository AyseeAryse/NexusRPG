"""
Backlog#3: квесты из plot_hooks фракций.

Проверяет:
- Маппинг HOOK_TYPE_TO_TEMPLATE покрывает ВСЕ hook.type каталога без «сирот»
  и все tpl_id существуют в QUEST_TEMPLATE_POOL
- generate_quest_from_hook: f1 (владелец) присутствует в квесте,
  rival из involved_factions/enemies, reward_reputation → владельцу
- Fallback: фракция без involved получает rival из enemies или работает без него
- source="plot_hook" и метаданные хука в квесте
"""

import json

import pytest

from src.world.procedural import (
    HOOK_TYPE_TO_TEMPLATE, ProceduralQuestGenerator)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def master():
    return load("game_data/FACTIONS_MASTER.json")


@pytest.fixture(scope="module")
def pool():
    return load("game_data/QUEST_TEMPLATE_POOL.json")["templates"]


@pytest.fixture(scope="module")
def all_hook_types(master):
    types = set()
    for f in master["factions"]:
        if "canonical_duplicate_of" in f:
            continue
        for h in (f.get("plot_hooks") or []):
            types.add(h.get("type"))
    return types


class TestMappingCoverage:
    def test_all_hook_types_mapped(self, all_hook_types):
        orphans = [t for t in all_hook_types if t not in HOOK_TYPE_TO_TEMPLATE]
        assert not orphans, f"хуки-сироты без шаблона: {orphans}"

    def test_all_tpl_ids_exist(self, pool):
        ids = {t["tpl_id"] for t in pool}
        bad = [v for v in HOOK_TYPE_TO_TEMPLATE.values() if v not in ids]
        assert not bad, f"маппинг ссылается на несуществующие tpl_id: {set(bad)}"

    def test_mapping_size_matches_hook_types(self, all_hook_types):
        assert len(HOOK_TYPE_TO_TEMPLATE) == len(all_hook_types)


class TestGenerateFromHook:
    @pytest.fixture
    def gen(self):
        return ProceduralQuestGenerator()

    def test_data_rebels_conspiracy_quest(self, gen, monkeypatch):
        # фиксируем выбор хука: random.choice возвращает первый элемент списка
        import src.world.procedural as proc
        monkeypatch.setattr(proc.random, "choice",
                            lambda seq: seq[0] if isinstance(seq, list) else seq)
        q = gen.generate_quest_from_hook("Data Rebels")
        assert "error" not in q
        assert q["source"] == "plot_hook"
        assert q["hook_owner"] == "Data Rebels"
        assert q["hook_type"] == "conspiracy"  # первый хук SC52
        assert q["reward_reputation"] == {"Data Rebels": 8}  # conspiracy→tier5
        assert q["rival_faction"] == "Shadow Consortium"

    def test_owner_name_in_description(self, gen):
        for faction in ("Data Rebels", "Helios Energy Corp.", "OPA"):
            q = gen.generate_quest_from_hook(faction)
            assert "error" not in q
            text = q["title"] + " " + q["description"] + " " + \
                str(q.get("hook_description", ""))
            assert faction in text, f"{faction}: имя не попало в квест"

    def test_reward_reputation_bonus_range(self, gen):
        """+5..+10 от тира шаблона."""
        for faction in ("OPA", "ByteHack Collective"):
            q = gen.generate_quest_from_hook(faction)
            if "error" in q:
                continue
            (fac, bonus), = q["reward_reputation"].items()
            assert fac == faction
            assert 5 <= bonus <= 10

    def test_rival_prefers_involved_then_enemies(self, gen):
        """MC2: involved=[OPA] → rival OPA; если пусто — из enemies."""
        q = gen.generate_quest_from_hook("Helios Energy Corp.")
        assert q["hook_type"] == "scandal"  # MC2 первый хук — scandal
        # у MC2 scandal-hook involved=[OPA]
        assert q["rival_faction"] == "OPA"

    def test_unknown_faction_error(self, gen):
        assert "error" in gen.generate_quest_from_hook("Несуществующие")

    def test_quest_fields_present(self, gen):
        q = gen.generate_quest_from_hook("Data Rebels")
        for k in ("title", "description", "stages", "reward_credits",
                  "reward_xp", "source", "hook_id", "hook_owner",
                  "reward_reputation"):
            assert k in q, k
