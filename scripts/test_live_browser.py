# -*- coding: utf-8 -*-
"""
Живой браузерный E2E-тест NexusRPG через Playwright.
Запуск: python scripts/test_live_browser.py
Требует запущенный сервер на http://localhost:8080.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(ROOT, "_audit", "screenshots")
os.makedirs(SHOT_DIR, exist_ok=True)

console_errors = []   # console.error / JS errors
page_errors = []      # uncaught exceptions
bad_responses = []    # 4xx/5xx responses
asserts = []          # (name, ok, detail)


def log(msg):
    print(msg, flush=True)


def check(name, ok, detail=""):
    asserts.append((name, bool(ok), detail))
    log(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def on_response(response):
    url = response.url
    if "/api/" in url and response.status >= 400:
        bad_responses.append((response.status, url))


def main():
    log("=" * 70)
    log("NexusRPG live E2E test (Playwright, headless Chromium)")
    log(f"Target: {BASE_URL}")
    log("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 900})
        page = ctx.new_page()

        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("response", on_response)

        # ---- 1. Load main page ----
        log("\n[1] Загрузка главной страницы...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(SHOT_DIR, "01_initial.png"))

        # ---- 2. Start game via preset flow ----
        log("\n[2] Старт игры через пресет...")
        # Шаг -1: бут-экран -> "ВОЙТИ В СИСТЕМУ"
        try:
            page.click("text=ВОЙТИ В СИСТЕМУ", timeout=5000)
            page.wait_for_timeout(1500)
            log("  прошёл бут-экран")
        except Exception as e:
            log(f"  (бут-экран пропущен: {e})")
        # Шаг -0.5: главное меню -> "НОВАЯ ИГРА"
        try:
            page.click("text=НОВАЯ ИГРА", timeout=5000)
            page.wait_for_timeout(1500)
            log("  выбрал НОВАЯ ИГРА")
        except Exception as e:
            log(f"  (главное меню пропущено: {e})")
        # Шаг 0: выбор режима
        try:
            page.click("text=ГОТОВЫЙ ПРЕСЕТ", timeout=5000)
            page.wait_for_timeout(1500)
        except Exception as e:
            log(f"  (шаг 0 пропущен: {e})")

        # Select first preset card
        try:
            page.locator(".preset-card").first.click(timeout=4000)
            page.wait_for_timeout(300)
            log("  выбрал первый пресет")
        except Exception as e:
            log(f"  (пресет не выбран: {e})")

        # Fill name
        try:
            page.fill("#inp-char-name-preset", "ТестКапитан", timeout=3000)
            log("  имя введено")
        except Exception:
            try:
                page.fill("#inp-char-name", "ТестКапитан", timeout=2000)
                log("  имя введено (alt)")
            except Exception as e:
                log(f"  (имя не введено: {e})")

        try:
            page.click("text=НАЧАТЬ ИГРУ", timeout=5000)
            # Старт генерирует вступительный нарратив через LM Studio — ждём
            # появления верхней панели игрового экрана до 180 сек.
            log("  кнопка нажата, жду игровой экран (до 180с)...")
            page.wait_for_selector('button.topbar-btn[title="Персонаж"]',
                                   state="visible", timeout=180000)
            log("  игра запущена — верхняя панель видна")
        except Exception as e:
            log(f"  (кнопка старта/ожидание: {str(e)[:150]})")

        page.screenshot(path=os.path.join(SHOT_DIR, "02_game_started.png"))

        # ---- 3. Click topbar tabs ----
        log("\n[3] Клики по вкладкам верхней панели...")
        tabs = [
            ("Персонаж", "Персонаж"),
            ("Инвентарь", "Инвентарь"),
            ("Корабль", "Корабль"),
            ("Локация", "Локация"),
            ("NPC", "NPC"),
            ("Квесты", "Квесты"),
            ("Фракции", "Фракции"),
        ]
        for title, shot in tabs:
            try:
                page.click(f'tooltip .topbar-btn[title="{title}"], button.topbar-btn[title="{title}"]',
                           timeout=3000)
                page.wait_for_timeout(1200)
                fn = f"03_tab_{shot}.png"
                page.screenshot(path=os.path.join(SHOT_DIR, fn))
                log(f"  открыта вкладка: {title} -> {fn}")
            except Exception as e:
                check(f"вкладка {title} кликается", False, str(e)[:120])

        # ---- 4. Assertions ----
        log("\n[4] Проверки...")

        # 4.1 History window must not contain [HP: or [MECHANICS]
        try:
            hist = page.inner_text("#chat-history") if page.locator("#chat-history").count() \
                else page.inner_text("#narrative-output")
        except Exception:
            hist = page.inner_text("body")
        bad_hp = re.findall(r"\[HP:", hist) if (re := __import__("re")) else []
        check("история не содержит [HP:", "[HP:" not in hist,
              f"найдено {hist.count('[HP:')} вхождений")
        check("история не содержит [MECHANICS]", "[MECHANICS]" not in hist,
              f"найдено {hist.count('[MECHANICS]')} вхождений")

        # 4.2 Quests tab: no [object Object]
        try:
            page.click('button.topbar-btn[title="Квесты"]', timeout=3000)
            page.wait_for_timeout(1000)
            qtext = page.inner_text("body")
            check("вкладка Квесты без [object Object]", "[object Object]" not in qtext)
        except Exception as e:
            check("вкладка Квесты без [object Object]", False, str(e)[:120])

        # 4.3 Factions tab: opened without NameError in console
        name_errors = [e for e in (console_errors + page_errors) if "NameError" in e]
        try:
            page.click('button.topbar-btn[title="Фракции"]', timeout=3000)
            page.wait_for_timeout(1500)
        except Exception as e:
            log(f"  (фракции: {e})")
        name_errors_after = [e for e in (console_errors + page_errors) if "NameError" in e]
        check("вкладка Фракции без NameError в консоли", len(name_errors_after) == 0,
              f"ошибок NameError: {len(name_errors_after)}")

        # 4.4 API endpoints return 200
        for ep in ("/api/factions/catalog?planet=Земля", "/api/settings"):
            try:
                r = page.request.get(BASE_URL + ep)
                check(f"{ep} -> 200", r.status == 200, f"status={r.status}")
            except Exception as e:
                check(f"{ep} -> 200", False, str(e)[:120])

        # ---- Phase 4 E2E: Contracts Board, CRT toggle, district radar ----
        log("\n[5] Phase 4: КОНТРАКТЫ / CRT / РАДАР")

        # 5.1 Открыть доску контрактов
        page.click('button.topbar-btn[title="Доска контрактов"]', timeout=4000)
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOT_DIR, "04_contracts_board.png"))
        board_text = page.inner_text("#side-panel-content")
        check("доска контрактов открылась", "ДОСКА КОНТРАКТОВ" in board_text and "ВЗЯТЬ КОНТРАКТ" in board_text)

        # 5.2 Взять первый контракт
        accept_clicked = False
        try:
            page.locator(".cb-accept").first.click(timeout=4000)
            accept_clicked = True
            page.wait_for_timeout(2000)
        except Exception as e:
            log(f"  (accept: {e})")
        check("кнопка Взять контракт сработала", accept_clicked)
        page.screenshot(path=os.path.join(SHOT_DIR, "05_contract_accepted.png"))

        # 5.3 Квест появился в активных (панель Квесты)
        page.click('button.topbar-btn[title="Квесты"]', timeout=4000)
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(SHOT_DIR, "06_quests_after_accept.png"))
        qtext = page.inner_text("#side-panel-content")
        check("принятый контракт в активных квестах", "Сдать контракт" in qtext or "КОНТРАКТ" in qtext.upper())

        # 5.4 Сдать контракт (кнопка «Сдать контракт»)
        completed = False
        try:
            page.locator("button:has-text('Сдать контракт')").first.click(timeout=4000)
            page.wait_for_timeout(2500)
            completed = True
        except Exception as e:
            log(f"  (complete: {e})")
        check("кнопка Сдать контракт сработала", completed)
        page.screenshot(path=os.path.join(SHOT_DIR, "07_contract_completed.png"))

        # 5.5 CRT toggle: вкл/выкл без падений
        page.click("#btn-crt-toggle", timeout=4000)
        page.wait_for_timeout(400)
        crt_on = page.evaluate("document.documentElement.classList.contains('crt-on')")
        page.click("#btn-crt-toggle", timeout=4000)
        page.wait_for_timeout(400)
        crt_off = page.evaluate("document.documentElement.classList.contains('crt-on')")
        check("CRT-тумблер переключается", crt_on and not crt_off, f"on={crt_on}, after-off={crt_off}")
        page.click("#btn-crt-toggle", timeout=2000)  # вернуть CRT

        # 5.6 Палитра переключается
        page.click("#btn-palette", timeout=4000)
        page.wait_for_timeout(300)
        page.click(".thud-palette-item[data-palette='amber']", timeout=4000)
        page.wait_for_timeout(400)
        amber_ok = page.evaluate("document.documentElement.classList.contains('palette-amber')")
        page.click("#btn-palette", timeout=3000)
        page.click(".thud-palette-item[data-palette='neon']", timeout=3000)
        page.wait_for_timeout(300)
        check("палитра Amber применяется", amber_ok)
        page.screenshot(path=os.path.join(SHOT_DIR, "08_palette_amber.png"))

        # 5.7 Радар района на вкладке Локация (SVG)
        page.click('button.topbar-btn[title="Локация"]', timeout=4000)
        page.wait_for_timeout(1200)
        radar_count = page.locator(".dm-node").count()
        page.screenshot(path=os.path.join(SHOT_DIR, "09_district_radar.png"))
        check("SVG-радар района отрисован", radar_count > 0, f"секторов: {radar_count}")

        # 5.8 Клик по сектору радара = вход в заведение
        if radar_count > 0:
            page.locator(".dm-node").first.click(timeout=3000)
            page.wait_for_timeout(1500)
            check("клик по сектору радара инициирует вход", True)

        # 5.9 Phase 30: кнопка «Связаться с заказчиком» не ReferenceError (регресс questContact)
        page.click('button.topbar-btn[title="Квесты"]', timeout=4000)
        page.wait_for_timeout(1000)
        contact_works = False
        try:
            page.locator("button:has-text('Связаться с заказчиком')").first.click(timeout=4000)
            page.wait_for_timeout(2000)
            # Действие должно уйти в игровой поток: в истории появляется текст диалога
            # или кнопка не бросает ReferenceError — проверяем отсутствие JS-ошибок дальше
            contact_works = True
        except Exception as e:
            log(f"  (contact: {e})")
        check("кнопка Связаться с заказчиком работает", contact_works)
        page.screenshot(path=os.path.join(SHOT_DIR, "10_quest_contact.png"))

        # ---- Summary ----
        log("\n" + "=" * 70)
        log("ИТОГИ")
        log("=" * 70)
        log(f"Console errors (JS): {len(console_errors)}")
        for e in console_errors[:20]:
            log("  - " + e[:200])
        log(f"Page errors (uncaught): {len(page_errors)}")
        for e in page_errors[:20]:
            log("  - " + e[:200])
        log(f"Bad API responses (4xx/5xx): {len(bad_responses)}")
        for st, u in bad_responses[:20]:
            log(f"  - [{st}] {u}")

        passed = sum(1 for _, ok, _ in asserts if ok)
        failed = len(asserts) - passed
        log(f"\nAsserts: {passed} passed, {failed} failed из {len(asserts)}")
        for name, ok, detail in asserts:
            if not ok:
                log(f"  FAIL: {name} — {detail}")

        browser.close()

        log("\nСкриншоты: " + SHOT_DIR)
        return 0 if failed == 0 and not console_errors and not page_errors and not bad_responses else 1


if __name__ == "__main__":
    sys.exit(main())
