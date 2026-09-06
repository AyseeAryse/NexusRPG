/* ═══════════════════════════════════════════════════════════════
   Phase 4: District Map — интерактивный радар района
   SVG-радар с секторами заведений, статусом безопасности и
   фракционным контролем. Клик по сектору → visitPlace().
   Изолированный модуль; в app.js — только вызов из renderMapPanel.
   ═══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    function log(msg) { console.log('[DistrictMap] ' + msg); }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/'/g, '&#39;').replace(/"/g, '&quot;');
    }

    const SEC_COLORS = { High: '#33ff66', Med: '#ffd700', Low: '#ff3355' };
    const SEC_RU = { High: 'ВЫСОКАЯ', Med: 'СРЕДНЯЯ', Low: 'НИЗКАЯ' };

    /**
     * SVG-радар: заведения размещаются по кругу вокруг центра (позиции игрока).
     * angle = i * 2π/n; radius чередуется для разных колец.
     */
    function buildRadarSvg(establishments, secLevel) {
        const size = 300;
        const cx = size / 2, cy = size / 2;
        const secColor = SEC_COLORS[secLevel] || SEC_COLORS.Med;
        const n = establishments.length;
        const R = 118;

        // Кольца радара
        let rings = '';
        [0.33, 0.66, 1.0].forEach(f => {
            rings += `<circle cx="${cx}" cy="${cy}" r="${R * f}" fill="none" ` +
                     `stroke="var(--border)" stroke-width="1" stroke-dasharray="3 4" opacity="0.6"/>`;
        });
        // Перекрестие
        rings += `<line x1="${cx - R - 8}" y1="${cy}" x2="${cx + R + 8}" y2="${cy}" stroke="var(--border)" stroke-width="1" opacity="0.5"/>`;
        rings += `<line x1="${cx}" y1="${cy - R - 8}" x2="${cx}" y2="${cy + R + 8}" stroke="var(--border)" stroke-width="1" opacity="0.5"/>`;

        // Игрок в центре
        const player = `<circle cx="${cx}" cy="${cy}" r="5" fill="var(--accent, #00f0ff)"/>` +
            `<circle cx="${cx}" cy="${cy}" r="9" fill="none" stroke="var(--accent, #00f0ff)" stroke-width="1" opacity="0.5"/>` +
            `<text x="${cx}" y="${cy + 22}" text-anchor="middle" font-size="9" fill="var(--text2)" font-family="monospace">ВЫ</text>`;

        // Сектора-заведения
        let nodes = '';
        establishments.forEach((est, i) => {
            const angle = (i * 2 * Math.PI / Math.max(1, n)) - Math.PI / 2;
            const radius = R * (0.55 + 0.45 * ((i % 2) ? 1 : 0.72));
            const x = cx + radius * Math.cos(angle);
            const y = cy + radius * Math.sin(angle);
            const name = esc(est.name || '?');
            const short = name.length > 18 ? name.slice(0, 17) + '…' : name;
            // Сектор: линия от центра + узел
            nodes += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="var(--border)" stroke-width="1" opacity="0.35"/>`;
            nodes += `<g class="dm-node" data-place="${esc(est.name)}" style="cursor:pointer">`;
            nodes += `<title>${name}${(est.services || []).length ? '\n' + esc((est.services || []).join(', ')) : ''}</title>`;
            nodes += `<circle cx="${x}" y="${y}" r="14" fill="transparent" stroke="none"/>`;
            nodes += `<circle cx="${x}" y="${y}" r="6" fill="var(--bg3)" stroke="${secColor}" stroke-width="1.5"/>`;
            // Метка — чуть дальше узла, кнаружи (text не перехватывает клики)
            const lx = cx + (radius + 22) * Math.cos(angle);
            const ly = cy + (radius + 22) * Math.sin(angle);
            const anchor = Math.cos(angle) > 0.3 ? 'start' : Math.cos(angle) < -0.3 ? 'end' : 'middle';
            nodes += `<text x="${lx}" y="${ly}" text-anchor="${anchor}" font-size="9.5" pointer-events="none" ` +
                     `fill="var(--text)" font-family="monospace" style="paint-order:stroke;stroke:var(--bg);stroke-width:3px">${short}</text>`;
            nodes += `</g>`;
        });

        return `<svg viewBox="0 0 ${size} ${size + 14}" width="100%" style="max-width:340px;display:block;margin:0 auto">
            ${rings}${player}${nodes}
            <text x="${cx}" y="${size - 2}" text-anchor="middle" font-size="8.5" fill="var(--text2)" font-family="monospace">
                СЕКТОРОВ: ${n} // КЛИК = ВХОД
            </text>
        </svg>`;
    }

    /** Рендер радара + статус-панели в переданный html-фрагмент контейнера.
      * Вызывается из app.js renderMapPanel после построения базового html. */
    // Phase 28 F3: процедурные сектора-фоллбэк, чтобы радар никогда не был пустым
    const FALLBACK_SECTORS = [
        { name: 'Терминал связи', type: 'utility', services: ['связь', 'информация'] },
        { name: 'Служебный отсек', type: 'utility', services: ['ремонт', 'хранение'] },
        { name: 'Пункт отдыха экипажа', type: 'residential', services: ['ночлег', 'еда'] },
    ];

    function enhance(container, data) {
        const card = data.district_card || {};
        let estabs = data.establishments || [];
        let usedFallback = false;
        if (!estabs.length) {
            // Детерминированный выбор 2-3 секторов по хэшу локации (стабильно между визитами)
            const seedStr = `${card.name || ''}|${(data.location || {}).city || ''}`;
            let h = 0;
            for (let i = 0; i < seedStr.length; i++) h = (h * 31 + seedStr.charCodeAt(i)) >>> 0;
            const count = 2 + (h % 2); // 2 или 3
            estabs = FALLBACK_SECTORS.slice(h % 2, h % 2 + count);
            usedFallback = true;
        }
        const secLevel = card.security_level || 'Med';

        // Статусная ASCII-панель
        const A = window.Ascii || { bar: () => '', divider: () => '' };
        const control = card.control || 'нет данных';
        const pm = card.price_mod || 1.0;
        const secHex = SEC_COLORS[secLevel] || '#ffd700';
        const statusText =
            `БЕЗОПАСНОСТЬ ${A.bar({ High: 3, Med: 2, Low: 1 }[secLevel] || 2, 3)} ${SEC_RU[secLevel] || secLevel}\n` +
            `ЦЕНЫ         ×${pm.toFixed(2)}\n` +
            `КОНТРОЛЬ     ${String(control).slice(0, 34)}`;
        const fbMark = usedFallback ? '\nРЕЖИМ       процедурные сектора' : '';
        const statusBar = `<pre class="thud-statusbar" style="border-color:${secHex}55">${statusText}${fbMark}</pre>`;

        // Радар
        const radar = buildRadarSvg(estabs, secLevel);

        // Вставляем: заменяем старый ASCII-пре-радар (если есть) и список карточек
        const oldPre = container.querySelector('.radar-grid');
        if (oldPre) oldPre.remove();
        // Старый список карточек заведений остаётся снизу (полная информация), радар — сверху
        const anchor = container.querySelector('.panel-section-title');
        const wrap = document.createElement('div');
        wrap.innerHTML = statusBar + radar;
        if (anchor && anchor.parentNode) {
            // После первой секции (текущее положение) — перед карточкой района
            anchor.parentNode.insertBefore(wrap, anchor.nextSibling);
        } else {
            container.prepend(wrap);
        }

        // Обработчики: клик по узлу = visitPlace
        container.querySelectorAll('.dm-node').forEach(node => {
            node.addEventListener('click', () => {
                const place = node.dataset.place;
                if (place && typeof window.visitPlace === 'function') {
                    log('вход: ' + place);
                    window.visitPlace(place);
                }
            });
        });
        log('enhanced: ' + estabs.length + ' секторов, sec=' + secLevel);
    }

    window.DistrictMap = { enhance };
})();
