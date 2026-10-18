# -*- coding: utf-8 -*-
"""
Serwis procesów biznesowych przedsiębiorstwa (Enterprise Processes) i symulacji Document Flow.
Obsługuje pełne spektrum procesów dla firm produkcyjnych, handlowo-dystrybucyjnych,
usługowo-projektowych oraz logistyki posprzedażowej (reklamacje i zwroty).
"""

from typing import List, Dict, Any, Optional
from app.database.db_manager import get_db_connection, get_company_profile
from app.database.process_data import ENTERPRISE_PROCESSES

def get_available_processes(domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Zwraca listę wszystkich dostępnych procesów biznesowych z metadanymi i podsumowaniem integracji.
    Możliwość filtrowania po domenie: MANUFACTURING, TRADING, SERVICES, COMPLAINTS.
    """
    result = []
    for p in ENTERPRISE_PROCESSES:
        if domain and domain.upper() != 'ALL' and p["business_domain"] != domain.upper():
            continue
        result.append({
            "process_code": p["process_code"],
            "process_name": p["process_name"],
            "business_domain": p["business_domain"],
            "domain_name": p["domain_name"],
            "description": p["description"],
            "industry_fit": p["industry_fit"],
            "key_tcodes": p["key_tcodes"],
            "item_categories": p["item_categories"],
            "schedule_line_cats": p["schedule_line_cats"],
            "billing_types": p["billing_types"],
            "integration_modules": p["integration_modules"],
            "step_count": len(p.get("steps", []))
        })
    return result

def get_sd_process_catalog(process_code: Optional[str] = None, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Pobiera katalog etapów procesowych z bazy danych DuckDB.
    Wspiera filtrowanie po konkretnym kodzie procesu lub dziedzinie biznesowej.
    """
    con = get_db_connection()
    query = """
        SELECT step_order, phase, tcode, name, description, prerequisites, tables_involved, doc_type, module, process_code, process_name, business_domain
        FROM sd_process_catalog
        WHERE 1=1
    """
    params = []
    if process_code and process_code.upper() != 'ALL':
        query += " AND process_code = ?"
        params.append(process_code)
    elif domain and domain.upper() != 'ALL':
        query += " AND business_domain = ?"
        params.append(domain.upper())

    query += " ORDER BY process_code, step_order"
    rows = con.execute(query, params).fetchall()

    return [{
        "step": r[0],
        "phase": r[1],
        "tcode": r[2],
        "name": r[3],
        "desc": r[4],
        "prereq": r[5],
        "tables": r[6],
        "doc_type": r[7],
        "module": r[8],
        "process_code": r[9],
        "process_name": r[10],
        "business_domain": r[11]
    } for r in rows]

def get_available_scenarios(company_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Zwraca listę wszystkich zdefiniowanych scenariuszy Document Flow z podziałem na branże.
    Jeśli podano company_id, wzbogaca scenariusze o autodetekcję (confidence, evidence, is_inferred).
    """
    from app.services.process_inference_service import ProcessInferenceService

    raw_scenarios = [
        {
            "id": "vfx3_blocked",
            "scenario_key": "vfx3_blocked",
            "title": "Standard O2C (MTS): Blokada VFX3 (Błąd konta VKOA)",
            "scenario_title": "Standard O2C (MTS): Blokada VFX3 (Błąd konta VKOA)",
            "domain": "TRADING",
            "domain_label": "Handel & Dystrybucja",
            "badge_color": "rose",
            "process_code": "O2C_MTS",
            "steps_count": 6,
            "default_status": "error",
            "sd_key_objects": "VOV4: TA+NORM➔TAN, VOV6: TAN➔CP, VKOA: KOFI00 (Brak reguły)"
        },
        {
            "id": "o2c_success",
            "scenario_key": "o2c_success",
            "title": "Standard O2C (MTS): Sukces księgowania w FI",
            "scenario_title": "Standard O2C (MTS): Sukces księgowania w FI",
            "domain": "TRADING",
            "domain_label": "Handel & Dystrybucja",
            "badge_color": "emerald",
            "process_code": "O2C_MTS",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "VOV4: TA+NORM➔TAN, VOV6: TAN➔CP, VTFL: LF➔F2, VKOA: 800000"
        },
        {
            "id": "in_progress_delivery",
            "scenario_key": "in_progress_delivery",
            "title": "Standard O2C: W trakcie (Oczekuje na PGI ruch 601)",
            "scenario_title": "Standard O2C: W trakcie (Oczekuje na PGI ruch 601)",
            "domain": "TRADING",
            "domain_label": "Handel & Dystrybucja",
            "badge_color": "amber",
            "process_code": "O2C_MTS",
            "steps_count": 5,
            "default_status": "warning",
            "sd_key_objects": "VA01 ➔ VL01N (LF) ➔ Status WBSTK='A' (W realizacji)"
        },
        {
            "id": "dropship_tas",
            "scenario_key": "dropship_tas",
            "title": "Handel trójstronny: Dropshipping TAS (SD ➔ MM ➔ FI)",
            "scenario_title": "Handel trójstronny: Dropshipping TAS (SD ➔ MM ➔ FI)",
            "domain": "TRADING",
            "domain_label": "Handel & Dystrybucja",
            "badge_color": "sky",
            "process_code": "THIRD_PARTY_TAS",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "VOV4: TA+BANS➔TAS, VOV6: TAS➔CS (Banf MM), Fakturowanie: VF01 na podst. MIRO"
        },
        {
            "id": "consignment_ke",
            "scenario_key": "consignment_ke",
            "title": "Konsygnacja u klienta: Uzupełnienie KB ➔ Pobranie KE (Zapas W)",
            "scenario_title": "Konsygnacja u klienta: Uzupełnienie KB ➔ Pobranie KE (Zapas W)",
            "domain": "TRADING",
            "domain_label": "Handel & Dystrybucja",
            "badge_color": "indigo",
            "process_code": "CONSIGNMENT",
            "steps_count": 7,
            "default_status": "completed",
            "sd_key_objects": "KB (EBN, ruch 631) ➔ KE (KEN, ruch 633, Faktura F2) ➔ KA (KRN, ruch 632)"
        },
        {
            "id": "intercompany_iv",
            "scenario_key": "intercompany_iv",
            "title": "Sprzedaż międzyfirmowa: Wysyłka ze Spółki B ➔ Faktura IV",
            "scenario_title": "Sprzedaż międzyfirmowa: Wysyłka ze Spółki B ➔ Faktura IV",
            "domain": "TRADING",
            "domain_label": "Handel & Produkcja",
            "badge_color": "purple",
            "process_code": "INTERCOMPANY",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "Faktura F2 (Spółka A) + Faktura IV (Spółka B), Warunki: PI01/PI02"
        },
        {
            "id": "mto_production",
            "scenario_key": "mto_production",
            "title": "Produkcja MTO: Zlecenie VA01 ➔ Zlecenie CO01 ➔ Zapas E ➔ VA88",
            "scenario_title": "Produkcja MTO: Zlecenie VA01 ➔ Zlecenie CO01 ➔ Zapas E ➔ VA88",
            "domain": "MANUFACTURING",
            "domain_label": "Firmy Produkcyjne",
            "badge_color": "blue",
            "process_code": "MTO_PRODUCTION",
            "steps_count": 7,
            "default_status": "completed",
            "sd_key_objects": "VOV4: TA+0001➔TAK, VOV6: TAK➔CN (Zapas E), Klasa zapotrzebowań: 040, Rozliczenie: VA88"
        },
        {
            "id": "subcontracting_sd",
            "scenario_key": "subcontracting_sd",
            "title": "Podwykonawstwo: Wydanie 541 ➔ Przyjęcie 101/543 ➔ Montaż i wysyłka",
            "scenario_title": "Podwykonawstwo: Wydanie 541 ➔ Przyjęcie 101/543 ➔ Montaż i wysyłka",
            "domain": "MANUFACTURING",
            "domain_label": "Firmy Produkcyjne",
            "badge_color": "teal",
            "process_code": "SUBCONTRACTING",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "VA01 ➔ Banf typ pozycji L ➔ Ruch 541 (komponenty) ➔ Ruch 101/543 ➔ Wysyłka VL01N"
        },
        {
            "id": "service_rrb_dp90",
            "scenario_key": "service_rrb_dp90",
            "title": "Usługi nakładcze: Zlecenie serwisowe ➔ Godziny CAT2 ➔ DP90 ➔ Faktura L2",
            "scenario_title": "Usługi nakładcze: Zlecenie serwisowe ➔ Godziny CAT2 ➔ DP90 ➔ Faktura L2",
            "domain": "SERVICES",
            "domain_label": "Usługi & Projekty",
            "badge_color": "amber",
            "process_code": "SERVICE_RRB_DP90",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "CAT2 (Godziny) ➔ DP90 (DIP Profile) ➔ DMR (L2/L2N) ➔ Faktura L2"
        },
        {
            "id": "milestone_billing",
            "scenario_key": "milestone_billing",
            "title": "Kamienie milowe: Plan fakturowania ➔ Zaliczka FA ➔ Odbiór CJ20N ➔ F2",
            "scenario_title": "Kamienie milowe: Plan fakturowania ➔ Zaliczka FA ➔ Odbiór CJ20N ➔ F2",
            "domain": "SERVICES",
            "domain_label": "Usługi & Projekty",
            "badge_color": "cyan",
            "process_code": "MILESTONE_BILLING",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "Plan fakturowania typ 01, Zaliczka FA, Odbiór WBS CJ20N, Faktura F2"
        },
        {
            "id": "returns_re",
            "scenario_key": "returns_re",
            "title": "Zwroty & Reklamacje: Zlecenie RE ➔ Dostawa LR (651) ➔ Uznanie G2",
            "scenario_title": "Zwroty & Reklamacje: Zlecenie RE ➔ Dostawa LR (651) ➔ Uznanie G2",
            "domain": "COMPLAINTS",
            "domain_label": "Obsługa Zwrotów & QM",
            "badge_color": "rose",
            "process_code": "RETURNS_COMPLAINTS",
            "steps_count": 6,
            "default_status": "completed",
            "sd_key_objects": "AUART: RE ➔ PSTYV: REN ➔ Dostawa LR (Ruch 651) ➔ Faktura uznaniowa G2"
        }
    ]

    # Jeśli podano firmę, wzbogacamy o autodetekcję
    if company_id:
        try:
            inferred = ProcessInferenceService.infer_company_processes(company_id)
            proc_map = {p["process_code"]: p for p in inferred.get("processes", [])}

            for sc in raw_scenarios:
                inf = proc_map.get(sc["process_code"])
                if inf:
                    sc["is_inferred"] = inf["is_active"]
                    sc["confidence_score"] = inf["confidence_score"]
                    sc["confidence_level"] = inf["confidence_level"]
                    sc["evidence"] = inf["evidence"]
                    if inf["sd_key_objects"]:
                        sc["sd_key_objects"] = inf["sd_key_objects"]
                else:
                    sc["is_inferred"] = False
                    sc["confidence_score"] = 25
                    sc["confidence_level"] = "SUGGESTED"
                    sc["evidence"] = []

            # Sortowanie: najpierw aktywnie wykryte z najwyższą pewnością
            raw_scenarios.sort(key=lambda s: s.get("confidence_score", 0), reverse=True)
        except Exception as e:
            print(f"Błąd wnioskowania procesów w get_available_scenarios: {e}")

    return raw_scenarios

def get_document_flow_scenarios(company_id: str = "CLIENT_A", scenario: str = "vfx3_blocked") -> Dict[str, Any]:
    """
    Generuje realistyczny łańcuch Document Flow (SD-MM-PP-FI-CO-PS) dla wybranego klienta i scenariusza.
    """
    profile = get_company_profile(company_id) or {}
    ktopl = profile.get("ktopl", "INT")
    bukrs = profile.get("bukrs", "1000")
    waers = profile.get("waers", "EUR")

    if scenario == "success" or scenario == "o2c_success":
        return {
            "scenario_id": "o2c_success",
            "scenario_title": "Standard O2C (MTS): Pełny Sukces (Zaksięgowano w Finansach)",
            "business_domain": "TRADING",
            "domain_name": "Handel & Produkcja Seryjna",
            "process_code": "O2C_MTS",
            "overall_status": "success",
            "order_number": "10004562",
            "customer_id": "C-10001",
            "item_category": "TAN",
            "integration_summary": "Przepływ dokumentów bezbłędny. Zlecenie sprzedaży ➔ Dostawa LF ➔ Wydanie towaru 601 ➔ Faktura F2 ➔ Księgowanie FI-AR.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zapytanie i Oferta Handlowa",
                    "phase": "Pre-sales",
                    "doc_type": "QT",
                    "doc_number": "20000319",
                    "tcode": "VA23",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zrealizowano",
                    "date": "2026-09-06",
                    "value": f"18 500,00 {waers}",
                    "details": "Oferta handlowa zaakceptowana przez klienta."
                },
                {
                    "step_number": 2,
                    "name": "Zlecenie Sprzedaży (Sales Order)",
                    "phase": "Sales Order",
                    "doc_type": "TA / OR",
                    "doc_number": "10004562",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Otwarte do dostawy",
                    "date": "2026-09-07",
                    "value": f"18 500,00 {waers}",
                    "details": "Pozycja: TAN, Linia harmonogramu: CP. Sprawdzenie zapasu wolnego ATP: Dostępny."
                },
                {
                    "step_number": 3,
                    "name": "Dostawa Wychodząca (Outbound Delivery)",
                    "phase": "Shipping",
                    "doc_type": "LF",
                    "doc_number": "80012841",
                    "tcode": "VL03N",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Skompletowano",
                    "date": "2026-09-08 08:30",
                    "value": "-",
                    "details": "Zlecenie przeniesienia WM/EWM potwierdzone, kontrola wagi i etykiety SSCC zgodne."
                },
                {
                    "step_number": 4,
                    "name": "Wydanie Towarów (Post Goods Issue - PGI)",
                    "phase": "Goods Issue",
                    "doc_type": "WA / MatDoc",
                    "doc_number": "4900182415",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "completed",
                    "status_label": "Wydano (Ruch 601)",
                    "date": "2026-09-08 10:15",
                    "value": "-",
                    "details": "Księgowanie rozchodu magazynowego. Wartość COGS zredukowała stan magazynu."
                },
                {
                    "step_number": 5,
                    "name": "Faktura Sprzedaży (Billing Document)",
                    "phase": "Billing",
                    "doc_type": "F2",
                    "doc_number": "90045102",
                    "tcode": "VF03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zafakturowano",
                    "date": "2026-09-08 10:16",
                    "value": f"18 500,00 {waers}",
                    "details": "Faktura F2 utworzona poprawnie, status zwolnienia do księgowości = C (Zwolniona)."
                },
                {
                    "step_number": 6,
                    "name": "Księgowanie w Finansach (FI Accounting Doc)",
                    "phase": "Accounting",
                    "doc_type": "RV",
                    "doc_number": "140000088",
                    "tcode": "FB03",
                    "module": "FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano w FI-AR",
                    "date": "2026-09-08 10:16",
                    "value": f"18 500,00 {waers}",
                    "details": f"Konto przychodów 800000 (ERL), Plan kont: {ktopl}, BUKRS: {bukrs}. Brak jakichkolwiek blokad."
                }
            ]
        }

    elif scenario == "in_progress_delivery":
        return {
            "scenario_id": "in_progress_delivery",
            "scenario_title": "W trakcie realizacji: Dostawa utworzona, oczekuje na wydanie (PGI)",
            "business_domain": "TRADING",
            "domain_name": "Handel & Logistyka",
            "process_code": "O2C_MTS",
            "overall_status": "warning",
            "order_number": "10004572",
            "customer_id": "C-10002",
            "item_category": "TAN",
            "integration_summary": "Dostawa skompletowana w magazynie, oczekuje na zatwierdzenie wydania towarów (PGI ruch 601) przed wystawieniem faktury.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zapytanie i Oferta Handlowa",
                    "phase": "Pre-sales",
                    "doc_type": "QT",
                    "doc_number": "20000322",
                    "tcode": "VA23",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zrealizowano",
                    "date": "2026-09-10",
                    "value": f"8 900,00 {waers}",
                    "details": "Oferta zaakceptowana."
                },
                {
                    "step_number": 2,
                    "name": "Zlecenie Sprzedaży (Sales Order)",
                    "phase": "Sales Order",
                    "doc_type": "TA / OR",
                    "doc_number": "10004572",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "W realizacji",
                    "date": "2026-09-11 08:00",
                    "value": f"8 900,00 {waers}",
                    "details": "Zlecenie zatwierdzone, termin dostawy dzisiaj."
                },
                {
                    "step_number": 3,
                    "name": "Dostawa Wychodząca (Outbound Delivery)",
                    "phase": "Shipping",
                    "doc_type": "LF",
                    "doc_number": "80012855",
                    "tcode": "VL02N",
                    "module": "SD",
                    "status": "warning",
                    "status_label": "Oczekuje na PGI",
                    "date": "2026-09-11 11:15",
                    "value": "-",
                    "details": "Dostawa w trakcie kompletacji na magazynie. Brak zatwierdzonego wydania towaru (Post Goods Issue)."
                },
                {
                    "step_number": 4,
                    "name": "Wydanie Towarów (Post Goods Issue)",
                    "phase": "Goods Issue",
                    "doc_type": "WA",
                    "doc_number": "Oczekuje",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "pending",
                    "status_label": "Niewykonane",
                    "date": "-",
                    "value": "-",
                    "details": "Wymagane wykonanie VL02N -> Księguj wydanie towaru (ruch 601)."
                },
                {
                    "step_number": 5,
                    "name": "Faktura Sprzedaży (Billing Document)",
                    "phase": "Billing",
                    "doc_type": "F2",
                    "doc_number": "Oczekuje",
                    "tcode": "VF01",
                    "module": "SD",
                    "status": "pending",
                    "status_label": "Blokada fakturowania",
                    "date": "-",
                    "value": "-",
                    "details": "Fakturowanie możliwe dopiero po skutecznym PGI."
                }
            ]
        }

    elif scenario == "mto_production":
        return {
            "scenario_id": "mto_production",
            "scenario_title": "Produkcja na zlecenie klienta (Make-to-Order MTO)",
            "business_domain": "MANUFACTURING",
            "domain_name": "Firmy Produkcyjne & Inżynieryjne",
            "process_code": "MTO_PRODUCTION",
            "overall_status": "success",
            "order_number": "10009840",
            "customer_id": "C-10001",
            "item_category": "TAK (MTO Item)",
            "integration_summary": "Zintegrowany łańcuch SD-PP-CO-MM: Zlecenie sprzedaży steruje zleceniem produkcyjnym, zapas specjalny 'E' i rozliczenie wyniku zlecenia do CO-PA.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie Sprzedaży MTO",
                    "phase": "Sales Order",
                    "doc_type": "TA / MS",
                    "doc_number": "10009840",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zapas 'E' aktywny",
                    "date": "2026-09-01",
                    "value": f"145 000,00 {waers}",
                    "details": "Pozycja TAK, Klasa zapotrzebowań 040 (MTO). Zlecenie sprzedaży jest nośnikiem kosztów."
                },
                {
                    "step_number": 2,
                    "name": "Kalkulacja Kosztów Zlecenia (Unit Costing)",
                    "phase": "Controlling",
                    "doc_type": "Cost Estimate",
                    "doc_number": "CK-9840",
                    "tcode": "CK51N",
                    "module": "CO",
                    "status": "completed",
                    "status_label": "Skalkulowano",
                    "date": "2026-09-02",
                    "value": f"98 400,00 {waers}",
                    "details": "Wyznaczony koszt wytworzenia (COGM) na podstawie aktualnych cen surowców i stawek robocizny."
                },
                {
                    "step_number": 3,
                    "name": "Zlecenie Produkcyjne (PP Order)",
                    "phase": "Production",
                    "doc_type": "PP (CO01)",
                    "doc_number": "60004120",
                    "tcode": "CO03",
                    "module": "PP",
                    "status": "completed",
                    "status_label": "Potwierdzone (CNF)",
                    "date": "2026-09-05",
                    "value": "-",
                    "details": "Powiązane ze zleceniem sprzedaży 10009840/10. Pobranie komponentów (ruch 261) i robocizna (CO11N)."
                },
                {
                    "step_number": 4,
                    "name": "Przyjęcie Wyrobu na Zapas Zlecenia (Ruch 101 E)",
                    "phase": "Goods Receipt",
                    "doc_type": "MatDoc (101 E)",
                    "doc_number": "4900199120",
                    "tcode": "MIGO",
                    "module": "MM/PP",
                    "status": "completed",
                    "status_label": "Na stanie 'E'",
                    "date": "2026-09-08 14:00",
                    "value": "-",
                    "details": "Wyrób gotowy przyjęty na stan dedykowany dla zlecenia 10009840 (MSKA zapas specjalny klienta)."
                },
                {
                    "step_number": 5,
                    "name": "Dostawa Wychodząca & Wydanie Towaru (Ruch 601 E)",
                    "phase": "Shipping",
                    "doc_type": "LF / WA",
                    "doc_number": "80012990",
                    "tcode": "VL02N",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Wydano z zapasu E",
                    "date": "2026-09-09 11:00",
                    "value": "-",
                    "details": "Pobranie dedykowanego wyrobu ze składu zlecenia klienta i wysyłka transportem dedykowanym."
                },
                {
                    "step_number": 6,
                    "name": "Faktura Sprzedaży (Billing Document)",
                    "phase": "Billing",
                    "doc_type": "F2",
                    "doc_number": "90045220",
                    "tcode": "VF03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zaksięgowano",
                    "date": "2026-09-09 15:30",
                    "value": f"145 000,00 {waers}",
                    "details": "Faktura F2 przekazana do FI i KSeF/EDI."
                },
                {
                    "step_number": 7,
                    "name": "Rozliczenie Zlecenia do CO-PA",
                    "phase": "Settlement",
                    "doc_type": "Settlement",
                    "doc_number": "VA88-DOC",
                    "tcode": "VA88",
                    "module": "CO-PA",
                    "status": "completed",
                    "status_label": "Rozliczono marżę",
                    "date": "2026-09-10",
                    "value": f"Marża: +46 600,00 {waers}",
                    "details": "Narzuty kosztów ogólnych rozliczone. Rzeczywisty wynik marżowy przekazany do rachunku wyników CO-PA."
                }
            ]
        }

    elif scenario == "subcontracting_sd":
        return {
            "scenario_id": "subcontracting_sd",
            "scenario_title": "Kooperacja i Podwykonawstwo (Subcontracting in Sales)",
            "business_domain": "MANUFACTURING",
            "domain_name": "Produkcja & Kooperacja Obca",
            "process_code": "SUBCONTRACTING",
            "overall_status": "success",
            "order_number": "10009450",
            "customer_id": "C-10001",
            "item_category": "TAN / L (Subcontracting)",
            "integration_summary": "Łańcuch SD-PP-MM: Wyrób wymaga powierzenia surowców podwykonawcy (ruch 541 na stan 'O'), przyjęcia gotowej usługi (ruch 101/543) i wysyłki do klienta.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie Sprzedaży Wyrobu Kooperowanego",
                    "phase": "Sales Order",
                    "doc_type": "TA",
                    "doc_number": "10009450",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Wymaga obróbki obcej",
                    "date": "2026-09-02",
                    "value": f"68 000,00 {waers}",
                    "details": "Zlecenie sprzedaży 50 szt. przekładni. Wymagana zewnętrzna galwanizacja i hartowanie."
                },
                {
                    "step_number": 2,
                    "name": "Zamówienie Usługi Podwykonawczej (PO Typ L)",
                    "phase": "Subcontract PO",
                    "doc_type": "NB (Item L)",
                    "doc_number": "4500029800",
                    "tcode": "ME23N",
                    "module": "MM",
                    "status": "completed",
                    "status_label": "Zamówiono usługę",
                    "date": "2026-09-03",
                    "value": f"12 500,00 {waers}",
                    "details": "Zamówienie usługi u dostawcy Galwanotechnika Śląsk Sp. z o.o. z wykazem powierzanych komponentów."
                },
                {
                    "step_number": 3,
                    "name": "Wydanie Komponentów do Podwykonawcy (Ruch 541)",
                    "phase": "Component Issue",
                    "doc_type": "MatDoc (541)",
                    "doc_number": "4900193100",
                    "tcode": "ME2O / MIGO",
                    "module": "MM",
                    "status": "completed",
                    "status_label": "Na stanie 'O' u dostawcy",
                    "date": "2026-09-04",
                    "value": "-",
                    "details": "50 szt. korpusów przekazanych przewoźnikowi. Zapas specjalny 'O' w tabeli MSLB."
                },
                {
                    "step_number": 4,
                    "name": "Przyjęcie Wyrobu i Rozliczenie Zużycia (101/543)",
                    "phase": "Goods Receipt",
                    "doc_type": "MatDoc (101/543)",
                    "doc_number": "4900194200",
                    "tcode": "MIGO",
                    "module": "MM",
                    "status": "completed",
                    "status_label": "Przyjęto po obróbce",
                    "date": "2026-09-07",
                    "value": "-",
                    "details": "Przyjęcie ocynkowanych korpusów (101) z jednoczesnym automatycznym rozliczeniem zużycia półfabrykatów (543)."
                },
                {
                    "step_number": 5,
                    "name": "Weryfikacja Faktury Kooperanta (MIRO)",
                    "phase": "Vendor Invoice",
                    "doc_type": "RE",
                    "doc_number": "5105600240",
                    "tcode": "MIRO",
                    "module": "MM/FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano koszt usługi",
                    "date": "2026-09-08",
                    "value": f"12 500,00 {waers}",
                    "details": "Koszt obróbki obcej ujęty w księdze głównej i przypisany do kalkulacji zlecenia."
                },
                {
                    "step_number": 6,
                    "name": "Dostawa Końcowa i Faktura dla Klienta (F2)",
                    "phase": "Customer Dispatch",
                    "doc_type": "LF / F2",
                    "doc_number": "90045600",
                    "tcode": "VF03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zakończono sukcesem",
                    "date": "2026-09-09",
                    "value": f"68 000,00 {waers}",
                    "details": "Wysyłka wyrobu gotowego do klienta i wystawienie faktury końcowej."
                }
            ]
        }

    elif scenario == "dropship_tas":
        return {
            "scenario_id": "dropship_tas",
            "scenario_title": "Handel trójstronny: Dostawa bezpośrednia od dostawcy (Dropshipping TAS)",
            "business_domain": "TRADING",
            "domain_name": "Dystrybucja & E-Commerce",
            "process_code": "THIRD_PARTY_TAS",
            "overall_status": "success",
            "order_number": "10008711",
            "customer_id": "C-10002",
            "item_category": "TAS (Third-Party Item)",
            "integration_summary": "Integracja SD-MM-FI: Zlecenie generuje automatyczny Banf, zamówienie zakupu PO wysyłane do producenta z adresem klienta końcowego. Zero kosztów magazynu.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie Sprzedaży z Pozycją TAS",
                    "phase": "Sales Order",
                    "doc_type": "TA (TAS)",
                    "doc_number": "10008711",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Utworzono",
                    "date": "2026-09-08 09:00",
                    "value": f"42 000,00 {waers}",
                    "details": "Pozycja TAS, Linia harmonogramu CS. Adres dostawy = Adres klienta (Ship-to)."
                },
                {
                    "step_number": 2,
                    "name": "Automatyczne Zapotrzebowanie Zakupowe (Banf)",
                    "phase": "Purchase Requisition",
                    "doc_type": "PR (Banf)",
                    "doc_number": "10034120",
                    "tcode": "ME53N",
                    "module": "MM",
                    "status": "completed",
                    "status_label": "Wygenerowano",
                    "date": "2026-09-08 09:00",
                    "value": f"Koszt zakupu: 31 500,00 {waers}",
                    "details": "System SAP w tle wygenerował pozycję PR z przypisaniem konta 'X' i typu pozycji 'S'."
                },
                {
                    "step_number": 3,
                    "name": "Zamówienie Zakupu u Dostawcy (PO)",
                    "phase": "Purchase Order",
                    "doc_type": "NB (PO)",
                    "doc_number": "4500028910",
                    "tcode": "ME23N",
                    "module": "MM",
                    "status": "completed",
                    "status_label": "Wysłano do dostawcy",
                    "date": "2026-09-08 10:30",
                    "value": f"31 500,00 {waers}",
                    "details": "Wysłano zamówienie do dostawcy ABB z instrukcją dostawy bezpośrednio pod adres klienta."
                },
                {
                    "step_number": 4,
                    "name": "Awizo Wysyłki & Doręczenie do Klienta",
                    "phase": "Vendor Dispatch",
                    "doc_type": "ASN / POD",
                    "doc_number": "POD-ABB-771",
                    "tcode": "EDI / Monitor",
                    "module": "SD/MM",
                    "status": "completed",
                    "status_label": "Doręczono klientowi",
                    "date": "2026-09-10 14:00",
                    "value": "-",
                    "details": "Potwierdzenie doręczenia (POD) podpisane przez odbiorcę. Brak ruchu magazynowego w zakładzie własnym."
                },
                {
                    "step_number": 5,
                    "name": "Zaksięgowanie Faktury Dostawcy (MIRO)",
                    "phase": "Vendor Invoice",
                    "doc_type": "RE (MIRO)",
                    "doc_number": "5105600120",
                    "tcode": "MIRO",
                    "module": "MM/FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano koszt zakupu",
                    "date": "2026-09-10 16:30",
                    "value": f"31 500,00 {waers}",
                    "details": "Zaksięgowano zobowiązanie wobec dostawcy. Odblokowanie indeksu fakturowania klienta (billing index)."
                },
                {
                    "step_number": 6,
                    "name": "Faktura dla Klienta Końcowego (F2)",
                    "phase": "Customer Invoice",
                    "doc_type": "F2",
                    "doc_number": "90045330",
                    "tcode": "VF03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Wystawiono i zaksięgowano",
                    "date": "2026-09-11 08:30",
                    "value": f"42 000,00 {waers}",
                    "details": "Faktura oparta na zleceniu/przyjęciu dostawcy. Zrealizowana marża handlowa: 10 500,00 EUR (25%)."
                }
            ]
        }

    elif scenario == "consignment_ke":
        return {
            "scenario_id": "consignment_ke",
            "scenario_title": "Gospodarka konsygnacyjna: Uzupełnienie KB ➔ Pobranie KE (Zapas W)",
            "business_domain": "TRADING",
            "domain_name": "Sprzedaż Konsygnacyjna & Automotive",
            "process_code": "CONSIGNMENT",
            "overall_status": "success",
            "order_number": "10006200",
            "customer_id": "C-10001",
            "item_category": "KEN (Consignment Issue)",
            "integration_summary": "4-etapowa gospodarka depozytowa. Towar w magazynie klienta pozostaje własnością sprzedawcy aż do momentu pobrania KE.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Uzupełnienie Konsygnacji (Zlecenie KB)",
                    "phase": "Fill-up Order",
                    "doc_type": "KB",
                    "doc_number": "10005990",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zatowarowano",
                    "date": "2026-08-15",
                    "value": "-",
                    "details": "Pozycja KBN: Wysyłka 200 szt. do depozytu klienta. Brak faktury handlowej."
                },
                {
                    "step_number": 2,
                    "name": "Wydanie na Zapas Konsygnacyjny (Ruch 631)",
                    "phase": "Fill-up Delivery",
                    "doc_type": "LF / MatDoc",
                    "doc_number": "4900178000",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "completed",
                    "status_label": "Zapas specjalny 'W'",
                    "date": "2026-08-16",
                    "value": "-",
                    "details": "Przeniesienie na zapas specjalny 'W' klienta (tabela MSKU). Wartość bilansowa pozostaje po stronie sprzedawcy."
                },
                {
                    "step_number": 3,
                    "name": "Pobranie z Konsygnacji przez Klienta (Zlecenie KE)",
                    "phase": "Consignment Issue",
                    "doc_type": "KE",
                    "doc_number": "10006200",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Raport zużycia",
                    "date": "2026-09-09",
                    "value": f"28 000,00 {waers}",
                    "details": "Pozycja KEN: Klient pobrał z depozytu 50 szt. filtrów przemysłowych. Uruchomienie procedury fakturowania."
                },
                {
                    "step_number": 4,
                    "name": "Rozchód z Zapasu Konsygnacyjnego (Ruch 633)",
                    "phase": "Issue Delivery",
                    "doc_type": "LF / MatDoc",
                    "doc_number": "4900188440",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "completed",
                    "status_label": "Pobrano ze stanu W",
                    "date": "2026-09-09 11:00",
                    "value": "-",
                    "details": "Zdjęcie z zapasu specjalnego 'W' (ruch 633). Zaksięgowanie kosztu własnego (COGS)."
                },
                {
                    "step_number": 5,
                    "name": "Faktura za Pobrany Towar (Billing Document)",
                    "phase": "Billing",
                    "doc_type": "F2",
                    "doc_number": "90045410",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano w FI",
                    "date": "2026-09-10 09:00",
                    "value": f"28 000,00 {waers}",
                    "details": "Wystawienie faktury F2 na zużyte 50 szt. Przychód ERL zaksięgowany w FI."
                }
            ]
        }

    elif scenario == "intercompany_iv":
        return {
            "scenario_id": "intercompany_iv",
            "scenario_title": "Sprzedaż międzyfirmowa: Spółka A ➔ Fabryka B ➔ Faktura IV",
            "business_domain": "TRADING",
            "domain_name": "Grupy Kapitałowe & Sprzedaż Międzyfirmowa",
            "process_code": "INTERCOMPANY",
            "overall_status": "success",
            "order_number": "10007812",
            "customer_id": "C-10002",
            "item_category": "TAN",
            "integration_summary": "Podwójne fakturowanie cross-company: Spółka Handlowa A fakturuje klienta (F2), a Spółka Produkcyjna B wystawia fakturę międzyfirmową (IV) na Spółkę A wg cen transferowych.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie w Spółce Handlowej A",
                    "phase": "Sales Order",
                    "doc_type": "TA",
                    "doc_number": "10007812",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zakład dost. 2000",
                    "date": "2026-09-05",
                    "value": f"75 000,00 {waers}",
                    "details": "Org. sprzedaży 1000 (BUKRS 1000), ale zakład dostarczający = 2000 (należący do BUKRS 2000)."
                },
                {
                    "step_number": 2,
                    "name": "Dostawa z Fabryki Spółki B",
                    "phase": "Outbound Delivery",
                    "doc_type": "LF",
                    "doc_number": "80013100",
                    "tcode": "VL03N",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Skompletowano w Zakładzie B",
                    "date": "2026-09-06",
                    "value": "-",
                    "details": "Punkt wysyłki 2000. Załadunek bezpośrednio na naczepę do klienta."
                },
                {
                    "step_number": 3,
                    "name": "Wydanie Towarów (PGI w BUKRS 2000)",
                    "phase": "Goods Issue",
                    "doc_type": "WA / MatDoc",
                    "doc_number": "4900192000",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "completed",
                    "status_label": "PGI ruch 601",
                    "date": "2026-09-06 14:00",
                    "value": "-",
                    "details": "Księgowanie kosztu COGS w bilansie Spółki B."
                },
                {
                    "step_number": 4,
                    "name": "Faktura dla Klienta Zewnętrznego (F2)",
                    "phase": "Customer Billing",
                    "doc_type": "F2",
                    "doc_number": "90045550",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Wystawiono klientowi",
                    "date": "2026-09-07 09:00",
                    "value": f"75 000,00 {waers}",
                    "details": "Spółka A fakturuje klienta wg ceny rynkowej (75 000 EUR)."
                },
                {
                    "step_number": 5,
                    "name": "Faktura Wewnętrzna Intercompany (IV)",
                    "phase": "Intercompany Billing",
                    "doc_type": "IV",
                    "doc_number": "94000120",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Cena transferowa (PI01)",
                    "date": "2026-09-07 11:30",
                    "value": f"55 000,00 {waers}",
                    "details": "Spółka Produkcyjna B obciąża Spółkę Handlową A wg warunku ceny transferowej PI01 (55 000 EUR)."
                },
                {
                    "step_number": 6,
                    "name": "Automatyczne Zaksięgowanie Zobowiązania (IDoc EDI)",
                    "phase": "EDI AP Posting",
                    "doc_type": "KR (Vendor Doc)",
                    "doc_number": "190000045",
                    "tcode": "WE02 / FB03",
                    "module": "FI",
                    "status": "completed",
                    "status_label": "EDI RD04 zaksięgowane",
                    "date": "2026-09-07 11:31",
                    "value": f"55 000,00 {waers}",
                    "details": "Komunikat EDI RD04 automatycznie zaksięgował fakturę dostawcy w Spółce A, bilansując rozrachunki."
                }
            ]
        }

    elif scenario == "service_rrb_dp90":
        return {
            "scenario_id": "service_rrb_dp90",
            "scenario_title": "Usługi nakładcze: Zlecenie serwisowe ➔ Godziny CAT2 ➔ DP90 ➔ Faktura L2",
            "business_domain": "SERVICES",
            "domain_name": "Usługi, Projekty & Rozliczenia T&M",
            "process_code": "SERVICE_RRB_DP90",
            "overall_status": "success",
            "order_number": "40001290",
            "customer_id": "C-10001",
            "item_category": "TAD / DIEN",
            "integration_summary": "Resource-Related Billing (RRB): Rejestracja roboczogodzin w CATS i kosztów w CO, przetwarzanie pozycji dynamicznych DIP (DP90) i fakturowanie nakładcze.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie Serwisowe / Element WBS",
                    "phase": "Service Order",
                    "doc_type": "SM01 / PS",
                    "doc_number": "40001290",
                    "tcode": "IW33",
                    "module": "CS/PS",
                    "status": "completed",
                    "status_label": "Przypisano profil DIP",
                    "date": "2026-09-01",
                    "value": "-",
                    "details": "Zlecenie wdrożenia i serwisu linii produkcyjnej. Profil DIP: SD_SERVICES."
                },
                {
                    "step_number": 2,
                    "name": "Rejestracja Godzin i Nakładów (CAT2)",
                    "phase": "Timesheet",
                    "doc_type": "CATS Timesheet",
                    "doc_number": "CAT-20260907",
                    "tcode": "CAT2",
                    "module": "HR/CO",
                    "status": "completed",
                    "status_label": "Zatwierdzono 48 RBG",
                    "date": "2026-09-07",
                    "value": f"Koszty: 7 200,00 {waers}",
                    "details": "Konsultanci wprowadzili 48 roboczogodzin senior konsultanta oraz koszty delegacji."
                },
                {
                    "step_number": 3,
                    "name": "Kalkulacja Pozycji Dynamicznych (DP90)",
                    "phase": "DIP Processing",
                    "doc_type": "DIP Request",
                    "doc_number": "DP90-RUN-1",
                    "tcode": "DP90",
                    "module": "SD/CO",
                    "status": "completed",
                    "status_label": "Przeliczono cennik",
                    "date": "2026-09-08 10:00",
                    "value": f"Do fakturowania: 12 000,00 {waers}",
                    "details": "Profil DIP przekształcił 48 godzin wg stawki 250 EUR/h na pozycję cennikową SRV-01."
                },
                {
                    "step_number": 4,
                    "name": "Żądanie Rozliczenia (Debit Memo Request - DMR)",
                    "phase": "Debit Memo Request",
                    "doc_type": "DMR (L2)",
                    "doc_number": "70001450",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zatwierdzone",
                    "date": "2026-09-08 11:30",
                    "value": f"12 000,00 {waers}",
                    "details": "Dokument sprzedaży typu DMR. Blokada rozliczeń zwolniona przez PM."
                },
                {
                    "step_number": 5,
                    "name": "Faktura za Usługi (Billing Document L2)",
                    "phase": "Billing",
                    "doc_type": "L2",
                    "doc_number": "90045660",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano",
                    "date": "2026-09-08 14:00",
                    "value": f"12 000,00 {waers}",
                    "details": "Faktura za usługi profesjonalne zaksięgowana w FI. Przychód przypisany do obiektu CO."
                }
            ]
        }

    elif scenario == "milestone_billing":
        return {
            "scenario_id": "milestone_billing",
            "scenario_title": "Kamienie milowe: Plan fakturowania etapowego (Projekty & S/4HANA)",
            "business_domain": "SERVICES",
            "domain_name": "Projekty Inżynieryjne & Wdrożenia",
            "process_code": "MILESTONE_BILLING",
            "overall_status": "success",
            "order_number": "10008820",
            "customer_id": "C-10001",
            "item_category": "TAO (Milestone Item)",
            "integration_summary": "Integracja SD-PS: Fakturowanie etapowe powiązane ze zwolnieniem kamieni milowych w strukturze WBS projektu.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zlecenie z Harmonogramem Fakturowania",
                    "phase": "Sales Contract",
                    "doc_type": "TA (TAO)",
                    "doc_number": "10008820",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Plan etapowy",
                    "date": "2026-08-01",
                    "value": f"200 000,00 {waers}",
                    "details": "Umowa z 3 kamieniami milowymi: 20% zaliczka, 50% instalacja, 30% odbiór końcowy."
                },
                {
                    "step_number": 2,
                    "name": "Faktura Zaliczkowa (Down Payment Request)",
                    "phase": "Down Payment",
                    "doc_type": "FA",
                    "doc_number": "90044100",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Zaliczka 20%",
                    "date": "2026-08-05",
                    "value": f"40 000,00 {waers}",
                    "details": "Zaksięgowano zaliczkę od zamawiającego w FI na koncie rozliczeń zaliczek."
                },
                {
                    "step_number": 3,
                    "name": "Odbiór Etapu 1 i Zwolnienie Kamienia w CJ20N",
                    "phase": "Project Milestone",
                    "doc_type": "PS Milestone",
                    "doc_number": "MSTONE-01",
                    "tcode": "CJ20N",
                    "module": "PS",
                    "status": "completed",
                    "status_label": "Zwolniono kamień milowy",
                    "date": "2026-09-05",
                    "value": "-",
                    "details": "Kierownik projektu zwolnił kamień milowy w PS. Automatyczne odblokowanie linii fakturowania."
                },
                {
                    "step_number": 4,
                    "name": "Faktura Częściowa za Etap 1",
                    "phase": "Partial Billing",
                    "doc_type": "F2 (Partial)",
                    "doc_number": "90045710",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Zafakturowano 50%",
                    "date": "2026-09-06",
                    "value": f"100 000,00 {waers}",
                    "details": "Faktura częściowa z częściowym rozliczeniem zaliczki (rozliczono 20 000 EUR zaliczki)."
                }
            ]
        }

    elif scenario == "returns_re":
        return {
            "scenario_id": "returns_re",
            "scenario_title": "Reklamacje i zwroty: Zlecenie RE ➔ Przyjęcie LR (651) ➔ Uznanie G2",
            "business_domain": "COMPLAINTS",
            "domain_name": "Obsługa Reklamacji & Zwroty",
            "process_code": "RETURNS_COMPLAINTS",
            "overall_status": "success",
            "order_number": "10009120",
            "customer_id": "C-10001",
            "item_category": "REN (Returns Item)",
            "integration_summary": "Kompleksowa obsługa reklamacji: przyjęcie fizyczne do strefy kwarantanny QM, ekspertyza techniczna i wystawienie faktury korygującej G2.",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zgłoszenie Reklamacyjne & Zlecenie Zwrotu (RE)",
                    "phase": "Return Order",
                    "doc_type": "RE",
                    "doc_number": "10009120",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zlecenie z blokadą uznania",
                    "date": "2026-09-08",
                    "value": f"-9 250,00 {waers}",
                    "details": "Powód zwrotu: Uszkodzenie transportowe. Referencja do faktury 90045100. Blokada fakturowania 08 aktywna."
                },
                {
                    "step_number": 2,
                    "name": "Dostawa Zwrotna (Return Delivery LR)",
                    "phase": "Return Delivery",
                    "doc_type": "LR",
                    "doc_number": "84000112",
                    "tcode": "VL03N",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Przyjęto od kuriera",
                    "date": "2026-09-09",
                    "value": "-",
                    "details": "Dostawa zwrotna przyjęta na rampie magazynowej."
                },
                {
                    "step_number": 3,
                    "name": "Przyjęcie do Kwarantanny QM (Ruch 651)",
                    "phase": "Goods Receipt",
                    "doc_type": "MatDoc (651)",
                    "doc_number": "4900195500",
                    "tcode": "VL02N",
                    "module": "MM/QM",
                    "status": "completed",
                    "status_label": "Zapas zablokowany (651)",
                    "date": "2026-09-09 14:30",
                    "value": "-",
                    "details": "Towar umieszczony w składzie zablokowanym do decyzji inspektora jakości (decyzja użycia UD)."
                },
                {
                    "step_number": 4,
                    "name": "Zatwierdzenie Reklamacji & Zdjęcie Blokady",
                    "phase": "Release Block",
                    "doc_type": "Order Approval",
                    "doc_number": "APP-9120",
                    "tcode": "VA02",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Blokada usunięta",
                    "date": "2026-09-10 10:00",
                    "value": "-",
                    "details": "Kierownik serwisu usunął blokadę fakturowania w zleceniu RE po potwierdzeniu wady fabrycznej."
                },
                {
                    "step_number": 5,
                    "name": "Faktura Korygująca / Uznanie (Credit Memo G2)",
                    "phase": "Credit Memo",
                    "doc_type": "G2",
                    "doc_number": "90045800",
                    "tcode": "VF03",
                    "module": "SD/FI",
                    "status": "completed",
                    "status_label": "Zaksięgowano korektę",
                    "date": "2026-09-10 12:00",
                    "value": f"-9 250,00 {waers}",
                    "details": "Zmniejszenie należności klienta, korekta przychodów ERL i należnego podatku VAT."
                }
            ]
        }

    else:
        # Domyślny scenariusz: vfx3_blocked (Standard O2C z blokadą w VFX3)
        return {
            "scenario_id": "vfx3_blocked",
            "scenario_title": "Zlecenie Standardowe: Faktura zablokowana w VFX3 (Błąd VKOA)",
            "business_domain": "TRADING",
            "domain_name": "Handel & Dystrybucja",
            "process_code": "O2C_MTS",
            "overall_status": "error",
            "order_number": "10004561",
            "customer_id": "C-10001",
            "item_category": "TAN",
            "integration_summary": "Dostawa i wydanie towaru zrealizowane. Faktura sprzedaży utworzona, ale zablokowana przed księgowaniem w FI z powodu błędu determinacji konta przychodów (VF067).",
            "steps": [
                {
                    "step_number": 1,
                    "name": "Zapytanie i Oferta (Inquiry & Quotation)",
                    "phase": "Pre-sales",
                    "doc_type": "QT",
                    "doc_number": "20000318",
                    "tcode": "VA23",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Zrealizowano",
                    "date": "2026-09-07",
                    "value": f"24 800,00 {waers}",
                    "details": f"Oferta wyceniona wg schematu standardowego dla {bukrs}. Zaakceptowana przez klienta."
                },
                {
                    "step_number": 2,
                    "name": "Zlecenie Sprzedaży (Sales Order)",
                    "phase": "Sales Order",
                    "doc_type": "TA / OR",
                    "doc_number": "10004561",
                    "tcode": "VA03",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Otwarte do dostawy",
                    "date": "2026-09-08",
                    "value": f"24 800,00 {waers}",
                    "details": "Pozycje: 40 szt. materiału. Kontrola kredytowa VKM1: Zwolniona (Credit Check OK)."
                },
                {
                    "step_number": 3,
                    "name": "Dostawa Wychodząca (Outbound Delivery)",
                    "phase": "Shipping",
                    "doc_type": "LF",
                    "doc_number": "80012840",
                    "tcode": "VL03N",
                    "module": "SD",
                    "status": "completed",
                    "status_label": "Skompletowano (Picked)",
                    "date": "2026-09-09",
                    "value": "-",
                    "details": f"Magazyn centralny (Zakład {bukrs}). Kompletacja WM/EWM zakończona pomyślnie."
                },
                {
                    "step_number": 4,
                    "name": "Wydanie Towarów (Post Goods Issue - PGI)",
                    "phase": "Goods Issue",
                    "doc_type": "WA / MatDoc",
                    "doc_number": "4900182410",
                    "tcode": "VL02N",
                    "module": "MM/SD",
                    "status": "completed",
                    "status_label": "Wydano (Ruch 601)",
                    "date": "2026-09-10 11:30",
                    "value": "-",
                    "details": "Zmniejszenie zapasu magazynowego (MSEG ruch 601). Księgowanie kosztu własnego sprzedaży (COGS)."
                },
                {
                    "step_number": 5,
                    "name": "Faktura Sprzedaży (Billing Document)",
                    "phase": "Billing",
                    "doc_type": "F2",
                    "doc_number": "90045100",
                    "tcode": "VF02 / VFX3",
                    "module": "SD",
                    "status": "error",
                    "status_label": "Zablokowana w VFX3",
                    "date": "2026-09-11 08:45",
                    "value": f"24 800,00 {waers}",
                    "details": "Dokument rozliczeniowy utworzony w VF01, ale zablokowany z braku konta przychodu w VKOA.",
                    "error_info": {
                        "error_code": "VF067",
                        "message": f"Konto przychodów nie zostało ustalone dla konta KOFI w {ktopl} / {bukrs}",
                        "suggested_action": "Uruchom zakładkę '🩺 VKOA Fix' i dodaj brakujące konto przychodów dla ERL lub użyj 1-klikowego Quick-Fixa.",
                        "tcode": "VKOA / VFX3"
                    }
                },
                {
                    "step_number": 6,
                    "name": "Księgowanie w Finansach (FI Accounting Doc)",
                    "phase": "Accounting",
                    "doc_type": "RV",
                    "doc_number": "Brak (Zablokowane)",
                    "tcode": "FB03",
                    "module": "FI",
                    "status": "pending",
                    "status_label": "Oczekuje na odblokowanie",
                    "date": "-",
                    "value": "-",
                    "details": "Dokument księgowy FI zostanie automatycznie utworzony natychmiast po uzupełnieniu reguły w VKOA."
                }
            ]
        }

# Funkcja dla zgodności wstecznej
def get_catalog_data():
    o2c = get_sd_process_catalog()
    return o2c, []
