# -*- coding: utf-8 -*-
"""
Symulator Procedury Cenowej SAP SD (V/08 / PRCD_ELEMENTS / KONV) zintegrowany z VKOA (KOFI00).
Oblicza kaskadę warunków cenowych (Cena bazowa -> Rabaty -> Wartość Netto -> Fracht -> Podatek VAT -> Brutto)
oraz weryfikuje dla każdego klucza konta (ERL, ERS, ERF, MWS) determinację kont księgi głównej FI w VKOA.
"""

from typing import Dict, Any, List, Optional
from app.database.db_manager import get_db_connection, get_company_profile
from app.services.vkoa_service import VkoaTroubleshooterService


class PricingSimulatorService:
    """
    Silnik symulacji kalkulacji cen (V/08) i integracji SD-FI (VKOA) na poziomie pozycji zlecenia/faktury.
    """

    @classmethod
    def get_pricing_context(cls, company_id: str) -> Dict[str, Any]:
        """
        Zwraca listę klientów, materiałów oraz zdefiniowanych warunków cenowych dla aktywnej firmy,
        aby zasilić formularz symulatora V/08.
        """
        con = get_db_connection()
        profile = get_company_profile(company_id) or {}

        customers_rows = con.execute("""
            SELECT kunnr, name1, vkorg, vtweg, spart, COALESCE(ktgrd, '01') as ktgrd,
                   COALESCE(land1, 'PL') as land1, COALESCE(taxkd, '1') as taxkd,
                   COALESCE(inco1, 'DAP') as inco1
            FROM sap_customers
            WHERE company_id = ?
            ORDER BY kunnr
        """, [company_id]).fetchall()

        materials_rows = con.execute("""
            SELECT matnr, maktx, mtart, werks, meins, COALESCE(stprs, 100.0) as stprs,
                   COALESCE(ktgrm, '02') as ktgrm, COALESCE(taxm1, '1') as taxm1
            FROM sap_materials
            WHERE company_id = ?
            ORDER BY matnr
        """, [company_id]).fetchall()

        conditions_rows = con.execute("""
            SELECT kschl, condition_class, calc_type, description, account_key, access_seq, notes
            FROM sd_pricing_conditions
            WHERE company_id = ?
            ORDER BY kschl
        """, [company_id]).fetchall()

        return {
            "status": "success",
            "company_id": company_id,
            "company_name": profile.get("name", company_id),
            "ktopl": profile.get("ktopl", "INT"),
            "waers": profile.get("waers", "EUR"),
            "customers": [
                {
                    "kunnr": r[0],
                    "name1": r[1],
                    "vkorg": r[2],
                    "vtweg": r[3],
                    "spart": r[4],
                    "ktgrd": r[5],
                    "land1": r[6],
                    "taxkd": r[7],
                    "inco1": r[8]
                }
                for r in customers_rows
            ],
            "materials": [
                {
                    "matnr": r[0],
                    "maktx": r[1],
                    "mtart": r[2],
                    "werks": r[3],
                    "meins": r[4],
                    "stprs": float(r[5] or 100.0),
                    "suggested_price": round(float(r[5] or 100.0) * 1.35, 2),
                    "ktgrm": r[6],
                    "taxm1": r[7]
                }
                for r in materials_rows
            ],
            "conditions": [
                {
                    "kschl": r[0],
                    "condition_class": r[1],
                    "calc_type": r[2],
                    "description": r[3],
                    "account_key": r[4],
                    "access_seq": r[5],
                    "notes": r[6]
                }
                for r in conditions_rows
            ]
        }

    @classmethod
    def simulate_pricing_procedure(
        cls,
        company_id: str,
        kunnr: str,
        matnr: str,
        quantity: float = 10.0,
        discount_pct: float = 5.0,
        freight_val: float = 150.0,
        override_base_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Przeprowadza pełną symulację procedury cenowej (V/08 -> PRCD_ELEMENTS)
        oraz sprawdza determinację kont księgowych VKOA dla każdego aktywnego warunku.
        """
        con = get_db_connection()
        profile = get_company_profile(company_id) or {}
        ktopl = profile.get("ktopl", "INT")
        waers = profile.get("waers", "EUR")

        # 1. Pobranie danych klienta (KNVV / KNA1)
        cust_row = con.execute("""
            SELECT kunnr, name1, vkorg, vtweg, spart, COALESCE(ktgrd, '01'),
                   COALESCE(land1, 'PL'), COALESCE(taxkd, '1'), COALESCE(inco1, 'DAP')
            FROM sap_customers
            WHERE company_id = ? AND kunnr = ?
            LIMIT 1
        """, [company_id, kunnr]).fetchone()

        if not cust_row:
            cust_row = con.execute("""
                SELECT kunnr, name1, vkorg, vtweg, spart, COALESCE(ktgrd, '01'),
                       COALESCE(land1, 'PL'), COALESCE(taxkd, '1'), COALESCE(inco1, 'DAP')
                FROM sap_customers
                WHERE company_id = ?
                LIMIT 1
            """, [company_id]).fetchone()

        if cust_row:
            cust = {
                "kunnr": cust_row[0],
                "name1": cust_row[1],
                "vkorg": cust_row[2],
                "vtweg": cust_row[3],
                "spart": cust_row[4],
                "ktgrd": cust_row[5] or "01",
                "land1": cust_row[6] or "PL",
                "taxkd": cust_row[7] or "1",
                "inco1": cust_row[8] or "DAP"
            }
        else:
            cust = {
                "kunnr": kunnr or "100010",
                "name1": "Odbiorca Testowy SAP",
                "vkorg": "1000",
                "vtweg": "10",
                "spart": "00",
                "ktgrd": "01",
                "land1": "PL",
                "taxkd": "1",
                "inco1": "DAP"
            }

        # 2. Pobranie danych materiału (MARA / MVKE)
        mat_row = con.execute("""
            SELECT matnr, maktx, mtart, werks, meins, COALESCE(stprs, 100.0),
                   COALESCE(ktgrm, '02'), COALESCE(taxm1, '1')
            FROM sap_materials
            WHERE company_id = ? AND matnr = ?
            LIMIT 1
        """, [company_id, matnr]).fetchone()

        if not mat_row:
            mat_row = con.execute("""
                SELECT matnr, maktx, mtart, werks, meins, COALESCE(stprs, 100.0),
                       COALESCE(ktgrm, '02'), COALESCE(taxm1, '1')
                FROM sap_materials
                WHERE company_id = ?
                LIMIT 1
            """, [company_id]).fetchone()

        if mat_row:
            mat = {
                "matnr": mat_row[0],
                "maktx": mat_row[1],
                "mtart": mat_row[2],
                "werks": mat_row[3],
                "meins": mat_row[4] or "SZT",
                "stprs": float(mat_row[5] or 100.0),
                "ktgrm": mat_row[6] or "02",
                "taxm1": mat_row[7] or "1"
            }
        else:
            mat = {
                "matnr": matnr or "MAT-100",
                "maktx": "Materiał Testowy SAP",
                "mtart": "FERT",
                "werks": "1000",
                "meins": "SZT",
                "stprs": 1000.0,
                "ktgrm": "02",
                "taxm1": "1"
            }

        # 3. Pobranie słownika warunków cenowych firmy (sd_pricing_conditions)
        cond_rows = con.execute("""
            SELECT kschl, condition_class, calc_type, description, account_key, access_seq
            FROM sd_pricing_conditions
            WHERE company_id = ?
        """, [company_id]).fetchall()
        cond_map = {r[0]: {
            "kschl": r[0],
            "condition_class": r[1],
            "calc_type": r[2],
            "description": r[3],
            "account_key": r[4],
            "access_seq": r[5]
        } for r in cond_rows}

        # Dobór kodów warunków (standard vs Z-custom w zależności od profilu firmy)
        price_kschl = "ZPR1" if "ZPR1" in cond_map and company_id == "CLIENT_B" else "PR00"
        disc_kschl = "ZREB" if "ZREB" in cond_map else ("K007" if "K007" in cond_map else "K004")
        freight_kschl = "ZFRE" if "ZFRE" in cond_map else "KF00"
        tax_kschl = "MWST"

        procedure_code = "ZSE001 (Nordic Retail Pricing)" if company_id == "CLIENT_B" else "RVAA01 (Standard S/4HANA Pricing)"

        # 4. Wyliczenie wartości w krokach V/08 (PRCD_ELEMENTS)
        qty = max(0.001, float(quantity or 1.0))
        disc_pct = max(0.0, min(100.0, float(discount_pct or 0.0)))
        freight_amount = max(0.0, float(freight_val or 0.0))

        unit_price = (
            round(float(override_base_price), 2)
            if override_base_price is not None and float(override_base_price) > 0
            else round(mat["stprs"] * 1.35, 2)
        )
        base_value = round(unit_price * qty, 2)
        discount_value = -round(base_value * (disc_pct / 100.0), 2) if disc_pct > 0 else 0.0
        net_after_discount = round(base_value + discount_value, 2)
        netwr_total = round(net_after_discount + freight_amount, 2)
        cost_total = round(mat["stprs"] * qty, 2)
        margin_val = round(netwr_total - cost_total, 2)
        margin_pct = round((margin_val / netwr_total) * 100.0, 1) if netwr_total > 0 else 0.0

        # Determinacja stawki podatku MWST na podstawie kraju, TAXKD i TAXM1
        if cust["taxkd"] == "0" or mat["taxm1"] == "0" or cust["ktgrd"] == "02":
            tax_rate_pct = 0.0
            tax_reason = f"0% VAT (Eksport / WDT – KTGRD={cust['ktgrd']}, Kraj={cust['land1']})"
        elif cust["land1"] in ("SE", "NO", "FI"):
            tax_rate_pct = 25.0
            tax_reason = f"25% VAT (Stawka nordycka – Kraj={cust['land1']}, TAXKD={cust['taxkd']})"
        else:
            tax_rate_pct = 23.0
            tax_reason = f"23% VAT (Stawka krajowa – Kraj={cust['land1']}, TAXKD={cust['taxkd']})"

        tax_value = round(netwr_total * (tax_rate_pct / 100.0), 2)
        gross_total = round(netwr_total + tax_value, 2)

        raw_steps = [
            {
                "step": 10,
                "counter": 1,
                "kschl": price_kschl,
                "name": cond_map.get(price_kschl, {}).get("description", "Cena bazowa materiału (Cennik VK11)"),
                "is_subtotal": False,
                "kbetr": f"{unit_price:,.2f} {waers} / 1 {mat['meins']}",
                "kwert": base_value,
                "kvsl": cond_map.get(price_kschl, {}).get("account_key") or "ERL",
                "access_seq": cond_map.get(price_kschl, {}).get("access_seq") or "PR02 ( Tabela A304 )",
                "active": True
            },
            {
                "step": 20,
                "counter": 1,
                "kschl": disc_kschl,
                "name": cond_map.get(disc_kschl, {}).get("description", "Rabat handlowy klienta / materiału (%)"),
                "is_subtotal": False,
                "kbetr": f"-{disc_pct:.1f} %",
                "kwert": discount_value,
                "kvsl": cond_map.get(disc_kschl, {}).get("account_key") or "ERS",
                "access_seq": cond_map.get(disc_kschl, {}).get("access_seq") or "K007 ( Tabela A007 )",
                "active": disc_pct > 0
            },
            {
                "step": 100,
                "counter": 0,
                "kschl": "SUB1",
                "name": "Wartość Netto po rabatach handlowych",
                "is_subtotal": True,
                "kbetr": "Suma kroków 10 - 90",
                "kwert": net_after_discount,
                "kvsl": None,
                "access_seq": "—",
                "active": True
            },
            {
                "step": 150,
                "counter": 1,
                "kschl": freight_kschl,
                "name": cond_map.get(freight_kschl, {}).get("description", f"Koszty transportu i spedycji ({cust['inco1']})"),
                "is_subtotal": False,
                "kbetr": f"{freight_amount:,.2f} {waers} (Nagłówek/Pozycja)",
                "kwert": freight_amount,
                "kvsl": cond_map.get(freight_kschl, {}).get("account_key") or "ERF",
                "access_seq": cond_map.get(freight_kschl, {}).get("access_seq") or "KF00 ( Incoterms )",
                "active": freight_amount > 0
            },
            {
                "step": 800,
                "counter": 0,
                "kschl": "NETWR",
                "name": "Wartość Netto pozycji (VBAP-NETWR / VBRP-NETWR)",
                "is_subtotal": True,
                "kbetr": "Podstawa opodatkowania VAT",
                "kwert": netwr_total,
                "kvsl": None,
                "access_seq": "—",
                "active": True
            },
            {
                "step": 900,
                "counter": 1,
                "kschl": tax_kschl,
                "name": f"Podatek należny VAT ({tax_reason})",
                "is_subtotal": False,
                "kbetr": f"{tax_rate_pct:.1f} %",
                "kwert": tax_value,
                "kvsl": "MWS",
                "access_seq": "MWST ( Kraj / TAXKD / TAXM1 )",
                "active": True
            },
            {
                "step": 940,
                "counter": 1,
                "kschl": "VPRS",
                "name": f"Koszt własny sprzedaży (Wycena MM03: {mat['stprs']:.2f} {waers}/{mat['meins']})",
                "is_subtotal": False,
                "kbetr": f"Marża: {margin_val:,.2f} {waers} ({margin_pct}%)",
                "kwert": cost_total,
                "kvsl": None,
                "access_seq": "Statystyczny (MBEW-STPRS)",
                "active": True,
                "is_statistical": True
            },
            {
                "step": 990,
                "counter": 0,
                "kschl": "BRUTTO",
                "name": "Wartość Brutto do zapłaty (Należność FI na koncie klienta)",
                "is_subtotal": True,
                "kbetr": "NETWR + MWST",
                "kwert": gross_total,
                "kvsl": None,
                "access_seq": "—",
                "active": True
            }
        ]

        # 5. Integracja każdego aktywnego klucza konta (KVSL) z symulatorem VKOA (KOFI00)
        vkoa_issues: List[Dict[str, Any]] = []
        enriched_steps: List[Dict[str, Any]] = []

        for s in raw_steps:
            if not s["active"]:
                continue

            kvsl = s.get("kvsl")
            if kvsl:
                vkoa_sim = VkoaTroubleshooterService.simulate_account_determination(
                    company_id=company_id,
                    ktopl=ktopl,
                    vkorg=cust["vkorg"],
                    ktgrd_cust=cust["ktgrd"],
                    ktgrm_mat=mat["ktgrm"],
                    kvsl=kvsl
                )
                if vkoa_sim.get("success"):
                    s["vkoa"] = {
                        "status": "DETERMINED",
                        "saknr": vkoa_sim["account"],
                        "matched_table": vkoa_sim["matched_table"],
                        "rule_desc": (vkoa_sim.get("rule_details") or {}).get("description", "")
                    }
                else:
                    qf = vkoa_sim.get("quick_fix", {})
                    s["vkoa"] = {
                        "status": "MISSING",
                        "saknr": None,
                        "matched_table": None,
                        "error_code": "VF067",
                        "suggested_saknr": qf.get("saknr", "800000"),
                        "quick_fix": qf
                    }
                    vkoa_issues.append({
                        "kschl": s["kschl"],
                        "kvsl": kvsl,
                        "ktopl": ktopl,
                        "vkorg": cust["vkorg"],
                        "ktgrd_cust": cust["ktgrd"],
                        "ktgrm_mat": mat["ktgrm"],
                        "suggested_saknr": qf.get("saknr", "800000"),
                        "quick_fix": qf,
                        "error_log": f"VF067: Account determination for entry {ktopl} {cust['vkorg']} {cust['ktgrd']} {mat['ktgrm']} {kvsl} not possible"
                    })
            else:
                s["vkoa"] = None

            enriched_steps.append(s)

        billing_ready = len(vkoa_issues) == 0

        return {
            "status": "success",
            "company_id": company_id,
            "procedure": procedure_code,
            "ktopl": ktopl,
            "waers": waers,
            "customer": cust,
            "material": mat,
            "inputs": {
                "quantity": qty,
                "discount_pct": disc_pct,
                "freight_val": freight_amount,
                "unit_price": unit_price
            },
            "totals": {
                "base_value": base_value,
                "discount_value": discount_value,
                "freight_value": freight_amount,
                "netwr": netwr_total,
                "tax_rate_pct": tax_rate_pct,
                "tax_value": tax_value,
                "gross_total": gross_total,
                "cost_total": cost_total,
                "margin_val": margin_val,
                "margin_pct": margin_pct
            },
            "steps": enriched_steps,
            "billing_ready": billing_ready,
            "vkoa_issues": vkoa_issues
        }
