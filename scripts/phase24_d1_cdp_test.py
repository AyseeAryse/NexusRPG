# -*- coding: utf-8 -*-
"""D1 CDP-тест: панель «ЛОКАЦИЯ» на живом сервере (headless Chrome + raw CDP).

Флоу: меню → ЗАГРУЗИТЬ → загрузка сейва → клик 🗺 в топбаре → проверка
заголовка панели, подписи .panel-hint и консоли на ошибки.
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
PORT = 9223


def http_json(path, method="GET"):
    req = urllib.request.Request(BASE.replace("8080", str(PORT)) + path, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


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
        targets = None
        for _ in range(40):
            try:
                targets = http_json("/json")
                if targets:
                    break
            except Exception:
                time.sleep(0.5)
        assert targets, "CDP endpoint не поднялся"
        page = next(t for t in targets if t.get("type") == "page")
        cdp = CDP(page["webSocketDebuggerUrl"])

        cdp.cmd("Page.enable")
        cdp.cmd("Runtime.enable")
        # Логгер ошибок консоли — инжект ДО первой навигации (на каждый новый документ)
        cdp.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": (
            "window.__errs=[];window.addEventListener('error',function(e){"
            "window.__errs.push(String(e && e.message));});")})

        def eval_js(expr):
            return cdp.js(expr)

        # 1) Открыть игру
        cdp.cmd("Page.navigate", {"url": BASE})
        time.sleep(2.5)

        # 2) Клик «ЗАГРУЗИТЬ» в главном меню
        r = eval_js("""(() => {
            const btns = [...document.querySelectorAll('#screen-menu button')];
            const b = btns.find(x => x.textContent.trim() === 'ЗАГРУЗИТЬ');
            if (!b) return 'NO_BUTTON';
            b.click(); return 'CLICKED';
        })()""")
        print("menu->saves:", r)
        time.sleep(1.5)
        print("saves-list:", str(eval_js(
            "document.getElementById('saves-list') ? "
            "document.getElementById('saves-list').innerText.slice(0,200) : 'NO_LIST'"))[:220])

        # 3) Загрузить сохранение (первая кнопка ЗАГРУЗИТЬ в списке сейвов)
        r = eval_js("""(() => {
            const b = document.querySelector('#saves-list .btn-primary');
            if (!b) return 'NO_SAVE';
            b.click(); return 'LOADING';
        })()""")
        print("load:", r)

        # 4) Ждать игровой экран (до 40с)
        ready = False
        for _ in range(40):
            v = eval_js("!document.getElementById('screen-game').classList.contains('hidden')")
            if v:
                ready = True
                break
            time.sleep(1)
        print("game screen ready:", ready)
        assert ready, "игровой экран не открылся"

        # 5) Клик по кнопке карты в топбаре (tooltip «Локация»)
        r = eval_js("""(() => {
            const b = document.querySelector('button.topbar-btn[title="Локация"]');
            if (!b) return 'NO_MAP_BTN: ' +
                [...document.querySelectorAll('.topbar-btn')].map(x => x.title).join('|');
            b.click(); return 'CLICKED';
        })()""")
        print("topbar map click:", r)
        time.sleep(2)

        # 6) Проверки панели
        title = eval_js("document.getElementById('side-panel-title') ? "
                        "document.getElementById('side-panel-title').textContent : '?'")
        hidden = eval_js("document.getElementById('side-panel').classList.contains('hidden')")
        hint = eval_js("""(() => {
            const h = document.querySelector('#side-panel-content .panel-hint');
            return h ? h.textContent.trim() : 'NO_HINT';
        })()""")
        content = eval_js("document.getElementById('side-panel-content')"
                          ".innerText.slice(0, 400)")
        print("panel title :", repr(title))
        print("panel hidden:", hidden)
        print("panel hint  :", repr(hint))
        print("content head:\n" + str(content)[:380])

        ok_title = title == "ЛОКАЦИЯ"
        ok_btn = r == "CLICKED"
        ok_hint = isinstance(hint, str) and hint.startswith("Текущая локация")

        # 7) Ошибки консоли за сессию
        errs = eval_js(
            "(window.__errs || []).concat("
            "window.__errs === undefined ? ['LOGGER_MISSING'] : [])") or []
        print("console errors:", errs if errs else "0 ✅")

        verdict = "PASS" if (ok_title and ok_btn and ok_hint and hidden is False
                             and not errs) else "FAIL"
        print("D1 VERDICT:", verdict)
        cdp.close()
    finally:
        proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
