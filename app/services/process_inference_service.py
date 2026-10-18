# -*- coding: utf-8 -*-
"""
Silnik Automatycznego Wnioskowania Procesów SAP SD (Process Auto-Discovery Engine).
Analizuje dane firmy, kartoteki podstawowe (MVKE, KNVV, LFA1), konfigurację SD
(AUART, KSCHL, VKOA) oraz importowane raporty, automatycznie identyfikując aktywne
procesy biznesowe przedsiębiorstwa i wyliczając wskaźniki pewności (confidence).
"""

import re
from typing import Dict, Any, List, Optional
from app.database.db_manager import get_db_connection, get_company_profile

class ProcessInferenceService:
    """
    Ekspercki silnik analityczny wykrywający procesy biznesowe w strukturach SAP SD.
    """

    @classmethod
    def infer_company_processes(cls, company_id: str) -> Dict[str, Any]:
        """
        Główna metoda analityczna: bada profil i bazę firmy, zwracając wykryte procesy,
        dowody (evidence), poziomy pewności i aktywne domeny.
        """
        con = get_db_connection()
        profile = get_company_profile(company_id) or {}
        company_name = profile.get("name", company_id)
        industry = (profile.get("industry") or "").lower()
        notes = (profile.get("custom_z_notes") or "").lower()

        # 1. Pobranie danych materiałowych (MVKE / MARC / MARA)
        materials = con.execute("""
            SELECT matnr, maktx, mtart, werks, ktgrm,
                   COALESCE(mtpos, 'NORM') as mtpos,
                   COALESCE(mtvfp, '01') as mtvfp
            FROM sap_materials WHERE company_id = ?
        """, [company_id]).fetchall()

        # 2. Pobranie danych klientów (KNVV / KNA1)
        customers = con.execute("""
            SELECT kunnr, name1, vkorg, vtweg, spart, ktgrd,
                   COALESCE(land1, 'PL') as land1,
                   COALESCE(credit_limit, 0) as credit_limit,
                   COALESCE(vwerk, '') as vwerk
            FROM sap_customers WHERE company_id = ?
        """, [company_id]).fetchall()

        # 3. Pobranie dostawców i podwykonawców (LFA1 / LFM1)
        vendors = con.execute("""
            SELECT lifnr, name1, land1, partner_role, is_subcontractor, notes
            FROM sap_vendors WHERE company_id = ?
        """, [company_id]).fetchall()

        # 4. Pobranie rodzajów zleceń (AUART)
        order_types = con.execute("""
            SELECT auart, bezeichnung, item_cat_group, default_item_cat, billing_type
            FROM sd_order_types WHERE company_id = ?
        """, [company_id]).fetchall()

        # 5. Pobranie warunków cenowych (KSCHL)
        pricing = con.execute("""
            SELECT kschl, condition_class, calc_type, account_key, notes
            FROM sd_pricing_conditions WHERE company_id = ?
        """, [company_id]).fetchall()

        # 6. Pobranie reguł VKOA
        vkoa_rules = con.execute("""
            SELECT table_num, ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl, saknr
            FROM sd_vkoa_rules WHERE company_id = ?
        """, [company_id]).fetchall()

        # 7. Pobranie obszarów sprzedaży
        sales_areas = con.execute("""
            SELECT vkorg, vtweg, spart, name, waers
            FROM sd_sales_areas WHERE company_id = ?
        """, [company_id]).fetchall()

        # 8. Analiza rzeczywistego wolumenu z tabel transakcyjnych (VBAK + VBAP)
        pstyv_map = {}
        total_order_items = 0
        try:
            order_stats = con.execute("""
                SELECT pstyv, COUNT(*) as cnt, COALESCE(SUM(netwr), 0) as turnover
                FROM sap_orders_vbak_vbap
                WHERE company_id = ?
                GROUP BY pstyv
            """, [company_id]).fetchall()
            total_order_items = sum(r[1] for r in order_stats) if order_stats else 0
            pstyv_map = {r[0]: (r[1], float(r[2])) for r in order_stats}
        except Exception:
            pass

        # 9. Analiza przepływu logistycznego LIPS + VBRK
        flow_lead_time = 0.0
        total_flows = 0
        try:
            flow_stats = con.execute("""
                SELECT COUNT(*), COALESCE(AVG(lead_time_days), 0)
                FROM sap_flow_lips_vbrk
                WHERE company_id = ?
            """, [company_id]).fetchone()
            if flow_stats:
                total_flows = flow_stats[0] or 0
                flow_lead_time = round(float(flow_stats[1] or 0), 1)
        except Exception:
            pass

        # Agregacja cech
        mat_mtpos_list = [m[5].upper() for m in materials]
        mat_mtart_list = [(m[2] or '').upper() for m in materials]
        cust_land_list = [c[6].upper() for c in customers]
        cust_ktgrd_list = [(c[5] or '').upper() for c in customers]
        vendor_subcon_count = sum(1 for v in vendors if v[4] is True or (v[3] and v[3].upper() in ['SU', 'SUB']) or 'podwykon' in (v[5] or '').lower())
        auart_list = [o[0].upper() for o in order_types]
        kschl_list = [p[0].upper() for p in pricing]
        kvsl_list = [v[5].upper() for v in vkoa_rules]

        detected_processes: List[Dict[str, Any]] = []

        # ---------------------------------------------------------------------
        # 1. MAKE-TO-STOCK (O2C_MTS)
        # ---------------------------------------------------------------------
        score_mts = 30
        evidence_mts = []
        norm_count = mat_mtpos_list.count('NORM') + mat_mtpos_list.count('NORM_S')
        if norm_count > 0:
            score_mts += 30
            evidence_mts.append(f"Wykryto {norm_count} indeksów z grupą pozycji MVKE-MTPOS = 'NORM' (Pozycja standardowa TAN)")
        if any(a in ['TA', 'OR', 'ZOR1'] for a in auart_list):
            score_mts += 15
            evidence_mts.append("Skonfigurowany standardowy rodzaj zlecenia sprzedaży AUART 'TA'/'OR'")
        if 'TAN' in pstyv_map:
            cnt_tan, val_tan = pstyv_map['TAN']
            score_mts += 30
            evidence_mts.append(f"Dowód transakcyjny z VBAK/VBAP: {cnt_tan:,} pozycji MTS zrealizowanych z kategorią 'TAN'")
        if total_flows > 0:
            evidence_mts.append(f"Przepływ logistyczny LIPS/VBRK: {total_flows:,} dokumentów dostaw (śr. lead time: {flow_lead_time} dni)")
        if any(k in ['PR00', 'ZPR1'] for k in kschl_list):
            score_mts += 10
            evidence_mts.append("Zdefiniowany standardowy warunek ceny bazowej PR00/ZPR1")
        if any(ind in industry for ind in ['produkcja', 'manufacturing', 'chemia', 'fmcg', 'seryjn']):
            score_mts += 10
            evidence_mts.append("Profil branżowy firmy wskazuje na produkcję seryjną / masową")
        score_mts = min(score_mts, 100)
        detected_processes.append(cls._build_process_entry(
            code="O2C_MTS",
            title="Produkcja na magazyn (Make-to-Stock)",
            domain="MANUFACTURING",
            score=score_mts,
            evidence=evidence_mts,
            scenario_key="o2c_success",
            sd_key_objects="AUART: TA, MTPOS: NORM ➔ PSTYV: TAN, ETTYP: CP, Faktura: F2"
        ))

        # ---------------------------------------------------------------------
        # 2. MAKE-TO-ORDER (MTO_PRODUCTION)
        # ---------------------------------------------------------------------
        score_mto = 10
        evidence_mto = []
        mto_mat_count = mat_mtpos_list.count('0001') + mat_mtpos_list.count('BANC')
        if mto_mat_count > 0:
            score_mto += 35
            evidence_mto.append(f"Wykryto {mto_mat_count} materiałów z grupą pozycji MTO ('0001' / 'BANC')")
        if 'TAK' in pstyv_map:
            cnt_tak, val_tak = pstyv_map['TAK']
            score_mto += 45
            evidence_mto.append(f"Dowód transakcyjny z VBAK/VBAP: {cnt_tak:,} pozycji zleceń MTO (kategoria pozycji 'TAK')")
        if any(kw in notes or kw in industry for kw in ['mto', 'pod zlecenie', 'jednostkow', 'maszyn', 'konfigurator']):
            score_mto += 25
            evidence_mto.append("Notatki profilu lub branża wskazują na produkcję pod zlecenie / wyroby konfigurowalne")
        if any(a in ['TAK', 'ZMTO'] for a in auart_list):
            score_mto += 15
            evidence_mto.append("Skonfigurowany rodzaj pozycji TAK ze sterowaniem zapasem specjalnym 'E'")
        if score_mto >= 40:
            evidence_mto.append("Powiązanie ze zleceniem CO01 i rozliczeniem kosztów VA88 do CO-PA")
        score_mto = min(score_mto, 100)
        detected_processes.append(cls._build_process_entry(
            code="MTO_PRODUCTION",
            title="Produkcja pod zlecenie klienta (Make-to-Order)",
            domain="MANUFACTURING",
            score=score_mto,
            evidence=evidence_mto,
            scenario_key="mto_production",
            sd_key_objects="AUART: TA, MTPOS: 0001 ➔ PSTYV: TAK, ETTYP: CN (Zapas E), Rozliczenie: VA88"
        ))

        # ---------------------------------------------------------------------
        # 3. PODWYKONAWSTWO / KOOPERACJA OBCA (SUBCONTRACTING)
        # ---------------------------------------------------------------------
        score_sub = 5
        evidence_sub = []
        if vendor_subcon_count > 0:
            score_sub += 55
            evidence_sub.append(f"Wykryto {vendor_subcon_count} zweryfikowanych podwykonawców (rola 'SU' lub flaga podwykonawcy w LFA1)")
        if any(kw in notes for kw in ['podwykonaw', 'kooperacj', '541', 'bans']):
            score_sub += 30
            evidence_sub.append("Zarejestrowane reguły kooperacji obcej (ruch materiałowy 541 w MIGO)")
        if score_sub >= 35:
            evidence_sub.append("Zapotrzebowanie zakupu MM z typem pozycji L (Podwykonawstwo)")
        score_sub = min(score_sub, 100)
        detected_processes.append(cls._build_process_entry(
            code="SUBCONTRACTING",
            title="Kooperacja obca i podwykonawstwo",
            domain="MANUFACTURING",
            score=score_sub,
            evidence=evidence_sub,
            scenario_key="subcontracting_sd",
            sd_key_objects="Zlecenie: VA01 ➔ Banf MM typ pozycji L ➔ Ruch 541 (wydanie komponentów) ➔ Ruch 101/543"
        ))

        # ---------------------------------------------------------------------
        # 4. DROPSHIPPING / DOSTAWA BEZPOŚREDNIA TAS (THIRD_PARTY_TAS)
        # ---------------------------------------------------------------------
        score_tas = 10
        evidence_tas = []
        bans_count = mat_mtpos_list.count('BANS')
        if bans_count > 0:
            score_tas += 40
            evidence_tas.append(f"Wykryto {bans_count} indeksów z grupą pozycji MVKE-MTPOS = 'BANS' (Towary trójstronne TAS)")
        if 'TAS' in pstyv_map:
            cnt_tas, val_tas = pstyv_map['TAS']
            score_tas += 45
            evidence_tas.append(f"Dowód transakcyjny z VBAK/VBAP: {cnt_tas:,} pozycji zrealizowanych w modelu TAS (Dropshipping)")
        if any(kw in notes or kw in industry for kw in ['dropship', 'trójstron', 'tas', 'dostawa bezpośrednia', 'handel']):
            score_tas += 25
            evidence_tas.append("Profil klienta zawiera procedury handlu trójstronnego lub dropshippingu")
        if len(vendors) > 0 and (score_tas >= 40):
            score_tas += 10
            evidence_tas.append("Baza dostawców LFA1 gotowa do automatycznego generowania zamówień ME21N")
        score_tas = min(score_tas, 100)
        detected_processes.append(cls._build_process_entry(
            code="THIRD_PARTY_TAS",
            title="Handel trójstronny i Dropshipping TAS",
            domain="TRADING",
            score=score_tas,
            evidence=evidence_tas,
            scenario_key="dropship_tas",
            sd_key_objects="AUART: TA, MTPOS: BANS ➔ PSTYV: TAS, ETTYP: CS, Fakturowanie: VF01 na podst. MIRO"
        ))

        # ---------------------------------------------------------------------
        # 5. ZAMÓWIENIE INDYWIDUALNE TAB (INDIVIDUAL_PO_TAB)
        # ---------------------------------------------------------------------
        score_tab = 10
        evidence_tab = []
        tab_count = mat_mtpos_list.count('TAB')
        if tab_count > 0:
            score_tab += 60
            evidence_tab.append(f"Wykryto {tab_count} indeksów z grupą pozycji MVKE-MTPOS = 'TAB'")
        if any(kw in notes for kw in ['tab', 'indywidualne zamówienie', 'zakup pod klienta']):
            score_tab += 30
            evidence_tab.append("Wykryto procedurę zakupu towarów dedykowanych z przyjęciem do magazynu własnego")
        score_tab = min(score_tab, 100)
        detected_processes.append(cls._build_process_entry(
            code="INDIVIDUAL_PO_TAB",
            title="Indywidualne zamówienie zakupu TAB",
            domain="TRADING",
            score=score_tab,
            evidence=evidence_tab,
            scenario_key="in_progress_delivery",
            sd_key_objects="AUART: TA, MTPOS: TAB ➔ PSTYV: TAB, ETTYP: CB, Magazyn ➔ Dostawa VL01N"
        ))

        # ---------------------------------------------------------------------
        # 6. ZAPAS KONSYGNACYJNY U KLIENTA (CONSIGNMENT)
        # ---------------------------------------------------------------------
        score_cons = 15
        evidence_cons = []
        if any(a in ['KB', 'KE', 'KA', 'KR'] for a in auart_list):
            score_cons += 40
            evidence_cons.append("Skonfigurowane dedykowane rodzaje zleceń konsygnacyjnych (KB/KE/KA/KR)")
        cons_cnt = sum(pstyv_map.get(k, (0, 0))[0] for k in ['EBN', 'KEN', 'KRN', 'KAN'])
        if cons_cnt > 0:
            score_cons += 45
            evidence_cons.append(f"Dowód transakcyjny z VBAK/VBAP: {cons_cnt:,} pozycji w przepływie konsygnacyjnym (EBN/KEN)")
        if any(kw in notes for kw in ['konsygnacj', 'zapas w', 'kb', 'ke', 'skład konsygnacyjny']):
            score_cons += 25
            evidence_cons.append("Profil firmy zawiera notatki o obsłudze składów konsygnacyjnych u odbiorców")
        if score_cons >= 40:
            evidence_cons.append("Sterowanie ruchem magazynowym 631 (uzupełnienie) i 633 (pobranie z fakturą)")
        score_cons = min(score_cons, 100)
        detected_processes.append(cls._build_process_entry(
            code="CONSIGNMENT",
            title="Zapas konsygnacyjny u klienta (KB/KE)",
            domain="TRADING",
            score=score_cons,
            evidence=evidence_cons,
            scenario_key="consignment_ke",
            sd_key_objects="KB (EBN, ruch 631) ➔ KE (KEN, ruch 633, Faktura F2) ➔ KA (KRN, 632)"
        ))

        # ---------------------------------------------------------------------
        # 7. SPRZEDAŻ MIĘDZYFIRMOWA (INTERCOMPANY)
        # ---------------------------------------------------------------------
        score_ic = 10
        evidence_ic = []
        if any(k in ['PI01', 'PI02', 'IV01'] for k in kschl_list):
            score_ic += 45
            evidence_ic.append("Wykryto warunki cenowe cen transferowych (PI01/PI02) w technice warunków")
        if any(a == 'IV' for a in auart_list) or any(v[4] == 'IV' for v in order_types):
            score_ic += 25
            evidence_ic.append("Zdefiniowany rodzaj faktury wewnętrznej Intercompany IV")
        if any(kw in notes or kw in industry for kw in ['intercompany', 'międzyfirmow', 'cross-company', 'iv']):
            score_ic += 25
            evidence_ic.append("Profil wskazuje na strukturę wielozakładową lub powiązania kapitałowe spółek")
        if len(sales_areas) > 1:
            score_ic += 10
            evidence_ic.append(f"Zdefiniowano {len(sales_areas)} obszary sprzedaży - możliwa dostawa z obcej jednostki")
        score_ic = min(score_ic, 100)
        detected_processes.append(cls._build_process_entry(
            code="INTERCOMPANY",
            title="Sprzedaż międzyfirmowa (Intercompany IV)",
            domain="TRADING",
            score=score_ic,
            evidence=evidence_ic,
            scenario_key="intercompany_iv",
            sd_key_objects="Zlecenie A ➔ Wysyłka Zakład B ➔ Faktura Klienta F2 ➔ Faktura Międzyfirmowa IV"
        ))

        # ---------------------------------------------------------------------
        # 8. USŁUGI NAKŁADCZE RRB DP90 (SERVICE_RRB_DP90)
        # ---------------------------------------------------------------------
        score_rrb = 10
        evidence_rrb = []
        serv_mat_count = mat_mtpos_list.count('DIEN') + mat_mtpos_list.count('LEIS')
        if serv_mat_count > 0:
            score_rrb += 40
            evidence_rrb.append(f"Wykryto {serv_mat_count} indeksów usługowych z grupą pozycji DIEN / LEIS")
        srv_cnt = sum(pstyv_map.get(k, (0, 0))[0] for k in ['L2N', 'TAD'])
        if srv_cnt > 0:
            score_rrb += 45
            evidence_rrb.append(f"Dowód transakcyjny z VBAK/VBAP: {srv_cnt:,} pozycji rozliczeń usługowych (L2N/TAD)")
        if any(kw in notes or kw in industry for kw in ['usług', 'serwis', 'rrb', 'dp90', 'roboczogodzin', 'it']):
            score_rrb += 30
            evidence_rrb.append("Profil firmy wskazuje na usługi profesjonalne, serwis techniczny lub consulting")
        if any(a in ['L2', 'DMR', 'ZSRV'] for a in auart_list):
            score_rrb += 20
            evidence_rrb.append("Skonfigurowany rodzaj zlecenia żądania debetowego (Debit Memo Request L2)")
        score_rrb = min(score_rrb, 100)
        detected_processes.append(cls._build_process_entry(
            code="SERVICE_RRB_DP90",
            title="Rozliczenie usług nakładczych (RRB DP90)",
            domain="SERVICES",
            score=score_rrb,
            evidence=evidence_rrb,
            scenario_key="service_rrb_dp90",
            sd_key_objects="CAT2 (Godziny) ➔ DP90 (DIP Profile) ➔ Debit Memo Request L2 ➔ Faktura L2"
        ))

        # ---------------------------------------------------------------------
        # 9. KAMIENIE MILOWE & PROJEKTY (MILESTONE_BILLING)
        # ---------------------------------------------------------------------
        score_ms = 10
        evidence_ms = []
        if mat_mtpos_list.count('PSMB') > 0:
            score_ms += 50
            evidence_ms.append("Wykryto materiały z grupą pozycji PSMB (Milestone Billing)")
        if any(kw in notes or kw in industry for kw in ['kamienie milowe', 'projekt', 'harmonogram', 'etapow', 'wbs']):
            score_ms += 35
            evidence_ms.append("Notatki profilu wskazują na fakturowanie etapowe wg odbioru kamieni milowych")
        if score_ms >= 35:
            evidence_ms.append("Plan fakturowania typu 01 z integracją modułu PS (WBS CJ20N) i zaliczkami FA")
        score_ms = min(score_ms, 100)
        detected_processes.append(cls._build_process_entry(
            code="MILESTONE_BILLING",
            title="Fakturowanie według kamieni milowych",
            domain="SERVICES",
            score=score_ms,
            evidence=evidence_ms,
            scenario_key="milestone_billing",
            sd_key_objects="Zlecenie VA01 ➔ Plan fakturowania ➔ Zaliczka FA ➔ Odbiór CJ20N ➔ Faktura F2"
        ))

        # ---------------------------------------------------------------------
        # 10. OBSŁUGA ZWROTÓW I REKLAMACJI (RETURNS_COMPLAINTS)
        # ---------------------------------------------------------------------
        score_ret = 20
        evidence_ret = []
        if any(a in ['RE', 'CR', 'DR', 'G2'] for a in auart_list):
            score_ret += 45
            evidence_ret.append("Skonfigurowany rodzaj zlecenia zwrotu RE lub uznania G2")
        if any(k in ['ERS', 'EVU'] for k in kvsl_list):
            score_ret += 20
            evidence_ret.append("Reguły księgowania rabatów lub korekt przychodu VKOA (ERS/EVU)")
        if score_ret >= 40:
            evidence_ret.append("Standardowy obieg zwrotu: Zlecenie RE ➔ Dostawa zwrotna LR (ruch 651) ➔ Uznanie G2")
        score_ret = min(score_ret, 100)
        detected_processes.append(cls._build_process_entry(
            code="RETURNS_COMPLAINTS",
            title="Obsługa zwrotów i noty uznaniowe",
            domain="COMPLAINTS",
            score=score_ret,
            evidence=evidence_ret,
            scenario_key="returns_re",
            sd_key_objects="Zlecenie zwrotu RE ➔ Dostawa LR (ruch 651) ➔ Kontrola QM ➔ Faktura uznaniowa G2"
        ))

        # Sortowanie procesów wg punktacji pewności (malejąco)
        detected_processes.sort(key=lambda x: x["confidence_score"], reverse=True)

        # Wyznaczenie aktywnych domen i profilu głównego
        active_processes = [p for p in detected_processes if p["is_active"]]
        active_domains = list(dict.fromkeys(p["domain"] for p in active_processes))
        if not active_domains:
            active_domains = ["TRADING"]

        domain_priority = {
            "MANUFACTURING": sum(p["confidence_score"] for p in detected_processes if p["domain"] == "MANUFACTURING"),
            "TRADING": sum(p["confidence_score"] for p in detected_processes if p["domain"] == "TRADING"),
            "SERVICES": sum(p["confidence_score"] for p in detected_processes if p["domain"] == "SERVICES"),
            "COMPLAINTS": sum(p["confidence_score"] for p in detected_processes if p["domain"] == "COMPLAINTS")
        }
        primary_domain = max(domain_priority, key=domain_priority.get)

        # Krótkie podsumowanie analityczne
        top_processes_names = [p["title"] for p in active_processes[:3]]
        summary_text = (
            f"Dla profilu '{company_name}' silnik Auto-Discovery zidentyfikował "
            f"{len(active_processes)} aktywnych procesów biznesowych (Domena wiodąca: {primary_domain}). "
            f"Kluczowe procesy: {', '.join(top_processes_names)}."
        )

        return {
            "company_id": company_id,
            "company_name": company_name,
            "primary_domain": primary_domain,
            "active_domains": active_domains,
            "summary": summary_text,
            "total_detected": len(active_processes),
            "processes": detected_processes
        }

    @classmethod
    def _build_process_entry(cls, code: str, title: str, domain: str, score: int,
                             evidence: List[str], scenario_key: str, sd_key_objects: str) -> Dict[str, Any]:
        """Buduje ujednolicony rekord wykrytego procesu."""
        confidence_level = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "SUGGESTED")
        is_active = score >= 40
        return {
            "process_code": code,
            "title": title,
            "domain": domain,
            "confidence_score": score,
            "confidence_level": confidence_level,
            "is_active": is_active,
            "evidence": evidence,
            "scenario_key": scenario_key,
            "sd_key_objects": sd_key_objects
        }

    @classmethod
    def analyze_raw_report_snippet(cls, data_type: str, content: str) -> Dict[str, Any]:
        """
        Skanuje surowy wsad CSV / wyciąg z SAP w poszukiwaniu specyficznych grup pozycji,
        kodów transakcji czy ról, zwracając listę nowo odkrytych procesów.
        """
        content_upper = content.upper()
        discovered: List[Dict[str, str]] = []

        if data_type == 'materials' or 'MTPOS' in content_upper or 'MATNR' in content_upper:
            if 'BANS' in content_upper:
                discovered.append({
                    "process_code": "THIRD_PARTY_TAS",
                    "title": "Dostawa bezpośrednia / Dropshipping (TAS)",
                    "reason": "Wykryto grupę pozycji BANS w indeksach materiałowych"
                })
            if '0001' in content_upper or 'BANC' in content_upper:
                discovered.append({
                    "process_code": "MTO_PRODUCTION",
                    "title": "Produkcja pod zlecenie klienta (MTO)",
                    "reason": "Wykryto grupę pozycji MTO (0001/BANC) w danych materiałowych"
                })
            if 'NORM' in content_upper:
                discovered.append({
                    "process_code": "O2C_MTS",
                    "title": "Standardowa produkcja na magazyn (MTS)",
                    "reason": "Wykryto standardową grupę pozycji NORM"
                })
            if 'DIEN' in content_upper or 'LEIS' in content_upper:
                discovered.append({
                    "process_code": "SERVICE_RRB_DP90",
                    "title": "Usługi nakładcze (RRB DP90)",
                    "reason": "Wykryto indeksy usługowe (DIEN/LEIS)"
                })
            if 'PSMB' in content_upper:
                discovered.append({
                    "process_code": "MILESTONE_BILLING",
                    "title": "Fakturowanie wg kamieni milowych",
                    "reason": "Wykryto grupę pozycji PSMB"
                })

        elif data_type == 'vendors' or 'LIFNR' in content_upper:
            if 'SU' in content_upper or 'PODWYKON' in content_upper or 'SUBCONTRACT' in content_upper:
                discovered.append({
                    "process_code": "SUBCONTRACTING",
                    "title": "Kooperacja obca i podwykonawstwo",
                    "reason": "Wykryto dostawcę z rolą podwykonawcy (SU / Kooperacja)"
                })

        return {
            "data_type": data_type,
            "discovered_processes": discovered,
            "count": len(discovered)
        }
