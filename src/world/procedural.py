"""
Procedural Engine v2 — generates infinite content from templates.
- ProceduralQuestGenerator: 30 templates × variables = infinite quests
- WorldTicker: 25 event types, faction wars, crises, opportunities
- FactionWarEngine: active conflicts, territory, alliance shifts
- ConsequenceTracker: 15 action types → delayed world reactions
"""
import random
import time
from typing import Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════
#  QUEST VARIABLES — combinatorial pool
# ════════════════════════════════════════════════════════════

QUEST_VARIABLES = {
    "factions": [
        "ООН Земли", "Helios Corp", "Kurosawa Heavy Industries", "Mars Liberation Front",
        "Data Rebels", "Void Syndicate", "Church of the Signal", "Steel Vanguard",
        "Ceres Mining Collective", "Titan Separatists", "Belt Free Traders",
        "Lunar Concord", "Apex Biotech", "Neon Circle", "Ghost Fleet",
        "Eclipse Cartel", "Red Meridian", "UEG Security", "Ganymede Scientific",
        "Vesta Commune", "Europa Divers Guild", "Io Refinery Union",
        "Phobos Militia", "Triton Deep Corps", "Enceladus Water Authority",
    ],
    "targets": [
        "Виктор Крейн", "Зара аль-Фарис", "Иван «Молот» Петров", "Рин Куросава",
        "Доктор Мерседес Вальдес", "Марко «Призрак» Чен", "Капитан Орлов",
        "Леди Нова", "Саймон «Крыса» Джонсон", "Аника Танака", "Профессор Вебер",
        "Командор Стил", "Маугли", "Консул Дракон", "Шёпот",
        "Диего Сантос", "Хельга Бьёрк", "Рашид аль-Мустафа", "Юки Сато",
        "Алекс Кондор", "Тень", "Барон Рихтер", "Мамба", "Оракул",
    ],
    "items": [
        "прототип квантового процессора", "ящик нелегальных медикаментов",
        "зашифрованные данные", "контейнер с нанитами", "украденные документы",
        "слиток обогащённого титана", "экспериментальное оружие",
        "образец внеземной ДНК", "нейро-имплант военного класса",
        "антиквариат с Земли", "контейнер со спорами", "партия синтетиков",
        "чёрный ящик с разбитого корабля", "корпоративный архив",
        "кредитные чипы на крупную сумму", "биохимический реагент",
        "ИИ-ядро в транспортном контейнере", "картридж с вакциной",
        "голографическая карта маршрутов", "шпионское оборудование",
    ],
    "locations": [
        "Церера", "Нью-Токио (Марс)", "Олимпус-Сити", "Станция «Хаос»",
        "Пояс Астероидов, сектор Г-3", "Титан, купол Альфа", "Ганимед, лаборатория",
        "Европа, подлёдная база", "Фобос, орбитальная крепость",
        "Веста, коммуна Либре", "Луна, Селена-Прайм", "Ио, рафинировочный завод",
        "Тритон, глубоководный купол", "Энцелад, водозаборная станция",
        "Деймос, ретрансляционный узел", "Паллада, шахтёрский посёлок",
        "Каллисто, тюрьма «Стикс»", "Юнона, свободный порт",
    ],
    "giver_titles": [
        "загадочный посредник", "местный фиксер", "корпоративный агент",
        "старый друг семьи", "анонимный контакт на доске объявлений",
        "отчаявшийся торговец", "военный офицер в отставке", "портовый диспетчер",
        "хакер из даркнета", "пьяный пилот в баре", "нервный учёный",
        "представитель гильдии", "медик из трущоб", "уличный информатор",
    ],
}


# ════════════════════════════════════════════════════════════
#  30 QUEST TEMPLATES
# ════════════════════════════════════════════════════════════

def _qt(type_, titles, descs, stages, comps, skill, credits, xp, danger):
    return {"type": type_, "titles": titles, "descriptions": descs,
            "stages_template": stages, "complications": comps,
            "skill_check": skill, "base_reward_credits": credits,
            "base_reward_xp": xp, "danger": danger}

QUEST_TEMPLATES = [
    _qt("delivery",
        ["Срочная доставка в {destination}", "Груз для {faction}", "Посылка без вопросов", "Экспресс-курьер: {item}", "Доставка под прикрытием"],
        ["Нужно доставить {item} из {origin} в {destination}. Без вопросов.", "{giver} просит отнести {item} для {faction}. Времени мало.", "Таинственная посылка ждёт в {origin}. Получатель — в {destination}. Не вскрывать."],
        ["Забрать {item}", "Добраться до {destination}", "Передать получателю", "Получить оплату"],
        ["ambush", "customs", "rival_courier", "item_dangerous", "recipient_missing"],
        "survival", (1500, 5000), (100, 250), (1, 3)),

    _qt("elimination",
        ["Контракт на {target}", "Тихая зачистка", "Проблема по имени {target}", "Охота на {target}", "Последний контракт"],
        ["{giver} хочет, чтобы {target} перестал быть проблемой.", "{faction} тихо охотится на {target}. Оплата по факту.", "Контракт анонимный: устранить {target} в {destination}."],
        ["Найти информацию о {target}", "Выследить цель", "Устранить {target}", "Подтвердить выполнение"],
        ["target_bodyguards", "innocent_bystanders", "target_is_sympathetic", "double_cross", "law_enforcement"],
        "combat", (5000, 15000), (200, 500), (3, 5)),

    _qt("investigation",
        ["Кто убил {target}?", "Пропавшие данные", "Тайна {destination}", "Запутанное дело", "Следы ведут в {destination}"],
        ["В {origin} произошло нечто странное. {giver} хочет знать правду.", "{target} исчез. Последний раз видели в {destination}.", "Кто-то в {faction} скрывает правду."],
        ["Собрать улики", "Опросить свидетелей", "Проследить связи", "Раскрыть правду"],
        ["false_trail", "witness_scared", "evidence_destroyed", "multiple_suspects", "investigator_becomes_target"],
        "investigation", (2000, 8000), (200, 400), (2, 4)),

    _qt("heist",
        ["Ограбление в {destination}", "Большой куш", "Операция «{item}»", "Хранилище {faction}", "Невозможная кража"],
        ["{giver} собирает команду. Цель — {item} в хранилище {faction}.", "В {destination} — {item}. Охрана лучшая в системе.", "Три уровня защиты, таймер, и {faction} наготове."],
        ["Разведка объекта", "Собрать снаряжение", "Проникнуть внутрь", "Забрать {item}", "Уйти незамеченным"],
        ["alarm_triggered", "guard_patrol", "vault_upgraded", "inside_man_betrays", "rival_crew"],
        "stealth", (8000, 25000), (300, 600), (3, 5)),

    _qt("escort",
        ["Охрана {target}", "Безопасный маршрут", "VIP-сопровождение в {destination}", "Живой груз", "Защитить и доставить"],
        ["{target} нужно в {destination}. Кто-то не хочет этого.", "{faction} перевозит VIP. Нужна дополнительная охрана.", "Свидетель должен выступить в {destination}. По дороге ждут."],
        ["Встретить подопечного", "Спланировать маршрут", "Обеспечить безопасность", "Доставить в {destination}"],
        ["ambush_on_route", "target_panics", "sabotage", "second_attack_wave", "target_has_secret"],
        "combat", (3000, 10000), (150, 350), (2, 4)),

    _qt("hacking",
        ["Взлом {faction}", "Цифровое вторжение", "Операция «Призрак в сети»", "Данные {target}", "Кибератака на {destination}"],
        ["{giver} нужны данные из серверов {faction}.", "В системе {destination} — компромат на {target}.", "Сеть {faction} — крепость. ICE военного класса. Внутри — {item}."],
        ["Найти точку входа", "Обойти ICE", "Извлечь данные", "Замести следы"],
        ["trace_detected", "ice_upgraded", "data_corrupted", "counter_hacker", "physical_security"],
        "hacking", (3000, 12000), (200, 450), (2, 4)),

    _qt("diplomacy",
        ["Перемирие {faction} и {faction2}", "Мирные переговоры", "Посредник в конфликте", "Дипломатическая миссия", "Голос разума"],
        ["{faction} и {faction2} на грани войны. Нужен посредник.", "{giver} верит, что конфликт решается словами.", "На кону — судьба {destination}. Переговоры завтра."],
        ["Встретиться с обеими сторонами", "Выяснить требования", "Найти компромисс", "Закрепить соглашение"],
        ["one_side_lies", "assassination_attempt", "third_party_interference", "deadline_pressure", "past_betrayal"],
        "negotiation", (2000, 8000), (250, 500), (1, 3)),

    _qt("sabotage",
        ["Саботаж на {destination}", "Тихий удар по {faction}", "Вредительство", "Операция «Чёрный день»", "Подрыв изнутри"],
        ["{faction} стала слишком сильной. {giver} хочет подорвать ресурсы.", "Объект в {destination} нужно вывести из строя.", "Реактор, сервера, транспорт — выбери цель."],
        ["Разведка объекта", "Подготовить оборудование", "Проникнуть и заложить", "Уйти до последствий"],
        ["civilians_present", "reinforced_security", "timer_malfunction", "moral_dilemma", "unexpected_allies"],
        "engineering", (4000, 12000), (200, 450), (3, 5)),

    _qt("rescue",
        ["Спасение {target}", "Вызволить из плена", "Операция «Свобода»", "Узник {destination}", "Последний шанс"],
        ["{target} в плену у {faction}. Время на исходе.", "В тюрьме {destination} удерживают человека.", "{giver} умоляет — {target} схвачен, скоро будет поздно."],
        ["Разведать место содержания", "Спланировать операцию", "Вытащить {target}", "Обеспечить эвакуацию"],
        ["hostage_moved", "booby_trap", "hostage_injured", "enemy_reinforcements", "stockholm_syndrome"],
        "combat", (4000, 12000), (200, 500), (3, 5)),

    _qt("exploration",
        ["Неизведанный сектор", "Экспедиция в {destination}", "Первый контакт", "Заброшенная станция", "Тайны {destination}"],
        ["Сканеры засекли аномалию в {destination}. Никто не исследовал.", "Старая карта ведёт к {destination}.", "Заброшенная станция в {destination} передаёт сигнал 30 лет."],
        ["Добраться до точки", "Исследовать окрестности", "Разобраться с находкой", "Вернуться с данными"],
        ["environmental_hazard", "hostile_fauna", "ancient_tech", "cave_in", "rival_expedition"],
        "survival", (2000, 10000), (200, 500), (2, 5)),

    _qt("bounty",
        ["Розыск: {target}", "Живым или мёртвым", "Награда за голову {target}", "Беглец из {origin}", "Охотник за головами"],
        ["{target} в розыске. {faction} предлагает награду.", "Сбежал из-под стражи в {origin}. Замечен в {destination}.", "Этот контракт висит месяц. Три охотника не вернулись."],
        ["Изучить досье", "Выследить в {destination}", "Нейтрализовать", "Доставить доказательство"],
        ["target_has_friends", "target_is_innocent", "rival_hunter", "target_offers_deal", "law_complications"],
        "investigation", (5000, 20000), (250, 500), (3, 5)),

    _qt("smuggling",
        ["Контрабанда для {faction}", "Серый груз", "Чёрный маршрут через {destination}", "Тайный канал", "Невидимый груз"],
        ["{item} нужно провезти мимо патрулей {faction}.", "Таможня {destination} ужесточила контроль. Груз должен пройти.", "{giver} платит втрое — если {item} проедет тихо."],
        ["Получить груз", "Спланировать маршрут", "Пройти патрули", "Передать получателю", "Получить оплату"],
        ["inspection", "informer", "pirate_intercept", "cargo_damaged", "double_payment"],
        "criminal", (4000, 15000), (150, 400), (2, 4)),

    _qt("medical",
        ["Эпидемия в {destination}", "Пациент Зеро", "Спасти {target}", "Лекарство на вес золота", "Карантинная зона"],
        ["В {destination} вспышка неизвестной болезни.", "{target} отравлен. Антидот только в {destination}.", "{faction} скрывает масштаб эпидемии."],
        ["Диагностировать", "Найти лекарство", "Применить лечение", "Предотвратить распространение"],
        ["contamination_risk", "corporate_coverup", "patient_dies", "mutation", "quarantine"],
        "medicine", (2000, 8000), (200, 500), (2, 4)),

    _qt("trade",
        ["Торговая сделка века", "Дефицит в {destination}", "Посредник между мирами", "Выгодный контракт", "Торговый маршрут"],
        ["В {destination} дефицит {item}. Кто привезёт — озолотится.", "{faction} ищет посредника для закупки {item}.", "Торговая война между {origin} и {destination}."],
        ["Найти товар", "Договориться о цене", "Организовать доставку", "Закрыть сделку"],
        ["price_crash", "counterfeit_goods", "trade_war", "pirate_tax", "guild_politics"],
        "negotiation", (3000, 20000), (100, 300), (1, 3)),

    _qt("survival",
        ["Катастрофа в {destination}", "Выжить любой ценой", "Авария на станции", "SOS из {destination}", "Последние часы"],
        ["Станция {destination} терпит крушение.", "Авария отрезала сектор. Кислорода на часы.", "Сигнал SOS из {destination}. Спасатели не успевают."],
        ["Добраться до места", "Оценить ситуацию", "Спасти выживших", "Эвакуироваться"],
        ["aftershock", "trapped_survivors", "resource_shortage", "looters", "structural_collapse"],
        "survival", (2000, 8000), (200, 500), (3, 5)),

    # ═══════════ NEW 15 TEMPLATES ═══════════

    _qt("convoy_raid",
        ["Перехват конвоя {faction}", "Груз нельзя упустить", "Засада на трассе", "Пиратский налёт", "Караван на восток"],
        ["Конвой {faction} везёт {item}. Маршрут известен.", "{giver} хочет перехватить поставку через {destination}.", "Три грузовика, два эскорта. Внутри — {item}."],
        ["Разведать маршрут", "Подготовить засаду", "Атаковать конвой", "Забрать груз", "Скрыться"],
        ["military_escort", "decoy_convoy", "ambush_reversed", "cargo_booby_trapped", "reinforcements_called"],
        "combat", (6000, 20000), (200, 500), (4, 5)),

    _qt("prison_break",
        ["Побег из {destination}", "Операция «Каллисто»", "Взлом тюремного блока", "Свобода для {target}", "Сломать клетку"],
        ["{target} сидит в тюрьме {destination}. Законных способов нет.", "{giver} платит за побег заключённого.", "Тюрьма неприступна. Но у каждой крепости есть слабость."],
        ["Изучить план тюрьмы", "Найти слабое место", "Проникнуть", "Найти {target}", "Вывести наружу"],
        ["lockdown", "guard_rotation_changed", "target_refuses", "warden_alerted", "riot_breaks_out"],
        "stealth", (8000, 25000), (300, 600), (4, 5)),

    _qt("artifact_recovery",
        ["Артефакт Предтеч", "Древняя технология", "Находка в {destination}", "Реликвия забытой эры", "Сигнал из глубины"],
        ["Обнаружена технология неизвестного происхождения.", "На {destination} найден артефакт. {faction} отправляет команду.", "{giver} получил координаты древнего объекта."],
        ["Добраться до места", "Обследовать объект", "Извлечь артефакт", "Изучить / продать"],
        ["alien_defense", "reality_distortion", "competing_team", "artifact_is_alive", "containment_failure"],
        "science", (5000, 30000), (300, 700), (3, 5)),

    _qt("corporate_espionage",
        ["Корпоративный шпионаж", "Двойная игра", "Крот в {faction}", "Тайная операция", "Информация — оружие"],
        ["{faction2} нанимает для внедрения в {faction}.", "Промышленный шпионаж: {item} — разработка {faction}.", "Стань кротом. Устройся в {faction}, узнай планы."],
        ["Создать легенду", "Внедриться в {faction}", "Найти секреты", "Передать информацию", "Выйти без подозрений"],
        ["cover_blown", "counter_intel", "double_agent", "falling_for_enemy", "blackmail"],
        "negotiation", (5000, 20000), (250, 600), (3, 5)),

    _qt("gladiator",
        ["Арена {destination}", "Кровавый спорт", "Чемпион нужен", "Подпольные бои", "Турнир на выживание"],
        ["Подпольная арена в {destination}. Победитель забирает всё.", "{giver} организует турнир. Пять бойцов, один выход.", "Чемпион арены — {target}. Его никто не побеждал."],
        ["Записаться на турнир", "Победить в отборочных", "Выиграть полуфинал", "Финальный бой"],
        ["rigged_fight", "poison_before_match", "crowd_turns_hostile", "champion_cheats", "bet_gone_wrong"],
        "combat", (3000, 15000), (200, 500), (3, 5)),

    _qt("propaganda",
        ["Война за умы", "Голос {faction}", "Дезинформация", "Пропаганда в {destination}", "Смена нарратива"],
        ["{faction} хочет изменить мнение в {destination}.", "Распространить информацию против {faction2}.", "{giver} верит, что слово сильнее пули."],
        ["Изучить аудиторию", "Подготовить материалы", "Распространить", "Оценить эффект"],
        ["counter_propaganda", "arrested_for_sedition", "source_exposed", "backfire", "viral_effect"],
        "negotiation", (2000, 8000), (150, 400), (1, 3)),

    _qt("mutant_hunt",
        ["Охота на мутанта", "Тварь из тоннелей", "Зачистка сектора", "Монстр {destination}", "Выродки"],
        ["Что-то убивает людей в тоннелях {destination}.", "Эксперименты {faction} вышли из-под контроля.", "Тварь нападает ночью. Никто не выживал."],
        ["Собрать информацию", "Выследить", "Подготовить ловушку", "Уничтожить или поймать"],
        ["multiple_creatures", "creature_intelligent", "lab_origin", "civilian_casualties", "creature_sympathetic"],
        "combat", (3000, 12000), (200, 500), (3, 5)),

    _qt("cult_investigation",
        ["Секта Сигнала", "Культ в {destination}", "Пропавшие верующие", "Голос из пустоты", "Ложные пророки"],
        ["Люди исчезают. Связь с культом в {destination}.", "{giver} потерял близкого — ушёл к сектантам.", "Культ растёт. Лидер — {target}. Что скрывают?"],
        ["Внедриться в культ", "Завоевать доверие", "Узнать цель", "Решить: уничтожить или раскрыть"],
        ["brainwashing", "leader_has_powers", "infiltrator_discovered", "members_willing", "cosmic_truth"],
        "investigation", (3000, 10000), (250, 600), (2, 5)),

    _qt("undercover",
        ["Под прикрытием", "Чужая шкура", "Крот", "Две жизни", "Игра теней"],
        ["{faction2} нужен агент внутри {faction}.", "Внедрись в банду {target}. Узнай планы.", "Долгая операция: стать своим среди чужих."],
        ["Принять легенду", "Войти в доверие", "Получить доступ к секретам", "Передать информацию", "Безопасно выйти"],
        ["loyalty_test", "cover_nearly_blown", "genuine_friendship", "asked_to_kill", "handler_compromised"],
        "criminal", (5000, 18000), (300, 600), (3, 5)),

    _qt("debt_collection",
        ["Долг платежом красен", "Коллектор", "Счёт для {target}", "Неоплаченные услуги", "Кредитная линия закрыта"],
        ["{target} должен {faction} крупную сумму.", "{giver} устал ждать. {target} в {destination}.", "Найти {target}, получить деньги. Метод — на выбор."],
        ["Найти должника", "Объяснить ситуацию", "Получить деньги", "Вернуть заказчику"],
        ["debtor_broke", "debtor_dangerous", "sob_story", "third_party_debt", "debtor_has_dirt"],
        "negotiation", (2000, 8000), (100, 300), (2, 4)),

    _qt("protection",
        ["Крыша для {destination}", "Безопасность стоит денег", "Защита района", "Сторожевой пёс", "Местная безопасность"],
        ["Торговцы {destination} нуждаются в защите.", "{giver} открыл бизнес, нужно отпугнуть вымогателей.", "Район под контролем банды. Жители скидываются."],
        ["Осмотреть район", "Установить маршрут", "Разобраться с угрозами", "Долгосрочная безопасность"],
        ["bigger_gang_arrives", "client_is_criminal", "police_interference", "protection_war", "moral_gray"],
        "combat", (1500, 5000), (100, 250), (2, 4)),

    _qt("rebellion",
        ["Восстание в {destination}", "Свобода или смерть", "Искра революции", "Голос угнетённых", "Под знаменем свободы"],
        ["Народ {destination} устал от {faction}. Нужна искра.", "{giver} возглавляет подполье. Нужны ресурсы и боец.", "{faction} душит {destination}. Повстанцы готовы."],
        ["Связаться с подпольем", "Организовать ресурсы", "Подготовить восстание", "Час Х", "Удержать позиции"],
        ["traitor_in_ranks", "civilian_casualties", "faction_reinforcements", "moral_ambiguity", "pyrrhic_victory"],
        "survival", (3000, 10000), (300, 700), (4, 5)),

    _qt("salvage",
        ["Спасение обломков", "Мёртвый корабль", "Добыча среди руин", "Сигнал разбитого судна", "Кладбище кораблей"],
        ["Обломки дрейфуют в {destination}. Внутри может быть {item}.", "Грузовоз {faction} потерпел крушение. Кто найдёт — тот хозяин.", "На кладбище кораблей есть судно с ценным грузом."],
        ["Найти обломки", "Проникнуть на борт", "Обследовать отсеки", "Извлечь ценное", "Вернуться"],
        ["hull_breach", "automated_defense", "other_scavengers", "ship_not_empty", "radiation_leak"],
        "engineering", (3000, 15000), (150, 400), (2, 4)),

    _qt("terraforming",
        ["Проект терраформирования", "Зелёный Марс", "Дыхание жизни", "Генератор атмосферы", "Новый рубеж"],
        ["Проект на {destination} нуждается в специалистах.", "{faction} запускает генератор атмосферы. Что-то не так.", "Последний шанс сделать {destination} обитаемым."],
        ["Прибыть на объект", "Диагностировать", "Починить оборудование", "Запустить систему"],
        ["sabotage_suspected", "toxic_atmosphere", "native_organism", "equipment_failure", "rival_project"],
        "science", (4000, 15000), (200, 500), (2, 4)),

    _qt("courier_war",
        ["Гонка курьеров", "Первым доставит", "Конкуренция доставки", "Быстрее пули", "Перехвати посылку"],
        ["Два заказчика, одна посылка. Кто первым.", "{faction} и {faction2} отправили курьеров за {item}.", "Гонка через полсистемы. Приз — контракт с {faction}."],
        ["Получить задание", "Обогнать конкурентов", "Преодолеть препятствия", "Доставить первым"],
        ["rival_sabotage", "route_blocked", "space_storm", "double_cross", "third_party_theft"],
        "piloting", (2000, 10000), (150, 350), (2, 4)),
]


# ════════════════════════════════════════════════════════════
#  25 WORLD EVENT TEMPLATES — the living world
# ════════════════════════════════════════════════════════════

WORLD_EVENT_TEMPLATES = {
    "faction_war": [
        "{f1} объявляет войну {f2}. Бои вспыхивают по всему Поясу.",
        "Вооружённый конфликт между {f1} и {f2} в секторе {loc}.",
        "Эскалация: {f1} атаковала аванпост {f2}.",
        "{f1} и {f2} вступили в конфликт из-за контроля над {loc}.",
    ],
    "faction_alliance": [
        "{f1} и {f2} подписали пакт о взаимопомощи.",
        "Альянс: {f1} объединяется с {f2} против общей угрозы.",
        "{f1} предоставляет {f2} базы в обмен на ресурсы.",
    ],
    "faction_betrayal": [
        "{f1} нарушает договор с {f2}. Доверие разрушено.",
        "Предательство: {f1} передала секреты {f2} третьей стороне.",
        "Скандал: посол {f1} пойман на шпионаже против {f2}.",
    ],
    "economic_crisis": [
        "Крах фондового рынка {loc}. Цены на {goods} взлетели втрое.",
        "Дефицит {goods} по всей системе. Паника в торговых хабах.",
        "{f1} ввела эмбарго на {goods}. Чёрный рынок процветает.",
        "Гиперинфляция в {loc}: кредиты обесцениваются.",
        "Банкротство крупнейшего банка {loc}.",
    ],
    "economic_boom": [
        "Открытие ресурсов в {loc} — золотая лихорадка!",
        "{f1} заключила мегаконтракт на {goods}. Акции взлетели.",
        "Торговый бум в {loc}: цены на {goods} падают, изобилие.",
    ],
    "epidemic": [
        "Вспышка вируса «Нова-7» в {loc}. Введён карантин.",
        "Эпидемия синтетической чумы: {loc} изолирована.",
        "Заражение жизнеобеспечения в {loc}. Тысячи больных.",
    ],
    "political_coup": [
        "Переворот в {loc}: {f1} свергает правительство.",
        "Военный путч: генералы {f1} захватили {loc}.",
        "Тихая революция: новое правительство {loc} лояльно {f1}.",
    ],
    "political_election": [
        "Выборы в {loc}: кандидат {f1} против кандидата {f2}.",
        "Скандал на выборах в {loc}: обвинения в фальсификации.",
        "Новый мэр {loc} объявляет курс на сближение с {f1}.",
    ],
    "technology_breakthrough": [
        "Прорыв {f1}: прототип квантового двигателя.",
        "Учёные {loc} открыли новый элемент.",
        "{f1} представила клонирование памяти. Этические дебаты.",
        "Новый тип брони из {loc} — революция в военном деле.",
    ],
    "technology_disaster": [
        "Катастрофа ИИ: система {loc} вышла из-под контроля.",
        "Утечка нанитов {f1}: район {loc} заражён.",
        "Сбой квантовой сети: связь в {loc} потеряна на 48 часов.",
    ],
    "natural_disaster": [
        "Солнечная буря накрыла {loc}. Электроника сбоит.",
        "Метеоритный дождь угрожает {loc}. Эвакуация.",
        "Разгерметизация купола в {loc}: экстренное оповещение.",
        "Тектоника на {loc}: трещины в жилых секторах.",
        "Солнечная вспышка X: корабли в секторе {loc} лежат в дрейфе.",
    ],
    "pirate_raid": [
        "Пиратский флот атакует маршруты вблизи {loc}.",
        "Рейдеры {f1} грабят транспорты у {loc}.",
        "Масштабный пиратский налёт: {loc} в осаде.",
    ],
    "crime_wave": [
        "Волна преступности в {loc}: ограбления и убийства.",
        "Наркокартель {f1} расширяется в {loc}. Полиция бессильна.",
        "Серийный убийца терроризирует {loc}.",
        "Кибератаки на банки {loc}. Миллионы украдены.",
        "Банды делят территории {loc}.",
    ],
    "rebellion_event": [
        "Восстание рабочих на {loc}: шахтёры требуют условий.",
        "Протесты в {loc} против {f1}. Баррикады и столкновения.",
        "{f2} поддерживает повстанцев в {loc} против {f1}.",
    ],
    "refugee_crisis": [
        "Поток беженцев из {loc} после конфликта {f1} и {f2}.",
        "Тысячи беженцев прибывают в {loc}. Ресурсы на исходе.",
        "Гуманитарный кризис: беженцы заполняют {loc}.",
    ],
    "labor_strike": [
        "Всеобщая забастовка в {loc}: транспорт остановлен.",
        "Шахтёры {loc} бастуют против {f1}.",
        "Портовая забастовка в {loc}: торговля парализована.",
    ],
    "ai_incident": [
        "ИИ-управляющий {loc} отказывается выполнять приказы.",
        "Массовый сбой дронов-охранников в {loc}: атакуют людей.",
        "ИИ {f1} объявляет себя разумным и требует прав.",
    ],
    "resource_discovery": [
        "Богатая жила руды в секторе {loc}. Гонка началась.",
        "Водяной лёд рядом с {loc}: ценнейший ресурс.",
        "Залежи на {loc}: {f1} и {f2} снаряжают экспедиции.",
    ],
    "military_exercise": [
        "{f1} проводит учения у {loc}. Напряжённость растёт.",
        "Военный флот {f1} входит в нейтральный сектор. {f2} протестует.",
        "Оружейные испытания {f1} в {loc}: маршруты нарушены.",
    ],
    "tournament": [
        "Межпланетный турнир бойцов в {loc}.",
        "Гонки через астероидное поле: призовой фонд — {goods}.",
        "Хакерский чемпионат в {loc}.",
    ],
    "celebrity_event": [
        "Знаменитый пилот {target} объявляет рекордный перелёт.",
        "Политик {loc} пойман на коррупции.",
        "Свадьба наследников {f1} и {f2}: возможный альянс?",
    ],
    "smuggling_ring": [
        "Раскрыта контрабандная сеть в {loc}: {goods} под носом у властей.",
        "{f1} усиливает патрули в {loc}.",
        "Новый маршрут контрабанды {goods} через {loc}.",
    ],
    "migration_wave": [
        "Переселение в {loc}: население выросло на 30%.",
        "Исход из {loc}: люди бегут от {f1}.",
        "Колонисты основывают поселение рядом с {loc}.",
    ],
    "scientific_expedition": [
        "Экспедиция к границе системы стартует с {loc}.",
        "{f1} отправляет исследовательский корабль в неизученный сектор.",
        "Аномалия в {loc}: научная экспедиция ищет ответы.",
    ],
    "black_market_event": [
        "Новый чёрный рынок в трущобах {loc}: всё за цену.",
        "Облава на чёрный рынок {loc}: торговцы в панике.",
        "{f1} контролирует чёрный рынок {loc}: «защита» за долю.",
    ],
}

WORLD_EVENT_VARS = {
    "corps": QUEST_VARIABLES["factions"][:19],
    "goods": [
        "водяной лёд", "обогащённый титан", "медикаменты", "боеприпасы",
        "продовольствие", "квантовые процессоры", "топливные стержни",
        "кислородные картриджи", "нейро-имплантаты", "редкоземельные элементы",
        "стимуляторы", "генетический материал", "антиматерия",
        "живые организмы", "шифровальные ключи",
    ],
    "locs": QUEST_VARIABLES["locations"][:16],
    "targets": QUEST_VARIABLES["targets"][:8],
}


# ════════════════════════════════════════════════════════════
#  PROCEDURAL QUEST GENERATOR
# ════════════════════════════════════════════════════════════

class ProceduralQuestGenerator:
    def __init__(self):
        self.generated_count = 0
        self.recent_types = []
        self.quest_history_ids = set()

    def generate_quest(self, player_level: int = 1, location: Dict = None,
                       preferred_type: str = None, faction_standings: Dict = None) -> Dict:
        """Generate a procedural quest appropriate for player."""
        if preferred_type:
            templates = [t for t in QUEST_TEMPLATES if t["type"] == preferred_type]
        else:
            templates = [t for t in QUEST_TEMPLATES if t["type"] not in self.recent_types[-5:]]
            if not templates:
                templates = list(QUEST_TEMPLATES)

        template = random.choice(templates)
        self.recent_types.append(template["type"])
        if len(self.recent_types) > 10:
            self.recent_types = self.recent_types[-10:]

        quest = self._fill_variables(template, location, faction_standings)

        level_mult = 1 + (player_level - 1) * 0.25
        cr_min, cr_max = template["base_reward_credits"]
        xp_min, xp_max = template["base_reward_xp"]
        quest["reward_credits"] = int(random.randint(cr_min, cr_max) * level_mult)
        quest["reward_xp"] = int(random.randint(xp_min, xp_max) * level_mult)

        d_min, d_max = template["danger"]
        quest["danger_level"] = min(5, random.randint(d_min, d_max) + player_level // 3)

        if random.random() < 0.5 and template.get("complications"):
            quest["complication"] = random.choice(template["complications"])
        else:
            quest["complication"] = None

        quest["skill_check"] = template["skill_check"]
        quest["type"] = template["type"]
        quest["generated"] = True
        quest["turn_created"] = 0

        self.generated_count += 1
        quest["id"] = f"proc_quest_{self.generated_count}_{int(time.time()) % 10000}"
        self.quest_history_ids.add(quest["id"])
        return quest

    def generate_quest_chain(self, player_level: int = 1, chain_length: int = 3,
                             location: Dict = None) -> List[Dict]:
        """Generate a multi-quest chain with escalating stakes."""
        chain = []
        chain_types = random.sample(
            [t["type"] for t in QUEST_TEMPLATES if t["danger"][1] >= 3],
            min(chain_length, 5)
        )
        chain_id = f"chain_{int(time.time()) % 10000}"
        for i, qtype in enumerate(chain_types[:chain_length]):
            q = self.generate_quest(player_level=player_level + i, location=location, preferred_type=qtype)
            q["chain_id"] = chain_id
            q["chain_step"] = i + 1
            q["chain_total"] = chain_length
            q["reward_credits"] = int(q["reward_credits"] * (1 + i * 0.3))
            q["reward_xp"] = int(q["reward_xp"] * (1 + i * 0.3))
            chain.append(q)
        return chain

    def _fill_variables(self, template: Dict, location: Dict = None,
                        faction_standings: Dict = None) -> Dict:
        vars_ = {
            "faction": random.choice(QUEST_VARIABLES["factions"]),
            "faction2": random.choice(QUEST_VARIABLES["factions"]),
            "target": random.choice(QUEST_VARIABLES["targets"]),
            "item": random.choice(QUEST_VARIABLES["items"]),
            "origin": location["name"] if location and "name" in location else random.choice(QUEST_VARIABLES["locations"]),
            "destination": random.choice(QUEST_VARIABLES["locations"]),
            "giver": random.choice(QUEST_VARIABLES["giver_titles"]),
        }
        while vars_["faction2"] == vars_["faction"]:
            vars_["faction2"] = random.choice(QUEST_VARIABLES["factions"])
        while vars_["destination"] == vars_["origin"]:
            vars_["destination"] = random.choice(QUEST_VARIABLES["locations"])

        title = random.choice(template["titles"])
        desc = random.choice(template["descriptions"])
        for k, v in vars_.items():
            title = title.replace("{" + k + "}", v)
            desc = desc.replace("{" + k + "}", v)

        stages = []
        for s in template["stages_template"]:
            for k, v in vars_.items():
                s = s.replace("{" + k + "}", v)
            stages.append({"description": s, "completed": False})

        return {"title": title, "description": desc, "stages": stages, "variables": vars_}

    def on_quest_complete(self, quest_type: str):
        pass

    def get_prompt_context(self) -> str:
        return f"[Процедурный генератор: {self.generated_count} квестов, {len(QUEST_TEMPLATES)} шаблонов]"


# ════════════════════════════════════════════════════════════
#  WORLD TICKER — living world simulation
# ════════════════════════════════════════════════════════════

class WorldTicker:
    def __init__(self):
        self.active_events: List[Dict] = []
        self.event_history: List[Dict] = []
        self.faction_tensions: Dict[str, float] = {}
        self.active_wars: List[Dict] = []
        self.active_crises: List[Dict] = []
        self.turn_counter = 0
        self.event_id_counter = 0
        # V4: time-based tiered event manager
        self._tiered_manager = None
        self._last_legacy_hours = 0  # cooldown for legacy events too

    def _get_tiered_manager(self):
        if self._tiered_manager is None:
            from src.content.v4_legacy import TieredEventManager
            self._tiered_manager = TieredEventManager()
        return self._tiered_manager

    def _extract_player_data(self, game_state) -> Dict:
        """Extract player data from game_state for trigger checking."""
        if game_state is None:
            return {"level": 1, "credits": 0, "skills": {}, "attributes": {},
                    "faction_rep": {}, "inventory": []}
        char = getattr(game_state, 'character', {}) or {}
        skills = char.get("skills", {})
        attrs = char.get("attributes", {})
        faction_rep = getattr(game_state, 'faction_reputation', {}) or {}
        inventory = getattr(game_state, 'inventory', []) or []
        return {
            "level": char.get("level", 1),
            "credits": char.get("credits", 0),
            "skills": skills,
            "attributes": attrs,
            "faction_rep": faction_rep,
            "inventory": inventory,
        }

    def tick(self, game_state) -> List[Dict]:
        self.turn_counter += 1
        events = []
        game_time = getattr(game_state, 'game_time', None) or {"year": 2387, "month": 3, "day": 15, "hour": 8}

        # === LEGACY template events (also cooldown-based now) ===
        from src.content.v4_legacy import _game_time_to_hours
        current_hours = _game_time_to_hours(game_time)
        legacy_elapsed = current_hours - self._last_legacy_hours

        # Legacy minor: every ~2 weeks game time (336h), not every 3-6 turns
        if legacy_elapsed >= random.randint(240, 504):
            ev = self._generate_event("minor", game_state)
            if ev:
                events.append(ev)
                self._last_legacy_hours = current_hours

        # Legacy major: every ~2-4 months (1440-2880h)
        if legacy_elapsed >= random.randint(1440, 2880):
            ev = self._generate_event("major", game_state)
            if ev:
                events.append(ev)

        # Legacy critical: every ~6-12 months (4320-8760h)
        if legacy_elapsed >= random.randint(4320, 8760):
            ev = self._generate_event("critical", game_state)
            if ev:
                events.append(ev)

        # === V4: Tiered event (time + trigger based) ===
        player = self._extract_player_data(game_state)
        manager = self._get_tiered_manager()
        tiered_ev = manager.try_generate_event(game_time, player)
        if tiered_ev:
            # Fill in template variables
            vp = WORLD_EVENT_VARS
            text = tiered_ev.get("text", "")
            f1 = random.choice(vp["corps"])
            f2 = random.choice([c for c in vp["corps"] if c != f1])
            loc = random.choice(vp["locs"])
            goods = random.choice(vp["goods"])
            text = text.replace("{f1}", f1).replace("{f2}", f2).replace("{loc}", loc).replace("{goods}", goods)

            self.event_id_counter += 1
            tier = tiered_ev.get("tier", 8)
            sev_map = {1: 3, 2: 3, 3: 2, 4: 2, 5: 1, 6: 1, 7: 1, 8: 0}

            events.append({
                "id": f"te_{self.event_id_counter}_{tier}",
                "turn": self.turn_counter,
                "category": f"tier_{tier}_{tiered_ev.get('tier_name', '')}",
                "severity_level": tiered_ev.get("tier_name", ""),
                "text": text,
                "severity": sev_map.get(tier, 1),
                "tier": tier,
                "tier_name": tiered_ev.get("tier_name", ""),
                "factions_involved": [f1, f2] if tier <= 4 else [],
                "location": loc,
                "duration": tiered_ev.get("duration_days", 1),
                "resolved": False,
                "quest_hook": tiered_ev.get("quest_hook"),
                "effects": tiered_ev.get("effects", {}),
            })

        self._update_tensions()
        war = self._check_faction_conflicts(game_state)
        if war: events.append(war)
        self._resolve_crises()

        for e in events:
            self.active_events.append(e)
            self.event_history.append(e)
        if len(self.active_events) > 20:
            self.active_events = self.active_events[-20:]

        return events

    def _generate_event(self, severity: str, game_state) -> Optional[Dict]:
        if severity == "minor":
            types = ["economic_boom", "crime_wave", "celebrity_event", "smuggling_ring",
                     "tournament", "labor_strike", "black_market_event", "migration_wave"]
        elif severity == "major":
            types = ["faction_war", "faction_alliance", "faction_betrayal", "economic_crisis",
                     "epidemic", "pirate_raid", "rebellion_event", "technology_breakthrough",
                     "resource_discovery", "refugee_crisis", "political_election", "scientific_expedition"]
        else:
            types = ["political_coup", "natural_disaster", "ai_incident", "technology_disaster",
                     "military_exercise", "faction_war"]

        event_type = random.choice(types)
        templates = WORLD_EVENT_TEMPLATES.get(event_type, [])
        if not templates: return None

        text = random.choice(templates)
        vp = WORLD_EVENT_VARS
        f1 = random.choice(vp["corps"])
        f2 = random.choice([c for c in vp["corps"] if c != f1])
        loc = random.choice(vp["locs"])
        goods = random.choice(vp["goods"])
        target = random.choice(vp["targets"])
        text = text.replace("{f1}", f1).replace("{f2}", f2).replace("{loc}", loc).replace("{goods}", goods).replace("{target}", target)

        self.event_id_counter += 1
        sev_num = {"minor": 1, "major": 2, "critical": 3}[severity]

        event = {
            "id": f"we_{self.event_id_counter}_{int(time.time()) % 1000}",
            "turn": self.turn_counter, "category": event_type, "severity_level": severity,
            "text": text, "severity": sev_num, "factions_involved": [f1, f2],
            "location": loc, "duration": random.randint(3, 15), "resolved": False,
            "quest_hook": sev_num >= 2, "effects": self._gen_effects(event_type, sev_num),
        }
        if sev_num >= 2: self.active_crises.append(event)
        return event

    def _gen_effects(self, event_type: str, severity: int) -> Dict:
        e = {}
        if "crisis" in event_type: e["price_modifier"] = random.uniform(0.5, 0.8)
        elif "boom" in event_type: e["price_modifier"] = random.uniform(1.2, 1.8)
        if event_type in ("faction_war", "pirate_raid", "rebellion_event"):
            e["danger_increase"] = severity; e["trade_disrupted"] = True
        if event_type == "epidemic": e["medical_demand"] = True; e["movement_restricted"] = True
        if event_type == "technology_breakthrough": e["new_items_available"] = True
        if event_type == "crime_wave": e["theft_chance"] = 0.1 * severity
        if event_type in ("labor_strike", "rebellion_event"): e["services_disrupted"] = True
        if event_type == "resource_discovery": e["price_modifier"] = 0.7; e["rush"] = True
        return e

    def _resolve_crises(self):
        for c in self.active_crises[:]:
            c["duration"] -= 1
            if c["duration"] <= 0:
                c["resolved"] = True
                self.active_crises.remove(c)
                if random.random() < 0.3:
                    self.active_events.append({
                        "id": f"we_aft_{c['id']}", "turn": self.turn_counter,
                        "category": "aftermath", "text": f"Последствия: {c['text'][:60]}... стабилизация.",
                        "severity": 1, "factions_involved": c["factions_involved"],
                        "location": c["location"], "duration": 5, "resolved": False,
                        "quest_hook": False, "effects": {},
                    })

    def _update_tensions(self):
        corps = WORLD_EVENT_VARS["corps"]
        if random.random() < 0.2:
            f1, f2 = random.sample(corps, 2)
            key = f"{f1}_vs_{f2}"
            cur = self.faction_tensions.get(key, 50)
            self.faction_tensions[key] = max(0, min(100, cur + random.randint(-10, 15)))

    def _check_faction_conflicts(self, game_state) -> Optional[Dict]:
        for key, tension in list(self.faction_tensions.items()):
            if tension >= 90 and key not in [w.get("key") for w in self.active_wars]:
                parts = key.split("_vs_")
                if len(parts) != 2: continue
                f1, f2 = parts
                self.active_wars.append({"key": key, "factions": [f1, f2], "turn_started": self.turn_counter})
                templates = WORLD_EVENT_TEMPLATES.get("faction_war", [])
                text = random.choice(templates) if templates else f"{f1} и {f2} вступили в войну!"
                text = text.replace("{f1}", f1).replace("{f2}", f2).replace("{loc}", random.choice(WORLD_EVENT_VARS["locs"]))
                self.event_id_counter += 1
                return {
                    "id": f"war_{self.event_id_counter}", "turn": self.turn_counter,
                    "category": "faction_war_outbreak", "text": text, "severity": 3,
                    "factions_involved": [f1, f2], "location": random.choice(WORLD_EVENT_VARS["locs"]),
                    "duration": random.randint(10, 30), "resolved": False, "quest_hook": True,
                    "effects": {"danger_increase": 3, "trade_disrupted": True, "faction_war": True},
                }
            if tension < 30 and key in [w.get("key") for w in self.active_wars]:
                self.active_wars = [w for w in self.active_wars if w["key"] != key]
                self.faction_tensions[key] = 25
        return None

    def get_prompt_context(self) -> str:
        if not self.active_events and not self.active_wars: return ""
        parts = ["## МИРОВЫЕ СОБЫТИЯ:"]
        for e in self.active_events[-5:]:
            icon = {"minor": "📰", "major": "⚠️", "critical": "🔴"}.get(e.get("severity_level", "minor"), "📌")
            parts.append(f"{icon} {e['text']}")
        if self.active_wars:
            parts.append("\n### АКТИВНЫЕ ВОЙНЫ:")
            for w in self.active_wars:
                parts.append(f"⚔️ {w['factions'][0]} vs {w['factions'][1]} (ход {w['turn_started']})")
        if self.active_crises:
            parts.append(f"\n### АКТИВНЫЕ КРИЗИСЫ ({len(self.active_crises)}):")
            for c in self.active_crises[:3]:
                parts.append(f"🆘 {c['text'][:80]}...")
        return "\n".join(parts)


# ════════════════════════════════════════════════════════════
#  CONSEQUENCE TRACKER
# ════════════════════════════════════════════════════════════

class ConsequenceTracker:
    CONSEQUENCE_TEMPLATES = {
        "killed_npc": [
            {"text": "Знакомый {target} ищет мести. Наёмники на хвосте.", "effect": "bounty", "severity": 3, "delay": 5},
            {"text": "Слухи о гибели {target} распространяются.", "effect": "reputation", "severity": 2, "delay": 3},
            {"text": "{faction} назначает награду за убийцу {target}.", "effect": "wanted", "severity": 3, "delay": 4},
        ],
        "helped_faction": [
            {"text": "{faction} помнит добро. Новые возможности.", "effect": "opportunity", "severity": 1, "delay": 3},
            {"text": "Контакт в {faction} предлагает эксклюзивный контракт.", "effect": "quest", "severity": 1, "delay": 5},
        ],
        "betrayed_faction": [
            {"text": "{faction} посылает ликвидаторов.", "effect": "ambush", "severity": 4, "delay": 4},
            {"text": "Счета заморожены: {faction} использует связи.", "effect": "economic_penalty", "severity": 3, "delay": 3},
            {"text": "Информатор {faction} сливает местоположение.", "effect": "exposed", "severity": 2, "delay": 6},
        ],
        "got_rich": [
            {"text": "Воры заметили твоё состояние.", "effect": "theft_attempt", "severity": 2, "delay": 4},
            {"text": "Налоговая интересуется доходами.", "effect": "investigation", "severity": 2, "delay": 7},
        ],
        "high_notoriety": [
            {"text": "Репортёры преследуют. Анонимность потеряна.", "effect": "fame", "severity": 2, "delay": 3},
            {"text": "Корпорации рассматривают тебя как угрозу.", "effect": "surveillance", "severity": 3, "delay": 5},
        ],
        "completed_major_quest": [
            {"text": "Успех привлекает клиентов. Предложения сыплются.", "effect": "quest_offers", "severity": 1, "delay": 2},
            {"text": "Твоё имя на слуху. Фракции хотят завербовать.", "effect": "recruitment", "severity": 1, "delay": 4},
        ],
        "stole_item": [
            {"text": "Владелец обнаружил пропажу. Детективы ищут.", "effect": "investigation", "severity": 2, "delay": 5},
            {"text": "Краденое опознано. Торговцы осторожничают.", "effect": "trade_penalty", "severity": 2, "delay": 3},
        ],
        "saved_civilians": [
            {"text": "Местные благодарны. Скидки и поддержка.", "effect": "local_support", "severity": 1, "delay": 2},
            {"text": "СМИ: ты — народный герой.", "effect": "fame_positive", "severity": 1, "delay": 3},
        ],
        "destroyed_property": [
            {"text": "Счёт за ущерб от корпорации.", "effect": "fine", "severity": 2, "delay": 4},
            {"text": "Полиция ищет виновника разрушений.", "effect": "wanted_minor", "severity": 2, "delay": 3},
        ],
        "hacked_system": [
            {"text": "Контр-хакеры отследили. Они знают.", "effect": "counter_hack", "severity": 3, "delay": 4},
            {"text": "Данные оказались подсадкой. Вирус в системе.", "effect": "virus", "severity": 3, "delay": 2},
        ],
        "made_deal_with_criminal": [
            {"text": "«Партнёр» шантажирует: плати или информация утечёт.", "effect": "blackmail", "severity": 3, "delay": 6},
            {"text": "Связь с преступником замечена. Доверие падает.", "effect": "reputation_loss", "severity": 2, "delay": 4},
        ],
        "refused_quest": [
            {"text": "Заказчик нашёл другого. Но память длинная.", "effect": "grudge", "severity": 1, "delay": 8},
            {"text": "Нерешённая проблема разрослась. Последствия.", "effect": "world_impact", "severity": 2, "delay": 5},
        ],
        "explored_unknown": [
            {"text": "Находка привлекла учёных. Приглашение.", "effect": "opportunity_science", "severity": 1, "delay": 3},
            {"text": "Координаты утекли. Конкуренты в пути.", "effect": "competition", "severity": 2, "delay": 4},
        ],
        "used_violence_public": [
            {"text": "Видео драки в сети. Полиция ищет.", "effect": "wanted_minor", "severity": 2, "delay": 2},
            {"text": "Свидетели дали показания. Штраф или арест.", "effect": "fine_or_arrest", "severity": 2, "delay": 3},
        ],
        "corrupted_official": [
            {"text": "Чиновник хочет ещё денег. Шантаж.", "effect": "blackmail", "severity": 3, "delay": 5},
            {"text": "Проверка обнаружила нарушения. Указывают на тебя.", "effect": "investigation", "severity": 3, "delay": 7},
        ],
    }

    def __init__(self):
        self.pending: List[Dict] = []
        self.triggered: List[Dict] = []
        self.action_log: List[Dict] = []

    def log_action(self, action_type: str, details: Dict):
        self.action_log.append({"type": action_type, "details": details, "turn": details.get("turn", 0)})
        templates = self.CONSEQUENCE_TEMPLATES.get(action_type, [])
        if templates:
            t = random.choice(templates)
            text = t["text"]
            for key, val in details.items():
                text = text.replace("{" + key + "}", str(val))
            self.pending.append({
                "text": text, "effect": t["effect"], "severity": t["severity"],
                "trigger_turn": details.get("turn", 0) + t["delay"],
                "source_action": action_type, "details": details,
            })

    def check_consequences(self, current_turn: int) -> List[Dict]:
        triggered = []
        for cons in self.pending[:]:
            if current_turn >= cons["trigger_turn"]:
                triggered.append(cons)
                self.triggered.append(cons)
                self.pending.remove(cons)
        return triggered

    def get_prompt_context(self) -> str:
        parts = []
        if self.pending: parts.append(f"## ОЖИДАЮЩИЕ ПОСЛЕДСТВИЯ: {len(self.pending)}")
        if self.triggered:
            recent = self.triggered[-5:]
            parts.append("## ПОСЛЕДСТВИЯ ДЕЙСТВИЙ ИГРОКА:")
            for c in recent:
                icon = "🔴" if c["severity"] >= 4 else "⚠" if c["severity"] >= 3 else "📌"
                parts.append(f"{icon} {c['text']} [эффект: {c['effect']}]")
        return "\n".join(parts) if parts else ""
