#!/usr/bin/env python3
"""Real CDP test: headless Chrome + raw CDP + real click on attr button"""
import subprocess, time, json, sys, urllib.request, websocket

subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
proc = subprocess.Popen([chrome_path, '--remote-debugging-port=9235',
    '--headless=new', '--no-sandbox', '--disable-gpu',
    '--disable-dev-shm-usage', '--remote-allow-origins=*', 'about:blank'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='D:/NexusRPG-main')
print(f'Chrome PID: {proc.pid}')
time.sleep(5)
resp = urllib.request.urlopen('http://localhost:9235/json')
tabs = json.loads(resp.read())
page_tabs = [t for t in tabs if t.get('type') == 'page']
ws_url = page_tabs[0]['webSocketDebuggerUrl']
print(f'CDP connected')
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
    return r.get('result', {}).get('result', {}).get('value', None)

# Enable domains
cdp('Runtime.enable')
cdp('Page.enable')
cdp('Network.enable')
cdp('Log.enable')
time.sleep(1)
cdp('Page.navigate', {'url': 'http://localhost:8080/'})
print('Navigating to game...')
time.sleep(5)

# Setup
print('Setting up...')
res = js("""
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
print(f'Setup: {res}')

# === REAL DOM ASSERTIONS ===
print()
print('=== REAL DOM ASSERTIONS (live headless Chrome) ===')

_q1 = js('document.body.innerHTML.includes("АТРИБУТЫ")')
print(f'1. Body contains АТРИБУТЫ: {_q1}')
_q2 = js('document.querySelectorAll(".attr-item").length')
print(f'2. attr-item elements: {_q2}')
_q3 = js('document.querySelectorAll(".attr-item-can-upgrade").length')
print(f'3. attr-item-can-upgrade (clickable): {_q3}')
_q4 = js('document.querySelectorAll(".attr-upgrade-btn").length')
print(f'4. attr-upgrade-btn (+ buttons): {_q4}')
_q5 = js('document.querySelectorAll(".attr-item-cap").length')
print(f'5. attr-item-cap (at max): {_q5}')
_q6 = js('document.body.innerHTML.includes("ОЧКИ АТРИБУТОВ")')
print(f'6. ОЧКИ АТРИБУТОВ section visible: {_q6}')
_q7 = js('typeof window.spendAttributePoint === "function"')
print(f'7. spendAttributePoint defined: {_q7}')

# Get ИНТ (intelligence) item details
intel_info = js("""
(function() {
    const items = document.querySelectorAll('.attr-item');
    for (const item of items) {
        const name = item.querySelector('.attr-name')?.textContent || '';
        if (name === 'ИНТ') {
            return JSON.stringify({
                name: name,
                classes: Array.from(item.classList).join(' '),
                hasBtn: !!item.querySelector('.attr-upgrade-btn'),
                onclick: item.getAttribute('onclick') || '',
                text: item.textContent
            });
        }
    }
    return 'not found';
})()
""")
print(f'8. ИНТ (Intelligence) item: {intel_info}')

# === REAL CLICK TEST ===
print()
print('=== REAL CLICK TEST ===')

# Track network
network_log = []
def track_network():
    ws.settimeout(2)
    for _ in range(50):
        try:
            msg = json.loads(ws.recv())
            m = msg.get('method', '')
            if m == 'Network.requestWillBeSent':
                req = msg.get('params', {}).get('request', {})
                url = req.get('url', '')
                method = req.get('method', '')
                if 'spend/attr' in url:
                    network_log.append(f'{method} {url} body={req.get("postData","")[:100]}')
            elif m == 'Network.responseReceived':
                resp = msg.get('params', {}).get('response', {})
                url = resp.get('url', '')
                if 'spend/attr' in url:
                    network_log.append(f'RESPONSE {resp.get("status")} {url}')
        except:
            break

# Click the + button on ИНТ
click_result = js("""
(async () => {
    const items = document.querySelectorAll('.attr-item');
    for (const item of items) {
        const name = item.querySelector('.attr-name')?.textContent || '';
        if (name === 'ИНТ' && item.classList.contains('attr-item-can-upgrade')) {
            const btn = item.querySelector('.attr-upgrade-btn');
            if (btn) {
                btn.click();
                await new Promise(r => setTimeout(r, 2000));
                return 'clicked ИНТ';
            }
        }
    }
    return 'no button found';
})()
""")
print(f'Click result: {click_result}')

# Track network
track_network()

# Verify state
unspent_after = js('gameState?.character?.unspent_attribute_points')
print(f'After click - unspent_attr_points: {unspent_after} (expected 0)')

new_int = js('gameState?.character?.attributes?.intelligence')
print(f'After click - intelligence: {new_int} (expected 6)')

# Server state
try:
    resp = urllib.request.urlopen('http://localhost:8080/api/state', timeout=5)
    ss = json.loads(resp.read())
    print(f'Server - unspent_attr: {ss["character"]["unspent_attribute_points"]} (expected 0)')
    print(f'Server - intelligence: {ss["character"]["attributes"]["intelligence"]} (expected 6)')
except Exception as e:
    print(f'Server check error: {e}')

# Check no more upgradeable items
no_upgrade = js('document.querySelectorAll(".attr-item-can-upgrade").length')
print(f'After spend - attr-item-can-upgrade: {no_upgrade} (expected 0)')

# === Network log ===
print()
print('=== NETWORK EVENTS ===')
for entry in network_log:
    print(f'  {entry}')

# === CONSOLE ===
print()
print('=== CONSOLE ERRORS ===')
ws.settimeout(2)
errors = []
for _ in range(30):
    try:
        msg = json.loads(ws.recv())
        m = msg.get('method', '')
        if m == 'Runtime.consoleAPICalled':
            level = msg.get('params', {}).get('level', 'unknown')
            args = msg.get('params', {}).get('args', [])
            if args and level in ('error', 'warning'):
                errors.append(f'  [{level}] {args[0].get("value","")[:300]}')
        elif m == 'Runtime.exceptionThrown':
            errors.append(f'  [exception] {str(msg.get("params",{}).get("exceptionDetails",{}))[:300]}')
    except:
        break
print(f'Console errors: {len(errors)}')
for e in errors:
    print(e)

ws.close()
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
print()
print('=== CDP REAL TEST COMPLETE ===')