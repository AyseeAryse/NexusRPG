"""
A2 Pilot v5: обобщённая конверсия + расширенная симуляция по ВСЕМ уникальным defense.

Обобщённая функция конверсии (не таблица бэндов):
  1. Фактический P(d20) старой системы: ac = 10 + defense, player_bonus = 7
     → p_old = clamp((21 - (ac - bonus)) / 20, 0, 1)
  2. Порог X: перебор nat_sum 3..12, берём argmin |P(2d6 >= X) - p_old|
     (P(2d6>=X) — точные вероятности треугольного распределения, не симуляция)

Симуляция: для каждого уникального defense берётся реальный шаблон-представитель,
500 боёв OLD vs NEW. NEW: крит nat_sum>=11 (8.33%), броня игрока DR −5.
"""

import random

random.seed(20260823)
N_SIM = 500

PLAYER_BONUS = 7          # combat_skill 5 + dex_mod 2
ARMOR_AC = 5              # старая модель
ARMOR_DR = 5              # новая модель (Титан, defense 15/3)
CRIT_THRESHOLD = 11       # 8.33%

# Точные вероятности P(2d6 >= x) для x=2..12
_P2 = {}
for _x in range(2, 13):
    cnt = sum(1 for a in range(1, 7) for b in range(1, 7) if a + b >= _x)
    _P2[_x] = cnt / 36


def exact_d20_hit_chance(defense: int) -> float:
    """Фактический шанс попадания игрока в старой системе."""
    need = (10 + defense) - PLAYER_BONUS
    if need <= 1:
        return 1.0
    if need > 20:
        return 0.0
    return (21 - need) / 20


def convert_threshold(defense: int) -> int:
    """Обобщённая формула: порог 2d6, минимизирующий |P(2d6>=X) - P(d20)|."""
    p_old = exact_d20_hit_chance(defense)
    best_x, best_err = 12, 2.0
    for x in range(3, 13):
        err = abs(_P2[x] - p_old)
        if err < best_err:
            best_x, best_err = x, err
    return best_x


# Представители каждого defense из реальных шаблонов
REPRESENTATIVES = {
    0: {"name": "Торчок",        "hp": 14,  "attack": 3,  "dmg": "1d6+1"},
    1: {"name": "Головорез",     "hp": 20,  "attack": 3,  "dmg": "1d6"},
    2: {"name": "Бандит",        "hp": 25,  "attack": 4,  "dmg": "1d6+2"},
    3: {"name": "Карманник",     "hp": 12,  "attack": 2,  "dmg": "1d4"},
    4: {"name": "Охранник",      "hp": 30,  "attack": 4,  "dmg": "1d6+1"},
    5: {"name": "Корп-агент",    "hp": 40,  "attack": 6,  "dmg": "1d10+3"},
    6: {"name": "Оперативник",   "hp": 48,  "attack": 7,  "dmg": "1d10+4"},
    7: {"name": "Дрон-отщепенец","hp": 60,  "attack": 6,  "dmg": "1d10+2"},
    8: {"name": "Экзоскелет",    "hp": 80,  "attack": 8,  "dmg": "2d8+5"},
    9: {"name": "Прототип «Титан»","hp":120, "attack": 10, "dmg": "2d10+6"},
}

WEAPON_MAP = {
    "1d4": (1,4,0), "1d6": (1,6,0), "1d6+1": (1,6,1), "1d6+2": (1,6,2),
    "1d8+1": (1,8,1), "1d10+2": (1,10,2), "1d10+3": (1,10,3), "1d10+4": (1,10,4),
    "2d8+5": (2,8,5), "2d10+6": (2,10,6), "3d8": (3,8,0),
}


def roll_damage(formula):
    c, s, b = WEAPON_MAP[formula]
    t = 0
    for _ in range(c):
        t += random.randint(1, s)
    return t + b


def sim_old(enemy):
    e_hp, p_hp = enemy["hp"], 50
    ac_enemy = 10 + enemy["defense"] + ARMOR_AC
    ac_player = 10 + 2 + PLAYER_BONUS // 2 + ARMOR_AC
    r = 0
    while e_hp > 0 and p_hp > 0 and r < 100:
        r += 1
        rv = random.randint(1, 20) + PLAYER_BONUS
        if rv >= ac_enemy:
            d = roll_damage("3d8")
            if rv - PLAYER_BONUS >= 19:
                d *= 2
            e_hp -= d
        if e_hp > 0:
            re_ = random.randint(1, 20) + enemy["attack"]
            if re_ >= ac_player:
                ed = roll_damage(enemy["dmg"])
                if re_ - enemy["attack"] >= 19:
                    ed *= 2
                p_hp -= ed
    return p_hp > 0, r, max(0, p_hp)


def sim_new(enemy, threshold):
    e_hp, p_hp = enemy["hp"], 50
    dc_enemy = threshold - (PLAYER_BONUS - 7)
    dc_player = DT_PDEF   # полоса pdef игрока при бонусе врага как есть
    r = 0
    while e_hp > 0 and p_hp > 0 and r < 100:
        r += 1
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        nat = d1 + d2
        crit = nat >= CRIT_THRESHOLD
        if nat + PLAYER_BONUS >= dc_enemy:
            d = roll_damage("3d8")
            if crit:
                d *= 2
            e_hp -= d
        if e_hp > 0:
            e1, e2 = random.randint(1, 6), random.randint(1, 6)
            enat = e1 + e2
            ecrit = enat >= CRIT_THRESHOLD
            if enat + enemy["attack"] >= dc_player:
                ed = roll_damage(enemy["dmg"])
                if ecrit:
                    ed *= 2
                p_hp -= max(1, ed - ARMOR_DR)
    return p_hp > 0, r, max(0, p_hp)


# Полоса pdef игрока для вражеского to-hit (dex_mod 2 + skill/2 2 = 4 → DT[4]=15),
# но враг бьёт СВОИМ бонусом как есть; DR уже режет урон.
DT_PDEF = 15

print(f"=== A2 ПИЛОТ v5: обобщённая конверсия, все defense 0-9, {N_SIM}×2 на значение ===\n")
print(f"{'def':>4}{'P(d20)':>8}{'X':>4}{'P(2d6)':>8} | {'OLD win':>8}{'NEW win':>8}{'Δwin п.п.':>10} {'Вердикт':<8}")
print("-" * 72)

all_ok = True
results = {}
for d in sorted(REPRESENTATIVES.keys()):
    enemy = dict(REPRESENTATIVES[d])
    enemy["defense"] = d
    p_old = exact_d20_hit_chance(d)
    x = convert_threshold(d)
    ow = nw = orr = nrn = ohp = nhp = 0
    for _ in range(N_SIM):
        a = sim_old(enemy)
        b = sim_new(enemy, x)
        ow += a[0]; orr += a[1]; ohp += a[2]
        nw += b[0]; nrn += b[1]; nhp += b[2]
    ow /= N_SIM * 0.01; nw /= N_SIM * 0.01
    orr /= N_SIM; nrn /= N_SIM; ohp /= N_SIM; nhp /= N_SIM
    dw = nw - ow
    ok = abs(dw) <= 7
    all_ok &= ok
    results[d] = dw
    print(f"{d:>4}{p_old:>8.0%}{x:>4}{_P2[x]:>8.0%} | {ow:>7.1f}%{nw:>7.1f}%{dw:>+10.1f} {'✅' if ok else '❌ >±7'}")

print("\n" + "=" * 72)
fails = [d for d, dw in results.items() if abs(dw) > 7]
if all_ok:
    print("ИТОГ: все уникальные defense-значения в пределах ±7 п.п. — раскатка разрешена")
else:
    print(f"ИТОГ: выход за ±7 на defense={fails} — раскатка заблокирована")
