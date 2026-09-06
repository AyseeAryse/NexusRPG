#!/usr/bin/env python3
"""Real CDP test: headless Chrome + raw CDP + real click"""
import subprocess, time, json, sys, urllib.request, websocket

subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
proc = subprocess.Popen([chrome_path, '--remote-debugging-port=9234',
    '--headless=new', '--no-sandbox', '--disable-gpu',
    '--disable-dev-shm-usage', '--remote-allow-origins=*', 'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='D:/NexusRPG-main')
print(f'Chrome PID: {proc.pid}')
time.sleep(5)
resp = urllib.request.urlopen('http://localhost:9234/json')
tabs = json.loads(resp.read())
page_tabs = [t for t in tabs if t.get('type') == 'page']
ws_url = page_tabs[0]['webSocketDebuggerUrl']
ws = websocket.WebSocket()
ws.connect(ws_url)

mid = [0]
def cdp(m, p=None):
    mid[0] += 1
    ws.send(json.dumps({'id': mid[0], 'method': m, 'params': p or {}}))
    for _ in range(200):
        r = json.loads(ws.recv())
        if r.get('id') == mid[0]:
            return r
    return {}

def js(expr, await_promise=True):
    r = cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': await_promise})
    val = r.get('result', {}).get('result', {}).get('value', None)
    return val

cdp('Runtime.enable')
cdp('Page.enable')
cdp('Network.enable')
cdp('Log.enable')
time.sleep(1)
cdp('Page.navigate', {'url': 'http://localhost:8080/'})
time.sleep(5)

# Setup
js("""
(async () => {
    let r = await fetch('/api/state');
    let d = await r.json();
    gameState = d;
    const content = document.getElementById('side-panel-content');
    window.renderCharacterPanel(content);
    await new Promise(r => setTimeout(r, 500));
    return 'ok';
})()
""")

# List all attr-item names
items = js("""
(function() {
    const items = document.querySelectorAll('.attr-item');
    let result = [];
    items.forEach(item => {
        const name = item.querySelector('.attr-name')?.textContent || '';
        const val = item.querySelector('.attr-val')?.textContent || '';
        const onclick = item.getAttribute('onclick') || '';
        result.push({name, val, onclick});
    });
    return JSON.stringify(result);
})()
""")
print('All attr-items:')
for item in json.loads(items):
    print(f'  {item}')

ws.close()
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)