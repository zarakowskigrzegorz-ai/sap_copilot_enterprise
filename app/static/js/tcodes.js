// =========================================================================
// MODUŁ 5: SPOTLIGHT SEARCH 200+ TRANSAKCJI SAP SD & SPRO (⌘K / Ctrl+K)
// =========================================================================

let currentTcodeCategory = 'ALL';
let tcodeSearchTimeout = null;

function openTcodesSpotlightModal(initialQuery = '') {
    const modal = document.getElementById('modal-tcodes-spotlight');
    if (!modal) return;

    modal.classList.remove('hidden');
    const searchInput = document.getElementById('tcode-search-input');
    if (searchInput) {
        if (initialQuery) {
            searchInput.value = initialQuery;
        }
        setTimeout(() => searchInput.focus(), 80);
    }
    loadTcodes(currentTcodeCategory, searchInput ? searchInput.value.trim() : '');
}

function closeTcodesSpotlightModal() {
    const modal = document.getElementById('modal-tcodes-spotlight');
    if (modal) modal.classList.add('hidden');
}

// Skrót klawiszowy ⌘K / Ctrl+K oraz Escape dla Spotlight T-Codes
document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const modal = document.getElementById('modal-tcodes-spotlight');
        if (modal && !modal.classList.contains('hidden')) {
            closeTcodesSpotlightModal();
        } else {
            openTcodesSpotlightModal();
        }
    } else if (e.key === 'Escape') {
        const modal = document.getElementById('modal-tcodes-spotlight');
        if (modal && !modal.classList.contains('hidden')) {
            closeTcodesSpotlightModal();
        }
    }
});

async function loadTcodes(category = 'ALL', searchQuery = '') {
    try {
        currentTcodeCategory = category;

        const [catRes, tcRes] = await Promise.all([
            fetch(`/api/tcodes/categories?company_id=${currentCompanyId}`),
            fetch(`/api/tcodes?company_id=${currentCompanyId}&category=${encodeURIComponent(category)}&q=${encodeURIComponent(searchQuery)}`)
        ]);

        const catData = await catRes.json();
        const tcData = await tcRes.json();

        renderTcodesCategories(catData.categories || []);
        renderTcodesGrid(tcData.tcodes || [], tcData.total || 0);
    } catch (err) {
        console.error("Błąd ładowania katalogu transakcji T-Codes:", err);
    }
}

function renderTcodesCategories(categories) {
    const bar = document.getElementById('tcodes-category-bar');
    if (!bar) return;

    const totalAll = categories.reduce((acc, c) => acc + (c.count || 0), 0);

    let html = `
        <button type="button" onclick="filterTcodesByCategory('ALL')" class="tcode-cat-pill ${currentTcodeCategory === 'ALL' ? 'active' : ''}">
            🌐 Wszystkie (${totalAll})
        </button>
    `;

    categories.forEach(cat => {
        const isActive = currentTcodeCategory === cat.category;
        const safeCat = (cat.category || '').replace(/'/g, "\\'");
        html += `
            <button type="button" onclick="filterTcodesByCategory('${safeCat}')" class="tcode-cat-pill ${isActive ? 'active' : ''}">
                ${cat.category} (${cat.count})
            </button>
        `;
    });

    bar.innerHTML = html;
}

function filterTcodesByCategory(category) {
    const searchEl = document.getElementById('tcode-search-input');
    const q = searchEl ? searchEl.value.trim() : '';
    loadTcodes(category, q);
}

function handleTcodeSearchInput(val) {
    if (tcodeSearchTimeout) clearTimeout(tcodeSearchTimeout);
    tcodeSearchTimeout = setTimeout(() => {
        loadTcodes(currentTcodeCategory, (val || '').trim());
    }, 180);
}

function renderTcodesGrid(tcodes, totalCount) {
    const grid = document.getElementById('tcodes-grid-container');
    const counterEl = document.getElementById('tcodes-total-counter');
    if (counterEl) counterEl.textContent = `${totalCount} T-Codes`;
    if (!grid) return;

    if (!tcodes || tcodes.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align:center; padding: 36px; color: var(--ios-text-secondary);">
                🔍 Brak transakcji spełniających kryteria wyszukiwania. Możesz dodać własną transakcję Z* poniżej.
            </div>
        `;
        return;
    }

    grid.innerHTML = tcodes.map(t => {
        const isCustom = t.is_custom_z || (t.tcode && (t.tcode.startsWith('Z') || t.tcode.startsWith('Y')));
        const safeTcode = (t.tcode || '').replace(/'/g, "\\'");
        const safeName = (t.name || '').replace(/'/g, "\\'");
        return `
            <div class="tcode-card-item">
                <div>
                    <div class="tcode-card-top">
                        <span class="tcode-code-badge ${isCustom ? 'custom-z' : ''}" onclick="copyText('${safeTcode}')" style="cursor:pointer;" title="Kliknij, aby skopiować kod transakcji">
                            ${t.tcode} ${isCustom ? '★ Z-Custom' : ''}
                        </span>
                        <span class="tcode-cat-tag">${t.category}</span>
                    </div>
                    <h4 class="tcode-title" style="margin-top:6px;">${t.name}</h4>
                    <p class="tcode-desc" style="margin-top:4px;">${t.description}</p>
                </div>

                <div class="tcode-card-footer">
                    <div style="color: var(--ios-text-secondary);">
                        ${t.tables_involved ? `🗄️ Tabele: <code>${t.tables_involved}</code>` : `⚙️ SPRO / SAP GUI`}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <button type="button" onclick="copyText('${safeTcode}')" class="ios-tcode-pill" title="Kopiuj kod T-Code">
                            📋 Kopiuj
                        </button>
                        <button type="button" onclick="askCopilotAboutTcode('${safeTcode}', '${safeName}')" class="ios-btn-primary" style="padding: 4px 10px; font-size: 10.5px;">
                            💬 Zapytaj Copilota
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function askCopilotAboutTcode(tcode, name) {
    closeTcodesSpotlightModal();
    switchTab('chat');
    sendQuickQuery(`Wyjaśnij zastosowanie transakcji SAP ${tcode} (${name}) w module SD, powiązane tabele oraz konfigurację SPRO.`);
}

async function handleCreateCustomTcode(e) {
    e.preventDefault();
    const payload = {
        company_id: currentCompanyId,
        tcode: document.getElementById('custom-tcode-code').value.trim().toUpperCase(),
        name: document.getElementById('custom-tcode-name').value.trim(),
        category: document.getElementById('custom-tcode-cat').value.trim() || 'Custom Z-Transactions',
        description: document.getElementById('custom-tcode-desc').value.trim(),
        tables_involved: document.getElementById('custom-tcode-tables').value.trim().toUpperCase(),
        spro_path: document.getElementById('custom-tcode-spro').value.trim()
    };

    try {
        const res = await fetch('/api/tcodes/custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('custom-tcode-code').value = '';
            document.getElementById('custom-tcode-name').value = '';
            document.getElementById('custom-tcode-desc').value = '';
            document.getElementById('custom-tcode-tables').value = '';
            document.getElementById('custom-tcode-spro').value = '';
            await loadTcodes('ALL', '');
            showToast(`✅ Dodano własną transakcję ${payload.tcode} do katalogu firmy ${currentCompanyId}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd dodawania transakcji'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd połączenia z serwerem");
    }
}

// Eksport globalny dla atrybutów inline HTML
window.openTcodesSpotlightModal = openTcodesSpotlightModal;
window.closeTcodesSpotlightModal = closeTcodesSpotlightModal;
window.loadTcodes = loadTcodes;
window.filterTcodesByCategory = filterTcodesByCategory;
window.handleTcodeSearchInput = handleTcodeSearchInput;
window.askCopilotAboutTcode = askCopilotAboutTcode;
window.handleCreateCustomTcode = handleCreateCustomTcode;
