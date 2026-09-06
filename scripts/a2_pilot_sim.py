"""
A2 Pilot v3 (ФИНАЛ): Monte Carlo сравнение d20 vs 2d6 боевых систем.

Старая система (как в src/systems/combat.py):
  игрок:  d20 + combat_skill + (dex-5)   vs AC(10 + def + armor_ac)
  враг:   d20 + attack                   vs AC(10 + pdef + armor_ac)
  крит:   нат. бросок >= 19              (~10%)
  броня:  модификатор AC (+5 у Титана)

Новая система (кандидат конверсии на канон 2d6):
  to-hit: кусочная DC-таблица DT[defense] = {0-2:14, 3-5:15, 6-8:16, 9+:17}
          при базовом бонусе игрока 7; при ином бонусе DC_eff = DC - (bonus-7).
  крит:   сумма двух кубиков >= 11 → комбинации (5,6),(6,5),(6,6) = 3/36 = 8.33%.
          Кубы бросаются РАЗДЕЛЬНО (randint(1,6) × 2), не randint(2,12) —
          иначе распределение суммы было бы линейным, а не треугольным.
  броня:  DR = defense/3 (Титан 15 → −5 урона за попадание), минимум 1.

Игрок фиксированный: combat_skill=5, dex=7 (мод +2), HP=50, оружие 3d8,
броня Титан. Враги — три пилотных шаблона (низкий/средний/высокий тир).
500 симуляций на систему/врага, фиксированный seed.
"""

import random

random.seed(20260823)
N_SIM = 500

PILOT_ENEMIES = {
    "junkie":          {"name": "Торчок с ножом",   "hp": 14,  "attack": 3,  "defense": 0, "dmg": "1d6+1"},
    "corporate_agent": {"name": "Корп-агент",       "hp": 40,  "attack": 6,  "defense": 5, "dmg": "1d10+3"},
    "prototype_mech":  {"name": "Прототип «Титан»", "hp": 120, "attack": 10, "defense": 9, "dmg": "2d10+6"},
}

PLAYER = {
    "combat_skill": 5,
    "dex": 7,
    "hp": 50,
    "weapon": "3d8",
    "armor_ac": 5,   # старая модель: +5 к AC
    "armor_dr": 5,   # новая модель: −5 урона за попадание
}

WEAPON_MAP = {"1d6+1": (1, 6, 1), "1d10+3": (1, 10, 3), "2d10+6": (2, 10, 6), "3d8": (3, 8, 0)}

# Кусочная таблица to-hit при бонусе 7 (подогнана под цели d20: 65%/40%/20%)
DT = {0: 14, 1: 14, 2: 14, 3: 15, 4: 15, 5: 15, 6: 16, 7: 16, 8: 16, 9: 17}

CRIT_THRESHOLD = 11   # сумма >= 11 → крит: 8.33%


def roll_damage(formula):
    """Бросок урона по формуле NdM+B."""
    c, s, b = WEAPON_MAP[formula]
    total = 0
    for _ in range(c):
        total += random.randint(1, s)
    return total + b


# ---------- OLD d20 system ----------
def sim_old(enemy):
    e_hp = enemy["hp"]
    p_hp = PLAYER["hp"]
    ac_enemy = 10 + enemy["defense"] + PLAYER["armor_ac"]
    ac_player = 10 + (PLAYER["dex"] - 5) + PLAYER["combat_skill"] // 2 + PLAYER["armor_ac"]
    rounds = 0
    while e_hp > 0 and p_hp > 0 and rounds < 100:
        rounds += 1
        # --- атака игрока ---
        attack_roll = random.randint(1, 20) + PLAYER["combat_skill"] + (PLAYER["dex"] - 5)
        natural = attack_roll - PLAYER["combat_skill"] - (PLAYER["dex"] - 5)
        if attack_roll >= ac_enemy:
            dmg = roll_damage(PLAYER["weapon"])
            if natural >= 19:
                dmg *= 2
            e_hp -= dmg
        # --- атака врага ---
        if e_hp > 0:
            enemy_roll = random.randint(1, 20) + enemy["attack"]
            if enemy_roll >= ac_player:
                edmg = roll_damage(enemy["dmg"])
                if enemy_roll - enemy["attack"] >= 19:
                    edmg *= 2
                p_hp -= edmg
    return p_hp > 0, rounds, max(0, p_hp)


# ---------- NEW 2d6 system ----------
def sim_new(enemy):
    e_hp = enemy["hp"]
    p_hp = PLAYER["hp"]
    player_bonus = PLAYER["combat_skill"] + (PLAYER["dex"] - 5)           # = 7
    dc_enemy = DT.get(min(9, enemy["defense"]), 17) - (player_bonus - 7)  # сдвиг под бонус
    enemy_bonus = enemy["attack"]
    dc_player = DT.get(4, 15)                                             # полоса pdef игрока
    rounds = 0
    while e_hp > 0 and p_hp > 0 and rounds < 100:
        rounds += 1
        # --- атака игрока ---
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        nat_sum = die1 + die2
        is_crit = nat_sum >= CRIT_THRESHOLD                                # 8.33%
        if nat_sum + player_bonus >= dc_enemy:
            dmg = roll_damage(PLAYER["weapon"])
            if is_crit:
                dmg *= 2
            e_hp -= dmg
        # --- атака врага ---
        if e_hp > 0:
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
            enat = die1 + die2
            ecrit = enat >= CRIT_THRESHOLD
            if enat + enemy_bonus >= dc_player:
                edmg = roll_damage(enemy["dmg"])
                if ecrit:
                    edmg *= 2
                edmg = max(1, edmg - PLAYER["armor_dr"])                   # броня режет урон
                p_hp -= edmg
    return p_hp > 0, rounds, max(0, p_hp)


print(f"=== A2 ПИЛОТ v3 (финал): {N_SIM} симуляций × 2 системы × 3 врага ===\n")
print(f"{'Враг':<26}{'Система':<13}{'Win-rate':>9}{'Раундов':>9}{'HP ост.':>9}")
print("-" * 68)

verdict_all = True
for key, enemy in PILOT_ENEMIES.items():
    stats = {}
    for label, fn in [("OLD d20", sim_old), ("NEW 2d6", sim_new)]:
        wins = rounds_sum = hp_sum = 0
        for _ in range(N_SIM):
            won, rnd, hp_left = fn(enemy)
            wins += int(won)
            rounds_sum += rnd
            hp_sum += hp_left
        stats[label] = (wins / N_SIM * 100, rounds_sum / N_SIM, hp_sum / N_SIM)

    o = stats["OLD d20"]
    n = stats["NEW 2d6"]
    delta_wr = n[0] - o[0]
    ok = abs(delta_wr) <= 7
    verdict_all &= ok
    print(f"{enemy['name']:<26}{'OLD d20':<13}{o[0]:>8.1f}%{o[1]:>9.1f}{o[2]:>9.1f}")
    print(f"{'':<26}{'NEW 2d6':<13}{n[0]:>8.1f}%{n[1]:>9.1f}{n[2]:>9.1f}")
    print(f"{'':<26}{'Δ win-rate':<13}{delta_wr:>+8.1f} п.п. {'✅ ≤±7' if ok else '❌ >±7'}")
    print()

print("=" * 68)
print("ВЕРДИКТ пилота:", "все три врага в пределах ±7 п.п." if verdict_all else "есть выход за ±7 п.п.")
