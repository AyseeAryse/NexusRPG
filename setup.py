#!/usr/bin/env python3
"""NEXUS RPG — Setup & Validation"""
import os, sys, json

BASE = os.path.dirname(os.path.abspath(__file__))

def check():
    print("=" * 50)
    print("  NEXUS RPG — Проверка системы")
    print("=" * 50)
    ok = True

    # Dependencies
    for mod in ['flask', 'requests']:
        try:
            __import__(mod)
            print(f"  ✓ {mod}")
        except ImportError:
            print(f"  ✗ {mod} — pip install {mod}")
            ok = False

    # Game data
    gd = os.path.join(BASE, 'game_data')
    files = [f for f in os.listdir(gd) if f.endswith('.json')] if os.path.exists(gd) else []
    valid = 0
    for f in files:
        try:
            json.load(open(os.path.join(gd, f), encoding='utf-8'))
            valid += 1
        except: pass
    print(f"  ✓ game_data: {len(files)} файлов ({valid} валидных)")

    # Database
    db = os.path.join(BASE, 'database')
    if os.path.exists(db):
        subdirs = [d for d in os.listdir(db) if os.path.isdir(os.path.join(db, d))]
        print(f"  ✓ database: {len(subdirs)} категорий")
    else:
        print(f"  ⚠ database/ не найдена, создаю...")
        for d in ['factions','skills','lore','npcs','locations','items','quests']:
            os.makedirs(os.path.join(db, d), exist_ok=True)
        print(f"  ✓ database создана")

    # Saves
    sd = os.path.join(BASE, 'saves')
    os.makedirs(sd, exist_ok=True)
    saves = len([f for f in os.listdir(sd) if f.endswith('.json')])
    print(f"  ✓ saves: {saves} сохранений")

    # Templates & static
    for f in ['templates/index.html', 'static/app.js', 'static/style.css']:
        p = os.path.join(BASE, f)
        if os.path.exists(p):
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} НЕ НАЙДЕН")
            ok = False

    print("=" * 50)
    if ok:
        print("  Всё готово! Запускайте: python server.py")
    else:
        print("  Есть ошибки. Исправьте и запустите снова.")
    print("=" * 50)

if __name__ == '__main__':
    check()
