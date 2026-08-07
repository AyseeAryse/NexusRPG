"""
NPC Registry — generates, stores, and retrieves named NPCs.
Uses NPC_ARCHETYPES (200 types) + NPC_NAME_GENERATOR (60 names) + appearance tables.
Every NPC created during play is saved and can be recalled.
"""
import random
import json
from typing import Dict, List, Optional

# ==========================================
# NAME TABLES (from NPC_NAME_GENERATOR.json)
# ==========================================
NAME_TABLES = {
    "Земля": [
        "Алекс Чен", "Мария Гонзалес", "Джамал Окафор", "Прия Шарма",
        "Эрик Ларссон", "Юки Танака", "Фатима Аль-Рашид", "Коннор О'Брайен",
        "Зара Одуйя", "Дмитрий Волков", "Изабелла Сантос", "Кваме Асанте",
        "Лин Вэй", "Рашид Хасан", "Нина Петрова", "Карлос Ривера",
        "Амара Сингх", "Лиам Мёрфи", "Кэйко Ямамото", "Омар Бенали",
        "Анна Козлова", "Сато Хиро", "Елена Миронова", "Хуан Карлос Рейес",
        "Софи Бернар", "Микаэль Йоханссон", "Ван Ли Мин", "Арджун Патель",
        "Натали Дюбуа", "Игорь Сидоров",
    ],
    "Марс": [
        "Рекс Стил", "Нова Кримсон", "Зед Маринер", "Ария Редстоун",
        "Кейн Дастер", "Луна Крейтер", "Дэш Айронворкс", "Вера Оксидин",
        "Шторм Растерсон", "Блейз Марков", "Терра Реддинг", "Аксель Дастборн",
        "Сейбл Марскейп", "Флинт Крейтерфейс", "Руби Сэндсторм",
        "Титан Айронсайд", "Эмбер Дастклауд", "Рейвен Редпланет",
        "Стил Марсден", "Кримсон Вэйл", "Грэнит Форж", "Оникс Дриллер",
        "Хром Марсфилд", "Искра Вулканова", "Гранит Ковальски",
    ],
    "Пояс астероидов": [
        "Джейк-Шахтёр", "Стелла Войд", "Рок Хаммерфист", "Комета Дрифтер",
        "Астероид Энни", "Войд Уокер", "Кристал Диггер", "Стоун Брейкер",
        "Ор Хантер", "Спейс Риппер", "Метал Шард", "Даст Дэвил",
        "Крейтер Мак", "Вакуум Вик", "Дебрис Дэн", "Чанк Чарли",
        "Рубл Роуз", "Грэвел Грейс", "Боулдер Боб", "Пебл Пит",
        "Дрилла Кей", "Зеро-Джи Зак", "Флот Сэм", "Ника Пылевая",
    ],
    "Ганимед": [
        "Доктор Ева Фрост", "Профессор Такеши Мори", "Лина Айсберг",
        "Хельга Нордстрём", "Рэй Криоген", "Нова Биолайт", "Артур Глейшер",
        "Зоя Термоплаз", "Кай Деепфриз", "Мира Гидроклер",
        "Доктор Вэнь Чжоу", "Профессор Айрис Кольд", "Нильс Тайдал",
        "Серена Айсвокер", "Борис Ледников",
    ],
    "Луна": [
        "Армстронг Хейз", "Селена Грей", "Нил Крейтервиль", "Лунара Сильвер",
        "Тайкон Дарксайд", "Артемис Райт", "Базз Регалит", "Кратер Джонс",
        "Пыль Макгрегор", "Орбита Ли", "Гелий Тринадцатый", "Вакуум Мэй",
    ],
}

# ==========================================
# APPEARANCE TABLE (from NPC_NAME_GENERATOR)
# ==========================================
APPEARANCES = [
    "шрам через левый глаз от лазерного ожога",
    "кибернетическая рука с видимыми сервоприводами",
    "татуировка фракции на шее",
    "гетерохромия — один глаз голубой, другой карий",
    "седые волосы, хотя выглядит молодо — от стресса",
    "металлические зубные импланты с позолотой",
    "бионический глаз с красной подсветкой",
    "выжженная на запястье метка бывшего раба",
    "дорогой костюм с логотипом корпорации",
    "военная выправка и точные, экономные движения",
    "нервный тик — постоянно проверяет коммуникатор",
    "искусственная кожа на половине лица после ожогов",
    "дорогие ювелирные импланты в ушах",
    "мозоли на руках от физического труда",
    "элегантная походка аристократа",
    "запах машинного масла и металла",
    "бледность от жизни на космических станциях",
    "мускулистое телосложение горняка",
    "изысканный парфюм земной элиты",
    "постоянная настороженность в глазах",
    "QR-код татуировка на шее",
    "светящийся нейроинтерфейс на виске",
    "протез ноги с видимой гидравликой",
    "глубокие тёмные круги под глазами — недосып",
    "заметный белтерский акцент — растягивает гласные",
    "лицо в мелких шрамах от кислотного дождя",
    "левая рука покрыта светящимися тату-схемами",
    "разбитые костяшки кулаков — привык решать кулаками",
    "тонкие губы, сжатые в постоянную полуулыбку",
    "один глаз закрыт повязкой с мерцающим индикатором",
]

# ==========================================
# SPEECH STYLES (from DIALOGUE_INTEGRATED_WITH_LIFEPATH)
# ==========================================
SPEECH_STYLES = {
    "военный": {
        "style": "Чёткий, рубленый. Короткие предложения. Команды.",
        "vocabulary": "звания, тактика, «принял», «отбой», «на позицию»",
        "example": "«Доклад. Цель обнаружена. Жду приказа. Время — не на нашей стороне.»",
    },
    "корпоративный": {
        "style": "Вежливый, уклончивый. Много подтекста. Никогда не говорит прямо.",
        "vocabulary": "«синергия», «оптимизация», «реструктуризация», «ничего личного»",
        "example": "«Мы ценим ваш... вклад. Однако текущая ситуация требует определённой... гибкости.»",
    },
    "белтерский": {
        "style": "Грубый, с протяжным акцентом. Сленг Пояса. Прямолинейный.",
        "vocabulary": "«бротер», «ми-ми», «кэсэ», «да-да, пампа», «ой»",
        "example": "«Ой, бротер... Тебе чё, жить надоело? На Поясе так не делают, ми-ми.»",
    },
    "учёный": {
        "style": "Точный, педантичный. Много терминов. Увлекается темой.",
        "vocabulary": "«гипотеза», «коррелирует», «статистически значимо», «интересно»",
        "example": "«Фасцинирующе! Квантовая когерентность сохраняется даже при... Впрочем, вам это вряд ли интересно.»",
    },
    "криминальный": {
        "style": "Тихий, угрожающий. Много намёков. Никогда не называет вещи прямо.",
        "vocabulary": "«работа», «услуга», «долг», «было бы жаль», «друзья»",
        "example": "«У меня есть... предложение. Из тех, от которых лучше не отказываться. Ты же умный, да?»",
    },
    "уличный": {
        "style": "Быстрый, агрессивный. Сленг. Много бравады.",
        "vocabulary": "«чел», «тема», «замес», «по-любому», «чётко»",
        "example": "«Слышь, чел, тут такая тема — шеф сказал, надо по-быстрому. Ты в деле или нет?»",
    },
    "аристократический": {
        "style": "Изысканный, снисходительный. Длинные фразы. Скука в голосе.",
        "vocabulary": "«дражайший», «соизвольте», «какая проза», «утомительно»",
        "example": "«Дражайший, вы же понимаете, что ваше... положение не позволяет вам быть столь дерзким?»",
    },
    "наёмник": {
        "style": "Деловой, циничный. Считает всё в кредитах. Без эмоций.",
        "vocabulary": "«контракт», «оплата», «условия», «без вопросов», «моё дело — работа»",
        "example": "«Двадцать тысяч. Аванс — половина. Без вопросов. Если хочешь дешевле — найди другого.»",
    },
    "религиозный": {
        "style": "Торжественный, метафоричный. Цитаты, притчи.",
        "vocabulary": "«путь», «истина», «заблудшие», «знамение», «провидение»",
        "example": "«Звёзды говорят с теми, кто умеет слушать. Ты здесь неслучайно, странник.»",
    },
    "хакерский": {
        "style": "Быстрый, с техно-жаргоном. Саркастичный. Нервозный.",
        "vocabulary": "«крякнуть», «бэкдор», «файрвол», «ледоруб», «чистый»",
        "example": "«Их ICE — мусор. Третий уровень, смешно. Дай мне пять минут и root-доступ — и всё.»",
    },
}

# Map origin keywords to default speech style
ORIGIN_SPEECH_MAP = {
    "MILITARY": "военный",
    "ELITE": "аристократический",
    "CORPORATE": "корпоративный",
    "SLUMS": "уличный",
    "BELT": "белтерский",
    "CERES": "белтерский",
    "SALVAG": "белтерский",
    "SCIENTIST": "учёный",
    "GANYMEDE": "учёный",
    "HACKER": "хакерский",
    "SMUGGL": "криминальный",
    "CRIMINAL": "криминальный",
    "REBEL": "уличный",
    "NOMAD": "белтерский",
    "DIPLOMAT": "корпоративный",
    "CELEBRITY": "аристократический",
    "FIGHTER": "наёмник",
    "MERCENARY": "наёмник",
}

# ==========================================
# ARCHETYPE ROLES (simplified from 200 archetypes)
# ==========================================
ARCHETYPE_ROLES = [
    {"role": "Торговец", "motive": "прибыль", "function": "поставщик/информатор"},
    {"role": "Наёмник", "motive": "деньги и репутация", "function": "союзник/враг в бою"},
    {"role": "Информатор", "motive": "выживание", "function": "источник слухов и данных"},
    {"role": "Техник", "motive": "любопытство к технике", "function": "ремонт/модификации"},
    {"role": "Бармен", "motive": "спокойная жизнь", "function": "слухи/убежище/контакты"},
    {"role": "Охранник", "motive": "долг/оплата", "function": "препятствие/союзник"},
    {"role": "Контрабандист", "motive": "свобода и деньги", "function": "нелегальные товары/транспорт"},
    {"role": "Врач", "motive": "помощь/прибыль", "function": "лечение/импланты"},
    {"role": "Фиксер", "motive": "связи и влияние", "function": "квестодатель/посредник"},
    {"role": "Хакер", "motive": "информация", "function": "взлом/данные"},
    {"role": "Пилот", "motive": "свобода", "function": "транспорт/побег"},
    {"role": "Полицейский", "motive": "порядок/коррупция", "function": "закон/угроза"},
    {"role": "Журналист", "motive": "правда/слава", "function": "информация/разоблачение"},
    {"role": "Учёный", "motive": "знания", "function": "экспертиза/квестодатель"},
    {"role": "Проповедник", "motive": "вера", "function": "моральный компас/фанатик"},
    {"role": "Политик", "motive": "власть", "function": "квестодатель/манипулятор"},
    {"role": "Уличный боец", "motive": "выживание", "function": "силовое решение"},
    {"role": "Шпион", "motive": "информация/лояльность", "function": "двойной агент"},
    {"role": "Механик", "motive": "ремёсла", "function": "крафтинг/ремонт"},
    {"role": "Ребёнок улиц", "motive": "выживание", "function": "проводник/вор"},
]

# Faction affiliations
FACTION_POOL = [
    "LunarTech Industries", "Helios Energy Corp", "Protogen", "Genesis Bioworks",
    "Nexus Pharmaceuticals", "Aetherium Dynamics", "Omega Defense Systems",
    "Mars Fleet", "ООН Земли", "OPA", "Марсианская Республика",
    "Black Lotus Triad", "Shadow Consortium", "Data Rebels",
    "SENTINEL PMC", "Iron Wolves", "Black Aegis",
    "Kurosawa Heavy Industries", "QuantumMeals Corp", "Vesta Industrial Union",
    "независимый",
]


class NPCRegistry:
    """Generates, stores, and retrieves NPCs."""

    def __init__(self):
        self.npcs: Dict[str, Dict] = {}  # name -> NPC data
        self._used_names: set = set()

    def generate_npc(self, planet: str = "Земля", role: str = None,
                     faction: str = None, importance: str = "minor",
                     name: str = None, location: str = "") -> Dict:
        """Generate a new NPC with full details."""
        # Pick name from planet pool (or use provided name)
        if name and name not in self.npcs:
            self._used_names.add(name)
        else:
            name_pool = NAME_TABLES.get(planet, NAME_TABLES["Земля"])
            available = [n for n in name_pool if n not in self._used_names]
            if not available:
                first = random.choice(name_pool).split()[0]
                suffix = random.choice(["Младший", "II", str(random.randint(1, 99))])
                available = [f"{first} {suffix}"]
            name = random.choice(available)
            self._used_names.add(name)

        # Pick archetype
        if role:
            archetype = next((a for a in ARCHETYPE_ROLES if role.lower() in a["role"].lower()), None)
        else:
            archetype = random.choice(ARCHETYPE_ROLES)

        if not archetype:
            archetype = random.choice(ARCHETYPE_ROLES)

        # Pick appearance (2 traits)
        appearance = random.sample(APPEARANCES, min(2, len(APPEARANCES)))

        # Pick speech style based on role/planet
        speech_key = self._pick_speech_style(archetype["role"], planet)
        speech = SPEECH_STYLES.get(speech_key, SPEECH_STYLES["уличный"])

        # Pick faction
        if not faction:
            faction = random.choice(FACTION_POOL)

        npc = {
            "name": name,
            "planet": planet,
            "role": archetype["role"],
            "motive": archetype["motive"],
            "function": archetype["function"],
            "appearance": appearance,
            "speech_style": speech_key,
            "speech_info": speech,
            "faction": faction,
            "importance": importance,  # minor / notable / major
            "disposition": random.choice(["нейтральный", "дружелюбный", "настороженный", "враждебный"]),
            "met_count": 0,
            "notes": [],
        }

        self.npcs[name] = npc
        return npc

    def _pick_speech_style(self, role: str, planet: str) -> str:
        """Pick speech style based on role and planet."""
        role_upper = role.upper()
        for keyword, style in ORIGIN_SPEECH_MAP.items():
            if keyword in role_upper:
                return style

        # Planet-based defaults
        planet_defaults = {
            "Земля": random.choice(["корпоративный", "уличный", "аристократический"]),
            "Марс": random.choice(["военный", "учёный", "наёмник"]),
            "Пояс астероидов": "белтерский",
            "Ганимед": "учёный",
            "Луна": random.choice(["корпоративный", "учёный"]),
        }
        return planet_defaults.get(planet, "уличный")

    def get_npc(self, name: str) -> Optional[Dict]:
        """Retrieve NPC by name (fuzzy match)."""
        if name in self.npcs:
            return self.npcs[name]
        # Fuzzy: partial match
        name_lower = name.lower()
        for npc_name, npc in self.npcs.items():
            if name_lower in npc_name.lower():
                return npc
        return None

    def record_encounter(self, name: str, turn: int = 0, context: str = "",
                         note: str = "", disposition_change: int = 0):
        """Record that player met this NPC. Stores interaction memory."""
        npc = self.get_npc(name)
        if npc:
            npc["met_count"] += 1
            npc["last_met_turn"] = turn
            # Store memory
            memory_entry = {"turn": turn}
            if context:
                memory_entry["context"] = context[:120]
            if note:
                memory_entry["note"] = note[:120]
            if not npc.get("memory"):
                npc["memory"] = []
            npc["memory"].append(memory_entry)
            # Keep last 10 memories
            npc["memory"] = npc["memory"][-10:]
            # Update disposition
            if disposition_change:
                dispositions = ["враждебный", "настороженный", "нейтральный", "дружелюбный", "союзник"]
                current_idx = dispositions.index(npc.get("disposition", "нейтральный")) if npc.get("disposition") in dispositions else 2
                new_idx = max(0, min(len(dispositions)-1, current_idx + disposition_change))
                npc["disposition"] = dispositions[new_idx]
            # Legacy compat
            if note:
                npc["notes"].append(note[:120])
                npc["notes"] = npc["notes"][-5:]

    def get_known_npcs(self, limit: int = 10) -> List[Dict]:
        """Get list of NPCs the player has met, sorted by importance."""
        importance_order = {"major": 0, "notable": 1, "minor": 2}
        npcs = sorted(
            self.npcs.values(),
            key=lambda n: (importance_order.get(n["importance"], 3), -n["met_count"])
        )
        return npcs[:limit]

    def get_prompt_context(self, limit: int = 8) -> str:
        """Generate prompt context about known NPCs for the AI."""
        known = self.get_known_npcs(limit)
        if not known:
            return ""

        lines = ["## ИЗВЕСТНЫЕ NPC (помни их при встрече!):"]
        for npc in known:
            app = ", ".join(npc["appearance"][:1])
            lines.append(
                f"- **{npc['name']}** ({npc['role']}, {npc['faction']}) — "
                f"{app}. Стиль речи: {npc['speech_style']}. "
                f"Отношение: {npc['disposition']}. Встреч: {npc['met_count']}."
            )
            # Show memories for important NPCs
            memories = npc.get("memory", [])
            if memories:
                last = memories[-1]
                mem_text = last.get("context", last.get("note", ""))
                if mem_text:
                    lines.append(f"  Последняя встреча: {mem_text}")
            elif npc["notes"]:
                lines.append(f"  Заметки: {'; '.join(npc['notes'][-2:])}")
        return "\n".join(lines)

    def get_speech_guide(self) -> str:
        """Generate speech style reference for the AI prompt."""
        lines = ["## СТИЛИ РЕЧИ NPC (используй для разных NPC!):"]
        for key, style in SPEECH_STYLES.items():
            lines.append(f"**{key}**: {style['style']} Пример: {style['example']}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "npcs": self.npcs,
            "_used_names": list(self._used_names),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCRegistry':
        reg = cls()
        reg.npcs = data.get("npcs", {})
        reg._used_names = set(data.get("_used_names", []))
        return reg
