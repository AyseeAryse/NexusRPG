"""
A2 Pilot v6: 3d6 vs OLD d20 — все defense 0-9.

Ключевые отличия от v5:
  1. Вражеский to-hit — ТОЧНЫЙ per-attack DC (не placeholder DT_PDEF=15).
     Старая цель для врага: P = clamp((attack+2)/20) — включает броню игрока.
  2. Куб 3d6 вместо 2d6: 16 уровней вероятности, шаг мельче в зоне 40-60%.
     Конверсия: argmin |P(3d6>=X) - P(d20)| по точному распределению 3d6.
  3. Крит 3d6: nat_sum >= 15 → 9.26% (близко к d20 ~10%), подобран отдельно.
  4. Броня: только через цели to-hit (включена в старые проценты) — без DR,
     чтобы не задваивать защиту.

Игрок: combat_skill=5, dex=7, HP=50, оружие 3d8, Титан (+5 AC старая модель).
"""

import random

random.seed(20260823)
N_SIM = 500

PLAYER_BONUS = 7
ARMOR_AC = 5
CRIT_3D6 = 15   # P = 9.26%

REP = {
 0: {"name": "Торчок",         "hp": 14,  "attack": 3,  "dmg": "1d6+1",   "defense": 0},
 1: {"name": "Головорез",      "hp": 20,  "attack": 3,  "dmg": "1d6",     "defense": 1},
 2: {"name": "Бандит",         "hp": 25,  "attack": 4,  "dmg": "1d6+2",   "defense": 2},
 3: {"name": "Карманник",      "hp": 12,  "attack": 2,  "dmg": "1d4",     "defense": 3},
 4: {"name": "Охранник",       "hp": 30,  "attack": 4,  "dmg": "1d6+1",   "defense": 4},
 5: {"name": "Корп-агент",     "hp": 40,  "attack": 6,  "dmg": "1d10+3",  "defense": 5},
 6: {"name": "Оперативник",    "hp": 48,  "attack": 7,  "dmg": "1d10+4",  "defense": 6},
 7: {"name": "Дрон-отщепенец", "hp": 60,  "attack": 6,  "dmg": "1d10+2",  "defense": 7},
 8: {"name": "Экзоскелет",     "hp": 80,  "attack": 8,  "dmg": "2d8+5",   "defense": 8},
 9: {"name": "Прототип «Титан»","hp": 120,"attack": 10, "dmg": "2d10+6",  "defense": 9},
}

WEAPON_MAP = {
    "1d4": (1,4,0), "1d6": (1,6,0), "1d6+1": (1,6,1), "1d6+2": (1,6,2),
    "1d8+1": (1,8,1), "1d10+2": (1,10,2), "1d10+3": (1,10,3), "1d10+4": (1,10,4),
    "2d8+5": (2,8,5), "2d10+6": (2,10,6), "3d8": (3,8,0),
}

# Точные распределения
P2 = {x: sum(1 for a in range(1,7) for b in range(1,7) if a+b>=x)/36 for x in range(2,13)}
P3 = {x: sum(1 for a in range(1,7) for b in range(1,7) for c in range(1,7) if a+b+c>=x)/216 for x in range(3,19)}

def exact_d20_hit(defense):
    need = (10 + defense) - PLAYER_BONUS
    if need <= 1: return 1.0
    if need > 20: return 0.0
    return (21 - need) / 20


def player_dc_exact_3d6(defense, bonus=PLAYER_BONUS):
    """DC на nat_sum 3d6, минимизирующий отклонение от старой цели."""
    tgt = exact_d20_hit(defense)
    best_x, best_err = None, 2.0
    for x in range(4, 19):
        err = abs(P3[x] - tgt)
        if err < best_err:
            best_x, best_err = x, err
    return best_x


def enemy_threshold_3d6(attack):
    """Порог nat_sum 3d6 для врага: цель (attack+2)/20."""
    tgt = max(0.0, min(1.0, (attack + 2) / 20))
    best_x, best_err = None, 2.0
    for x in range(4, 19):
        err = abs(P3[x] - tgt)
        if err < best_err:
            best_x, best_err = x, err
    return best_x


def roll_damage(formula):
    c, s, b = WEAPON_MAP[formula]
    total = 0
    for _ in range(c):
        total += random.randint(1, s)
    return total + b


def sim_old(enemy):
    e_hp = enemy["hp"]; p_hp = 50
    ac_enemy = 10 + enemy["defense"] + ARMOR_AC
    ac_player = 10 + (7 - 5) + PLAYER_BONUS // 2 + ARMOR_AC   # 19
    r = 0
    while e_hp > 0 and p_hp > 0 and r < 100:
        r += 1
        rv = random.randint(1, 20) + PLAYER_BONUS
        if rv >= ac_enemy:
            d = roll_damage("3d8")
            if rv - PLAYER_BONUS >= 19: d *= 2
            e_hp -= d
        if e_hp > 0:
            re_ = random.randint(1, 20) + enemy["attack"]
            if re_ >= ac_player:
                ed = roll_damage(enemy["dmg"])
                if re_ - enemy["attack"] >= 19: ed *= 2
                p_hp -= ed
    return p_hp > 0, r, max(0, p_hp)


def sim_new(enemy, dc_enemy_eff, enemy_thr):
    e_hp = enemy["hp"]; p_hp = 50
    r = 0
    while e_hp > 0 and p_hp > 0 and r < 100:
        r += 1
        # --- игрок: 3d6 ---
        d1 = random.randint(1, 6); d2 = random.randint(1, 6); d3 = random.randint(1, 6)
        nat = d1 + d2 + d3
        crit = nat >= CRIT_3D6
        if nat >= dc_enemy_eff:
            d = roll_damage("3d8")
            if crit: d *= 2
            e_hp -= d
        # --- враг: 3d6 ---
        if e_hp > 0:
            e1 = random.randint(1, 6); e2 = random.randint(1, 6); e3 = random.randint(1, 6)
            enat = e1 + e2 + e3
            ecrit = enat >= CRIT_3D6
            if enat >= enemy_thr:
                ed = roll_damage(enemy["dmg"])
                if ecrit: ed *= 2
                p_hp -= ed
    return p_hp > 0, r, max(0, p_hp)


print(f"=== A2 ПИЛОТ v6: 3d6 vs OLD d20, все defense 0-9, {N_SIM}×2 ===\n")
print(f"{'def':>4}{'P(d20)':>8}{'X3d6':>6}{'P(3d6)':>8} | {'OLD win':>8}{'NEW win':>8}{'Δwin п.п.':>10} {'Вердикт':<8}")
print("-" * 76)

all_ok = True
results = {}
for d in sorted(REP.keys()):
    enemy = REP[d]
    p_old = exact_d20_hit(d)
    x_eff = player_dc_exact_3d6(d)          # порог nat_sum 3d6 (бонус уже «вшит» в цель)
    ethr = enemy_threshold_3d6(enemy["attack"])
    ow = nw = orr = nrn = ohp = nhp = 0
    for _ in range(N_SIM):
        a = sim_old(enemy)
        b = sim_new(enemy, x_eff, ethr)
        ow += a[0]; orr += a[1]; ohp += a[2]
        nw += b[0]; nrn += b[1]; nhp += b[2]
    ow /= N_SIM * .01; nw /= N_SIM * .01
    orr /= N_SIM; nrn /= N_SIM; ohp /= N_SIM; nhp /= N_SIM
    dw = nw - ow
    ok = abs(dw) <= 7
    all_ok &= ok
    results[d] = dw
    print(f"{d:>4}{p_old:>8.0%}{x_eff:>6}{P3[x_eff]:>8.0%} | {ow:>7.1f}%{nw:>7.1f}%{dw:>+10.1f} {'✅' if ok else '❌ >±7'}")

fails = [d for d, dw in results.items() if abs(dw) > 7]
print("\n" + "=" * 76)
if all_ok:
    print("ИТОГ: ВСЕ defense 0-9 в пределах ±7 п.п. — раскатка на 28 шаблонов с 3d6 разрешена")
else:
    print(f"ИТОГ: выход за ±7 на defense={fails}")
