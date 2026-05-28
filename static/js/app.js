/* ============================================================
   NEXUS RPG — Client Application v3 (all fixes)
   ============================================================ */

// ---- Toast Notification System ----
function showToast(message, type = 'error', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;top:16px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;max-width:400px;';
        document.body.appendChild(container);
        // Add animation
        const style = document.createElement('style');
        style.textContent = '@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}';
        document.head.appendChild(style);
    }
    const toast = document.createElement('div');
    const colors = { error: '#ff4444', success: '#44ff44', info: '#44aaff', warning: '#ffaa00' };
    const icons = { error: '❌', success: '✅', info: 'ℹ️', warning: '⚠️' };
    toast.style.cssText = `padding:12px 16px;border-radius:8px;color:#fff;font-size:14px;background:${colors[type]||colors.info}33;border:1px solid ${colors[type]||colors.info};backdrop-filter:blur(10px);animation:slideIn 0.3s ease;cursor:pointer;`;
    toast.textContent = `${icons[type]||''} ${message}`;
    toast.onclick = () => toast.remove();
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, duration);
}

// ---- Safe API fetch wrapper ----
async function apiFetch(url, options = {}) {
    try {
        const resp = await fetch(url, options);
        if (!resp.ok) {
            const data = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }));
            showToast(data.error || `Ошибка ${resp.status}: ${url}`, 'error');
            return { _error: true, ...data };
        }
        return await resp.json();
    } catch (err) {
        showToast(`Сервер недоступен: ${err.message}`, 'error');
        return { _error: true, error: err.message };
    }
}

// ---- State ----
let gameState = null;
let selectedPreset = null;
let isSending = false;
let creationMode = null;
let creationData = null;
let customChar = { origin: null, formative: null, specialization: null, attributes: {}, skills: {} };

// ---- Skill/Attr names ----
const SKILL_NAMES = {
    hacking: 'Хакинг', piloting: 'Пилотирование', negotiation: 'Переговоры',
    combat: 'Бой', stealth: 'Скрытность', technology: 'Технологии',
    medicine: 'Медицина', engineering: 'Инженерия', education: 'Образование',
    criminal: 'Криминал', law: 'Право', biology: 'Биология',
    survival: 'Выживание', diplomacy: 'Дипломатия', bureaucracy: 'Бюрократия',
};
const ATTR_LABELS = {
    strength:'СИЛ', dexterity:'ЛОВ', intelligence:'ИНТ', charisma:'ХАР',
    endurance:'ВЫН', willpower:'ВОЛ', reflexes:'РЕФ', tech_empathy:'ТЕХ'
};

function attrLabel(key) { return ATTR_LABELS[key] || key; }
function skillLabel(key) { return SKILL_NAMES[key] || key; }

// ---- Screen Management ----
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById('screen-' + id);
    if (screen) {
        screen.classList.add('active');
        if (id === 'menu') checkAIStatus();
        if (id === 'char-create') initCharCreation();
    }
}

// ---- Boot Sequence ----
async function bootSequence() {
    const status = document.getElementById('boot-status');
    const bar = document.getElementById('boot-progress-bar');
    const actions = document.getElementById('boot-actions');
    const errDiv = document.getElementById('boot-error');

    const lines = [
        { text: '[SYS] Загрузка ядра NEXUS v3.87...', delay: 300 },
        { text: '[SYS] Инициализация баз данных...', delay: 400 },
        { text: '[KB]  Загрузка игровых файлов...', delay: 500 },
        { text: '[AI]  Подключение к AI-бэкенду...', delay: 600 },
    ];

    let progress = 0;
    for (const line of lines) {
        await sleep(line.delay);
        addBootLine(status, line.text);
        progress += 20;
        bar.style.width = progress + '%';
    }

    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        addBootLine(status, `[KB]  Загружено файлов: ${data.game_files}`, 'ok');
        progress += 15; bar.style.width = progress + '%';
        await sleep(300);

        if (data.ai.status === 'ok') {
            addBootLine(status, `[AI]  Подключено: ${data.ai.backend} (${data.ai.models?.length || 0} моделей)`, 'ok');
            progress = 100;
        } else {
            addBootLine(status, `[AI]  ⚠ AI не подключен: ${data.ai.hint || data.ai.status}`, 'warn');
            addBootLine(status, '[AI]  Настройте в меню Настройки', 'warn');
            progress = 90;
        }
        bar.style.width = progress + '%';
        if (data.saves > 0) addBootLine(status, `[SAV] Найдено сохранений: ${data.saves}`, 'ok');
    } catch (e) {
        addBootLine(status, `[ERR] ${e.message}`, 'error');
        errDiv.textContent = 'Не удалось подключиться к серверу.';
        errDiv.classList.remove('hidden');
    }

    await sleep(500);
    addBootLine(status, '[SYS] Система готова.', 'ok');
    bar.style.width = '100%';
    actions.classList.remove('hidden');
}

function addBootLine(container, text, cls) {
    const div = document.createElement('div');
    div.className = 'boot-line ' + (cls || '');
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ---- AI Status ----
async function checkAIStatus() {
    const el = document.getElementById('menu-ai-status');
    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        if (data.ai.status === 'ok') {
            el.textContent = `AI: ✓ ${data.ai.backend} (${data.ai.current_model || data.ai.models?.[0] || '?'})`;
            el.className = 'ai-status connected';
        } else {
            el.textContent = 'AI: ✗ не подключен';
            el.className = 'ai-status error';
        }
    } catch {
        el.textContent = 'AI: ✗ сервер недоступен';
        el.className = 'ai-status error';
    }
}

// ============================================================
// SETTINGS — with auto model scanning
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[name="backend"]').forEach(r => {
        r.addEventListener('change', () => {
            document.getElementById('ollama-settings').classList.toggle('hidden', r.value !== 'ollama');
            document.getElementById('lmstudio-settings').classList.toggle('hidden', r.value !== 'lmstudio');
            const cloudEl = document.getElementById('cloud-settings');
            if (cloudEl) cloudEl.classList.toggle('hidden', r.value !== 'cloud_api');
        });
    });
});

function onCloudProviderChange() {
    const sel = document.getElementById('inp-cloud-provider');
    const urlInput = document.getElementById('inp-cloud-url');
    if (sel.value === 'custom') {
        urlInput.classList.remove('hidden');
        urlInput.value = '';
    } else {
        urlInput.classList.add('hidden');
        urlInput.value = sel.value;
    }
}

async function refreshModels(backend) {
    const selectId = backend === 'ollama' ? 'inp-ollama-model' : 'inp-lmstudio-model';
    const select = document.getElementById(selectId);
    if (!select) return;
    select.innerHTML = '<option value="">⏳ Сканирование...</option>';

    // Save URL first
    const urlInput = backend === 'ollama' ? 'inp-ollama-url' : 'inp-lmstudio-url';
    const urlVal = document.getElementById(urlInput)?.value;
    if (urlVal) {
        await fetch('/api/settings', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ backend, [backend === 'ollama' ? 'ollama_url' : 'lmstudio_url']: urlVal })
        });
    }

    try {
        const resp = await fetch('/api/models');
        const data = await resp.json();
        select.innerHTML = '';
        if (data.models && data.models.length > 0) {
            data.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m; opt.textContent = m;
                if (m === data.current) opt.selected = true;
                select.appendChild(opt);
            });
        } else {
            select.innerHTML = '<option value="">— модели не найдены —</option>';
        }
    } catch {
        select.innerHTML = '<option value="">— ошибка подключения —</option>';
    }
}

async function saveSettings() {
    const backend = document.querySelector('input[name="backend"]:checked').value;
    let model = '';
    if (backend === 'ollama') model = document.getElementById('inp-ollama-model')?.value || '';
    else if (backend === 'lmstudio') model = document.getElementById('inp-lmstudio-model')?.value || '';
    else if (backend === 'cloud_api') model = document.getElementById('inp-cloud-model')?.value || 'gpt-4o-mini';

    const cloudUrl = document.getElementById('inp-cloud-provider')?.value === 'custom'
        ? document.getElementById('inp-cloud-url')?.value
        : document.getElementById('inp-cloud-provider')?.value;

    const payload = {
        backend,
        ollama_url: document.getElementById('inp-ollama-url').value,
        lmstudio_url: document.getElementById('inp-lmstudio-url').value,
        cloud_url: cloudUrl || '',
        cloud_key: document.getElementById('inp-cloud-key')?.value || '',
        model,
        temperature: parseFloat(document.getElementById('inp-temperature').value),
        max_tokens: parseInt(document.getElementById('inp-max-tokens').value),
    };

    const statusEl = document.getElementById('settings-status');
    try {
        await fetch('/api/settings', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        statusEl.textContent = '✓ Настройки сохранены';
        statusEl.className = 'status-message ok';
    } catch (e) {
        statusEl.textContent = `✗ ${e.message}`;
        statusEl.className = 'status-message error';
    }
}

async function testConnection() {
    const statusEl = document.getElementById('settings-status');
    statusEl.textContent = 'Проверка...';
    await saveSettings();
    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        if (data.ai.status === 'ok') {
            statusEl.textContent = `✓ Подключено! Модели: ${data.ai.models?.join(', ')}`;
            statusEl.className = 'status-message ok';
            const backend = document.querySelector('input[name="backend"]:checked').value;
            refreshModels(backend);
        } else {
            statusEl.textContent = `✗ ${data.ai.hint || 'Не удалось подключиться'}`;
            statusEl.className = 'status-message error';
        }
    } catch (e) {
        statusEl.textContent = `✗ ${e.message}`;
        statusEl.className = 'status-message error';
    }
}

async function loadSettings() {
    try {
        const resp = await fetch('/api/settings');
        const data = await resp.json();
        const backend = data.backend || 'ollama';
        
        // Set radio button
        const radio = document.getElementById(`radio-${backend === 'cloud_api' ? 'cloud' : backend}`);
        if (radio) radio.checked = true;
        
        // Show/hide panels
        document.getElementById('ollama-settings').classList.toggle('hidden', backend !== 'ollama');
        document.getElementById('lmstudio-settings').classList.toggle('hidden', backend !== 'lmstudio');
        const cloudEl = document.getElementById('cloud-settings');
        if (cloudEl) cloudEl.classList.toggle('hidden', backend !== 'cloud_api');
        
        document.getElementById('inp-ollama-url').value = data.ollama_url || '';
        document.getElementById('inp-lmstudio-url').value = data.lmstudio_url || '';
        document.getElementById('inp-temperature').value = data.temperature || 0.8;
        document.getElementById('temp-val').textContent = data.temperature || 0.8;
        document.getElementById('inp-max-tokens').value = data.max_tokens || 6048;
        
        // Cloud API settings
        if (data.cloud_url) {
            const provider = document.getElementById('inp-cloud-provider');
            const urlInput = document.getElementById('inp-cloud-url');
            if (provider) {
                const match = [...provider.options].find(o => o.value === data.cloud_url);
                if (match) { provider.value = data.cloud_url; }
                else { provider.value = 'custom'; if (urlInput) { urlInput.classList.remove('hidden'); urlInput.value = data.cloud_url; } }
            }
        }
        if (data.cloud_model) {
            const cm = document.getElementById('inp-cloud-model');
            if (cm) cm.value = data.cloud_model;
        }
        
        if (backend !== 'cloud_api') refreshModels(backend);
    } catch {}
}

// ============================================================
// CHARACTER CREATION
// ============================================================

async function initCharCreation() {
    creationMode = null;
    customChar = { origin: null, formative: null, specialization: null, attributes: {}, skills: {} };
    selectedPreset = null;
    goCreationStep(0);
    if (!creationData) {
        try {
            const resp = await fetch('/api/creation-data');
            creationData = await resp.json();
        } catch (e) { console.error('Failed to load creation data:', e); }
    }
}

function setCreationMode(mode) {
    creationMode = mode;
    if (mode === 'preset') { goCreationStep('1a'); loadPresets(); }
    else { goCreationStep(1); }
}

function goCreationStep(step) {
    document.querySelectorAll('.creation-step').forEach(s => s.classList.remove('active'));
    const target = document.getElementById('cstep-' + step);
    if (target) target.classList.add('active');

    const stepNum = typeof step === 'number' ? step : (step === '1a' ? 1 : 0);
    document.querySelectorAll('.step-dot').forEach(d => {
        d.classList.toggle('active', parseInt(d.dataset.step) <= stepNum);
    });

    const names = {
        0: 'Режим создания',
        '1a': 'Готовый пресет',
        1: 'Имя, возраст и предыстория',
        2: 'Происхождение',
        3: 'Годы становления',
        4: 'Специализация',
        5: 'Распределение очков',
    };
    document.getElementById('creation-step-name').textContent = names[step] || '';

    if (step === 2 && creationData) renderOrigins();
    if (step === 3 && creationData) renderFormativeYears();
    if (step === 4 && creationData) renderSpecializations();
    if (step === 5 && creationData) renderPointAllocation();
}

// ---- Presets ----
async function loadPresets() {
    const grid = document.getElementById('preset-grid');
    try {
        const resp = await fetch('/api/presets');
        const presets = await resp.json();
        grid.innerHTML = '';
        presets.forEach(p => {
            const card = document.createElement('div');
            card.className = 'preset-card';
            const attrs = p.final_stats?.attributes || {};
            const creds = p.final_stats?.starting_resources?.credits || 0;
            let statsHtml = '';
            for (const [k, v] of Object.entries(attrs)) {
                statsHtml += `<div class="preset-stat-item"><span>${attrLabel(k)}</span><span class="val">${v}</span></div>`;
            }
            card.innerHTML = `
                <div class="preset-name">${p.name}</div>
                <div class="preset-desc">${p.description || ''}</div>
                <div class="preset-stats">${statsHtml}</div>
                <div class="preset-diff">₡${formatNum(creds)}</div>
            `;
            card.onclick = () => {
                selectedPreset = p;
                document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                document.getElementById('char-name-section-preset').classList.remove('hidden');
            };
            grid.appendChild(card);
        });
    } catch { grid.innerHTML = '<div class="empty-state">Ошибка загрузки</div>'; }
}

async function startGamePreset() {
    if (!selectedPreset) return alert('Выберите пресет!');
    const name = document.getElementById('inp-char-name-preset').value.trim();
    if (!name) return alert('Введите имя!');
    showLoading(true);
    try {
        await fetch('/api/character/create', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ preset_id: selectedPreset.id })
        });
        const resp = await fetch('/api/game/start', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name })
        });
        const data = await resp.json();
        gameState = data.game_state;
        updateGameUI(gameState);
        clearNarrative();
        if (data.narrative) addNarrativeMessage(data.narrative, 'gm');
        showScreen('game');
    } catch (e) { alert('Ошибка: ' + e.message); }
    showLoading(false);
}

// ---- Custom Creation Steps ----
function renderOrigins() {
    const list = document.getElementById('origins-list');
    list.innerHTML = '';
    const origins = creationData.origins || [];
    // Group by region
    const groups = {};
    origins.forEach(o => {
        const g = o.group || 'Другое';
        if (!groups[g]) groups[g] = [];
        groups[g].push(o);
    });
    for (const [groupName, items] of Object.entries(groups)) {
        const groupHeader = document.createElement('div');
        groupHeader.className = 'option-group-header';
        groupHeader.textContent = groupName;
        list.appendChild(groupHeader);
        items.forEach(o => {
            const item = document.createElement('div');
            item.className = 'option-card' + (customChar.origin === o.id ? ' selected' : '');
            let modsHtml = renderModBadges(o.attr_mods, o.skill_mods);
            const rarity = o.rarity ? `<span class="rarity-badge rarity-${o.rarity}">${o.rarity}</span>` : '';
            const credits = o.credits ? `<span class="credits-badge">₡${formatNum(o.credits)}</span>` : '';
            item.innerHTML = `
                <div class="option-header">
                    <div class="option-name">${o.name}</div>
                    <div class="option-tags">${rarity}${credits}</div>
                </div>
                <div class="option-desc">${o.description || ''}</div>
                ${modsHtml}
            `;
            item.onclick = () => {
                customChar.origin = o.id;
                list.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
                item.classList.add('selected');
                document.getElementById('btn-origin-next').disabled = false;
            };
            list.appendChild(item);
        });
    }
}

function renderFormativeYears() {
    const list = document.getElementById('formative-list');
    list.innerHTML = '';
    const years = creationData.formative_years || [];
    const originId = customChar.origin || '';
    
    // Origin → excluded formative year groups
    // Elite/Corp origins can't have criminal street backgrounds
    // Street/refugee origins can't have elite corporate backgrounds
    const ORIGIN_EXCLUSIONS = {
        // Элита и корпорации — нет криминала
        'ORIGIN_EARTH_ELITE':      ['Криминальные'],
        'ORIGIN_EARTH_CORP_HEIR':  ['Криминальные'],
        'ORIGIN_EARTH_DIPLOMAT':   ['Криминальные'],
        'ORIGIN_UNIQUE_MAGNATE':   ['Криминальные'],
        // Трущобы, беженцы — нет элитного корпоратива
        'ORIGIN_EARTH_SLUMS':      ['Корпоративные'],
        'ORIGIN_EARTH_REFUGEE':    ['Корпоративные'],
        'ORIGIN_MARS_TUNNELER':    ['Корпоративные'],
        // Повстанцы — нет корпоратива
        'ORIGIN_MARS_REBEL':       ['Корпоративные'],
        // Контрабандисты — нет корпоратива
        'ORIGIN_BELT_SMUGGLER':    ['Корпоративные'],
    };
    
    // Also exclude specific formative events by logic
    const ORIGIN_EXCLUDE_SPECIFIC = {
        'ORIGIN_EARTH_ELITE':     ['FY_STREET_LIFE','FY_SLUMS_GANGWAR','FY_SMUGGLING_RUNS','FY_UNDERGROUND_FIGHTS','FY_PIRATE_CAPTIVE'],
        'ORIGIN_EARTH_CORP_HEIR': ['FY_STREET_LIFE','FY_SLUMS_GANGWAR','FY_SMUGGLING_RUNS','FY_UNDERGROUND_FIGHTS','FY_PIRATE_CAPTIVE'],
        'ORIGIN_UNIQUE_MAGNATE':  ['FY_STREET_LIFE','FY_SLUMS_GANGWAR','FY_UNDERGROUND_FIGHTS'],
        'ORIGIN_EARTH_DIPLOMAT':  ['FY_STREET_LIFE','FY_SLUMS_GANGWAR','FY_UNDERGROUND_FIGHTS','FY_SMUGGLING_RUNS'],
        'ORIGIN_EARTH_SLUMS':     ['FY_FAMILY_BUSINESS','FY_CORP_INTERNSHIP','FY_DIPLOMATIC_MISSION','FY_ELITE_BOARDING_SCHOOL'],
        'ORIGIN_EARTH_REFUGEE':   ['FY_FAMILY_BUSINESS','FY_CORP_INTERNSHIP','FY_DIPLOMATIC_MISSION','FY_SPORTS_ACHIEVEMENTS','FY_ELITE_BOARDING_SCHOOL'],
        'ORIGIN_MARS_TUNNELER':   ['FY_FAMILY_BUSINESS','FY_CORP_INTERNSHIP','FY_DIPLOMATIC_MISSION','FY_ELITE_BOARDING_SCHOOL'],
        'ORIGIN_BELT_MINER':      ['FY_FAMILY_BUSINESS','FY_DIPLOMATIC_MISSION','FY_ELITE_BOARDING_SCHOOL'],
        'ORIGIN_UNIQUE_AI_CHILD': ['FY_LOVE_TRIANGLE','FY_FAMILY_BUSINESS','FY_ELITE_BOARDING_SCHOOL','FY_MEDIA_SENSATION'],
    };
    
    const excludedGroups = ORIGIN_EXCLUSIONS[originId] || [];
    const excludedIds = ORIGIN_EXCLUDE_SPECIFIC[originId] || [];
    
    const groups = {};
    const compatible = [];
    const incompatible = [];
    
    years.forEach(fy => {
        const isExcluded = excludedGroups.includes(fy.group) || excludedIds.includes(fy.id);
        if (isExcluded) incompatible.push(fy);
        else compatible.push(fy);
    });
    
    // Group compatible first
    compatible.forEach(fy => {
        const g = fy.group || 'Другое';
        if (!groups[g]) groups[g] = [];
        groups[g].push({...fy, excluded: false});
    });
    // Then incompatible
    if (incompatible.length > 0) {
        groups['⛔ Недоступно для вашего происхождения'] = incompatible.map(fy => ({...fy, excluded: true}));
    }
    
    for (const [groupName, items] of Object.entries(groups)) {
        const groupHeader = document.createElement('div');
        groupHeader.className = 'option-group-header' + (groupName.includes('⛔') ? ' excluded-group' : '');
        groupHeader.textContent = groupName;
        list.appendChild(groupHeader);
        items.forEach(fy => {
            const item = document.createElement('div');
            const isExcluded = fy.excluded;
            item.className = 'option-card' + (customChar.formative === fy.id ? ' selected' : '') + (isExcluded ? ' excluded' : '');
            let modsHtml = renderModBadges(fy.attr_mods, fy.skill_mods);
            item.innerHTML = `
                <div class="option-name">${fy.name}${isExcluded ? ' 🚫' : ''}</div>
                <div class="option-desc">${fy.description || ''}</div>
                ${modsHtml}
            `;
            if (!isExcluded) {
                item.onclick = () => {
                    customChar.formative = fy.id;
                    list.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
                    item.classList.add('selected');
                    document.getElementById('btn-fy-next').disabled = false;
                };
            }
            list.appendChild(item);
        });
    }
}

function renderSpecializations() {
    const list = document.getElementById('spec-list');
    list.innerHTML = '';
    const specs = creationData.specializations || [];
    const groups = {};
    specs.forEach(sp => {
        const g = sp.group || 'Другое';
        if (!groups[g]) groups[g] = [];
        groups[g].push(sp);
    });
    for (const [groupName, items] of Object.entries(groups)) {
        const groupHeader = document.createElement('div');
        groupHeader.className = 'option-group-header';
        groupHeader.textContent = groupName;
        list.appendChild(groupHeader);
        items.forEach(sp => {
            const item = document.createElement('div');
            item.className = 'option-card' + (customChar.specialization === sp.id ? ' selected' : '');
            let modsHtml = renderModBadges({}, sp.skill_mods);
            const equip = (sp.equipment || []).join(', ');
            item.innerHTML = `
                <div class="option-name">${sp.name}</div>
                <div class="option-desc">${sp.description || ''}</div>
                ${modsHtml}
                ${equip ? `<div class="option-equip">🔧 ${equip}</div>` : ''}
            `;
            item.onclick = () => {
                customChar.specialization = sp.id;
                list.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
                item.classList.add('selected');
                document.getElementById('btn-spec-next').disabled = false;
            };
            list.appendChild(item);
        });
    }
}

function renderModBadges(attrMods, skillMods) {
    let badges = '';
    for (const [k, v] of Object.entries(attrMods || {})) {
        const cls = v > 0 ? 'positive' : (v < 0 ? 'negative' : 'neutral');
        badges += `<span class="mod-badge ${cls}">${attrLabel(k)} ${v > 0 ? '+' : ''}${v}</span>`;
    }
    for (const [k, v] of Object.entries(skillMods || {})) {
        const cls = v > 0 ? 'positive' : 'negative';
        badges += `<span class="mod-badge ${cls}">${skillLabel(k)} ${v > 0 ? '+' : ''}${v}</span>`;
    }
    return badges ? `<div class="option-mods">${badges}</div>` : '';
}

function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.slice(0, len) + '...' : str;
}

// Point allocation
function renderPointAllocation() {
    const budget = creationData.point_budget;
    if (Object.keys(customChar.attributes).length === 0) {
        creationData.attributes.forEach(a => { customChar.attributes[a.id] = budget.attr_base; });
    }
    if (Object.keys(customChar.skills).length === 0) {
        creationData.skills.forEach(s => { customChar.skills[s] = 0; });
    }
    renderAttrSliders();
    renderSkillSliders();
    renderCharSummary();
}

function renderAttrSliders() {
    const budget = creationData.point_budget;
    const container = document.getElementById('attr-sliders');
    container.innerHTML = '';
    const total = Object.values(customChar.attributes).reduce((a, b) => a + b, 0);
    document.getElementById('attr-points-left').textContent = `(осталось: ${budget.attributes - total})`;

    creationData.attributes.forEach(a => {
        const val = customChar.attributes[a.id] || budget.attr_base;
        const div = document.createElement('div');
        div.className = 'slider-row';
        div.innerHTML = `
            <span class="slider-label">${a.abbr}</span>
            <button class="btn-inc" onclick="changeAttr('${a.id}',-1)">−</button>
            <span class="slider-val" id="av-${a.id}">${val}</span>
            <button class="btn-inc" onclick="changeAttr('${a.id}',1)">+</button>
            <span class="slider-desc">${a.name}</span>
        `;
        container.appendChild(div);
    });
}

function changeAttr(id, delta) {
    const budget = creationData.point_budget;
    const cur = customChar.attributes[id] || budget.attr_base;
    const newVal = cur + delta;
    if (newVal < budget.attr_min || newVal > budget.attr_max) return;
    const total = Object.values(customChar.attributes).reduce((a, b) => a + b, 0);
    if (delta > 0 && total >= budget.attributes) return;
    customChar.attributes[id] = newVal;
    document.getElementById('av-' + id).textContent = newVal;
    document.getElementById('attr-points-left').textContent = `(осталось: ${budget.attributes - Object.values(customChar.attributes).reduce((a, b) => a + b, 0)})`;
    renderCharSummary();
}

function renderSkillSliders() {
    const budget = creationData.point_budget;
    const container = document.getElementById('skill-sliders');
    container.innerHTML = '';
    const total = Object.values(customChar.skills).reduce((a, b) => a + b, 0);
    document.getElementById('skill-points-left').textContent = `(осталось: ${budget.skills - total})`;

    creationData.skills.forEach(s => {
        const val = customChar.skills[s] || 0;
        const name = creationData.skill_names[s] || s;
        const div = document.createElement('div');
        div.className = 'slider-row';
        div.innerHTML = `
            <span class="slider-label-wide">${name}</span>
            <button class="btn-inc" onclick="changeSkill('${s}',-1)">−</button>
            <span class="slider-val" id="sv-${s}">${val}</span>
            <button class="btn-inc" onclick="changeSkill('${s}',1)">+</button>
        `;
        container.appendChild(div);
    });
}

function changeSkill(id, delta) {
    const budget = creationData.point_budget;
    const cur = customChar.skills[id] || 0;
    const newVal = cur + delta;
    if (newVal < budget.skill_min || newVal > budget.skill_max) return;
    const total = Object.values(customChar.skills).reduce((a, b) => a + b, 0);
    if (delta > 0 && total >= budget.skills) return;
    customChar.skills[id] = newVal;
    document.getElementById('sv-' + id).textContent = newVal;
    document.getElementById('skill-points-left').textContent = `(осталось: ${budget.skills - Object.values(customChar.skills).reduce((a, b) => a + b, 0)})`;
}

function renderCharSummary() {
    const el = document.getElementById('char-summary');
    const name = document.getElementById('inp-char-name')?.value || '?';
    const age = document.getElementById('inp-age')?.value || 30;
    const originData = creationData.origins.find(o => o.id === customChar.origin);
    const fyData = creationData.formative_years.find(f => f.id === customChar.formative);
    const specData = creationData.specializations.find(s => s.id === customChar.specialization);

    el.innerHTML = `
        <div class="panel-section-title">СВОДКА</div>
        <div class="summary-line"><b>Имя:</b> ${name} | <b>Возраст:</b> ${age}</div>
        <div class="summary-line"><b>Происхождение:</b> ${originData?.name || '—'}</div>
        <div class="summary-line"><b>Становление:</b> ${fyData?.name || '—'}</div>
        <div class="summary-line"><b>Специализация:</b> ${specData?.name || '—'}</div>
    `;
}

function updateAge(val) {
    document.getElementById('age-val').textContent = val;
    const v = parseInt(val);
    let cat = 'Взрослый (26-45)';
    if (v <= 25) cat = 'Молодой (16-25)';
    else if (v <= 45) cat = 'Взрослый (26-45)';
    else if (v <= 65) cat = 'Зрелый (46-65)';
    else cat = 'Пожилой (66-80)';
    document.getElementById('age-category').textContent = cat;
}

async function startGameCustom() {
    const name = document.getElementById('inp-char-name').value.trim();
    if (!name) return alert('Введите имя!');
    if (!customChar.origin) return alert('Выберите происхождение!');
    if (!customChar.specialization) return alert('Выберите специализацию!');

    showLoading(true);
    try {
        const payload = {
            preset_id: 'custom', name,
            age: parseInt(document.getElementById('inp-age').value) || 30,
            origin: customChar.origin,
            formative_years: customChar.formative || '',
            specialization: customChar.specialization,
            backstory: document.getElementById('inp-backstory')?.value || '',
            attributes: customChar.attributes,
            skills: Object.fromEntries(Object.entries(customChar.skills).filter(([_, v]) => v > 0)),
        };
        await fetch('/api/character/create', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const resp = await fetch('/api/game/start', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name })
        });
        const data = await resp.json();
        gameState = data.game_state;
        updateGameUI(gameState);
        clearNarrative();
        if (data.narrative) addNarrativeMessage(data.narrative, 'gm');
        showScreen('game');
    } catch (e) { alert('Ошибка: ' + e.message); }
    showLoading(false);
}

// ============================================================
// SAVES — FIXED: chat history restoration
// ============================================================

async function showSaves() {
    showScreen('saves');
    const list = document.getElementById('saves-list');
    try {
        const resp = await fetch('/api/saves');
        const saves = await resp.json();
        if (saves.length === 0) { list.innerHTML = '<div class="empty-state">Нет сохранений</div>'; return; }
        list.innerHTML = '';
        saves.forEach(s => {
            const item = document.createElement('div');
            item.className = 'save-item';
            const loc = s.location || {};
            const gt = s.game_time || {};
            item.innerHTML = `
                <div class="save-info">
                    <div class="save-name">${s.character_name || '?'} — ${s.character_class || '?'}</div>
                    <div class="save-meta">
                        Ур.${s.level || 1} • ${loc.city || '?'}, ${loc.planet || '?'}
                        • ${gt.year || '?'}.${String(gt.month||0).padStart(2,'0')}.${String(gt.day||0).padStart(2,'0')}
                        • ${formatDate(s.save_time)}
                    </div>
                </div>
                <div class="save-actions">
                    <button class="btn btn-sm btn-primary" onclick="loadGame('${s.slot_name}')">ЗАГРУЗИТЬ</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSave('${s.slot_name}')">✕</button>
                </div>
            `;
            list.appendChild(item);
        });
    } catch { list.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function loadGame(slotName) {
    showLoading(true);
    try {
        const resp = await fetch('/api/load', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ slot_name: slotName })
        });
        const data = await resp.json();
        if (data.error) { alert(data.error); }
        else {
            gameState = data.game_state;
            updateGameUI(gameState);
            clearNarrative();

            // FIXED: Restore chat history, filtering out system prompts
            const history = data.conversation_history || [];
            if (history.length > 0) {
                let shownCount = 0;
                for (const msg of history) {
                    // Skip system/intro prompts (they start with "Начни игру!" or contain system instructions)
                    if (msg.role === 'user' && isSystemPrompt(msg.content)) continue;
                    if (msg.role === 'user') {
                        addNarrativeMessage(msg.content, 'player');
                        shownCount++;
                    } else if (msg.role === 'assistant') {
                        addNarrativeMessage(msg.content, 'gm');
                        shownCount++;
                    }
                }
                if (shownCount > 0) {
                    addSystemMessage('— История загружена. Продолжайте игру! —');
                } else {
                    addSystemMessage(`Игра загружена. Добро пожаловать, ${data.character_name || 'Путник'}!`);
                }
            } else {
                addSystemMessage(`Игра загружена. Добро пожаловать, ${data.character_name || 'Путник'}!`);
            }
            showScreen('game');
        }
    } catch (e) { alert('Ошибка: ' + e.message); }
    showLoading(false);
}

function isSystemPrompt(text) {
    if (!text) return false;
    return text.startsWith('Начни игру!') ||
           text.includes('ПЕРВАЯ сцена') ||
           text.includes('Дай 6 вариантов') ||
           text.length > 200;
}

async function quickSave() {
    try {
        const resp = await fetch('/api/save', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const data = await resp.json();
        if (data.success) addSystemMessage('💾 Игра сохранена!');
    } catch (e) { addSystemMessage('⚠ Ошибка: ' + e.message); }
}

async function deleteSave(slotName) {
    if (!confirm('Удалить сохранение?')) return;
    await fetch('/api/save/delete', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ slot_name: slotName })
    });
    showSaves();
}

// ============================================================
// GAMEPLAY — FIXED: error handling, AI errors shown nicely
// ============================================================

async function sendAction() {
    if (isSending) return;
    const input = document.getElementById('player-input');
    const action = input.value.trim();
    if (!action) return;

    isSending = true;
    input.value = '';
    document.getElementById('btn-send').disabled = true;
    addNarrativeMessage(action, 'player');
    const typingId = showTypingIndicator();

    try {
        const resp = await fetch('/api/action/stream', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ action })
        });

        if (resp.ok && resp.headers.get('content-type')?.includes('text/event-stream')) {
            removeTypingIndicator(typingId);
            const msgEl = createNarrativeElement('', 'gm');
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '', buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            if (data.type === 'token') {
                                fullText += data.data;
                                // During streaming, show raw text without choice buttons
                                msgEl.innerHTML = formatNarrativeRaw(fullText);
                                scrollNarrative();
                            } else if (data.type === 'dice') {
                                addDiceResult(data.data);
                            } else if (data.type === 'world_event') {
                                showWorldEvent(data.data);
                            } else if (data.type === 'mechanical') {
                                handleMechanicalResult(data.data);
                            } else if (data.type === 'subsystem') {
                                handleSubsystemResult(data.data);
                            } else if (data.type === 'done') {
                                // V7: done now contains rich data
                                const doneData = data.data;
                                if (doneData.game_state) {
                                    gameState = doneData.game_state;
                                    updateGameUI(gameState);
                                } else {
                                    // Legacy: done data IS the game state
                                    gameState = doneData;
                                    updateGameUI(gameState);
                                }
                                handlePostActionEvents(doneData);
                            }
                        } catch {}
                    }
                }
            }
            // After stream complete — render with choice buttons
            if (fullText.match(/^\[ОШИБКА/)) {
                msgEl.className = 'msg msg-error';
            } else {
                msgEl.innerHTML = formatNarrative(fullText);
                scrollNarrative();
            }
        } else {
            const data = await resp.json();
            removeTypingIndicator(typingId);
            if (data.dice_results) addDiceResult(data.dice_results);
            // Combat or subsystem JSON response (not streamed)
            const text = data.narrative || data.error || 'Неизвестная ошибка';
            if (text.match(/^\[ОШИБКА/)) {
                addErrorMessage(text);
            } else {
                addNarrativeMessage(text, 'gm');
            }
            if (data.game_state) { gameState = data.game_state; updateGameUI(gameState); }
            handlePostActionEvents(data);
        }
    } catch {
        removeTypingIndicator(typingId);
        try {
            const resp2 = await fetch('/api/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action })
            });
            const data = await resp2.json();
            if (data.dice_results) addDiceResult(data.dice_results);
            const text = data.narrative || data.error || 'Ошибка';
            if (text.match(/^\[ОШИБКА/)) {
                addErrorMessage(text);
            } else {
                addNarrativeMessage(text, 'gm');
            }
            if (data.game_state) { gameState = data.game_state; updateGameUI(gameState); }
        } catch (e2) {
            addErrorMessage('⚠ Не удалось подключиться к ИИ: ' + e2.message);
        }
    }

    isSending = false;
    document.getElementById('btn-send').disabled = false;
    input.focus();
}

function quickAction(action) {
    document.getElementById('player-input').value = action;
    sendAction();
}

// ═══════════════════════════════════════════════════
// V7: POST-ACTION EVENT HANDLERS
// ═══════════════════════════════════════════════════

function handlePostActionEvents(data) {
    if (!data) return;

    // Victory rewards
    if (data.victory_rewards) {
        const r = data.victory_rewards;
        showToast(`🏆 Победа! +${r.xp || 0} XP, +₡${(r.credits || 0).toLocaleString('ru-RU')}${r.flawless ? ' ⭐ БЕЗУПРЕЧНО!' : ''}`, 'success', 5000);
        if (r.level_up) {
            setTimeout(() => showLevelUpNotification(r.level_up), 1500);
        }
    }

    // Level up (from XP gain outside combat)
    if (data.level_up && !data.victory_rewards) {
        showLevelUpNotification(data.level_up);
    }

    // Defeat (fail-forward)
    if (data.defeat) {
        const d = data.defeat;
        showDefeatNotification(d);
    }

    // Reputation changes
    if (data.rep_changes) {
        showToast(`📊 Репутация: ${data.rep_changes}`, 'info', 3000);
    }

    // New quest
    if (data.new_quest) {
        showToast(`📋 Новый квест: ${data.new_quest.title || '???'}`, 'info', 4000);
    }

    // Chain offer
    if (data.chain_offer) {
        showToast(`🔗 Доступна сюжетная линия: «${data.chain_offer.name || '???'}»`, 'info', 5000);
    }

    // Property income
    if (data.property_income) {
        const pi = data.property_income;
        if (pi.total_income > 0) {
            showToast(`🏠 Доход с недвижимости: +₡${pi.total_income.toLocaleString('ru-RU')}`, 'success', 3000);
        }
    }

    // Combat state info
    if (data.combat_state) {
        const cs = data.combat_state;
        if (cs.status === 'active') {
            updateCombatUI(cs);
        }
    }
}

function showLevelUpNotification(levelUp) {
    const overlay = document.createElement('div');
    overlay.className = 'level-up-overlay';
    overlay.innerHTML = `
        <div class="level-up-popup">
            <div class="level-up-icon">⬆️</div>
            <div class="level-up-title">УРОВЕНЬ ${levelUp.new_level}!</div>
            <div class="level-up-details">
                +${levelUp.skill_points || 3} очков навыков
                ${levelUp.hp_gain ? `<br>+${levelUp.hp_gain} HP` : ''}
                ${levelUp.perk_available ? '<br>🌟 Доступен новый перк!' : ''}
            </div>
            <button class="btn btn-primary" onclick="this.closest('.level-up-overlay').remove()">ОТЛИЧНО!</button>
        </div>
    `;
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('visible'), 50);
}

function showDefeatNotification(defeat) {
    const overlay = document.createElement('div');
    overlay.className = 'defeat-overlay';
    const changes = (defeat.changes || []).map(c => `<div class="defeat-change">• ${c}</div>`).join('');
    overlay.innerHTML = `
        <div class="defeat-popup">
            <div class="defeat-icon">⚠️</div>
            <div class="defeat-title">${(defeat.name || 'КРИТИЧЕСКОЕ СОСТОЯНИЕ').toUpperCase()}</div>
            <div class="defeat-desc">${defeat.description || 'Вы потеряли сознание...'}</div>
            <div class="defeat-changes">${changes}</div>
            <button class="btn btn-primary" onclick="this.closest('.defeat-overlay').remove()">ПРОДОЛЖИТЬ</button>
        </div>
    `;
    document.body.appendChild(overlay);
    setTimeout(() => overlay.classList.add('visible'), 50);
}

function updateCombatUI(combatState) {
    // Show combat info in narrative
    if (combatState.enemies && combatState.enemies.length > 0) {
        const enemies = combatState.enemies.map(e =>
            `${e.name}: ${e.hp}/${e.max_hp} HP`
        ).join(' | ');
        showToast(`⚔️ Бой: ${enemies}`, 'warning', 4000);
    }
}

function handleMechanicalResult(result) {
    if (!result) return;
    const t = result.type;
    if (t === 'buy' && result.success) {
        showToast(`🛒 ${result.message || `Куплено: ${result.bought}`}`, 'success', 3000);
    } else if (t === 'sell' && result.success) {
        showToast(`💰 ${result.message || `Продано за ₡${result.earned}`}`, 'success', 3000);
    } else if ((t === 'travel' || t === 'travel_planet') && result.success) {
        showToast(`📍 Перемещение: ${result.to || result.to_planet || '?'}`, 'info', 3000);
        if (result.encounter) {
            setTimeout(() => showToast(`⚠️ ${result.encounter.text || 'Встреча!'}`, 'warning', 4000), 1000);
        }
    } else if (result.error) {
        showToast(`❌ ${result.error}`, 'error', 4000);
    }
}

function handleSubsystemResult(result) {
    if (!result) return;
    const sys = result.system;
    if (sys === 'combat' && result.combat_started) {
        showToast('⚔️ Начинается бой!', 'warning', 3000);
    } else if (sys === 'hacking') {
        showToast(`🔓 Хакинг: ${result.narrative || 'Подключение...'}`, 'info', 4000);
    } else if (sys === 'crafting') {
        if (result.success) {
            showToast(`🔧 Создано: ${result.item_name || '???'}`, 'success', 3000);
        } else {
            showToast(`🔧 Крафт не удался: ${result.error || 'недостаточно материалов'}`, 'error', 3000);
        }
    } else if (sys === 'investigation') {
        showToast(`🔍 Расследование: ${result.narrative || 'Новые улики...'}`, 'info', 4000);
    }
}

// ============================================================
// UI UPDATES
// ============================================================

function updateGameUI(state) {
    if (!state) return;
    const c = state.character || {};
    const loc = state.location || {};

    setText('game-char-name', c.name || '—');
    setText('game-char-class', `${c.class || c.origin_name || '?'} Ур.${c.level || 1}`);
    setText('game-location', `${loc.city || '?'}, ${loc.planet || '?'} • ${loc.district || ''}`);
    setText('game-time', state.time || '—');

    const hpPct = c.hp_max ? (c.hp / c.hp_max * 100) : 100;
    const sanPct = c.sanity_max ? (c.sanity / c.sanity_max * 100) : 100;
    const xpPct = c.xp_next ? (c.xp / c.xp_next * 100) : 0;

    const hpBar = document.getElementById('hp-bar');
    const sanBar = document.getElementById('san-bar');
    const xpBar = document.getElementById('xp-bar');
    if (hpBar) hpBar.style.width = hpPct + '%';
    if (sanBar) sanBar.style.width = sanPct + '%';
    if (xpBar) xpBar.style.width = xpPct + '%';

    setText('hp-text', `${c.hp || 0}/${c.hp_max || 0}`);
    setText('san-text', `${c.sanity || 0}/${c.sanity_max || 0}`);
    setText('xp-text', `${c.xp || 0}/${c.xp_next || 1000}`);
    setText('credits-text', formatNum(c.credits || 0));
}

function addNarrativeMessage(text, type) {
    const scroll = document.getElementById('narrative-scroll');
    const div = document.createElement('div');
    div.className = `msg msg-${type}`;
    if (type === 'gm') {
        div.innerHTML = formatNarrative(text);
    } else {
        div.textContent = type === 'player' ? `> ${text}` : text;
    }
    scroll.appendChild(div);
    scrollNarrative();
    return div;
}

function createNarrativeElement(text, type) {
    const scroll = document.getElementById('narrative-scroll');
    const div = document.createElement('div');
    div.className = `msg msg-${type}`;
    div.innerHTML = formatNarrative(text);
    scroll.appendChild(div);
    scrollNarrative();
    return div;
}

function addSystemMessage(text) {
    const scroll = document.getElementById('narrative-scroll');
    const div = document.createElement('div');
    div.className = 'msg msg-system';
    div.textContent = text;
    scroll.appendChild(div);
    scrollNarrative();
}

function addErrorMessage(text) {
    const scroll = document.getElementById('narrative-scroll');
    const div = document.createElement('div');
    div.className = 'msg msg-error';
    div.textContent = text;
    scroll.appendChild(div);
    scrollNarrative();
}

function addDiceResult(dice) {
    const scroll = document.getElementById('narrative-scroll');
    const div = document.createElement('div');
    div.className = 'msg msg-dice';
    const cls = dice.success ? 'dice-result-success' : 'dice-result-failure';
    const labels = {
        'critical_success': '💥 КРИТИЧЕСКИЙ УСПЕХ!', 'great_success': '✨ Отличный успех!',
        'success': '✓ Успех', 'failure': '✗ Провал',
        'bad_failure': '💀 Серьёзный провал', 'critical_failure': '☠ КРИТИЧЕСКИЙ ПРОВАЛ!',
    };
    const skillName = skillLabel(dice.skill || '?');
    const attrName = attrLabel(dice.attribute || '?');
    // Build modifiers line
    let mods = [];
    if (dice.psych_modifier) mods.push(`🧠 психика ${dice.psych_modifier > 0 ? '+' : ''}${dice.psych_modifier}`);
    if (dice.companion_bonus) mods.push(`👥 компаньон +${dice.companion_bonus}`);
    if (dice.implant_bonus) mods.push(`🔩 импланты +${dice.implant_bonus}`);
    if (dice.security_mod) mods.push(`🛡️ безопасность ${dice.security_mod > 0 ? '+' : ''}${dice.security_mod} DC`);
    const modsHtml = mods.length ? `<div class="dice-mods">${mods.join(' │ ')}</div>` : '';
    div.innerHTML = `
        <div class="dice-header">🎲 ${skillName} + ${attrName}</div>
        <div class="dice-formula">[${dice.rolls?.join(', ')}] = ${dice.roll_total || 0} + ${dice.bonus || 0} = <b>${dice.result || 0}</b> vs DC ${dice.difficulty || 10}</div>
        ${modsHtml}
        <div class="${cls}"><b>${labels[dice.quality] || dice.quality}</b> (${dice.margin >= 0 ? '+' : ''}${dice.margin || 0})</div>
    `;
    scroll.appendChild(div);
    scrollNarrative();
}

function formatNarrative(text) {
    if (!text) return '';

    // Split narrative from choices block
    let narrativePart = text;
    let choicesHtml = '';

    // Find the choices block (various formats the AI might use)
    const choicePatterns = [
        /\*?\*?Что будешь делать\??\*?\*?\s*\n/i,
        /\*?\*?Что (?:ты )?(?:будешь|хочешь) делать\??\*?\*?\s*\n/i,
        /\*?\*?Выбери действие:?\*?\*?\s*\n/i,
        /\*?\*?Доступные действия:?\*?\*?\s*\n/i,
    ];

    let choiceStart = -1;
    for (const pat of choicePatterns) {
        const m = text.search(pat);
        if (m !== -1) { choiceStart = m; break; }
    }

    if (choiceStart !== -1) {
        narrativePart = text.substring(0, choiceStart).trim();
        const choicesText = text.substring(choiceStart);

        // Parse numbered choices (1. ... 2. ... etc)
        const choiceLines = [];
        const lineRegex = /^\s*(\d+)\.\s*(.+)$/gm;
        let match;
        while ((match = lineRegex.exec(choicesText)) !== null) {
            choiceLines.push({ num: match[1], text: match[2].trim() });
        }

        if (choiceLines.length > 0) {
            choicesHtml = '<div class="choices-block"><div class="choices-title">Что будешь делать?</div><div class="choices-grid">';
            for (const ch of choiceLines) {
                const isCustom = ch.num === '7' || ch.text.toLowerCase().includes('свой вариант');
                if (isCustom) {
                    choicesHtml += `<div class="choice-btn choice-custom" onclick="choiceCustom()">
                        <span class="choice-num">✎</span>
                        <span class="choice-text">Свой вариант</span>
                    </div>`;
                } else {
                    const escaped = ch.text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                    choicesHtml += `<div class="choice-btn" onclick="choiceSelect('${escaped}')">
                        <span class="choice-num">${ch.num}</span>
                        <span class="choice-text">${ch.text}</span>
                    </div>`;
                }
            }
            choicesHtml += '</div></div>';
        }
    }

    // Format the narrative part — clean markdown
    let html = narrativePart
        // Remove orphan markdown headers (just ## or ### with no text)
        .replace(/^#{1,4}\s*$/gm, '')
        // Remove [STATE] blocks and other AI artifacts
        .replace(/\[STATE\][\s\S]*?\[\/STATE\]/g, '')
        .replace(/\[SYSTEM\][\s\S]*?\[\/SYSTEM\]/g, '')
        // Markdown formatting
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h3>$1</h3>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        // Clean up empty paragraphs
        .replace(/<p>\s*<\/p>/g, '')
        .replace(/<br>\s*<br>\s*<br>/g, '<br><br>');

    html = '<p>' + html + '</p>';

    return html + choicesHtml;
}

function choiceSelect(text) {
    const input = document.getElementById('player-input');
    input.value = text;
    sendAction();
}

function choiceCustom() {
    const input = document.getElementById('player-input');
    input.focus();
    input.placeholder = 'Опиши своё действие...';
}

function formatNarrativeRaw(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/\n/g, '<br>');
}

function clearNarrative() { document.getElementById('narrative-scroll').innerHTML = ''; }
function scrollNarrative() {
    const s = document.getElementById('narrative-scroll');
    s.scrollTop = s.scrollHeight;
}

function showTypingIndicator() {
    const scroll = document.getElementById('narrative-scroll');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'typing-indicator';
    div.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
    scroll.appendChild(div);
    scrollNarrative();
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ---- Side Panels — FIXED: Russian skill names ----
function togglePanel(panel) {
    const sp = document.getElementById('side-panel');
    if (!sp.classList.contains('hidden') && sp.dataset.current === panel) { closeSidePanel(); return; }
    sp.classList.remove('hidden');
    sp.dataset.current = panel;
    const title = document.getElementById('side-panel-title');
    const content = document.getElementById('side-panel-content');
    const panels = {
        character:     ['ПЕРСОНАЖ',       renderCharacterPanel],
        inventory:     ['ИНВЕНТАРЬ',      renderInventoryPanel],
        implants:      ['ИМПЛАНТЫ',       renderImplantPanel],
        quests:        ['КВЕСТЫ',         renderQuestsPanel],
        shop:          ['МАГАЗИН',        renderShopPanel],
        world:         ['НОВОСТИ МИРА',   renderWorldPanel],
        map:           ['КАРТА',          renderMapPanel],
        npcs:          ['NPC',            renderNPCPanel],
        crafting:      ['КРАФТИНГ',       renderCraftingPanel],
        companions:    ['КОМПАНЬОНЫ',     renderCompanionsPanel],
        ship:          ['КОРАБЛЬ',        renderShipPanel],
        property:      ['НЕДВИЖИМОСТЬ',   renderPropertyPanel],
        hacking:       ['ХАКИНГ',         renderHackingPanel],
        investigation: ['РАССЛЕДОВАНИЯ',  renderInvestigationPanel],
        factions:      ['ФРАКЦИИ',        renderFactionsPanel],
    };
    const p = panels[panel];
    if (p) { title.textContent = p[0]; p[1](content); }
}

function closeSidePanel() { document.getElementById('side-panel').classList.add('hidden'); }

function renderCharacterPanel(container) {
    if (!gameState) return;
    const c = gameState.character || {};
    let html = '';

    // Character info block
    html += '<div class="char-info-block">';
    if (c.origin_name) html += `<div class="char-info-row"><span class="char-info-label">Происхождение</span><span class="char-info-val">${c.origin_name}</span></div>`;
    if (c.specialization_name || c.class) html += `<div class="char-info-row"><span class="char-info-label">Специализация</span><span class="char-info-val">${c.specialization_name || c.class}</span></div>`;
    if (c.age) html += `<div class="char-info-row"><span class="char-info-label">Возраст</span><span class="char-info-val">${c.age}</span></div>`;
    html += `<div class="char-info-row"><span class="char-info-label">Уровень</span><span class="char-info-val">${c.level || 1}</span></div>`;
    html += '</div>';

    // Attributes
    html += '<div class="panel-section-title">АТРИБУТЫ</div><div class="attr-grid">';
    for (const [k, v] of Object.entries(c.attributes || {})) {
        html += `<div class="attr-item"><span class="attr-name">${attrLabel(k)}</span><span class="attr-val">${v}</span></div>`;
    }
    html += '</div>';

    // Skills — FIXED: Russian names
    html += '<div class="panel-section-title">НАВЫКИ</div><div class="skill-list">';
    for (const [k, v] of Object.entries(c.skills || {})) {
        if (v > 0) html += `<div class="skill-item"><span class="skill-name">${skillLabel(k)}</span><span class="skill-val">${v}</span></div>`;
    }
    html += '</div>';

    // Extras: psychology, skill points, perks
    html += renderCharacterPanelExtras();

    container.innerHTML = html;
}

async function renderInventoryPanel(container) {
    try {
        const items = await (await fetch('/api/inventory')).json();
        if (items.length === 0) { container.innerHTML = '<div class="empty-state">Пусто</div>'; return; }
        let html = '<div class="skill-list">';
        items.forEach((i, idx) => {
            html += `<div class="shop-item">
                <div class="shop-item-info">
                    <div class="shop-item-name rarity-${i.rarity || 'common'}">${i.name || '?'}</div>
                    <div class="shop-item-stats">${i.stats || ''} ${i.qty > 1 ? `×${i.qty}` : ''}</div>
                </div>
                <button class="btn-sell" onclick="sellItem(${idx})">Продать</button>
            </div>`;
        });
        container.innerHTML = html + '</div>';
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function sellItem(index) {
    try {
        const resp = await fetch('/api/shop/sell', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ index })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`💰 ${data.message}`, 'system');
            // Refresh panels
            const content = document.getElementById('side-panel-content');
            renderInventoryPanel(content);
            if (gameState) { gameState.character.credits = data.credits; updateCreditsUI(data.credits); }
        } else {
            addNarrativeMessage(`⚠ ${data.error}`, 'system');
        }
    } catch { addNarrativeMessage('⚠ Ошибка продажи', 'system'); }
}

// ═══════════════════════════════════════════
// IMPLANT PANEL
// ═══════════════════════════════════════════
async function renderImplantPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/implant/list')).json();
        const installed = data.installed || [];
        const available = data.available || [];
        const nearClinic = data.near_clinic;
        const fee = data.surgery_fee || 5000;
        const humanity = data.humanity || 100;
        const slots = data.max_implant_slots || 6;
        const usedSlots = data.used_slots || 0;

        let html = `<div class="implant-header">
            <div class="implant-humanity">🧠 Человечность: <b>${humanity}/100</b></div>
            <div class="implant-slots">🔩 Слоты: <b>${usedSlots}/${slots}</b></div>
            <div class="implant-clinic">${nearClinic
                ? '🏥 <span style="color:var(--green)">Клиника рядом</span> (₡' + fee.toLocaleString() + ')'
                : '⚠️ <span style="color:var(--gold)">Нет клиники</span> — самоустановка (DC+4)'}</div>
        </div>`;

        // Humanity bar
        const humColor = humanity > 60 ? 'var(--green)' : humanity > 30 ? 'var(--gold)' : 'var(--red)';
        html += `<div class="implant-bar"><div class="implant-bar-fill" style="width:${humanity}%;background:${humColor}"></div></div>`;

        // Installed
        html += '<div class="implant-section-title">✅ УСТАНОВЛЕНЫ</div>';
        if (installed.length === 0) {
            html += '<div class="empty-state" style="padding:8px">Нет установленных имплантов</div>';
        } else {
            installed.forEach(imp => {
                const bonuses = [];
                for (const [s, v] of Object.entries(imp.skill_bonuses || {})) {
                    bonuses.push(`${skillLabel(s)} +${v}`);
                }
                for (const [a, v] of Object.entries(imp.attr_bonuses || {})) {
                    bonuses.push(`${attrLabel(a)} ${v > 0 ? '+' : ''}${v}`);
                }
                html += `<div class="implant-card installed">
                    <div class="implant-info">
                        <div class="implant-name rarity-${imp.rarity || 'common'}">${imp.name}</div>
                        <div class="implant-stats">${imp.stats || ''}</div>
                        ${bonuses.length ? '<div class="implant-bonuses">' + bonuses.join(', ') + '</div>' : ''}
                    </div>
                    <button class="btn-remove-implant" onclick="removeImplant(${imp.inv_index})">✖ Удалить</button>
                </div>`;
            });
        }

        // Available for install
        html += '<div class="implant-section-title">📦 В ИНВЕНТАРЕ (можно установить)</div>';
        if (available.length === 0) {
            html += '<div class="empty-state" style="padding:8px">Нет имплантов в инвентаре. Купите в магазине.</div>';
        } else {
            available.forEach(imp => {
                const dc = imp.surgery_dc + (nearClinic ? 0 : 4);
                const humCost = imp.humanity_cost || 0;
                html += `<div class="implant-card available">
                    <div class="implant-info">
                        <div class="implant-name rarity-${imp.rarity || 'common'}">${imp.name}</div>
                        <div class="implant-stats">${imp.stats || ''}</div>
                        <div class="implant-meta">DC ${dc} │ 🧠 −${humCost} человечность${nearClinic ? ' │ ₡' + fee.toLocaleString() : ''}</div>
                    </div>
                    <button class="btn-install-implant" onclick="installImplant(${imp.inv_index})"
                        ${usedSlots >= slots ? 'disabled title="Нет свободных слотов"' : ''}>
                        🔩 Установить
                    </button>
                </div>`;
            });
        }

        container.innerHTML = html;
    } catch(e) {
        container.innerHTML = `<div class="empty-state">Ошибка: ${e.message}</div>`;
    }
}

async function installImplant(invIndex) {
    try {
        const resp = await fetch('/api/implant/install', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ inv_index: invIndex })
        });
        const data = await resp.json();
        if (data.success) {
            // Show surgery roll
            if (data.surgery_roll) addDiceResult({...data.surgery_roll, skill: 'medicine', attribute: 'intelligence'});
            addNarrativeMessage(`${data.message}\n🧠 Человечность: ${data.humanity} (−${data.humanity_lost})`, 'system');
            if (data.side_effects?.length) {
                addNarrativeMessage('⚠️ Побочные эффекты: ' + data.side_effects.join(', '), 'system');
            }
            if (data.credits !== undefined && gameState) {
                gameState.character.credits = data.credits; updateCreditsUI(data.credits);
            }
        } else {
            if (data.surgery_roll) addDiceResult({...data.surgery_roll, skill: 'medicine', attribute: 'intelligence'});
            addNarrativeMessage(`${data.message}\n${(data.complications || []).join('\n')}`, 'system');
        }
        renderImplantPanel(document.getElementById('side-panel-content'));
    } catch(e) { addNarrativeMessage('⚠ Ошибка установки импланта', 'system'); }
}

async function removeImplant(invIndex) {
    if (!confirm('Удалить имплант? Часть бонусов будет потеряна.')) return;
    try {
        const resp = await fetch('/api/implant/remove', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ inv_index: invIndex })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`${data.message}\n🧠 Человечность: ${data.humanity} (+${data.humanity_restored})`, 'system');
        } else {
            addNarrativeMessage(`⚠ ${data.error || 'Ошибка'}`, 'system');
        }
        renderImplantPanel(document.getElementById('side-panel-content'));
    } catch(e) { addNarrativeMessage('⚠ Ошибка удаления', 'system'); }
}

async function renderShopPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/shop')).json();
        const credits = data.credits || gameState?.character?.credits || 0;
        const items = data.items || [];
        const priceMod = data.price_modifier || 1.0;
        const shopName = data.shop_name || 'Магазин';
        const security = data.security || 'medium';

        // Group by category
        const categories = {};
        const CAT_NAMES = {weapons:'⚔️ ОРУЖИЕ', armor:'🛡 БРОНЯ', implants:'🧬 ИМПЛАНТЫ', gadgets:'🔧 ГАДЖЕТЫ', consumables:'💊 РАСХОДНИКИ'};
        items.forEach(i => {
            if (!categories[i.category]) categories[i.category] = [];
            categories[i.category].push(i);
        });

        let html = `<div class="shop-header-name">${shopName}</div>`;
        html += `<div class="shop-credits">Баланс: ₡${credits.toLocaleString('ru-RU')}</div>`;
        if (security === 'none' || security === 'low') {
            html += `<div class="world-econ down">🏴 Чёрный рынок — нелегальные товары</div>`;
        }

        let html = `<div class="shop-credits">Баланс: ₡${credits.toLocaleString('ru-RU')}</div>`;

        // Price indicator
        if (priceMod > 1.05) html += `<div class="world-econ up">📈 Цены повышены (×${priceMod.toFixed(2)})</div>`;
        else if (priceMod < 0.95) html += `<div class="world-econ down">📉 Цены снижены (×${priceMod.toFixed(2)})</div>`;

        // Filter buttons
        html += '<div class="shop-filter">';
        html += `<span class="shop-filter-btn active" onclick="filterShop(this, 'all')">Все</span>`;
        for (const [cat, name] of Object.entries(CAT_NAMES)) {
            if (categories[cat]) html += `<span class="shop-filter-btn" onclick="filterShop(this, '${cat}')">${name.split(' ')[0]}</span>`;
        }
        html += '</div>';

        for (const [cat, catItems] of Object.entries(categories)) {
            html += `<div class="shop-category" data-cat="${cat}">${CAT_NAMES[cat] || cat}</div>`;
            catItems.forEach(item => {
                const canBuy = credits >= item.price;
                html += `<div class="shop-item" data-cat="${cat}">
                    <div class="shop-item-info">
                        <div class="shop-item-name rarity-${item.rarity}">${item.name}</div>
                        <div class="shop-item-stats">${item.stats}</div>
                    </div>
                    <span class="shop-item-price ${canBuy ? '' : 'too-expensive'}">₡${item.price.toLocaleString('ru-RU')}</span>
                    <button class="btn-buy" ${canBuy ? '' : 'disabled'} onclick="buyItem('${item.id}')">Купить</button>
                </div>`;
            });
        }
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка загрузки магазина</div>'; }
}

function filterShop(btn, category) {
    document.querySelectorAll('.shop-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.shop-item, .shop-category').forEach(el => {
        if (category === 'all') el.style.display = '';
        else el.style.display = el.dataset.cat === category ? '' : 'none';
    });
}

async function buyItem(itemId) {
    try {
        const resp = await fetch('/api/shop/buy', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`🛒 ${data.message}`, 'system');
            if (gameState) { gameState.character.credits = data.credits; updateCreditsUI(data.credits); }
            // Refresh shop panel
            const content = document.getElementById('side-panel-content');
            renderShopPanel(content);
        } else {
            addNarrativeMessage(`⚠ ${data.error}`, 'system');
        }
    } catch { addNarrativeMessage('⚠ Ошибка покупки', 'system'); }
}

function updateCreditsUI(credits) {
    setText('credits-text', (credits || 0).toLocaleString('ru-RU'));
}

async function renderWorldPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/world')).json();
        let html = '';

        // Economy
        const pm = data.price_modifier || 1.0;
        if (pm !== 1.0) {
            const cls = pm > 1.05 ? 'up' : pm < 0.95 ? 'down' : '';
            html += `<div class="world-econ ${cls}">📊 Индекс цен: ×${pm.toFixed(2)} | Нестабильность: ${data.instability || 0}%</div>`;
        }

        // News
        const news = data.news_history || [];
        if (news.length) {
            html += '<div class="panel-section-title">📡 ПОСЛЕДНИЕ НОВОСТИ</div>';
            news.reverse().forEach(n => { html += `<div class="world-news-item">${n}</div>`; });
        }

        // Latest context
        const ctx = data.last_context || {};
        if (ctx.rumors?.length) {
            html += '<div class="panel-section-title">🗣 СЛУХИ</div>';
            ctx.rumors.forEach(r => { html += `<div class="world-rumor-item">${r}</div>`; });
        }
        if (ctx.atmosphere) {
            html += '<div class="panel-section-title">🌆 АТМОСФЕРА</div>';
            html += `<div class="world-news-item">${ctx.atmosphere}</div>`;
        }

        if (!html) html = '<div class="empty-state">Пока нет событий</div>';
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

function showWorldEvent(data) {
    const ticker = document.getElementById('news-ticker');
    const tickerText = document.getElementById('ticker-text');
    if (!ticker || !tickerText) return;

    const parts = [];
    if (data.news?.length) parts.push(...data.news);
    if (data.rumors?.length) parts.push(...data.rumors.map(r => `[СЛУХ] ${r}`));
    if (data.economic_event) parts.push(`[ЭКОНОМИКА] ${data.economic_event}`);

    if (parts.length) {
        ticker.classList.remove('hidden');
        tickerText.textContent = parts.join(' ● ');
        // Auto-hide after 15 seconds
        setTimeout(() => ticker.classList.add('hidden'), 15000);
    }
}

async function renderQuestsPanel(container) {
    try {
        const data = await (await fetch('/api/quests')).json();
        const a = data.active || [], c = data.completed || [];
        if (!a.length && !c.length) { container.innerHTML = '<div class="empty-state">Нет квестов</div>'; return; }
        let html = '';
        if (a.length) { html += '<div class="panel-section-title">АКТИВНЫЕ</div>'; a.forEach(q => { html += `<div class="quest-item"><b>${q.title || '?'}</b><br>${q.description || ''}</div>`; }); }
        if (c.length) { html += '<div class="panel-section-title">ЗАВЕРШЁННЫЕ</div>'; c.forEach(q => { html += `<div class="quest-item completed">✓ ${q.title || '?'}</div>`; }); }
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

// ---- MAP PANEL ----
async function renderMapPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/map/location')).json();
        let html = '';

        // Current location
        const loc = data.location || {};
        html += `<div class="panel-section-title">📍 ТЕКУЩЕЕ ПОЛОЖЕНИЕ</div>`;
        html += `<div class="map-location-card">`;
        html += `<div class="map-planet">🌍 ${loc.planet || '?'}</div>`;
        html += `<div class="map-city">🏙 ${loc.city || '?'}</div>`;
        html += `<div class="map-district">📌 ${loc.district || '?'}</div>`;
        if (loc.place) html += `<div class="map-place">🏢 ${loc.place}</div>`;
        html += `</div>`;

        // Description
        if (data.description) {
            html += `<div class="map-description">${data.description.replace(/\n/g, '<br>')}</div>`;
        }

        // Establishments in current district
        const estabs = data.establishments || [];
        if (estabs.length) {
            html += `<div class="panel-section-title">🏢 ЗАВЕДЕНИЯ</div>`;
            estabs.forEach(e => {
                const services = (e.services || []).join(', ');
                html += `<div class="map-establishment" onclick="visitPlace('${e.name.replace(/'/g, "\\'")}')">
                    <div class="map-estab-name">${e.name}</div>
                    <div class="map-estab-services">${services}</div>
                </div>`;
            });
        }

        // Other districts
        const districts = data.districts || [];
        if (districts.length > 1) {
            html += `<div class="panel-section-title">🗺 РАЙОНЫ ${loc.city || ''}</div>`;
            districts.forEach(d => {
                const isCurrent = d.name === loc.district;
                html += `<div class="map-district-item ${isCurrent ? 'current' : ''}" onclick="${isCurrent ? '' : `moveToDistrict('${d.name.replace(/'/g, "\\'")}')`}">
                    <div class="map-dist-name">${isCurrent ? '📌 ' : ''}${d.name}</div>
                    <div class="map-dist-info">${d.type} | Безопасность: ${d.security}</div>
                </div>`;
            });
        }

        // Cities on planet
        const cities = data.cities || [];
        if (cities.length > 1) {
            html += `<div class="panel-section-title">🏙 ГОРОДА</div>`;
            cities.forEach(c => {
                const isCurrent = c === loc.city;
                html += `<div class="map-city-item ${isCurrent ? 'current' : ''}" onclick="${isCurrent ? '' : `moveToCity('${c.replace(/'/g, "\\'")}')`}">
                    ${isCurrent ? '📌 ' : '🚊 '}${c}
                </div>`;
            });
        }

        // Routes to other planets
        const routes = data.routes || {};
        if (Object.keys(routes).length) {
            html += `<div class="panel-section-title">🚀 МАРШРУТЫ</div>`;
            for (const [dest, info] of Object.entries(routes)) {
                const riskEmoji = info.risk === 'minimal' ? '🟢' : info.risk === 'low' ? '🟡' : info.risk === 'medium' ? '🟠' : '🔴';
                html += `<div class="map-route-item" onclick="moveToPlanet('${dest}')">
                    <div class="map-route-dest">🚀 ${dest}</div>
                    <div class="map-route-info">${info.time} | Δv ${info.delta_v} | ${riskEmoji} ${info.risk}</div>
                </div>`;
            }
        }

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка загрузки карты</div>'; }
}

async function moveToDistrict(district) {
    try {
        const resp = await fetch('/api/map/move', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ district })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`📍 Перемещение в район: ${district}`, 'system');
            if (data.travel_event) handleTravelEvent(data.travel_event);
            if (data.new_npc) addNarrativeMessage(`👤 В толпе замечаешь нового человека...`, 'system');
            closeSidePanel();
            sendAction(`Перемещаюсь в район ${district} и осматриваюсь`);
        }
    } catch { addNarrativeMessage('⚠ Ошибка перемещения', 'system'); }
}

async function moveToCity(city) {
    try {
        const resp = await fetch('/api/map/move', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ city })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`🏙 Перемещение в город: ${city}`, 'system');
            closeSidePanel();
            sendAction(`Прибываю в ${city} и осматриваю окрестности`);
        }
    } catch { addNarrativeMessage('⚠ Ошибка перемещения', 'system'); }
}

async function moveToPlanet(planet) {
    if (!confirm(`Перелёт до ${planet} может занять много часов. Продолжить?`)) return;
    try {
        const resp = await fetch('/api/map/move', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ planet })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`🚀 ${data.message}`, 'system');
            closeSidePanel();
            sendAction(`Прибываю на ${planet}. Выхожу из корабля и осматриваюсь`);
        } else {
            addNarrativeMessage(`⚠ ${data.error}`, 'system');
        }
    } catch { addNarrativeMessage('⚠ Ошибка перелёта', 'system'); }
}

function visitPlace(place) {
    closeSidePanel();
    sendAction(`Иду в ${place}`);
}

// ---- NPC PANEL ----
async function renderNPCPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/npcs')).json();
        const npcs = data.npcs || [];
        if (!npcs.length) { container.innerHTML = '<div class="empty-state">Вы ещё никого не встретили</div>'; return; }

        let html = `<div class="panel-section-title">👥 ИЗВЕСТНЫЕ NPC (${data.total})</div>`;
        npcs.forEach(npc => {
            const impClass = npc.importance === 'major' ? 'npc-major' : npc.importance === 'notable' ? 'npc-notable' : '';
            const dispEmoji = npc.disposition === 'дружелюбный' ? '💚' : npc.disposition === 'враждебный' ? '❤️‍🔥' : npc.disposition === 'настороженный' ? '💛' : '⚪';
            html += `<div class="npc-card ${impClass}">
                <div class="npc-name">${dispEmoji} ${npc.name}</div>
                <div class="npc-info">${npc.role} | ${npc.faction}</div>
                <div class="npc-appearance">${(npc.appearance || []).join('; ')}</div>
                <div class="npc-speech">Речь: ${npc.speech_style} | Встреч: ${npc.met_count}</div>
                ${npc.notes?.length ? `<div class="npc-notes">${npc.notes.slice(-2).join('; ')}</div>` : ''}
            </div>`;
        });
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

// ---- CRAFTING PANEL ----
async function renderCraftingPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await (await fetch('/api/crafting/recipes')).json();
        const recipes = data.recipes || [];
        let html = '<div class="panel-section-title">🔧 ЧЕРТЕЖИ</div>';

        recipes.forEach(r => {
            const recipe = r.recipe;
            const canCraft = r.can_craft;
            const missing = r.missing || [];
            const materials = recipe.materials.map(m => `${m.name} ×${m.qty}`).join(', ');

            html += `<div class="craft-recipe ${canCraft ? 'craftable' : 'locked'}">
                <div class="craft-name">${recipe.name}</div>
                <div class="craft-result rarity-${recipe.result.rarity}">${recipe.result.name} — ${recipe.result.stats}</div>
                <div class="craft-materials">Материалы: ${materials}</div>
                <div class="craft-skill">Навык: ${recipe.skill} (DC ${recipe.difficulty}) | Ваш: ${r.skill_value}</div>
                ${missing.length ? `<div class="craft-missing">❌ ${missing.join(', ')}</div>` : ''}
                ${canCraft ? `<button class="btn-craft" onclick="doCraft('${recipe.id}')">⚒ Создать (${recipe.time_minutes} мин)</button>` : ''}
            </div>`;
        });

        // Materials reference
        html += '<div class="panel-section-title">📦 МАТЕРИАЛЫ (покупай в магазине)</div>';
        const mats = data.materials || [];
        html += '<div class="craft-materials-list">';
        mats.forEach(m => {
            html += `<span class="craft-mat rarity-${m.rarity}">${m.name} ₡${m.price}</span>`;
        });
        html += '</div>';

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function doCraft(recipeId) {
    try {
        const resp = await fetch('/api/crafting/craft', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ recipe_id: recipeId })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`⚒ Создано: ${data.item.name} (${data.item.stats})`, 'system');
        } else {
            addNarrativeMessage(`❌ ${data.reason || 'Ошибка крафта'}`, 'system');
        }
        // Refresh crafting panel
        const content = document.getElementById('side-panel-content');
        if (document.getElementById('side-panel').dataset.current === 'crafting') {
            renderCraftingPanel(content);
        }
    } catch { addNarrativeMessage('⚠ Ошибка крафта', 'system'); }
}

// ---- ENHANCED CHARACTER PANEL (with psychology, perks, property) ----
function renderCharacterPanelExtras() {
    if (!gameState) return '';
    const c = gameState.character || {};
    let html = '';

    // Psychology
    const stress = c.stress || 30;
    const humanity = c.humanity || 60;
    html += '<div class="panel-section-title">🧠 ПСИХОЛОГИЯ</div>';
    html += `<div class="psych-bar"><span>Стресс</span><div class="bar-bg"><div class="bar-fill stress" style="width:${stress}%"></div></div><span>${stress}%</span></div>`;
    html += `<div class="psych-bar"><span>Человечность</span><div class="bar-bg"><div class="bar-fill humanity" style="width:${humanity}%"></div></div><span>${humanity}%</span></div>`;

    // Skill points
    const sp = c.unspent_skill_points || 0;
    if (sp > 0) {
        html += `<div class="panel-section-title">⬆ ОЧКИ НАВЫКОВ: ${sp}</div>`;
        html += '<div class="skill-up-grid">';
        for (const [k, v] of Object.entries(c.skills || {})) {
            html += `<div class="skill-up-item" onclick="spendSkillPoint('${k}')"><span>${skillLabel(k)} ${v}</span><span class="skill-up-btn">+</span></div>`;
        }
        html += '</div>';
    }

    // Perks — load async
    const perks = c.perks || [];
    if (perks.length) {
        html += '<div class="panel-section-title">🏆 ПЕРКИ</div>';
        perks.forEach(p => {
            html += `<div class="perk-item"><b>${p.name}</b>: ${p.description}</div>`;
        });
    }

    // Perk selection button (always show if eligible)
    html += '<div id="perks-available-section"></div>';
    // Trigger async perk loading
    setTimeout(() => loadAvailablePerks(), 50);

    return html;
}

async function loadAvailablePerks() {
    const section = document.getElementById('perks-available-section');
    if (!section) return;
    try {
        const data = await apiFetch('/api/perks');
        if (data._error) return;
        const avail = data.available || [];
        if (avail.length === 0) return;

        let html = '<div class="panel-section-title">🌟 ДОСТУПНЫЕ ПЕРКИ</div>';
        avail.forEach(p => {
            html += `<div class="perk-available" onclick="selectPerk('${p.id}')">
                <div class="perk-name-avail">${p.name}</div>
                <div class="perk-desc-avail">${p.description}</div>
                ${p.requirement ? `<div class="perk-req">${p.requirement}</div>` : ''}
            </div>`;
        });
        section.innerHTML = html;
    } catch {}
}

async function selectPerk(perkId) {
    const resp = await apiFetch('/api/perks/select', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ perk_id: perkId })
    });
    if (resp.success) {
        showToast(`🌟 Перк получен: ${resp.perk?.name || perkId}`, 'success');
        addNarrativeMessage(`🌟 Новый перк: ${resp.perk?.name || perkId}`, 'system');
        renderCharacterPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось выбрать перк', 'error'); }
}

async function spendSkillPoint(skill) {
    try {
        const resp = await fetch('/api/levelup/spend', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ skill })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`⬆ ${skillLabel(skill)}: ${data.new_value} (осталось очков: ${data.remaining})`, 'system');
            // Update local state
            if (gameState?.character) {
                gameState.character.skills[skill] = data.new_value;
                gameState.character.unspent_skill_points = data.remaining;
            }
            // Refresh panel
            const content = document.getElementById('side-panel-content');
            renderCharacterPanel(content);
        }
    } catch { addNarrativeMessage('⚠ Ошибка', 'system'); }
}

// ---- TRAVEL EVENT HANDLING ----
function handleTravelEvent(event) {
    if (!event) return;
    const emoji = event.type === 'encounter' ? '⚔' : event.type === 'opportunity' ? '💡' : event.type === 'hazard' ? '⚠' : '🌆';
    addNarrativeMessage(`${emoji} ${event.text}`, 'system');
}

// ═══════════════════════════════════════════════════
// COMPANIONS PANEL
// ═══════════════════════════════════════════════════
async function renderCompanionsPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const team = await apiFetch('/api/companions/team');
        const avail = await apiFetch('/api/companions/available');
        let html = '';

        // Current team
        const companions = team.companions || [];
        html += `<div class="panel-section-title">🤝 ГРУППА (${companions.length}/3)</div>`;
        if (companions.length === 0) {
            html += '<div class="empty-state">Нет компаньонов. Ищите союзников в мире!</div>';
        }
        companions.forEach(c => {
            const loyalty = c.loyalty || 50;
            const loyClass = loyalty >= 70 ? 'high' : loyalty >= 40 ? 'mid' : 'low';
            const skills = Object.entries(c.skills || {}).map(([s,v]) => `${skillLabel(s)} +${v}`).join(', ');
            html += `<div class="companion-card">
                <div class="companion-name">${c.nickname ? c.nickname + ' — ' : ''}${c.name || c.id}</div>
                <div class="companion-type">${c.type || 'Союзник'}</div>
                ${skills ? `<div class="companion-bonus">⚡ ${skills}</div>` : ''}
                <div class="companion-loyalty ${loyClass}">Лояльность: <div class="bar-bg"><div class="bar-fill" style="width:${loyalty}%;background:${loyalty>=70?'#44ff44':loyalty>=40?'#ffaa00':'#ff4444'}"></div></div> ${loyalty}%</div>
                ${c.personal_quest ? `<div class="companion-quest">📜 ${c.personal_quest}</div>` : ''}
                <button class="btn-dismiss" onclick="dismissCompanion('${c.id}')">Отпустить</button>
            </div>`;
        });

        // Combat bonus
        if (team.combat_bonus) {
            const bonusStr = Object.entries(team.combat_bonus).map(([k,v]) => `${k}: +${v}`).join(', ');
            if (bonusStr) html += `<div class="companion-combat-bonus">⚔️ Бонус группы: ${bonusStr}</div>`;
        }

        // Available recruits — location-based
        const recruits = avail.recruits || [];
        const locName = avail.location || '';
        html += `<div class="panel-section-title">📢 ДОСТУПНЫЕ НАЁМНИКИ ${locName ? '<span style="color:var(--text2);font-size:11px">(' + locName + ')</span>' : ''}</div>`;
        if (recruits.length === 0) {
            html += '<div class="empty-state">Здесь никого нет. Попробуйте в другом районе или городе.</div>';
        }
        recruits.forEach(r => {
            const skills = Object.entries(r.skills || {}).map(([s,v]) => `${skillLabel(s)} +${v}`).join(', ');
            const typeIcon = r.type === 'combat' ? '⚔️' : r.type === 'tech' ? '💻' : r.type === 'social' ? '🗣️' : '👤';
            html += `<div class="recruit-card">
                <div class="companion-name">${typeIcon} ${r.nickname ? r.nickname + ' — ' : ''}${r.name}</div>
                <div class="companion-type">${r.type || '?'}${r.faction ? ' │ ' + r.faction : ''}</div>
                ${r.description ? `<div class="recruit-desc">${r.description}</div>` : ''}
                ${skills ? `<div class="companion-bonus">⚡ ${skills}</div>` : ''}
                ${r.location ? `<div class="recruit-loc">📍 ${r.location}</div>` : ''}
                ${r.dialogue?.greeting ? `<div class="recruit-quote">"${r.dialogue.greeting}"</div>` : ''}
                <div class="recruit-footer">
                    ${r.cost ? `<span class="recruit-cost">₡${r.cost.toLocaleString('ru-RU')}</span>` : ''}
                    <button class="btn-buy" onclick="recruitCompanion(${JSON.stringify(r).replace(/"/g,'&quot;')})">Нанять</button>
                </div>
            </div>`;
        });

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка загрузки</div>'; }
}

async function recruitCompanion(companion) {
    const resp = await apiFetch('/api/companions/recruit', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ companion })
    });
    if (resp.success) {
        showToast(`🤝 ${companion.name || 'Компаньон'} присоединился!`, 'success');
        addNarrativeMessage(`🤝 ${companion.name} присоединился к группе!`, 'system');
        renderCompanionsPanel(document.getElementById('side-panel-content'));
    } else {
        showToast(resp.error || 'Не удалось нанять', 'error');
    }
}

async function dismissCompanion(id) {
    const resp = await apiFetch('/api/companions/dismiss', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ companion_id: id })
    });
    if (resp.success) {
        showToast('Компаньон отпущен', 'info');
        renderCompanionsPanel(document.getElementById('side-panel-content'));
    }
}

// ═══════════════════════════════════════════════════
// SHIP PANEL
// ═══════════════════════════════════════════════════
async function renderShipPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await apiFetch('/api/ship/info');
        const ship = data.ship;
        let html = '';

        if (!ship) {
            html += '<div class="empty-state">У вас нет корабля</div>';
            html += '<div class="panel-section-title">🚀 КУПИТЬ КОРАБЛЬ</div>';
            const classes = [
                {id: 'shuttle', name: 'Шаттл «Искра»', desc: 'Малый, дешёвый, без оружия', price: '~25,000'},
                {id: 'courier', name: 'Курьер «Стриж»', desc: 'Быстрый, лёгкое вооружение', price: '~75,000'},
                {id: 'freighter', name: 'Грузовик «Бык»', desc: 'Большой трюм, медленный', price: '~120,000'},
                {id: 'gunship', name: 'Канонерка «Коршун»', desc: 'Боевой, хорошая броня', price: '~200,000'},
            ];
            classes.forEach(c => {
                html += `<div class="ship-class-card">
                    <div class="ship-class-name">${c.name}</div>
                    <div class="ship-class-desc">${c.desc}</div>
                    <div class="ship-class-price">₡${c.price}</div>
                    <button class="btn-buy" onclick="buyShip('${c.id}')">Купить</button>
                </div>`;
            });
        } else {
            // Ship info
            const fuelPct = Math.round(ship.fuel / ship.fuel_max * 100);
            const hullPct = Math.round(ship.hull / ship.hull_max * 100);
            html += `<div class="ship-info">
                <div class="ship-name-big">${ship.name || 'Безымянный'}</div>
                <div class="ship-class-label">${ship.ship_class || '?'}</div>
            </div>`;

            html += `<div class="ship-stats">
                <div class="ship-stat">
                    <span>🛡 Корпус</span>
                    <div class="bar-bg"><div class="bar-fill hp-fill" style="width:${hullPct}%"></div></div>
                    <span>${ship.hull}/${ship.hull_max}</span>
                </div>
                <div class="ship-stat">
                    <span>⛽ Топливо</span>
                    <div class="bar-bg"><div class="bar-fill xp-fill" style="width:${fuelPct}%"></div></div>
                    <span>${ship.fuel}/${ship.fuel_max}</span>
                </div>
                ${ship.shields_max ? `<div class="ship-stat"><span>🔵 Щиты</span><span>${ship.shields || 0}/${ship.shields_max}</span></div>` : ''}
                ${ship.weapons ? `<div class="ship-stat"><span>⚔️ Оружие</span><span>${ship.weapons}</span></div>` : ''}
                ${ship.cargo_max ? `<div class="ship-stat"><span>📦 Трюм</span><span>${(ship.cargo || []).length}/${ship.cargo_max}</span></div>` : ''}
            </div>`;

            // Cargo
            if (ship.cargo_capacity || ship.cargo_max) {
                const cargo = ship.cargo || [];
                const cap = ship.cargo_capacity || ship.cargo_max || 0;
                html += `<div class="panel-section-title">📦 ТРЮМ (${cargo.length}/${cap})</div>`;
                if (cargo.length > 0) {
                    cargo.forEach(item => {
                        const name = typeof item === 'string' ? item : (item.name || '?');
                        html += `<div class="ship-upgrade">${name}</div>`;
                    });
                } else {
                    html += '<div class="empty-state">Пусто</div>';
                }
                html += `<button class="btn-buy" onclick="loadCargoPrompt()">📦 Загрузить груз</button>`;
            }

            // Upgrades
            if (ship.upgrades && ship.upgrades.length > 0) {
                html += '<div class="panel-section-title">⚙️ МОДИФИКАЦИИ</div>';
                ship.upgrades.forEach(u => {
                    html += `<div class="ship-upgrade">${u.name || u}</div>`;
                });
            }

            // Actions
            html += '<div class="ship-actions">';
            if (fuelPct < 100) {
                html += `<button class="btn-buy" onclick="refuelShip()">⛽ Заправить (₡${((ship.fuel_max - ship.fuel) * 5)})</button>`;
            }
            if (hullPct < 100) {
                html += `<button class="btn-buy" onclick="repairShip()">🔧 Ремонт</button>`;
            }
            html += `<button class="btn-buy" onclick="upgradeShipPrompt()">⚙️ Улучшить</button>`;
            html += '</div>';
        }
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function buyShip(shipClass) {
    const name = prompt('Назовите свой корабль:') || null;
    const resp = await apiFetch('/api/ship/buy', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ class: shipClass, name })
    });
    if (resp.success || resp.ship) {
        showToast(`🚀 Корабль куплен!`, 'success');
        addNarrativeMessage(`🚀 Вы приобрели корабль "${name || shipClass}"!`, 'system');
        renderShipPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось купить', 'error'); }
}

async function refuelShip() {
    const resp = await apiFetch('/api/ship/refuel', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' });
    if (resp.refueled) {
        showToast(`⛽ Заправлено! -₡${resp.cost}`, 'success');
        if (gameState?.character) gameState.character.credits -= resp.cost;
        updateCreditsUI(gameState?.character?.credits);
        renderShipPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Ошибка заправки', 'error'); }
}

async function repairShip() {
    const resp = await apiFetch('/api/ship/repair', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}' });
    if (resp.repaired || resp.success) {
        showToast(`🔧 Ремонт завершён! -₡${resp.cost || 0}`, 'success');
        renderShipPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Ошибка ремонта', 'error'); }
}

async function loadCargoPrompt() {
    const item = prompt('Какой предмет загрузить в трюм?');
    if (!item) return;
    const resp = await apiFetch('/api/ship/cargo/load', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ item, qty: 1 })
    });
    if (resp.success || resp.loaded) {
        showToast(`📦 Загружено: ${item}`, 'success');
        renderShipPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось загрузить', 'error'); }
}

async function upgradeShipPrompt() {
    const upgradeId = prompt('ID улучшения (shields, weapons, engines, stealth):');
    if (!upgradeId) return;
    const resp = await apiFetch('/api/ship/upgrade', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ upgrade_id: upgradeId })
    });
    if (resp.success || resp.installed) {
        showToast(`⚙️ Установлено: ${upgradeId}`, 'success');
        renderShipPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось установить', 'error'); }
}

// ═══════════════════════════════════════════════════
// PROPERTY PANEL
// ═══════════════════════════════════════════════════
async function renderPropertyPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await apiFetch('/api/property/list');
        const props = data.properties || [];
        let html = '';

        // Owned properties
        html += `<div class="panel-section-title">🏠 НЕДВИЖИМОСТЬ (${props.length})</div>`;
        if (props.length === 0) {
            html += '<div class="empty-state">Нет собственности</div>';
        }
        props.forEach(p => {
            const condClass = p.condition >= 70 ? 'good' : p.condition >= 40 ? 'fair' : 'bad';
            html += `<div class="property-card">
                <div class="property-name">${p.name}</div>
                <div class="property-type">${p.type} | 📍 ${typeof p.location === 'object' ? (p.location.district || p.location.city || '?') : p.location}</div>
                <div class="property-stats">
                    ${p.income_per_cycle > 0 ? `<span class="prop-income">💰 Доход: ₡${p.income_per_cycle}/цикл</span>` : ''}
                    <span>📦 Хранилище: ${(p.stored_items || []).length}/${p.storage_capacity}</span>
                    <span>🛡 Защита: ${p.defense_level}</span>
                    <span class="prop-cond ${condClass}">⚙ Состояние: ${p.condition}%</span>
                </div>
                <div class="property-features">${(p.features || []).map(f => `<span class="prop-feat">${f}</span>`).join('')}</div>
                <button class="btn-buy" onclick="storeItemInProperty('${p.id}')">📦 Положить предмет</button>
            </div>`;
        });

        // Income summary
        if (props.some(p => p.income_per_cycle > 0)) {
            const incomeData = await apiFetch('/api/property/income');
            if (incomeData.total_income > 0) {
                html += `<div class="property-income-total">💰 Общий доход: ₡${incomeData.total_income.toLocaleString('ru-RU')}/цикл</div>`;
            }
        }

        // Buy new property
        html += '<div class="panel-section-title">🏗 КУПИТЬ НЕДВИЖИМОСТЬ</div>';
        const types = [
            {id:'apartment', name:'Квартира', desc:'Отдых, сохранение', price:'~15,000'},
            {id:'warehouse', name:'Склад', desc:'100 слотов хранения, крафт-станция', price:'~30,000'},
            {id:'shop', name:'Магазин', desc:'Пассивный доход ₡500/цикл', price:'~50,000'},
            {id:'bar', name:'Бар', desc:'Доход ₡400, слухи, рекруты', price:'~45,000'},
            {id:'hideout', name:'Убежище', desc:'Скрытный, высокая защита', price:'~25,000'},
            {id:'office', name:'Офис фиксера', desc:'Доход ₡800, квесты, контакты', price:'~80,000'},
        ];
        types.forEach(t => {
            html += `<div class="ship-class-card">
                <div class="ship-class-name">${t.name}</div>
                <div class="ship-class-desc">${t.desc}</div>
                <div class="ship-class-price">₡${t.price}</div>
                <button class="btn-buy" onclick="buyProperty('${t.id}')">Купить</button>
            </div>`;
        });

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function buyProperty(propType) {
    const name = prompt('Название (или оставьте пустым):') || null;
    const loc = gameState?.location || {};
    const resp = await apiFetch('/api/property/buy', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: propType, location: loc, name })
    });
    if (resp.acquired) {
        showToast(`🏠 Приобретено: ${resp.acquired.name}`, 'success');
        addNarrativeMessage(`🏠 Вы купили ${resp.acquired.name}!`, 'system');
        renderPropertyPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось купить', 'error'); }
}

async function storeItemInProperty(propertyId) {
    const item = prompt('Какой предмет положить на хранение?');
    if (!item) return;
    const resp = await apiFetch('/api/property/store', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ property_id: propertyId, item })
    });
    if (resp.stored) {
        showToast(`📦 ${item} на хранении (${resp.capacity})`, 'success');
        renderPropertyPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось', 'error'); }
}

// ═══════════════════════════════════════════════════
// HACKING PANEL
// ═══════════════════════════════════════════════════
async function renderHackingPanel(container) {
    // Check if there's an active hack
    const hack = engine_hackState;
    let html = '';

    if (hack && hack.status === 'active') {
        // Active hacking session
        html += `<div class="hack-header">
            <div class="hack-target">🎯 ${hack.target || 'Система'}</div>
            <div class="hack-alert ${hack.alert >= 4 ? 'critical' : hack.alert >= 2 ? 'warning' : ''}">
                ⚠️ Тревога: ${hack.alert || 0}/${hack.max_alert || 5}
            </div>
            <div class="hack-turns">Ходов: ${hack.turns_left || '?'}</div>
        </div>`;

        // Network nodes
        html += '<div class="panel-section-title">🔗 СЕТЬ</div><div class="hack-nodes">';
        (hack.nodes || []).forEach((node, i) => {
            const isCurrent = i === hack.current_node;
            const isCleared = node.cleared;
            html += `<div class="hack-node ${isCurrent ? 'current' : ''} ${isCleared ? 'cleared' : ''}">
                <span class="node-idx">${i + 1}</span>
                <span class="node-ice">${isCleared ? '✅' : node.ice_type || '???'}</span>
                ${node.data ? `<span class="node-data">📦 ${node.data}</span>` : ''}
            </div>`;
        });
        html += '</div>';

        // Actions
        html += '<div class="panel-section-title">⌨️ ДЕЙСТВИЯ</div><div class="hack-actions">';
        const actions = [
            {id: 'crack_ice', label: '🔓 Взломать ICE', desc: 'Прямой взлом (шумно)'},
            {id: 'stealth_bypass', label: '🥷 Обойти', desc: 'Тихий обход (+1 ход)'},
            {id: 'advance', label: '➡️ Следующий нод', desc: 'Продвинуться вглубь'},
            {id: 'extract_data', label: '📥 Извлечь данные', desc: 'Скачать из текущего нода'},
            {id: 'disconnect', label: '🔌 Отключиться', desc: 'Безопасный выход'},
        ];
        actions.forEach(a => {
            html += `<button class="hack-action-btn" onclick="doHackAction('${a.id}')">
                <div class="hack-action-name">${a.label}</div>
                <div class="hack-action-desc">${a.desc}</div>
            </button>`;
        });
        html += '</div>';
    } else {
        // No active hack — show location-aware targets
        html += '<div class="empty-state">Нет активного взлома</div>';
        html += '<div class="panel-section-title">🎯 НАЧАТЬ ВЗЛОМ</div>';
        html += '<div id="hack-targets-list">Загрузка...</div>';
        setTimeout(() => loadHackTargets(), 50);
    }
    container.innerHTML = html;
}

async function loadHackTargets() {
    const el = document.getElementById('hack-targets-list');
    if (!el) return;
    try {
        const data = await apiFetch('/api/hacking/targets');
        if (data._error || !data.targets || data.targets.length === 0) {
            el.innerHTML = '<div class="empty-state">В этой локации нечего взламывать. Найдите терминал или сеть.</div>';
            return;
        }
        let html = '';
        if (data.location_name) {
            html += `<div class="hack-location">📍 ${data.location_name}</div>`;
        }
        data.targets.forEach(t => {
            const locked = t.requires_skill && (gameState?.character?.skills?.hacking || 0) < t.requires_skill;
            html += `<button class="hack-target-btn ${locked ? 'locked' : ''}" 
                ${locked ? 'disabled' : `onclick="startHack('${t.id}')"`}>
                <div class="hack-action-name">${t.name}</div>
                <div class="hack-action-desc">${t.desc}</div>
                ${t.difficulty ? `<div class="hack-diff">Сложность: ${t.difficulty}</div>` : ''}
                ${locked ? `<div class="hack-req">Нужен Хакинг ${t.requires_skill}+</div>` : ''}
            </button>`;
        });
        el.innerHTML = html;
    } catch { el.innerHTML = '<div class="empty-state">Ошибка загрузки</div>'; }
}

let engine_hackState = null;

async function startHack(targetType) {
    const resp = await apiFetch('/api/hacking/start', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ target_type: targetType })
    });
    if (resp.status === 'active' || resp.nodes) {
        engine_hackState = resp;
        showToast('💻 Подключение установлено!', 'info');
        addNarrativeMessage(`💻 Хакинг: подключение к "${targetType}"...`, 'system');
        renderHackingPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || resp.narrative || 'Ошибка подключения', 'error'); }
}

async function doHackAction(action) {
    const resp = await apiFetch('/api/hacking/action', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action })
    });
    if (resp.narrative) addNarrativeMessage(`💻 ${resp.narrative}`, 'system');
    if (resp.status === 'completed' || resp.status === 'detected' || resp.status === 'disconnected') {
        engine_hackState = null;
        if (resp.loot) {
            showToast(`💻 Взлом завершён! Добыча: ${resp.loot.map(l=>l.name||l).join(', ')}`, 'success', 5000);
        } else if (resp.status === 'detected') {
            showToast('🚨 Обнаружены! Соединение разорвано!', 'error');
        } else {
            showToast('💻 Отключились', 'info');
        }
    } else {
        engine_hackState = resp;
    }
    renderHackingPanel(document.getElementById('side-panel-content'));
}

// ═══════════════════════════════════════════════════
// INVESTIGATION PANEL
// ═══════════════════════════════════════════════════
async function renderInvestigationPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await apiFetch('/api/investigation/list');
        const cases = data.active || [];
        let html = '';

        if (cases.length === 0) {
            html += '<div class="empty-state">Нет активных расследований</div>';
        }

        // Open new case button
        html += `<button class="btn-buy" style="margin:8px 0" onclick="openNewCase()">🔍 Открыть новое дело</button>`;

        cases.forEach(c => {
            const cluesPct = c.clues ? Math.round(c.clues.length / (c.required_clues || 5) * 100) : 0;
            html += `<div class="case-card">
                <div class="case-title">📁 ${c.name || c.type || 'Дело'}</div>
                <div class="case-type">${c.type || '?'} | Статус: ${c.status || 'открыто'}</div>
                <div class="case-progress">
                    <span>Улики: ${(c.clues || []).length}/${c.required_clues || 5}</span>
                    <div class="bar-bg"><div class="bar-fill xp-fill" style="width:${cluesPct}%"></div></div>
                </div>`;

            // Show clues
            if (c.clues && c.clues.length > 0) {
                html += '<div class="case-clues">';
                c.clues.forEach(clue => {
                    html += `<div class="clue-item">🔎 <b>${clue.type || '?'}:</b> ${clue.description || clue.text || '?'}</div>`;
                });
                html += '</div>';
            }

            // Suspects
            if (c.suspects && c.suspects.length > 0) {
                html += '<div class="case-suspects">';
                c.suspects.forEach(s => {
                    html += `<div class="suspect-item">🧑 ${s.name || s}: ${s.motive || '?'}</div>`;
                });
                html += '</div>';
            }

            // Conclude button
            if (cluesPct >= 60) {
                html += `<button class="btn-buy" onclick="concludeCase('${c.id || 0}')">📋 Сделать выводы</button>`;
            }
            html += `<div class="case-actions">
                <button class="btn-buy" onclick="addClueToCase('${c.id || 0}')">🔎 Добавить улику</button>
                <button class="btn-buy" onclick="addSuspectToCase('${c.id || 0}')">🧑 Добавить подозреваемого</button>
            </div>`;
            html += '</div>';
        });

        if (data.closed_count > 0) {
            html += `<div class="panel-section-title">✅ Закрытые дела: ${data.closed_count}</div>`;
        }

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

async function concludeCase(caseId) {
    const suspect = prompt('Кого вы обвиняете? (введите имя)');
    if (!suspect) return;
    const resp = await apiFetch('/api/investigation/conclude', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ case_id: caseId, suspect })
    });
    if (resp.success || resp.result) {
        showToast(`📋 Дело закрыто: ${resp.result || 'Вердикт вынесен'}`, 'success', 5000);
        addNarrativeMessage(`📋 Расследование завершено: ${resp.result || resp.narrative || ''}`, 'system');
        renderInvestigationPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Не удалось', 'error'); }
}

async function openNewCase() {
    const name = prompt('Название дела (или оставьте пустым):');
    const types = ['murder', 'theft', 'conspiracy', 'missing_person', 'sabotage'];
    const type = prompt(`Тип дела (${types.join(', ')}):`) || 'theft';
    const resp = await apiFetch('/api/investigation/open', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type, name: name || undefined })
    });
    if (resp.name || resp.id) {
        showToast(`🔍 Дело открыто: ${resp.name || type}`, 'success');
        addNarrativeMessage(`🔍 Новое расследование: ${resp.name || type}`, 'system');
        renderInvestigationPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Ошибка', 'error'); }
}

async function addClueToCase(caseId) {
    const clueType = prompt('Тип улики (witness, physical, digital, document):') || 'physical';
    const description = prompt('Описание улики:');
    if (!description) return;
    const resp = await apiFetch('/api/investigation/clue', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ case_id: caseId, type: clueType, description })
    });
    if (resp.success || resp.added) {
        showToast(`🔎 Улика добавлена`, 'success');
        renderInvestigationPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Ошибка', 'error'); }
}

async function addSuspectToCase(caseId) {
    const name = prompt('Имя подозреваемого:');
    if (!name) return;
    const motive = prompt('Предполагаемый мотив:') || '';
    const resp = await apiFetch('/api/investigation/suspect', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ case_id: caseId, name, motive })
    });
    if (resp.success || resp.added) {
        showToast(`🧑 Подозреваемый добавлен: ${name}`, 'success');
        renderInvestigationPanel(document.getElementById('side-panel-content'));
    } else { showToast(resp.error || 'Ошибка', 'error'); }
}

// ═══════════════════════════════════════════════════
// FACTIONS PANEL
// ═══════════════════════════════════════════════════
async function renderFactionsPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
        const data = await apiFetch('/api/factions');
        const factions = data.factions || [];
        let html = '<div class="panel-section-title">⚖️ РЕПУТАЦИЯ ФРАКЦИЙ</div>';

        if (factions.length === 0) {
            html += '<div class="empty-state">Пока нет данных о репутации</div>';
        }

        factions.forEach(f => {
            const rep = f.reputation || 0;
            const pct = Math.min(100, Math.max(0, 50 + rep / 2));
            const color = rep >= 50 ? '#44ff44' : rep >= 20 ? '#88ff88' : rep >= -20 ? '#aaaaaa' : rep >= -50 ? '#ffaa00' : '#ff4444';
            const standing = f.standing || (rep >= 50 ? 'Союзник' : rep >= 20 ? 'Дружелюбный' : rep >= -20 ? 'Нейтральный' : rep >= -50 ? 'Подозрительный' : 'Враждебный');
            html += `<div class="faction-card">
                <div class="faction-header">
                    <span class="faction-name">${f.faction}</span>
                    <span class="faction-standing" style="color:${color}">${standing}</span>
                </div>
                <div class="faction-bar">
                    <div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
                    <span class="faction-rep" style="color:${color}">${rep >= 0 ? '+' : ''}${rep}</span>
                </div>
            </div>`;
        });

        html += '<div class="panel-section-title" style="margin-top:16px;font-size:0.8em;color:#666">Репутация меняется от ваших действий. Помощь фракции повышает статус, враждебные действия — понижают.</div>';
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

// ---- Helpers ----
function setText(id, text) { const el = document.getElementById(id); if (el) el.textContent = text; }
function formatNum(n) { return n?.toLocaleString('ru-RU') || '0'; }
function formatDate(iso) {
    if (!iso) return '?';
    try { return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); } catch { return iso; }
}
function showLoading(show) { document.getElementById('loading-overlay').classList.toggle('hidden', !show); }

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => { loadSettings(); bootSequence(); });
