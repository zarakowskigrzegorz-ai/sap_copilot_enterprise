// =========================================================================
// MODUŁ 2: MULTI-COMPANY WORKSPACE, MASTER DATA GOVERNANCE (MDG) & AUTO-FIX
// =========================================================================

let currentPstyvFilter = '';
let ordersTableLoaded = false;

async function loadCompaniesList() {
    try {
        const res = await fetch('/api/companies');
        const data = await res.json();
        currentCompanyId = data.active_id || 'CLIENT_A';
        currentCompanyProfile = data.active_profile || {};

        const populateSelect = (selectEl) => {
            if (!selectEl) return;
            selectEl.innerHTML = '';
            (data.companies || []).forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = `${c.name} (${c.id})`;
                if (c.id === currentCompanyId) opt.selected = true;
                selectEl.appendChild(opt);
            });
        };

        populateSelect(document.getElementById('company-select'));
        populateSelect(document.getElementById('header-company-select'));
        populateSelect(document.getElementById('lock-company-select'));

        updateCompanyUI(currentCompanyProfile);
    } catch (err) {
        console.error("Błąd ładowania profili firm:", err);
    }
}

function updateCompanyUI(profile) {
    if (!profile) return;

    const ktoplEl = document.getElementById('badge-ktopl');
    const bukrsEl = document.getElementById('badge-bukrs');
    const waersEl = document.getElementById('badge-waers');
    if (ktoplEl) ktoplEl.textContent = profile.ktopl || 'INT';
    if (bukrsEl) bukrsEl.textContent = profile.bukrs || '1000';
    if (waersEl) waersEl.textContent = profile.waers || 'EUR';

    const headerCompanyEl = document.getElementById('header-company-name');
    if (headerCompanyEl) {
        headerCompanyEl.textContent = `${profile.name || profile.id} (${profile.bukrs || '1000'} | ${profile.waers || 'EUR'})`;
    }

    const headerSelect = document.getElementById('header-company-select');
    if (headerSelect && profile.id) {
        headerSelect.value = profile.id;
    }

    const lockSelect = document.getElementById('lock-company-select');
    if (lockSelect && profile.id) {
        lockSelect.value = profile.id;
    }

    const indicator = document.getElementById('chat-client-indicator');
    if (indicator) {
        indicator.textContent = `Profil aktywny: ${profile.name} (Plan kont: ${profile.ktopl} | Jednostka: ${profile.bukrs} | Waluta: ${profile.waers})`;
    }

    const vkoaKtopl = document.getElementById('vkoa-ktopl');
    const vkoaVkorg = document.getElementById('vkoa-vkorg');
    if (vkoaKtopl) vkoaKtopl.value = profile.ktopl || 'INT';
    if (vkoaVkorg) vkoaVkorg.value = profile.id === 'CLIENT_B' ? '2000' : '1000';
}

async function handleCompanyChange(companyId) {
    try {
        const res = await fetch('/api/companies/active', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: companyId })
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentCompanyId = data.active_id;
            currentCompanyProfile = data.active_profile;
            ordersTableLoaded = false;

            updateCompanyUI(currentCompanyProfile);
            await Promise.all([
                loadSdStructures(),
                loadSmartMemory(),
                loadInferredProcesses(),
                typeof loadPricingSimulatorContext === 'function' ? loadPricingSimulatorContext() : Promise.resolve()
            ]);

            if (activeTab === 'process') {
                loadDocumentFlow(currentFlowScenario);
            } else if (activeTab === 'vkoa') {
                const pricingSub = document.getElementById('vkoa-subview-pricing');
                if (pricingSub && !pricingSub.classList.contains('hidden') && typeof runPricingSimulation === 'function') {
                    runPricingSimulation();
                } else if (typeof runVkoaTroubleshoot === 'function') {
                    runVkoaTroubleshoot(false);
                }
            }
            showToast(`🔄 Przełączono środowisko na: ${currentCompanyProfile.name} (${currentCompanyProfile.ktopl})`);
        }
    } catch (err) {
        console.error("Błąd przełączania firmy:", err);
    }
}

// --- MODAL TWORZENIA / EDYCJI PROFILU FIRMY ---

function openCompanyModal() {
    const modal = document.getElementById('company-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCompanyModal() {
    const modal = document.getElementById('company-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleCreateCompany(e) {
    e.preventDefault();
    const payload = {
        id: document.getElementById('new-comp-id').value.trim().toUpperCase(),
        name: document.getElementById('new-comp-name').value.trim(),
        ktopl: document.getElementById('new-comp-ktopl').value.trim().toUpperCase(),
        bukrs: document.getElementById('new-comp-bukrs').value.trim(),
        waers: document.getElementById('new-comp-waers').value.trim().toUpperCase(),
        industry: document.getElementById('new-comp-industry').value.trim(),
        custom_z_notes: document.getElementById('new-comp-notes').value.trim()
    };

    try {
        const res = await fetch('/api/companies/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeCompanyModal();
            await loadCompaniesList();
            await handleCompanyChange(payload.id);
            showToast(`✅ Utworzono profil firmy: ${payload.name}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd tworzenia firmy'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd komunikacji z serwerem");
    }
}

function openEditCompanyModal() {
    if (!currentCompanyProfile || !currentCompanyProfile.id) return;
    const modal = document.getElementById('edit-company-modal');
    if (!modal) return;

    document.getElementById('edit-comp-id').value = currentCompanyProfile.id || '';
    document.getElementById('edit-comp-name').value = currentCompanyProfile.name || '';
    document.getElementById('edit-comp-ktopl').value = currentCompanyProfile.ktopl || 'INT';
    document.getElementById('edit-comp-bukrs').value = currentCompanyProfile.bukrs || '1000';
    document.getElementById('edit-comp-waers').value = currentCompanyProfile.waers || 'EUR';
    document.getElementById('edit-comp-industry').value = currentCompanyProfile.industry || '';
    document.getElementById('edit-comp-notes').value = currentCompanyProfile.custom_z_notes || '';

    modal.classList.remove('hidden');
}

function closeEditCompanyModal() {
    const modal = document.getElementById('edit-company-modal');
    if (modal) modal.classList.add('hidden');
}

async function handleUpdateCompany(e) {
    e.preventDefault();
    const payload = {
        id: document.getElementById('edit-comp-id').value.trim().toUpperCase(),
        name: document.getElementById('edit-comp-name').value.trim(),
        ktopl: document.getElementById('edit-comp-ktopl').value.trim().toUpperCase(),
        bukrs: document.getElementById('edit-comp-bukrs').value.trim(),
        waers: document.getElementById('edit-comp-waers').value.trim().toUpperCase(),
        industry: document.getElementById('edit-comp-industry').value.trim(),
        custom_z_notes: document.getElementById('edit-comp-notes').value.trim()
    };

    try {
        const res = await fetch('/api/companies/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeEditCompanyModal();
            currentCompanyProfile = data.profile;
            await loadCompaniesList();
            updateCompanyUI(currentCompanyProfile);
            showToast(`💾 Zaktualizowano profil firmy: ${payload.name}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd aktualizacji firmy'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd komunikacji z serwerem");
    }
}

async function handleDeleteCompany() {
    const compId = document.getElementById('edit-comp-id').value.trim().toUpperCase();
    const compName = document.getElementById('edit-comp-name').value.trim();
    if (!compId) return;

    const confirmed = window.confirm(
        `Czy na pewno chcesz bezpowrotnie usunąć profil "${compName}" (${compId}) wraz ze wszystkimi powiązanymi regułami VKOA, strukturami SD i pamięcią AI?`
    );
    if (!confirmed) return;

    try {
        const res = await fetch('/api/companies/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: compId })
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeEditCompanyModal();
            currentCompanyId = data.new_active_id;
            currentCompanyProfile = data.new_profile;
            await loadCompaniesList();
            await handleCompanyChange(currentCompanyId);
            showToast(`🗑️ ${data.message}`);
        } else {
            showToast(`⚠️ ${data.message || 'Nie można usunąć profilu firmy'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd podczas usuwania profilu firmy");
    }
}

// =========================================================================
// MODAL MASTER DATA & AUTO-SETUP Z RAPORTÓW SAP
// =========================================================================

function openMasterDataModal() {
    const editBtn = document.getElementById('btn-edit-profile');
    if (editBtn) {
        editBtn.classList.remove('btn-profile-glow');
    }

    const modal = document.getElementById('modal-master-data');
    if (!modal) return;

    if (currentCompanyProfile) {
        const nameEl = document.getElementById('manual-name');
        const ktoplEl = document.getElementById('manual-ktopl');
        const bukrsEl = document.getElementById('manual-bukrs');
        const waersEl = document.getElementById('manual-waers');
        if (nameEl) nameEl.value = currentCompanyProfile.name || '';
        if (ktoplEl) ktoplEl.value = currentCompanyProfile.ktopl || 'INT';
        if (bukrsEl) bukrsEl.value = currentCompanyProfile.bukrs || '1000';
        if (waersEl) waersEl.value = currentCompanyProfile.waers || 'EUR';
    }

    modal.classList.remove('hidden');
    loadMdgHealthcheck();
    loadSampleCsvTemplate();
    loadProfileIntelligence();
}

function closeMasterDataModal() {
    const modal = document.getElementById('modal-master-data');
    if (modal) modal.classList.add('hidden');
}

async function applyReportPreset(reportType) {
    try {
        const res = await fetch('/api/companies/setup-from-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report_type: reportType })
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentCompanyId = data.active_id;
            currentCompanyProfile = data.profile;
            await loadCompaniesList();
            updateCompanyUI(currentCompanyProfile);
            await loadSdStructures();
            await loadMdgHealthcheck();
            await loadInferredProcesses();
            closeMasterDataModal();
            showToast(`⚡ ${data.message}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd ładowania raportu'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd połączenia z serwerem przy ładowaniu raportu");
    }
}

async function handleManualMasterDataSubmit(e) {
    e.preventDefault();
    const payload = {
        manual: true,
        company_id: currentCompanyId,
        name: document.getElementById('manual-name').value.trim(),
        ktopl: document.getElementById('manual-ktopl').value.trim().toUpperCase(),
        bukrs: document.getElementById('manual-bukrs').value.trim(),
        vkorg: document.getElementById('manual-vkorg').value.trim(),
        vtweg: document.getElementById('manual-vtweg').value.trim(),
        spart: document.getElementById('manual-spart').value.trim(),
        waers: document.getElementById('manual-waers').value.trim().toUpperCase()
    };

    try {
        const res = await fetch('/api/companies/setup-from-report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            currentCompanyId = data.active_id;
            currentCompanyProfile = data.profile;
            await loadCompaniesList();
            updateCompanyUI(currentCompanyProfile);
            await loadSdStructures();
            await loadMdgHealthcheck();
            await loadInferredProcesses();
            closeMasterDataModal();
            showToast(`💾 ${data.message}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd zapisu danych'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd zapisu Master Data");
    }
}

// =========================================================================
// MASTER DATA GOVERNANCE (MDG), 1-CLICK AUTO-FIX & CSV IMPORT
// =========================================================================

async function loadMdgHealthcheck() {
    try {
        const res = await fetch(`/api/mdg/healthcheck?company_id=${currentCompanyId}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        const scoreBadge = document.getElementById('mdg-score-badge');
        const scoreNum = document.getElementById('mdg-score-num');
        const statusText = document.getElementById('mdg-status-text');
        const statusDesc = document.getElementById('mdg-status-desc');
        const autoFixBtn = document.getElementById('btn-mdg-autofix-all');

        if (scoreNum) scoreNum.textContent = `${data.quality_score}%`;
        if (scoreBadge) {
            scoreBadge.classList.remove('score-warning', 'score-danger');
            if (data.quality_score < 60) {
                scoreBadge.classList.add('score-danger');
            } else if (data.quality_score < 85) {
                scoreBadge.classList.add('score-warning');
            }
        }

        if (statusText) {
            statusText.textContent = data.ready_for_o2c
                ? "✅ Profil gotowy do procesów O2C i fakturowania"
                : "⚠️ Wykryto luki w danych podstawowych (ryzyko VF067 / FF704)";
        }
        if (statusDesc) {
            statusDesc.textContent = `Przeanalizowano ${data.stats.customers_count} klientów, ${data.stats.materials_count} materiałów, ${data.stats.vendors_count} dostawców (${data.stats.subcontractors_count} podwykonawców).`;
        }

        if (autoFixBtn) {
            if (data.issues && data.issues.length > 0) {
                autoFixBtn.style.display = 'inline-flex';
                autoFixBtn.textContent = `⚡ Auto-Fix MDG (${data.issues.length} luk ➔ 100%)`;
            } else {
                autoFixBtn.textContent = `✅ MDG 100% (Kompletne)`;
            }
        }

        const custEl = document.getElementById('stat-cust-cnt');
        const matEl = document.getElementById('stat-mat-cnt');
        const vendEl = document.getElementById('stat-vendor-cnt');
        const vkoaEl = document.getElementById('stat-vkoa-cnt');

        if (custEl) custEl.textContent = data.stats.customers_count;
        if (matEl) matEl.textContent = data.stats.materials_count;
        if (vendEl) vendEl.textContent = `${data.stats.vendors_count} (${data.stats.subcontractors_count} Subcon)`;
        if (vkoaEl) vkoaEl.textContent = data.stats.vkoa_rules_count;

        const issuesContainer = document.getElementById('mdg-issues-container');
        if (issuesContainer) {
            if (!data.issues || data.issues.length === 0) {
                issuesContainer.innerHTML = `
                    <div class="mdg-issue-item" style="border-left-color: #34c759;">
                        <div class="mdg-issue-header">
                            <span class="issue-title">🎉 Kompletność danych Master Data na poziomie 100%</span>
                            <span class="issue-tcode">O2C READY</span>
                        </div>
                        <div class="issue-desc">Wszystkie grupy rozliczeniowe (KTGRD, KTGRM), klasyfikacje podatkowe (TAXKD), reguły ATP (MTVFP) oraz wpisy w Tabeli 001 VKOA są spójne.</div>
                    </div>
                `;
            } else {
                issuesContainer.innerHTML = data.issues.map(iss => {
                    const safeCat = (iss.category || 'ALL').replace(/'/g, "\\'");
                    return `
                        <div class="mdg-issue-item severity-${iss.severity}">
                            <div class="mdg-issue-header">
                                <span class="issue-title">${iss.severity === 'CRITICAL' ? '🚨' : '⚠️'} ${iss.title}</span>
                                <div style="display:flex; align-items:center; gap:6px;">
                                    <span class="issue-tcode">${iss.tcode}</span>
                                    <button type="button" onclick="runMdgAutoFix('${safeCat}')" class="btn-mdg-issue-fix" title="Napraw tę kategorię 1-kliknięciem">
                                        ⚡ Auto-Fix
                                    </button>
                                </div>
                            </div>
                            <div class="issue-desc">${iss.desc}</div>
                        </div>
                    `;
                }).join('');
            }
        }
    } catch (err) {
        console.error("Błąd ładowania audytu MDG:", err);
    }
}

async function runMdgAutoFix(category = 'ALL') {
    const autoFixBtn = document.getElementById('btn-mdg-autofix-all');
    const origText = autoFixBtn ? autoFixBtn.innerHTML : '';
    if (autoFixBtn) {
        autoFixBtn.disabled = true;
        autoFixBtn.innerHTML = '⏳ Naprawianie MDG...';
    }

    try {
        const res = await fetch('/api/mdg/auto-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_id: currentCompanyId,
                category: category
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            await loadMdgHealthcheck();
            await loadSdStructures();
            await loadInferredProcesses();
            if (typeof loadPricingSimulatorContext === 'function') {
                await loadPricingSimulatorContext();
            }
            playUnlockChime();
            showToast(`⚡ Auto-Heal MDG: ${data.message}`);
        } else {
            showToast(`⚠️ ${data.message || 'Błąd automatycznej naprawy MDG'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd połączenia z serwerem podczas Auto-Fix MDG");
    } finally {
        if (autoFixBtn) {
            autoFixBtn.disabled = false;
            if (origText && autoFixBtn.innerHTML === '⏳ Naprawianie MDG...') {
                autoFixBtn.innerHTML = origText;
            }
        }
    }
}

async function loadSampleCsvTemplate() {
    const typeSelect = document.getElementById('csv-data-type');
    const textarea = document.getElementById('csv-content-input');
    if (!typeSelect || !textarea) return;

    const dataType = typeSelect.value;
    try {
        const res = await fetch(`/api/mdg/sample-csv/${dataType}`);
        const data = await res.json();
        if (data.status === 'success') {
            textarea.value = data.csv_content;
        }
    } catch (err) {
        console.error("Błąd ładowania szablonu CSV:", err);
    }
}

function handleCsvTypeChange() {
    loadSampleCsvTemplate();
}

function downloadCsvTemplate() {
    const typeSelect = document.getElementById('csv-data-type');
    const textarea = document.getElementById('csv-content-input');
    if (!typeSelect || !textarea || !textarea.value.trim()) return;

    const dataType = typeSelect.value;
    const blob = new Blob([textarea.value], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sap_${dataType}_template_${currentCompanyId}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`📥 Pobrano wzorzec CSV: sap_${dataType}_template.csv`);
}

async function submitCsvImport() {
    const typeSelect = document.getElementById('csv-data-type');
    const textarea = document.getElementById('csv-content-input');
    if (!typeSelect || !textarea) return;

    const csvContent = textarea.value.trim();
    if (!csvContent) {
        showToast("⚠️ Wklej zawartość CSV przed importem");
        return;
    }

    try {
        const res = await fetch('/api/mdg/import-csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_id: currentCompanyId,
                data_type: typeSelect.value,
                csv_content: csvContent
            })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`🚀 ${data.message}`);
            await loadMdgHealthcheck();
            await loadSdStructures();
            if (data.inferred_processes && typeof renderInferredBanner === 'function') {
                inferredProcessesData = data.inferred_processes;
                renderInferredBanner(data.inferred_processes);
                renderScenariosStrip();
            } else {
                await loadInferredProcesses();
            }
        } else {
            showToast(`⚠️ ${data.message || 'Błąd importu CSV'}`);
        }
    } catch (err) {
        showToast("⚠️ Błąd połączenia podczas importu CSV");
    }
}

async function loadSdStructures() {
    try {
        const res = await fetch(`/api/sd-structures?company_id=${currentCompanyId}`);
        const data = await res.json();

        const saContainer = document.getElementById('sd-sales-areas-list');
        if (saContainer) {
            saContainer.innerHTML = (data.sales_areas || []).map(sa => `
                <div class="flex items-center justify-between bg-slate-50 border border-slate-200/80 rounded-lg px-2.5 py-1.5">
                    <div>
                        <span class="font-mono font-bold text-indigo-700">${sa.vkorg} / ${sa.vtweg} / ${sa.spart}</span>
                        <p class="text-[10px] text-slate-500">${sa.name}</p>
                    </div>
                    <span class="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-slate-200 font-semibold">${sa.waers}</span>
                </div>
            `).join('');
        }

        const otContainer = document.getElementById('sd-order-types-list');
        if (otContainer) {
            otContainer.innerHTML = (data.order_types || []).map(ot => `
                <div class="bg-slate-50 border border-slate-200/80 rounded-lg px-2.5 py-1.5">
                    <div class="flex items-center justify-between">
                        <span class="font-mono font-bold text-slate-800 bg-amber-100 text-amber-900 px-1.5 py-0.5 rounded text-[10px]">${ot.auart}</span>
                        <span class="font-mono text-[10px] text-slate-500">Poz: <b>${ot.default_item_cat}</b> ➔ Fakt: <b>${ot.billing_type}</b></span>
                    </div>
                    <p class="text-[11px] font-medium text-slate-700 mt-1">${ot.bezeichnung}</p>
                </div>
            `).join('');
        }

        const prContainer = document.getElementById('sd-pricing-list');
        if (prContainer) {
            prContainer.innerHTML = (data.pricing_conditions || []).map(pr => `
                <div class="flex items-center justify-between bg-slate-50 border border-slate-200/80 rounded-lg px-2.5 py-1.5">
                    <div>
                        <span class="font-mono font-bold text-emerald-700">${pr.kschl}</span>
                        <span class="text-[11px] text-slate-700 ml-1">${pr.description}</span>
                    </div>
                    <span class="font-mono text-[10px] bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded font-bold border border-indigo-200" title="Klucz konta VKOA">${pr.account_key || '-'}</span>
                </div>
            `).join('');
        }
    } catch (err) {
        console.error("Błąd ładowania struktur SD:", err);
    }
}

// =========================================================================
// PROFIL HANDLOWO-LOGISTYCZNY & PRÓBKA KORPORACYJNA (3 500 POZYCJI VBAK/VBAP)
// =========================================================================

async function loadProfileIntelligence(companyId) {
    const cid = companyId || currentCompanyId;
    const summaryContainer = document.getElementById('intel-executive-summary');
    if (!summaryContainer) return;

    try {
        const res = await fetch(`/api/profile/intelligence?company_id=${cid}`);
        const data = await res.json();

        if (data.status === 'success') {
            const bullets = data.summary_bullets || data.executive_summary || [];
            if (bullets.length > 0) {
                summaryContainer.innerHTML = bullets.map(b => {
                    const formatted = b.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    return `<div class="intel-bullet"><span>💡</span> <span>${formatted}</span></div>`;
                }).join('');
            } else {
                summaryContainer.innerHTML = '<div class="intel-loading">Brak zarejestrowanych danych transakcyjnych. Kliknij "Załaduj próbkę korporacyjną" powyżej.</div>';
            }

            // Filar 1: VBAK + VBAP
            const comm = data.commercial || {};
            const vbakCnt = document.getElementById('intel-vbak-cnt');
            const vbakOrders = document.getElementById('intel-vbak-orders');
            const vbakTurnover = document.getElementById('intel-vbak-turnover');
            const vbakAvg = document.getElementById('intel-vbak-avg');
            if (vbakCnt) vbakCnt.textContent = (comm.total_items_count || 0).toLocaleString();
            if (vbakOrders) vbakOrders.textContent = (comm.total_orders_count || 0).toLocaleString();
            if (vbakTurnover) vbakTurnover.textContent = comm.total_turnover_fmt || '0 PLN';
            if (vbakAvg) vbakAvg.textContent = comm.avg_item_value_fmt || '0 PLN';

            const unitsContainer = document.getElementById('intel-units-tags');
            if (unitsContainer && comm.top_units) {
                unitsContainer.innerHTML = comm.top_units.map(([u, pct]) =>
                    `<span class="pillar-tag"><strong>${u}</strong> (${pct}%)</span>`
                ).join('');
            }

            const modelsContainer = document.getElementById('intel-models-tags');
            if (modelsContainer && comm.models_breakdown) {
                modelsContainer.innerHTML = comm.models_breakdown.map(m =>
                    `<span class="pillar-tag"><strong>${m.model}</strong> (${m.count} poz., ${m.turnover_pct}%)</span>`
                ).join('');
            }

            // Filar 2: KNVV
            const port = data.portfolio || {};
            const knvvCnt = document.getElementById('intel-knvv-cnt');
            const knvvDom = document.getElementById('intel-knvv-dom');
            const knvvExp = document.getElementById('intel-knvv-exp');
            const knvvZterm = document.getElementById('intel-knvv-zterm');
            if (knvvCnt) knvvCnt.textContent = (port.total_customers_count || 0).toLocaleString();
            if (knvvDom) knvvDom.textContent = `${port.domestic_pct || 0}%`;
            if (knvvExp) knvvExp.textContent = `${port.export_pct || 0}%`;
            if (knvvZterm && port.payment_terms && port.payment_terms[0]) {
                knvvZterm.textContent = port.payment_terms[0].code;
            }

            const incoContainer = document.getElementById('intel-incoterms-tags');
            if (incoContainer && port.incoterms) {
                incoContainer.innerHTML = port.incoterms.map(i =>
                    `<span class="pillar-tag"><strong>${i.code}</strong> (${i.pct}%)</span>`
                ).join('');
            }

            const kdgrpContainer = document.getElementById('intel-kdgrp-tags');
            if (kdgrpContainer && port.customer_groups) {
                kdgrpContainer.innerHTML = port.customer_groups.map(g =>
                    `<span class="pillar-tag">${g.name} (<strong>${g.pct}%</strong>)</span>`
                ).join('');
            }

            // Filar 3: LIPS + VBRK
            const log = data.logistics || {};
            const lipsCnt = document.getElementById('intel-lips-cnt');
            const lipsLead = document.getElementById('intel-lips-lead');
            const lipsVstel = document.getElementById('intel-lips-vstel');
            const lipsRoutes = document.getElementById('intel-lips-routes');
            if (lipsCnt) lipsCnt.textContent = (log.total_flow_records || 0).toLocaleString();
            if (lipsLead) lipsLead.textContent = `${log.avg_lead_time_days || 0} dni`;
            if (lipsVstel) lipsVstel.textContent = (log.shipping_points ? log.shipping_points.length : 0);
            if (lipsRoutes) lipsRoutes.textContent = (log.routes ? log.routes.length : 0);

            const vstelContainer = document.getElementById('intel-vstel-tags');
            if (vstelContainer && log.shipping_points) {
                vstelContainer.innerHTML = log.shipping_points.map(s =>
                    `<span class="pillar-tag"><strong>${s.code}</strong>: ${s.name} (${s.pct}%)</span>`
                ).join('');
            }

            const flowContainer = document.getElementById('intel-flow-tags');
            if (flowContainer && log.billing_types) {
                flowContainer.innerHTML = log.billing_types.map(b =>
                    `<span class="pillar-tag"><strong>${b.type}</strong> (${b.count} dok., ${b.pct}%)</span>`
                ).join('');
            }

            // Filar 4: TVxx Słowniki & Żargon
            const jargon = data.jargon || {};
            const jargonCnt = document.getElementById('intel-jargon-cnt');
            const jargonZcodes = document.getElementById('intel-jargon-zcodes');
            if (jargonCnt) jargonCnt.textContent = (jargon.total_dictionary_entries || 0).toLocaleString();
            if (jargonZcodes) jargonZcodes.textContent = (jargon.z_codes ? jargon.z_codes.length : 0);

            const zList = document.getElementById('intel-z-list');
            if (zList && jargon.z_codes) {
                zList.innerHTML = jargon.z_codes.map(z =>
                    `<div class="pillar-z-item"><span class="z-code-badge">${z.code}</span> <span class="z-code-meaning"><strong>${z.name}</strong> ➔ ${z.business_meaning}</span></div>`
                ).join('');
            }
        }
    } catch (err) {
        console.error('Błąd pobierania raportu inteligencji:', err);
    }
}

async function seedEnterpriseData(force = false) {
    const btn = document.getElementById('btn-seed-enterprise');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Zasilanie bazy (3 500 pozycji)...';
    }

    showToast('🚀 Generowanie 3 500 pozycji VBAK/VBAP, KNVV, LIPS i TVxx...');

    try {
        const res = await fetch('/api/profile/seed-enterprise-samples', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: currentCompanyId, force: force })
        });
        const data = await res.json();

        if (data.status === 'success') {
            playUnlockChime();
            showToast(`✅ Sukces! ${data.message || 'Zasilono bazę danymi korporacyjnymi'}`);
            await loadProfileIntelligence(currentCompanyId);
            await loadMdgHealthcheck(currentCompanyId);
            await loadInferredProcesses(currentCompanyId);
            loadOrdersTable(currentPstyvFilter);
        } else {
            showToast('⚠️ Błąd seedowania danych: ' + data.message);
        }
    } catch (err) {
        showToast('⚠️ Błąd sieciowy: ' + err.message);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '⚡ Załaduj próbkę korporacyjną';
        }
    }
}

function toggleOrdersTable() {
    const box = document.getElementById('orders-accordion-box');
    if (box && !box.open && !ordersTableLoaded) {
        loadOrdersTable('');
    }
}

function filterOrdersTable(pstyv) {
    currentPstyvFilter = pstyv;
    const chips = document.querySelectorAll('.table-filter-chip');
    chips.forEach(c => c.classList.remove('active'));

    const activeId = pstyv ? `chip-pstyv-${pstyv.toLowerCase()}` : 'chip-pstyv-all';
    const activeChip = document.getElementById(activeId);
    if (activeChip) activeChip.classList.add('active');

    loadOrdersTable(pstyv);
}

async function loadOrdersTable(pstyv = '') {
    const tbody = document.getElementById('orders-table-tbody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="11" class="text-center py-3 text-secondary">⏳ Ładowanie pozycji VBAK/VBAP...</td></tr>';

    try {
        const url = `/api/profile/orders?company_id=${currentCompanyId}&pstyv=${encodeURIComponent(pstyv)}&limit=30`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.status === 'success' && data.orders && data.orders.length > 0) {
            tbody.innerHTML = data.orders.map(o => `
                <tr>
                    <td><strong>${o.vbeln}</strong></td>
                    <td>${o.posnr}</td>
                    <td>${o.erdat}</td>
                    <td><span class="badge-sd">${o.auart}</span></td>
                    <td><code>${o.matnr}</code></td>
                    <td>${o.arktx}</td>
                    <td>${o.kwmeng.toLocaleString()}</td>
                    <td>${o.vrkme}</td>
                    <td>${o.netpr.toFixed(2)} ${o.waerk}</td>
                    <td><strong>${o.netwr.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${o.waerk}</strong></td>
                    <td><span class="z-code-badge">${o.pstyv}</span></td>
                </tr>
            `).join('');
            ordersTableLoaded = true;
        } else {
            tbody.innerHTML = '<tr><td colspan="11" class="text-center py-3 text-secondary">Brak pozycji dla podanego filtru.</td></tr>';
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="11" class="text-center py-3 text-danger">Błąd ładowania: ${err.message}</td></tr>`;
    }
}

// Eksport globalny dla atrybutów inline HTML
window.loadCompaniesList = loadCompaniesList;
window.updateCompanyUI = updateCompanyUI;
window.handleCompanyChange = handleCompanyChange;
window.openCompanyModal = openCompanyModal;
window.closeCompanyModal = closeCompanyModal;
window.handleCreateCompany = handleCreateCompany;
window.openEditCompanyModal = openEditCompanyModal;
window.closeEditCompanyModal = closeEditCompanyModal;
window.handleUpdateCompany = handleUpdateCompany;
window.handleDeleteCompany = handleDeleteCompany;
window.openMasterDataModal = openMasterDataModal;
window.closeMasterDataModal = closeMasterDataModal;
window.applyReportPreset = applyReportPreset;
window.handleManualMasterDataSubmit = handleManualMasterDataSubmit;
window.loadMdgHealthcheck = loadMdgHealthcheck;
window.runMdgAutoFix = runMdgAutoFix;
window.loadSampleCsvTemplate = loadSampleCsvTemplate;
window.handleCsvTypeChange = handleCsvTypeChange;
window.downloadCsvTemplate = downloadCsvTemplate;
window.submitCsvImport = submitCsvImport;
window.loadSdStructures = loadSdStructures;
window.loadProfileIntelligence = loadProfileIntelligence;
window.seedEnterpriseData = seedEnterpriseData;
window.toggleOrdersTable = toggleOrdersTable;
window.filterOrdersTable = filterOrdersTable;
window.loadOrdersTable = loadOrdersTable;
