import subprocess, time, json, os, sys, urllib.request, urllib.error, websocket

# Kill any old Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Start Chrome headless with CDP
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
proc = subprocess.Popen([
    chrome_path,
    '--remote-debugging-port=9225',
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--remote-allow-origins=*',
    'about:blank'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='D:/NexusRPG-main')
print(f'Chrome PID: {proc.pid}')
time.sleep(5)

# Verify server is running
try:
    resp = urllib.request.urlopen('http://localhost:8080/api/status')
    print("Server: OK")
except:
    print("Server: NOT RUNNING")
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
    sys.exit(1)

# Connect via CDP
resp = urllib.request.urlopen('http://localhost:9225/json')
tabs = json.loads(resp.read())
page_tabs = [t for t in tabs if t.get('type') == 'page']
ws_url = page_tabs[0]['webSocketDebuggerUrl']
print(f'CDP connected')

ws = websocket.WebSocket()
ws.connect(ws_url)

msg_id = [0]
def send_cdp(method, params=None):
    msg_id[0] += 1
    mid = msg_id[0]
    ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
    for _ in range(200):
        r = json.loads(ws.recv())
        if r.get('id') == mid:
            return r
    return {}

def eval_js(expr, wait_ms=100):
    # Use async/await pattern for async operations
    result = send_cdp('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
    val = result.get('result', {}).get('result', {}).get('value', None)
    if val is None:
        # Check for exception
        exc = result.get('result', {}).get('exceptionDetails')
        if exc:
            print(f"  JS exception: {json.dumps(exc, indent=2)[:300]}")
    return val

# Enable domains
send_cdp('Runtime.enable')
send_cdp('Page.enable')
send_cdp('Network.enable')
time.sleep(1)

# Navigate to game
send_cdp('Page.navigate', {'url': 'http://localhost:8080/'})
print('Navigating to game...')
time.sleep(5)

# Create character + start game using async/await
# This ensures the fetch completes before we proceed
print('Creating character and starting game...')
setup_js = """
(async () => {
    // Create character
    let resp = await fetch('/api/character/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: 'CDPRealTest2', origin: 'ORIGIN_EARTH_SLUMS', formative_years: 'FY_UNIVERSITY', specialization: 'SPEC_HACKER', age: 25})
    });
    let data = await resp.json();
    window.gameState = {character: data, phase: 'menu'};
    window.updateGameUI(window.gameState);
    
    // Start game
    resp = await fetch('/api/game/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({preset_id: 'custom'})
    });
    data = await resp.json();
    if (data.game_state) {
        window.gameState = data.game_state;
        window.updateGameUI(window.gameState);
    }
    
    return 'done';
})()
"""
result = eval_js(setup_js, wait_ms=100)
print(f'Setup result: {result}')
time.sleep(2)

# Check phase
phase = eval_js('window.gameState?.phase || "unknown"')
print(f'Phase: {phase}')

# Check character was created
char_name = eval_js('window.gameState?.character?.name || "none"')
print(f'Character name: {char_name}')

# Give the character attr points directly in JS state
eval_js("""
window.gameState.character.unspent_attribute_points = 1;
window.gameState.character.level = 4;
window.gameState.character.max_attribute = 8;
window.gameState.character.attributes.intelligence = 5;
window.gameState.character.attributes.strength = 5;
"done"
""")

# Render the character panel directly to the side panel content
# This bypasses the UI button click and directly calls the render function
render_result = eval_js("""
const content = document.getElementById('side-panel-content');
if (content) {
    window.renderCharacterPanel(content);
    "rendered";
} else {
    "no side-panel-content element found";
}
""")
print(f'Render panel result: {render_result}')
time.sleep(2)

# === REAL DOM ASSERTIONS ===
print()
print('=== REAL DOM ASSERTIONS (live headless Chrome CDP) ===')
print()

# Check if the panel has attr content
has_attrs_title = eval_js('document.body.innerHTML.includes("АТРИБУТЫ")')
print(f'1. Body contains АТРИБУТЫ: {has_attrs_title}')

attr_item_count = eval_js('document.querySelectorAll(".attr-item").length')
print(f'2. attr-item elements in DOM: {attr_item_count}')

attr_upgrade_count = eval_js('document.querySelectorAll(".attr-item-can-upgrade").length')
print(f'3. attr-item-can-upgrade count: {attr_upgrade_count} (expected: 8 attrs, all clickable since <8 cap)')

upgrade_btn_count = eval_js('document.querySelectorAll(".attr-upgrade-btn").length')
print(f'4. attr-upgrade-btn (+ buttons) count: {upgrade_btn_count}')

attr_cap_count = eval_js('document.querySelectorAll(".attr-item-cap").length')
print(f'5. attr-item-cap count: {attr_cap_count} (expected: 0, none at cap yet)')

has_points_label = eval_js('document.body.innerHTML.includes("ОЧКИ АТРИБУТОВ")')
print(f'6. ОЧКИ АТРИБУТОВ section visible (unspent>0): {has_points_label}')

spend_fn = eval_js('typeof window.spendAttributePoint === "function"')
print(f'7. spendAttributePoint function defined: {spend_fn}')

# Get the full attr-grid HTML
attr_grid_html = eval_js('document.querySelector(".attr-grid")?.innerHTML || "NOT FOUND"')
print(f'8. attr-grid HTML (first 500 chars):')
if attr_grid_html and attr_grid_html != 'NOT FOUND':
    print(f'   {str(attr_grid_html)[:500]}')
else:
    print(f'   {attr_grid_html}')

# Check specific attribute rendering
intel_item_html = eval_js("""
const items = document.querySelectorAll('.attr-item');
let result = '';
items.forEach(item => {
    const name = item.querySelector('.attr-name')?.textContent || '';
    if (name.includes('Интеллект')) {
        result = item.innerHTML;
    }
});
result || 'not found'
""")
print(f'9. Intelligence attr-item HTML:')
print(f'   {intel_item_html}')

# Check that intelligence IS clickable (5 < 8 cap, 1 unspent point)
intel_clickable = eval_js("""
const items = document.querySelectorAll('.attr-item');
let found = false;
let classes = '';
items.forEach(item => {
    const name = item.querySelector('.attr-name')?.textContent || '';
    if (name.includes('Интеллект')) {
        found = item.classList.contains('attr-item-can-upgrade');
        classes = Array.from(item.classList).join(', ');
    }
});
`clickable=${found} classes=${classes}`
""")
print(f'10. Intelligence clickable: {intel_clickable}')

# === REAL CLICK TEST ===
print()
print('=== REAL CLICK TEST ===')

click_js = """
(async () => {
    const items = document.querySelectorAll('.attr-item');
    let clicked = false;
    for (const item of items) {
        const name = item.querySelector('.attr-name')?.textContent || '';
        if (name.includes('Интеллект') && item.classList.contains('attr-item-can-upgrade')) {
            const btn = item.querySelector('.attr-upgrade-btn');
            if (btn) {
                btn.click();
                clicked = true;
            }
        }
    }
    // Wait a bit for the async fetch to complete
    await new Promise(r => setTimeout(r, 1500));
    return `clicked=${clicked}`;
})()
"""
click_result = eval_js(click_js)
print(f'Click result: {click_result}')

# Verify state updated
time.sleep(1)
unspent = eval_js('window.gameState?.character?.unspent_attribute_points')
print(f'After click - unspent_attr_points: {unspent} (expected 0)')

new_int = eval_js('window.gameState?.character?.attributes?.intelligence')
print(f'After click - intelligence: {new_int} (expected 6)')

# Verify no more clickable items
no_upgrade_after = eval_js('document.querySelectorAll(".attr-item-can-upgrade").length')
print(f'After spend - attr-item-can-upgrade count: {no_upgrade_after} (expected 0)')

# Check server state reflects the change
try:
    resp = urllib.request.urlopen('http://localhost:8080/api/state', timeout=5)
    server_state = json.loads(resp.read())
    print(f'Server - unspent_attr: {server_state["character"]["unspent_attribute_points"]} (expected 0)')
    print(f'Server - intelligence: {server_state["character"]["attributes"]["intelligence"]} (expected 6)')
except Exception as e:
    print(f'State check error: {e}')

# === Console error check ===
print()
print('=== CONSOLE ERROR CHECK ===')
ws.send(json.dumps({'id': 9999, 'method': 'Log.enable'}))
time.sleep(1)

ws.settimeout(3)
errors = []
while True:
    try:
        msg = ws.recv()
        m = json.loads(msg)
        if m.get('method') == 'Runtime.consoleAPICalled':
            level = m.get('params', {}).get('level', 'unknown')
            args = m.get('params', {}).get('args', [])
            if args and level in ('error', 'warning'):
                text = args[0].get('value', str(args[0].get('description', '')))[:300]
                errors.append(f'  [{level}] {text}')
        elif m.get('method') == 'Runtime.exceptionThrown':
            details = m.get('params', {}).get('exceptionDetails', {})
            text = str(details)[:300]
            errors.append(f'  [exception] {text}')
    except:
        break

print(f'Console errors: {len(errors)}')
for e in errors:
    print(e)

# Cleanup
ws.close()
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
print()
print('=== CDP REAL TEST COMPLETE ===')
