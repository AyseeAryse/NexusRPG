# Фаза 24c B5 (v3, версия 2): корректный проход многострочных dict'ов V3_SHOP_ITEMS.
# Никаких while-пассов: явный индекс, сбор блока до строки с "}, на конце.
import re

PATH = r"D:\NexusRPG-main\src\content\v3_legacy.py"

def classify(name, cat, rarity=""):
    if re.search(r"(кустарн|самодельн|заточк|обрез|подпольн|контрабанд|нелегаль)", name, re.I):
        return "illegal"
    if cat == "weapons" and re.search(
            r"(плазм|лазер|снайпер|электромагнит|рельсов|гранатом|пулем)", name, re.I):
        return "restricted"
    if cat == "implants" and rarity in ("epic", "legendary", "эпический", "легендарный",
                                        "уникальный", "артефакт"):
        return "restricted"
    if cat == "consumables" and re.search(r"адреналин|стимулятор", name, re.I):
        return "restricted"
    return "legal"

lines = open(PATH, encoding="utf-8").read().splitlines(keepends=True)
out = []
in_shop = False
current_cat = None
counts = {"legal": 0, "restricted": 0, "illegal": 0}
i = 0
n = len(lines)
while i < n:
    line = lines[i]
    if re.match(r"V3_SHOP_ITEMS\s*=", line):
        in_shop = True
        out.append(line); i += 1
        continue
    if in_shop and (re.match(r"^(def |class |from |import |[A-Za-z_]+\s*=)", line)
                    and "SHOP_ITEMS" not in line
                    and not line.lstrip().startswith(('"', "#", "}", "{"))):
        in_shop = False
        out.append(line); i += 1
        continue
    if in_shop:
        m_cat = re.match(r'\s*"([a-z_]+)":\s*\[\s*$', line)
        if m_cat:
            current_cat = m_cat.group(1)
            out.append(line); i += 1
            continue
        # Начало dict-позиции: содержит "id": и ещё не имеет legality
        if current_cat and '"id"' in line and "legality" not in line:
            block = [line]
            # Если dict закрылся в этой же строке — однострочный
            if re.search(r'\},\s*$', line):
                full = line
                m_name = re.search(r'"name":\s*"([^"]*)"', full)
                m_rar = re.search(r'"rarity":\s*"([^"]*)"', full)
                leg = classify(m_name.group(1) if m_name else "", current_cat,
                               m_rar.group(1) if m_rar else "")
                counts[leg] += 1
                indent = re.match(r"\s*", line).group(0)
                out.append(re.sub(r'\}(,?)\s*$',
                                  f', "legality": "{leg}"' + '}\\1\n', line, count=1))
                i += 1
                continue
            # Многострочный: копим до строки с "},
            j = i
            while j < n and not re.search(r'\}\s*,?\s*$', lines[j]):
                j += 1
                if j < n:
                    block.append(lines[j])
            full = "".join(block)
            m_name = re.search(r'"name":\s*"([^"]*)"', full)
            m_rar = re.search(r'"rarity":\s*"([^"]*)"', full)
            leg = classify(m_name.group(1) if m_name else "", current_cat,
                           m_rar.group(1) if m_rar else "")
            counts[leg] += 1
            last = block[-1]
            block[-1] = re.sub(r'\}(,?)\s*$',
                                  f', "legality": "{leg}"' + '}\\1\n', last, count=1)
            out.extend(block)
            i = j + 1
            continue
    out.append(line)
    i += 1

open(PATH, "w", encoding="utf-8").write("".join(out))
import ast
ast.parse(open(PATH, encoding="utf-8").read())
print(f"v3_legacy: {counts} | AST OK")
