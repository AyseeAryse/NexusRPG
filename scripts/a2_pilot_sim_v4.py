"""
A2 Pilot v4 (Финальная точная конверсия, вариант 7): per-enemy пороги.

Ключевое отличие от v3: DT-таблица целилась в ОБОБЩЁННЫЕ бэнды (65/40/20%),
а реальный OLD-хит по конкретным врагам другой (реальный код: ac = 10 + defense,
без брони у врага):
    Торчок (def0):  nat>=3  → 90%
    Корп-агент (5): nat>=8  → 65%
    Титан (9):      nat>=12 → 45%

Точная конверсия: для каждого врага порог nat_sum_2d6 подобран так, чтобы
P(2d6>=X) ≈ фактический P(d20) старой системы:
    Торчок → X=4 (88.9%), Корп-агент → X=7 (58.3%), Титан → X=8 (41.7%).

Остальная механика как в v3: крит nat_sum>=11 (8.33%), броня игрока = DR −5,
вражеский to-hit по игроку — через ту же таблицу полос pdef.
"""

import random

random.seed(20260823)
N_SIM = 500

PILOT_ENEMIES = {
    "junkie":          {"name": "Торчок с ножом",   "hp": 14,  "attack": 3,  "defense": 0,  "dmg": "1d6+1"},
    "corporate_agent": {"name": "Корп-агент",       "hp": 40,  "attack": 6,  "defense": 5,  "dmg": "1d10+3"},
    "prototype_mech":  {"name": "Прототип «Титан»", "hp": 120, "attack": 10, "defense": 9,  "dmg": "2d10+6"},
}

PLAYER = {
    "combat_skill": 5, "dex": 7, "hp": 50, "weapon": "3d8",
    "armor_ac": 5,   # старая модель
    "armor_dr": 5,   # новая модель: −5 урона за попадание
}

# ТОЧНЫЕ пороги 2d6 per-enemy (подогнаны под фактический d20-хит реального кода)
EXACT_THRESHOLD = {
    "junkie":          4,   # цель 90%  → P(2d6>=4) = 88.9%
    "corporate_agent": 7,   # цель 65%  → P(2d6>=7) = 58.3%
    "prototype_mech":  8,   # цель 45%  → P(2d6>=8) = 41.7%
}

WEAPON_MAP = {"1d6+1": (1, 6, 1), "1d10+3": (1, 10, 3), "2d10+6": (2, 10, 6), "3d8": (3, 8, 0)}

CRIT_THRESHOLD = 11  # 8.33%


def roll_damage(formula):
    c, s, b = WEAPON_MAP[formula]
    total = 0
    for _ in range(c):
        total += random.randint(1, s)
    return total + b


# ---------- OLD d20 (ТОЧНО как реальный код combat.py) ----------
def sim_old(enemy):
    e_hp = enemy["hp"]
    p_hp = PLAYER["hp"]
    ac_enemy = 10 + enemy["defense"]                       # БЕЗ armor — как в коде
    ac_player = 10 + (PLAYER["dex"] - 5) + PLAYER["combat_skill"] // 2 + PLAYER["armor_ac"]  # A1: с бронёй
    rounds = 0
    while e_hp > 0 and p_hp > 0 and rounds < 100:
        rounds += 1
        attack_roll = random.randint(1, 20) + PLAYER["combat_skill"] + (PLAYER["dex"] - 5)
        natural = attack_roll - PLAYER["combat_skill"] - (PLAYER["dex"] - 5)
        if attack_roll >= ac_enemy:
            dmg = roll_damage(PLAYER["weapon"])
            if natural >= 19:
                dmg *= 2
            e_hp -= dmg
        if e_hp > 0:
            enemy_roll = random.randint(1, 20) + enemy["attack"]
            if enemy_roll >= ac_player:
                edmg = roll_damage(enemy["dmg"])
                if enemy_roll - enemy["attack"] >= 19:
                    edmg *= 2
                p_hp -= edmg
    return p_hp > 0, rounds, max(0, p_hp)


# ---------- NEW 2d6 (точная per-enemy конверсия) ----------
def sim_new(enemy, key):
    e_hp = enemy["hp"]
    p_hp = PLAYER["hp"]
    player_bonus = PLAYER["combat_skill"] + (PLAYER["dex"] - 5)   # 7
    dc_enemy = EXACT_THRESHOLD[key] - (player_bonus - 7)          # при бонусе 7 = сам порог
    dc_player = 15                                                # полоса pdef (как v3)
    rounds = 0
    while e_hp > 0 and p_hp > 0 and rounds < 100:
        rounds += 1
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        nat_sum = die1 + die2
        is_crit = nat_sum >= CRIT_THRESHOLD                       # 8.33%
        if nat_sum + player_bonus >= dc_enemy:
            dmg = roll_damage(PLAYER["weapon"])
            if is_crit:
                dmg *= 2
            e_hp -= dmg
        if e_hp > 0:
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
            enat = die1 + die2
            ecrit = enat >= CRIT_THRESHOLD
            if enat + enemy["attack"] >= dc_player:
                edmg = roll_damage(enemy["dmg"])
                if ecrit:
                    edmg *= 2
                edmg = max(1, edmg - PLAYER["armor_dr"])
                p_hp -= edmg
    return p_hp > 0, rounds, max(0, p_hp)


print(f"=== A2 ПИЛОТ v4 (точная per-enemy конверсия): {N_SIM}×2×3 ===\n")
print(f"{'Враг':<26}{'Система':<13}{'Win-rate':>9}{'Раундов':>9}{'HP ост.':>9}")
print("-" * 68)

verdict_all = True
for key, enemy in PILOT_ENEMIES.items():
    stats = {}
    for label, fn in [("OLD d20", sim_old), ("NEW 2d6", sim_new)]:
        wins = rounds_sum = hp_sum = 0
        for _ in range(N_SIM):
            won, rnd, hp_left = fn(enemy) if label == "OLD d20" else fn(enemy, key)
            wins += int(won); rounds_sum += rnd; hp_sum += hp_left
        stats[label] = (wins / N_SIM * 100, rounds_sum / N_SIM, hp_sum / N_SIM)

    o = stats["OLD d20"]; n = stats["NEW 2d6"]
    delta_wr = n[0] - o[0]
    ok = abs(delta_wr) <= 7
    verdict_all &= ok
    print(f"{enemy['name']:<26}{'OLD d20':<13}{o[0]:>8.1f}%{o[1]:>9.1f}{o[2]:>9.1f}")
    print(f"{'':<26}{'NEW 2d6':<13}{n[0]:>8.1f}%{n[1]:>9.1f}{n[2]:>9.1f}")
    print(f"{'':<26}{'Δ win-rate':<13}{delta_wr:>+8.1f} п.п. {'✅ ≤±7' if ok else '❌ >±7'}")
    print()

print("=" * 68)
print("ВЕРДИКТ:", "точная конверсия сошлась на всех трёх ✅" if verdict_all else "расхождение осталось даже с точной калибровкой")
