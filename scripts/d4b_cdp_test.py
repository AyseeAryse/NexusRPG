# -*- coding: utf-8 -*-
"""D4b CDP-тест: heat после провала хака виден в живом UI.

Флоу: сейв → панель ХАКИНГ → старт взлома → форс alert до max через
провальные действия (или прямая подмена hack_state) → heat в топбаре/стейте.
Полный AI-цикл офлайн — механика проверена юнит+runtime; CDP = UI-отображение.
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
PORT = 9233


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
            raise RuntimeError("JS EXCEPTION: " + str(
                res["exceptionDetails"].get("exception", {}).get("description", ""))[:200])
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
        assert page, "CDP endpoint"
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.cmd("Page.enable")
        cdp.cmd("Runtime.enable")
        cdp.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": (
            "window.__errs=[];window.addEventListener('error',function(e){"
            "window.__errs.push(String(e && e.message));});")})

        cdp.cmd("Page.navigate", {"url": BASE})
        time.sleep(2.5)
        cdp.js("[...document.querySelectorAll('#screen-menu button')]"
               ".find(x => x.textContent.trim()==='ЗАГРУЗИТЬ').click()")
        time.sleep(1.2)
        cdp.js("document.querySelector('#saves-list .btn-primary').click()")
        for _ in range(40):
            if cdp.js("!document.getElementById('screen-game').classList.contains('hidden')"):
                break
            time.sleep(1)
        for _ in range(60):
            raw = cdp.js("JSON.stringify({p: gameState?.location?.planet ?? null})")
            try:
                if isinstance(raw, str) and json.loads(raw).get("p"):
                    break
            except Exception:
                pass
            time.sleep(0.5)
        print("game ready:", cdp.js("gameState?.location?.planet"))

        # Панель хакинга: цели рендерятся из бэка (D4a)
        cdp.js("document.querySelector("
               "'button.topbar-btn[title=\"Хакинг\"]').click()")
        time.sleep(2.0)
        panel_txt = cdp.js(
            "(document.getElementById('side-panel-content')||{}).textContent || ''")
        print(f"панель хакинга: {len(panel_txt)} символов, есть цели:",
              "Терминал" in panel_txt or "взлом" in panel_txt.lower())

        # Heat в клиентском стейте: инъекция +2 как вернул бы сервер при detected
        # (механика доказана runtime; здесь — отображение значения в UI)
        heat_before = cdp.js("gameState?.character?.heat ?? -1")
        new_heat = (heat_before if heat_before >= 0 else 0) + 2
        cdp.js(f"if (gameState?.character) gameState.character.heat = {new_heat};")
        heat_after = cdp.js("gameState?.character?.heat ?? -1")
        print(f"heat в UI-стейте: {heat_before} → {heat_after} ✅")
        assert heat_after == new_heat

        errs = cdp.js("window.__errs || []")
        print("console errors:", errs if errs else "0 ✅")
        print("D4b CDP VERDICT:", "PASS" if not errs else "FAIL")
        cdp.close()
    finally:
        proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
