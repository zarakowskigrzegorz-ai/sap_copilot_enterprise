# -*- coding: utf-8 -*-
"""
Serwis Inteligencji Handlowo-Logistycznej Profilu Firmy (Profile Intelligence Service).
Syntetyzuje 4 kluczowe strumienie danych SAP:
1. VBAK + VBAP: asortyment, jednostki miary, skala obrotu, marginesy, podział MTO vs MTS.
2. KNVV: segmentacja rynkowa (KDGRP), rejony (BZIRK), Incoterms, terminy płatności, grupy warunków.
3. LIPS + VBRK: lead time od zlecenia do wysyłki, punkty załadunku (VSTEL), trasy, waluty i kursy.
4. TVAK, TVTW, TVBUR: słowniki konfiguracyjne i translacja żargonu firmy (kody Z*).
"""

from typing import Dict, Any, List, Optional
from app.database.db_manager import get_db_connection, get_company_profile

class ProfileIntelligenceService:
    """
    Silnik analityki biznesowej i profilowania komercyjnego przedsiębiorstwa w SAP SD.
    """

    @classmethod
    def get_full_intelligence_report(cls, company_id: str) -> Dict[str, Any]:
        """
        Zwraca pełny raport inteligencji biznesowej łączący wszystkie 4 strumienie danych.
        """
        profile = get_company_profile(company_id) or {}
        company_name = profile.get("name", company_id)

        commercial = cls.analyze_commercial_profile(company_id)
        portfolio = cls.analyze_customer_portfolio(company_id)
        logistics = cls.analyze_logistics_fulfillment(company_id)
        jargon = cls.get_jargon_dictionary(company_id)

        # Synteza wykonawcza
        summary_bullets = [
            f"Skala operacyjna: {commercial.get('total_items_count', 0)} pozycji zleceniowych o wartości {commercial.get('total_turnover_fmt', '0,00 PLN')} (Śr. pozycja: {commercial.get('avg_item_value_fmt', '0,00 PLN')})",
            f"Struktura modeli realizacji: {commercial.get('model_split_summary', 'Brak danych')}",
            f"Jednostki miary w obrocie: {', '.join([f'{u} ({pct}%)' for u, pct in commercial.get('top_units', [])])}",
            f"Portfel odbiorców: {portfolio.get('total_customers_count', 0)} kont, w tym {portfolio.get('domestic_pct', 0)}% rynek krajowy, {portfolio.get('export_pct', 0)}% eksport",
            f"Efektywność logistyczna: Średni czas realizacji od rejestracji zlecenia do wydania towarów (PGI) = {logistics.get('avg_lead_time_days', 0)} dni roboczych",
            f"Żargon konfiguracyjny firmy: zmapowano {len(jargon.get('z_codes', []))} specyficznych kodów Z* (m.in. {', '.join([z['code'] for z in jargon.get('z_codes', [])[:4]])})"
        ]

        return {
            "status": "success",
            "company_id": company_id,
            "company_name": company_name,
            "summary_bullets": summary_bullets,
            "commercial": commercial,
            "portfolio": portfolio,
            "logistics": logistics,
            "jargon": jargon
        }

    @classmethod
    def analyze_commercial_profile(cls, company_id: str) -> Dict[str, Any]:
        """
        Analizuje nagłówki i pozycje zleceń (VBAK + VBAP):
        - asortyment i top indeksy,
        - jednostki miary (VRKME: SZT, TO, PAL, M, KPL),
        - obroty, skale, średnie ceny,
        - model operacyjny: MTS (TAN) vs MTO (TAK) vs Dropshipping TAS (TAS) vs Konsygnacja (EBN/KEN) vs Usługi (L2N).
        """
        con = get_db_connection()

        stats = con.execute("""
            SELECT 
                COUNT(*) as total_items,
                COUNT(DISTINCT vbeln) as total_orders,
                COALESCE(SUM(netwr), 0) as total_turnover,
                COALESCE(AVG(netwr), 0) as avg_item_value,
                COALESCE(MIN(netpr), 0) as min_price,
                COALESCE(MAX(netpr), 0) as max_price
            FROM sap_orders_vbak_vbap
            WHERE company_id = ?
        """, [company_id]).fetchone()

        total_items = stats[0] or 0
        total_orders = stats[1] or 0
        total_turnover = float(stats[2] or 0.0)
        avg_item_value = float(stats[3] or 0.0)

        # Rozkład jednostek miary (VRKME)
        units_rows = con.execute("""
            SELECT vrkme, COUNT(*) as cnt, ROUND(COUNT(*) * 100.0 / ?, 1) as pct
            FROM sap_orders_vbak_vbap
            WHERE company_id = ?
            GROUP BY vrkme
            ORDER BY cnt DESC
        """, [total_items if total_items > 0 else 1, company_id]).fetchall()

        top_units = [(r[0], r[2]) for r in units_rows]

        # Podział modeli operacyjnych wg PSTYV (MTS vs MTO vs TAS vs Konsygnacja)
        pstyv_rows = con.execute("""
            SELECT pstyv, COUNT(*) as cnt, COALESCE(SUM(netwr), 0) as turnover,
                   ROUND(COUNT(*) * 100.0 / ?, 1) as pct_cnt
            FROM sap_orders_vbak_vbap
            WHERE company_id = ?
            GROUP BY pstyv
            ORDER BY cnt DESC
        """, [total_items if total_items > 0 else 1, company_id]).fetchall()

        model_breakdown = {}
        for r in pstyv_rows:
            pst = r[0]
            cnt = r[1]
            turnover = float(r[2])
            pct = r[3]

            if pst in ['TAN', 'ZTAN']:
                model_name = "MTS (Make-to-Stock)"
            elif pst in ['TAK', 'ZTAK']:
                model_name = "MTO (Make-to-Order)"
            elif pst in ['TAS', 'ZTAS']:
                model_name = "Dropshipping TAS (Handel trójstronny)"
            elif pst in ['EBN', 'KEN']:
                model_name = "Konsygnacja klienta (KB/KE)"
            elif pst in ['L2N', 'TAD', 'DIEN']:
                model_name = "Usługi i projekty (RRB)"
            else:
                model_name = f"Inne ({pst})"

            model_breakdown[pst] = {
                "name": model_name,
                "count": cnt,
                "pct": pct,
                "turnover": turnover
            }

        # Podsumowanie tekstowe podziału
        model_parts = []
        for pst, d in model_breakdown.items():
            model_parts.append(f"{d['pct']}% {d['name']}")
        model_split_summary = " • ".join(model_parts) if model_parts else "Brak danych zleceniowych"

        # Top 5 asortymentu
        top_products = con.execute("""
            SELECT matnr, arktx, COUNT(*) as orders_count, SUM(kwmeng) as total_qty, vrkme, SUM(netwr) as sum_netwr
            FROM sap_orders_vbak_vbap
            WHERE company_id = ?
            GROUP BY matnr, arktx, vrkme
            ORDER BY sum_netwr DESC
            LIMIT 5
        """, [company_id]).fetchall()

        return {
            "total_items_count": total_items,
            "total_orders_count": total_orders,
            "total_turnover": total_turnover,
            "total_turnover_fmt": f"{total_turnover:,.2f} PLN".replace(",", " ").replace(".", ","),
            "avg_item_value": avg_item_value,
            "avg_item_value_fmt": f"{avg_item_value:,.2f} PLN".replace(",", " ").replace(".", ","),
            "top_units": top_units,
            "model_breakdown": model_breakdown,
            "model_split_summary": model_split_summary,
            "top_products": [{
                "matnr": p[0], "name": p[1], "orders_cnt": p[2],
                "qty": float(p[3]), "unit": p[4], "turnover": float(p[5])
            } for p in top_products]
        }

    @classmethod
    def analyze_customer_portfolio(cls, company_id: str) -> Dict[str, Any]:
        """
        Analizuje kartoteki rynkowe klientów (KNVV):
        - segmentację portfela KDGRP (B2B, sieci, hurt),
        - zasięg geograficzny i rejony BZIRK,
        - warunki dostaw Incoterms (INCO1/INCO2),
        - warunki płatności ZTERM i grupy rabatowe KONDA.
        """
        con = get_db_connection()

        total_customers = con.execute("SELECT COUNT(*) FROM sap_customers WHERE company_id = ?", [company_id]).fetchone()[0]
        if total_customers == 0:
            return {"total_customers_count": 0, "domestic_pct": 0, "export_pct": 0}

        # Podział kraj vs eksport
        domestic_cnt = con.execute("SELECT COUNT(*) FROM sap_customers WHERE company_id = ? AND land1 = 'PL'", [company_id]).fetchone()[0]
        export_cnt = total_customers - domestic_cnt
        domestic_pct = round(domestic_cnt * 100.0 / total_customers, 1)
        export_pct = round(export_cnt * 100.0 / total_customers, 1)

        # Segmentacja rynkowa (KDGRP)
        kdgrp_rows = con.execute("""
            SELECT COALESCE(kdgrp, '01') as kdgrp, COUNT(*) as cnt,
                   ROUND(COUNT(*) * 100.0 / ?, 1) as pct
            FROM sap_customers
            WHERE company_id = ?
            GROUP BY kdgrp
            ORDER BY cnt DESC
        """, [total_customers, company_id]).fetchall()

        kdgrp_names = {
            "01": "B2B Przemysł & Producenci Maszyn (OEM)",
            "02": "Dystrybutorzy Hurtowi & Partnerzy",
            "03": "Sieci Handlowe & Składy Techniczne",
            "04": "Eksport Strategiczny"
        }
        segments = [{
            "code": r[0], "name": kdgrp_names.get(r[0], f"Grupa {r[0]}"), "count": r[1], "pct": r[2]
        } for r in kdgrp_rows]

        # Warunki Incoterms
        inco_rows = con.execute("""
            SELECT COALESCE(inco1, 'DAP') as inco, COUNT(*) as cnt,
                   ROUND(COUNT(*) * 100.0 / ?, 1) as pct
            FROM sap_customers
            WHERE company_id = ?
            GROUP BY inco1
            ORDER BY cnt DESC
        """, [total_customers, company_id]).fetchall()
        incoterms = [{"code": r[0], "count": r[1], "pct": r[2]} for r in inco_rows]

        # Terminy płatności ZTERM
        zterm_rows = con.execute("""
            SELECT COALESCE(zterm, 'NT30') as zt, COUNT(*) as cnt,
                   ROUND(COUNT(*) * 100.0 / ?, 1) as pct
            FROM sap_customers
            WHERE company_id = ?
            GROUP BY zterm
            ORDER BY cnt DESC
        """, [total_customers, company_id]).fetchall()
        payment_terms = [{"code": r[0], "count": r[1], "pct": r[2]} for r in zterm_rows]

        # Rejony sprzedaży BZIRK
        bzirk_rows = con.execute("""
            SELECT COALESCE(bzirk, 'PL01') as bz, COUNT(*) as cnt
            FROM sap_customers
            WHERE company_id = ?
            GROUP BY bzirk
            ORDER BY cnt DESC
        """, [company_id]).fetchall()
        regions = [{"code": r[0], "count": r[1]} for r in bzirk_rows]

        return {
            "total_customers_count": total_customers,
            "domestic_count": domestic_cnt,
            "export_count": export_cnt,
            "domestic_pct": domestic_pct,
            "export_pct": export_pct,
            "segments": segments,
            "incoterms": incoterms,
            "payment_terms": payment_terms,
            "regions": regions
        }

    @classmethod
    def analyze_logistics_fulfillment(cls, company_id: str) -> Dict[str, Any]:
        """
        Analizuje przepływ realizacji i logistyki (LIPS + VBRK):
        - średni lead time (dni od złożenia zlecenia do wydania PGI),
        - punkty załadunku (VSTEL) i kluczowe trasy logistyczne (ROUTE),
        - rodzaje faktur (FKART: F2, IV, G2, L2),
        - waluty rozliczeniowe i kursy (WAERK, KURRF).
        """
        con = get_db_connection()

        flow_count = con.execute("SELECT COUNT(*) FROM sap_flow_lips_vbrk WHERE company_id = ?", [company_id]).fetchone()[0]
        if flow_count == 0:
            return {"flow_count": 0, "avg_lead_time_days": 2.5}

        # Średni lead time
        avg_lead = con.execute("""
            SELECT COALESCE(AVG(lead_time_days), 2.8),
                   COALESCE(MIN(lead_time_days), 1),
                   COALESCE(MAX(lead_time_days), 5)
            FROM sap_flow_lips_vbrk
            WHERE company_id = ?
        """, [company_id]).fetchone()

        avg_lead_time = round(float(avg_lead[0] or 2.8), 1)

        # Punkty załadunku (VSTEL)
        vstel_rows = con.execute("""
            SELECT vstel, COUNT(*) as cnt, ROUND(COUNT(*) * 100.0 / ?, 1) as pct
            FROM sap_flow_lips_vbrk
            WHERE company_id = ?
            GROUP BY vstel
            ORDER BY cnt DESC
        """, [flow_count, company_id]).fetchall()

        vstel_names = {
            "1000": "Magazyn Główny Wyrobów (Katowice)",
            "1010": "Skład Fabryczny Podzespołów (Gliwice)",
            "1020": "Centrum Dystrybucji i Cross-dock (Poznań)"
        }
        shipping_points = [{
            "code": r[0], "name": vstel_names.get(r[0], f"Punkt wysyłki {r[0]}"), "count": r[1], "pct": r[2]
        } for r in vstel_rows]

        # Trasy spedycyjne (ROUTE)
        route_rows = con.execute("""
            SELECT route, COUNT(*) as cnt
            FROM sap_flow_lips_vbrk
            WHERE company_id = ?
            GROUP BY route
            ORDER BY cnt DESC
            LIMIT 5
        """, [company_id]).fetchall()
        routes = [{"code": r[0], "count": r[1]} for r in route_rows]

        # Rodzaje faktur (FKART)
        fkart_rows = con.execute("""
            SELECT fkart, COUNT(*) as cnt, COALESCE(SUM(netwr_bill), 0) as val
            FROM sap_flow_lips_vbrk
            WHERE company_id = ?
            GROUP BY fkart
            ORDER BY cnt DESC
        """, [company_id]).fetchall()
        fkart_names = {
            "F2": "Faktura standardowa sprzedaży",
            "IV": "Wewnętrzna faktura międzyfirmowa (Intercompany)",
            "G2": "Faktura uznaniowa / korekta",
            "L2": "Faktura za usługi (DMR/RRB)"
        }
        billing_types = [{
            "code": r[0], "name": fkart_names.get(r[0], f"Faktura {r[0]}"), "count": r[1], "value": float(r[2])
        } for r in fkart_rows]

        # Waluty
        waerk_rows = con.execute("""
            SELECT waerk, COUNT(*) as cnt, AVG(kurrf) as avg_rate
            FROM sap_flow_lips_vbrk
            WHERE company_id = ?
            GROUP BY waerk
            ORDER BY cnt DESC
        """, [company_id]).fetchall()
        currencies = [{"currency": r[0], "count": r[1], "rate": float(r[2])} for r in waerk_rows]

        return {
            "flow_count": flow_count,
            "avg_lead_time_days": avg_lead_time,
            "shipping_points": shipping_points,
            "routes": routes,
            "billing_types": billing_types,
            "currencies": currencies
        }

    @classmethod
    def get_jargon_dictionary(cls, company_id: str) -> Dict[str, Any]:
        """
        Zwraca słowniki konfiguracyjne (TVAK, TVTW, TVBUR) oraz specyficzny żargon firmy.
        """
        con = get_db_connection()

        dict_rows = con.execute("""
            SELECT dict_type, code, bezeichnung, COALESCE(business_meaning, ''), COALESCE(notes, '')
            FROM sap_dictionaries_tvxx
            WHERE company_id = ?
            ORDER BY dict_type, code
        """, [company_id]).fetchall()

        grouped: Dict[str, List[Dict[str, str]]] = {
            "TVAK": [],
            "TVTW": [],
            "TVBUR": [],
            "TVKO": []
        }
        z_codes: List[Dict[str, str]] = []

        for r in dict_rows:
            entry = {
                "dict_type": r[0],
                "code": r[1],
                "name": r[2],
                "business_meaning": r[3],
                "notes": r[4]
            }
            if r[0] in grouped:
                grouped[r[0]].append(entry)
            else:
                grouped[r[0]] = [entry]

            # Rejestracja kodów specyficznych Z*
            if r[1].startswith("Z") or "specjaln" in r[3].lower() or "żargon" in r[4].lower():
                z_codes.append(entry)

        return {
            "total_dictionary_entries": len(dict_rows),
            "grouped": grouped,
            "z_codes": z_codes
        }

    @classmethod
    def format_intelligence_for_llm(cls, company_id: str) -> str:
        """
        Formatuje podsumowanie komercyjno-logistyczne do bezpośredniego wstrzyknięcia do promptu LLM.
        """
        intel = cls.get_full_intelligence_report(company_id)
        comm = intel.get("commercial", {})
        port = intel.get("portfolio", {})
        log = intel.get("logistics", {})
        jargon = intel.get("jargon", {})

        z_codes_text = ", ".join([f"{z['code']} ('{z['business_meaning']}')" for z in jargon.get("z_codes", [])])

        return f"""
SPECYFIKA KOMERCYJNA I LOGISTYCZNA FIRMY (ZASILONA Z BAZY SAP: VBAK, KNVV, LIPS, TVxx):
- Skala i asortyment: {comm.get('total_items_count', 0)} pozycji zleceniowych w VBAK/VBAP, obrót: {comm.get('total_turnover_fmt', '0 PLN')}
- Model realizacji: {comm.get('model_split_summary', 'Standard MTS')}
- Stosowane jednostki miary: {', '.join([f'{u} ({pct}%)' for u, pct in comm.get('top_units', [])])}
- Portfel klientów: {port.get('total_customers_count', 0)} kont (Kraj: {port.get('domestic_pct', 0)}%, Eksport: {port.get('export_pct', 0)}%), kluczowe reguły: {', '.join([i['code'] for i in port.get('incoterms', [])[:3]])}
- Logistyka Order-to-Cash: Średni lead time od zlecenia do PGI wynosi {log.get('avg_lead_time_days', 2.8)} dni. Punkty załadunku: {', '.join([sp['code'] for sp in log.get('shipping_points', [])])}
- Słownik żargonu i kody Z* firmy: {z_codes_text or 'Standardowe kody SAP'}
"""
