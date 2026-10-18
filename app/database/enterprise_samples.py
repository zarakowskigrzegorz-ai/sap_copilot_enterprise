# -*- coding: utf-8 -*-
"""
Generator Próbek Danych Korporacyjnych SAP SD (Enterprise Data Generator).
Generuje kompletne zbiory danych o wolumenach produkcyjnych zgodnych ze specyfikacją:
1. VBAK + VBAP: 3 000 – 5 000 pozycji zleceń sprzedaży (asortyment, jednostki, skale, MTO vs MTS).
2. KNVV: 200 – 500 kont klientów (KDGRP, BZIRK, KONDA, INCO1/2, ZTERM, KVGR1-5).
3. LIPS + VBRK: 1 000 – 2 000 rekordów realizacji i logistyki (LFART, VSTEL, ROUTE, FKART, FKTYP, WAERK, KURRF, lead time).
4. TVAK, TVTW, TVBUR: słowniki konfiguracyjne z mapowaniem specyficznego żargonu firmy.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.database.db_manager import get_db_connection

class EnterpriseDataGenerator:
    """
    Generator realistycznych danych korporacyjnych dla profilu firmy w SAP Copilot.
    """

    PRODUCTS_CATALOG = [
        {"matnr": "IND-1001", "name": "Silnik trójfazowy 15kW IE3", "mtpos": "NORM", "unit": "SZT", "base_price": 2850.0, "category": "MTS"},
        {"matnr": "IND-1002", "name": "Silnik trójfazowy 45kW IE4 High-Eff", "mtpos": "NORM", "unit": "SZT", "base_price": 7400.0, "category": "MTS"},
        {"matnr": "IND-1003", "name": "Silnik serwo synchroniczny 3.5Nm", "mtpos": "NORM", "unit": "SZT", "base_price": 1950.0, "category": "MTS"},
        {"matnr": "IND-2001", "name": "Prasa hydrauliczna 200T Specyfikacja Klienta", "mtpos": "0001", "unit": "SZT", "base_price": 85000.0, "category": "MTO"},
        {"matnr": "IND-2002", "name": "Agregat pompowy wysokociśnieniowy Custom", "mtpos": "0001", "unit": "SZT", "base_price": 42000.0, "category": "MTO"},
        {"matnr": "IND-2003", "name": "Linia podająca automatyczna MTO", "mtpos": "BANC", "unit": "SZT", "base_price": 120000.0, "category": "MTO"},
        {"matnr": "IND-3001", "name": "Serwer Przemysłowy Rack 4U (Dostawa TAS)", "mtpos": "BANS", "unit": "SZT", "base_price": 16500.0, "category": "TAS"},
        {"matnr": "IND-3002", "name": "Sterownik PLC Siemens S7-1500 (Dropship)", "mtpos": "BANS", "unit": "SZT", "base_price": 8900.0, "category": "TAS"},
        {"matnr": "IND-3003", "name": "Falownik Schneider 75kW (Dropship TAS)", "mtpos": "BANS", "unit": "SZT", "base_price": 14200.0, "category": "TAS"},
        {"matnr": "IND-4001", "name": "Kabel zasilający miedziany 4x35mm2", "mtpos": "NORM", "unit": "M", "base_price": 48.5, "category": "MTS"},
        {"matnr": "IND-4002", "name": "Kabel sterowniczy ekranowany LiYCY", "mtpos": "NORM", "unit": "M", "base_price": 18.2, "category": "MTS"},
        {"matnr": "IND-5001", "name": "Granulat tworzywa PA6 GF30 Wtrysk", "mtpos": "NORM", "unit": "TO", "base_price": 12800.0, "category": "MTS"},
        {"matnr": "IND-5002", "name": "Stal konstrukcyjna profil HEB 200", "mtpos": "NORM", "unit": "TO", "base_price": 4600.0, "category": "MTS"},
        {"matnr": "IND-6001", "name": "Paleta euro podzespołów złącznych", "mtpos": "NORM", "unit": "PAL", "base_price": 3200.0, "category": "MTS"},
        {"matnr": "IND-6002", "name": "Komplet uszczelnień vitonowych (Zapas W)", "mtpos": "NORM", "unit": "KPL", "base_price": 480.0, "category": "CONSIGNMENT"},
        {"matnr": "IND-7001", "name": "Usługa montażu i rozruchu na obiekcie", "mtpos": "DIEN", "unit": "KPL", "base_price": 4500.0, "category": "SERVICE"}
    ]

    CUSTOMER_NAMES_BASE = [
        "ABB Industrial Sp. z o.o.", "Siemens Mobility Polska", "KGHM Zanam S.A.", "Orlen Automatyka",
        "Amica Wronki S.A.", "Solaris Bus & Coach", "Huta Stalowa Wola", "FCA Poland Tychy",
        "Grupa Azoty Puławy", "Alstom Pojazdy Szynowe", "Danfoss Poland", "Rockwell Automation Polska",
        "Valeo Autosystemy Skawina", "BWI Poland Technical Center", "Electrolux Poland",
        "Wielton S.A. Wieluń", "Bumar-Łabędy Gliwice", "Volkswagen Poznań", "MAN Trucks Niepołomice",
        "Kostal Poland", "ZF Automotive Poland", "Mahle Polska Krotoszyn", "Brose Doksy s.r.o.",
        "SKF Polska Poznań", "Schneider Electric Dystrybucja", "Eaton Automotive Bielsko",
        "Trelleborg Wheel Systems", "Hutchinson Poland Żywiec", "Cooper Standard Piotrków",
        "Faurecia Gorzów", "Gestamp Polska Września", "Stellantis Gliwice", "Toyota Motor Manufacturing"
    ]

    @classmethod
    def seed_enterprise_dataset(cls, company_id: str = "CLIENT_A", force: bool = False) -> Dict[str, Any]:
        """
        Główna metoda zasilająca: generuje pełny profil korporacyjny dla podanej firmy.
        """
        con = get_db_connection()

        # Sprawdzenie czy już istnieją dane zleceń
        existing_orders = con.execute("SELECT COUNT(*) FROM sap_orders_vbak_vbap WHERE company_id = ?", [company_id]).fetchone()[0]
        if existing_orders > 100 and not force:
            return {
                "status": "already_seeded",
                "message": f"Baza firmy {company_id} posiada już {existing_orders} pozycji zleceń.",
                "orders_count": existing_orders
            }

        # ---------------------------------------------------------------------
        # 1. GENEROWANIE KARTOTEK SŁOWNIKOWYCH (TVAK, TVTW, TVBUR, TVKO)
        # ---------------------------------------------------------------------
        con.execute("DELETE FROM sap_dictionaries_tvxx WHERE company_id = ?", [company_id])
        dictionaries = [
            # TVAK - Rodzaje Zleceń Sprzedaży
            ("TVAK", "TA", "Zlecenie standardowe", "Standardowa sprzedaż wyrobów gotowych (MTS) z magazynu centralnego", "Dokument podstawowy"),
            ("TVAK", "ZOR1", "Zlecenie ekspresowe B2B", "Priorytetowa wysyłka 24h dla kluczowych klientów OEM", "Krótszy czas kompletacji"),
            ("TVAK", "ZEXP", "Zlecenie eksportowe", "Eksport kraje trzecie z odprawą celną SAD i regułami Incoterms DAP/FCA", "Wymaga odprawy celnej"),
            ("TVAK", "ZDOM", "Zlecenie krajowe hurt", "Sprzedaż krajowa do sieci dystrybucji z rabatami obrotowymi", "Wydłużony termin płatności"),
            ("TVAK", "KB", "Uzupełnienie konsygnacji", "Wysyłka towaru do składu konsygnacyjnego klienta (zapas W, bez faktury)", "Ruch magazynowy 631"),
            ("TVAK", "KE", "Pobranie z konsygnacji", "Rozliczenie pobrania ze składu konsygnacyjnego (faktura F2, ruch 633)", "Fakturowane natychmiast"),
            ("TVAK", "RE", "Zlecenie zwrotu", "Przyjęcie reklamowanego towaru na skład kwarantanny QM (ruch 651)", "Wymaga referencji do F2"),
            ("TVAK", "L2", "Żądanie debetowe RRB", "Fakturowanie nakładcze roboczogodzin z CAT2 po transakcji DP90", "Usługi inżynierskie"),
            # TVTW - Kanały Dystrybucji
            ("TVTW", "10", "Sprzedaż bezpośrednia OEM/B2B", "Dostawy bezpośrednio do zakładów produkcyjnych i producentów maszyn", "Kanał strategiczny"),
            ("TVTW", "20", "Dystrybucja hurtowa i partnerska", "Sprzedaż przez sieć certyfikowanych dystrybutorów i hurtowni", "Rabaty cennikowe KONDA"),
            ("TVTW", "30", "Projekty i Generalne Wykonawstwo", "Dedykowane kontrakty infrastrukturalne i przetargi przemysłowe", "Fakturowanie etapowe"),
            # TVBUR - Biura Sprzedaży
            ("TVBUR", "1010", "Biuro Handlowe Śląsk (Katowice)", "Centrala operacyjna i obsługa przemysłu ciężkiego (Region Południe)", "Główny punkt kontaktu"),
            ("TVBUR", "1020", "Biuro Handlowe Mazowsze (Warszawa)", "Obsługa klientów strategicznych OEM, sieci handlowych i centrali korporacji", "Biuro kluczowych kont"),
            ("TVBUR", "1030", "Biuro Eksportu DACH (Frankfurt)", "Obsługa rynków Niemcy, Austria, Szwajcaria i kraje Beneluksu", "Rozliczenia w EUR"),
            # TVKO - Organizacje Sprzedaży
            ("TVKO", "1000", "Global Manufacturing Polska", "Główna organizacja sprzedaży spółki produkcyjnej", "Kraj i eksport"),
            ("TVKO", "2000", "Apex International Trading", "Wewnętrzna spółka dystrybucyjna dla operacji Intercompany", "Rozliczenia IV")
        ]

        con.execute("DELETE FROM sap_dictionaries_tvxx WHERE company_id = ?", [company_id])
        max_dict_id_row = con.execute("SELECT COALESCE(MAX(id), 0) FROM sap_dictionaries_tvxx").fetchone()
        dict_id = (max_dict_id_row[0] if max_dict_id_row else 0) + 1

        for d in dictionaries:
            con.execute("""
                INSERT INTO sap_dictionaries_tvxx (id, company_id, dict_type, code, bezeichnung, business_meaning, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [dict_id, company_id, d[0], d[1], d[2], d[3], d[4]])
            dict_id += 1

        # ---------------------------------------------------------------------
        # 2. GENEROWANIE PORTFELA RYNKOWEGO KLIENTÓW KNVV (300 KONT)
        # ---------------------------------------------------------------------
        random.seed(42)
        cities_poland = ["Katowice", "Gliwice", "Warszawa", "Poznań", "Wrocław", "Kraków", "Dąbrowa Górnicza", "Płock", "Gdańsk", "Łódź", "Bielsko-Biała"]
        cities_export = ["Berlin", "Monachium", "Stuttgart", "Frankfurt", "Drezno", "Ostrawa", "Praga", "Bratysława", "Wiedeń"]
        kdgrp_choices = [("01", "B2B Przemysł & OEM"), ("02", "Dystrybutor Hurtowy"), ("03", "Sieci i Składy Techniczne"), ("04", "Eksport Kluczowy")]
        bzirk_choices = ["PL01", "PL02", "PL03", "PL04", "DE01", "CEE1"]
        inco_choices = ["DAP", "FCA", "EXW", "CPT", "DDP"]
        zterm_choices = ["NT14", "NT30", "NT60", "0001", "ZT05"]

        created_customers = []
        for i in range(1, 301):
            kunnr = f"C-{10000 + i}"
            is_export = (i % 5 == 0)
            base_name = cls.CUSTOMER_NAMES_BASE[(i - 1) % len(cls.CUSTOMER_NAMES_BASE)]
            cust_name = f"{base_name} Oddział {i}" if i > len(cls.CUSTOMER_NAMES_BASE) else base_name
            
            land = "DE" if is_export and (i % 2 == 0) else ("CZ" if is_export else "PL")
            city = random.choice(cities_export) if is_export else random.choice(cities_poland)
            kdgrp, kdgrp_name = kdgrp_choices[3] if is_export else random.choice(kdgrp_choices[:3])
            bzirk = "DE01" if land == "DE" else ("CEE1" if land == "CZ" else random.choice(bzirk_choices[:4]))
            konda = "03" if kdgrp == "01" else ("02" if kdgrp == "02" else "01")
            inco1 = "FCA" if is_export else random.choice(inco_choices)
            zterm = "NT60" if kdgrp == "02" else random.choice(zterm_choices)
            vwerk = "1000" if bzirk in ["PL01", "PL02", "PL03"] else "1010"
            credit_limit = round(random.uniform(200000.0, 5000000.0), 2)
            exposure = round(credit_limit * random.uniform(0.1, 0.75), 2)
            ktgrd = "02" if is_export else "01"
            taxkd = "0" if is_export else "1"

            kvgr1 = "STRATEGICZNY" if credit_limit > 2000000 else ("KLUCZOWY" if credit_limit > 800000 else "STANDARD")
            kvgr2 = "EKSPORT" if is_export else "KRAJ"

            con.execute("""
                INSERT OR REPLACE INTO sap_customers 
                (kunnr, company_id, name1, vkorg, vtweg, spart, ktgrd, credit_limit, current_exposure,
                 land1, stceg, zterm, inco1, inco2, vwerk, taxkd, kdgrp, bzirk, konda, kvgr1, kvgr2)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                kunnr, company_id, cust_name, "1000", "10" if kdgrp == "01" else "20", "00",
                ktgrd, credit_limit, exposure, land, f"{land}{random.randint(100000000, 999999999)}",
                zterm, inco1, city, vwerk, taxkd, kdgrp, bzirk, konda, kvgr1, kvgr2
            ])
            created_customers.append(kunnr)

        # ---------------------------------------------------------------------
        # 3. GENEROWANIE 3 500 POZYCJI ZLECEŃ SPRZEDAŻY (VBAK + VBAP)
        # ---------------------------------------------------------------------
        con.execute("DELETE FROM sap_orders_vbak_vbap WHERE company_id = ?", [company_id])
        con.execute("DELETE FROM sap_flow_lips_vbrk WHERE company_id = ?", [company_id])

        max_order_id_row = con.execute("SELECT COALESCE(MAX(id), 0) FROM sap_orders_vbak_vbap").fetchone()
        item_id = (max_order_id_row[0] if max_order_id_row else 0) + 1

        max_flow_id_row = con.execute("SELECT COALESCE(MAX(id), 0) FROM sap_flow_lips_vbrk").fetchone()
        flow_id = (max_flow_id_row[0] if max_flow_id_row else 0) + 1

        start_date = datetime.now() - timedelta(days=180)
        order_seq = 10001000
        total_items_created = 0
        items_per_order_choices = [1, 2, 3, 4, 5]

        auart_weights = [
            ("TA", 0.55),
            ("ZOR1", 0.15),
            ("ZEXP", 0.15),
            ("ZDOM", 0.08),
            ("KB", 0.04),
            ("L2", 0.03)
        ]

        order_rows = []
        flow_rows = []

        while total_items_created < 3500:
            order_seq += 1
            vbeln = str(order_seq)
            days_ago = random.randint(0, 180)
            erdat = (start_date + timedelta(days=days_ago)).date()
            
            # Losowanie rodzaju zlecenia
            rand_val = random.random()
            cum = 0.0
            chosen_auart = "TA"
            for auart, weight in auart_weights:
                cum += weight
                if rand_val <= cum:
                    chosen_auart = auart
                    break

            # Dobór klienta
            if chosen_auart == "ZEXP":
                export_customers = [c for c in created_customers if int(c.split("-")[1]) % 5 == 0]
                kunnr = random.choice(export_customers) if export_customers else created_customers[0]
            else:
                kunnr = random.choice(created_customers)

            num_items = random.choice(items_per_order_choices)
            for pos_idx in range(1, num_items + 1):
                if total_items_created >= 3500:
                    break

                posnr = pos_idx * 10
                prod = random.choice(cls.PRODUCTS_CATALOG)

                # Dobór PSTYV wg asortymentu i zlecenia
                if chosen_auart == "KB":
                    pstyv = "EBN"
                elif chosen_auart == "L2":
                    pstyv = "L2N"
                elif prod["category"] == "MTO":
                    pstyv = "TAK"
                elif prod["category"] == "TAS":
                    pstyv = "TAS"
                elif prod["category"] == "CONSIGNMENT":
                    pstyv = "KEN"
                else:
                    pstyv = "TAN"

                # Ilości wg jednostki miary
                if prod["unit"] == "TO":
                    kwmeng = round(random.uniform(2.0, 24.0), 1)
                elif prod["unit"] == "M":
                    kwmeng = round(random.uniform(100.0, 2500.0), 0)
                elif prod["unit"] == "PAL":
                    kwmeng = float(random.randint(1, 15))
                elif prod["unit"] == "KPL":
                    kwmeng = float(random.randint(1, 5))
                else:
                    kwmeng = round(random.uniform(1.0, 50.0), 0)

                # Wycena z rabatami
                price_discount_factor = random.uniform(0.88, 1.05)
                netpr = round(prod["base_price"] * price_discount_factor, 2)
                netwr = round(kwmeng * netpr, 2)
                waerk = "EUR" if chosen_auart == "ZEXP" else "PLN"

                order_rows.append((
                    item_id, company_id, vbeln, posnr, erdat, chosen_auart, "1000", "10", "00", kunnr,
                    prod["matnr"], prod["name"], kwmeng, prod["unit"], netpr, netwr, waerk, pstyv
                ))
                item_id += 1
                total_items_created += 1

                # -------------------------------------------------------------
                # 4. GENEROWANIE PRZEPŁYWU REALIZACJI (LIPS + VBRK) - do 1 500
                # -------------------------------------------------------------
                if len(flow_rows) < 1500 and chosen_auart != "KB":
                    lead_time = random.randint(1, 5)
                    erdat_deliv = erdat + timedelta(days=lead_time)
                    erdat_bill = erdat_deliv + timedelta(days=1)
                    deliv_num = f"800{vbeln[4:]}"
                    bill_num = f"900{vbeln[4:]}"

                    vstel_choice = random.choice(["1000", "1010", "1020"])
                    route_choice = "DE0001" if chosen_auart == "ZEXP" else random.choice(["PL0001", "PL0002", "PL0003"])
                    fkart_choice = "IV" if random.random() < 0.08 else ("L2" if pstyv == "L2N" else "F2")
                    kurrf = 4.3250 if waerk == "EUR" else 1.0

                    flow_rows.append((
                        flow_id, company_id, vbeln, posnr, deliv_num, posnr, "LF", vstel_choice, route_choice, erdat_deliv,
                        bill_num, posnr, fkart_choice, "L", waerk, kurrf, erdat_bill, netwr, lead_time
                    ))
                    flow_id += 1

        # Szybki zapis wsadowy (Bulk Batch Insert)
        con.executemany("""
            INSERT INTO sap_orders_vbak_vbap 
            (id, company_id, vbeln, posnr, erdat, auart, vkorg, vtweg, spart, kunnr, matnr, arktx, kwmeng, vrkme, netpr, netwr, waerk, pstyv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, order_rows)

        con.executemany("""
            INSERT INTO sap_flow_lips_vbrk
            (id, company_id, vbeln_order, posnr_order, vbeln_deliv, posnr_deliv, lfart, vstel, route, erdat_deliv,
             vbeln_bill, posnr_bill, fkart, fktyp, waerk, kurrf, erdat_bill, netwr_bill, lead_time_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, flow_rows)

        logistics_flow_records = [r[0] for r in flow_rows]

        return {
            "status": "success",
            "company_id": company_id,
            "orders_items_count": total_items_created,
            "customers_count": len(created_customers),
            "logistics_flow_count": len(logistics_flow_records),
            "dictionaries_count": len(dictionaries),
            "message": f"Pomyślnie zasilono profil firmy {company_id} kompletnym zbiorem korporacyjnym: "
                       f"{total_items_created} pozycji zleceń (VBAK+VBAP), {len(created_customers)} kont KNVV, "
                       f"{len(logistics_flow_records)} rekordów realizacji (LIPS+VBRK) i słowniki TVAK/TVTW/TVBUR."
        }
