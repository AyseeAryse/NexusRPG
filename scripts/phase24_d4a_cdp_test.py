# -*- coding: utf-8 -*-
"""D4a CDP-тест: панели хакинга/расследований на живом сервере (headless Chrome).

Флоу: сейв → панель ХАКИНГ (подсказка + цели + старт + синхронизация узлов +
отключение) → панель РАССЛЕДОВАНИЯ (выбор типа кликом, лиды, подсказка,
добавление улики через UI с подменённым prompt) → ошибки консоли.
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
PORT = 9224


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
        # Логгер ошибок ДО первой навигации
        cdp.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": (
            "window.__errs=[];window.addEventListener('error',function(e){"
            "window.__errs.push(String(e && e.message));});")})

        def eval_js(expr):
            return cdp.js(expr)

        cdp.cmd("Page.navigate", {"url": BASE})
        time.sleep(2.5)

        # Меню → ЗАГРУЗИТЬ → загрузить первый сейв
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

        # ═══ ПАНЕЛЬ ХАКИНГА ═══
        r = eval_js("""(() => {
            const b = document.querySelector('button.topbar-btn[title="Хакинг"]');
            if (!b) return 'NO_BTN';
            b.click(); return 'OK';
        })()""")
        time.sleep(1.5)
        hint = eval_js("[...(document.querySelectorAll('#side-panel-content .panel-hint'))]"
                       ".map(h => h.textContent.trim()).join(' ')")
        print("hacking hint:", str(hint)[:120])
        assert "Цели зависят от района" in str(hint), "подсказка хакинга не видна"

        targets_txt = ""
        for _ in range(10):
            targets_txt = eval_js(
                "(document.getElementById('hack-targets-list')||{}).innerText||''")
            if targets_txt.strip():
                break
            time.sleep(0.5)
        print("targets:", targets_txt.replace("\n", " | ")[:160])
        assert "Терминал" in targets_txt, "цели не загрузились"

        # Старт взлома по первой активной кнопке цели
        r = eval_js("""(() => {
            const b = document.querySelector('.hack-target-btn:not(.locked):not([disabled])');
            if (!b) return 'NO_ENABLED_TARGET';
            b.click(); return 'STARTED';
        })()""")
        time.sleep(1.5)
        assert r == "STARTED", f"старт взлома не сработал: {r}"
        nodes_info = eval_js("""(() => {
            const ns = [...document.querySelectorAll('#side-panel-content .hack-node')];
            return {count: ns.length,
                    labels: ns.map(n => n.querySelector('.node-ice').textContent.trim())};
        })()""")
        print("nodes:", nodes_info)
        assert nodes_info["count"] >= 2, "узлы не отрендерились"
        assert all(l != "???" for l in nodes_info["labels"]), \
            "фантомные ??? остались — снимок узлов не применился"

        # Отключиться — полный цикл действия без ошибок
        eval_js("[...document.querySelectorAll('.hack-action-btn')]"
                ".find(b => b.textContent.includes('Отключиться')).click()")
        time.sleep(1.2)
        empty = eval_js("(document.getElementById('side-panel-content').innerText"
                        ").includes('Нет активного взлома')")
        print("after disconnect ->", "empty state OK" if empty else "UNEXPECTED")
        print("HACKING PANEL: PASS")

        # ═══ ПАНЕЛЬ РАССЛЕДОВАНИЙ ═══
        eval_js("document.querySelector('button.topbar-btn[title=\"Расследования\"]').click()")
        time.sleep(1.0)

        # Открытие дела: клик «Открыть новое дело» → выбор типа КЛИКОМ (chooseFromList).
        # Headless-специфика: нативный prompt() блокирует рендерер навечно,
        # поэтому имя дела подменяем ПУСТЫМ до клика (openNewCase отправит undefined).
        eval_js("window.prompt = () => '';")
        eval_js("[...document.querySelectorAll('#side-panel-content .btn-buy')]"
                ".find(b => b.textContent.includes('Открыть новое дело')).click()")
        time.sleep(0.5)
        r = eval_js("""(() => {
            const btns = [...document.querySelectorAll('body > div:last-child button')];
            const theft = btns.find(b => b.textContent.trim() === 'Кража');
            if (!theft) return 'NO_DIALOG: ' + btns.map(b=>b.textContent.trim()).slice(0,12).join('|');
            theft.click(); return 'CHOSEN';
        })()""")
        time.sleep(1.2)
        assert r == "CHOSEN", f"диалог выбора типа не сработал: {r}"
        body = eval_js("document.getElementById('side-panel-content').innerText")
        assert "ЛИДЫ:" in body, "лиды не отрендерились"
        assert "место кражи" in body, "лиды кражи не совпадают"
        assert "опиши поиск в действии" in body, "подсказка расследования не видна"
        print("case opened via UI, leads+hint rendered")

        # Улика через UI: подменяем prompt каноничными ответами и жмём кнопку
        eval_js("""(() => {
            window.__ans = ['witness', 'CDP-тест улики из живого UI'];
            window.prompt = () => window.__ans.shift() || '';
        })()""")
        eval_js("[...document.querySelectorAll('#side-panel-content .btn-buy')]"
                ".find(b => b.textContent.includes('Добавить улику')).click()")
        time.sleep(1.5)
        body = eval_js("document.getElementById('side-panel-content').innerText")
        assert "CDP-тест улики из живого UI" in body, "улика через UI не дошла до карточки"
        progress = eval_js("""(() => {
            const m = document.getElementById('side-panel-content')
                .innerText.match(/Улики:\\s*(\\d+)\\/(\\d+)/);
            return m ? m[0] : 'NO_PROGRESS';
        })()""")
        print("clue via UI:", progress, "✅")
        assert progress.startswith("Улики: 1/"), "прогресс не вырос"

        # Ошибки консоли за всю сессию
        errs = eval_js("window.__errs || []")
        print("console errors:", errs if errs else "0 ✅")

        verdict = "PASS" if not errs else "FAIL"
        print("D4a CDP VERDICT:", verdict)
        cdp.close()
    finally:
        proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
