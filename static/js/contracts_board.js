/* ═══════════════════════════════════════════════════════════════
   Phase 4: Contracts Board — доска процедурных контрактов
   Изолированный модуль. Требует: app.js (showToast, gameState,
   sendAction, updateGameUI), hud_terminal.js (window.Ascii).
   В app.js — только вызов ContractsBoard.render(container).
   ═══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    let cachedContracts = [];

    function log(msg) { console.log('[ContractsBoard] ' + msg); }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/'/g, '&#39;').replace(/"/g, '&quot;');
    }

    /** Карточка одного контракта с Dual-Path визуализацией */
    function contractCard(c, index) {
        const title = esc(c.title || 'Без названия');
        const giver = esc(c.giver || '—');
        const credits = Number(c.reward_credits || 0).toLocaleString('ru-RU');
        const xp = Number(c.reward_xp || 0);
        const desc = esc(String(c.description || '').slice(0, 140));

        // Dual-Path: пути решения (силовой / технический / социальный)
        let pathsHtml = '';
        const paths = Array.isArray(c.paths) ? c.paths : [];
        if (paths.length) {
            const pathIcons = ['⚔️', '🤝', '💻', '🎲'];
            const pathRows = paths.map((p, pi) => {
                // description может быть строкой ИЛИ массивом строк (бэкенд отдаёт оба вида)
                const lines = Array.isArray(p.description) ? p.description : [p.description];
                const first = esc(String(lines[0] || p.label || '').replace(/^[\w\s]+:\s*/, ''));
                return `<div class="cb-path">
                    <span class="cb-path-icon">${pathIcons[pi % pathIcons.length]}</span>
                    <span class="cb-path-text">${first}</span>
                </div>`;
            }).join('');
            pathsHtml = `<div class="cb-paths" data-count="${paths.length}">
                <div class="cb-paths-title">DUAL-PATH // ${paths.length} ПУТИ</div>
                ${pathRows}
            </div>`;
        }

        // Требования
        let reqHtml = '';
        const req = c.requirements || {};
        const reqBits = [];
        if (req.min_reputation) reqBits.push('репутация ≥ ' + req.min_reputation);
        (req.skills || []).forEach(s => reqBits.push(esc(typeof s === 'string' ? s : (s.name || ''))));
        if (reqBits.length) reqHtml = `<div class="cb-reqs">ТРЕБОВАНИЯ: ${reqBits.join(' · ')}</div>`;

        return `<div class="cb-contract thud-frame" data-title="КОНТРАКТ #${index + 1}" data-id="${esc(c.id)}">
            <div class="cb-title">${title}</div>
            <div class="cb-giver">👤 ${giver}</div>
            <div class="cb-desc">${desc}</div>
            ${pathsHtml}
            ${reqHtml}
            <div class="cb-footer">
                <span class="cb-rewards">₡${credits} · ${xp} XP</span>
                <button class="btn-buy cb-accept" onclick="ContractsBoard.accept('${esc(c.id)}')">ВЗЯТЬ КОНТРАКТ</button>
            </div>
        </div>`;
    }

    /** Рендер доски в контейнер side-panel */
    async function render(container) {
        container.innerHTML = '<div class="empty-state">Загрузка доски контрактов...</div>';
        try {
            const resp = await fetch('/api/contracts/available');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();
            cachedContracts = data.contracts || [];

            const A = window.Ascii || { box: (t) => t };
            let html = `<pre class="cb-ascii-header">${A.box('ДОСКА КОНТРАКТОВ', 34)}</pre>`;
            html += `<div class="thud-statusbar">ДОСТУПНО: ${data.count || cachedContracts.length}` +
                ` // ТИР: ${data.tier ?? '—'} // ЛОКАЦИЯ: ${esc((data.location || {}).district || '—')}</div>`;

            if (!cachedContracts.length) {
                html += '<div class="empty-state">Доска пуста. Контракты появляются по мере развития мира.</div>';
            } else {
                cachedContracts.forEach((c, i) => { html += contractCard(c, i); });
            }
            container.innerHTML = html;
            log('rendered ' + cachedContracts.length + ' contracts');
        } catch (e) {
            container.innerHTML = '<div class="empty-state">Доска контрактов недоступна: ' + esc(e.message) + '</div>';
            log('render error: ' + e.message);
        }
    }

    /** Взять контракт → POST /api/contracts/accept */
    async function accept(contractId) {
        if (!contractId) return;
        try {
            const resp = await fetch('/api/contracts/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contract_id: contractId }),
            });
            const data = await resp.json();
            if (data.success && data.quest) {
                if (typeof showToast === 'function') {
                    showToast(`📋 Контракт принят: ${data.quest.title || contractId}`, 'success');
                }
                // Обновить глобальное состояние (счётчик активных квестов в HUD)
                if (data.game_state && typeof updateGameUI === 'function') {
                    window.gameState = data.game_state;
                    updateGameUI(data.game_state);
                }
                // Перерисовать доску (контракт исчез из доступных)
                const content = document.getElementById('side-panel-content');
                if (document.getElementById('side-panel')?.dataset.current === 'contracts') {
                    render(content);
                }
                log('accepted ' + contractId);
            } else {
                const msg = data.error || 'Не удалось взять контракт';
                if (typeof showToast === 'function') showToast(msg, 'error');
                log('accept failed: ' + msg);
            }
        } catch (e) {
            if (typeof showToast === 'function') showToast('Ошибка сети: ' + e.message, 'error');
            log('accept error: ' + e.message);
        }
    }

    /** Сдать контракт → POST /api/contracts/complete + анимация награды */
    async function complete(contractId) {
        if (!contractId) return;
        try {
            const resp = await fetch('/api/contracts/complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contract_id: contractId }),
            });
            const data = await resp.json();
            if (data.success) {
                const cr = Number(data.reward_credits || 0).toLocaleString('ru-RU');
                const xp = Number(data.reward_xp || 0);
                if (typeof showToast === 'function') {
                    showToast(`✅ Контракт сдан! +₡${cr} · +${xp} XP`, 'success');
                }
                // Анимация начисления в истории — одна строка, без спама
                if (typeof addNarrativeMessage === 'function') {
                    addNarrativeMessage(
                        `<span class="thud-reward-flash">✅ КОНТРАКТ ЗАВЕРШЁН · +₡${cr} · +${xp} XP</span>`,
                        'system');
                }
                if (data.game_state && typeof updateGameUI === 'function') {
                    window.gameState = data.game_state;
                    updateGameUI(data.game_state);
                }
                // Обновить панель квестов, если открыта
                const panel = document.getElementById('side-panel')?.dataset.current;
                const content = document.getElementById('side-panel-content');
                if (panel === 'quests' && typeof renderQuestsPanel === 'function') {
                    renderQuestsPanel(content);
                }
                log('completed ' + contractId);
            } else {
                const msg = data.error || 'Не удалось сдать контракт';
                if (typeof showToast === 'function') showToast(msg, 'error');
                log('complete failed: ' + msg);
            }
        } catch (e) {
            if (typeof showToast === 'function') showToast('Ошибка сети: ' + e.message, 'error');
            log('complete error: ' + e.message);
        }
    }

    window.ContractsBoard = { render, accept, complete };
})();
