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
// Phase 26: expose to window for CDP tests and console inspection
// (let is block-scoped; window assignment re-uses the same object reference)
Object.defineProperty(window, 'gameState', {
    get() { return gameState; },
    set(v) { gameState = v; }
});
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
    // Phase 27 D6: расширенные русские имена (включая канонизацию tactics)
    tactics: 'Тактика', leadership: 'Лидерство', deception: 'Обман',
    intimidation: 'Запугивание', streetwise: 'Уличная интуиция',
    close_quarters: 'Ближний бой CQB', boarding_tactics: 'Абордажная тактика',
    first_aid_combat: 'Боевая медицина', zero_g_combat: 'Нуль-G бой',
    heavy_weapons: 'Тяжёлое оружие', sniping: 'Снайперская стрельба',
    armor_operation: 'Тяжёлая броня', evasion: 'Уклонение',
    tracking: 'Следопытство', drones: 'Дроны и рой',
    research: 'Исследования', biology2: 'Биология продвинутая',
    education: 'Образование', diplomacy2: 'Дипломатия',
    navigation_astrogation: 'Навигация и астрогация', ship_systems: 'Корабельные системы',
    electronics_repair: 'Ремонт электроники', network_security: 'Сетевая безопасность',
    crypto_analysis: 'Криптоанализ', robotics: 'Робототехника',
    demolition: 'Подрывное дело', zero_g: 'Нуль-G перемещение',
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


// Phase 4.1: синхронизация мини-HUD бейджа с engine_hackState (без ожидания game_state)
function updateHackBadge() {
    const badge = document.getElementById('hack-badge');
    if (!badge) return;
    if (engine_hackState && engine_hackState.status === 'active') {
        badge.classList.add('visible');
        const targetEl = document.getElementById('hack-badge-target');
        if (targetEl) targetEl.textContent = engine_hackState.target ? ' · ' + engine_hackState.target : '';
    } else if (gameState && gameState.active_hack) {
        badge.classList.add('visible');
    } else {
        badge.classList.remove('visible');
    }
}

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

    // Phase 4.1: хакерский мини-HUD — булев индикатор активного хака (client_state.active_hack).
    // Детали (target/alert/turns) доступны только из engine_hackState текущей сессии;
    // если вкладка ХАКИНГ не открывалась (или после F5) — показываем только статус HACK.
    const badge = document.getElementById('hack-badge');
    if (badge) {
        if (state.active_hack) {
            badge.classList.add('visible');
            const targetEl = document.getElementById('hack-badge-target');
            if (targetEl) targetEl.textContent = engine_hackState?.target ? ' · ' + engine_hackState.target : '';
        } else {
            badge.classList.remove('visible');
        }
    }
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

    // Phase 28 F6: нарративная обёртка исхода + тумблер подробных кубов
    const outcomeText = diceOutcomeNarrative(dice);
    const showDetails = localStorage.getItem('nexus_dice_details') === '1';
    let detailsHtml = '';
    if (showDetails) {
        detailsHtml = `
        <div class="dice-formula">[${dice.rolls?.join(', ')}] = ${dice.roll_total || 0} + ${dice.bonus || 0} = <b>${dice.result || 0}</b> vs DC ${dice.difficulty || 10}</div>
        ${modsHtml}
        <div class="${cls}"><b>${labels[dice.quality] || dice.quality}</b> (${dice.margin >= 0 ? '+' : ''}${dice.margin || 0})</div>`;
    } else {
        detailsHtml = `<div class="${cls}"><b>${labels[dice.quality] || dice.quality}</b></div>`;
    }
    div.innerHTML = `
        <div class="dice-header">🎲 ${skillName} + ${attrName}</div>
        ${outcomeText ? `<div class="dice-outcome">${outcomeText}</div>` : ''}
        ${detailsHtml}
    `;
    scroll.appendChild(div);
    scrollNarrative();
}

// Phase 28 F6: краткий литературный исход броска вместо голой математики
function diceOutcomeNarrative(dice) {
    const skill = skillLabel(dice.skill || '');
    const success = dice.success !== false && ['critical_success', 'great_success', 'success'].includes(dice.quality);
    const margin = Math.abs(dice.margin || 0);
    const degree = margin >= 8 ? 'с решительным преимуществом' : margin >= 4 ? 'уверенно' : 'едва ли';
    if (success) {
        return `✅ УСПЕХ: ${skill ? 'применение навыка «' + skill + '» ' : ''}позволило ${degree} добиться цели.`;
    }
    return `❌ НЕУДАЧА: ${skill ? '«' + skill + '» не сработал' : 'попытка провалилась'}${margin >= 4 ? ' — последствия неизбежны' : ''}.`;
}

// Тумблер подробных кубов (вызывается из кнопки тулбара)
function toggleDiceDetails() {
    const cur = localStorage.getItem('nexus_dice_details') === '1';
    localStorage.setItem('nexus_dice_details', cur ? '0' : '1');
    const btn = document.getElementById('btn-dice-details');
    if (btn) {
        btn.classList.toggle('thud-active', !cur);
        btn.title = !cur ? 'Кубы: ПОДРОБНО (клик — скрыть)' : 'Кубы: только исход (клик — подробно)';
    }
    showToast(cur ? '🎲 Кубы: только исход' : '🎲 Кубы: подробная математика', 'info');
}

function formatNarrative(text) {
    if (!text) return '';

    // Split narrative from choices block
    let narrativePart = text;
    let choicesHtml = '';

    // Phase 26 fix: вырезаем блоки [MECHANICS]...[/MECHANICS] и [ACTION]...[/ACTION]
    // (ИИ иногда оборачивает механики и действия в такие блоки).
    // Phase 27 D1: вырезаем телеметрию [HP: +5], [HEAT: ...], [TIME: ...] и т.п.
    narrativePart = narrativePart
        // Phase 27 D1: незакрытый [STATE] (модель забывает [/STATE]) — до конца текста
        .replace(/\[STATE\][\s\S]*$/i, '')
        // Закрытые блоки — удаляем целиком
        .replace(/\[MECHANICS\][\s\S]*?\[\/MECHANICS\]/gi, '')
        .replace(/\[ACTION\][\s\S]*?\[\/ACTION\]/gi, '')
        // Незакрытые [MECHANICS] без перевода на choices — вырезаем до конца абзаца
        .replace(/\[MECHANICS\][^\[]*?(?=\n\n|\[|\d+\.|$)/gi, '')
        // Незакрытый [ACTION] — вырезаем саму метку, но оставляем строки после
        .replace(/\[ACTION\]\s*\n/gi, '')
        // Телеметрия: отдельные строки с [HP: ±N] и компания
        .replace(/^\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|SANITY|FUEL)\s*[:±][^\]]*\]\s*$/gim, '')
        // Телеметрия: инлайн-вхождения
        .replace(/\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|SANITY|FUEL)\s*[:±][^\]]*\]/gi, '')
        // Phase 27 R7: заголовки структуры промпта («1) НАРРАТИВ», «2) МЕХАНИЧЕСКИЕ ИЗМЕНЕНИЯ»...)
        .replace(/^\s*(?:#+\s*)?\*{0,2}\d\s*[).—-]\s*(?:НАРРАТИВ|МЕХАНИЧЕСКИЕ\s+ИЗМЕНЕНИЯ|ЗАГОЛОВОК\s+ВЫБОРА|ПРОНУМЕРОВАННЫХ\s+ВАРИАНТОВ|ВАРИАНТЫ\s+ДЕЙСТВИЙ|СВОБОДНЫЙ\s+ВВОД|7-Й\s+ВАРИАНТ|СТРУКТУРА\s+ОТВЕТА)\*{0,2}\s*[:—*-]?\s*$/gim, '')
        // Phase 28 F1: сырые ```json/``` блоки (закрытые и незакрытые)
        .replace(/```(?:json)?[\s\S]*?(?:```|$)/gi, '')
        // Phase 28 F1: инструкции нумерации и форматирования из промпта
        .replace(/^\s*(?:#+\s*)?\*{0,2}(?:\d\s*[).—-]?\s*(?:\d\s*-\s*\d\s*)?)?(?:ПРОНУМЕРОВАННЫХ\s+ВАРИАНТОВ\s+ДЕЙСТВИЙ[^\n]*|СТРОГО\s+В\s+ФОРМАТЕ[^\n]*|Ролевые\s+теги\s+ВСЕГДА[^\n]*|После\s+тега\s+—[^\n]*|7-Й\s+ВАРИАНТ\s+—\s+СВОБОДНЫЙ\s+ВВОД[^\n]*|Если\s+требуется\s+проверка\s+навыков[^\n]*|НЕ\s+выходи\s+за\s+пределы[^\n]*)\*{0,2}\s*$/gim, '');

    // Find the choices block (various formats the AI might use)
    const choicePatterns = [
        /\*?\*?Что будешь делать\??\*?\*?\s*\n/i,
        /\*?\*?Что (?:ты )?(?:будешь|хочешь) делать\??\*?\*?\s*\n/i,
        /\*?\*?Выбери действие:?\*?\*?\s*\n/i,
        /\*?\*?Доступные действия:?\*?\*?\s*\n/i,
        // Phase 26 fix: варианты с маркером [ACTION] перед списком
        /\[ACTION\]\s*\n?/i,
    ];

    let choiceStart = -1;
    for (const pat of choicePatterns) {
        const m = narrativePart.search(pat);
        if (m !== -1) { choiceStart = m; break; }
    }

    // Phase 26 fix: если ни один заголовок не найден, ищем первую
    // нумерованную строку вида "1. [ТЕГ]..." — некоторые ИИ дают список
    // сразу без заголовка "Что будешь делать?"
    if (choiceStart === -1) {
        const numberedMatch = narrativePart.match(/^\s*\d+\.\s*\[/m);
        if (numberedMatch) {
            choiceStart = numberedMatch.index;
        }
    }

    if (choiceStart !== -1) {
        narrativePart = narrativePart.substring(0, choiceStart).trim();
        const choicesText = text.substring(text.indexOf(narrativePart) + narrativePart.length);

        // Parse numbered choices (1. ... 2. ... etc)
        const choiceLines = [];
        const lineRegex = /^\s*(\d+)\.\s*(.+)$/gm;
        let match;
        while ((match = lineRegex.exec(choicesText)) !== null) {
            choiceLines.push({ num: match[1], text: match[2].trim() });
        }

        // Phase 26 fix: fallback — если нумерованных нет, но есть строки с [TAG] в начале,
        // попробуем парсить их (некоторые ИИ пропускают нумерацию, но дают [ТЕГ] — описание)
        if (choiceLines.length === 0) {
            const tagRegex = /^\s*\[([А-Яа-яЁё\s]+)\]\s*(.+)$/gm;
            let tagMatch;
            let idx = 1;
            while ((tagMatch = tagRegex.exec(choicesText)) !== null) {
                choiceLines.push({ num: String(idx++), text: `[${tagMatch[1]}] ${tagMatch[2].trim()}` });
            }
        }

        if (choiceLines.length > 0) {
            choicesHtml = '<div class="choices-block"><div class="choices-title">Что будешь делать?</div><div class="choices-grid">';
            for (const ch of choiceLines) {
                // Phase 26 fix: вырезаем [ТЕГ] из отображаемого текста (он только для классификации)
                const displayText = ch.text.replace(/^\s*\[[А-Яа-яЁё\s]+\]\s*/, '').trim();
                const isCustom = ch.num === '7' || displayText.toLowerCase().includes('свой вариант');
                if (isCustom) {
                    choicesHtml += `<div class="choice-btn choice-custom" onclick="choiceCustom()">
                        <span class="choice-num">✎</span>
                        <span class="choice-text">Свой вариант</span>
                    </div>`;
                } else {
                    const escaped = displayText.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                    choicesHtml += `<div class="choice-btn" onclick="choiceSelect('${escaped}')">
                        <span class="choice-num">${ch.num}</span>
                        <span class="choice-text">${escaped}</span>
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
        // Phase 26 fix: вырезаем оставшиеся одиночные блоки [MECHANICS] и [ACTION]
        // (на случай если они остались после первого прохода)
        .replace(/\[MECHANICS\][^\[]*?(?=\n\n|\[|\d+\.|$)/gi, '')
        .replace(/\[ACTION\]\s*\n/gi, '')
        // Phase 26 fix (round 2): вырезаем одиночные inline-теги механик,
        // которые ИИ иногда оставляет прямо в нарративе:
        //   [HP: -5], [HEAT: +2], [CREDITS: 100], [STRESS: -3], [HUMANITY: -1], [TIME: +1ч]
        // Каждый тег заменяется на пустую строку (теряется при рендере, но
        // пользователь всё равно видит эффект через UI-нотификации).
        .replace(/\[(?:HP|HEAT|CREDITS|STRESS|HUMANITY|TIME|XP|MONEY|FAME|HEAT|HEALTH)[^\]]*\]/gi, '')
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
        // Phase 27 D1: [STATE]-блок и телеметрия не показываются даже во время стриминга
        .replace(/\[STATE\][\s\S]*$/i, '')
        .replace(/^\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|SANITY|FUEL)\s*[:±][^\]]*\]\s*$/gim, '')
        .replace(/\s*\[(?:HP|HEAT|TIME|CREDITS|STRESS|HUMANITY|XP|SANITY|FUEL)\s*[:±][^\]]*\]/gi, '')
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
        contracts:     ['КОНТРАКТЫ',      (c) => window.ContractsBoard && ContractsBoard.render(c)],
        shop:          ['МАГАЗИН',        renderShopPanel],
        world:         ['НОВОСТИ МИРА',   renderWorldPanel],
        map:           ['ЛОКАЦИЯ',        renderMapPanel],
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
    // Phase 31 H5: принадлежность — фракция с максимальной репутацией или «независимый агент»
    const _rels = (gameState && gameState.faction_relations) || [];
    if (_rels.length) {
        const best = _rels.reduce((a, b) => (b.standing > a.standing ? b : a));
        const affil = best.standing >= 15
            ? `${best.name} (репутация ${best.standing > 0 ? '+' : ''}${best.standing})`
            : `Независимый агент (лучшая репутация: ${best.name} ${best.standing > 0 ? '+' : ''}${best.standing})`;
        html += `<div class="char-info-row"><span class="char-info-label">Принадлежность</span><span class="char-info-val">${affil}</span></div>`;
    } else {
        html += `<div class="char-info-row"><span class="char-info-label">Принадлежность</span><span class="char-info-val">Независимый агент</span></div>`;
    }
    if (c.age) html += `<div class="char-info-row"><span class="char-info-label">Возраст</span><span class="char-info-val">${c.age}</span></div>`;
    html += `<div class="char-info-row"><span class="char-info-label">Уровень</span><span class="char-info-val">${c.level || 1}</span></div>`;
    // Phase 28 F5: прогресс уровня + кнопка прокачки при накопленных очках
    const xpNow = c.xp || 0, xpNext = c.xp_next || 1000;
    const xpPct = Math.min(100, Math.round(xpNow / Math.max(1, xpNext) * 100));
    const f5Skill = c.unspent_skill_points || 0;
    const f5Attr = c.unspent_attribute_points || 0;
    const canLevelUp = f5Skill > 0 || f5Attr > 0;
    html += `<div style="margin:6px 0 10px">
        <div style="display:flex;justify-content:space-between;font-size:0.78em;color:var(--text2)"><span>Опыт</span><span>${xpNow} / ${xpNext}</span></div>
        <div class="bar-bg" style="height:8px"><div class="bar-fill xp-fill" style="width:${xpPct}%"></div></div>
    </div>`;
    if (canLevelUp) {
        html += `<button class="btn btn-sm" style="background:var(--gold,#ffd700);color:#111;font-weight:700;margin-bottom:10px"
            onclick="openLevelUpPanel()">⬆ Повысить характеристики / навыки (${f5Attr} АТР · ${f5Skill} нав.)</button>`;
    }

    // Phase 27 D6: Тир влияния P0-P7
    const tier = c.influence_tier;
    if (tier) html += `<div class="char-info-row"><span class="char-info-label">Тир влияния</span><span class="char-info-val" style="color:var(--accent)">P${tier.tier} — ${tier.name || tier.tier_name || ''}</span></div>`;
    html += '</div>';

    // Phase 27 D6: черты происхождения (Origin Traits)
    const traits = c.origin_traits || [];
    if (traits.length) {
        html += '<div class="panel-section-title">🧬 ЧЕРТЫ ПРОИСХОЖДЕНИЯ</div><div class="trait-list">';
        traits.forEach(t => { html += `<div class="trait-item">▸ ${t}</div>`; });
        html += '</div>';
    }

    // Phase 27 D6: отношения с ключевыми фракциями региона
    const rels = c.faction_relations || [];
    if (rels.length) {
        html += '<div class="panel-section-title">⚖️ ОТНОШЕНИЯ ФРАКЦИЙ РЕГИОНА</div>';
        rels.forEach(r => {
            const color = r.standing > 0 ? 'var(--accent)' : r.standing < 0 ? '#f66' : 'var(--text2)';
            html += `<div class="char-info-row"><span class="char-info-label">${r.name}</span><span class="char-info-val" style="color:${color}">${r.standing > 0 ? '+' : ''}${r.standing} · ${r.attitude}</span></div>`;
        });
    }

    // Attributes — show base (effective) and + to allocate if unspent points
    const attrBonuses = c.attr_bonuses || {};
    const unspentAttr = c.unspent_attribute_points || 0;
    const maxAttr = c.max_attribute || 10;
    html += '<div class="panel-section-title">АТРИБУТЫ</div><div class="attr-grid">';
    for (const [k, v] of Object.entries(c.attributes || {})) {
        const bonus = attrBonuses[k] || 0;
        const eff = v + bonus;
        const onCap = v >= maxAttr;
        const clickable = unspentAttr > 0 && !onCap;
        const cls = clickable ? 'attr-item-can-upgrade' : onCap ? 'attr-item-cap' : '';
        html += `<div class="attr-item ${cls}" ${clickable ? `onclick="spendAttributePoint('${k}')"` : ''}>
            <span class="attr-name">${attrLabel(k)}</span>
            <span class="attr-val">${v}${bonus > 0 ? ' <span class="attr-bonus">(+${bonus})</span>' : ''}</span>
            ${clickable ? '<span class="attr-upgrade-btn">+</span>' : ''}
        </div>`;
    }
    html += '</div>';

    // Phase 28 F5: показываем ВСЕ навыки мира — нулевые приглушённо (ветки развития видны)
    html += '<div class="panel-section-title">НАВЫКИ</div><div class="skill-list">';
    // Phase 31 H6: прокачка навыков существует (кнопка «⬆ Повысить» при свободных очках,
    // механика spendSkillPoint + endpoint). Строки навыков теперь кликабельны — открывают
    // панель прокачки, чтобы механизм был обнаружим в UI.
    const skillEntries = Object.entries(c.skills || {}).sort((a, b) => b[1] - a[1]);
    const canLevelUpHint = (c.unspent_skill_points || 0) > 0 || (c.unspent_attribute_points || 0) > 0;
    for (const [k, v] of skillEntries) {
        const title = canLevelUpHint
            ? 'title="Есть свободные очки — нажмите, чтобы распределить"'
            : 'title="Очки навыков появляются при росте уровня"';
        if (v > 0) {
            html += `<div class="skill-item" style="cursor:pointer" ${title} onclick="openLevelUpPanel()"><span class="skill-name">${skillLabel(k)}</span><span class="skill-val">${v}</span></div>`;
        } else {
            html += `<div class="skill-item skill-zero" style="cursor:pointer" ${title} onclick="openLevelUpPanel()"><span class="skill-name">${skillLabel(k)}</span><span class="skill-val">0</span></div>`;
        }
    }
    html += '</div>';
    html += `<div style="font-size:0.75em;color:var(--text2);margin:4px 0 8px">Нажмите на навык, чтобы открыть панель прокачки${canLevelUpHint ? ' — есть свободные очки!' : ''}.</div>`;

    // Extras: psychology, skill points, perks
    html += renderCharacterPanelExtras();

    container.innerHTML = html;
}

async function renderInventoryPanel(container) {
    // Phase 27 R2: единственный источник данных — /api/inventory/slots (слоты + вес + имя для действий).
    // Прежняя двойная загрузка (slots + flat list) гонялась и давала рассинхрон («пустой» инвентарь).
    try {
        const slotsData = await (await fetch('/api/inventory/slots')).json();
        if (!slotsData || !slotsData.slots) throw new Error('bad payload');

        const { weapon = [], armor = [], implant = [], pocket = [] } = slotsData.slots;
        const total = slotsData.total_weight || 0, cap = slotsData.capacity || 50;
        const all = [...weapon, ...armor, ...implant, ...pocket];

        if (!all.length) {
            container.innerHTML = '<div class="empty-state">Сумка пуста. Снаряжение выдаётся при создании персонажа и покупается в магазинах.</div>';
            return;
        }

        const pct = Math.min(100, Math.round(total / cap * 100));
        const wEmoji = slotsData.overloaded ? '⚠️' : '⚖️';
        let html = `<div class="panel-hint">${wEmoji} Вес: ${total} / ${cap} кг ${slotsData.overloaded ? '— ПЕРЕГРУЗ!' : ''}</div>`;
        html += `<div class="bar-bg" style="margin-bottom:10px"><div class="bar-fill ${slotsData.overloaded ? 'stress' : 'xp-fill'}" style="width:${pct}%"></div></div>`;

        const groups = [
            ['🔫 ОРУЖИЕ', weapon],
            ['🛡 БРОНЯ', armor],
            ['🧬 ИМПЛАНТЫ', implant],
            ['👖 КАРМАН', pocket],
        ];
        groups.forEach(([title, items]) => {
            html += `<div class="panel-section-title">${title} (${items.length})</div>`;
            if (!items.length) {
                html += '<div class="empty-state" style="padding:4px">— пусто —</div>';
                return;
            }
            items.forEach(it => {
                const nm = (it.name || '?').replace(/'/g, "\'");
                // Phase 28 G1: кнопки строго по типу предмета
                const equippedMark = it.equipped ? ' <span style="color:var(--accent)">◆</span>' : '';
                let actionBtns = '';
                if (it.usable) {
                    actionBtns = `<button class="btn-sell" style="background:#2a5a2a" onclick="useItem('${nm}')">Использовать</button>`;
                } else if (it.equippable) {
                    actionBtns = it.equipped
                        ? `<button class="btn-sell" style="background:#5a4a2a" onclick="equipItem('${nm}', 'unequip')">Снять</button>`
                        : `<button class="btn-sell" style="background:#2a4a5a" onclick="equipItem('${nm}', 'equip')">Экипировать</button>`;
                } else {
                    // Phase 31 H8: tool-предметы (лабораторный набор, анализатор, журнал) —
                    // scene-items по дизайну: применяются автоматически в сценах сканирования/
                    // расследования. Показываем пояснение вместо «мёртвой» кнопочной зоны.
                    actionBtns = `<span style="font-size:0.72em;color:var(--text2);max-width:150px;text-align:right" title="Этот инструмент применяется автоматически в подходящих сценах (сканирование, расследование, взлом)">инструмент для сцен</span>`;
                }
                html += `<div class="shop-item">
                    <div class="shop-item-info">
                        <div class="shop-item-name">${it.name || '?'}${equippedMark} ${it.qty > 1 ? `×${it.qty}` : ''}</div>
                        ${it.stats ? `<div class="shop-item-stats">${it.stats} · ${it.weight} кг</div>` : `<div class="shop-item-stats">${it.weight} кг</div>`}
                    </div>
                    <div style="display:flex;gap:4px">
                        ${actionBtns}
                        <button class="btn-sell" onclick="sellItemByName('${nm}')">Продать</button>
                    </div>
                </div>`;
            });
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = '<div class="empty-state">Ошибка загрузки инвентаря. <button class="btn-sell" onclick="togglePanel(\'inventory\')">Повторить</button></div>';
    }
}

// Phase 27 R2: продажа по имени — индекс из слот-панели не соответствует плоскому списку
// Phase 27 D2 (восстановлено в Phase 30: R2-splice удалил функции, onclick остался)
async function questContact(questId) {
    if (!questId) { showToast('Квест без идентификатора', 'error'); return; }
    // Связаться с заказчиком = инициировать диалог через игровой поток
    sendAction(`Связываюсь с заказчиком квеста и обсуждаю детали задания`);
}

async function questAbandon(questId) {
    if (!questId) { showToast('Квест без идентификатора', 'error'); return; }
    if (!confirm('Отказаться от этого квеста? Репутация заказчика может пострадать.')) return;
    try {
        const resp = await fetch('/api/quests/abandon', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ quest_id: questId })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`📴 Вы отказались от задания «${data.quest_title || questId}».`, 'system');
            const content = document.getElementById('side-panel-content');
            renderQuestsPanel(content);
            if (data.game_state) { gameState = data.game_state; updateGameUI(gameState); }
        } else {
            showToast(data.error || 'Не удалось отказаться', 'error');
        }
    } catch (e) { showToast('Ошибка сети: ' + e.message, 'error'); }
}

async function sellItemByName(name) {
    try {
        const resp = await fetch('/api/shop/sell', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name })
        });
        const data = await resp.json();
        if (data.success) {
            showToast(`💰 ${data.message}`, 'success');
            const content = document.getElementById('side-panel-content');
            renderInventoryPanel(content);
            if (gameState) { gameState.character.credits = data.credits; updateCreditsUI(data.credits); }
        } else {
            showToast(data.error || 'Ошибка продажи', 'error');
        }
    } catch { showToast('Ошибка продажи', 'error'); }
}

// Обратная совместимость: старые вызовы по индексу
async function sellItem(index) { sellItemByName(''); }

// Phase 28 G3: войти в заведение и сразу открыть его магазин
async function enterAndShop(placeName) {
    await enterPlace(placeName);      // серверная фиксация + UI-плашка
    togglePanel('shop');              // магазин отрендерит ассортимент этого заведения
}

// Phase 28 G4: вход в заведение (сервер + плашка + реакция окружения)
async function enterPlace(placeName) {
    try {
        const resp = await fetch('/api/map/enter', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ place: placeName })
        });
        const data = await resp.json();
        if (data.success) {
            if (gameState) {
                gameState.location = data.location;
                updateGameUI(gameState);
            }
            const loc = data.location || {};
            addNarrativeMessage(`📍 Текущее положение: ${loc.planet || '?'} → ${loc.city || '?'} → ${loc.district || '?'} → <b>${placeName}</b>`, 'system');
            if (data.ambience) addNarrativeMessage(data.ambience, 'system');
        }
    } catch (e) { showToast('Ошибка входа: ' + e.message, 'error'); }
}

// Phase 28 G1: экипировать/снять
async function equipItem(name, action) {
    try {
        const resp = await fetch('/api/inventory/equip', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ item_name: name, action })
        });
        const data = await resp.json();
        if (data.success) {
            showToast(`🔧 ${data.message}`, 'success');
            const content = document.getElementById('side-panel-content');
            if (document.getElementById('side-panel')?.dataset.current === 'inventory') {
                renderInventoryPanel(content);
            }
        } else {
            showToast(data.error || 'Ошибка', 'error');
        }
    } catch (e) { showToast('Ошибка сети: ' + e.message, 'error'); }
}

// Phase 27 R1: мгновенное использование расходника БЕЗ LLM
async function useItem(name) {
    try {
        const resp = await fetch('/api/inventory/use', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ item_name: name })
        });
        const data = await resp.json();
        if (data.success) {
            // Тихое обновление HUD — БЕЗ спама в окно истории
            showToast(`💉 ${data.message}`, 'success');
            if (data.hp !== undefined && gameState?.character) {
                gameState.character.hp = data.hp;
                gameState.character.hp_max = data.hp_max;
                updateGameUI(gameState);
            }
            const content = document.getElementById('side-panel-content');
            if (document.getElementById('side-panel')?.dataset.current === 'inventory') {
                renderInventoryPanel(content);
            }
        } else {
            showToast(data.error || 'Нельзя использовать', 'error');
        }
    } catch (e) { showToast('Ошибка сети: ' + e.message, 'error'); }
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

        // Phase 4.1: терминальный стиль (Ascii.bar + .ti-*; см. terminal_hud.css)
        const humBar = window.Ascii ? Ascii.bar(humanity, 100, 20) : '[' + '#'.repeat(Math.round(humanity/5)).padEnd(20, '·') + ']';
        const humColor = humanity > 60 ? 'var(--green, #33ff66)' : humanity > 30 ? 'var(--gold, #ffd700)' : 'var(--red, #ff4466)';
        const clinic = nearClinic
            ? `<span class="ti-clinic-ok">[КЛИНИКА РЯДОМ · ₡${fee.toLocaleString()}]</span>`
            : `<span class="ti-clinic-no">[КЛИНИКИ НЕТ · САМОУСТАНОВКА DC+4]</span>`;

        let html = '<div class="ti-panel">';
        html += `<div class="ti-header">
            <div class="ti-header-line">
                <span>ЧЕЛОВЕЧНОСТЬ: <b style="color:${humColor}">${humanity}/100</b></span>
                <span>СЛОТЫ: <b>${usedSlots}/${slots}</b></span>
            </div>
            <div class="ti-header-line"><span>${clinic}</span></div>
        </div>`;
        html += `<div class="ti-humanity-bar">HUM ${humBar}</div>`;

        // Installed
        html += '<div class="ti-section-title">// УСТАНОВЛЕНЫ</div>';
        if (installed.length === 0) {
            html += '<div class="ti-empty">— нет установленных имплантов —</div>';
        } else {
            installed.forEach(imp => {
                const bonuses = [];
                for (const [s, v] of Object.entries(imp.skill_bonuses || {})) {
                    bonuses.push(`${skillLabel(s)} +${v}`);
                }
                for (const [a, v] of Object.entries(imp.attr_bonuses || {})) {
                    bonuses.push(`${attrLabel(a)} ${v > 0 ? '+' : ''}${v}`);
                }
                html += `<div class="ti-card installed">
                    <div class="implant-info">
                        <div class="ti-name rarity-${imp.rarity || 'common'}">■ ${imp.name}</div>
                        <div class="ti-stats">${imp.stats || ''}</div>
                        ${bonuses.length ? '<div class="ti-bonuses">↑ ' + bonuses.join(' · ') + '</div>' : ''}
                    </div>
                    <button class="ti-btn ti-btn-remove" onclick="removeImplant(${imp.inv_index})">[ СНЯТЬ ]</button>
                </div>`;
            });
        }

        // Available for install
        html += '<div class="ti-section-title">// В ИНВЕНТАРЕ — ДОСТУПНО К УСТАНОВКЕ</div>';
        if (available.length === 0) {
            html += '<div class="ti-empty">— имплантов в инвентаре нет (магазин: категория ИМПЛАНТЫ) —</div>';
        } else {
            available.forEach(imp => {
                const dc = imp.surgery_dc + (nearClinic ? 0 : 4);
                const humCost = imp.humanity_cost || 0;
                html += `<div class="ti-card available">
                    <div class="implant-info">
                        <div class="ti-name rarity-${imp.rarity || 'common'}">□ ${imp.name}</div>
                        <div class="ti-stats">${imp.stats || ''}</div>
                        <div class="ti-meta">DC ${dc} · ЧЕЛОВЕЧНОСТЬ −${humCost}${nearClinic ? ' · ₡' + fee.toLocaleString() : ''}</div>
                    </div>
                    <button class="ti-btn ti-btn-install" onclick="installImplant(${imp.inv_index})"
                        ${usedSlots >= slots ? 'disabled title="Нет свободных слотов"' : ''}>
                        [ УСТАНОВИТЬ ]
                    </button>
                </div>`;
            });
        }
        html += '</div>';

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
        // Phase 27 R3: магазин доступен только в торговых зонах
        // Phase 28 G3: в торговой зоне, но не в конкретном заведении → выбор точки
        if (data.needs_place_selection) {
            let pickHtml = `<div class="empty-state">🏪 ${data.hint || 'Выберите торговое заведение'}</div>`;
            (data.trade_establishments || []).forEach(t => {
                pickHtml += `<div class="map-establishment" onclick="enterAndShop('${String(t).replace(/'/g, "\'")}')">
                    <div class="map-estab-name">◈ ${t}</div>
                </div>`;
            });
            pickHtml += `<div class="shop-credits">Баланс: ₡${credits.toLocaleString('ru-RU')}</div>`;
            container.innerHTML = pickHtml;
            return;
        }
        if (data.allowed === false) {
            let offHtml = `<div class="empty-state">🚫 ${data.hint || 'Поблизости нет торговых терминалов. Посетите торговую зону района.'}</div>`;
            if (data.nearby_establishments && data.nearby_establishments !== '—') {
                offHtml += `<div class="panel-hint">Заведения района: ${data.nearby_establishments}. Откройте вкладку ЛОКАЦИЯ, чтобы войти в торговую точку.</div>`;
            }
            offHtml += `<div class="shop-credits">Баланс: ₡${credits.toLocaleString('ru-RU')}</div>`;
            container.innerHTML = offHtml;
            return;
        }
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
                // Backlog#4 (III): бейдж МЕСТНОГО статуса (не глобальной метки)
                const local = item.local_legality || item.legality || 'legal';
                const badge = local !== 'legal'
                    ? `<span class="shop-legality-badge leg-${local}">${local === 'illegal' ? '🚫 НЕЛЕГАЛЬНО' : '⚠ ОГРАНИЧЕНО'}</span>`
                    : '';
                html += `<div class="shop-item" data-cat="${cat}">
                    <div class="shop-item-info">
                        <div class="shop-item-name rarity-${item.rarity}">${item.name} ${badge}</div>
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
            news.reverse().forEach(n => { html += `<div class="world-news-item">${n.text || n}</div>`; });
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
        if (!a.length && !c.length) { container.innerHTML = '<div class="empty-state">Нет квестов. Доступные контракты — в панели МАГАЗИН → Контракты или через диалоги NPC.</div>'; return; }
        let html = '';
        if (a.length) { html += '<div class="panel-section-title">АКТИВНЫЕ</div>'; a.forEach(q => {
            // Phase 27 D2: stage может быть строкой ИЛИ объектом {label/description/title} —
            // иначе рендерится "[object Object]"
            const stageText = (s) => {
                if (typeof s === 'string') return s;
                if (s && typeof s === 'object') return s.description || s.title || s.label || s.name || '';
                return String(s ?? '');
            };
            const stages = (q.stages || []).map((s, si) => {
                const mark = si < (q.current_stage || 0) ? '✅' : si === (q.current_stage || 0) ? '▶️' : '⬜';
                const lbl = stageText(s);
                const stageLbl = (s && typeof s === 'object' && s.label) ? ` <b>[${s.label}]</b>` : '';
                return `${mark}${stageLbl} ${lbl}`;
            }).filter(t => t.trim().length > 1).join('<br>');
            const rewards = [
                q.reward_credits ? `₡${Number(q.reward_credits).toLocaleString('ru-RU')}` : '',
                q.reward_xp ? `${q.reward_xp} XP` : '',
                ...(q.reward_items || [])
            ].filter(Boolean).join(' · ');
            const qid = (q.contract_id || q.id || '').toString().replace(/'/g, '');
            html += `<div class="quest-item">
                <b>${q.title || '?'}</b>
                ${q.giver ? `<div style="color:var(--text2)">👤 Заказчик: ${q.giver}</div>` : ''}
                <div style="margin-top:4px">${q.description || ''}</div>
                ${stages ? `<div style="margin-top:6px;font-size:0.92em">${stages}</div>` : ''}
                ${rewards ? `<div style="margin-top:6px;color:var(--accent)">🎁 ${rewards}</div>` : ''}
                <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
                    <button class="btn btn-sm" onclick="questContact('${qid}')">📞 Связаться с заказчиком</button>
                    <button class="btn btn-sm btn-danger" onclick="questAbandon('${qid}')">✖ Отказаться</button>
                    ${q.contract_id ? `<button class="btn btn-sm" style="background:#2a5a2a" onclick="ContractsBoard.complete('${qid}')">✅ Сдать контракт</button>` : ''}
                </div>
            </div>`;
        }); }
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

        // D1: панель показывает локацию, не галактику; перелёты — кликом по маршрутам ниже
        html += `<div class="panel-hint">Текущая локация: район, заведения, города планеты. 🚀 Перелёты между мирами — по маршрутам внизу панели.</div>`;

        // Current location
        const loc = data.location || {};
        html += `<div class="panel-section-title">📍 ТЕКУЩЕЕ ПОЛОЖЕНИЕ</div>`;
        html += `<div class="map-location-card">`;
        html += `<div class="map-planet">🌍 ${loc.planet || '?'}</div>`;
        html += `<div class="map-city">🏙 ${loc.city || '?'}</div>`;
        html += `<div class="map-district">📌 ${loc.district || '?'}</div>`;
        if (loc.place) html += `<div class="map-place">🏢 ${loc.place}</div>`;
        html += `</div>`;

        // Phase 27 D7/R5: киберпанк-карточка района (лор-простыня удалена)
        const card = data.district_card || {};
        if (card.name) {
            const secEmoji = card.security_level === 'High' ? '🟢' : card.security_level === 'Med' ? '🟡' : '🔴';
            const secLabel = {High: 'ВЫСОКАЯ', Med: 'СРЕДНЯЯ', Low: 'НИЗКАЯ'}[card.security_level] || '?';
            const pm = card.price_mod || 1.0;
            const pmLabel = pm > 1 ? `+${Math.round((pm - 1) * 100)}%` : pm < 1 ? `-${Math.round((1 - pm) * 100)}%` : 'базовые';
            html += `<div class="panel-section-title">🌆 КАРТОЧКА РАЙОНА</div>`;
            html += `<div class="map-location-card district-card">
                <div class="district-card-header">
                    <span class="district-name">🌆 ${card.name}</span>
                    ${card.type ? `<span class="district-type">${card.type}</span>` : ''}
                </div>
                <div class="district-stat"><span>${secEmoji} Безопасность</span><span class="sec-${card.security_level?.toLowerCase()}">${secLabel}</span></div>
                <div class="district-stat"><span>💰 Модификатор цен</span><span>${pmLabel} (×${pm})</span></div>
                <div class="district-stat"><span>🌦 Атмосфера</span><span>${card.weather || '—'}</span></div>
                ${card.control ? `<div class="district-stat"><span>🚩 Контроль</span><span>${card.control}</span></div>` : ''}
            </div>`;
        }

        // Phase 27 R5: терминальный радар заведений + кнопки входа
        const estabs = data.establishments || [];
        if (estabs.length) {
            html += `<div class="panel-section-title">📡 РАДАР ЗАВЕДЕНИЙ (${estabs.length})</div>`;
            // ASCII-радар: сетка точек, столбцы = заведения
            const gridCols = 3;
            let radar = '';
            for (let r = 0; r < Math.ceil(estabs.length / gridCols); r++) {
                let row = '';
                for (let c = 0; c < gridCols; c++) {
                    const e = estabs[r * gridCols + c];
                    row += e ? '◈──' : '····';
                }
                radar += row + '·\n';
            }
            html += `<pre class="radar-grid">${radar}</pre>`;
            estabs.forEach(e => {
                const services = (e.services || []).join(', ');
                html += `<div class="map-establishment" onclick="visitPlace('${e.name.replace(/'/g, "\'")}')">
                    <div class="map-estab-name">◈ ${e.name}</div>
                    <div class="map-estab-services">${services}</div>
                    <button class="btn-sell" onclick="event.stopPropagation();visitPlace('${e.name.replace(/'/g, "\'")}')">Войти в заведение</button>
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
        // Phase 4: радар района поверх панели (изолированный модуль)
        if (window.DistrictMap) DistrictMap.enhance(container, data);
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

// Phase 28 G4: вход = серверная фиксация места + обновление плашки + реакция окружения
function visitPlace(place) {
    enterPlace(place).then(() => closeSidePanel());
}

// ---- NPC PANEL ----
async function renderNPCPanel(container) {
    container.innerHTML = '<div class="empty-state">Загрузка...</div>';
    try {
       // Phase 27 D3: категории вместо вываливания 168 NPC в кучу
       const [knownData, catalogData] = await Promise.all([
           (await fetch('/api/npcs')).json(),
           (await fetch('/api/npcs/catalog')).json()
       ]);
       const npcs = knownData.npcs || [];          // знакомые (встречи в игре)
       const contacts = catalogData.contacts || []; // авторские NPC, с кем говорили
       const here = catalogData.here || [];         // NPC текущей планеты/города
       const othersCount = catalogData.others_count || 0;

       const npcCard = (npc) => {
           const imp = npc.importance === 'critical' || npc.importance === 'major' ? 'npc-major'
                     : npc.importance === 'notable' ? 'npc-notable' : '';
           const nm = (npc.name || '').replace(/'/g, "\'");
           const loc = (npc.location || '').replace(/'/g, "\'");
           // Phase 27 R6: интерактив — Вызов (только контакты) и Маршрут (если известно место)
           const callBtn = npc.can_call
               ? `<button class="btn-sell" style="background:#2a4a5a" onclick="npcCall('${nm}')">📞 Вызов</button>`
               : '';
           const routeBtn = npc.location
               ? `<button class="btn-sell" onclick="npcRoute('${loc}')">🧭 Маршрут</button>`
               : '';
           const btns = (callBtn || routeBtn)
               ? `<div style="display:flex;gap:4px;margin-top:6px">${callBtn}${routeBtn}</div>` : '';
           return `<div class="npc-card ${imp}">
               <div class="npc-name">${npc.name}${npc.can_call ? ' 💚' : ''}</div>
               <div class="npc-info">${[npc.role, npc.faction].filter(Boolean).join(' | ')}${npc.location ? ' | ' + npc.location : ''}</div>
               ${npc.description ? `<div class="npc-notes">${String(npc.description).slice(0, 160)}</div>` : ''}
               ${btns}
           </div>`;
       };

       let html = `<div class="panel-section-title">🤝 КОНТАКТЫ (${npcs.length + contacts.length})</div>`;
       if (!npcs.length && !contacts.length) {
           html += '<div class="empty-state">Вы ещё ни с кем не говорили</div>';
       } else {
           // Процедурные знакомые (детальные карточки)
           npcs.forEach(npc => {
               const impClass = npc.importance === 'major' ? 'npc-major' : npc.importance === 'notable' ? 'npc-notable' : '';
               const dispEmoji = npc.disposition === 'дружелюбный' ? '💚' : npc.disposition === 'враждебный' ? '❤️‍🔥' : npc.disposition === 'настороженный' ? '💛' : '⚪';
               html += `<div class="npc-card ${impClass}">
                   <div class="npc-name">${dispEmoji} ${npc.name}</div>
                   <div class="npc-info">${[npc.role, npc.faction].filter(Boolean).join(' | ')}</div>
                   <div class="npc-appearance">${(npc.appearance || []).join('; ')}</div>
                   <div class="npc-speech">Речь: ${npc.speech_style} | Встреч: ${npc.met_count}</div>
                   ${npc.notes?.length ? `<div class="npc-notes">${npc.notes.slice(-2).join('; ')}</div>` : ''}
               </div>`;
           });
           // Авторские контакты
           contacts.forEach(npc => { html += npcCard(npc); });
       }

       html += `<div class="panel-section-title">📍 В ЭТОЙ ЛОКАЦИИ (${here.length})</div>`;
       if (!here.length) {
           html += '<div class="empty-state">Заметных персон на этой планете не замечено</div>';
       } else {
           here.forEach(npc => { html += npcCard(npc); });
       }

       if (othersCount > 0) {
           html += `<div class="panel-hint">🌍 Ещё ${othersCount} NPC в остальной системе — они появятся здесь, когда вы прибудете на их планеты.</div>`;
       }
       container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}
// Phase 27 R6: NPC interaction
async function npcCall(name) {
    closeSidePanel();
    sendAction(`Вызываю ${name} по связи`);
}

function npcRoute(location) {
    showToast(`🧭 Маршрут проложен: ${location}`, 'info');
    addNarrativeMessage(`🧭 Навигация указывает: ${location}. Откройте вкладку ЛОКАЦИЯ для перемещения.`, 'system');
    togglePanel('map');
}

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

    // Phase 24c B5-3: Attribute points
    const unspentAttr = c.unspent_attribute_points || 0;
    if (unspentAttr > 0) {
        html += `<div class="panel-section-title">⬆ ОЧКИ АТРИБУТОВ: ${unspentAttr}</div>`;
        html += '<div class="attr-up-grid">Нажмите + рядом с атрибутом для повышения</div>';
    }

    // Perks — load async
    const perks = c.perks || [];
    if (perks.length) {
        html += '<div class="panel-section-title">🏆 ПЕРКИ</div>';
        perks.forEach(p => {
            html += `<div class="perk-item"><b>${p.name}</b>: ${p.description}</div>`;
        });
    }

    // Perk selection button (only show when perk points are unspent)
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
        // Фаза 24c B5-1: показывать доступные перки ТОЛЬКО при unspent_perk_points > 0
        const unspent = data.unspent_perk_points || 0;
        if (unspent <= 0) return;  // не spam-ить на каждом рендере панели
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

// Phase 28 F5: панель прокачки (атрибуты/навыки уже кликабельны в панели персонажа)
function openLevelUpPanel() {
    togglePanel('character');
    showToast('⬆ Распределяйте очки: атрибуты — плюсиком у значения, навыки — в списке ниже', 'info');
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

async function spendAttributePoint(attr) {
    try {
        const resp = await fetch('/api/levelup/spend/attr', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ attr })
        });
        const data = await resp.json();
        if (data.success) {
            addNarrativeMessage(`⬆ Атрибут ${attrLabel(attr)}: ${data.new_value} (осталось очков: ${data.remaining})`, 'system');
            if (gameState?.character) {
                gameState.character.attributes[attr] = data.new_value;
                gameState.character.unspent_attribute_points = data.remaining;
                gameState.character.max_attribute = data.max_attr;
            }
            const content = document.getElementById('side-panel-content');
            renderCharacterPanel(content);
        } else {
            addNarrativeMessage(`⚠ ${data.error}`, 'system');
        }
    } catch { addNarrativeMessage('⚠ Ошибка распределения атрибута', 'system'); }
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
                ${r.personality ? `<div class="recruit-desc" style="color:var(--text2)">Характер: ${r.personality}</div>` : ''}
                ${skills ? `<div class="companion-bonus">⚡ ${skills}</div>` : ''}
                ${r.location ? `<div class="recruit-loc">📍 ${r.location}</div>` : ''}
                ${r.dialogue?.greeting ? `<div class="recruit-quote">"${r.dialogue.greeting}"</div>` : ''}
                ${r.personal_quest ? `<div class="companion-quest">📜 ${r.personal_quest}</div>` : ''}
                ${(r.recruit_condition && (r.recruit_condition.min_level || r.recruit_condition.min_faction_rep)) ? `<div class="recruit-loc">🔒 Требования: ${r.recruit_condition.min_level ? 'уровень ' + r.recruit_condition.min_level : ''}${r.recruit_condition.min_faction_rep ? ', репутация ' + Object.entries(r.recruit_condition.min_faction_rep).map(([f,v]) => f + ' ≥' + v).join(', ') : ''}</div>` : ''}
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
            html += '<div class="panel-section-title">🚀 РЫНОК КОРАБЛЕЙ</div>';
            // Phase 27 R4: компактные карточки + модальный Datasheet по «Осмотреть»
            const catData = await (await fetch('/api/ship/catalog')).json();
            const ships = (catData.ships || []).slice(0, 24);
            if (!ships.length) {
                html += '<div class="empty-state">Каталог кораблей недоступен</div>';
            } else {
                ships.forEach((s, si) => {
                    html += `<div class="ship-class-card ship-compact">
                        <div class="ship-class-name">${s.name}</div>
                        <div class="ship-class-desc">${s.ship_class || ''}${s.range ? ' · ' + s.range : ''}</div>
                        <div class="ship-class-price">₡${(s.price || 0).toLocaleString('ru-RU')}</div>
                        <button class="btn-buy" onclick="showShipDatasheet(${si})">Осмотреть</button>
                    </div>`;
                });
                // Полные данные для модалки держим в замыкании через window
                window._shipCatalog = ships;
                const total = catData.total || ships.length;
                if (total > ships.length) {
                    html += `<div class="panel-hint">Показаны 24 самых доступных из ${total} моделей.</div>`;
                }
            }
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

// Phase 27 D4: покупка конкретной модели из VEHICLES.json
async function buyShipModel(modelName, price) {
    const name = prompt(`Название для корабля «${modelName}»:`, modelName) || modelName;
    const resp = await apiFetch('/api/ship/buy', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ class: modelName, name, model_price: price })
    });
    if (resp.success || resp.ship) {
        showToast(`🚀 Корабль «${name}» куплен!`, 'success');
        addNarrativeMessage(`🚀 Вы приобрели корабль "${name}"!`, 'system');
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
        html += '<div id="property-types-list">Загрузка...</div>';
        setTimeout(() => loadPropertyTypes(), 50);

        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

// B4: каталог типов из API — реальные цены вместо хардкода
async function loadPropertyTypes() {
    const el = document.getElementById('property-types-list');
    if (!el) return;
    try {
        const data = await apiFetch('/api/property/types');
        const myCredits = gameState?.character?.credits ?? 0;
        let html = '';
        (data.types || []).forEach(t => {
            const afford = myCredits >= t.price;
            html += `<div class="ship-class-card ${afford ? '' : 'locked'}">
                <div class="ship-class-name">${t.name}</div>
                <div class="ship-class-desc">${t.features ? t.features.join(', ') : ''}${t.income > 0 ? ` | 💰 ₡${t.income}/цикл` : ''}</div>
                <div class="ship-class-price">₡${t.price.toLocaleString('ru-RU')}</div>
                <button class="btn-buy" onclick="buyProperty('${t.id}')">Купить</button>
                ${afford ? '' : `<div class="hack-req">Не хватает ₡${(t.price - myCredits).toLocaleString('ru-RU')}</div>`}
            </div>`;
        });
        el.innerHTML = html;
    } catch { el.innerHTML = '<div class="empty-state">Ошибка загрузки</div>'; }
}

async function buyProperty(propType) {
    // B4: бездиалоговое имя (prompt = headless-мина, устранена по решению Фазы B4)
    const loc = gameState?.location || gameState?.current_location || {};
    const resp = await apiFetch('/api/property/buy', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: propType, location: loc })
    });
    if (resp.acquired) {
        showToast(`🏠 Приобретено: ${resp.acquired.name}${resp.credits_left !== undefined ? ` (остаток ₡${resp.credits_left.toLocaleString('ru-RU')})` : ''}`, 'success');
        addNarrativeMessage(`🏠 Вы купили ${resp.acquired.name} за ₡${(resp.cost || 0).toLocaleString('ru-RU')}!`, 'system');
        if (gameState?.character && resp.credits !== undefined) gameState.character.credits = resp.credits;
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
            // D4a (H3): узлы приходят снимком из бэка (current/cleared/ice_type/data)
            const isCurrent = !!node.current || i === hack.current_node;
            const isCleared = !!node.cleared;
            html += `<div class="hack-node ${isCurrent ? 'current' : ''} ${isCleared ? 'cleared' : ''}">
                <span class="node-idx">${i + 1}</span>
                <span class="node-ice">${isCleared ? '✅' : node.ice_type || '—'}</span>
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
        // D4a (O1): контекстная подсказка — от чего зависят цели
        html += `<div class="panel-hint">🎯 Цели зависят от района: в криминальных зонах — Чёрная сеть, в корпоративных — серверы и банки данных, у военных объектов — военные системы. Навык Хакинг открывает цели посложнее, но и добыча там жирнее. Тихий обход (+1 ход) безопаснее прямого взлома ICE.</div>`;
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
        updateHackBadge();
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
        updateHackBadge();
        if (resp.loot) {
            // D4a (H1): loot — строка лута; credits_gained уже применены бэком к персонажу
            showToast(`💻 Взлом завершён! Добыча: ${resp.loot}${resp.credits_gained ? ` (+${resp.credits_gained}₡)` : ''}`, 'success', 5000);
        } else if (resp.status === 'detected') {
            showToast('🚨 Обнаружены! Соединение разорвано!', 'error');
        } else {
            showToast('💻 Отключились', 'info');
        }
    } else {
        // D4a (H3): полная синхронизация состояния из бэка (включая снимок узлов)
        engine_hackState = { ...(engine_hackState || {}), ...resp, ...(resp.hack_state || {}) };
        if (resp.hack_state?.nodes) engine_hackState.nodes = resp.hack_state.nodes;
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

            // D4a (O1): контекстная подсказка + лиды из шаблона дела
            html += `<div class="panel-hint">🔎 Улики ищи по лидам ниже — опиши поиск в действии (например, «осматриваю место кражи», «опроси свидетелей»), и ГМ подкинет находку. Надёжные улики (high) повышают точность выводов.</div>`;
            if (Array.isArray(c.leads) && c.leads.length > 0) {
                html += '<div class="case-leads"><span class="leads-title">🔗 ЛИДЫ:</span> ';
                html += c.leads.map(l => `<span class="lead-item">${l}</span>`).join('');
                html += '</div>';
            }

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
    // D4a (I4): канонические типы дел (INVESTIGATION_TEMPLATES) с RU-подписями, select вместо prompt
    const caseTypes = [
        ['murder', 'Убийство'], ['theft', 'Кража'], ['disappearance', 'Исчезновение'],
        ['conspiracy', 'Заговор'], ['sabotage', 'Саботаж'], ['corruption', 'Коррупция'],
        ['smuggling', 'Контрабандная сеть'], ['espionage', 'Шпионаж']
    ];
    const type = await chooseFromList('Тип дела:', caseTypes);
    if (!type) return;
    const name = prompt('Название дела (или оставьте пустым):');
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

// D4a (I4): диалог выбора из списка (fallback на prompt в старых браузерах)
function chooseFromList(title, pairs) {
    return new Promise(resolve => {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:10000;';
        const box = document.createElement('div');
        box.style.cssText = 'background:#1a1a2e;border:1px solid #00ffff44;border-radius:8px;padding:16px;min-width:280px;color:#e0e0e0;font-family:inherit;';
        box.innerHTML = `<div style="margin-bottom:10px;font-weight:bold;">${title}</div>`;
        const list = document.createElement('div');
        pairs.forEach(([val, label]) => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-block';
            btn.style.cssText = 'display:block;width:100%;margin:3px 0;text-align:left;';
            btn.textContent = label;
            btn.onclick = () => { overlay.remove(); resolve(val); };
            list.appendChild(btn);
        });
        const cancel = document.createElement('button');
        cancel.className = 'btn btn-sm btn-block';
        cancel.style.cssText = 'display:block;width:100%;margin:8px 0 0;';
        cancel.textContent = 'Отмена';
        cancel.onclick = () => { overlay.remove(); resolve(null); };
        box.appendChild(list); box.appendChild(cancel);
        overlay.appendChild(box);
        overlay.onclick = e => { if (e.target === overlay) { overlay.remove(); resolve(null); } };
        document.body.appendChild(overlay);
    });
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
        // Фаза 23 D3: каталог — контакты (rep) + силы региона (без rep)
        const planet = (gameState?.location?.planet) || (gameState?.current_location?.planet) || '';
        const data = await apiFetch('/api/factions/catalog' + (planet ? `?planet=${encodeURIComponent(planet)}` : ''));
        const contacts = data.contacts || [];
        const regional = data.regional || [];

        const esc = s => String(s ?? '').replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
        const repColor = rep => rep >= 50 ? '#44ff44' : rep >= 20 ? '#88ff88' : rep >= -20 ? '#aaaaaa' : rep >= -50 ? '#ffaa00' : '#ff4444';
        const repBar = (rep) => {
            const pct = Math.min(100, Math.max(0, 50 + rep / 2));
            const color = repColor(rep);
            const standing = rep >= 50 ? 'Союзник' : rep >= 20 ? 'Дружелюбный' : rep >= -20 ? 'Нейтральный' : rep >= -50 ? 'Подозрительный' : 'Враждебный';
            return `<div class="faction-header">
                    <span class="faction-name">${esc(f_name)}</span>
                    <span class="faction-standing" style="color:${color}">${standing}</span>
                </div>
                <div class="faction-bar">
                    <div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
                    <span class="faction-rep" style="color:${color}">${rep >= 0 ? '+' : ''}${rep}</span>
                </div>`;
        };

        let html = '<div class="panel-section-title">⚖️ ВАШИ КОНТАКТЫ</div>';
        if (contacts.length === 0) {
            html += '<div class="empty-state">Пока нет контактов. Репутация появляется после действий и квестов.</div>';
        }
        contacts.forEach(f => {
            f_name = f.name;
            const rep = f.reputation || 0;
            let card = repBar(rep);
            if (f.full_details) {
                const d = f.full_details;
                const leaders = (d.leaders || []).map(l => `${esc(l.name)} — ${esc(l.role)}`).join('<br>') || '—';
                card += `<details class="faction-details"><summary>Подробнее о фракции</summary>
                    <div class="faction-info"><b>История:</b> ${esc(d.history)}</div>
                    <div class="faction-info"><b>Легенды:</b> ${esc(d.legends)}</div>
                    <div class="faction-info"><b>Лидеры:</b> ${leaders}</div>
                    <div class="faction-info"><b>Союзники:</b> ${esc((d.allies || []).join(', '))} · <b>Враги:</b> ${esc((d.enemies || []).join(', '))}</div>
                    ${(d.mechanics || []).length ? `<div class="faction-info"><b>Что даёт союз:</b><ul>${d.mechanics.map(m => `<li>${esc(m)}</li>`).join('')}</ul></div>` : ''}
                    ${(d.plot_hooks || []).length ? `<div class="faction-info"><b>Слухи и ходы:</b><ul>${d.plot_hooks.map(h => `<li>${esc(h)}</li>`).join('')}</ul></div>
                    <button class="btn-buy" onclick="startHookQuest('${esc(d.hook_owner || '')}')">🔍 Взяться за дело</button>` : ''}
                </details>`;
            }
            html += `<div class="faction-card">${card}</div>`;
        });

        html += `<div class="panel-section-title" style="margin-top:16px">🌍 СИЛЫ РЕГИОНА${data.planet ? ': ' + esc(data.planet) : ''}</div>`;
        if (regional.length === 0) {
            html += '<div class="empty-state">Данных о регионе нет</div>';
        }
        regional.forEach(f => {
            f_name = f.name;
            html += `<div class="faction-card">
                <div class="faction-header">
                    <span class="faction-name">${esc(f.name)}</span>
                    <span class="faction-standing" style="color:#666">${esc(f.type)}</span>
                </div>
                <div class="faction-info">${esc(f.business_area)} · Регион: ${esc(f.influence_region)}</div>
                <div class="faction-norep">нет контакта</div>
            </div>`;
        });

        html += '<div class="panel-section-title" style="margin-top:16px;font-size:0.8em;color:#666">Репутация меняется от ваших действий. Помощь фракции повышает статус, враждебные действия — понижают.</div>';
        container.innerHTML = html;
    } catch { container.innerHTML = '<div class="empty-state">Ошибка</div>'; }
}

// Backlog#3: квест из plot_hook фракции (ручная агентность игрока)
async function startHookQuest(factionName) {
    if (!factionName) { showToast('Неизвестная фракция', 'error'); return; }
    const resp = await apiFetch(`/api/factions/${encodeURIComponent(factionName)}/hook-quest`, {
        method: 'POST', headers: {'Content-Type': 'application/json'}
    });
    if (resp.error) { showToast(resp.error, 'error'); return; }
    showToast(`🔍 Новое дело: ${resp.title}`, 'success', 5000);
    addNarrativeMessage(`🔍 Дело от «${resp.hook_owner}»: ${resp.hook_description || resp.title}`, 'system');
    renderQuestsPanel(document.getElementById('side-panel-content'));
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

// ═══════════════════════════════════════════════════
// Phase 27 R4: MODAL (Datasheet корабля) — универсальное модальное окно
// ═══════════════════════════════════════════════════
function showModal(title, bodyHtml, footerHtml) {
    closeModal();
    const overlay = document.createElement('div');
    overlay.id = 'nexus-modal-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,10,0.78);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(3px)';
    overlay.innerHTML = `
        <div id="nexus-modal" style="background:var(--card,#0d1520);border:1px solid var(--accent,#0ff);border-radius:12px;max-width:520px;width:92%;max-height:80vh;overflow-y:auto;box-shadow:0 0 40px rgba(0,255,255,0.15)">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid var(--border,#123)">
                <b style="color:var(--accent,#0ff);letter-spacing:1px">${title}</b>
                <button onclick="closeModal()" style="background:none;border:none;color:var(--text2,#89a);font-size:20px;cursor:pointer">✕</button>
            </div>
            <div style="padding:14px 18px">${bodyHtml}</div>
            ${footerHtml ? `<div style="padding:12px 18px;border-top:1px solid var(--border,#123);display:flex;gap:8px;justify-content:flex-end">${footerHtml}</div>` : ''}
        </div>`;
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
    document.body.appendChild(overlay);
}

function closeModal() {
    const el = document.getElementById('nexus-modal-overlay');
    if (el) el.remove();
}

// Datasheet корабля: полные ТТХ + покупка
// Phase 31 H4: подписи единиц для ТТХ корабля.
// Скорость «0.08c» — доля скорости света; добавляем человекочитаемую подпись.
function fmtShipSpeed(v) {
    if (v === null || v === undefined || v === '') return '?';
    const s = String(v);
    const m = s.match(/^([\d.]+)\s*c$/i);
    if (m) {
        const frac = parseFloat(m[1]);
        if (!isNaN(frac) && frac > 0) {
            // оценочное время перелёта Земля → Проксима (4.24 св. года) при постоянной скорости
            const years = 4.24 / frac;
            const note = years >= 1 ? `≈${years.toFixed(1)} св. лет от Земли до Проксимы` : 'околосветовая';
            return `${s} c (${frac * 100}% скорости света; до Проксимы ${note})`;
        }
        return `${s} (доля скорости света)`;
    }
    return s;
}
// Трюм: единый стандарт системы корабля — «ед. груза» (внутренние слоты груза, как в cargo/load).
function fmtShipCargo(v) {
    if (v === null || v === undefined || v === '') return '?';
    return `${v} ед. груза`;
}
function showShipDatasheet(index) {
    const s = (window._shipCatalog || [])[index];
    if (!s) { showToast('Данные корабля недоступны', 'error'); return; }
    const row = (k, v) => v ? `<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed var(--border,#123)"><span style="color:var(--text2,#89a)">${k}</span><span>${v}</span></div>` : '';
    const body = `
        <div style="font-size:1.1em;font-weight:700;color:var(--accent,#0ff);margin-bottom:8px">${s.name}</div>
        ${s.note ? `<div style="color:var(--text2,#89a);font-style:italic;font-size:0.88em;margin-bottom:10px">${s.note}</div>` : ''}
        ${row('Класс', s.ship_class)}
        ${row('Двигатель', s.engine)}
        ${row('Дальность прыжка', s.range)}
        ${row('Макс. скорость', fmtShipSpeed(s.max_speed))}
        ${row('Корпус', s.hull)}
        ${row('Броня', s.armor)}
        ${row('Щиты', s.shields)}
        ${row('Трюм', fmtShipCargo(s.cargo_capacity || s.capacity))}
        ${row('Экипаж', s.crew)}
        ${s.features?.length ? `<div style="margin-top:10px"><b>Особенности:</b><ul style="margin:4px 0 0 18px;padding:0">${s.features.map(f => `<li>${f}</li>`).join('')}</ul></div>` : ''}
        <div style="margin-top:12px;font-size:1.15em;color:var(--accent,#0ff)">₡${(s.price || 0).toLocaleString('ru-RU')}</div>`;
    const footer = `
        <button onclick="closeModal()" style="background:var(--border,#123);border:none;color:var(--text,#ccc);padding:8px 16px;border-radius:6px;cursor:pointer">Закрыть</button>
        <button onclick="closeModal(); buyShipModel('${(s.name || '').replace(/'/g, "\'")}', ${s.price || 0})"
                style="background:var(--accent,#0aa);border:none;color:#001;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:700">Купить</button>`;
    showModal('📋 ТТХ КОРАБЛЯ', body, footer);
}
