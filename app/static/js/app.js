// =========================================================================
// MODUŁ 6 (CORE): STAN GLOBALNY, INICJALIZACJA, NAWIGACJA, CZAT & SMART MEMORY
// =========================================================================

let currentCompanyId = 'CLIENT_A';
let currentCompanyProfile = {};
let activeTab = 'chat';
let currentFlowScenario = 'standard';
let inferredProcessesData = null;
let activeRoadmaps = {};

// =========================================================================
// INICJALIZACJA APLIKACJI (DOMContentLoaded)
// =========================================================================
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    initLockScreen();
    await loadCompaniesList();
    await Promise.all([
        loadSdStructures(),
        loadSmartMemory(),
        loadInferredProcesses(),
        typeof loadPricingSimulatorContext === 'function' ? loadPricingSimulatorContext() : Promise.resolve()
    ]);
});

// =========================================================================
// NAWIGACJA MIĘDZY ZAKŁADKAMI (APPLE iOS SEGMENTED CONTROL)
// =========================================================================
function switchTab(tab) {
    activeTab = tab;
    const tabs = ['chat', 'vkoa', 'process'];
    tabs.forEach(t => {
        const view = document.getElementById(`view-${t}`);
        const btn = document.getElementById(`btn-${t}`);
        if (view) {
            if (t === tab) view.classList.remove('hidden');
            else view.classList.add('hidden');
        }
        if (btn) {
            if (t === tab) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });

    if (tab === 'process') {
        loadScenariosList().then(() => {
            loadDocumentFlow(currentFlowScenario);
        });
    } else if (tab === 'vkoa') {
        const pricingSub = document.getElementById('vkoa-subview-pricing');
        if (pricingSub && !pricingSub.classList.contains('hidden')) {
            runPricingSimulation();
        } else {
            const container = document.getElementById('vkoa-results-container');
            if (container && container.innerHTML.includes('vkoa-placeholder')) {
                fillVkoaSample('missing');
            }
        }
    }
}

// =========================================================================
// SMART MEMORY (PAMIĘĆ KONTEKSTOWA AI PER FIRMA)
// =========================================================================
async function loadSmartMemory() {
    try {
        const res = await fetch(`/api/get-memory?company_id=${currentCompanyId}`);
        const data = await res.json();
        const list = document.getElementById('memory-rules-list') || document.getElementById('memory-list');
        const countEl = document.getElementById('memory-count');
        const rules = data.memories || data.rules || [];

        if (countEl) countEl.textContent = rules.length;
        if (!list) return;

        if (rules.length === 0) {
            list.innerHTML = `<p class="text-[11px] text-slate-400 italic py-2 text-center">Brak wyuczonych reguł w tym profilu.</p>`;
            return;
        }

        list.innerHTML = rules.map(r => `
            <div class="bg-amber-50/60 border border-amber-200/80 rounded-lg p-2 text-[11px] relative group">
                <div class="flex items-center justify-between mb-0.5">
                    <span class="font-mono font-bold text-[9px] uppercase bg-amber-200/80 text-amber-900 px-1.5 py-0.5 rounded">${r.category || 'SD'}</span>
                </div>
                <p class="text-slate-500 text-[10px] truncate" title="${r.original_prompt}">Gdy: "${r.original_prompt}"</p>
                <p class="text-slate-800 font-semibold mt-0.5 leading-snug">${r.corrected_output}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error("Błąd ładowania Smart Memory:", err);
    }
}

async function saveMemoryRule(prompt, correction, category = 'GENERAL') {
    try {
        const res = await fetch('/api/save-memory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, correction, category, company_id: currentCompanyId })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`🧠 Zapisano regułę Smart Memory dla profilu ${currentCompanyId}!`);
            loadSmartMemory();
        } else {
            showToast('⚠️ Błąd zapisu reguły: ' + data.message);
        }
    } catch (err) {
        showToast('⚠️ Błąd sieciowy: ' + err.message);
    }
}

function promptCorrection(originalPrompt, currentOutput) {
    const promptText = decodeURIComponent(originalPrompt);
    const defaultOutput = decodeURIComponent(currentOutput || '');
    const userCorrection = window.prompt(
        `Naucz asystenta SD prawidłowej odpowiedzi dla zapytania:\n"${promptText}"\n(Profil: ${currentCompanyId})\n\nWpisz poprawną odpowiedź / regułę:`,
        defaultOutput
    );
    if (userCorrection && userCorrection.trim()) {
        saveMemoryRule(promptText, userCorrection.trim(), 'SD_CUSTOM');
    }
}

// =========================================================================
// CZAT KONSULTANTA SAP SD & KARTY EKSPERTYZ BŁĘDÓW / PROCESÓW
// =========================================================================
function clearChat() {
    const box = document.getElementById('chat-messages');
    if (box) {
        box.innerHTML = `
            <div class="chat-bubble-ai">
                <span class="bubble-title">Rozmowa została wyczyszczona.</span>
                Wpisz kod błędu (np. <strong>VF067</strong>, <strong>V1382</strong>, <strong>VL150</strong>) lub wybierz proces z paska poniżej.
            </div>`;
    }
}

function sendQuickQuery(text) {
    const input = document.getElementById('user-input');
    if (input) {
        input.value = text;
        handleFormSubmit(new Event('submit'));
    }
}

async function handleFormSubmit(event) {
    if (event && event.preventDefault) event.preventDefault();
    const input = document.getElementById('user-input');
    const query = input ? input.value.trim() : '';
    if (!query) return;

    const box = document.getElementById('chat-messages');
    box.innerHTML += `<div class="chat-bubble-user">${query}</div>`;
    input.value = '';
    box.scrollTop = box.scrollHeight;

    const loadingId = 'loading-' + Date.now();
    box.innerHTML += `
        <div id="${loadingId}" class="chat-bubble-ai text-slate-400 font-sans flex items-center gap-2 text-xs">
            <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span>Analiza zapytania w kontekście profilu ${currentCompanyId}...</span>
        </div>`;
    box.scrollTop = box.scrollHeight;

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: query, company_id: currentCompanyId })
        });
        const data = await response.json();

        const loader = document.getElementById(loadingId);
        if (loader) {
            loader.outerHTML = `
                <div class="chat-bubble-ai space-y-2">
                    ${renderChatResponse(data, query)}
                </div>`;
        }
        box.scrollTop = box.scrollHeight;
    } catch (err) {
        const loader = document.getElementById(loadingId);
        if (loader) {
            loader.outerHTML = `
                <div class="chat-bubble-ai border-red-200 text-red-700 dark:text-red-400 text-xs">
                    Błąd komunikacji: ${err.message}
                </div>`;
        }
        box.scrollTop = box.scrollHeight;
    }
}

function triggerRoadmapQuickFix(quickFixType) {
    if (quickFixType === 'vkoa') {
        switchTab('vkoa');
        if (typeof switchVkoaSubview === 'function') {
            switchVkoaSubview('analyzer');
        }
        const rawInput = document.getElementById('vkoa-raw-error');
        if (rawInput) {
            rawInput.value = 'Błąd VF067: Konto przychodów nie zostało ustalone dla konta KOFI';
        }
        runVkoaTroubleshoot(true);
        showToast('⚡ Uruchomiono VKOA Troubleshooter & Quick-Fix!');
    } else {
        showToast('ℹ️ Ten błąd wymaga konfiguracji w SAP GUI zgodnie z krokami w ekspertyzie.');
    }
}

function renderExpertConsultationCard(diag, originalQuery) {
    const cardId = 'consultation-' + Math.random().toString(36).substring(2, 9);
    activeRoadmaps[cardId] = { diag: diag };

    const encodedPrompt = encodeURIComponent(originalQuery || '');
    const encodedContent = encodeURIComponent(diag.markdown_report || '');

    let variantsHtml = '';
    if (diag.solution_variants && diag.solution_variants.length > 0) {
        variantsHtml = diag.solution_variants.map((variant, idx) => {
            let badgeStyle = 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border-blue-200 dark:border-blue-900/40';
            if (idx === 1) {
                badgeStyle = 'bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-900/40';
            } else if (idx >= 2) {
                badgeStyle = 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-900/40';
            }

            const stepsHtml = (variant.steps || []).map(s => `
                <li class="leading-relaxed text-xs text-slate-700 dark:text-slate-300 pl-1">
                    ${s}
                </li>
            `).join('');

            return `
                <div class="p-3.5 rounded-xl border border-slate-200/70 dark:border-white/10 bg-slate-50/50 dark:bg-white/[0.02] space-y-2">
                    <div class="flex items-center gap-2">
                        <span class="text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${badgeStyle}">
                            ${variant.name}
                        </span>
                    </div>
                    ${variant.desc ? `<p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-sans">${variant.desc}</p>` : ''}
                    <ol class="list-decimal list-inside space-y-1.5 pt-0.5">
                        ${stepsHtml}
                    </ol>
                </div>
            `;
        }).join('');
    } else if (diag.roadmap && diag.roadmap.length > 0) {
        const stepsHtml = diag.roadmap.map(st => `
            <li class="leading-relaxed text-xs text-slate-700 dark:text-slate-300 pl-1">
                <strong>${st.title}</strong>${st.tcode ? ` (<code>${st.tcode}</code>)` : ''}: ${st.desc}
            </li>
        `).join('');
        variantsHtml = `
            <div class="p-3.5 rounded-xl border border-slate-200/70 dark:border-white/10 bg-slate-50/50 dark:bg-white/[0.02]">
                <ol class="list-decimal list-inside space-y-2">
                    ${stepsHtml}
                </ol>
            </div>
        `;
    }

    const tcodesBadges = (diag.tcodes || []).map(tc => `
        <button onclick="copyTCode('${tc}')" class="ios-tcode-pill" title="Kopiuj transakcję ${tc} do schowka">
            <span>📋</span> ${tc}
        </button>
    `).join(' ');

    const tablesBadges = (diag.tables || []).map(tb => `
        <span class="font-mono text-[10px] bg-slate-200/60 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-slate-700 dark:text-slate-300 font-semibold">${tb}</span>
    `).join(' ');

    const sproHtml = diag.spro_path && diag.spro_path !== 'N/A' ? `
        <div class="text-[11px] text-slate-600 dark:text-slate-400 font-mono pt-1.5 border-t border-slate-200/40 dark:border-white/5 flex items-center justify-between gap-2">
            <span class="truncate">📂 <strong>SPRO:</strong> ${diag.spro_path}</span>
            <button onclick="copyToClipboard('${diag.spro_path.replace(/'/g, "\\'")}', 'Skopiowano ścieżkę SPRO!')" 
                    class="text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0 font-sans text-xs font-medium">
                Kopiuj SPRO
            </button>
        </div>
    ` : '';

    const pitfallsHtml = (diag.pitfalls_and_secondary && diag.pitfalls_and_secondary.length > 0) ? `
        <div class="p-3 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/30 rounded-xl space-y-1.5 text-xs text-amber-900 dark:text-amber-200">
            <div class="font-bold flex items-center gap-1.5 text-amber-800 dark:text-amber-300">
                <span>⚠️</span> Uwagi Architekta & Błędy Wtórne (Na co uważać):
            </div>
            <ul class="list-disc list-inside space-y-1 text-slate-700 dark:text-slate-300 pl-1">
                ${diag.pitfalls_and_secondary.map(p => `<li class="leading-relaxed">${p}</li>`).join('')}
            </ul>
        </div>
    ` : '';

    const quickFixBtn = diag.quick_fix ? `
        <button onclick="triggerRoadmapQuickFix('${diag.quick_fix_type || 'vkoa'}')" 
                class="py-1.5 px-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-semibold text-xs shadow-xs flex items-center gap-1.5 transition active:scale-95">
            <span>⚡</span> Wykonaj 1-Click Quick-Fix
        </button>
    ` : '';

    return `
        <div class="ios-expert-card space-y-3.5 font-sans">
            <div class="border-b border-slate-200/60 dark:border-white/10 pb-3">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <div class="flex items-center gap-2">
                        <span class="ios-badge ios-badge-error text-xs font-bold font-mono tracking-wide">🚨 ${diag.code}</span>
                        <span class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">${diag.category}</span>
                    </div>
                    <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                        ${diag.company ? `🏢 ${diag.company.name} | ${diag.company.ktopl} / ${diag.company.bukrs}` : ''}
                    </span>
                </div>
                <h3 class="text-sm font-bold text-slate-900 dark:text-white leading-snug">${diag.title}</h3>
            </div>

            ${diag.business_impact ? `
                <div class="p-3 bg-red-50/50 dark:bg-red-950/20 border border-red-200/50 dark:border-red-900/30 rounded-xl space-y-1 text-xs text-slate-800 dark:text-slate-200 leading-relaxed">
                    <div class="font-bold text-red-700 dark:text-red-400 flex items-center gap-1.5 text-xs">
                        <span>🔍</span> Analiza Problemu & Wpływ Biznesowy:
                    </div>
                    <p class="text-slate-700 dark:text-slate-300 pt-0.5">${diag.business_impact}</p>
                </div>
            ` : ''}

            ${diag.technical_mechanism ? `
                <div class="p-3 bg-blue-50/40 dark:bg-blue-950/20 border border-blue-200/50 dark:border-blue-900/30 rounded-xl space-y-1 text-xs text-slate-800 dark:text-slate-200 leading-relaxed">
                    <div class="font-bold text-blue-800 dark:text-blue-300 flex items-center gap-1.5 text-xs">
                        <span>⚙️</span> Mechanizm Techniczny w SAP:
                    </div>
                    <p class="text-slate-700 dark:text-slate-300 pt-0.5">${diag.technical_mechanism}</p>
                </div>
            ` : ''}

            <div class="space-y-2 pt-1">
                <div class="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                    <span class="flex items-center gap-1.5">
                        <span>💡</span> Warianty Rozwiązania (Rekomendacje Senior Architekta):
                    </span>
                </div>
                <div class="space-y-2.5">
                    ${variantsHtml}
                </div>
            </div>

            <div class="p-3 rounded-xl bg-slate-50/70 dark:bg-neutral-900/70 border border-slate-200/60 dark:border-white/10 space-y-2 text-xs">
                <div class="flex flex-wrap items-center gap-2">
                    <span class="font-semibold text-slate-700 dark:text-slate-300">🛠️ Transakcje SAP:</span>
                    <div class="flex flex-wrap gap-1.5">${tcodesBadges}</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                    <span class="font-semibold text-slate-700 dark:text-slate-300">📋 Tabele systemowe:</span>
                    <div class="flex flex-wrap gap-1 font-mono text-[11px] text-slate-600 dark:text-slate-400">${tablesBadges}</div>
                </div>
                ${sproHtml}
            </div>

            ${pitfallsHtml}

            <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/60 dark:border-white/10 text-xs">
                <div class="flex items-center gap-2">
                    <button onclick="copyConsultationReport('${cardId}')" 
                            class="ios-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
                            title="Kopiuj pełną ekspertyzę do schowka">
                        <span>📋</span> Kopiuj pełną ekspertyzę
                    </button>
                    <button onclick="promptCorrection('${encodedPrompt}', '${encodedContent}')" 
                            class="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium text-[11px]">
                        ✍️ Skoryguj regułę (${currentCompanyId})
                    </button>
                </div>
                ${quickFixBtn}
            </div>
        </div>
    `;
}

function copyConsultationReport(cardId) {
    const item = activeRoadmaps[cardId];
    if (!item || !item.diag) return;
    const d = item.diag;
    const text = d.markdown_report || JSON.stringify(d, null, 2);
    copyToClipboard(text, '📋 Skopiowano kompletną ekspertyzę doradczą!');
}

function formatSapMarkdown(rawText) {
    if (!rawText) return '';
    const lines = String(rawText).split('\n');
    let html = '';
    let inList = false;

    const formatInline = (str) => {
        return str
            .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold text-slate-900 dark:text-white">$1</strong>')
            .replace(/`([A-Z0-9_/]{2,15})`/g, `<button type="button" onclick="copyTCode('$1')" class="ios-tcode-pill" style="padding:1px 6px; font-size:10.5px;">$1</button>`)
            .replace(/`([^`]+)`/g, '<code class="font-mono text-[11px] bg-slate-200/70 dark:bg-zinc-800 px-1.5 py-0.5 rounded">$1</code>');
    };

    for (let rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            continue;
        }
        if (line.startsWith('### ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h4 class="text-sm font-bold text-slate-900 dark:text-white mt-2 mb-1">${formatInline(line.slice(4))}</h4>`;
        } else if (line.startsWith('## ')) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h3 class="text-sm font-extrabold text-blue-700 dark:text-blue-400 mt-2 mb-1">${formatInline(line.slice(3))}</h3>`;
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
            if (!inList) {
                html += '<ul class="list-disc list-inside space-y-1 my-1.5 pl-1">';
                inList = true;
            }
            html += `<li class="leading-relaxed">${formatInline(line.slice(2))}</li>`;
        } else if (/^\d+\.\s+/.test(line)) {
            if (!inList) {
                html += '<ul class="list-decimal list-inside space-y-1 my-1.5 pl-1">';
                inList = true;
            }
            html += `<li class="leading-relaxed">${formatInline(line.replace(/^\d+\.\s+/, ''))}</li>`;
        } else {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<p class="leading-relaxed my-1">${formatInline(line)}</p>`;
        }
    }
    if (inList) html += '</ul>';
    return html;
}

function renderChatResponse(data, originalQuery) {
    const encodedPrompt = encodeURIComponent(originalQuery || '');

    if (data.type === 'diagnosis' && data.diagnosis) {
        return renderExpertConsultationCard(data.diagnosis, originalQuery);
    } else if (data.type === 'guide') {
        const formatted = formatSapMarkdown(data.content || '');
        const encodedContent = encodeURIComponent(data.content || '');
        return `
            <div class="space-y-2.5">
                <div class="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans space-y-1">
                    ${formatted}
                </div>
                <div class="flex justify-end pt-1 border-t border-slate-200/50 dark:border-white/10">
                    <button onclick="promptCorrection('${encodedPrompt}', '${encodedContent}')" 
                            class="text-[11px] text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium">
                        ✍️ Naucz reguły / Skoryguj do Smart Memory (${currentCompanyId})
                    </button>
                </div>
            </div>
        `;
    } else {
        const parts = (data.csv_output || '').split(';');
        const [tcode, matnr, maktx, mtart, werks, meins, menge] = parts;
        const badgeClass = (data.status || '').includes('ERROR') ? 'ios-badge-error' : 'ios-badge-success';

        return `
            <div class="space-y-2.5">
                <div class="flex justify-between items-center">
                    <span class="ios-badge ${badgeClass} text-[10px]">STATUS: ${data.status}</span>
                    <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono">${data.notes || ''}</span>
                </div>
                <div class="overflow-x-auto border border-slate-200/80 dark:border-white/10 rounded-xl bg-white dark:bg-black">
                    <table class="w-full text-left border-collapse font-mono text-[11px]">
                        <thead>
                            <tr class="bg-slate-100/70 dark:bg-neutral-900 text-slate-600 dark:text-slate-400 border-b border-slate-200/60 dark:border-white/10">
                                <th class="p-2">T-Code</th>
                                <th class="p-2">Indeks</th>
                                <th class="p-2">Opis</th>
                                <th class="p-2">Zakład</th>
                                <th class="p-2">JM</th>
                                <th class="p-2">Ilość</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="text-blue-700 dark:text-blue-300">
                                <td class="p-2 font-bold">${tcode || ''}</td>
                                <td class="p-2">${matnr || ''}</td>
                                <td class="p-2">${maktx || ''}</td>
                                <td class="p-2">${werks || ''}</td>
                                <td class="p-2">${meins || ''}</td>
                                <td class="p-2 font-bold">${menge || ''}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="flex justify-between items-center pt-1">
                    <button onclick="copyToClipboard('${(data.csv_output || '').replace(/'/g, "\\'")}', '📋 Skopiowano wsad CSV!')" 
                            class="ios-btn-secondary text-xs">
                        📋 Kopiuj wsad CSV
                    </button>
                    <button onclick="promptCorrection('${encodedPrompt}', '${encodeURIComponent(data.csv_output || '')}')" 
                            class="text-[11px] text-blue-600 dark:text-blue-400 hover:underline font-medium">
                        ✍️ Naucz reguły AI
                    </button>
                </div>
            </div>
        `;
    }
}

// =========================================================================
// NARZĘDZIA POMOCNICZE (TOAST & CLIPBOARD)
// =========================================================================
function showToast(message, duration = 2600) {
    const toast = document.getElementById('ios-toast');
    if (!toast) return;
    toast.innerText = message;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

function copyToClipboard(text, msg = '📋 Skopiowano do schowka!') {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(msg);
        }).catch(() => fallbackCopy(text, msg));
    } else {
        fallbackCopy(text, msg);
    }
}

function fallbackCopy(text, msg) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast(msg);
}

function copyText(text) {
    copyToClipboard(text, `📋 Skopiowano: ${text}`);
}

function copyTCode(tcode) {
    copyToClipboard(tcode, `📋 Skopiowano kod transakcji: ${tcode}`);
}

// Eksport globalny dla atrybutów inline HTML
window.switchTab = switchTab;
window.loadSmartMemory = loadSmartMemory;
window.saveMemoryRule = saveMemoryRule;
window.promptCorrection = promptCorrection;
window.clearChat = clearChat;
window.sendQuickQuery = sendQuickQuery;
window.handleFormSubmit = handleFormSubmit;
window.triggerRoadmapQuickFix = triggerRoadmapQuickFix;
window.renderExpertConsultationCard = renderExpertConsultationCard;
window.copyConsultationReport = copyConsultationReport;
window.showToast = showToast;
window.copyToClipboard = copyToClipboard;
window.copyText = copyText;
window.copyTCode = copyTCode;
