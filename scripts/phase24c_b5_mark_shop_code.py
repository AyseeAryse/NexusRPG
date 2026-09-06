# Фаза 24c B5 (часть 2): вставка legality в dict-позиции трёх SHOP-каталогов в коде.
# Формат: однострочные dict'ы {"id": ..., "name": ..., ..., "rarity": ...}.
# Проход: находим каждый блок CAT: [...] внутри SHOP_ITEMS-присваиваний,
# для каждой dict-строки вычисляем legality по имени/категории/rarity и вставляем поле.
import re

ROOT = r"D:\NexusRPG-main"

def classify(name, cat, rarity=""):
    if re.search(r"(кустарн|самодельн|заточк|обрез|подпольн|контрабанд|нелегаль)", name, re.I):
        return "illegal"
    if cat == "weapons" and re.search(
            r"(плазм|лазер|снайпер|электромагнит|рельсов|гранатом|гранатомёт|пулем)", name, re.I):
        return "restricted"
    if cat == "implants" and rarity in ("epic", "legendary", "эпический", "легендарный",
                                        "уникальный", "артефакт"):
        return "restricted"
    if cat == "consumables" and re.search(r"адреналин|стимулятор", name, re.I):
        return "restricted"
    return "legal"

def process(path):
    t = open(path, encoding="utf-8").read()
    lines = t.splitlines(keepends=True)
    out = []
    current_cat = None
    counts = {"legal": 0, "restricted": 0, "illegal": 0}
    in_shop_scope = False
    for line in lines:
        # Входим в scope SHOP_ITEMS-присваивания
        if re.match(r"(EXPANDED|V2|V3)_SHOP_ITEMS\s*=", line):
            in_shop_scope = True
            current_cat = None
            out.append(line)
            continue
        # Выходим из scope на следующем top-level присваивании/классе
        if in_shop_scope and re.match(r"^[A-Z_]+\s*=|^class |^def ", line) and "SHOP_ITEMS" not in line:
            in_shop_scope = False
            out.append(line)
            continue
        if in_shop_scope:
            m_cat = re.match(r'\s*"([a-z_]+)":\s*\[\s*$', line)
            if m_cat:
                current_cat = m_cat.group(1)
                out.append(line)
                continue
            # Однострочный dict позиции
            m_item = re.match(r'(\s*)\{(.*)\}(,?)\s*$', line)
            if m_item and current_cat and '"id"' in line and "legality" not in line:
                body = m_item.group(2)
                m_name = re.search(r'"name":\s*"([^"]*)"', body)
                m_rar = re.search(r'"rarity":\s*"([^"]*)"', body)
                leg = classify(m_name.group(1) if m_name else "", current_cat,
                               m_rar.group(1) if m_rar else "")
                counts[leg] += 1
                out.append(f'{m_item.group(1)}{{{body}, "legality": "{leg}"}}{m_item.group(3)}\n')
                continue
        out.append(line)
    open(path, "w", encoding="utf-8").write("".join(out))
    return counts

for mod in ("base.py", "v2_legacy.py", "v3_legacy.py"):
    p = rf"{ROOT}\src\content\{mod}"
    c = process(p)
    import ast
    ast.parse(open(p, encoding="utf-8").read())
    print(f"{mod}: {c} | AST OK")
