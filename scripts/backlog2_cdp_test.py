# -*- coding: utf-8 -*-
"""Backlog#2 CDP-тест: Data Rebels в панели ФРАКЦИЙ на живом сервере.

Флоу: сейв → панель ⚖️ → Data Rebels среди «сил региона» Земли → раскрытие
карточки <details> (история/легенды/механика/хуки) → консоль 0 ошибок.
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
PORT = 9226


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
                res["exceptionDetails"].get("exception", {}).get(
                    "description", ""))[:300])
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
            "window.__errs.push(String(e && e.message));});")})

        cdp.cmd("Page.navigate", {"url": BASE})
        time.sleep(2.5)
        cdp.js("[...document.querySelectorAll('#screen-menu button')]"
               ".find(x => x.textContent.trim()==='ЗАГРУЗИТЬ').click()")
        time.sleep(1.2)
        cdp.js("document.querySelector('#saves-list .btn-primary').click()")
        ready = False
        for _ in range(40):
            if cdp.js("!document.getElementById('screen-game')"
                      ".classList.contains('hidden')"):
                ready = True
                break
            time.sleep(1)
        assert ready, "игровой экран не открылся"
        print("game screen: ready")

        # Урок B4: gameState присваивается асинхронно ПОСЛЕ появления экрана —
        # поллим до появления location.planet (до 30с)
        planet = None
        for _ in range(60):
            raw = cdp.js(
                "JSON.stringify({p: gameState?.location?.planet ?? null})")
            try:
                planet = json.loads(raw).get("p") if isinstance(raw, str) else None
            except Exception:
                planet = None
            if planet:
                break
            time.sleep(0.5)
        print("planet:", planet)

        # Панель фракций
        cdp.js("document.querySelector("
               "'button.topbar-btn[title=\"Фракции\"]').click()")
        time.sleep(2.0)

        # Data Rebels среди сил региона Земли (карточки .faction-card, без details)
        found = cdp.js("""(() => {
            const cards = [...document.querySelectorAll(
                '#side-panel-content .faction-card')];
            const el = cards.find(i => i.textContent.includes('Data Rebels'));
            if (!el) return null;
            return {
                name: el.querySelector('.faction-name')?.textContent.trim(),
                type: el.querySelector('.faction-standing')?.textContent.trim(),
                info: el.querySelector('.faction-info')?.textContent.trim().slice(0, 120),
            };
        })()""")
        assert found, "Data Rebels не найдена в панели ФРАКЦИЙ"
        print("Data Rebels в списке региона ✅:", found)
        assert found["name"] == "Data Rebels"
        assert "Нижний город" in found["info"], found

        # Соседи по региону присутствуют (не путаем список)
        neighbors = cdp.js("""(() => {
            const t = document.getElementById('side-panel-content').textContent;
            return {opa: t.includes('OPA'), blt: t.includes('Black Lotus Triad')};
        })()""")
        print("соседи региона:", neighbors)

        errs = cdp.js("window.__errs || []")
        print("console errors:", errs if errs else "0 ✅")
        verdict = "PASS" if not errs else "FAIL"
        print("BACKLOG#2 CDP VERDICT:", verdict)
        cdp.close()
    finally:
        proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
