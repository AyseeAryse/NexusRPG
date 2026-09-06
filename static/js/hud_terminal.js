/* ═══════════════════════════════════════════════════════════════
   Phase 4: HUD Terminal — CRT toggle, palettes, ASCII helpers
   Изолированный модуль. В app.js — только вызов HudTerminal.init().
   ═══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    const LS_CRT = 'nexus_crt_enabled';
    const LS_PALETTE = 'nexus_palette';

    const PALETTES = [
        { id: 'neon', name: 'Cyber Neon', color: '#00f0ff' },
        { id: 'amber', name: 'Amber', color: '#ffb000' },
        { id: 'green', name: 'Green Phosphor', color: '#33ff66' },
    ];

    function log(msg) { console.log('[HUD] ' + msg); }

    function crtEnabled() {
        return localStorage.getItem(LS_CRT) === '1';
    }

    function applyCrt() {
        const on = crtEnabled();
        document.documentElement.classList.toggle('crt-on', on);
        const btn = document.getElementById('btn-crt-toggle');
        if (btn) {
            btn.classList.toggle('thud-active', on);
            btn.title = on ? 'CRT: ВКЛ (клик — выключить)' : 'CRT: ВЫКЛ (клик — включить)';
        }
        log('CRT ' + (on ? 'ON' : 'OFF'));
    }

    function currentPalette() {
        return localStorage.getItem(LS_PALETTE) || 'neon';
    }

    function applyPalette(id) {
        const root = document.documentElement;
        root.classList.remove('palette-amber', 'palette-green');
        if (id === 'amber') root.classList.add('palette-amber');
        if (id === 'green') root.classList.add('palette-green');
        localStorage.setItem(LS_PALETTE, id);
        document.querySelectorAll('.thud-palette-item').forEach(el =>
            el.classList.toggle('active', el.dataset.palette === id));
        log('Palette: ' + id);
    }

    /* ── ASCII-хелперы (используются другими модулями через window.Ascii) ── */
    const Ascii = {
        /** Двойная рамка ╔═╗ ║ ╚═╝ вокруг строки заголовка */
        box(title, width) {
            const w = width || (title.length + 8);
            const line = '═'.repeat(Math.max(1, w - 2));
            const pad = Math.max(0, w - 4 - title.length);
            const left = ' '.repeat(Math.floor(pad / 2));
            const right = ' '.repeat(Math.ceil(pad / 2));
            return [
                '╔' + line + '╗',
                '║ ' + left + title + right + ' ║',
                '╚' + line + '╝',
            ].join('\n');
        },
        /** Одинарная линия-разделитель */
        divider(width) {
            return '─'.repeat(width || 32);
        },
        /** Индикатор уровня: [██████░░░░] */
        bar(value, max, width) {
            const w = width || 10;
            const filled = Math.round(Math.min(1, value / Math.max(1, max)) * w);
            return '[' + '█'.repeat(filled) + '░'.repeat(w - filled) + ']';
        },
    };

    /* ── Инъекция кнопок в тулбар ── */
    function injectToolbarButtons() {
        const bar = document.querySelector('.topbar-right');
        if (!bar || document.getElementById('btn-crt-toggle')) return;

        // CRT-тумблер
        const crtBtn = document.createElement('button');
        crtBtn.id = 'btn-crt-toggle';
        crtBtn.className = 'topbar-btn';
        crtBtn.title = '📺 Эффекты CRT-монитора: сканлайны, виньетка, свечение (сейчас: ВЫКЛ)';
        crtBtn.textContent = '📺';
        crtBtn.addEventListener('click', () => {
            localStorage.setItem(LS_CRT, crtEnabled() ? '0' : '1');
            applyCrt();
        });

        // Палитра-меню
        const palWrap = document.createElement('div');
        palWrap.style.cssText = 'position:relative;display:inline-block';
        palWrap.innerHTML =
            '<button class="topbar-btn" id="btn-palette" title="🎨 Цветовая палитра терминала: Cyber Neon / Amber / Green Phosphor">🎨</button>' +
            '<div class="thud-palette-menu" id="thud-palette-menu">' +
            PALETTES.map(p =>
                `<div class="thud-palette-item" data-palette="${p.id}">` +
                `<span class="thud-swatch" style="background:${p.color}"></span>${p.name}</div>`
            ).join('') +
            '</div>';
        palWrap.querySelector('#btn-palette').addEventListener('click', (e) => {
            e.stopPropagation();
            document.getElementById('thud-palette-menu').classList.toggle('open');
        });
        palWrap.querySelectorAll('.thud-palette-item').forEach(el => {
            el.addEventListener('click', () => {
                applyPalette(el.dataset.palette);
                document.getElementById('thud-palette-menu').classList.remove('open');
            });
        });
        document.addEventListener('click', () => {
            const menu = document.getElementById('thud-palette-menu');
            if (menu) menu.classList.remove('open');
        });

        // Кубы: подробности/только исход
        const diceBtn = document.createElement('button');
        diceBtn.id = 'btn-dice-details';
        diceBtn.className = 'topbar-btn';
diceBtn.title = '🎲 Детализация бросков кубов: только исход / подробная математика';
        diceBtn.textContent = '🎲';
        diceBtn.addEventListener('click', () => {
            if (typeof toggleDiceDetails === 'function') toggleDiceDetails();
        });

        // Вставляем перед кнопкой меню (☰), чтобы была в конце блока
        const menuBtn = bar.querySelector('button[title="Меню"]');
        bar.insertBefore(diceBtn, menuBtn);
        bar.insertBefore(crtBtn, menuBtn);
        bar.insertBefore(palWrap, menuBtn);
    }

    function init() {
        injectToolbarButtons();
        applyCrt();
        applyPalette(currentPalette());
        window.Ascii = Ascii; // ASCII-хелперы для других модулей
        log('init complete (CRT=' + crtEnabled() + ', palette=' + currentPalette() + ')');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.HudTerminal = { init, applyCrt, applyPalette, crtEnabled, currentPalette };
})();
