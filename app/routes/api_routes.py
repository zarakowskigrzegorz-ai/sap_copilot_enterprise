import io
from flask import Blueprint, request, jsonify, send_file, render_template
from app.database.db_manager import (
    get_db_connection,
    get_active_company_id,
    set_active_company,
    get_company_profile,
    get_all_companies,
    create_company_profile,
    update_company_profile,
    delete_company_profile,
    save_ai_memory,
    get_ai_memories,
    approve_export_transaction,
    get_sd_tcodes,
    get_sd_tcode_categories,
    add_custom_sd_tcode
)
from app.services.transaction_service import TransactionService
from app.services.process_service import (
    get_sd_process_catalog,
    get_document_flow_scenarios,
    get_available_processes,
    get_available_scenarios
)
from app.services.vkoa_service import VkoaTroubleshooterService

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def home():
    return render_template('index.html')

@api_bp.route('/landing')
@api_bp.route('/strona')
def landing_page():
    """Dedykowana strona produktowa / wizytówka aplikacji SAP SD Enterprise Copilot."""
    return render_template('landing.html')

# --- MULTI-COMPANY WORKSPACE API ---

@api_bp.route('/api/companies', methods=['GET'])
def get_companies():
    """Zwraca listę wszystkich profili firm i identyfikator aktywnej firmy."""
    companies = get_all_companies()
    active_id = get_active_company_id()
    active_profile = get_company_profile(active_id)
    return jsonify({
        "status": "success",
        "companies": companies,
        "active_id": active_id,
        "active_profile": active_profile
    })

@api_bp.route('/api/companies/active', methods=['POST'])
def switch_active_company():
    """Przełącza aktywny profil klienta."""
    data = request.json or {}
    company_id = data.get('company_id', '').strip()
    if not company_id:
        return jsonify({"status": "error", "message": "Brak company_id"}), 400
    
    success = set_active_company(company_id)
    if not success:
        return jsonify({"status": "error", "message": f"Firma {company_id} nie istnieje"}), 404
    
    profile = get_company_profile(company_id)
    return jsonify({
        "status": "success",
        "active_id": company_id,
        "active_profile": profile
    })

@api_bp.route('/api/companies/create', methods=['POST'])
def create_company():
    """Tworzy nowy profil klienta w Multi-Company Workspace."""
    data = request.json or {}
    company_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    ktopl = data.get('ktopl', 'INT').strip().upper()
    bukrs = data.get('bukrs', '1000').strip()
    waers = data.get('waers', 'EUR').strip().upper()
    industry = data.get('industry', '').strip()
    custom_z_notes = data.get('custom_z_notes', '').strip()

    if not company_id or not name:
        return jsonify({"status": "error", "message": "ID i Nazwa firmy są wymagane"}), 400

    success = create_company_profile(company_id, name, ktopl, bukrs, waers, industry, custom_z_notes)
    if not success:
        return jsonify({"status": "error", "message": f"Firma o ID {company_id} już istnieje"}), 409

    return jsonify({"status": "success", "id": company_id})

@api_bp.route('/api/companies/update', methods=['POST'])
def update_company():
    """Aktualizuje profil klienta w Multi-Company Workspace."""
    data = request.json or {}
    company_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    ktopl = data.get('ktopl', 'INT').strip().upper()
    bukrs = data.get('bukrs', '1000').strip()
    waers = data.get('waers', 'EUR').strip().upper()
    industry = data.get('industry', '').strip()
    custom_z_notes = data.get('custom_z_notes', '').strip()

    if not company_id or not name:
        return jsonify({"status": "error", "message": "ID i Nazwa firmy są wymagane"}), 400

    success = update_company_profile(company_id, name, ktopl, bukrs, waers, industry, custom_z_notes)
    if not success:
        return jsonify({"status": "error", "message": f"Firma {company_id} nie istnieje"}), 404

    profile = get_company_profile(company_id)
    return jsonify({"status": "success", "profile": profile})

@api_bp.route('/api/companies/setup-from-report', methods=['POST'])
def setup_from_report():
    """Automatycznie konfiguruje profil firmy i Master Data na podstawie wybranego raportu SAP lub danych ręcznych."""
    data = request.json or {}
    report_type = data.get('report_type')
    company_id = data.get('company_id') or get_active_company_id()
    
    presets = {
        'EC01_MANUFACTURING': {
            'id': 'CLIENT_A',
            'name': 'Global Manufacturing Corp',
            'ktopl': 'INT',
            'bukrs': '1000',
            'waers': 'EUR',
            'industry': 'Przemysł Maszynowy & Produkcja Dyskretna',
            'custom_z_notes': 'Auto-setup z raportu EC01: Obszar 1000/10/00, procedura wyceny PR00, determinacja KOFI00.',
            'sales_area': {'vkorg': '1000', 'vtweg': '10', 'spart': '00', 'name': 'Krajowa sprzedaż maszyn'}
        },
        'RETAIL_FMCG': {
            'id': 'CLIENT_B',
            'name': 'Retail & FMCG Europe',
            'ktopl': 'PL01',
            'bukrs': '2000',
            'waers': 'PLN',
            'industry': 'Handel Detaliczny & Sieci Sklepowe FMCG',
            'custom_z_notes': 'Auto-setup z raportu VKOA: Obszar 2000/20/01, rabaty RA00/K007, dostawy ekspresowe.',
            'sales_area': {'vkorg': '2000', 'vtweg': '20', 'spart': '01', 'name': 'Sieć sklepów detalicznych'}
        },
        'TECH_CLOUD': {
            'id': 'CLIENT_C',
            'name': 'Cloud & Tech Enterprise Solutions',
            'ktopl': 'US01',
            'bukrs': '3000',
            'waers': 'USD',
            'industry': 'Nowe Technologie, SaaS & Usługi Cloud',
            'custom_z_notes': 'Auto-setup z raportu SPRO: Obszar 3000/10/02, fakturowanie subskrypcji i kontraktów WV.',
            'sales_area': {'vkorg': '3000', 'vtweg': '10', 'spart': '02', 'name': 'Sprzedaż licencji i subskrypcji'}
        }
    }
    
    if report_type in presets:
        cfg = presets[report_type]
        target_id = cfg['id']
        exists = get_company_profile(target_id)
        if exists:
            update_company_profile(target_id, cfg['name'], cfg['ktopl'], cfg['bukrs'], cfg['waers'], cfg['industry'], cfg['custom_z_notes'])
        else:
            create_company_profile(target_id, cfg['name'], cfg['ktopl'], cfg['bukrs'], cfg['waers'], cfg['industry'], cfg['custom_z_notes'])
        
        con = get_db_connection()
        sa = cfg['sales_area']
        con.execute("""
            INSERT OR REPLACE INTO sd_sales_areas (id, company_id, vkorg, vtweg, spart, name, waers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [f"{target_id}_{sa['vkorg']}_{sa['vtweg']}_{sa['spart']}", target_id, sa['vkorg'], sa['vtweg'], sa['spart'], sa['name'], cfg['waers']])
        
        set_active_company(target_id)
        profile = get_company_profile(target_id)
        return jsonify({
            'status': 'success',
            'message': f"Pomyślnie załadowano profil z raportu: {cfg['name']}",
            'profile': profile,
            'active_id': target_id
        })
    elif data.get('manual'):
        name = data.get('name', 'Nowa Firma').strip()
        ktopl = data.get('ktopl', 'INT').strip().upper()
        bukrs = data.get('bukrs', '1000').strip()
        waers = data.get('waers', 'EUR').strip().upper()
        vkorg = data.get('vkorg', '1000').strip()
        vtweg = data.get('vtweg', '10').strip()
        spart = data.get('spart', '00').strip()
        industry = data.get('industry', 'Ogólna').strip()
        target_id = company_id or 'CLIENT_A'
        
        exists = get_company_profile(target_id)
        if exists:
            update_company_profile(target_id, name, ktopl, bukrs, waers, industry, f"Obszar: {vkorg}/{vtweg}/{spart}")
        else:
            create_company_profile(target_id, name, ktopl, bukrs, waers, industry, f"Obszar: {vkorg}/{vtweg}/{spart}")
            
        con = get_db_connection()
        con.execute("""
            INSERT OR REPLACE INTO sd_sales_areas (id, company_id, vkorg, vtweg, spart, name, waers)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [f"{target_id}_{vkorg}_{vtweg}_{spart}", target_id, vkorg, vtweg, spart, f"Obszar {vkorg}", waers])
        
        set_active_company(target_id)
        profile = get_company_profile(target_id)
        return jsonify({
            'status': 'success',
            'message': f"Zapisano Master Data dla firmy: {name}",
            'profile': profile,
            'active_id': target_id
        })
    else:
        return jsonify({'status': 'error', 'message': 'Nieznany typ raportu'}), 400

@api_bp.route('/api/companies/delete', methods=['POST'])
def delete_company():
    """Usuwa profil klienta i kaskadowo czyści powiązane dane."""
    data = request.json or {}
    company_id = data.get('company_id', '').strip().upper()
    if not company_id:
        return jsonify({"status": "error", "message": "Brak company_id"}), 400

    success, message, new_active_id = delete_company_profile(company_id)
    if not success:
        return jsonify({"status": "error", "message": message}), 400

    new_profile = get_company_profile(new_active_id) if new_active_id else None
    return jsonify({
        "status": "success",
        "message": message,
        "new_active_id": new_active_id,
        "new_profile": new_profile
    })

# --- MASTER DATA GOVERNANCE (MDG) & CSV IMPORT / EXPORT ---

@api_bp.route('/api/mdg/healthcheck', methods=['GET'])
def get_mdg_healthcheck():
    """Przeprowadza pełny audyt MDG jakości danych podstawowych dla wybranej firmy."""
    company_id = request.args.get('company_id') or get_active_company_id()
    from app.services.mdg_service import MdgService
    audit_res = MdgService.audit_master_data(company_id)
    return jsonify(audit_res)

@api_bp.route('/api/mdg/import-csv', methods=['POST'])
def import_mdg_csv():
    """Importuje wsad CSV (Klienci, Dostawcy, Materiały) i aktualizuje profil MDG."""
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    data_type = data.get('data_type', '').strip().lower()
    csv_content = data.get('csv_content', '').strip()
    
    if not csv_content:
        return jsonify({"status": "error", "message": "Brak zawartości CSV do zaimportowania"}), 400
    if data_type not in ['customers', 'vendors', 'materials']:
        return jsonify({"status": "error", "message": "Niepoprawny typ danych (obsługiwane: customers, vendors, materials)"}), 400

    from app.services.mdg_service import MdgService
    res = MdgService.import_csv_data(csv_content, data_type, company_id)
    return jsonify(res)

@api_bp.route('/api/mdg/sample-csv/<data_type>', methods=['GET'])
def get_mdg_sample_csv(data_type):
    """Zwraca przykładowy szablon CSV dla danego typu danych."""
    from app.services.mdg_service import MdgService
    content = MdgService.get_sample_csv(data_type)
    if not content:
        return jsonify({"status": "error", "message": "Niepoprawny typ danych"}), 404
    return jsonify({"status": "success", "data_type": data_type, "csv_content": content})

@api_bp.route('/api/mdg/auto-fix', methods=['POST'])
def auto_fix_mdg():
    """Automatycznie naprawia luki w kartotekach Master Data i matrycy VKOA (1-Click Auto-Heal MDG)."""
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    category = data.get('category')
    from app.services.mdg_service import MdgService
    res = MdgService.auto_fix_master_data(company_id, category)
    return jsonify(res)

# --- PRICING PROCEDURE SIMULATOR (V/08 -> PRCD_ELEMENTS -> VKOA) ---

@api_bp.route('/api/pricing/context', methods=['GET'])
def get_pricing_context():
    """Zwraca listę klientów, materiałów i warunków cenowych dla symulatora V/08."""
    company_id = request.args.get('company_id') or get_active_company_id()
    from app.services.pricing_service import PricingSimulatorService
    res = PricingSimulatorService.get_pricing_context(company_id)
    return jsonify(res)

@api_bp.route('/api/pricing/simulate', methods=['POST'])
def simulate_pricing():
    """Symuluje kaskadę wyceny V/08 (PRCD_ELEMENTS) i weryfikuje determinację kont VKOA."""
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    kunnr = data.get('kunnr', '').strip()
    matnr = data.get('matnr', '').strip()
    quantity = float(data.get('quantity', 10.0) or 10.0)
    discount_pct = float(data.get('discount_pct', 5.0) or 0.0)
    freight_val = float(data.get('freight_val', 150.0) or 0.0)
    override_price = data.get('override_base_price')
    override_base_price = float(override_price) if override_price not in (None, '') else None

    from app.services.pricing_service import PricingSimulatorService
    res = PricingSimulatorService.simulate_pricing_procedure(
        company_id=company_id,
        kunnr=kunnr,
        matnr=matnr,
        quantity=quantity,
        discount_pct=discount_pct,
        freight_val=freight_val,
        override_base_price=override_base_price
    )
    return jsonify(res)

@api_bp.route('/api/sd-structures', methods=['GET'])
def get_sd_structures():
    """Pobiera komplet struktur SD dla aktywnej firmy (obszary, AUART, warunki, VKOA)."""
    company_id = request.args.get('company_id') or get_active_company_id()
    con = get_db_connection()

    profile = get_company_profile(company_id)
    sales_areas = con.execute(
        "SELECT id, vkorg, vtweg, spart, name, waers FROM sd_sales_areas WHERE company_id = ?",
        [company_id]
    ).fetchall()

    order_types = con.execute(
        "SELECT id, auart, bezeichnung, item_cat_group, default_item_cat, billing_type, notes FROM sd_order_types WHERE company_id = ?",
        [company_id]
    ).fetchall()

    pricing = con.execute(
        "SELECT id, kschl, condition_class, calc_type, description, account_key, access_seq, notes FROM sd_pricing_conditions WHERE company_id = ?",
        [company_id]
    ).fetchall()

    vkoa = con.execute(
        "SELECT id, table_num, ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl, saknr, description FROM sd_vkoa_rules WHERE company_id = ? ORDER BY table_num, kvsl",
        [company_id]
    ).fetchall()

    return jsonify({
        "company": profile,
        "sales_areas": [{"id": r[0], "vkorg": r[1], "vtweg": r[2], "spart": r[3], "name": r[4], "waers": r[5]} for r in sales_areas],
        "order_types": [{"id": r[0], "auart": r[1], "bezeichnung": r[2], "item_cat_group": r[3], "default_item_cat": r[4], "billing_type": r[5], "notes": r[6]} for r in order_types],
        "pricing_conditions": [{"id": r[0], "kschl": r[1], "condition_class": r[2], "calc_type": r[3], "description": r[4], "account_key": r[5], "access_seq": r[6], "notes": r[7]} for r in pricing],
        "vkoa_rules": [{"id": r[0], "table_num": r[1], "ktopl": r[2], "vkorg": r[3], "ktgrd_cust": r[4], "ktgrm_mat": r[5], "kvsl": r[6], "saknr": r[7], "description": r[8]} for r in vkoa]
    })

# --- VKOA ACCOUNT DETERMINATION TROUBLESHOOTER API ---

@api_bp.route('/api/vkoa/troubleshoot', methods=['POST'])
def troubleshoot_vkoa():
    """
    Główny endpoint modułu VKOA Troubleshooter:
    Przyjmuje tekst błędu z SAP lub bezpośrednie parametry.
    Wykonuje symulację sekwencji dostępu KOFI00 i zwraca pełną diagnozę oraz Quick-Fix.
    """
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    profile = get_company_profile(company_id)
    default_ktopl = profile.get('ktopl', 'INT')

    raw_error = data.get('raw_error', '').strip()

    # Jeśli podano ciąg tekstowy błędu -> parsujemy
    if raw_error:
        parsed = VkoaTroubleshooterService.parse_error_string(raw_error, default_ktopl=default_ktopl)
        ktopl = data.get('ktopl') or parsed['ktopl']
        vkorg = data.get('vkorg') or parsed['vkorg']
        ktgrd = data.get('ktgrd_cust') or parsed['ktgrd_cust']
        ktgrm = data.get('ktgrm_mat') or parsed['ktgrm_mat']
        kvsl = data.get('kvsl') or parsed['kvsl']
    else:
        ktopl = data.get('ktopl', default_ktopl).strip().upper()
        vkorg = data.get('vkorg', '1000').strip().upper()
        ktgrd = data.get('ktgrd_cust', '01').strip()
        ktgrm = data.get('ktgrm_mat', '01').strip()
        kvsl = data.get('kvsl', 'ERL').strip().upper()

    result = VkoaTroubleshooterService.simulate_account_determination(
        company_id=company_id,
        ktopl=ktopl,
        vkorg=vkorg,
        ktgrd_cust=ktgrd,
        ktgrm_mat=ktgrm,
        kvsl=kvsl
    )

    return jsonify(result)

@api_bp.route('/api/vkoa/quick-fix', methods=['POST'])
def quick_fix_vkoa():
    """Aplikuje 1-klikowy Quick-Fix do bazy aktywnej firmy i zwraca odświeżoną symulację."""
    data = request.json or {}
    result = VkoaTroubleshooterService.apply_quick_fix(data)
    return jsonify(result)

# --- SMART MEMORY API (IZOLACJA WG PROFILU) ---

@api_bp.route('/api/get-memory', methods=['GET'])
def get_memory():
    company_id = request.args.get('company_id') or get_active_company_id()
    memories = get_ai_memories(company_id=company_id, limit=100)
    return jsonify({
        "company_id": company_id,
        "memories": memories,
        "rules": [f"[{m['id']}] '{m['original_prompt']}' ➔ {m['corrected_output']}" for m in memories]
    })

@api_bp.route('/api/save-memory', methods=['POST'])
def save_memory():
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    prompt = data.get('prompt', '').strip()
    correction = data.get('correction', '').strip()
    category = data.get('category', 'GENERAL').strip()

    if not prompt or not correction:
        return jsonify({"status": "error", "message": "Wymagany prompt i treść korekty"}), 400

    mem_id = save_ai_memory(prompt, correction, company_id=company_id, category=category)
    return jsonify({"status": "success", "id": mem_id, "company_id": company_id})

# --- KATALOG PROCESÓW PRZEDSIĘBIORSTWA & DOCUMENT FLOW ---

@api_bp.route('/api/get-process-catalog', methods=['GET'])
def get_process_catalog():
    domain = request.args.get('domain')
    process_code = request.args.get('process_code')
    processes = get_available_processes(domain=domain)
    steps = get_sd_process_catalog(process_code=process_code, domain=domain)
    return jsonify({
        "status": "success",
        "processes": processes,
        "steps": steps,
        "count": len(steps)
    })

@api_bp.route('/api/processes/inferred', methods=['GET'])
def get_inferred_processes():
    """Zwraca wyniki autodetekcji procesów biznesowych SD dla wybranej firmy."""
    company_id = request.args.get('company_id') or get_active_company_id()
    from app.services.process_inference_service import ProcessInferenceService
    result = ProcessInferenceService.infer_company_processes(company_id)
    return jsonify({
        "status": "success",
        **result
    })

@api_bp.route('/api/document-flow/scenarios', methods=['GET'])
def get_flow_scenarios():
    company_id = request.args.get('company_id') or get_active_company_id()
    scenarios = get_available_scenarios(company_id=company_id)
    return jsonify({
        "status": "success",
        "company_id": company_id,
        "scenarios": scenarios
    })

@api_bp.route('/api/document-flow', methods=['GET'])
def get_document_flow():
    company_id = request.args.get('company_id') or get_active_company_id()
    scenario = request.args.get('scenario', 'vfx3_blocked').strip()
    flow = get_document_flow_scenarios(company_id=company_id, scenario=scenario)
    return jsonify({
        "status": "success",
        "company_id": company_id,
        "scenario": scenario,
        "flow": flow
    })

# --- CZAT / TRANSAKCJE ASYSTENTA ---

@api_bp.route('/api/process', methods=['POST'])
def process_command():
    data = request.json or {}
    user_prompt = data.get('prompt', '').strip()
    company_id = data.get('company_id') or get_active_company_id()

    if not user_prompt:
        return jsonify({"type": "guide", "content": "Wprowadź polecenie transakcyjne lub zapytanie doradcze."})

    result = TransactionService.process_text_input(user_prompt, company_id=company_id)
    return jsonify(result)

@api_bp.route('/api/batch-import', methods=['POST'])
def batch_import():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Brak pliku w żądaniu"}), 400

    file = request.files['file']
    company_id = request.form.get('company_id') or get_active_company_id()

    if not file or not file.filename:
        return jsonify({"status": "error", "message": "Nie wybrano pliku"}), 400

    try:
        count = TransactionService.process_batch_file(file, company_id=company_id)
        return jsonify({"status": "success", "count": count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/api/approve/<int:trans_id>', methods=['POST'])
def approve_transaction(trans_id):
    success = approve_export_transaction(trans_id)
    return jsonify({"status": "success" if success else "error"})

@api_bp.route('/api/export-lsmw', methods=['GET'])
def export_lsmw():
    company_id = request.args.get('company_id') or get_active_company_id()
    tsv_content = TransactionService.get_lsmw_export_content(company_id=company_id)
    return send_file(
        io.BytesIO(tsv_content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'SAP_SD_LSMW_{company_id}.txt'
    )

# --- KATALOG TRANSAKCJI SD (T-CODES) API ---

@api_bp.route('/api/tcodes', methods=['GET'])
def get_tcodes():
    """Wyszukiwanie i filtrowanie transakcji SAP SD."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    company_id = request.args.get('company_id') or get_active_company_id()
    limit = int(request.args.get('limit', 300))

    tcodes = get_sd_tcodes(query=query if query else None, category=category if category else None, company_id=company_id, limit=limit)
    return jsonify({
        "status": "success",
        "count": len(tcodes),
        "total": len(tcodes),
        "company_id": company_id,
        "tcodes": tcodes
    })

@api_bp.route('/api/tcodes/categories', methods=['GET'])
def get_tcodes_categories():
    """Zwraca dostępne kategorie transakcji wraz z liczbą kodów."""
    company_id = request.args.get('company_id') or get_active_company_id()
    cats = get_sd_tcode_categories(company_id=company_id)
    return jsonify({"status": "success", "categories": cats})

@api_bp.route('/api/tcodes/custom', methods=['POST'])
def add_custom_tcode():
    """Dodaje customową transakcję Z* dla wybranego klienta."""
    data = request.json or {}
    tcode = data.get('tcode', '').strip().upper()
    name = data.get('name', '').strip()
    category = data.get('category', 'CUSTOM_Z_CODES').strip()
    description = data.get('description', '').strip()
    tables = data.get('tables_involved', '').strip()
    spro_path = data.get('spro_path', '').strip()
    company_id = data.get('company_id') or get_active_company_id()

    if not tcode or not name or not description:
        return jsonify({"status": "error", "message": "T-Code, Nazwa i Opis są wymagane"}), 400

    add_custom_sd_tcode(tcode, name, category, description, tables, spro_path, company_id)
    return jsonify({"status": "success", "tcode": tcode, "company_id": company_id})

# --- INTELIGENCJA HANDLOWO-LOGISTYCZNA I PRÓBKI KORPORACYJNE (ENTERPRISE SAMPLES) ---

@api_bp.route('/api/profile/intelligence', methods=['GET'])
def get_profile_intelligence():
    """Zwraca pełny profil analityki komercyjnej, logistycznej oraz żargonu dla aktywnej firmy."""
    company_id = request.args.get('company_id') or get_active_company_id()
    from app.services.profile_intelligence_service import ProfileIntelligenceService
    report = ProfileIntelligenceService.get_full_intelligence_report(company_id)
    return jsonify(report)

@api_bp.route('/api/profile/seed-enterprise-samples', methods=['POST'])
def seed_enterprise_samples():
    """Generuje lub przeładowuje próbkę korporacyjną (3 500 VBAK/VBAP, 300 KNVV, 1 500 LIPS/VBRK, TVxx)."""
    data = request.json or {}
    company_id = data.get('company_id') or get_active_company_id()
    force = bool(data.get('force', False))
    from app.database.enterprise_samples import EnterpriseDataGenerator
    result = EnterpriseDataGenerator.seed_enterprise_dataset(company_id=company_id, force=force)
    return jsonify(result)

@api_bp.route('/api/profile/dictionaries', methods=['GET'])
def get_profile_dictionaries():
    """Zwraca słowniki konfiguracyjne TVAK/TVTW/TVBUR oraz specyficzny żargon firmy."""
    company_id = request.args.get('company_id') or get_active_company_id()
    from app.services.profile_intelligence_service import ProfileIntelligenceService
    jargon = ProfileIntelligenceService.get_jargon_dictionary(company_id)
    return jsonify({"status": "success", "company_id": company_id, **jargon})

@api_bp.route('/api/profile/orders', methods=['GET'])
def get_profile_orders():
    """Pobiera wycinek zleceń z tabeli sap_orders_vbak_vbap dla tabeli podglądu w UI."""
    company_id = request.args.get('company_id') or get_active_company_id()
    limit = int(request.args.get('limit', 50))
    pstyv = request.args.get('pstyv', '').strip()
    con = get_db_connection()
    
    query = """
        SELECT vbeln, posnr, erdat, auart, vkorg, vtweg, spart, kunnr, matnr, arktx, kwmeng, vrkme, netpr, netwr, waerk, pstyv
        FROM sap_orders_vbak_vbap
        WHERE company_id = ?
    """
    params = [company_id]
    if pstyv:
        query += " AND pstyv = ?"
        params.append(pstyv)
    query += " ORDER BY erdat DESC, vbeln DESC, posnr ASC LIMIT ?"
    params.append(limit)

    rows = con.execute(query, params).fetchall()
    orders = [
        {
            "vbeln": r[0], "posnr": r[1], "erdat": str(r[2]), "auart": r[3],
            "vkorg": r[4], "vtweg": r[5], "spart": r[6], "kunnr": r[7],
            "matnr": r[8], "arktx": r[9], "kwmeng": float(r[10] or 0),
            "vrkme": r[11], "netpr": float(r[12] or 0), "netwr": float(r[13] or 0),
            "waerk": r[14], "pstyv": r[15]
        }
        for r in rows
    ]
    return jsonify({"status": "success", "count": len(orders), "orders": orders})


