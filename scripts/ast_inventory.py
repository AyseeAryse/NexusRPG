# -*- coding: utf-8 -*-
"""
AST-инвентаризация GameEngine (Phase 30, только карта — без рефакторинга).

Считает:
  1. Методы класса GameEngine: имя, строки тела, трогаемые self.<subsystem>,
     прямые вызовы из src/server/routes/*.
  2. Subsystem-поля, созданные в __init__: тип/класс, модуль импорта,
     число методов-пользователей.
  3. Оглавление static/js/app.js: top-level функции/секции + строки.

Запуск: python scripts/ast_inventory.py
Выход: текстовые таблицы в stdout + _audit/engine_inventory.md
"""
import ast
import os
import re
import json
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_PATH = os.path.join(ROOT, "src", "core", "engine.py")
ROUTES_DIR = os.path.join(ROOT, "src", "server", "routes")
APPJS_PATH = os.path.join(ROOT, "static", "js", "app.js")
OUT_PATH = os.path.join(ROOT, "_audit", "engine_inventory.md")


# ─────────────────────────────────────────────────────────────
# Часть 1: методы GameEngine
# ─────────────────────────────────────────────────────────────

def collect_methods(tree):
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "GameEngine")
    methods = []
    for node in cls.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Строки тела: от строки декоратора/def до конца последнего statement
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        end = max(getattr(n, "end_lineno", 0) or 0
                  for n in ast.walk(node)
                  if hasattr(n, "lineno") or hasattr(n, "end_lineno"))
        # self.<attr> — чтение атрибутов у self (Name.self → Attribute)
        touched = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "self"):
                touched.add(n.attr)
        methods.append({
            "name": node.name,
            "start": start,
            "end": end,
            "lines": end - start + 1,
            "touched": touched,
            "args": [a.arg for a in node.args.args],
        })
    return methods


# ─────────────────────────────────────────────────────────────
# Часть 2: поля __init__
# ─────────────────────────────────────────────────────────────

def collect_init_fields(tree, methods):
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "GameEngine")
    init = next(n for n in cls.body
                if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    fields = {}
    for node in ast.walk(init):
        # self.X = <expr>
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Attribute)
                and isinstance(node.targets[0].value, ast.Name)
                and node.targets[0].value.id == "self"):
            name = node.targets[0].attr
            expr = node.value
            if isinstance(expr, ast.Call):
                func = expr.func
                if isinstance(func, ast.Name):
                    cls_name = func.id
                elif isinstance(func, ast.Attribute):
                    cls_name = func.attr
                else:
                    cls_name = "?"
            elif isinstance(expr, ast.Dict):
                cls_name = "dict literal"
            elif isinstance(expr, ast.List):
                cls_name = "list literal"
            elif isinstance(expr, ast.Name):
                cls_name = f"alias of {expr.id}"
            else:
                cls_name = ast.dump(expr)[:40]
            fields[name] = cls_name
    return fields


def build_import_map(tree):
    """Имя класса/константы → модуль, из которого импортирован."""
    imap = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imap[alias.asname or alias.name] = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imap[alias.asname or alias.name] = alias.name
    return imap


# ─────────────────────────────────────────────────────────────
# Часть 3: вызовы из routes
# ─────────────────────────────────────────────────────────────

def collect_routes_calls(method_names):
    """Для каждого имени метода — в каких файлах routes/ он вызывается
    через get_engine().<name>( / engine.<name>( / .state... не считаем."""
    calls = defaultdict(set)
    pat = re.compile(
        r"(?:get_engine\(\)|\bengine\b|\.engine\b)\s*\.\s*([a-zA-Z_]\w*)\s*\(")
    for fname in os.listdir(ROUTES_DIR):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(ROUTES_DIR, fname)
        text = open(path, encoding="utf-8").read()
        for m in pat.finditer(text):
            name = m.group(1)
            if name in method_names:
                calls[name].add(fname)
    return calls


# ─────────────────────────────────────────────────────────────
# Часть 4: app.js оглавление
# ─────────────────────────────────────────════════════════════

def js_outline_fixed():
    """Корректная версия: функции и секции, размер = до следующей метки."""
    text = open(APPJS_PATH, encoding="utf-8").read()
    lines = text.split("\n")
    marks = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", line)
        if m:
            marks.append((i, "function", m.group(1)))
            continue
        m2 = re.match(r"^\s*//\s*[═=-]{2,}\s*(.+?)\s*[═=-]{2,}\s*$", line)
        if m2:
            marks.append((i, "section", m2.group(1)))
    out = []
    for idx, (ln, kind, name) in enumerate(marks):
        end = marks[idx + 1][0] - 1 if idx + 1 < len(marks) else len(lines)
        out.append((ln, kind, name, end - ln + 1))
    return out


# ─────────────────────────────────────────────────────────────
# Отчёт
# ─────────────────────────────────────────────────────────────

def main():
    src = open(ENGINE_PATH, encoding="utf-8").read()
    tree = ast.parse(src)

    methods = collect_methods(tree)
    fields = collect_init_fields(tree, methods)
    imap = build_import_map(tree)
    routes_calls = collect_routes_calls({m["name"] for m in methods})

    # Поля, которые реально используются методами (touched)
    field_users = defaultdict(list)
    for m in methods:
        for attr in m["touched"]:
            if attr in fields:
                field_users[attr].append(m["name"])

    # Подсистемы = поля-объекты из __init__ (исключаем data-поля типа state/saves_dir)
    subsystem_fields = {k: v for k, v in fields.items()
                        if "literal" not in v and v not in ("dict literal",)}

    # Группировка методов по набору подсистем
    groups = defaultdict(list)
    for m in methods:
        subs = sorted(a for a in m["touched"] if a in subsystem_fields)
        key = "+".join(subs) if subs else "(none)"
        groups[key].append(m)

    L = []
    A = L.append
    A("# AST-инвентаризация GameEngine — сгенерировано scripts/ast_inventory.py\n")

    A("## 1. Сводка\n")
    total_lines = sum(m["lines"] for m in methods)
    A(f"- Классов в engine.py с именем GameEngine: 1")
    A(f"- Методов GameEngine: **{len(methods)}**")
    A(f"- Суммарный объём тел методов: **{total_lines} строк**")
    A(f"- Subsystem-полей в __init__: **{len(subsystem_fields)}** "
      f"(+{len(fields)-len(subsystem_fields)} data-полей)\n")

    A("## 2. Subsystem-поля __init__ (Задача 2)\n")
    A("| Поле | Класс/тип | Модуль импорта | Методов-пользователей | Методы |")
    A("|---|---|---|---|---|")
    for name in sorted(fields, key=lambda k: -len(field_users.get(k, []))):
        cls_name = fields[name]
        module = imap.get(cls_name, "— (локальный/встроенный)")
        users = field_users.get(name, [])
        A(f"| self.{name} | {cls_name} | {module} | {len(users)} | "
          f"{', '.join(users[:8])}{' …' if len(users) > 8 else ''} |")
    A("")

    A("## 3. Методы, трогающие 3+ подсистем — «God methods»\n")
    god = [m for m in methods
           if len([a for a in m["touched"] if a in subsystem_fields]) >= 3]
    god.sort(key=lambda m: -m["lines"])
    A(f"Найдено: **{len(god)}**\n")
    A("| Метод | Строк | Подсистемы | Вызывается из routes |")
    A("|---|---|---|---|")
    for m in god:
        subs = sorted(a for a in m["touched"] if a in subsystem_fields)
        rc = ", ".join(sorted(routes_calls.get(m["name"], []))) or "—"
        A(f"| `{m['name']}` | {m['lines']} | {len(subs)}: {', '.join(subs)} | {rc} |")
    A("")

    A("## 4. Группировка методов по набору подсистем\n")
    for key in sorted(groups, key=lambda k: -sum(m["lines"] for m in groups[k])):
        ms = groups[key]
        total = sum(m["lines"] for m in ms)
        A(f"### Группа `{key}` — {len(ms)} методов, {total} строк\n")
        A("| Метод | Строк | routes |")
        A("|---|---|---|")
        for m in sorted(ms, key=lambda x: -x["lines"]):
            rc = ", ".join(sorted(routes_calls.get(m["name"], []))) or "—"
            A(f"| `{m['name']}` | {m['lines']} | {rc} |")
        A("")

    A("## 5. Полный список методов (Задача 1)\n")
    A("| Метод | строки | объём | подсистемы | routes |")
    A("|---|---|---|---|---|")
    for m in sorted(methods, key=lambda x: x["start"]):
        subs = sorted(a for a in m["touched"] if a in subsystem_fields)
        rc = ", ".join(sorted(routes_calls.get(m["name"], []))) or "—"
        A(f"| `{m['name']}` | {m['start']}–{m['end']} | {m['lines']} | "
          f"{', '.join(subs) if subs else '—'} | {rc} |")
    A("")

    A("## 6. app.js — оглавление top-level (Задача 3)\n")
    outline = js_outline_fixed()
    total_js = sum(o[3] for o in outline)
    A(f"Функций/секций: **{len(outline)}**, охвачено строк: {total_js} из {len(open(APPJS_PATH, encoding='utf-8').read().splitlines())}\n")
    A("| строки | тип | имя | объём |")
    A("|---|---|---|---|")
    for ln, kind, name, span in outline:
        A(f"| {ln}–{ln+span-1} | {kind} | `{name}` | {span} |")

    report = "\n".join(L)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(report[:3000])
    print(f"\n...\n\nПолный отчёт: {OUT_PATH} ({len(report)} символов)")


if __name__ == "__main__":
    main()
