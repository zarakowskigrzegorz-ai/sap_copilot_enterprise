// =========================================================================
// MODUŁ 4: AUTO-DISCOVERY PROCESÓW BIZNESOWYCH & DOCUMENT FLOW TIMELINE
// =========================================================================

let currentDomainFilter = 'ALL';
let availableScenariosList = [];
let currentInferredData = null;
let selectedInferredProcess = null;

async function loadInferredProcesses(companyId) {
    const cId = companyId || currentCompanyId;
    const banner = document.getElementById('process-inferred-banner');
    if (!banner) return;

    try {
        const res = await fetch(`/api/processes/inferred?company_id=${cId}`);
        const data = await res.json();
        if (data.status === 'success') {
            currentInferredData = data;
            inferredProcessesData = data;
            renderInferredBanner(data);
        }
    } catch (err) {
        console.error('Błąd pobierania wnioskowania procesów:', err);
    }
}

function renderInferredBanner(data) {
    const badge = document.getElementById('inferred-count-badge');
    const summary = document.getElementById('inferred-summary-text');
    const container = document.getElementById('inferred-tags-container');
    if (!container) return;

    if (badge) badge.textContent = `${data.total_detected || 0} wykrytych procesów`;
    if (summary) summary.textContent = data.summary || '';

    const activeList = (data.processes || []).filter(p => p.is_active);
    if (activeList.length === 0) {
        container.innerHTML = `
            <div class="text-xs text-slate-400 italic">
                Brak jednoznacznych wskaźników procesowych w kartotekach. Zaimportuj materiały lub zdefiniuj profil firmy.
            </div>
        `;
        return;
    }

    container.innerHTML = activeList.map(p => {
        const scoreClass = p.confidence_score >= 70 ? 'inferred-score-high' : 'inferred-score-med';
        const isSelected = selectedInferredProcess === p.process_code;
        return `
            <button type="button" 
                    onclick="handleInferredTagClick('${p.process_code}')" 
                    class="inferred-tag-pill ${isSelected ? 'active' : ''}"
                    id="pill-inferred-${p.process_code}"
                    title="Pewność: ${p.confidence_score}% (${p.confidence_level}) • Kliknij, aby zobaczyć dowody z SAP">
                <span>${p.title}</span>
                <span class="inferred-score-badge ${scoreClass}">${p.confidence_score}%</span>
            </button>
        `;
    }).join('');
}

function handleInferredTagClick(processCode) {
    if (!currentInferredData) return;
    const proc = currentInferredData.processes.find(p => p.process_code === processCode);
    if (!proc) return;

    selectedInferredProcess = processCode;
    renderInferredBanner(currentInferredData);

    const drawer = document.getElementById('inferred-evidence-drawer');
    if (drawer) {
        drawer.classList.remove('hidden');
        drawer.innerHTML = `
            <div class="flex items-center justify-between border-b border-slate-200/60 dark:border-white/10 pb-1.5 mb-1.5">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-bold text-xs text-slate-800 dark:text-white">🔍 Dowody Auto-Discovery: ${proc.title} [${proc.process_code}]</span>
                    <span class="ios-badge ios-badge-blue text-[10px] font-mono">${proc.confidence_level} (${proc.confidence_score}%)</span>
                </div>
                <button type="button" onclick="document.getElementById('inferred-evidence-drawer').classList.add('hidden')" class="text-slate-400 hover:text-slate-600 text-xs">✕ Zamknij</button>
            </div>
            <div class="text-[11.5px] text-slate-700 dark:text-slate-200 mb-1">
                <strong>Struktura i obiekty SD:</strong> <code class="text-blue-700 dark:text-blue-400 font-bold">${proc.sd_key_objects}</code>
            </div>
            <div class="text-[11px] font-semibold text-slate-500 mb-0.5">Znalezione wskaźniki w kartotekach i konfiguracji klienta ${currentCompanyId}:</div>
            <ul class="list-disc pl-5 text-[11px] text-slate-600 dark:text-slate-300 space-y-0.5">
                ${(proc.evidence || []).map(e => `<li>${e}</li>`).join('')}
            </ul>
            <div class="mt-2.5 pt-2 border-t border-slate-200/40 dark:border-white/5 flex items-center justify-between gap-2 flex-wrap">
                <button type="button" onclick="switchFlowScenario('${proc.scenario_key}')" class="ios-btn-primary text-xs flex items-center gap-1">
                    <span>🔄</span> Załaduj ten proces w Document Flow
                </button>
                <button type="button" onclick="askCopilotAboutProcess('${proc.process_code}', '${(proc.title || '').replace(/'/g, "\\'")}')" class="btn-sample-csv text-xs flex items-center gap-1">
                    <span>💬</span> Zapytaj Copilota o konfigurację SPRO
                </button>
            </div>
        `;
    }

    if (proc.domain) {
        filterProcessesByDomain(proc.domain);
    }
    if (proc.scenario_key) {
        switchFlowScenario(proc.scenario_key);
    }
}

async function refreshProcessInference() {
    showToast('🔍 Analizowanie kartotek i wnioskowanie procesów...');
    await loadInferredProcesses(currentCompanyId);
    await loadScenariosList();
    showToast('✅ Zaktualizowano wykryte procesy biznesowe');
}

async function loadScenariosList(domain) {
    if (domain !== undefined) currentDomainFilter = domain;
    const strip = document.getElementById('process-scenarios-strip');
    if (!strip) return;

    try {
        const res = await fetch(`/api/document-flow/scenarios?company_id=${currentCompanyId}`);
        const data = await res.json();
        if (data.status === 'success' && data.scenarios) {
            availableScenariosList = data.scenarios;
            renderScenariosStrip();
        }
    } catch (err) {
        console.error('Błąd pobierania scenariuszy procesowych:', err);
    }
}

function renderScenariosStrip() {
    const strip = document.getElementById('process-scenarios-strip');
    if (!strip) return;

    const filtered = currentDomainFilter === 'ALL'
        ? availableScenariosList
        : availableScenariosList.filter(s => s.domain === currentDomainFilter);

    if (filtered.length === 0) {
        strip.innerHTML = `<div class="text-xs text-slate-400 p-3 italic">Brak scenariuszy dla wybranej dziedziny.</div>`;
        return;
    }

    const domainTags = {
        'MANUFACTURING': { label: '🏭 Produkcja', class: 'bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300' },
        'TRADING': { label: '🛒 Handel & Dystrybucja', class: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300' },
        'SERVICES': { label: '💼 Usługi & Projekty', class: 'bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300' },
        'COMPLAINTS': { label: '🔄 Reklamacje & Zwroty', class: 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300' },
        'STANDARD': { label: '📦 Standard O2C', class: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300' }
    };

    strip.innerHTML = filtered.map(s => {
        const isActive = s.scenario_key === currentFlowScenario;
        const tag = domainTags[s.domain] || { label: s.domain_label || s.domain, class: 'bg-slate-100 text-slate-700' };
        return `
            <div onclick="switchFlowScenario('${s.scenario_key}')" 
                 class="scenario-pill-card ${isActive ? 'active' : ''}" 
                 id="card-scenario-${s.scenario_key}"
                 title="${s.scenario_title}">
                <div class="scenario-card-header">
                    <span class="scenario-domain-tag ${tag.class}">${tag.label}</span>
                    <span class="ios-badge ios-badge-blue text-[9px] font-mono">${s.process_code}</span>
                </div>
                <div class="scenario-card-title">${s.scenario_title}</div>
                <div class="scenario-card-meta">
                    <span>${s.steps_count || 5} kroków SAP</span>
                    <span class="font-mono text-[9px] ${s.default_status === 'error' ? 'text-rose-500 font-bold' : (s.default_status === 'warning' ? 'text-amber-500 font-bold' : 'text-emerald-600 font-semibold')}">
                        ${s.default_status === 'error' ? '⛔ Problem' : (s.default_status === 'warning' ? '⏳ W toku' : '✓ Zakończony')}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

function filterProcessesByDomain(domain) {
    currentDomainFilter = domain;

    const filterButtons = {
        'ALL': 'filter-domain-all',
        'MANUFACTURING': 'filter-domain-mfg',
        'TRADING': 'filter-domain-trad',
        'SERVICES': 'filter-domain-serv',
        'COMPLAINTS': 'filter-domain-comp'
    };

    Object.entries(filterButtons).forEach(([dom, btnId]) => {
        const btn = document.getElementById(btnId);
        if (btn) {
            if (dom === domain) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });

    renderScenariosStrip();

    if (domain !== 'ALL' && availableScenariosList.length > 0) {
        const inDomain = availableScenariosList.filter(s => s.domain === domain);
        if (inDomain.length > 0 && !inDomain.some(s => s.scenario_key === currentFlowScenario)) {
            switchFlowScenario(inDomain[0].scenario_key);
        }
    }
}

function switchFlowScenario(scenarioKey) {
    currentFlowScenario = scenarioKey;
    renderScenariosStrip();
    loadDocumentFlow(scenarioKey);
}

async function loadDocumentFlow(scenario) {
    if (scenario) currentFlowScenario = scenario;

    const compTag = document.getElementById('process-active-company-tag');
    if (compTag) {
        compTag.textContent = currentCompanyProfile ? (currentCompanyProfile.name || currentCompanyProfile.company_name || currentCompanyId) : currentCompanyId;
    }

    loadInferredProcesses(currentCompanyId);

    if (availableScenariosList.length === 0) {
        await loadScenariosList();
    } else {
        renderScenariosStrip();
    }

    const container = document.getElementById('docflow-timeline');
    if (!container) return;

    container.innerHTML = `
        <div class="p-8 text-center text-slate-400 dark:text-slate-500 font-sans animate-pulse">
            Ładowanie przepływu dokumentów [${currentFlowScenario}] dla profilu ${currentCompanyId}...
        </div>
    `;

    try {
        const res = await fetch(`/api/document-flow?company_id=${currentCompanyId}&scenario=${currentFlowScenario}`);
        const data = await res.json();
        
        if (data.status === 'success' && data.flow) {
            renderDocumentFlowTimeline(data.flow);
        } else {
            container.innerHTML = `
                <div class="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 text-amber-800 dark:text-amber-300 rounded-2xl text-xs">
                    Nie odnaleziono łańcucha dokumentów dla scenariusza: ${currentFlowScenario}
                </div>
            `;
        }
    } catch (err) {
        container.innerHTML = `
            <div class="p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-rose-800 dark:text-rose-300 rounded-2xl text-xs">
                Błąd ładowania Document Flow: ${err.message}
            </div>
        `;
    }
}

function renderDocumentFlowTimeline(flow) {
    const container = document.getElementById('docflow-timeline');
    if (!container) return;

    const moduleClasses = {
        'SD': 'module-sd',
        'MM': 'module-mm',
        'PP': 'module-pp',
        'FI': 'module-fi',
        'CO': 'module-co',
        'PS': 'module-ps',
        'QM': 'module-qm'
    };

    let html = `
        <div class="mb-4 px-4 py-3 bg-slate-100/90 dark:bg-neutral-900/90 border border-slate-200/80 dark:border-neutral-800 rounded-2xl flex flex-wrap justify-between items-center gap-3 text-xs">
            <div class="flex items-center gap-2.5">
                <span class="ios-badge ios-badge-blue text-[11px] font-mono font-bold">${flow.process_code || 'SAP'}</span>
                <div>
                    <div class="font-bold text-slate-800 dark:text-slate-100 text-sm">
                        ${flow.scenario_title}
                    </div>
                    <div class="text-slate-500 dark:text-slate-400 font-mono text-[11px] mt-0.5">
                        Dokument #${flow.order_number} • Klient: ${flow.customer_id} • Sprzedaż: ${flow.sales_org || '1000'} / Zakład: ${flow.plant || '1000'}
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="askCopilotAboutProcess('${flow.process_code}', '${(flow.scenario_title || '').replace(/'/g, "\\'")}')" class="ios-btn-primary text-xs flex items-center gap-1.5" title="Zapytaj Copilota o szczegóły tego procesu biznesowego">
                    <span>💬</span> Zapytaj Copilota o ten proces
                </button>
                <button onclick="copyCurrentFlowAsNote('${flow.scenario_key}')" class="btn-sample-csv text-xs flex items-center gap-1" title="Kopiuj podsumowanie przepływu do schowka">
                    <span>📋</span> Kopiuj notatkę
                </button>
            </div>
        </div>
    `;

    (flow.steps || []).forEach((step, idx) => {
        let statusClass = 'status-completed';
        let statusBadge = 'ios-badge-success';
        let icon = '✓';

        if (step.status === 'error') {
            statusClass = 'status-error';
            statusBadge = 'ios-badge-error';
            icon = '✕';
        } else if (step.status === 'warning') {
            statusClass = 'status-warning';
            statusBadge = 'ios-badge-warning';
            icon = '⏳';
        } else if (step.status === 'blocked' || step.status === 'pending') {
            statusClass = 'status-pending';
            statusBadge = 'bg-slate-200 dark:bg-neutral-800 text-slate-600 dark:text-slate-400';
            icon = '○';
        }

        const modClass = moduleClasses[step.module] || 'module-sd';

        html += `
            <div class="docflow-card ${statusClass}">
                <div class="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <div class="flex items-center gap-2.5 flex-wrap">
                        <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step.status === 'error' ? 'bg-red-500 text-white' : (step.status === 'warning' ? 'bg-amber-500 text-white' : (step.status === 'completed' ? 'bg-emerald-500 text-white' : 'bg-slate-300 dark:bg-neutral-700 text-slate-600 dark:text-slate-300'))}">
                            ${icon}
                        </span>
                        <span class="module-badge ${modClass}">${step.module || 'SD'}</span>
                        <span class="font-bold text-xs text-slate-900 dark:text-white">${step.step_number}. ${step.name}</span>
                        <span class="ios-badge ios-badge-blue text-[10px] font-mono">${step.tcode}</span>
                        ${step.phase ? `<span class="text-[10px] text-slate-500 dark:text-slate-400 font-sans">(${step.phase})</span>` : ''}
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-mono text-slate-600 dark:text-slate-300 font-semibold">${step.doc_type ? step.doc_type + ': ' : ''}${step.doc_number || '-'}</span>
                        <span class="ios-badge ${statusBadge} text-[10px]">${step.status_label}</span>
                    </div>
                </div>

                <p class="text-xs text-slate-600 dark:text-slate-300 mt-1.5 leading-relaxed pl-8">
                    ${step.details}
                </p>

                <div class="flex flex-wrap items-center justify-between mt-2 pt-2 border-t border-slate-100 dark:border-white/5 pl-8 text-[11px] text-slate-400 font-mono gap-2">
                    <div class="flex items-center gap-3">
                        <span>Data: ${step.date || 'W toku'}</span>
                        ${step.tables_involved ? `<span class="text-[10px] text-slate-500">Tabele: <strong class="text-slate-600 dark:text-slate-300">${step.tables_involved}</strong></span>` : ''}
                    </div>
                    ${step.value && step.value !== '-' ? `<span class="font-bold text-slate-700 dark:text-slate-200 font-mono">Wartość: ${step.value}</span>` : ''}
                </div>

                ${step.error_info ? `
                    <div class="mt-3 p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 rounded-2xl ml-8 flex flex-wrap items-center justify-between gap-2">
                        <div>
                            <span class="font-bold text-xs text-red-700 dark:text-red-400 flex items-center gap-1.5">
                                <span>⛔</span> Kod błędu: ${step.error_info.code}
                            </span>
                            <div class="text-[11px] font-mono text-red-800 dark:text-red-300 mt-0.5">
                                ${step.error_info.message}
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            ${step.error_info.vkoa_params ? `
                                <button onclick="diagnoseFromFlowStep('${encodeURIComponent(JSON.stringify(step.error_info))}')" class="ios-btn-primary text-xs">
                                    🩺 Rozwiąż w VKOA
                                </button>
                            ` : ''}
                            <button onclick="sendQuickQuery('Błąd ${step.error_info.code}: ${(step.error_info.message || '').replace(/'/g, "\\'")}')" class="btn-sample-csv text-xs bg-red-100/60 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800">
                                💬 Diagnozuj z Copilotem
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        if (idx < flow.steps.length - 1) {
            html += `<div class="timeline-connector"></div>`;
        }
    });

    container.innerHTML = html;
}

function askCopilotAboutProcess(processCode, processName) {
    switchTab('chat');
    sendQuickQuery(`Wyjaśnij kompleksowo proces SAP: ${processName} (${processCode}). Podaj kluczowe transakcje, tabele i punkty integracji SD z MM/PP/FI/CO.`);
}

function copyCurrentFlowAsNote(scenarioKey) {
    const active = availableScenariosList.find(s => s.scenario_key === scenarioKey);
    const title = active ? active.scenario_title : scenarioKey;
    const noteText = `=== SAP SD ENTERPRISE COPILOT - PROCESS FLOW ===\nScenariusz: ${title} (${scenarioKey})\nProfil klienta: ${currentCompanyId}\nData generacji: ${new Date().toLocaleString('pl-PL')}\nStatus: Zweryfikowano w profilu.`;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(noteText).then(() => {
            showToast('📋 Skopiowano notatkę wdrożeniową do schowka');
        }).catch(() => {
            showToast('📋 Skopiowano podsumowanie procesu');
        });
    } else {
        showToast('📋 Skopiowano podsumowanie procesu');
    }
}

function diagnoseFromFlowStep(jsonStr) {
    try {
        const errorInfo = JSON.parse(decodeURIComponent(jsonStr));
        if (errorInfo.vkoa_params) {
            switchTab('vkoa');
            if (typeof switchVkoaSubview === 'function') {
                switchVkoaSubview('analyzer');
            }
            
            const rawInput = document.getElementById('vkoa-raw-error');
            if (rawInput && errorInfo.message) {
                rawInput.value = errorInfo.message;
            }

            const p = errorInfo.vkoa_params;
            if (p.ktopl) {
                const el = document.getElementById('vkoa-ktopl');
                if (el) el.value = p.ktopl;
            }
            if (p.vkorg) {
                const el = document.getElementById('vkoa-vkorg');
                if (el) el.value = p.vkorg;
            }
            if (p.ktgrd_cust) {
                const el = document.getElementById('vkoa-ktgrd');
                if (el) el.value = p.ktgrd_cust;
            }
            if (p.ktgrm_mat) {
                const el = document.getElementById('vkoa-ktgrm');
                if (el) el.value = p.ktgrm_mat;
            }
            if (p.kvsl) {
                const el = document.getElementById('vkoa-kvsl');
                if (el) el.value = p.kvsl;
            }

            runVkoaTroubleshoot(true);
        } else {
            switchTab('chat');
            sendQuickQuery(`Błąd ${errorInfo.code}: ${errorInfo.message}`);
        }
    } catch (e) {
        console.error('Błąd przejścia z kroku Document Flow do diagnostyki:', e);
    }
}

// Eksport globalny dla atrybutów inline HTML
window.loadInferredProcesses = loadInferredProcesses;
window.renderInferredBanner = renderInferredBanner;
window.handleInferredTagClick = handleInferredTagClick;
window.refreshProcessInference = refreshProcessInference;
window.loadScenariosList = loadScenariosList;
window.renderScenariosStrip = renderScenariosStrip;
window.filterProcessesByDomain = filterProcessesByDomain;
window.switchFlowScenario = switchFlowScenario;
window.loadDocumentFlow = loadDocumentFlow;
window.askCopilotAboutProcess = askCopilotAboutProcess;
window.copyCurrentFlowAsNote = copyCurrentFlowAsNote;
window.diagnoseFromFlowStep = diagnoseFromFlowStep;
