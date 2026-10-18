import os
import duckdb
from app.config import Config

_con = None

def get_db_connection():
    global _con
    if _con is None:
        db_path = Config.DB_PATH
        if db_path != ':memory:':
            dirname = os.path.dirname(db_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
        _con = duckdb.connect(database=db_path, read_only=False)
    return _con

def init_db():
    con = get_db_connection()

    # 1. Profile firm (Multi-Company Workspace)
    con.execute("""
        CREATE TABLE IF NOT EXISTS company_profiles (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            ktopl VARCHAR NOT NULL,
            bukrs VARCHAR NOT NULL,
            waers VARCHAR NOT NULL,
            industry VARCHAR,
            custom_z_notes VARCHAR,
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Obszary sprzedaży SAP SD (VKORG / VTWEG / SPART)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_sales_areas (
            id VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            vkorg VARCHAR NOT NULL,
            vtweg VARCHAR NOT NULL,
            spart VARCHAR NOT NULL,
            name VARCHAR,
            waers VARCHAR DEFAULT 'EUR',
            FOREIGN KEY (company_id) REFERENCES company_profiles(id)
        )
    """)

    # 3. Rodzaje zleceń sprzedaży SAP SD (AUART)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_order_types (
            id VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            auart VARCHAR NOT NULL,
            bezeichnung VARCHAR NOT NULL,
            item_cat_group VARCHAR DEFAULT 'NORM',
            default_item_cat VARCHAR DEFAULT 'TAN',
            billing_type VARCHAR DEFAULT 'F2',
            notes VARCHAR,
            FOREIGN KEY (company_id) REFERENCES company_profiles(id)
        )
    """)

    # 4. Technika warunków cenowych SAP SD (KSCHL / Condition Technique)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_pricing_conditions (
            id VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            kschl VARCHAR NOT NULL,
            condition_class VARCHAR NOT NULL,
            calc_type VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            account_key VARCHAR,
            access_seq VARCHAR,
            notes VARCHAR,
            FOREIGN KEY (company_id) REFERENCES company_profiles(id)
        )
    """)

    # 5. Ustalanie kont przychodów SAP SD (VKOA Rules - Access Tables 001-005)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_vkoa_rules (
            id VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            appl VARCHAR DEFAULT 'V',
            kschl VARCHAR DEFAULT 'KOFI',
            table_num VARCHAR NOT NULL,
            ktopl VARCHAR NOT NULL,
            vkorg VARCHAR,
            ktgrd_cust VARCHAR,
            ktgrm_mat VARCHAR,
            kvsl VARCHAR NOT NULL,
            saknr VARCHAR NOT NULL,
            hkont_accrual VARCHAR,
            description VARCHAR,
            FOREIGN KEY (company_id) REFERENCES company_profiles(id)
        )
    """)

    # 6. Materiały SAP SD (z widokiem sprzedaży MVKE: KTGRM, MTPOS, TAXM1 oraz zakładu MARC: MTVFP)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_materials (
            matnr VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            maktx VARCHAR,
            mtart VARCHAR,
            werks VARCHAR,
            meins VARCHAR,
            stprs DECIMAL(12,2),
            ktgrm VARCHAR DEFAULT '01',
            mtpos VARCHAR DEFAULT 'NORM',
            mtvfp VARCHAR DEFAULT '01',
            taxm1 VARCHAR DEFAULT '1'
        )
    """)

    # 7. Klienci SAP SD (z danymi sprzedaży KNVV: KTGRD)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_customers (
            kunnr VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            name1 VARCHAR,
            vkorg VARCHAR,
            vtweg VARCHAR,
            spart VARCHAR,
            ktgrd VARCHAR DEFAULT '01',
            credit_limit DECIMAL(15,2),
            current_exposure DECIMAL(15,2),
            land1 VARCHAR DEFAULT 'PL',
            stceg VARCHAR,
            zterm VARCHAR DEFAULT 'NT30',
            inco1 VARCHAR DEFAULT 'DAP',
            inco2 VARCHAR,
            vwerk VARCHAR,
            taxkd VARCHAR DEFAULT '1'
        )
    """)

    # 7b. Dostawcy, Podwykonawcy i Spedytorzy (LFA1 / LFM1 / BUT000)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_vendors (
            lifnr VARCHAR PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            name1 VARCHAR,
            land1 VARCHAR DEFAULT 'PL',
            stceg VARCHAR,
            ekorg VARCHAR,
            bukrs VARCHAR,
            waers VARCHAR DEFAULT 'EUR',
            zterm VARCHAR DEFAULT 'NT30',
            partner_role VARCHAR DEFAULT 'LF',
            is_subcontractor BOOLEAN DEFAULT FALSE,
            notes VARCHAR,
            FOREIGN KEY (company_id) REFERENCES company_profiles(id)
        )
    """)

    # 8. Stany magazynowe ATP
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_stock (
            matnr VARCHAR,
            werks VARCHAR,
            labst DECIMAL(12,2),
            meins VARCHAR,
            PRIMARY KEY (matnr, werks)
        )
    """)

    # 9. Katalog kroków procesowych (Enterprise Processes: Produkcja, Handel, Usługi, Reklamacje)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_process_catalog (
            id INTEGER PRIMARY KEY,
            process_code VARCHAR NOT NULL,
            process_name VARCHAR NOT NULL,
            business_domain VARCHAR NOT NULL,
            step_order INTEGER NOT NULL,
            phase VARCHAR NOT NULL,
            tcode VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            prerequisites VARCHAR,
            tables_involved VARCHAR,
            doc_type VARCHAR,
            module VARCHAR
        )
    """)

    # 10. Bufor transakcji eksportowych / symulacji
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_export (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR,
            tcode VARCHAR,
            matnr VARCHAR,
            maktx VARCHAR,
            mtart VARCHAR,
            werks VARCHAR,
            meins VARCHAR,
            menge VARCHAR,
            status VARCHAR DEFAULT 'NEW',
            notes VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 11. Izolowana pamięć AI (Smart Memory z podziałem na Company ID)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ai_memory (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            category VARCHAR DEFAULT 'GENERAL',
            original_prompt VARCHAR NOT NULL,
            corrected_output VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 12. Kompletny katalog transakcji SAP SD (T-Codes Library)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sd_tcodes_catalog (
            tcode VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            description VARCHAR NOT NULL,
            tables_involved VARCHAR,
            spro_path VARCHAR,
            is_custom_z BOOLEAN DEFAULT FALSE,
            company_id VARCHAR
        )
    """)

    # 13. Nagłówki i pozycje zleceń sprzedaży (VBAK + VBAP)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_orders_vbak_vbap (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            vbeln VARCHAR NOT NULL,
            posnr INTEGER NOT NULL,
            erdat DATE NOT NULL,
            auart VARCHAR NOT NULL,
            vkorg VARCHAR NOT NULL,
            vtweg VARCHAR NOT NULL,
            spart VARCHAR NOT NULL,
            kunnr VARCHAR NOT NULL,
            matnr VARCHAR NOT NULL,
            arktx VARCHAR,
            kwmeng DECIMAL(15,3),
            vrkme VARCHAR DEFAULT 'SZT',
            netpr DECIMAL(15,2),
            netwr DECIMAL(15,2),
            waerk VARCHAR DEFAULT 'PLN',
            pstyv VARCHAR DEFAULT 'TAN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 14. Przepływ realizacji i logistyka (LIPS + VBRK)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_flow_lips_vbrk (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            vbeln_order VARCHAR NOT NULL,
            posnr_order INTEGER NOT NULL,
            vbeln_deliv VARCHAR,
            posnr_deliv INTEGER,
            lfart VARCHAR DEFAULT 'LF',
            vstel VARCHAR DEFAULT '1000',
            route VARCHAR DEFAULT 'PL0001',
            erdat_deliv DATE,
            vbeln_bill VARCHAR,
            posnr_bill INTEGER,
            fkart VARCHAR DEFAULT 'F2',
            fktyp VARCHAR DEFAULT 'L',
            waerk VARCHAR DEFAULT 'PLN',
            kurrf DECIMAL(9,5) DEFAULT 1.0,
            erdat_bill DATE,
            netwr_bill DECIMAL(15,2),
            lead_time_days INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 15. Słowniki konfiguracyjne i żargon firmy (TVAK, TVTW, TVBUR, TVKO)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sap_dictionaries_tvxx (
            id INTEGER PRIMARY KEY,
            company_id VARCHAR NOT NULL,
            dict_type VARCHAR NOT NULL,
            code VARCHAR NOT NULL,
            bezeichnung VARCHAR NOT NULL,
            business_meaning VARCHAR,
            notes VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- ZASILENIE DANYMI POCZĄTKOWYMI (SEED DATA) ---
    seed_initial_data(con)

def seed_initial_data(con):
    # Migracja kolumn dla istniejących baz danych
    for col, col_def in [
        ('mtpos', "VARCHAR DEFAULT 'NORM'"),
        ('mtvfp', "VARCHAR DEFAULT '01'"),
        ('taxm1', "VARCHAR DEFAULT '1'")
    ]:
        try:
            con.execute(f"ALTER TABLE sap_materials ADD COLUMN {col} {col_def}")
        except Exception:
            pass

    for col, col_def in [
        ('land1', "VARCHAR DEFAULT 'PL'"),
        ('stceg', "VARCHAR DEFAULT ''"),
        ('zterm', "VARCHAR DEFAULT 'NT30'"),
        ('inco1', "VARCHAR DEFAULT 'DAP'"),
        ('inco2', "VARCHAR DEFAULT ''"),
        ('vwerk', "VARCHAR DEFAULT '1000'"),
        ('taxkd', "VARCHAR DEFAULT '1'"),
        ('kdgrp', "VARCHAR DEFAULT '01'"),
        ('bzirk', "VARCHAR DEFAULT 'PL01'"),
        ('konda', "VARCHAR DEFAULT '01'"),
        ('kvgr1', "VARCHAR DEFAULT 'STD'"),
        ('kvgr2', "VARCHAR DEFAULT 'TRAD'"),
        ('kvgr3', "VARCHAR DEFAULT ''"),
        ('kvgr4', "VARCHAR DEFAULT ''"),
        ('kvgr5', "VARCHAR DEFAULT ''")
    ]:
        try:
            con.execute(f"ALTER TABLE sap_customers ADD COLUMN {col} {col_def}")
        except Exception:
            pass

    # 1. Sprawdzenie czy katalog transakcji SD jest wypełniony
    tcodes_count = con.execute("SELECT COUNT(*) FROM sd_tcodes_catalog").fetchone()[0]
    if tcodes_count == 0:
        from app.database.tcodes_data import SD_TCODES_DATA
        for t in SD_TCODES_DATA:
            con.execute("""
                INSERT OR REPLACE INTO sd_tcodes_catalog 
                (tcode, name, category, description, tables_involved, spro_path, is_custom_z, company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [t['tcode'], t['name'], t['category'], t['description'], t['tables_involved'], t['spro_path'], t['is_custom_z'], t['company_id']])

    # 2. Sprawdzenie czy katalog procesów Enterprise jest wypełniony
    proc_count = 0
    try:
        proc_count = con.execute("SELECT COUNT(*) FROM sd_process_catalog").fetchone()[0]
    except Exception:
        con.execute("DROP TABLE IF EXISTS sd_process_catalog")
        con.execute("""
            CREATE TABLE sd_process_catalog (
                id INTEGER PRIMARY KEY,
                process_code VARCHAR NOT NULL,
                process_name VARCHAR NOT NULL,
                business_domain VARCHAR NOT NULL,
                step_order INTEGER NOT NULL,
                phase VARCHAR NOT NULL,
                tcode VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description VARCHAR NOT NULL,
                prerequisites VARCHAR,
                tables_involved VARCHAR,
                doc_type VARCHAR,
                module VARCHAR
            )
        """)

    if proc_count == 0:
        from app.database.process_data import ENTERPRISE_PROCESSES
        global_step_id = 1
        for proc in ENTERPRISE_PROCESSES:
            p_code = proc["process_code"]
            p_name = proc["process_name"]
            p_domain = proc["business_domain"]
            for st in proc["steps"]:
                con.execute("""
                    INSERT INTO sd_process_catalog 
                    (id, process_code, process_name, business_domain, step_order, phase, tcode, name, description, prerequisites, tables_involved, doc_type, module)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    global_step_id,
                    p_code,
                    p_name,
                    p_domain,
                    st["step_order"],
                    st["phase"],
                    st["tcode"],
                    st["name"],
                    st["description"],
                    st.get("prerequisites", ""),
                    st.get("tables_involved", ""),
                    st.get("doc_type", ""),
                    st.get("module", "SD")
                ])
                global_step_id += 1

    # 3. Sprawdzenie czy profile firm już istnieją
    existing_companies = con.execute("SELECT COUNT(*) FROM company_profiles").fetchone()[0]
    if existing_companies > 0:
        # Sprawdzenie czy zbiór danych korporacyjnych (VBAK/VBAP, KNVV, LIPS/VBRK, TVxx) został zainicjalizowany
        try:
            enterprise_orders = con.execute("SELECT COUNT(*) FROM sap_orders_vbak_vbap WHERE company_id = 'CLIENT_A'").fetchone()[0]
            if enterprise_orders == 0:
                from app.database.enterprise_samples import EnterpriseDataGenerator
                EnterpriseDataGenerator.seed_enterprise_dataset('CLIENT_A')
        except Exception as e:
            print(f"Info: seeding enterprise dataset on existing DB: {e}")
        return

    # --- PROFIL 1: KLIENT A (Global Manufacturing Corp) ---
    con.execute("""
        INSERT INTO company_profiles (id, name, ktopl, bukrs, waers, industry, custom_z_notes, is_active)
        VALUES (
            'CLIENT_A',
            'Global Manufacturing Corp (Klient A)',
            'INT',
            '1000',
            'EUR',
            'Automotive & Machinery',
            'Standard O2C z customowym typem zlecenia ZOR1 (Express Domestic). Specjalna marża na ZPR1. VKOA tabela 001 z podziałem na kraj (01) i eksport (02).',
            TRUE
        )
    """)

    # Obszary sprzedaży Klienta A
    con.execute("INSERT INTO sd_sales_areas VALUES ('SA_A1', 'CLIENT_A', '1000', '10', '00', 'Sprzedaż bezpośrednia - Kraj', 'EUR')")
    con.execute("INSERT INTO sd_sales_areas VALUES ('SA_A2', 'CLIENT_A', '1000', '20', '00', 'Hurt i dystrybucja - Eksport', 'EUR')")

    # Rodzaje zleceń Klienta A (AUART)
    con.execute("INSERT INTO sd_order_types VALUES ('OT_A1', 'CLIENT_A', 'TA', 'Standardowe zlecenie sprzedaży (Standard Order)', 'NORM', 'TAN', 'F2', 'Standardowe zlecenie z dostawą i fakturowaniem')")
    con.execute("INSERT INTO sd_order_types VALUES ('OT_A2', 'CLIENT_A', 'ZOR1', 'Zlecenie ekspresowe krajowe (Custom Z-Order)', 'NORM', 'ZTAN', 'ZF2', 'Wymaga automatycznego ustalania priorytetu dostawy')")
    con.execute("INSERT INTO sd_order_types VALUES ('OT_A3', 'CLIENT_A', 'RE', 'Zwrot od klienta (Returns Order)', 'NORM', 'REN', 'RE', 'Generuje dostawę zwrotną LR i fakturę korygującą')")
    con.execute("INSERT INTO sd_order_types VALUES ('OT_A4', 'CLIENT_A', 'KB', 'Uzupełnienie konsygnacji (Consignment Fill-up)', 'NORM', 'KBN', 'Brak', 'Wydanie towaru bez fakturowania')")

    # Warunki cenowe Klienta A (KSCHL)
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_A1', 'CLIENT_A', 'PR00', 'B', 'C', 'Cena podstawowa (Standard Base Price)', 'ERL', 'PR00', 'Główna pozycja przychodowa')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_A2', 'CLIENT_A', 'K004', 'A', 'A', 'Rabat materiałowy procentowy', 'ERS', 'K004', 'Deductions z przychodu')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_A3', 'CLIENT_A', 'K007', 'A', 'A', 'Rabat dla grupy klientów', 'ERS', 'K007', 'Deductions z przychodu')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_A4', 'CLIENT_A', 'KF00', 'A', 'B', 'Koszty frachtu zryczałtowane', 'ERF', 'KF00', 'Przychody z usług logistycznych')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_A5', 'CLIENT_A', 'MWST', 'D', 'A', 'Podatek VAT należny (Output Tax)', 'MWS', 'MWST', 'Konto rozliczenia podatku VAT')")

    # Reguły VKOA Klienta A (Access Tables 001 - 005)
    # Tabela 001: KTOPL + VKORG + KTGRD + KTGRM + KVSL -> SAKNR
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A1', 'CLIENT_A', 'V', 'KOFI', '001', 'INT', '1000', '01', '01', 'ERL', '800000', NULL, 'Przychody ze sprzedaży towarów - rynek krajowy')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A2', 'CLIENT_A', 'V', 'KOFI', '001', 'INT', '1000', '01', '02', 'ERL', '800100', NULL, 'Przychody ze sprzedaży wyrobów gotowych - rynek krajowy')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A3', 'CLIENT_A', 'V', 'KOFI', '001', 'INT', '1000', '02', '01', 'ERL', '800200', NULL, 'Przychody ze sprzedaży - eksport')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A4', 'CLIENT_A', 'V', 'KOFI', '001', 'INT', '1000', '01', '01', 'ERS', '809000', NULL, 'Udzielone rabaty i skonta - rynek krajowy')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A5', 'CLIENT_A', 'V', 'KOFI', '001', 'INT', '1000', '01', '01', 'MWS', '175000', NULL, 'Należny podatek VAT 23%')")
    # Tabela 004: Fallback dla rabatów i podatków
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A7', 'CLIENT_A', 'V', 'KOFI', '004', 'INT', NULL, NULL, NULL, 'ERS', '809000', NULL, 'Ogólny fallback rabatów sprzedaży')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_A8', 'CLIENT_A', 'V', 'KOFI', '004', 'INT', NULL, NULL, NULL, 'MWS', '175000', NULL, 'Ogólny fallback podatku VAT')")

    # Materiały i klienci Klienta A
    con.execute("""
        INSERT INTO sap_materials (matnr, company_id, maktx, mtart, werks, meins, stprs, ktgrm, mtpos, mtvfp, taxm1)
        VALUES ('SM-100', 'CLIENT_A', 'Smar łożyskowy litowy EP-2', 'ROH', '1000', 'KG', 45.50, '01', 'NORM', '01', '1')
    """)
    con.execute("""
        INSERT INTO sap_materials (matnr, company_id, maktx, mtart, werks, meins, stprs, ktgrm, mtpos, mtvfp, taxm1)
        VALUES ('FIL-990', 'CLIENT_A', 'Filtr Olejowy Przemysłowy Heavy-Duty', 'FERT', '1000', 'SZT', 185.00, '02', 'NORM', '02', '1')
    """)
    con.execute("""
        INSERT INTO sap_materials (matnr, company_id, maktx, mtart, werks, meins, stprs, ktgrm, mtpos, mtvfp, taxm1)
        VALUES ('SRV-01', 'CLIENT_A', 'Usługa serwisu i wdrożenia SD', 'DIEN', '1000', 'RBG', 250.00, '03', 'LEIS', '', '0')
    """)
    con.execute("INSERT INTO sap_stock VALUES ('SM-100', '1000', 450.00, 'KG')")
    con.execute("INSERT INTO sap_stock VALUES ('FIL-990', '1000', 65.00, 'SZT')")
    con.execute("""
        INSERT INTO sap_customers (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure, land1, stceg, zterm, inco1, inco2, vwerk, taxkd)
        VALUES ('C-10001', 'CLIENT_A', 'Auto-Trans Logistics Sp. z o.o.', '1000', '10', '00', '01', 75000.00, 14200.00, 'PL', 'PL5260001234', 'NT30', 'DAP', 'Katowice', '1000', '1')
    """)
    con.execute("""
        INSERT INTO sap_customers (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure, land1, stceg, zterm, inco1, inco2, vwerk, taxkd)
        VALUES ('C-10002', 'CLIENT_A', 'Euro-Machinery GmbH (Export)', '1000', '20', '00', '02', 120000.00, 45000.00, 'DE', 'DE123456789', 'NT60', 'FCA', 'Frankfurt', '1000', '1')
    """)
    con.execute("""
        INSERT INTO sap_vendors (lifnr, company_id, name1, land1, stceg, ekorg, bukrs, waers, zterm, partner_role, is_subcontractor, notes)
        VALUES ('V-20001', 'CLIENT_A', 'Galwanotechnika Śląsk Sp. z o.o.', 'PL', 'PL8991234567', '1000', '1000', 'EUR', 'NT14', 'LF', TRUE, 'Podwykonawca uszlachetniania ruch 541')
    """)
    con.execute("""
        INSERT INTO sap_vendors (lifnr, company_id, name1, land1, stceg, ekorg, bukrs, waers, zterm, partner_role, is_subcontractor, notes)
        VALUES ('V-20002', 'CLIENT_A', 'DSV Road Logistics Sp. z o.o.', 'PL', 'PL9876543210', '1000', '1000', 'EUR', 'NT30', 'SPED', FALSE, 'Spedytor i przewoźnik frachtowy')
    """)

    # Pamięć Smart Memory Klienta A
    con.execute("""
        INSERT INTO ai_memory (id, company_id, category, original_prompt, corrected_output, created_at)
        VALUES (
            1,
            'CLIENT_A',
            'AUART',
            'zlecenie ekspresowe dla klienta krajowego',
            'Dla Klienta A użyj customowego zlecenia ZOR1 z pozycją ZTAN oraz priorytetem dostawy 01.',
            CURRENT_TIMESTAMP
        )
    """)

    # --- PROFIL 2: KLIENT B (Nordic Retail & Tech AB) ---
    con.execute("""
        INSERT INTO company_profiles (id, name, ktopl, bukrs, waers, industry, custom_z_notes, is_active)
        VALUES (
            'CLIENT_B',
            'Nordic Retail & Tech AB (Klient B)',
            'SE01',
            '2000',
            'SEK',
            'Consumer Electronics & SaaS',
            'Specyficzny szwedzki plan kont SE01. Kody Z*: ZEXP (Nordic Express Export), warunek cenowy ZPR1 (Nordic Pricing Matrix). VKOA stosuje konta 3000-series wg kontoplanu BAS.',
            FALSE
        )
    """)

    # Obszary sprzedaży Klienta B
    con.execute("INSERT INTO sd_sales_areas VALUES ('SA_B1', 'CLIENT_B', '2000', '10', '01', 'Nordic Retail - Sweden B2C', 'SEK')")
    con.execute("INSERT INTO sd_sales_areas VALUES ('SA_B2', 'CLIENT_B', '2000', '20', '01', 'Nordic Wholesale - Scandinavia', 'EUR')")

    # Rodzaje zleceń Klienta B (AUART)
    con.execute("INSERT INTO sd_order_types VALUES ('OT_B1', 'CLIENT_B', 'OR', 'Standard Sales Order', 'NORM', 'TAN', 'F2', 'Standardowe zamówienie detaliczne i hurtowe')")
    con.execute("INSERT INTO sd_order_types VALUES ('OT_B2', 'CLIENT_B', 'ZEXP', 'Nordic Express Cross-Border (Custom Z-Order)', 'NORM', 'ZTAN', 'ZF2', 'Wymaga automatycznego sprawdzenia Intrastat')")
    con.execute("INSERT INTO sd_order_types VALUES ('OT_B3', 'CLIENT_B', 'CR', 'Credit Memo Request (Uznanie)', 'NORM', 'L2N', 'G2', 'Wymaga zatwierdzenia blokady rozliczeń 08')")

    # Warunki cenowe Klienta B (KSCHL)
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_B1', 'CLIENT_B', 'ZPR1', 'B', 'C', 'Nordic Base Retail Price', 'ERL', 'ZPR1', 'Customowa cena katalogowa dla rynku nordyckiego')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_B2', 'CLIENT_B', 'ZFRE', 'A', 'B', 'Nordic Eco-Logistics Surcharge', 'ERF', 'ZFRE', 'Opłata logistyczna zielonej dostawy')")
    con.execute("INSERT INTO sd_pricing_conditions VALUES ('PC_B3', 'CLIENT_B', 'MWST', 'D', 'A', 'MOMS (Swedish VAT 25%)', 'MWS', 'MWST', 'Szwedzki podatek VAT 25%')")

    # Reguły VKOA Klienta B
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_B1', 'CLIENT_B', 'V', 'KOFI', '001', 'SE01', '2000', '01', '01', 'ERL', '300000', NULL, 'Försäljning varor Sverige 25% MOMS')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_B2', 'CLIENT_B', 'V', 'KOFI', '001', 'SE01', '2000', '01', '03', 'ERL', '300100', NULL, 'Licensintäkter SaaS & Cloud')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_B3', 'CLIENT_B', 'V', 'KOFI', '001', 'SE01', '2000', '02', '01', 'ERL', '300200', NULL, 'Försäljning varor Export EU')")
    con.execute("INSERT INTO sd_vkoa_rules VALUES ('VK_B4', 'CLIENT_B', 'V', 'KOFI', '001', 'SE01', '2000', '01', '01', 'MWS', '261000', NULL, 'Utgående moms 25%')")

    # Materiały i klienci Klienta B
    con.execute("""
        INSERT INTO sap_materials (matnr, company_id, maktx, mtart, werks, meins, stprs, ktgrm, mtpos, mtvfp, taxm1)
        VALUES ('HUB-50', 'CLIENT_B', 'Nordic Smart IoT Gateway Hub', 'FERT', '2000', 'SZT', 890.00, '01', 'NORM', '02', '1')
    """)
    con.execute("""
        INSERT INTO sap_materials (matnr, company_id, maktx, mtart, werks, meins, stprs, ktgrm, mtpos, mtvfp, taxm1)
        VALUES ('SAS-PRO', 'CLIENT_B', 'Cloud Fleet Management License 1Y', 'DIEN', '2000', 'SZT', 2400.00, '03', 'LEIS', '', '0')
    """)
    con.execute("INSERT INTO sap_stock VALUES ('HUB-50', '2000', 320.00, 'SZT')")
    con.execute("INSERT INTO sap_stock VALUES ('SAS-PRO', '2000', 9999.00, 'SZT')")
    con.execute("""
        INSERT INTO sap_customers (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure, land1, stceg, zterm, inco1, inco2, vwerk, taxkd)
        VALUES ('C-20001', 'CLIENT_B', 'Stockholm Retail Stores AB', '2000', '10', '01', '01', 350000.00, 89000.00, 'SE', 'SE1234567801', 'NT30', 'FCA', 'Stockholm', '2000', '1')
    """)
    con.execute("""
        INSERT INTO sap_customers (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure, land1, stceg, zterm, inco1, inco2, vwerk, taxkd)
        VALUES ('C-20002', 'CLIENT_B', 'Helsinki Tech Logistics Oy', '2000', '20', '01', '02', 450000.00, 115000.00, 'FI', 'FI9876543210', 'NT60', 'DAP', 'Helsinki', '2000', '1')
    """)

    # Pamięć Smart Memory Klienta B
    con.execute("""
        INSERT INTO ai_memory (id, company_id, category, original_prompt, corrected_output, created_at)
        VALUES (
            2,
            'CLIENT_B',
            'PRICING',
            'jaki warunek cenowy dla zamówień nordyckich',
            'Dla Klienta B zamiast standardowego PR00 zawsze stosuj warunek ZPR1 (Nordic Pricing Matrix).',
            CURRENT_TIMESTAMP
        )
    """)

    # Zasilenie próbką korporacyjną dla nowo utworzonej bazy
    try:
        from app.database.enterprise_samples import EnterpriseDataGenerator
        EnterpriseDataGenerator.seed_enterprise_dataset('CLIENT_A')
    except Exception as e:
        print(f"Info: błąd seedowania korporacyjnego dla nowej bazy: {e}")

# --- FUNKCJE POMOCNICZE MULTI-COMPANY ---

def get_active_company_id() -> str:
    con = get_db_connection()
    row = con.execute("SELECT id FROM company_profiles WHERE is_active = TRUE LIMIT 1").fetchone()
    if row:
        return row[0]
    con.execute("UPDATE company_profiles SET is_active = TRUE WHERE id = 'CLIENT_A'")
    return 'CLIENT_A'

def set_active_company(company_id: str) -> bool:
    con = get_db_connection()
    exists = con.execute("SELECT COUNT(*) FROM company_profiles WHERE id = ?", [company_id]).fetchone()[0]
    if not exists:
        return False
    con.execute("UPDATE company_profiles SET is_active = FALSE")
    con.execute("UPDATE company_profiles SET is_active = TRUE WHERE id = ?", [company_id])
    return True

def get_company_profile(company_id: str = None) -> dict:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()
    
    row = con.execute("""
        SELECT id, name, ktopl, bukrs, waers, industry, custom_z_notes, is_active, created_at 
        FROM company_profiles WHERE id = ?
    """, [company_id]).fetchone()
    
    if not row:
        return {}
    return {
        "id": row[0],
        "name": row[1],
        "ktopl": row[2],
        "bukrs": row[3],
        "waers": row[4],
        "industry": row[5],
        "custom_z_notes": row[6],
        "is_active": bool(row[7]),
        "created_at": str(row[8])
    }

def get_all_companies() -> list:
    con = get_db_connection()
    rows = con.execute("""
        SELECT id, name, ktopl, bukrs, waers, industry, custom_z_notes, is_active 
        FROM company_profiles ORDER BY name
    """).fetchall()
    return [{
        "id": r[0],
        "name": r[1],
        "ktopl": r[2],
        "bukrs": r[3],
        "waers": r[4],
        "industry": r[5],
        "custom_z_notes": r[6],
        "is_active": bool(r[7])
    } for r in rows]

def create_company_profile(company_id: str, name: str, ktopl: str, bukrs: str, waers: str, industry: str = "", custom_z_notes: str = "") -> bool:
    con = get_db_connection()
    exists = con.execute("SELECT COUNT(*) FROM company_profiles WHERE id = ?", [company_id]).fetchone()[0]
    if exists:
        return False
    con.execute("""
        INSERT INTO company_profiles (id, name, ktopl, bukrs, waers, industry, custom_z_notes, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, FALSE)
    """, [company_id, name, ktopl, bukrs, waers, industry, custom_z_notes])
    return True

def update_company_profile(company_id: str, name: str, ktopl: str, bukrs: str, waers: str, industry: str = "", custom_z_notes: str = "") -> bool:
    con = get_db_connection()
    exists = con.execute("SELECT COUNT(*) FROM company_profiles WHERE id = ?", [company_id]).fetchone()[0]
    if not exists:
        return False
    con.execute("""
        UPDATE company_profiles 
        SET name = ?, ktopl = ?, bukrs = ?, waers = ?, industry = ?, custom_z_notes = ?
        WHERE id = ?
    """, [name, ktopl, bukrs, waers, industry, custom_z_notes, company_id])
    return True

def delete_company_profile(company_id: str):
    """
    Usuwa profil firmy oraz kaskadowo powiązane rekordy.
    Zwraca (sukces: bool, komunikat: str, nowy_aktywny_id: str).
    """
    con = get_db_connection()
    total_companies = con.execute("SELECT COUNT(*) FROM company_profiles").fetchone()[0]
    if total_companies <= 1:
        return False, "Nie można usunąć jedynego profilu klienta w systemie.", company_id

    row = con.execute("SELECT is_active FROM company_profiles WHERE id = ?", [company_id]).fetchone()
    if not row:
        return False, f"Profil {company_id} nie istnieje.", get_active_company_id()

    was_active = bool(row[0])

    # Kaskadowe czyszczenie powiązanych struktur i tabel klienta
    con.execute("DELETE FROM sd_sales_areas WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sd_order_types WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sd_pricing_conditions WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sd_vkoa_rules WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sap_materials WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sap_customers WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sap_vendors WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sap_export WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM ai_memory WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM sd_tcodes_catalog WHERE company_id = ?", [company_id])
    con.execute("DELETE FROM company_profiles WHERE id = ?", [company_id])

    # Jeśli usunięty profil był aktywny, uaktywnij pierwszy z pozostałych
    new_active_id = None
    if was_active:
        remaining = con.execute("SELECT id FROM company_profiles ORDER BY id LIMIT 1").fetchone()
        if remaining:
            new_active_id = remaining[0]
            con.execute("UPDATE company_profiles SET is_active = TRUE WHERE id = ?", [new_active_id])
    else:
        new_active_id = get_active_company_id()

    return True, f"Profil {company_id} został pomyślnie usunięty.", new_active_id

def save_ai_memory(prompt: str, correction: str, company_id: str = None, category: str = "GENERAL") -> int:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()
    max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM ai_memory").fetchone()[0] + 1
    con.execute(
        "INSERT INTO ai_memory (id, company_id, category, original_prompt, corrected_output, created_at) "
        "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        [max_id, company_id, category, prompt, correction]
    )
    return max_id

def get_ai_memories(company_id: str = None, limit: int = 50) -> list:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()
    rows = con.execute("""
        SELECT id, company_id, category, original_prompt, corrected_output, created_at 
        FROM ai_memory 
        WHERE company_id = ? 
        ORDER BY created_at DESC LIMIT ?
    """, [company_id, limit]).fetchall()
    return [{
        "id": r[0],
        "company_id": r[1],
        "category": r[2],
        "original_prompt": r[3],
        "corrected_output": r[4],
        "created_at": str(r[5])
    } for r in rows]

def approve_export_transaction(trans_id: int) -> bool:
    con = get_db_connection()
    con.execute("UPDATE sap_export SET status = 'APPROVED' WHERE id = ?", [trans_id])
    return True

# --- ZARZĄDZANIE KATALOGIEM TRANSAKCJI SD (T-CODES) ---

def get_sd_tcodes(query: str = None, category: str = None, company_id: str = None, limit: int = 300) -> list:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()

    sql = """
        SELECT tcode, name, category, description, tables_involved, spro_path, is_custom_z, company_id
        FROM sd_tcodes_catalog
        WHERE (company_id IS NULL OR company_id = ?)
    """
    params = [company_id]

    if category and category != 'ALL':
        sql += " AND category = ?"
        params.append(category)

    if query:
        q = f"%{query.strip().lower()}%"
        sql += """
            AND (
                LOWER(tcode) LIKE ? OR
                LOWER(name) LIKE ? OR
                LOWER(description) LIKE ? OR
                LOWER(tables_involved) LIKE ? OR
                LOWER(spro_path) LIKE ?
            )
        """
        params.extend([q, q, q, q, q])

    if query:
        q_clean = query.strip().upper()
        sql += " ORDER BY CASE WHEN UPPER(tcode) = ? THEN 0 ELSE 1 END, is_custom_z DESC, tcode ASC LIMIT ?"
        params.extend([q_clean, limit])
    else:
        sql += " ORDER BY is_custom_z DESC, tcode ASC LIMIT ?"
        params.append(limit)

    rows = con.execute(sql, params).fetchall()
    return [{
        "tcode": r[0],
        "name": r[1],
        "category": r[2],
        "description": r[3],
        "tables_involved": r[4] or "",
        "spro_path": r[5] or "",
        "is_custom_z": bool(r[6]),
        "company_id": r[7]
    } for r in rows]

def get_sd_tcode_categories(company_id: str = None) -> list:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()
    rows = con.execute("""
        SELECT category, COUNT(*) as cnt
        FROM sd_tcodes_catalog
        WHERE (company_id IS NULL OR company_id = ?)
        GROUP BY category
        ORDER BY category
    """, [company_id]).fetchall()
    return [{"category": r[0], "count": r[1]} for r in rows]


def add_custom_sd_tcode(tcode: str, name: str, category: str, description: str, tables_involved: str = "", spro_path: str = "", company_id: str = None) -> bool:
    con = get_db_connection()
    if not company_id:
        company_id = get_active_company_id()
    tcode = tcode.strip().upper()
    con.execute("""
        INSERT OR REPLACE INTO sd_tcodes_catalog 
        (tcode, name, category, description, tables_involved, spro_path, is_custom_z, company_id)
        VALUES (?, ?, ?, ?, ?, ?, TRUE, ?)
    """, [tcode, name, category, description, tables_involved, spro_path, company_id])
    return True
