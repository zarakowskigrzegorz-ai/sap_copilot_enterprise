# -*- coding: utf-8 -*-
"""
Serwis Master Data Governance (MDG) i Profilowania Partnerów dla SAP Copilot.
Zarządza kartotekami Klientów (KNA1/KNVV), Dostawców i Podwykonawców (LFA1/LFM1/EINE)
oraz Materiałów (MARA/MVKE/MARC). Przeprowadza audyt jakości danych O2C i fakturowania.
"""

import csv
import io
from typing import Dict, Any, List, Optional
from app.database.db_manager import get_db_connection, get_company_profile

class MdgService:
    """
    Silnik analizy Master Data Governance (MDG) i importu danych z SAP.
    """

    @classmethod
    def audit_master_data(cls, company_id: str) -> Dict[str, Any]:
        """
        Przeprowadza kompleksowy audyt integralności danych podstawowych dla wybranej firmy.
        Weryfikuje gotowość do procesów O2C, wykrywa luki w fakturowaniu (VF067),
        podatkach (FF704) oraz analizuje relacje podwykonawstwa i partnerów.
        """
        con = get_db_connection()
        profile = get_company_profile(company_id) or {}
        company_name = profile.get("name", company_id)

        # 1. Pobranie danych klientów
        customers = con.execute("""
            SELECT kunnr, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure,
                   COALESCE(land1, 'PL') as land1, COALESCE(stceg, '') as stceg,
                   COALESCE(zterm, 'NT30') as zterm, COALESCE(inco1, '') as inco1,
                   COALESCE(inco2, '') as inco2, COALESCE(vwerk, '') as vwerk,
                   COALESCE(taxkd, '1') as taxkd
            FROM sap_customers WHERE company_id = ?
        """, [company_id]).fetchall()

        # 2. Pobranie danych materiałów
        materials = con.execute("""
            SELECT matnr, maktx, mtart, werks, meins, stprs, ktgrm,
                   COALESCE(mtpos, 'NORM') as mtpos, COALESCE(mtvfp, '01') as mtvfp,
                   COALESCE(taxm1, '1') as taxm1
            FROM sap_materials WHERE company_id = ?
        """, [company_id]).fetchall()

        # 3. Pobranie danych dostawców i podwykonawców
        vendors = con.execute("""
            SELECT lifnr, name1, land1, stceg, ekorg, bukrs, waers, zterm, partner_role, is_subcontractor, notes
            FROM sap_vendors WHERE company_id = ?
        """, [company_id]).fetchall()

        # 4. Pobranie reguł VKOA
        vkoa_rules = con.execute("""
            SELECT table_num, ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl, saknr
            FROM sd_vkoa_rules WHERE company_id = ?
        """, [company_id]).fetchall()

        # --- ANALIZA JAKOŚCI I REGUŁ MDG ---
        issues: List[Dict[str, Any]] = []
        critical_count = 0
        warning_count = 0

        # Audyt Klientów
        cust_missing_ktgrd = [c for c in customers if not c[5] or c[5].strip() == '']
        if cust_missing_ktgrd:
            critical_count += len(cust_missing_ktgrd)
            issues.append({
                "severity": "CRITICAL",
                "category": "Customer Master (KNVV)",
                "title": f"Brak grupy rozliczenia klienta (KTGRD) u {len(cust_missing_ktgrd)} odbiorców",
                "desc": "Brak pola KTGRD bezpośrednio blokuje księgowanie faktur w module FI z błędem VF067 w VFX3.",
                "tcode": "BP / XD02",
                "affected": [f"{c[0]} ({c[1]})" for c in cust_missing_ktgrd[:3]]
            })

        cust_missing_taxkd = [c for c in customers if not c[14] or c[14].strip() == '']
        if cust_missing_taxkd:
            warning_count += len(cust_missing_taxkd)
            issues.append({
                "severity": "WARNING",
                "category": "Customer Tax (KNVI)",
                "title": f"Brak klasyfikacji podatkowej TAXKD u {len(cust_missing_taxkd)} odbiorców",
                "desc": "Może powodować błąd determinacji podatku VAT (FF704 / MWST) w zleceniach sprzedaży.",
                "tcode": "BP / XD02",
                "affected": [c[0] for c in cust_missing_taxkd[:3]]
            })

        cust_missing_inco = [c for c in customers if not c[11] or not c[12]]
        if cust_missing_inco:
            warning_count += len(cust_missing_inco)
            issues.append({
                "severity": "INFO",
                "category": "Customer Commercial (KNVV)",
                "title": f"Niekompletne Incoterms (brak reguły lub portu) u {len(cust_missing_inco)} klientów",
                "desc": "Zlecenie sprzedaży VA01 może zgłosić brak kompletności danych (Incompletion log V1382).",
                "tcode": "BP",
                "affected": [c[0] for c in cust_missing_inco[:3]]
            })

        # Audyt Materiałów
        mat_missing_ktgrm = [m for m in materials if not m[6] or m[6].strip() == '']
        if mat_missing_ktgrm:
            critical_count += len(mat_missing_ktgrm)
            issues.append({
                "severity": "CRITICAL",
                "category": "Material Master (MVKE)",
                "title": f"Brak grupy rozliczenia materiału (KTGRM) w {len(mat_missing_ktgrm)} indeksach",
                "desc": "Uniemożliwi poprawne wywołanie procedury KOFI00 – błąd VF067 przy tworzeniu faktury VF01.",
                "tcode": "MM02 (Sprzedaż 2)",
                "affected": [f"{m[0]} ({m[1]})" for m in mat_missing_ktgrm[:3]]
            })

        mat_missing_atp = [m for m in materials if not m[8] or m[8].strip() == '']
        if mat_missing_atp:
            warning_count += len(mat_missing_atp)
            issues.append({
                "severity": "WARNING",
                "category": "Material Logistics (MARC)",
                "title": f"Brak grupy kontroli dostępności ATP (MTVFP) w {len(mat_missing_atp)} materiałach",
                "desc": "System nie sprawdzi stanów wolnych w CO09, co może skutkować błędem braków magazynowych M7021.",
                "tcode": "MM02 (MRP 3)",
                "affected": [m[0] for m in mat_missing_atp[:3]]
            })

        # Audyt Pokrycia VKOA
        cust_groups = set([c[5] for c in customers if c[5]])
        mat_groups = set([m[6] for m in materials if m[6]])
        vkoa_covered_pairs = set([(r[3], r[4]) for r in vkoa_rules if r[3] and r[4]])
        
        missing_vkoa_combinations = []
        for cg in cust_groups:
            for mg in mat_groups:
                if (cg, mg) not in vkoa_covered_pairs:
                    missing_vkoa_combinations.append(f"Klient: {cg} x Materiał: {mg}")

        if missing_vkoa_combinations:
            issues.append({
                "severity": "WARNING",
                "category": "Revenue Account Determination (VKOA)",
                "title": f"Luki w matrycy VKOA dla {len(missing_vkoa_combinations)} kombinacji grup rozliczeniowych",
                "desc": "Dla występujących w kartotekach par grup brak bezpośredniego wpisu w Tabeli 001 VKOA.",
                "tcode": "VKOA",
                "affected": missing_vkoa_combinations[:3]
            })

        # Wyliczenie wskaźnika jakości danych (Data Quality Score)
        total_records = len(customers) + len(materials) + len(vendors)
        if total_records == 0:
            quality_score = 0
        else:
            penalty = (critical_count * 15) + (warning_count * 5)
            quality_score = max(10, min(100, 100 - penalty))

        subcontractors = [v for v in vendors if v[9]]
        forwarders = [v for v in vendors if v[8] == 'SPED']

        return {
            "status": "success",
            "company_id": company_id,
            "company_name": company_name,
            "quality_score": quality_score,
            "ready_for_o2c": quality_score >= 80 and critical_count == 0,
            "stats": {
                "customers_count": len(customers),
                "materials_count": len(materials),
                "vendors_count": len(vendors),
                "subcontractors_count": len(subcontractors),
                "forwarders_count": len(forwarders),
                "vkoa_rules_count": len(vkoa_rules)
            },
            "issues": issues,
            "samples": {
                "customers": [{
                    "kunnr": c[0], "name1": c[1], "vkorg": c[2], "ktgrd": c[5], "waers": profile.get("waers", "EUR")
                } for c in customers[:5]],
                "materials": [{
                    "matnr": m[0], "maktx": m[1], "mtart": m[2], "ktgrm": m[6], "stprs": float(m[5] or 0)
                } for m in materials[:5]],
                "vendors": [{
                    "lifnr": v[0], "name1": v[1], "role": v[8], "is_subcontractor": bool(v[9])
                } for v in vendors[:5]]
            }
        }

    @classmethod
    def import_csv_data(cls, content_str: str, data_type: str, company_id: str) -> Dict[str, Any]:
        """
        Importuje wsad CSV i zasila odpowiednie tabele Master Data w bazie.
        Obsługuje separatory ';' oraz ','.
        """
        con = get_db_connection()
        reader = csv.reader(io.StringIO(content_str.strip()), delimiter=';' if ';' in content_str else ',')
        rows = list(reader)
        if not rows:
            return {"status": "error", "message": "Plik CSV jest pusty"}

        header = [col.strip().upper() for col in rows[0]]
        data_rows = rows[1:]
        imported_count = 0

        if data_type == 'customers':
            for r in data_rows:
                if not r or len(r) < 2: continue
                kunnr = r[0].strip()
                name1 = r[1].strip()
                land1 = r[2].strip() if len(r) > 2 else 'PL'
                stceg = r[3].strip() if len(r) > 3 else ''
                vkorg = r[4].strip() if len(r) > 4 else '1000'
                vtweg = r[5].strip() if len(r) > 5 else '10'
                spart = r[6].strip() if len(r) > 6 else '00'
                ktgrd = r[7].strip() if len(r) > 7 else '01'
                zterm = r[8].strip() if len(r) > 8 else 'NT30'
                inco1 = r[9].strip() if len(r) > 9 else 'DAP'
                inco2 = r[10].strip() if len(r) > 10 else 'Lokalizacja'
                
                con.execute("""
                    INSERT OR REPLACE INTO sap_customers 
                    (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, land1, stceg, zterm, inco1, inco2)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, land1, stceg, zterm, inco1, inco2])
                imported_count += 1

        elif data_type == 'vendors':
            for r in data_rows:
                if not r or len(r) < 2: continue
                lifnr = r[0].strip()
                name1 = r[1].strip()
                land1 = r[2].strip() if len(r) > 2 else 'PL'
                stceg = r[3].strip() if len(r) > 3 else ''
                ekorg = r[4].strip() if len(r) > 4 else '1000'
                bukrs = r[5].strip() if len(r) > 5 else '1000'
                waers = r[6].strip() if len(r) > 6 else 'EUR'
                zterm = r[7].strip() if len(r) > 7 else 'NT30'
                role = r[8].strip() if len(r) > 8 else 'LF'
                is_sub = True if len(r) > 9 and r[9].strip().upper() in ['YES', 'TAK', '1', 'TRUE'] else False
                
                con.execute("""
                    INSERT OR REPLACE INTO sap_vendors 
                    (lifnr, company_id, name1, land1, stceg, ekorg, bukrs, waers, zterm, partner_role, is_subcontractor)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [lifnr, company_id, name1, land1, stceg, ekorg, bukrs, waers, zterm, role, is_sub])
                imported_count += 1

        elif data_type == 'materials':
            for r in data_rows:
                if not r or len(r) < 2: continue
                matnr = r[0].strip()
                maktx = r[1].strip()
                mtart = r[2].strip() if len(r) > 2 else 'FERT'
                werks = r[3].strip() if len(r) > 3 else '1000'
                meins = r[4].strip() if len(r) > 4 else 'SZT'
                ktgrm = r[5].strip() if len(r) > 5 else '02'
                mtpos = r[6].strip() if len(r) > 6 else 'NORM'
                mtvfp = r[7].strip() if len(r) > 7 else '01'
                stprs = float(r[8].strip()) if len(r) > 8 and r[8].strip() else 100.0
                
                con.execute("""
                    INSERT OR REPLACE INTO sap_materials 
                    (matnr, company_id, maktx, mtart, werks, meins, ktgrm, mtpos, mtvfp, stprs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [matnr, company_id, maktx, mtart, werks, meins, ktgrm, mtpos, mtvfp, stprs])
                imported_count += 1

        else:
            return {"status": "error", "message": f"Nieobsługiwany typ danych: {data_type}"}

        # Po zaimportowaniu od razu odświeżamy audyt MDG oraz uruchamiamy silnik Auto-Discovery procesów
        audit = cls.audit_master_data(company_id)
        
        from app.services.process_inference_service import ProcessInferenceService
        inferred = ProcessInferenceService.infer_company_processes(company_id)
        snippet_analysis = ProcessInferenceService.analyze_raw_report_snippet(data_type, content_str)

        discovered_titles = [d["title"] for d in snippet_analysis.get("discovered_processes", [])]
        extra_msg = ""
        if discovered_titles:
            extra_msg = f" • Auto-Discovery: zidentyfikowano procesy: {', '.join(discovered_titles)}"

        return {
            "status": "success",
            "imported_count": imported_count,
            "data_type": data_type,
            "message": f"Pomyślnie zaimportowano {imported_count} rekordów ({data_type}){extra_msg}",
            "audit": audit,
            "inferred_processes": inferred,
            "discovered_processes": snippet_analysis.get("discovered_processes", [])
        }

    @classmethod
    def get_sample_csv(cls, data_type: str) -> str:
        """Zwraca gotowy szablon CSV do pobrania lub wklejenia."""
        if data_type == 'customers':
            return (
                "KUNNR;NAME1;LAND1;STCEG;VKORG;VTWEG;SPART;KTGRD;ZTERM;INCO1;INCO2;WAERS;VWERK\n"
                "100010;ABB Power Systems Sp. z o.o.;PL;PL5260001234;1000;10;00;01;NT30;DAP;Katowice;EUR;1000\n"
                "100020;Siemens Mobility AG;DE;DE123456789;1000;10;00;02;NT60;FCA;Frankfurt;EUR;1000\n"
                "100030;Orlen Asfalt Sp. z o.o.;PL;PL7740001454;1000;10;00;01;NT14;CPT;Płock;PLN;1000\n"
            )
        elif data_type == 'vendors':
            return (
                "LIFNR;NAME1;LAND1;STCEG;EKORG;BUKRS;WAERS;ZTERM;ROLA_PARTNERA;CZY_PODWYKONAWCA\n"
                "200050;Galwanotechnika Śląsk Sp. z o.o.;PL;PL8991234567;1000;1000;PLN;NT14;LF;TAK\n"
                "200080;DSV Road Logistics Sp. z o.o.;PL;PL9876543210;1000;1000;EUR;NT30;SPED;NIE\n"
                "200090;Hartownia Przemysłowa Precyzja;PL;PL1122334455;1000;1000;PLN;NT30;LF;TAK\n"
            )
        elif data_type == 'materials':
            return (
                "MATNR;MAKTX;MTART;WERKS;MEINS;KTGRM;MTPOS;MTVFP;STPRS\n"
                "MAT-100;Falownik Przemysłowy Sinamics 50kW;FERT;1000;SZT;02;NORM;01;3450.00\n"
                "MAT-200;Transformator Suchy Żywiczny 100kVA;FERT;1000;SZT;02;NORM;01;8900.00\n"
                "MAT-300;Usługa Galwanizacji i Hartowania;DIEN;1000;KPL;03;DIEN;02;450.00\n"
                "MAT-400;Kabel Sterowniczy Miedź 4x2.5;ROH;1000;M;01;NORM;01;12.50\n"
            )
        return ""

    @classmethod
    def seed_default_ecosystem_if_needed(cls, company_id: str):
        """Uzupełnia domyślny ekosystem (dostawcy, podwykonawcy, klienci), jeśli profil jest pusty."""
        con = get_db_connection()
        vendor_cnt = con.execute("SELECT COUNT(*) FROM sap_vendors WHERE company_id = ?", [company_id]).fetchone()[0]
        if vendor_cnt == 0:
            cls.import_csv_data(cls.get_sample_csv('vendors'), 'vendors', company_id)
        
        cust_cnt = con.execute("SELECT COUNT(*) FROM sap_customers WHERE company_id = ?", [company_id]).fetchone()[0]
        if cust_cnt == 0:
            cls.import_csv_data(cls.get_sample_csv('customers'), 'customers', company_id)
            
        mat_cnt = con.execute("SELECT COUNT(*) FROM sap_materials WHERE company_id = ?", [company_id]).fetchone()[0]
        if mat_cnt == 0:
            cls.import_csv_data(cls.get_sample_csv('materials'), 'materials', company_id)

    @classmethod
    def auto_fix_master_data(cls, company_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Automatyczna naprawa luk w kartotekach Master Data (1-Click Auto-Heal MDG):
        - Uzupełnia brakujące grupy KTGRD, klasyfikacje podatkowe TAXKD oraz Incoterms u klientów (KNVV/KNVI)
        - Uzupełnia brakujące grupy KTGRM oraz grupy kontroli dostępności ATP (MTVFP) w materiałach (MVKE/MARC)
        - Generuje brakujące wpisy w Tabeli 001 VKOA dla wszystkich aktywnych par (KTGRD x KTGRM)
        """
        con = get_db_connection()
        profile = get_company_profile(company_id) or {}
        ktopl = profile.get("ktopl", "INT")

        # Pobranie domyślnego VKORG firmy
        sa_row = con.execute(
            "SELECT vkorg FROM sd_sales_areas WHERE company_id = ? LIMIT 1",
            [company_id]
        ).fetchone()
        default_vkorg = sa_row[0] if sa_row else "1000"

        fixed_actions: List[str] = []
        total_fixed = 0
        fix_all = not category or category.upper() == "ALL"

        # 1. Customer Master (KNVV) - KTGRD
        if fix_all or category == "Customer Master (KNVV)":
            missing_ktgrd = con.execute("""
                SELECT COUNT(*) FROM sap_customers
                WHERE company_id = ? AND (ktgrd IS NULL OR TRIM(ktgrd) = '')
            """, [company_id]).fetchone()[0]
            if missing_ktgrd > 0:
                con.execute("""
                    UPDATE sap_customers
                    SET ktgrd = CASE WHEN COALESCE(land1, 'PL') = 'PL' THEN '01' ELSE '02' END
                    WHERE company_id = ? AND (ktgrd IS NULL OR TRIM(ktgrd) = '')
                """, [company_id])
                total_fixed += missing_ktgrd
                fixed_actions.append(f"Uzupełniono KTGRD (01/02) u {missing_ktgrd} klientów (KNVV)")

        # 2. Customer Tax (KNVI) - TAXKD
        if fix_all or category == "Customer Tax (KNVI)":
            missing_taxkd = con.execute("""
                SELECT COUNT(*) FROM sap_customers
                WHERE company_id = ? AND (taxkd IS NULL OR TRIM(taxkd) = '')
            """, [company_id]).fetchone()[0]
            if missing_taxkd > 0:
                con.execute("""
                    UPDATE sap_customers
                    SET taxkd = '1'
                    WHERE company_id = ? AND (taxkd IS NULL OR TRIM(taxkd) = '')
                """, [company_id])
                total_fixed += missing_taxkd
                fixed_actions.append(f"Ustawiono pełną klasyfikację podatkową TAXKD='1' u {missing_taxkd} odbiorców (KNVI)")

        # 3. Customer Commercial (KNVV) - Incoterms
        if fix_all or category == "Customer Commercial (KNVV)":
            missing_inco = con.execute("""
                SELECT COUNT(*) FROM sap_customers
                WHERE company_id = ? AND (inco1 IS NULL OR TRIM(inco1) = '' OR inco2 IS NULL OR TRIM(inco2) = '')
            """, [company_id]).fetchone()[0]
            if missing_inco > 0:
                con.execute("""
                    UPDATE sap_customers
                    SET inco1 = CASE WHEN inco1 IS NULL OR TRIM(inco1) = '' THEN 'DAP' ELSE inco1 END,
                        inco2 = CASE WHEN inco2 IS NULL OR TRIM(inco2) = '' THEN 'Magazyn Centralny' ELSE inco2 END
                    WHERE company_id = ? AND (inco1 IS NULL OR TRIM(inco1) = '' OR inco2 IS NULL OR TRIM(inco2) = '')
                """, [company_id])
                total_fixed += missing_inco
                fixed_actions.append(f"Uzupełniono reguły Incoterms (DAP / Magazyn Centralny) u {missing_inco} klientów")

        # 4. Material Master (MVKE) - KTGRM
        if fix_all or category == "Material Master (MVKE)":
            missing_ktgrm = con.execute("""
                SELECT COUNT(*) FROM sap_materials
                WHERE company_id = ? AND (ktgrm IS NULL OR TRIM(ktgrm) = '')
            """, [company_id]).fetchone()[0]
            if missing_ktgrm > 0:
                con.execute("""
                    UPDATE sap_materials
                    SET ktgrm = CASE
                        WHEN mtart = 'DIEN' THEN '03'
                        WHEN mtart = 'ROH' THEN '01'
                        ELSE '02'
                    END
                    WHERE company_id = ? AND (ktgrm IS NULL OR TRIM(ktgrm) = '')
                """, [company_id])
                total_fixed += missing_ktgrm
                fixed_actions.append(f"Przypisano grupy rozliczeniowe materiału KTGRM w {missing_ktgrm} indeksach (MVKE)")

        # 5. Material Logistics (MARC) - MTVFP (ATP)
        if fix_all or category == "Material Logistics (MARC)":
            missing_atp = con.execute("""
                SELECT COUNT(*) FROM sap_materials
                WHERE company_id = ? AND (mtvfp IS NULL OR TRIM(mtvfp) = '')
            """, [company_id]).fetchone()[0]
            if missing_atp > 0:
                con.execute("""
                    UPDATE sap_materials
                    SET mtvfp = '01'
                    WHERE company_id = ? AND (mtvfp IS NULL OR TRIM(mtvfp) = '')
                """, [company_id])
                total_fixed += missing_atp
                fixed_actions.append(f"Aktywowano kontrolę dostępności ATP (MTVFP='01') w {missing_atp} materiałach (MARC)")

        # 6. Revenue Account Determination (VKOA) - brakujące pary (KTGRD x KTGRM)
        if fix_all or category == "Revenue Account Determination (VKOA)":
            cust_groups = [
                r[0] for r in con.execute(
                    "SELECT DISTINCT ktgrd FROM sap_customers WHERE company_id = ? AND ktgrd IS NOT NULL AND TRIM(ktgrd) != ''",
                    [company_id]
                ).fetchall()
            ]
            mat_groups = [
                r[0] for r in con.execute(
                    "SELECT DISTINCT ktgrm FROM sap_materials WHERE company_id = ? AND ktgrm IS NOT NULL AND TRIM(ktgrm) != ''",
                    [company_id]
                ).fetchall()
            ]
            existing_pairs = set(
                (r[0], r[1]) for r in con.execute(
                    "SELECT ktgrd_cust, ktgrm_mat FROM sd_vkoa_rules WHERE company_id = ? AND ktgrd_cust IS NOT NULL AND ktgrm_mat IS NOT NULL",
                    [company_id]
                ).fetchall()
            )

            default_gl = "3010" if ktopl == "SE01" else ("701000" if ktopl == "PL01" else "800000")
            vkoa_added = 0
            for cg in cust_groups:
                for mg in mat_groups:
                    if (cg, mg) not in existing_pairs:
                        rule_id = f"AUTO_{company_id}_001_{ktopl}_{default_vkorg}_{cg}_{mg}_ERL"
                        desc = f"Auto-Heal MDG: Przychody ze sprzedaży ({cg}/{mg})"
                        con.execute("""
                            INSERT OR REPLACE INTO sd_vkoa_rules
                            (id, company_id, appl, kschl, table_num, ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl, saknr, description)
                            VALUES (?, ?, 'V', 'KOFI', '001', ?, ?, ?, ?, 'ERL', ?, ?)
                        """, [rule_id, company_id, ktopl, default_vkorg, cg, mg, default_gl, desc])
                        vkoa_added += 1

            if vkoa_added > 0:
                total_fixed += vkoa_added
                fixed_actions.append(f"Utworzono {vkoa_added} brakujących reguł VKOA (Tabela 001 -> Konto G/L {default_gl})")

        audit = cls.audit_master_data(company_id)
        summary_msg = (
            " | ".join(fixed_actions)
            if fixed_actions
            else "Wszystkie kartoteki i reguły VKOA są już w 100% kompletne – brak luk do naprawy."
        )

        return {
            "status": "success",
            "company_id": company_id,
            "total_fixed": total_fixed,
            "fixed_actions": fixed_actions,
            "message": summary_msg,
            "audit": audit
        }

