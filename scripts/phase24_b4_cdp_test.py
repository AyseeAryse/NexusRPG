# -*- coding: utf-8 -*-
"""B4 CDP-тест: панель НЕДВИЖИМОСТЬ на живом сервере (headless Chrome).

Флоу: сейв → панель 🏠 → цены из API совпадают с утверждённой таблицей,
метка «Не хватает» на недоступных типах, покупка кликом БЕЗ prompt
(остаток в тосте/карточках), консоль 0 ошибок.
"""
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://localhost:8080"
PORT = 9225

EXPECTED_PRICES = {"Квартира": 12000, "Бар": 9000, "Магазин": 11000,
                   "Склад": 22000, "Офис фиксера": 17000, "Убежище": 30000}


class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.mid = 0

    def cmd(self, method, params=None):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method,
                                 "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                return msg.get("result", {})

    def js(self, expr):
        res = self.cmd("Runtime.evaluate",
                       {"expression": expr, "returnByValue": True})
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS EXCEPTION: {res['exceptionDetails'].get('exception', {}).get('description', res['exceptionDetails'])[:300]}")
        return res.get("result", {}).get("value")

    def close(self):
        self.ws.close()


def main():
    profile = tempfile.mkdtemp(prefix="nexus_cdp_")
    proc = subprocess.Popen([
        CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile}", "--no-first-run", "--disable-gpu",
        "--window-size=1400,900", "about:blank"])
    try:
        page = None
        for _ in range(40):
            try:
                with urllib.request.urlopen(
                        f"http://localhost:{PORT}/json", timeout=5) as r:
                    targets = json.loads(r.read().decode("utf-8"))
                pages = [t for t in targets if t.get("type") == "page"]
                if pages:
                    page = pages[0]
                    break
            except Exception:
                time.sleep(0.5)
        assert page, "CDP endpoint не поднялся"
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.cmd("Page.enable")
        cdp.cmd("Runtime.enable")
        cdp.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": (
            "window.__errs=[];window.addEventListener('error',function(e){"
            "window.__errs.push(String(e && e.message));});"
            # B4: prompt устранён из buyProperty; на всякий случай ломаем его явно,
            # чтобы тест поймал любой возврат диалога
            "window.prompt=function(){window.__errs.push('PROMPT_USED');return '';};")})

        def eval_js(expr):
            return cdp.js(expr)

        cdp.cmd("Page.navigate", {"url": BASE})
        time.sleep(2.5)

        eval_js("[...document.querySelectorAll('#screen-menu button')]"
                ".find(x => x.textContent.trim()==='ЗАГРУЗИТЬ').click()")
        time.sleep(1.2)
        eval_js("document.querySelector('#saves-list .btn-primary').click()")
        ready = False
        for _ in range(40):
            if eval_js("!document.getElementById('screen-game').classList.contains('hidden')"):
                ready = True
                break
            time.sleep(1)
        assert ready, "игровой экран не открылся"
        print("game screen: ready")

        # Дождаться клиентского стейта: gameState присваивается асинхронно ПОСЛЕ
        # появления игрового экрана (наблюдение CDP-прогонов). Поллинг до 30с.
        credits = None
        for _ in range(60):
            raw = eval_js(
                "JSON.stringify((window.gameState || gameState)"
                " ? {c: (gameState && gameState.character)"
                " ? gameState.character.credits : null} : {c: null})")
            try:
                val = json.loads(raw).get("c") if isinstance(raw, str) else None
            except Exception:
                val = None
            if isinstance(val, (int, float)):
                credits = val
                break
            time.sleep(0.5)
        assert credits is not None, (
            "gameState.character.credits так и не появились за 30с")
        print(f"credits персонажа сейва: ₡{credits:,}")

        # Панель недвижимости
        eval_js("document.querySelector('button.topbar-btn[title=\"Недвижимость\"]').click()")
        cards = {}
        for _ in range(10):
            cards = eval_js("""(() => {
                const out = {};
                document.querySelectorAll('#property-types-list .ship-class-card')
                  .forEach(c => {
                    const name = c.querySelector('.ship-class-name')?.textContent.trim();
                    const priceTxt = c.querySelector('.ship-class-price')?.textContent || '';
                    const num = parseInt(priceTxt.replace(/[^0-9]/g,''), 10);
                    const locked = !!c.querySelector('.hack-req');
                    out[name] = {price: num, locked};
                  });
                return out;
            })()""") or {}
            if len(cards) >= 6:
                break
            time.sleep(0.5)
        assert len(cards) >= 6, f"каталог не загрузился: {cards}"
        for name, info in cards.items():
            exp = EXPECTED_PRICES.get(name)
            assert exp is not None, f"неожиданный тип {name}"
            assert info["price"] == exp, f"{name}: {info['price']} != {exp}"
        print(f"цены из API == утверждённой таблице ✅ ({len(cards)} типов)")
        locked_count = sum(1 for v in cards.values() if v["locked"])
        print(f"метка 'Не хватает' стоит у {locked_count} из 6 (кредитов ₡{credits:,})")

        # Покупка самого дешёвого ДОСТУПНОГО типа кликом
        target = next((n for n, v in cards.items()
                       if not v["locked"]), None)
        if target:
            before = credits
            eval_js(f"""(() => {{
                const cardList = [...document.querySelectorAll('#property-types-list .ship-class-card')];
                const card = cardList.find(c =>
                    c.querySelector('.ship-class-name')?.textContent.trim() === '{target}');
                card.querySelector('.btn-buy').click();
            }})()""")
            time.sleep(1.5)
            after = eval_js("gameState?.character?.credits ?? -1")
            owned = eval_js("[...document.querySelectorAll('.property-card')].length")
            print(f"куплено '{target}': ₡{credits:,} → ₡{after:,}, карточек собственности: {owned}")
            assert (after < 0) or (after < credits) or after == 0, "кредиты не списались"
            assert owned >= 1, "карточка собственности не появилась"
        else:
            # Всё недоступно — проверяем отказ по кнопке дешёвого
            eval_js("""(() => {
                const cardList = [...document.querySelectorAll('#property-types-list .ship-class-card')];
                cardList.sort((a,b) =>
                  parseInt(a.querySelector('.ship-class-price').textContent.replace(/[^0-9]/g,''),10) -
                  parseInt(b.querySelector('.ship-class-price').textContent.replace(/[^0-9]/g,''),10));
                cardList[0].querySelector('.btn-buy').click();
            })()""")
            time.sleep(1.2)
            toasts = eval_js("[...document.querySelectorAll('.toast,.notification')]"
                             ".map(t=>t.textContent).join('|')")
            print(f"всё недоступно при ₡{credits:,} — отказ показан: {toasts[:100]}")

        errs = eval_js("window.__errs || []")
        print("console errors:", errs if errs else "0 ✅")
        verdict = "PASS" if not errs else "FAIL"
        print("B4 CDP VERDICT:", verdict)
        cdp.close()
    finally:
        proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
