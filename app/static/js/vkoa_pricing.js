// =========================================================================
// MODUŁ 3: VKOA TROUBLESHOOTER (KOFI00) & SYMULATOR WYCENY V/08 -> VKOA
// =========================================================================

let lastVkoaQuickFix = null;
let currentPricingContext = null;
let lastPricingSimulation = null;

function switchVkoaSubview(subview) {
    const analyzerBox = document.getElementById('vkoa-subview-analyzer');
    const pricingBox = document.getElementById('vkoa-subview-pricing');
    const btnAnalyzer = document.getElementById('btn-vkoa-sub-analyzer');
    const btnPricing = document.getElementById('btn-vkoa-sub-pricing');

    if (subview === 'pricing') {
        if (analyzerBox) analyzerBox.classList.add('hidden');
        if (pricingBox) pricingBox.classList.remove('hidden');
        if (btnAnalyzer) btnAnalyzer.classList.remove('active');
        if (btnPricing) btnPricing.classList.add('active');
        loadPricingSimulatorContext().then(() => runPricingSimulation());
    } else {
        if (pricingBox) pricingBox.classList.add('hidden');
        if (analyzerBox) analyzerBox.classList.remove('hidden');
        if (btnPricing) btnPricing.classList.remove('active');
        if (btnAnalyzer) btnAnalyzer.classList.add('active');
    }
}

// =========================================================================
// 1. VKOA ACCOUNT DETERMINATION TROUBLESHOOTER (KOFI00 / VF067)
// =========================================================================

function fillVkoaSample(type) {
    const ktopl = currentCompanyProfile.ktopl || 'INT';
    const vkorg = currentCompanyId === 'CLIENT_B' ? '2000' : '1000';

    document.getElementById('vkoa-ktopl').value = ktopl;
    document.getElementById('vkoa-vkorg').value = vkorg;

    if (type === 'existing') {
        document.getElementById('vkoa-ktgrd').value = '01';
        document.getElementById('vkoa-ktgrm').value = '02';
        document.getElementById('vkoa-kvsl').value = 'ERL';
        document.getElementById('vkoa-raw-error').value = `VF01 Log: Weryfikacja konta KOFI dla ${ktopl} ${vkorg} 01 02 ERL`;
    } else if (type === 'missing') {
        document.getElementById('vkoa-ktgrd').value = '02';
        document.getElementById('vkoa-ktgrm').value = '02';
        document.getElementById('vkoa-kvsl').value = 'ERL';
        document.getElementById('vkoa-raw-error').value = `VF067: Account determination for entry ${ktopl} ${vkorg} 02 02 ERL not possible`;
    } else if (type === 'rebate') {
        document.getElementById('vkoa-ktgrd').value = '01';
        document.getElementById('vkoa-ktgrm').value = '02';
        document.getElementById('vkoa-kvsl').value = 'ERS';
        document.getElementById('vkoa-raw-error').value = `VF067: Account determination for entry ${ktopl} ${vkorg} 01 02 ERS not possible`;
    }

    runVkoaTroubleshoot(false);
}

async function runVkoaTroubleshoot(useRawLog = false) {
    const container = document.getElementById('vkoa-results-container');
    if (!container) return;

    container.innerHTML = `
        <div class="flex items-center justify-center h-full text-slate-500 text-xs gap-2 py-8">
            <span class="animate-spin text-lg">⚙️</span> Symulacja sekwencji dostępu KOFI00 w tabelach C001-C005...
        </div>
    `;

    const payload = {
        company_id: currentCompanyId,
        raw_error: useRawLog ? document.getElementById('vkoa-raw-error').value : '',
        ktopl: document.getElementById('vkoa-ktopl').value.trim().toUpperCase(),
        vkorg: document.getElementById('vkoa-vkorg').value.trim(),
        ktgrd_cust: document.getElementById('vkoa-ktgrd').value,
        ktgrm_mat: document.getElementById('vkoa-ktgrm').value,
        kvsl: document.getElementById('vkoa-kvsl').value
    };

    try {
        const res = await fetch('/api/vkoa/troubleshoot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.inputs) {
            document.getElementById('vkoa-ktopl').value = data.inputs.ktopl;
            document.getElementById('vkoa-vkorg').value = data.inputs.vkorg;
            document.getElementById('vkoa-ktgrd').value = data.inputs.ktgrd_cust;
            document.getElementById('vkoa-ktgrm').value = data.inputs.ktgrm_mat;
            document.getElementById('vkoa-kvsl').value = data.inputs.kvsl;
        }

        renderVkoaSimulation(data);
    } catch (err) {
        container.innerHTML = `<div class="text-rose-600 text-xs p-4">Błąd symulacji VKOA: ${err.message}</div>`;
    }
}

function renderVkoaSimulation(data) {
    const container = document.getElementById('vkoa-results-container');
    lastVkoaQuickFix = data.quick_fix || null;

    const statusBanner = data.success
        ? `<div class="bg-emerald-50 border border-emerald-300 rounded-xl p-3.5 flex items-center justify-between shadow-sm">
               <div class="flex items-center gap-3">
                   <span class="text-2xl">✅</span>
                   <div>
                       <h4 class="text-xs font-bold text-emerald-950">${data.message}</h4>
                       <p class="text-[11px] text-emerald-800 mt-0.5">Faktura <b>VF01/VF02</b> zostanie poprawnie zwolniona do księgowości FI (Dokument księgowy bez blokady VFX3).</p>
                   </div>
               </div>
               <div class="text-right bg-white px-3 py-1.5 rounded-lg border border-emerald-200">
                   <span class="text-[10px] text-slate-400 uppercase font-bold block">Konto G/L (SAKNR)</span>
                   <span class="font-mono text-base font-extrabold text-emerald-700">${data.account}</span>
               </div>
           </div>`
        : `<div class="bg-rose-50 border border-rose-300 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-sm">
               <div class="flex items-start gap-3">
                   <span class="text-2xl">🚨</span>
                   <div>
                       <h4 class="text-xs font-bold text-rose-950">${data.message}</h4>
                       <p class="text-[11px] text-rose-800 mt-0.5">${data.root_cause}</p>
                   </div>
               </div>
               <button onclick="applyVkoaQuickFix()" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3.5 py-2 rounded-lg shadow transition flex items-center gap-1.5 shrink-0">
                   <span>⚡</span> Auto-Fix w VKOA (Dodaj konto ${data.quick_fix?.saknr || '800000'})
               </button>
           </div>`;

    const stepsHtml = (data.steps || []).map(s => {
        const isHit = s.status === 'FOUND';
        const badge = isHit
            ? `<span class="bg-emerald-600 text-white font-mono text-[10px] font-bold px-2 py-0.5 rounded-full">✓ ZNALEZIONO: ${s.account}</span>`
            : `<span class="bg-slate-200 text-slate-600 font-mono text-[10px] font-semibold px-2 py-0.5 rounded-full">✗ BRAK WPISU</span>`;

        const keysPills = Object.entries(s.keys || {}).map(([k, v]) =>
            `<span class="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded font-mono text-slate-700"><b>${k}:</b> ${v}</span>`
        ).join(' ');

        return `
            <div class="border ${isHit ? 'border-emerald-400 bg-emerald-50/50 ring-2 ring-emerald-500/20' : 'border-slate-200 bg-white'} rounded-xl p-3 transition">
                <div class="flex items-center justify-between mb-1.5">
                    <div class="flex items-center gap-2">
                        <span class="w-5 h-5 rounded-full ${isHit ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'} text-[10px] font-bold flex items-center justify-center">${s.step}</span>
                        <span class="text-xs font-bold text-slate-800">${s.table_name}</span>
                    </div>
                    ${badge}
                </div>
                <p class="text-[11px] text-slate-500 mb-2">${s.description}</p>
                <div class="flex flex-wrap gap-1.5">${keysPills}</div>
            </div>
        `;
    }).join('');

    let resolutionHtml = '';
    if (!data.success && data.resolution_steps) {
        const resSteps = data.resolution_steps.map(r => `
            <div class="bg-white border border-slate-200 rounded-lg p-2.5">
                <div class="flex items-center justify-between mb-1">
                    <span class="font-bold text-xs text-slate-800">${r.step}. ${r.action}</span>
                    <span class="tcode-pill" onclick="copyText('${r.tcode.split(' ')[0]}')">📋 ${r.tcode}</span>
                </div>
                <p class="text-[11px] text-slate-600">${r.details}</p>
            </div>
        `).join('');

        resolutionHtml = `
            <div class="mt-4 bg-amber-50/70 border border-amber-200 rounded-xl p-3.5">
                <h5 class="text-xs font-bold text-amber-950 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <span>🛠️</span> Instrukcja naprawcza dla konsultanta SAP SD/FI:
                </h5>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">${resSteps}</div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="space-y-3">
            ${statusBanner}
            <div class="pt-1">
                <h5 class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Ślad przeszukiwania sekwencji dostępu KOFI00 (Access Sequence Trace):</h5>
                <div class="space-y-2">${stepsHtml}</div>
            </div>
            ${resolutionHtml}
        </div>
    `;
}

async function applyVkoaQuickFix() {
    if (!lastVkoaQuickFix) return;
    try {
        const res = await fetch('/api/vkoa/quick-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastVkoaQuickFix)
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(`✅ ${data.message}`);
            await loadSdStructures();
            await runVkoaTroubleshoot(false);
        }
    } catch (err) {
        showToast("⚠️ Błąd podczas zapisywania reguły VKOA");
    }
}

// =========================================================================
// 2. SYMULATOR PROCEDURY WYCENY SAP SD (V/08 / PRCD_ELEMENTS -> VKOA)
// =========================================================================

async function loadPricingSimulatorContext() {
    const kunnrSelect = document.getElementById('pricing-kunnr');
    const matnrSelect = document.getElementById('pricing-matnr');
    if (!kunnrSelect || !matnrSelect) return;

    try {
        const res = await fetch(`/api/pricing/context?company_id=${currentCompanyId}`);
        const data = await res.json();
        if (data.status !== 'success') return;

        currentPricingContext = data;

        kunnrSelect.innerHTML = (data.customers || []).map(c =>
            `<option value="${c.kunnr}">${c.kunnr} – ${c.name1} (KTGRD: ${c.ktgrd}, Kraj: ${c.land1})</option>`
        ).join('');

        matnrSelect.innerHTML = (data.materials || []).map(m =>
            `<option value="${m.matnr}">${m.matnr} – ${m.maktx} (KTGRM: ${m.ktgrm}, Cena baz.: ${m.suggested_price} ${data.waers})</option>`
        ).join('');
    } catch (err) {
        console.error("Błąd ładowania kontekstu symulatora V/08:", err);
    }
}

function handlePricingMaterialChange() {
    const priceInput = document.getElementById('pricing-override-price');
    if (priceInput) {
        priceInput.value = '';
    }
    runPricingSimulation();
}

async function runPricingSimulation() {
    const container = document.getElementById('pricing-results-container');
    if (!container) return;

    const kunnrEl = document.getElementById('pricing-kunnr');
    const matnrEl = document.getElementById('pricing-matnr');
    if (!kunnrEl || !matnrEl) return;

    if (!kunnrEl.options.length || !matnrEl.options.length) {
        await loadPricingSimulatorContext();
    }

    const payload = {
        company_id: currentCompanyId,
        kunnr: kunnrEl.value,
        matnr: matnrEl.value,
        quantity: parseFloat(document.getElementById('pricing-qty')?.value || '10') || 10,
        discount_pct: parseFloat(document.getElementById('pricing-disc')?.value || '0') || 0,
        freight_val: parseFloat(document.getElementById('pricing-freight')?.value || '0') || 0,
        override_base_price: document.getElementById('pricing-override-price')?.value || null
    };

    try {
        const res = await fetch('/api/pricing/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            lastPricingSimulation = data;
            renderPricingSimulation(data);
        }
    } catch (err) {
        container.innerHTML = `<div class="text-rose-600 text-xs p-4">Błąd symulacji V/08: ${err.message}</div>`;
    }
}

function renderPricingSimulation(data) {
    const container = document.getElementById('pricing-results-container');
    if (!container) return;

    const w = data.waers || 'EUR';
    const t = data.totals || {};
    const c = data.customer || {};
    const m = data.material || {};

    const statusBanner = data.billing_ready
        ? `<div class="bg-emerald-50 border border-emerald-300 rounded-xl p-3 mb-3 flex items-center justify-between">
               <div class="flex items-center gap-2.5">
                   <span class="text-xl">✅</span>
                   <div>
                       <div class="text-xs font-bold text-emerald-950">Procedura ${data.procedure} kompletna – Wszystkie klucze kont VKOA ustalone!</div>
                       <div class="text-[11px] text-emerald-800">Klient <b>${c.kunnr}</b> (KTGRD: <code>${c.ktgrd}</code>) × Materiał <b>${m.matnr}</b> (KTGRM: <code>${m.ktgrm}</code>) ➔ Faktura VF01 zaksięguje się automatycznie w FI.</div>
                   </div>
               </div>
               <span class="ios-badge bg-chip-green">VF01 ➔ FI READY</span>
           </div>`
        : `<div class="bg-rose-50 border border-rose-300 rounded-xl p-3 mb-3 flex flex-wrap items-center justify-between gap-2">
               <div class="flex items-center gap-2.5">
                   <span class="text-xl">🚨</span>
                   <div>
                       <div class="text-xs font-bold text-rose-950">Wykryto błąd VF067 dla ${data.vkoa_issues.length} warunków cenowych w procedurze ${data.procedure}!</div>
                       <div class="text-[11px] text-rose-800">Faktura VF01 utknie w blokadzie księgowej <b>VFX3</b>. Użyj przycisku <b>⚡ Auto-Fix VKOA</b> bezpośrednio w wierszu tabeli poniżej.</div>
                   </div>
               </div>
               <span class="ios-badge ios-badge-error">BLOKADA VFX3 (VF067)</span>
           </div>`;

    const kpiStrip = `
        <div class="pricing-summary-strip">
            <div class="pricing-kpi-card">
                <span class="pricing-kpi-lbl">Wartość Netto (VBAP-NETWR)</span>
                <span class="pricing-kpi-val">${t.netwr.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${w}</span>
            </div>
            <div class="pricing-kpi-card">
                <span class="pricing-kpi-lbl">Podatek VAT (MWST ${t.tax_rate_pct}%)</span>
                <span class="pricing-kpi-val">${t.tax_value.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${w}</span>
            </div>
            <div class="pricing-kpi-card">
                <span class="pricing-kpi-lbl">Wartość Brutto Faktury</span>
                <span class="pricing-kpi-val" style="color: var(--ios-blue);">${t.gross_total.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${w}</span>
            </div>
            <div class="pricing-kpi-card">
                <span class="pricing-kpi-lbl">Marża Handlowa (po VPRS)</span>
                <span class="pricing-kpi-val" style="color: ${t.margin_val >= 0 ? 'var(--ios-green)' : 'var(--ios-red)'};">
                    ${t.margin_val.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${w} (${t.margin_pct}%)
                </span>
            </div>
        </div>
    `;

    const rowsHtml = (data.steps || []).map((s, idx) => {
        const rowClass = s.is_subtotal ? 'row-subtotal' : (s.is_statistical ? 'row-statistical' : '');
        let vkoaCell = `<span class="text-slate-400 text-[10px]">— (Pozycja sumaryczna / statyst.)</span>`;

        if (s.vkoa) {
            if (s.vkoa.status === 'DETERMINED') {
                vkoaCell = `
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span class="ios-badge bg-chip-green">G/L: ${s.vkoa.saknr}</span>
                        <span class="text-[10px] text-slate-500">Tabela ${s.vkoa.matched_table}</span>
                    </div>
                `;
            } else {
                const errLog = `VF067: Account determination for entry ${data.ktopl} ${c.vkorg} ${c.ktgrd} ${m.ktgrm} ${s.kvsl} not possible`;
                const safeLog = errLog.replace(/'/g, "\\'");
                vkoaCell = `
                    <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                        <span class="ios-badge ios-badge-error">❌ VF067 Brak konta</span>
                        <button type="button" onclick="applyPricingVkoaQuickFix(${idx})" class="btn-mdg-issue-fix" title="Dodaj konto ${s.vkoa.suggested_saknr} do Tabeli 001 VKOA">
                            ⚡ Auto-Fix (${s.vkoa.suggested_saknr})
                        </button>
                        <button type="button" onclick="handoffPricingToVkoaAnalyzer('${safeLog}')" class="ios-tcode-pill" title="Otwórz w analizatorze KOFI00">
                            🔍 KOFI00
                        </button>
                    </div>
                `;
            }
        }

        return `
            <tr class="${rowClass}">
                <td><code>${s.step}</code></td>
                <td><span class="ios-tcode-pill" onclick="copyText('${s.kschl}')">${s.kschl}</span></td>
                <td>${s.name}</td>
                <td><code>${s.kbetr}</code></td>
                <td style="font-family: var(--ios-mono); font-weight: 700;">
                    ${s.kwert.toLocaleString('pl-PL', {minimumFractionDigits: 2})} ${w}
                </td>
                <td>${s.kvsl ? `<span class="ios-badge ios-badge-blue">${s.kvsl}</span>` : '—'}</td>
                <td>${vkoaCell}</td>
            </tr>
        `;
    }).join('');

    container.innerHTML = `
        ${statusBanner}
        ${kpiStrip}
        <table class="pricing-cascade-table">
            <thead>
                <tr>
                    <th>Krok</th>
                    <th>Warunek (KSCHL)</th>
                    <th>Nazwa w schemacie wyceny (V/08)</th>
                    <th>Stawka / Reguła (KBETR)</th>
                    <th>Wartość pozycji (KWERT)</th>
                    <th>Klucz (KVSL)</th>
                    <th>Determinacja konta FI (VKOA / KOFI00)</th>
                </tr>
            </thead>
            <tbody>
                ${rowsHtml}
            </tbody>
        </table>
    `;
}

async function applyPricingVkoaQuickFix(stepIndex) {
    if (!lastPricingSimulation || !lastPricingSimulation.steps) return;
    const step = lastPricingSimulation.steps[stepIndex];
    if (!step || !step.vkoa || !step.vkoa.quick_fix) return;

    try {
        const res = await fetch('/api/vkoa/quick-fix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(step.vkoa.quick_fix)
        });
        const data = await res.json();
        if (data.status === 'success') {
            playUnlockChime();
            showToast(`✅ ${data.message}`);
            await loadSdStructures();
            await runPricingSimulation();
        }
    } catch (err) {
        showToast("⚠️ Błąd podczas zapisu reguły VKOA z symulatora wyceny");
    }
}

function handoffPricingToVkoaAnalyzer(errorLog) {
    switchVkoaSubview('analyzer');
    const rawInput = document.getElementById('vkoa-raw-error');
    if (rawInput) {
        rawInput.value = errorLog;
    }
    runVkoaTroubleshoot(true);
}

// Eksport globalny dla atrybutów inline HTML
window.switchVkoaSubview = switchVkoaSubview;
window.fillVkoaSample = fillVkoaSample;
window.runVkoaTroubleshoot = runVkoaTroubleshoot;
window.renderVkoaSimulation = renderVkoaSimulation;
window.applyVkoaQuickFix = applyVkoaQuickFix;
window.loadPricingSimulatorContext = loadPricingSimulatorContext;
window.handlePricingMaterialChange = handlePricingMaterialChange;
window.runPricingSimulation = runPricingSimulation;
window.applyPricingVkoaQuickFix = applyPricingVkoaQuickFix;
window.handoffPricingToVkoaAnalyzer = handoffPricingToVkoaAnalyzer;
