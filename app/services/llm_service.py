import re
import ollama
from app.config import Config
from app.database.db_manager import get_db_connection, get_active_company_id, get_company_profile
from app.services.entity_service import EntityService

def process_llm_query(user_prompt: str, company_id: str = None) -> str:
    """
    Główny silnik dialogowy asystenta konsultanta SAP SD.
    - 100% moduł SAP SD (Sales and Distribution)
    - Wstrzykiwanie kontekstu aktywnej firmy (Multi-Company Workspace)
    - Zero data leakage między profilami klientów
    - Dynamic Smart Memory RAG
    """
    if not company_id:
        company_id = get_active_company_id()

    con = get_db_connection()
    prompt_lower = user_prompt.lower().strip()
    profile = get_company_profile(company_id)

    # --- 0. SPRAWDZENIE SMART MEMORY (Izolacja wg aktywnego klienta) ---
    memory_match = con.execute("""
        SELECT corrected_output FROM ai_memory 
        WHERE company_id = ? AND LOWER(original_prompt) = ? 
        ORDER BY created_at DESC LIMIT 1
    """, [company_id, prompt_lower]).fetchone()
    
    if memory_match and memory_match[0]:
        return memory_match[0].strip()

    # --- 1. SPRAWDZENIE DIAGNOSTYKI BŁĘDÓW SAP SD (Root Cause, T-Codes, SPRO, Kroki naprawcze) ---
    from app.services.error_diagnosis_service import ErrorDiagnosisService
    error_diagnosis = ErrorDiagnosisService.diagnose_error(user_prompt, profile)
    if error_diagnosis:
        return error_diagnosis

    # --- 2. SZYBKA ŚCIEŻKA DLA DOKUMENTÓW SPRZEDAŻY SD (VA01) ---
    # Uruchamiana wyłącznie przy intencji utworzenia dokumentu, nie przy zapytaniach konsultingowych
    is_error_or_consulting = any(k in prompt_lower for k in [
        'błąd', 'blad', 'error', 'jak', 'dlaczego', 'gdzie', 'problem', 'konfiguracja',
        'tabela', 'spro', 'pomoc', 'analiza', 'status', 'schemat', 'determinacj', 'reguł'
    ])
    is_create_intent = (
        prompt_lower.startswith('va01') or
        any(prompt_lower.startswith(w) for w in [
            'utwórz zlecenie', 'utworz zlecenie', 'utwórz zamówienie', 'utworz zamówienie',
            'sprzedaj', 'dodaj zlecenie', 'wystaw zamówienie', 'nowe zlecenie'
        ]) or
        ('zlecenie' in prompt_lower and any(w in prompt_lower for w in ['sztuk', 'ilość', 'indeks', 'dla klienta', 'materiał']))
    )

    if is_create_intent and not is_error_or_consulting:
        qty = EntityService.extract_quantity(user_prompt, default=10.0)
        qty_str = str(int(qty)) if qty.is_integer() else str(qty)

        # Pobranie odpowiedniego AUART dla danej firmy
        order_types = con.execute(
            "SELECT auart, bezeichnung FROM sd_order_types WHERE company_id = ?",
            [company_id]
        ).fetchall()
        
        # Domyślny rodzaj zlecenia
        selected_auart = "TA"
        if order_types:
            # Jeśli w prompcie pojawia się specyficzny kod Z lub opis (np. ekspresowe, zor1, zexp)
            for ot in order_types:
                if ot[0].lower() in prompt_lower or any(w in prompt_lower for w in ot[1].lower().split() if len(w) > 4):
                    selected_auart = ot[0]
                    break
            else:
                selected_auart = order_types[0][0]

        mat = EntityService.find_material(user_prompt, company_id=company_id)
        if mat:
            matnr = mat['matnr']
            maktx = mat['maktx']
            mtart = mat['mtart']
            werks = mat['werks']
            meins = mat['meins']
        else:
            first_mat = con.execute(
                "SELECT matnr, maktx, mtart, werks, meins FROM sap_materials WHERE company_id = ? LIMIT 1",
                [company_id]
            ).fetchone()
            if first_mat:
                matnr, maktx, mtart, werks, meins = first_mat
            else:
                matnr = "SM-100"
                maktx = "Indeks materiałowy SD"
                mtart = "FERT"
                werks = "1000"
                meins = "SZT"

        return f"VA01;{matnr};{maktx};{mtart};{werks};{meins};{qty_str}"

    # --- 2. ŚCIEŻKA KONSULTANCKA SD (LLM + Dynamic RAG + Izolowany profil firmy) ---
    try:
        # Pobranie struktur SD aktywnego klienta
        sales_areas = con.execute(
            "SELECT vkorg, vtweg, spart, name FROM sd_sales_areas WHERE company_id = ?",
            [company_id]
        ).fetchall()
        
        order_types = con.execute(
            "SELECT auart, bezeichnung, default_item_cat, billing_type FROM sd_order_types WHERE company_id = ?",
            [company_id]
        ).fetchall()

        pricing_conds = con.execute(
            "SELECT kschl, description, account_key FROM sd_pricing_conditions WHERE company_id = ?",
            [company_id]
        ).fetchall()

        materials = con.execute(
            "SELECT matnr, maktx, mtart, ktgrm FROM sap_materials WHERE company_id = ?",
            [company_id]
        ).fetchall()

        customers = con.execute(
            "SELECT kunnr, name1, vkorg, ktgrd, land1 FROM sap_customers WHERE company_id = ?",
            [company_id]
        ).fetchall()

        vendors = con.execute(
            "SELECT lifnr, name1, partner_role, is_subcontractor FROM sap_vendors WHERE company_id = ?",
            [company_id]
        ).fetchall()

        # Pobranie wyuczonych reguł z pamięci tego klienta
        memory_rows = con.execute("""
            SELECT original_prompt, corrected_output FROM ai_memory 
            WHERE company_id = ? 
            ORDER BY created_at DESC LIMIT 5
        """, [company_id]).fetchall()

        memory_section = ""
        if memory_rows:
            rules_text = "\n".join([f"- Pytanie: \"{r[0]}\" -> Zapamiętana reguła: {r[1]}" for r in memory_rows])
            memory_section = f"\nZAPAMIĘTANE WYUCZONE REGUŁY KONSULTANTA DLA TEJ FIRMY:\n{rules_text}\n"

        # Dynamiczne dobranie relewantnych T-Codes z pełnej biblioteki 200+ transakcji
        from app.services.tcode_service import TCodeService
        relevant_tcodes = TCodeService.get_relevant_tcodes_for_prompt(user_prompt, company_id=company_id)
        tcodes_section = TCodeService.format_tcodes_for_system_prompt(relevant_tcodes)

        # Autodystrybucja i wnioskowanie procesów klienta (Auto-Discovery Engine)
        from app.services.process_inference_service import ProcessInferenceService
        inferred = ProcessInferenceService.infer_company_processes(company_id)
        active_inferred = [f"{p['title']} [{p['process_code']}] (Pewność: {p['confidence_score']}%, Dowód: {p['evidence'][0] if p['evidence'] else 'Konfiguracja profilu'})" for p in inferred.get('processes', []) if p['is_active']]
        inferred_section = f"""
AUTOMATYCZNIE WYKRYTE PROCESY BIZNESOWE Z KARTOTEK SAP:
- Domena główna: {inferred.get('primary_domain')}
- Zidentyfikowane procesy:
  {chr(10).join(['  • ' + pr for pr in active_inferred])}
"""

        # Inteligencja handlowo-logistyczna zasilana z VBAK, KNVV, LIPS, TVxx
        from app.services.profile_intelligence_service import ProfileIntelligenceService
        profile_intelligence_section = ProfileIntelligenceService.format_intelligence_for_llm(company_id)

        system_prompt = f"""
Jesteś elitarnym Senior Konsultantem i Architektem Rozwiązań SAP SD (Sales and Distribution).
Wspierasz konsultanta wdrożeniowego lub serwisowego w codziennych zadaniach na systemie S/4HANA & ECC.
Odpowiadasz WYŁĄCZNIE w zakresie modułu SAP SD: Order-to-Cash (O2C), ustalanie rodzajów zleceń AUART, 
kategorie pozycji VOV4, linie harmonogramu VOV6, sterowanie kopiowaniem VTLA/VTFL, technika warunków cenowych (schemat kalkulacyjny, KSCHL, reguły dostępu), 
fakturowanie VF01/VF02, determinacja kont przychodów VKOA (KOFI/KOFN) oraz procesy specjalne: TAS, MTO, Konsygnacja, Intercompany, RRB, Podwykonawstwo.

AKTYWNY PROFIL KLIENTA:
- Nazwa: {profile.get('name')} (ID: {company_id})
- Plan kont (KTOPL): {profile.get('ktopl')}
- Jednostka gospodarcza (BUKRS): {profile.get('bukrs')}
- Waluta systemowa: {profile.get('waers')}
- Notatki / Kody Z* klienta: {profile.get('custom_z_notes')}
- Obszary sprzedaży (VKORG/VTWEG/SPART): {sales_areas}
- Rodzaje zleceń sprzedaży (AUART): {order_types}
- Warunki cenowe (KSCHL): {pricing_conds}
- Dostępne materiały i grupy rozliczeniowe (KTGRM): {materials}
- Kartoteki klientów (KNA1/KNVV): {customers}
- Dostawcy i podwykonawcy (LFA1/LFM1): {vendors}
{profile_intelligence_section}
{inferred_section}
{memory_section}
{tcodes_section}

ZASADY ODPOWIEDZI:
1. Twoja odpowiedź konsultacyjna MUSI zaczynać się od tagu [GUIDE].
2. Odwołuj się do konkretnych transakcji SAP (np. SPRO, VA01, VF01, VF02, VKOA, VK11, VOV8, VOV4, BP, MM02, SE16N).
3. Podawaj precyzyjne tabele systemowe (VBAK, VBAP, VBRK, VBRP, KNA1, KNVV, LFA1, LFM1, EINE, MARA, MVKE, MARC).
4. Wykorzystuj wiedzę o automatycznie wykrytych procesach firmy (np. jeśli wykryto TAS lub MTO, uwzględniaj to w odpowiedzi).
5. Nigdy nie mieszaj danych innych firm – pracujesz wyłącznie na strukturach podanego klienta.
"""

        response = ollama.chat(
            model=Config.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            options={'num_predict': 400, 'temperature': 0.1}
        )

        return response['message']['content'].strip()

    except Exception:
        # Inteligentny tryb ekspercki (Fallback offline dla konsultanta SD)
        client_name = profile.get('name', company_id)
        ktopl = profile.get('ktopl', 'INT')
        
        # Wykrywanie tematów SD
        if any(k in prompt_lower for k in ['vkoa', 'księgowan', 'vf067', 'konto', 'przychod']):
            return (
                f"[GUIDE] **Ekspert SAP SD (Determiancja Kont VKOA - {client_name})**:\n"
                f"W strukturze aktywnego klienta plan kont to **{ktopl}**.\n"
                "• **Transakcja ustalania kont**: `VKOA` (lub SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Ustalanie kont -> Konta przychodów).\n"
                "• **Kluczowa sekwencja dostępu**: `KOFI00` (aplikacja `V`, rodzaj warunku `KOFI`).\n"
                "• **Kolejność weryfikacji tabel**:\n"
                "  1. Tabela 001: KTOPL + VKORG + KTGRD (Odbiorca KNVV) + KTGRM (Materiał MVKE) + Klucz konta (np. ERL)\n"
                "  2. Tabela 002: KTOPL + KTGRD + Klucz konta\n"
                "  3. Tabela 003: KTOPL + KTGRM + Klucz konta\n"
                "  4. Tabela 005: KTOPL + VKORG + Klucz konta\n"
                "  5. Tabela 004: KTOPL + Klucz konta (ogólny fallback)\n"
                "💡 Skorzystaj z dedykowanej zakładki **„🩺 VKOA Troubleshooter”**, aby automatycznie przeanalizować błąd faktury z VF01/VF02 i naprawić brakujący wpis jednym kliknięciem!"
            )
        elif any(k in prompt_lower for k in ['auart', 'rodzaj zlecen', 'typ zlecen', 'zor1', 'zexp']):
            z_notes = profile.get('custom_z_notes', '')
            return (
                f"[GUIDE] **Ekspert SAP SD (Rodzaje Zleceń AUART - {client_name})**:\n"
                f"W profilu klienta **{client_name}** skonfigurowane są specyficzne procesy sprzedażowe.\n"
                f"• **Notatki konfiguracyjne Z***: {z_notes}\n"
                "• **Transakcje konfiguracji SD**:\n"
                "  - `VOV8`: Definicja rodzaju zlecenia sprzedaży (AUART, blokady, schemat kalkulacji, profil dostawy)\n"
                "  - `VOV4`: Przypisanie kategorii pozycji (Rodzaj zlecenia + Grupa kat. pozycji NORM/BANS + Zastosowanie -> Kategoria PSTYV TAN/ZTAN)\n"
                "  - `VOV7`: Parametryzacja kategorii pozycji (kontrola fakturowania, ATP, wycena)"
            )
        elif any(k in prompt_lower for k in ['warunk', 'cenow', 'pr00', 'zpr1', 'k004', 'schemat']):
            return (
                f"[GUIDE] **Ekspert SAP SD (Technika Warunków Cenowych - {client_name})**:\n"
                f"Dla klienta **{client_name}** (waluta: {profile.get('waers')}):\n"
                "• **Podstawowe transakcje**:\n"
                "  - `V/08`: Definicja schematu kalkulacyjnego (Pricing Procedure, np. RVAA01)\n"
                "  - `V/06`: Definicja rodzajów warunków (Condition Types: PR00, rabaty K004/K007, narzuty KF00, podatki MWST)\n"
                "  - `VK11 / VK12 / VK13`: Utrzymanie rekordów warunków w tabelach kondycyjnych\n"
                "• **Przepływ do FI**: Warunki przychodowe mają przypisany klucz konta `ERL`, rabaty `ERS`, a podatek VAT `MWS`, co steruje późniejszą determinacją kont w `VKOA`."
            )
        elif any(k in prompt_lower for k in ['mdg', 'master data', 'dane podstawow', 'eksport', 'csv', 'tabel', 'partner', 'dostawc', 'podwykonawc', 'klient', 'profil firm']):
            return (
                f"[GUIDE] **Architektura Master Data Governance (MDG) i Profilowania Partnerów SAP ({client_name})**:\n\n"
                "Aby Copilot mógł bezbłędnie symulować procesy Order-to-Cash, diagnozować blokady fakturowania (`VF067`), determinację podatków (`FF704`) oraz sterować zaopatrzeniem i podwykonawstwem, profil firmy opiera się na **4 kluczowych filarach danych z SAP**:\n\n"
                "### 1. Klienci i Odbiorcy (Customer Master)\n"
                "• **Tabele SAP**: `KNA1` (dane ogólne: NIP/STCEG, kraj LAND1), `KNVV` (sprzedaż: VKORG, VTWEG, SPART, **KTGRD** do VKOA, warunki płatności ZTERM, Incoterms INCO1/INCO2, zakład dostarczający VWERK), `KNVI` (klasyfikacja podatkowa TAXKD).\n"
                "• **Skąd pobrać z SAP**: Transakcje `VCUST`, `XD03` / `BP` (S/4HANA), eksport `SE16N` z tabel `KNA1`/`KNVV` do pliku CSV (separator `;`).\n"
                "• **Rola w Copilocie**: Brak `KTGRD` natychmiast blokuje fakturę w FI (`VF067`), a brak `TAXKD` uniemożliwia naliczenie VAT (`MWST`/`FF704`).\n\n"
                "### 2. Dostawcy, Podwykonawcy i Spedytorzy (Vendor & Partner Profiling)\n"
                "• **Tabele SAP**: `LFA1` (dane ogólne dostawcy), `LFM1` (dane działu zakupów: EKORG, waluta WAERS, ZTERM), `EINE` (rekord informacyjny zaopatrzenia - typ infopomocniczego `PIR` dla podwykonawstwa infotyp 3), `BUT000` (Business Partner w S/4HANA: role `FLVN00`/`FLVN01`, `BUP003`).\n"
                "• **Skąd pobrać z SAP**: Transakcje `MK03`, `XK03`, `BP`, `ME1M`/`ME1L` (podwykonawstwo), eksport `SE16N` z tabel `LFA1` i `LFM1`.\n"
                "• **Rola w Copilocie**: Odróżnienie zwykłego dostawcy od **podwykonawcy uszlachetniania** (sterowanie ruchem materiałowym 541 w MIGO oraz pozycjami `BANS` w zleceniu SD) oraz **spedytora frachtowego** (rola `SPED`, sterowanie warunkiem frachtu `KF00`).\n\n"
                "### 3. Materiały i Indeksy Sprzedażowe (Material Master)\n"
                "• **Tabele SAP**: `MARA` (dane ogólne), `MAKT` (nazwy), `MVKE` (dane sprzedaży: **KTGRM** do VKOA, grupa typów pozycji **MTPOS** sterująca pozycją TAN/ZTAN/BANS/LEIS), `MARC` (zakład: grupa kontroli ATP **MTVFP**).\n"
                "• **Skąd pobrać z SAP**: Raport `MM60` (Katalog materiałów z zakładami i wyceną), transakcja `MM03`, eksport `SE16N` z `MVKE`/`MARA`.\n"
                "• **Rola w Copilocie**: Brak `KTGRM` uniemożliwia wywołanie procedury `KOFI00` (błąd `VF067`), a brak `MTVFP` uniemożliwia kontrolę dostępności w `CO09` (błąd `M7021`).\n\n"
                "### 4. Struktura Organizacyjna i Reguły VKOA\n"
                "• **Tabele SAP**: `T001` (BUKRS), `T004` (KTOPL), `TVKO`/`TVTW`/`TVSPA` (Obszary sprzedaży), `C001`-`C005` (tabele kondycyjne determinacji kont VKOA).\n"
                "• **Skąd pobrać z SAP**: Raport kopiowania jednostki gospodarczej `EC01`, transakcja `VKOA`.\n\n"
                "💡 **Wskazówka**: Otwórz po zalogowaniu panel **„⚙️ Master Data & Profil”** – możesz tam załadować gotowe presety z raportów `EC01`/`VKOA`, sprawdzić wskaźnik jakości danych **Data Quality Score** lub wkleić bezpośredni eksport CSV z SAP!"
            )
        elif any(k in prompt_lower for k in ['profil handlow', 'profil komercyjn', 'asortyment', 'wolumen', 'skala transakcji', 'lead time', 'żargon', 'z-order', 'knvv', 'vbak', 'lips', 'vbrk', 'próbk']):
            from app.services.profile_intelligence_service import ProfileIntelligenceService
            intel = ProfileIntelligenceService.get_full_intelligence_report(company_id)
            comm = intel.get('commercial', {})
            port = intel.get('portfolio', {})
            log = intel.get('logistics', {})
            jargon = intel.get('jargon', {})

            bullets = "\n".join([f"• {b}" for b in intel.get('summary_bullets', [])])
            top_prods = "\n".join([f"  - `{p['matnr']}`: {p['name']} ({p.get('orders_cnt', 0)} pozycji, obrót: {p['turnover']:,.2f} PLN)" for p in comm.get('top_products', [])[:4]])
            z_jargon_lines = "\n".join([f"  - `{z['dict_type']}` `{z['code']}`: **{z['name']}** ➔ Znaczenie: *{z['business_meaning']}*" for z in jargon.get('z_codes', [])[:5]])

            return (
                f"[GUIDE] **Raport Inteligencji Handlowo-Logistycznej ({client_name})**:\n\n"
                f"{bullets}\n\n"
                f"### 📦 Kluczowy Asortyment Handlowy (VBAK + VBAP):\n{top_prods}\n\n"
                f"### 🚚 Logistyka i Realizacja (LIPS + VBRK):\n"
                f"• **Średni czas od zlecenia do PGI**: {log.get('avg_lead_time_days', 0)} dni\n"
                f"• **Główne punkty wysyłki (VSTEL)**: {', '.join([sp.get('code', '') for sp in log.get('shipping_points', [])])}\n"
                f"• **Kluczowe trasy logistyczne**: {', '.join([r.get('code', '') for r in log.get('routes', [])[:4]])}\n\n"
                f"### 🏢 Słownik Żargonu Konfiguracyjnego (TVAK/TVTW/TVBUR):\n{z_jargon_lines or 'Brak zarejestrowanych specyficznych kodów Z*'}\n\n"
                "💡 Pełny podgląd i możliwość przeładowania 3 500 pozycji danych korporacyjnych znajdziesz w panelu **„⚙️ Master Data & Profil”**."
            )
        elif any(k in prompt_lower for k in ['tas', 'trojststronn', 'trójstronn', 'dropship', 'dostawa bezposredn', 'dostawa bezpośredn']):
            return (
                f"[GUIDE] **Ekspert Procesów Handlowych (Handel Trójstronny / Dropshipping TAS - {client_name})**:\n"
                "Proces dostawy bezpośredniej od dostawcy do klienta bez składowania w magazynie własnym:\n"
                "1. **Zlecenie sprzedaży (VA01)**: Pozycja z kategorią **`TAS`** (Third-party item) oraz kategorią linii harmonogramu **`CS`**.\n"
                "2. **Automatyczny Banf (EBAN)**: System natychmiast generuje pozycję zapotrzebowania zakupowego (typ przypisania konta 'X', typ pozycji 'S').\n"
                "3. **Zamówienie zakupu (ME21N / ME59N)**: Zamówienie u dostawcy z adresem doręczenia klienta docelowego (Ship-to).\n"
                "4. **Dostawa i faktura dostawcy (MIRO)**: Wprowadzenie faktury zakupu w MIRO odblokowuje fakturowanie klienta.\n"
                "5. **Faktura dla klienta (VF01)**: Wystawienie faktury F2 opartej na zleceniu lub dostawie zewnętrznej.\n"
                "💡 Zobacz pełny przebieg w zakładce **„🔄 Procesy & Document Flow”** (scenariusz: *Handel trójstronny TAS*)."
            )
        elif any(k in prompt_lower for k in ['mto', 'make-to-order', 'make to order', 'produkcja pod zlecenie', 'zapas e']):
            return (
                f"[GUIDE] **Ekspert Procesów Produkcyjnych (Make-to-Order MTO - {client_name})**:\n"
                "Proces produkcji jednostkowej lub konfigurowalnej ściśle powiązanej ze zleceniem sprzedaży:\n"
                "1. **Zlecenie sprzedaży MTO (VA01)**: Kategoria pozycji **`TAK`** (lub `TAC` dla konfigurowalnych). Przypisanie klasy zapotrzebowań **040** (`OVZG`).\n"
                "2. **Kalkulacja zlecenia (CK51N / VA02)**: Kalkulacja jednostkowa kosztu wytworzenia wyrobu na nośnik kosztów zlecenia.\n"
                "3. **Zlecenie produkcyjne (CO01 / MD04)**: Utworzenie zlecenia produkcyjnego z przypisaniem do zlecenia sprzedaży (`AUFNR -> VBELN/POSNR`).\n"
                "4. **Przyjęcie wyrobu (MIGO ruch 101 E)**: Przyjęcie wyrobu gotowego na zapas specjalny **'E'** (tabela `MSKA`).\n"
                "5. **Dostawa i PGI (VL01N / VL02N ruch 601 E)**: Wydanie ze składu dedykowanego pod dane zlecenie.\n"
                "6. **Rozliczenie do CO-PA (VA88 / KGI2)**: Przeniesienie rzeczywistych odchyleń produkcyjnych i marży do rachunku wyników.\n"
                "💡 Zobacz pełny przebieg w zakładce **„🔄 Procesy & Document Flow”** (scenariusz: *Produkcja MTO*)."
            )
        elif any(k in prompt_lower for k in ['konsygnacj', 'consign', 'zapas w', 'kb', 'ke', 'ka', 'kr']):
            return (
                f"[GUIDE] **Ekspert Gospodarki Konsygnacyjnej (Consignment Processing - {client_name})**:\n"
                "4-etapowy proces zarządzania depozytem u klienta (zapas specjalny **'W'** w tabeli `MSKU`):\n"
                "• **KB (Consignment Fill-up)**: Uzupełnienie depozytu. Dostawa LF ruchem **631**. Towar pozostaje własnością sprzedawcy. Brak faktury.\n"
                "• **KE (Consignment Issue)**: Pobranie i zużycie przez klienta. Rozchód ruchem **633** z zapasu W. Standardowa faktura handlowa **F2**.\n"
                "• **KR (Consignment Returns)**: Zwrot na skład konsygnacyjny ruchem **634**. Generuje fakturę korygującą **G2**.\n"
                "• **KA (Consignment Pick-up)**: Wycofanie niesprzedanego zapasu do magazynu własnego ruchem **632**. Brak faktury.\n"
                "💡 Zobacz pełny przebieg w zakładce **„🔄 Procesy & Document Flow”** (scenariusz: *Konsygnacja u klienta*)."
            )
        elif any(k in prompt_lower for k in ['intercompany', 'miedzyfirmow', 'międzyfirmow', 'iv', 'pi01', 'pi02', 'cross company', 'cross-company']):
            return (
                f"[GUIDE] **Ekspert Sprzedaży Międzyfirmowej (Intercompany Billing - {client_name})**:\n"
                "Sprzedaż z jednostki handlowej (Spółka A) z fizyczną wysyłką z zakładu spółki powiązanej (Spółka B):\n"
                "1. **Zlecenie w Spółce A (VA01)**: Org. sprzedaży 1000, ale Zakład dostarczający 2000 (należący do BUKRS 2000).\n"
                "2. **Dostawa i PGI (VL01N / VL02N)**: Realizacja w punkcie wysyłki zakładu 2000. Ruch 601 obciąża COGS w Spółce B.\n"
                "3. **Faktura dla klienta (VF01 typ F2)**: Wystawiana przez Spółkę A na kwotę rynkową dla odbiorcy docelowego.\n"
                "4. **Faktura wewnętrzna (VF01 typ IV)**: Wystawiana przez Spółkę B dla Spółki A wg cen transferowych (**PI01** kwotowy / **PI02** procentowy).\n"
                "5. **Automatyczne księgowanie AP (EDI IDoc RD04)**: Zamknięcie rozrachunków w Spółce A jako faktura dostawcy.\n"
                "💡 Zobacz pełny przebieg w zakładce **„🔄 Procesy & Document Flow”** (scenariusz: *Sprzedaż międzyfirmowa*)."
            )
        elif any(k in prompt_lower for k in ['rrb', 'dp90', 'uslugi nakladcz', 'usługi nakładcz', 'dip', 'time and material']):
            return (
                f"[GUIDE] **Ekspert Fakturowania Usług Nakładczych (Resource-Related Billing RRB - {client_name})**:\n"
                "Rozliczanie rzeczywistych godzin i kosztów w projektach i serwisie (Time & Material):\n"
                "1. **Obiekt kosztowy (IW31 / CJ20N)**: Zlecenie serwisowe lub element WBS z przypisanym profilem DIP (`ODP1`).\n"
                "2. **Ewidencja nakładów (CAT2 / KB21N)**: Zarejestrowanie roboczogodzin w CATS i kosztów rzeczywistych w CO.\n"
                "3. **Przetwarzanie pozycji dynamicznych (DP90)**: Odczyt kosztów, zastosowanie cennika i kalkulacja kwoty do zafakturowania.\n"
                "4. **Żądanie rozliczenia DMR (VA01 / DP90)**: Wygenerowanie dokumentu sprzedaży typu Debit Memo Request (pozycja `TAD`/`DIEN`).\n"
                "5. **Faktura za usługi (VF01 typ L2)**: Wystawienie faktury końcowej dla klienta i zaksięgowanie przychodów w FI.\n"
                "💡 Zobacz pełny przebieg w zakładce **„🔄 Procesy & Document Flow”** (scenariusz: *Usługi nakładcze DP90*)."
            )
        else:
            from app.services.tcode_service import TCodeService
            matched_tcodes = TCodeService.get_relevant_tcodes_for_prompt(user_prompt, company_id=company_id)
            tcode_hints = ""
            if matched_tcodes:
                tcode_list = "\n".join([f"  • `{tc['tcode']}` - **{tc['description']}** (Obszar: {tc['category']})" for tc in matched_tcodes[:4]])
                tcode_hints = f"\n\n🔍 **Sugerowane transakcje SAP dla Twojego zapytania**:\n{tcode_list}"

            return (
                f"[GUIDE] **Konsultant SAP SD ({client_name})**: Analizuję zapytanie w kontekście modułu Sales and Distribution dla profilu **{client_name}** (Plan kont: `{ktopl}`, BUKRS: `{profile.get('bukrs')}`)."
                f"{tcode_hints}\n\n"
                "💡 **W czym jeszcze mogę pomóc?**\n"
                "1. **Diagnoza błędów SD** (podaj kod błędu np. `VF067`, `V1382`, `VL150`, `FF704`, `M7021`, `V4001` lub opisz problem)\n"
                "2. **Determiancja kont VKOA i błędy fakturowania** (skorzystaj też z zakładki *🩺 VKOA Troubleshooter*)\n"
                "3. **Technika warunków cenowych** (schematy kalkulacyjne V/08, rodzaje warunków V/06, rekordy cenowe VK11)\n"
                "4. **Rodzaje zleceń sprzedaży AUART i kategorie pozycji** (VOV8, VOV4, VOV7)\n"
                "5. **Weryfikacja procesu Order-to-Cash** (zakładka *Przepływ Dokumentów* z podglądem łańcucha O2C)"
            )
