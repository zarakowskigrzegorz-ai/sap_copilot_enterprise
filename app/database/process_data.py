# -*- coding: utf-8 -*-
"""
Katalog kompleksowych procesów biznesowych SAP dla przedsiębiorstw produkcyjnych,
handlowo-dystrybucyjnych, usługowo-projektowych oraz logistyki posprzedażowej.
Zawiera powiązania międzymodułowe (SD, MM, PP, FI, CO, PS), typy pozycji, linie harmonogramu,
rodzaje faktur i tabele systemowe.
"""

ENTERPRISE_PROCESSES = [
    # =========================================================================
    # 1. FIRMY PRODUKCYJNE (MANUFACTURING)
    # =========================================================================
    {
        "process_code": "O2C_MTS",
        "process_name": "Produkcja na magazyn (Make-to-Stock - MTS)",
        "business_domain": "MANUFACTURING",
        "domain_name": "Produkcja Standardowa",
        "description": "Standardowy proces sprzedaży wyrobów gotowych z zapasu magazynowego, uzupełnianego planami produkcyjnymi PIR/MPS.",
        "industry_fit": "Przemysł masowy, FMCG, chemia, przetwórstwo tworzyw, standardowe maszyny seryjne",
        "key_tcodes": ["VA01", "VL01N", "LT03", "VL02N", "VF01", "VF02"],
        "item_categories": "TAN (Standard Item)",
        "schedule_line_cats": "CP (MRP requirement with ATP check)",
        "billing_types": "F2 (Invoice)",
        "integration_modules": "SD-PP-MM-FI-CO",
        "steps": [
            {
                "step_order": 1,
                "phase": "Pre-sales",
                "tcode": "VA11 / VA21",
                "name": "Zapytanie i Oferta Handlowa",
                "description": "Rejestracja zapytania ofertowego i kalkulacja ceny ofertowej dla odbiorcy.",
                "prerequisites": "Kartoteka klienta KNA1/BP, cennik materiału VK11",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "IN / QT",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Sales Order",
                "tcode": "VA01",
                "name": "Zlecenie Sprzedaży (Standard Order)",
                "description": "Utworzenie zlecenia sprzedaży. Sprawdzenie dostępności zapasu ATP i kontroli limitu kredytowego.",
                "prerequisites": "Zaakceptowana oferta lub zamówienie klienta, zapas wolny",
                "tables_involved": "VBAK, VBAP, VBEP, KONV",
                "doc_type": "TA / OR",
                "module": "SD"
            },
            {
                "step_order": 3,
                "phase": "Outbound Delivery",
                "tcode": "VL01N",
                "name": "Dostawa Wychodząca",
                "description": "Wygenerowanie dokumentu dostawy na podstawie terminu wysyłki z linii harmonogramu.",
                "prerequisites": "Otwarte pozycje zlecenia, potwierdzona data dostawy",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LF",
                "module": "SD"
            },
            {
                "step_order": 4,
                "phase": "Warehouse",
                "tcode": "LT03 / EWM",
                "name": "Kompletacja i Pakowanie (Picking & Packing)",
                "description": "Pobranie towaru z regałów magazynowych i przygotowanie jednostek wysyłkowych (HU).",
                "prerequisites": "Dostawa wychodząca, wolne jednostki składowania",
                "tables_involved": "VBFS, LIKP, LIPS",
                "doc_type": "TO / WT",
                "module": "WM/EWM"
            },
            {
                "step_order": 5,
                "phase": "Goods Issue",
                "tcode": "VL02N",
                "name": "Wydanie Towarów (Post Goods Issue - PGI)",
                "description": "Księgowanie rozchodu magazynowego (ruch 601), zmniejszenie stanu magazynowego i księgowanie kosztu COGS.",
                "prerequisites": "Skompletowana i sprawdzona dostawa",
                "tables_involved": "MKPF, MSEG, BKPF, BSEG",
                "doc_type": "WA / MatDoc",
                "module": "MM/SD"
            },
            {
                "step_order": 6,
                "phase": "Billing",
                "tcode": "VF01 / VF04",
                "name": "Faktura Sprzedaży",
                "description": "Wystawienie faktury dla odbiorcy na podstawie wydania towarów.",
                "prerequisites": "Zaksięgowane wydanie towaru (LIPS-WBSTK = 'C')",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD"
            },
            {
                "step_order": 7,
                "phase": "Accounting Release",
                "tcode": "VF02 / VFX3",
                "name": "Księgowanie w FI (General Ledger)",
                "description": "Automatyczne zaksięgowanie przychodu (ERL) i rozrachunku z odbiorcą w księdze głównej.",
                "prerequisites": "Prawidłowa determinacja kont w tabeli VKOA",
                "tables_involved": "BKPF, BSEG, BSID",
                "doc_type": "RV (FI Doc)",
                "module": "FI"
            }
        ]
    },
    {
        "process_code": "MTO_PRODUCTION",
        "process_name": "Produkcja pod zlecenie klienta (Make-to-Order - MTO)",
        "business_domain": "MANUFACTURING",
        "domain_name": "Produkcja Jednostkowa & MTO",
        "description": "Wytwarzanie wyrobów ściśle dopasowanych do specyfikacji klienta. Zlecenie sprzedaży jest nośnikiem kosztów i bezpośrednio generuje zlecenie produkcyjne.",
        "industry_fit": "Budowa maszyn przemysłowych, aparatura energetyczna, stolarka otworowa, meble na wymiar, automotive custom",
        "key_tcodes": ["VA01", "CK51N", "MD04", "CO01", "CO11N", "VL01N", "VF01", "VA88"],
        "item_categories": "TAK (Make-to-order without configuration) / TAC (Configurable)",
        "schedule_line_cats": "CP (Requirements to MRP with sales order stock allocation)",
        "billing_types": "F2 (Invoice)",
        "integration_modules": "SD-PP-CO-MM-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Engineering & Quotation",
                "tcode": "VA21 / CK51N",
                "name": "Specyfikacja Techniczna i Kalkulacja Kosztów",
                "description": "Opracowanie konfiguracji technicznej wyrobu i kalkulacja jednostkowa zlecenia sprzedaży.",
                "prerequisites": "Struktura BOM (CS01), marszruta technologiczna (CA01)",
                "tables_involved": "KEKO, KEPH, VBAK",
                "doc_type": "QT / Costing",
                "module": "SD/CO"
            },
            {
                "step_order": 2,
                "phase": "Sales Order (MTO)",
                "tcode": "VA01",
                "name": "Zlecenie Sprzedaży MTO",
                "description": "Wprowadzenie zlecenia z pozycją TAK. Przypisanie klasy zapotrzebowań (Requirement Class 040) tworzącej zapas specjalny 'E'.",
                "prerequisites": "Procedura ustalania typu pozycji VOV4, profil kalkulacji kosztów",
                "tables_involved": "VBAK, VBAP, VBUP",
                "doc_type": "TA / MS",
                "module": "SD"
            },
            {
                "step_order": 3,
                "phase": "Production Planning",
                "tcode": "MD04 / CO01",
                "name": "Utworzenie Zlecenia Produkcyjnego",
                "description": "Automatyczne (MRP) lub ręczne wygenerowanie zlecenia produkcyjnego powiązanego ze zleceniem sprzedaży (AUFNR -> VBELN/POSNR).",
                "prerequisites": "Otwarte zapotrzebowanie MRP, rozbicie BOM",
                "tables_involved": "AFKO, AFPO, RESB",
                "doc_type": "PP Order",
                "module": "PP"
            },
            {
                "step_order": 4,
                "phase": "Manufacturing Execution",
                "tcode": "CO11N / CO15",
                "name": "Realizacja Produkcji i Potwierdzenie Operacji",
                "description": "Pobranie komponentów ze składu (ruch 261) i potwierdzenie przepracowanych roboczogodzin (potwierdzenie operacji).",
                "prerequisites": "Zwolnione zlecenie produkcyjne (status REL)",
                "tables_involved": "AFRU, MSEG",
                "doc_type": "Confirmation",
                "module": "PP/CO"
            },
            {
                "step_order": 5,
                "phase": "Goods Receipt into MTO Stock",
                "tcode": "MIGO / CO01",
                "name": "Przyjęcie Wyrobu na Zapas Zlecenia (Ruch 101 E)",
                "description": "Przyjęcie wyrobu gotowego z produkcji bezpośrednio na zapas specjalny 'E' (Sales Order Stock przypisany do zlecenia sprzedaży).",
                "prerequisites": "Zakończona produkcja i kontrola jakości QM",
                "tables_involved": "MKPF, MSEG, MSKA",
                "doc_type": "MatDoc (101 E)",
                "module": "MM/PP"
            },
            {
                "step_order": 6,
                "phase": "Delivery from MTO Stock",
                "tcode": "VL01N",
                "name": "Dostawa ze Składu Zlecenia Klienta",
                "description": "Pobranie dedykowanego wyrobu z zapasu 'E' do wysyłki dla klienta.",
                "prerequisites": "Dostępny zapas specjalny w tabeli MSKA",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LF",
                "module": "SD"
            },
            {
                "step_order": 7,
                "phase": "Goods Issue (PGI)",
                "tcode": "VL02N",
                "name": "Wydanie Towaru ze Składu Zlecenia (Ruch 601 E)",
                "description": "Księgowanie wydania (ruch 601 E) z przypisaniem kosztu do pozycji zlecenia sprzedaży.",
                "prerequisites": "Skompletowana dostawa",
                "tables_involved": "MKPF, MSEG",
                "doc_type": "WA (601 E)",
                "module": "SD/MM"
            },
            {
                "step_order": 8,
                "phase": "Billing",
                "tcode": "VF01",
                "name": "Faktura Sprzedaży",
                "description": "Fakturowanie wyrobu wg ustalonej ceny zlecenia lub kalkulacji kosztowej.",
                "prerequisites": "Zaksięgowane wydanie towaru",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD"
            },
            {
                "step_order": 9,
                "phase": "Order Settlement",
                "tcode": "VA88 / KGI2",
                "name": "Rozliczenie Kosztów Zlecenia i Marży do CO-PA",
                "description": "Naliczenie narzutów kosztów ogólnych, porównanie kosztów rzeczywistych z przychodami i rozliczenie wyniku finansowego zlecenia.",
                "prerequisites": "Zakończone fakturowanie i potwierdzenia produkcyjne",
                "tables_involved": "COBK, COEP, CE1xxxx",
                "doc_type": "Settlement",
                "module": "CO-PA"
            }
        ]
    },
    {
        "process_code": "SUBCONTRACTING",
        "process_name": "Kooperacja i Podwykonawstwo (Subcontracting in Sales)",
        "business_domain": "MANUFACTURING",
        "domain_name": "Podwykonawstwo & Kooperacja",
        "description": "Proces produkcji, w którym część operacji technologicznych (np. cynkowanie, lakierowanie proszkowe, hartowanie) realizuje zewnętrzny podwykonawca.",
        "industry_fit": "Obróbka metali, konstrukcje stalowe, elektronika (EMS), automotive",
        "key_tcodes": ["VA01", "ME21N", "ME2O", "MIGO", "MIRO", "VL01N", "VF01"],
        "item_categories": "TAN (Parent item) / L (Subcontracting Purchase Item)",
        "schedule_line_cats": "CP",
        "billing_types": "F2",
        "integration_modules": "SD-PP-MM-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Sales Demand",
                "tcode": "VA01",
                "name": "Zlecenie Sprzedaży z Wymogiem Kooperacji",
                "description": "Rejestracja zlecenia sprzedaży wyrobu wymagającego operacji podwykonawczej wg technologii.",
                "prerequisites": "Marszruta z operacją obróbki obcej (klucz sterowania PP02)",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "TA",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Subcontract PO",
                "tcode": "ME21N",
                "name": "Zamówienie Usługi Podwykonawczej",
                "description": "Utworzenie zamówienia zakupu usługi z pozycją typu 'L' i wykazem komponentów do powierzenia.",
                "prerequisites": "Rekord informacyjny podwykonawstwa (EINE-ESOKZ = 3)",
                "tables_involved": "EKKO, EKPO, EKET",
                "doc_type": "NB (Item L)",
                "module": "MM"
            },
            {
                "step_order": 3,
                "phase": "Component Issue",
                "tcode": "ME2O / MIGO",
                "name": "Wydanie Komponentów do Podwykonawcy (Ruch 541)",
                "description": "Wysłanie półfabrykatów lub surowców do kooperanta. Przeniesienie na zapas powierzony 'O' u dostawcy.",
                "prerequisites": "Zatwierdzone zamówienie zakupu, dostępny zapas komponentów",
                "tables_involved": "MSEG, MKPF, MSLB",
                "doc_type": "MatDoc (541)",
                "module": "MM"
            },
            {
                "step_order": 4,
                "phase": "Goods Receipt",
                "tcode": "MIGO",
                "name": "Przyjęcie Wyrobu Przetworzonego (Ruch 101 i 543)",
                "description": "Przyjęcie przetworzonego elementu (ruch 101) z jednoczesnym automatycznym rozliczeniem zużycia komponentów (ruch 543).",
                "prerequisites": "Dostarczenie partii przez kooperanta",
                "tables_involved": "MKPF, MSEG",
                "doc_type": "MatDoc (101/543)",
                "module": "MM"
            },
            {
                "step_order": 5,
                "phase": "Subcontract Invoice",
                "tcode": "MIRO",
                "name": "Weryfikacja Faktury Podwykonawcy",
                "description": "Zaksięgowanie faktury za usługę obróbki obcej w module FI-AP.",
                "prerequisites": "Zaksięgowane przyjęcie towaru (GR)",
                "tables_involved": "RBKP, RSEG, BKPF",
                "doc_type": "RE",
                "module": "FI/MM"
            },
            {
                "step_order": 6,
                "phase": "Delivery to Customer",
                "tcode": "VL01N / VL02N",
                "name": "Dostawa Końcowa i PGI do Klienta",
                "description": "Wysyłka gotowego wyrobu do klienta po zakończeniu wszystkich faz produkcyjnych.",
                "prerequisites": "Wyrob gotowy na stanie magazynowym",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LF",
                "module": "SD"
            },
            {
                "step_order": 7,
                "phase": "Billing",
                "tcode": "VF01",
                "name": "Faktura Sprzedaży dla Odbiorcy",
                "description": "Wystawienie faktury F2 uwzględniającej pełną cenę sprzedaży.",
                "prerequisites": "Zaksięgowane PGI (ruch 601)",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD"
            }
        ]
    },

    # =========================================================================
    # 2. FIRMY HANDLOWO-DYSTRYBUCYJNE (TRADING & WHOLESALE)
    # =========================================================================
    {
        "process_code": "THIRD_PARTY_TAS",
        "process_name": "Handel trójstronny / Dostawa bezpośrednia (Third-Party Dropshipping - TAS)",
        "business_domain": "TRADING",
        "domain_name": "Handel Trójstronny & Dropshipping",
        "description": "Klient zamawia towar w naszej firmie, ale wysyłka realizowana jest bezpośrednio z magazynu dostawcy/producenta do klienta końcowego. Zero kosztów magazynowania.",
        "industry_fit": "Dystrybutorzy IT, hurtownie budowlane, e-commerce B2B/B2C, handel surowcami wielkotonażowymi",
        "key_tcodes": ["VA01", "ME59N", "ME21N", "MIRO", "VF01", "VF04"],
        "item_categories": "TAS (Third-party item)",
        "schedule_line_cats": "CS (Third-party with Purchase Requisition generation)",
        "billing_types": "F2 (Order-related or GR/IR-related billing)",
        "integration_modules": "SD-MM-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Third-Party Order",
                "tcode": "VA01",
                "name": "Zlecenie Sprzedaży z Pozycją TAS",
                "description": "Wprowadzenie zlecenia sprzedaży. Pozycja TAS automatycznie wskazuje adres dostawy klienta (Ship-to) jako miejsce odbioru.",
                "prerequisites": "Reguła pozycji VOV4: Grupa typu pozycji BANC -> TAS, linia CS",
                "tables_involved": "VBAK, VBAP, VBEP",
                "doc_type": "TA (Item TAS)",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Purchase Requisition",
                "tcode": "Automatyczny Banf (EBAN)",
                "name": "Automatyczne Wygenerowanie Zapotrzebowania (Banf)",
                "description": "System SAP w locie tworzy pozycję zapotrzebowania zakupowego powiązaną ze zleceniem sprzedaży (EBAN-BANFN).",
                "prerequisites": "Kategoria linii harmonogramu CS z przypisaniem konta 'X' i typu pozycji 'S'",
                "tables_involved": "EBAN",
                "doc_type": "PR (Banf)",
                "module": "MM"
            },
            {
                "step_order": 3,
                "phase": "Purchase Order",
                "tcode": "ME21N / ME59N",
                "name": "Zamówienie Zakupu u Dostawcy (PO)",
                "description": "Konwersja Banf na zamówienie zakupu wysyłane do producenta z adresem dostawy klienta docelowego.",
                "prerequisites": "Przypisane źródło dostaw (źródłownik lub umowa ramowa)",
                "tables_involved": "EKKO, EKPO, EKET",
                "doc_type": "NB",
                "module": "MM"
            },
            {
                "step_order": 4,
                "phase": "Vendor Direct Dispatch",
                "tcode": "EDI / Awizo dostawy",
                "name": "Dostawa Bezpośrednia od Dostawcy do Klienta",
                "description": "Dostawca wysyła towar bez fizycznego udziału naszego magazynu. Otrzymujemy potwierdzenie doręczenia (POD).",
                "prerequisites": "Potwierdzenie wysyłki przez dostawcę",
                "tables_involved": "EKES (Potwierdzenia)",
                "doc_type": "ASN / POD",
                "module": "MM/SD"
            },
            {
                "step_order": 5,
                "phase": "Vendor Invoice",
                "tcode": "MIRO",
                "name": "Zaksięgowanie Faktury Zakupowej Dostawcy",
                "description": "Wprowadzenie faktury zakupu w MIRO. W zależności od konfiguracji kontroli kopiowania, krok ten odblokowuje fakturowanie klienta.",
                "prerequisites": "Potwierdzenie dostawy lub dowód dostawy",
                "tables_involved": "RBKP, RSEG, BKPF",
                "doc_type": "RE",
                "module": "FI/MM"
            },
            {
                "step_order": 6,
                "phase": "Customer Billing",
                "tcode": "VF01 / VF04",
                "name": "Wystawienie Faktury dla Klienta Końcowego",
                "description": "Wystawienie faktury F2 powiązanej bezpośrednio ze zleceniem sprzedaży lub fakturą zakupu.",
                "prerequisites": "Faktura dostawcy MIRO lub przyjęcie statystyczne",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD"
            },
            {
                "step_order": 7,
                "phase": "Financial Settlement",
                "tcode": "VF02 / VFX3",
                "name": "Zaksięgowanie w FI i Rozliczenie Marży",
                "description": "Rozliczenie przychodu ze sprzedaży (ERL) z kosztem zakupu towaru handlowego (COGS) i marżą transakcyjną.",
                "prerequisites": "Ustalenie kont w VKOA",
                "tables_involved": "BKPF, BSEG",
                "doc_type": "RV",
                "module": "FI"
            }
        ]
    },
    {
        "process_code": "INDIVIDUAL_PO_TAB",
        "process_name": "Zamówienie indywidualne pod klienta (Individual Purchase Order - TAB)",
        "business_domain": "TRADING",
        "domain_name": "Zakup pod Zamówienie",
        "description": "Zamówienie zakupu towaru dedykowanego pod konkretne zlecenie klienta, ale z fizycznym przyjęciem do magazynu firmy przed wysyłką.",
        "industry_fit": "Dystrybutorzy części specjalistycznych, elektronika przemysłowa, farmacja specjalistyczna",
        "key_tcodes": ["VA01", "ME21N", "MIGO", "VL01N", "VL02N", "VF01"],
        "item_categories": "TAB (Individual purchase order)",
        "schedule_line_cats": "CB (Purchase requisition with receipt into sales order stock)",
        "billing_types": "F2",
        "integration_modules": "SD-MM-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Sales Order",
                "tcode": "VA01",
                "name": "Zlecenie z Pozycją TAB",
                "description": "Utworzenie zlecenia sprzedaży generującego zapotrzebowanie zakupowe na zapas zlecenia.",
                "prerequisites": "Typ pozycji TAB, kategoria linii CB",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "TA (Item TAB)",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Purchase Requisition",
                "tcode": "EBAN",
                "name": "Zapotrzebowanie Zakupowe pod Zapas Zlecenia 'E'",
                "description": "Automatyczne wygenerowanie pozycji PR z przypisaniem konta do zlecenia sprzedaży.",
                "prerequisites": "Linia harmonogramu CB",
                "tables_involved": "EBAN",
                "doc_type": "PR (Banf)",
                "module": "MM"
            },
            {
                "step_order": 3,
                "phase": "Purchase Order",
                "tcode": "ME21N",
                "name": "Zamówienie Zakupu u Dostawcy",
                "description": "Konwersja Banf na zamówienie zakupu z miejscem dostawy w naszym magazynie centralnym.",
                "prerequisites": "Wybrany dostawca",
                "tables_involved": "EKKO, EKPO",
                "doc_type": "NB",
                "module": "MM"
            },
            {
                "step_order": 4,
                "phase": "Goods Receipt into Stock E",
                "tcode": "MIGO",
                "name": "Przyjęcie do Magazynu na Zapas 'E' (Ruch 101 E)",
                "description": "Przyjęcie towaru na skład jako zapas specjalny zarezerwowany wyłącznie dla tego zlecenia klienta.",
                "prerequisites": "Dostawa od dostawcy",
                "tables_involved": "MKPF, MSEG, MSKA",
                "doc_type": "MatDoc (101 E)",
                "module": "MM"
            },
            {
                "step_order": 5,
                "phase": "Outbound Delivery",
                "tcode": "VL01N / VL02N",
                "name": "Dostawa Wychodząca i Wydanie Towarów (Ruch 601 E)",
                "description": "Wysyłka towaru do klienta ze składu dedykowanego.",
                "prerequisites": "Zapas dostępny w tabeli MSKA",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LF",
                "module": "SD"
            },
            {
                "step_order": 6,
                "phase": "Billing",
                "tcode": "VF01",
                "name": "Faktura Sprzedaży",
                "description": "Wystawienie faktury F2 dla odbiorcy.",
                "prerequisites": "Zaksięgowane wydanie towaru",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD"
            }
        ]
    },
    {
        "process_code": "CONSIGNMENT",
        "process_name": "Gospodarka konsygnacyjna u klienta (Consignment Processing - KB/KE/KR/KA)",
        "business_domain": "TRADING",
        "domain_name": "Sprzedaż Konsygnacyjna",
        "description": "4-etapowy proces depozytowy: towar jest składowany w magazynie klienta, ale pozostaje własnością sprzedawcy do momentu fizycznego pobrania.",
        "industry_fit": "Dostawcy komponentów motoryzacyjnych (Tier 1/2), dystrybucja narzędzi, farmacja szpitalna, retail",
        "key_tcodes": ["VA01 (KB)", "VL01N", "VA01 (KE)", "VF01", "VA01 (KR)", "VA01 (KA)"],
        "item_categories": "KBN (Fill-up) / KEN (Issue) / KRN (Returns) / KAN (Pick-up)",
        "schedule_line_cats": "E1 (Consignment Fill-up) / C0 (Consignment Issue)",
        "billing_types": "F2 (Dla pobrania KE) / G2 (Dla zwrotu KR) / Brak faktury (dla KB i KA)",
        "integration_modules": "SD-MM-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Consignment Fill-up",
                "tcode": "VA01 (typ KB)",
                "name": "Krok 1: Uzupełnienie Konsygnacji (Fill-up)",
                "description": "Zlecenie KB przemieszcza towar do składu klienta. Towar nadal jest własnością sprzedawcy (zapas specjalny 'W' klienta). Brak faktury.",
                "prerequisites": "Umowa konsygnacyjna z odbiorcą",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "KB (Item KBN)",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Fill-up Delivery",
                "tcode": "VL01N / VL02N",
                "name": "Wydanie na Zapas Konsygnacyjny (Ruch 631)",
                "description": "Przesunięcie zapasu z magazynu własnego na stan konsygnacyjny u klienta (ruch 631). Bez księgowania przychodu ani faktury.",
                "prerequisites": "Zapas wolny",
                "tables_involved": "MKPF, MSEG, MSKU",
                "doc_type": "LF (631)",
                "module": "SD/MM"
            },
            {
                "step_order": 3,
                "phase": "Consignment Issue",
                "tcode": "VA01 (typ KE)",
                "name": "Krok 2: Pobranie z Konsygnacji (Issue)",
                "description": "Raport klienta o zużyciu/sprzedaży towaru z depozytu. Utworzenie zlecenia pobrania KE, które zdejmuje towar ze stanu 'W' (ruch 633).",
                "prerequisites": "Raport zużycia od klienta, dostępny stan w MSKU",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "KE (Item KEN)",
                "module": "SD"
            },
            {
                "step_order": 4,
                "phase": "Issue Delivery & PGI",
                "tcode": "VL01N / VL02N",
                "name": "Rozchód z Zapasu Konsygnacyjnego (Ruch 633)",
                "description": "Księgowanie wydania (ruch 633) ze stanu konsygnacyjnego W. Księgowanie kosztu własnego (COGS).",
                "prerequisites": "Zlecenie pobrania KE",
                "tables_involved": "MKPF, MSEG, MSKU",
                "doc_type": "LF (633)",
                "module": "SD/MM"
            },
            {
                "step_order": 5,
                "phase": "Consignment Billing",
                "tcode": "VF01",
                "name": "Fakturowanie Pobranych Towarów",
                "description": "Wystawienie faktury F2 na rzeczywiście zużyte towary konsygnacyjne i zaksięgowanie w FI.",
                "prerequisites": "Zaksięgowane pobranie (ruch 633)",
                "tables_involved": "VBRK, VBRP, BKPF",
                "doc_type": "F2",
                "module": "SD/FI"
            },
            {
                "step_order": 6,
                "phase": "Consignment Pick-up",
                "tcode": "VA01 (typ KA)",
                "name": "Krok 3: Wycofanie Niesprzedanych Zapasów (Pick-up)",
                "description": "Wycofanie zalegającego towaru ze składu klienta z powrotem do magazynu własnego (ruch 632). Bez faktury.",
                "prerequisites": "Zlecenie wycofania KA",
                "tables_involved": "MKPF, MSEG, MSKU",
                "doc_type": "KA (Item KAN)",
                "module": "SD/MM"
            }
        ]
    },
    {
        "process_code": "INTERCOMPANY",
        "process_name": "Sprzedaż międzyfirmowa (Cross-Company Sales & Intercompany Billing)",
        "business_domain": "TRADING",
        "domain_name": "Sprzedaż Międzyfirmowa",
        "description": "Jednostka handlowa (Spółka A / BUKRS 1000) sprzedaje towar klientowi zewnętrznemu, ale fizyczna wysyłka odbywa się bezpośrednio z zakładu spółki produkcyjnej (Spółka B / BUKRS 2000).",
        "industry_fit": "Grupy kapitałowe, korporacje międzynarodowe, holdingi handlowo-produkcyjne",
        "key_tcodes": ["VA01", "VL01N", "VL02N", "VF01 (F2)", "VF01 (IV)", "EDI / FB60"],
        "item_categories": "TAN",
        "schedule_line_cats": "CP",
        "billing_types": "F2 (Customer Invoice) + IV (Intercompany Billing)",
        "integration_modules": "SD-MM-FI-EDI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Sales Order in Company A",
                "tcode": "VA01",
                "name": "Zlecenie w Jednostce Handlowej A",
                "description": "Zlecenie wprowadzone w Org. Sprzedaży 1000 (BUKRS 1000), ale z przypisaniem Zakładu Dostarczającego 2000 (należącego do BUKRS 2000).",
                "prerequisites": "Przypisanie zakładu do organizacji sprzedaży w SPRO",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "TA",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Outbound Delivery from Plant B",
                "tcode": "VL01N",
                "name": "Dostawa z Zakładu Spółki Produkcyjnej B",
                "description": "Dostawa realizowana w punkcie wysyłki zakładu 2000.",
                "prerequisites": "Otwarte pozycje zlecenia",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LF",
                "module": "SD"
            },
            {
                "step_order": 3,
                "phase": "Goods Issue in Plant B",
                "tcode": "VL02N",
                "name": "Wydanie Towarów ze Spółki B (PGI Ruch 601)",
                "description": "Rozchód magazynowy w BUKRS 2000. Księgowanie kosztu COGS w jednostce produkcyjnej B.",
                "prerequisites": "Skompletowana dostawa",
                "tables_involved": "MKPF, MSEG, BKPF",
                "doc_type": "WA (601)",
                "module": "MM/SD"
            },
            {
                "step_order": 4,
                "phase": "External Customer Invoice",
                "tcode": "VF01",
                "name": "Faktura dla Klienta Zewnętrznego (F2)",
                "description": "Faktura wystawiana przez jednostkę handlową A (BUKRS 1000) na kwotę rynkową dla klienta końcowego.",
                "prerequisites": "Zaksięgowane wydanie towaru",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "F2",
                "module": "SD/FI"
            },
            {
                "step_order": 5,
                "phase": "Intercompany Invoice (IV)",
                "tcode": "VF01",
                "name": "Faktura Wewnętrzna Międzyfirmowa (IV)",
                "description": "Faktura wystawiona przez Spółkę Produkcyjną B dla Spółki Handlowej A na podstawie cen transferowych (warunek cenowy PI01 / PI02).",
                "prerequisites": "Zdefiniowany klient wewnętrzny w SPRO (przypisany do BUKRS 1000)",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "IV",
                "module": "SD/FI"
            },
            {
                "step_order": 6,
                "phase": "Automated Vendor Posting",
                "tcode": "EDI / IDoc RD04 / FB60",
                "name": "Automatyczne Zaksięgowanie Zobowiązania w Spółce A",
                "description": "Komunikat EDI generuje dokument faktury dostawcy (AP) w jednostce handlowej A, zamykając rozrachunki wewnętrzne.",
                "prerequisites": "Konfiguracja profilu partnera EDI (WE20) i komunikatu RD04",
                "tables_involved": "BKPF, BSEG, EDIDC",
                "doc_type": "KR (Vendor Doc)",
                "module": "FI"
            }
        ]
    },

    # =========================================================================
    # 3. FIRMY USŁUGOWE I PROJEKTOWE (SERVICES & PROJECT-BASED)
    # =========================================================================
    {
        "process_code": "SERVICE_RRB_DP90",
        "process_name": "Fakturowanie usług nakładczych (Resource-Related Billing - RRB / DP90)",
        "business_domain": "SERVICES",
        "domain_name": "Usługi & Rozliczenia RRB",
        "description": "Rozliczanie rzeczywistych nakładów pracy (Time & Material), delegacji i zużytych materiałów na podstawie rejestracji w zleceniach serwisowych lub projektach.",
        "industry_fit": "Firmy konsultingowe i IT, serwisy maszyn i urządzeń, biura projektowe, audytorzy",
        "key_tcodes": ["VA41", "IW31 / CJ20N", "CAT2", "DP90", "VF01"],
        "item_categories": "TAD (Service item) / DIEN",
        "schedule_line_cats": "Brak wysyłki fizycznej",
        "billing_types": "L2 (Debit Memo) / F2",
        "integration_modules": "SD-CS-PS-CO-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Service Order or Project WBS",
                "tcode": "IW31 / CJ20N",
                "name": "Utworzenie Zlecenia Serwisowego lub Elementu WBS",
                "description": "Zdefiniowanie obiektu kosztowego, do którego będą przypisywane rzeczywiste nakłady czasu i materiałów.",
                "prerequisites": "Profil DIP (Dynamic Item Processor) przypisany w zleceniu",
                "tables_involved": "AUFK, PROJ, PRPS",
                "doc_type": "SM/PS Order",
                "module": "CS/PS"
            },
            {
                "step_order": 2,
                "phase": "Time & Expense Recording",
                "tcode": "CAT2 / KB21N",
                "name": "Rejestracja Godzin Pracy i Kosztów Rzeczywistych",
                "description": "Konsultanci i technicy wpisują przepracowane godziny (CAT2), koszty diet, hoteli i materiałów.",
                "prerequisites": "Zatwierdzone arkusze czasu pracy w CATS",
                "tables_involved": "CATSDB, COEP, COBK",
                "doc_type": "Timesheet / Cost Doc",
                "module": "CO/HR"
            },
            {
                "step_order": 3,
                "phase": "DIP Processing",
                "tcode": "DP90",
                "name": "Przetwarzanie Pozycji Dynamicznych (DP90)",
                "description": "Uruchomienie transakcji DP90. System odczytuje koszty, mapuje je wg profilu DIP na pozycje cennikowe i wylicza kwotę do zafakturowania.",
                "prerequisites": "Koszty zaksięgowane w CO, cennik roboczogodzin w VK11",
                "tables_involved": "AD01* (DIP tables), VBAK",
                "doc_type": "DIP Request",
                "module": "SD/CO"
            },
            {
                "step_order": 4,
                "phase": "Debit Memo Request (DMR)",
                "tcode": "VA02 / DP90",
                "name": "Wygenerowanie Żądania Rozliczenia (DMR)",
                "description": "Utworzenie dokumentu sprzedaży typu DMR (Debit Memo Request) z rozbiciem na stawki i godziny.",
                "prerequisites": "Zatwierdzenie propozycji rozliczenia w DP90",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "DMR (L2)",
                "module": "SD"
            },
            {
                "step_order": 5,
                "phase": "Service Invoice",
                "tcode": "VF01",
                "name": "Wystawienie Faktury za Usługi",
                "description": "Wystawienie faktury L2 ze specyfikacją wykonanych prac i zaksięgowanie w FI.",
                "prerequisites": "Zwolnione żądanie rozliczenia DMR",
                "tables_involved": "VBRK, VBRP, BKPF",
                "doc_type": "L2 (Invoice)",
                "module": "SD/FI"
            }
        ]
    },
    {
        "process_code": "MILESTONE_BILLING",
        "process_name": "Harmonogramy fakturowania i kamienie milowe (Milestone & Periodic Billing)",
        "business_domain": "SERVICES",
        "domain_name": "Projekty & Kamienie Milowe",
        "description": "Fakturowanie etapowe powiązane z postępem prac projektowych (np. 20% zaliczki, 50% odbiór prototypu, 30% wdrożenie produkcyjne) lub fakturowanie okresowe abonamentów.",
        "industry_fit": "Generalni wykonawcy, integratorzy systemów IT, budownictwo przemysłowe, licencje SaaS",
        "key_tcodes": ["VA01", "CJ20N", "VF01 (FA)", "VF01 (F2)", "VF04"],
        "item_categories": "TAO (Milestone Billing Item)",
        "schedule_line_cats": "Brak wysyłki fizycznej",
        "billing_types": "FA (Faktura zaliczkowa) / F2 (Faktura końcowa)",
        "integration_modules": "SD-PS-FI",
        "steps": [
            {
                "step_order": 1,
                "phase": "Contract with Billing Plan",
                "tcode": "VA01 / VA41",
                "name": "Zlecenie z Planem Fakturowania Etapowego",
                "description": "Definicja harmonogramu fakturowania w zleceniu z datami lub kamieniami milowymi powiązanymi z WBS.",
                "prerequisites": "Struktura projektu PS (CJ20N), procedura wyceny",
                "tables_involved": "VBAK, VBAP, FPLA, FPLT",
                "doc_type": "TA (Item TAO)",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Down Payment Invoice",
                "tcode": "VF01",
                "name": "Faktura Zaliczkowa (Wstępna)",
                "description": "Wystawienie faktury na zaliczkę (np. 20% wartości umowy) przed rozpoczęciem prac.",
                "prerequisites": "Otwarta linia planu fakturowania zaliczki",
                "tables_involved": "VBRK, VBRP",
                "doc_type": "FA",
                "module": "SD/FI"
            },
            {
                "step_order": 3,
                "phase": "Milestone Completion",
                "tcode": "CJ20N",
                "name": "Zaliczenie Kamienia Milowego w Projekcie",
                "description": "Kierownik projektu zatwierdza osiągnięcie etapu w systemie PS. SAP automatycznie usuwa blokadę fakturowania powiązanej linii.",
                "prerequisites": "Odbiór etapu przez zamawiającego",
                "tables_involved": "MLST, FPLT",
                "doc_type": "Milestone Release",
                "module": "PS/SD"
            },
            {
                "step_order": 4,
                "phase": "Partial Invoice",
                "tcode": "VF01",
                "name": "Faktura Częściowa za Etap",
                "description": "Wystawienie faktury za zrealizowany kamień milowy z częściowym rozliczeniem pobranych zaliczek.",
                "prerequisites": "Zwolniona blokada w planie fakturowania (FPLT-FAKSP = '')",
                "tables_involved": "VBRK, VBRP, BKPF",
                "doc_type": "F2 (Partial)",
                "module": "SD/FI"
            },
            {
                "step_order": 5,
                "phase": "Final Milestone & Closing",
                "tcode": "VF01",
                "name": "Faktura Końcowa i Zamknięcie Rozliczeń",
                "description": "Wystawienie faktury końcowej rozliczającej wszystkie zaliczki i fakturowanie pozostałej kwoty kontraktu.",
                "prerequisites": "Protokół odbioru końcowego",
                "tables_involved": "VBRK, VBRP, BKPF",
                "doc_type": "F2 (Final)",
                "module": "SD/FI"
            }
        ]
    },

    # =========================================================================
    # 4. REKLAMACJE, ZWROTY I KOREKTY (REVERSE LOGISTICS & COMPLAINTS)
    # =========================================================================
    {
        "process_code": "RETURNS_COMPLAINTS",
        "process_name": "Reklamacje, zwroty i faktury korygujące (Returns & Complaints - RE/LR/G2)",
        "business_domain": "COMPLAINTS",
        "domain_name": "Reklamacje & Zwroty",
        "description": "Kompleksowa obsługa zwrotu wadliwego lub omyłkowo wysłanego towaru: przyjęcie magazynowe do strefy kwarantanny, kontrola jakości i wystawienie faktury korygującej.",
        "industry_fit": "Każde przedsiębiorstwo handlowe i produkcyjne (Dział Obsługi Klienta / Reklamacji)",
        "key_tcodes": ["VA01 (RE)", "VL01N (LR)", "VL02N", "VA02", "VF01 (G2)"],
        "item_categories": "REN (Returns Item)",
        "schedule_line_cats": "DN (Returns with replenishment/stock adjustment)",
        "billing_types": "G2 (Credit Memo / Faktura korygująca)",
        "integration_modules": "SD-MM-FI-QM",
        "steps": [
            {
                "step_order": 1,
                "phase": "Return Order",
                "tcode": "VA01 (typ RE)",
                "name": "Rejestracja Zlecenia Zwrotu (RE)",
                "description": "Wprowadzenie zlecenia zwrotu z referencją do pierwotnej faktury sprzedaży F2. Wskazanie kodu przyczyny zwrotu (Order Reason).",
                "prerequisites": "Faktura sprzedaży w historii klienta, powód zwrotu (np. wada fabryczna, pomyłka w dostawie)",
                "tables_involved": "VBAK, VBAP",
                "doc_type": "RE (Item REN)",
                "module": "SD"
            },
            {
                "step_order": 2,
                "phase": "Return Delivery",
                "tcode": "VL01N",
                "name": "Dostawa Zwrotna (LR)",
                "description": "Utworzenie dokumentu przyjęcia zwrotu od przewoźnika do magazynu reklamacji.",
                "prerequisites": "Zlecenie zwrotu RE",
                "tables_involved": "LIKP, LIPS",
                "doc_type": "LR",
                "module": "SD"
            },
            {
                "step_order": 3,
                "phase": "Goods Receipt (PGR)",
                "tcode": "VL02N",
                "name": "Przyjęcie Towaru Zwrotnego (Ruch 651 lub 653)",
                "description": "Zaksięgowanie przyjęcia na stan: ruch 651 (zapas zablokowany do decyzji QM) lub ruch 653 (bezpośrednio na stan wolny).",
                "prerequisites": "Dostarczenie przesyłki przez kuriera",
                "tables_involved": "MKPF, MSEG",
                "doc_type": "MatDoc (651/653)",
                "module": "MM/SD"
            },
            {
                "step_order": 4,
                "phase": "Billing Block Release",
                "tcode": "VA02",
                "name": "Zdjęcie Blokady Uznania",
                "description": "Po pozytywnej weryfikacji technicznej kierownik serwisu zdejmuje blokadę rozliczeń ze zlecenia zwrotu.",
                "prerequisites": "Ekspertyza jakościowa QM",
                "tables_involved": "VBAK (pole FAKSK)",
                "doc_type": "Block Release",
                "module": "SD"
            },
            {
                "step_order": 5,
                "phase": "Credit Memo Billing",
                "tcode": "VF01",
                "name": "Wystawienie Faktury Korygującej (Uznanie G2)",
                "description": "Wystawienie korekty faktury (G2) ze zmniejszeniem należności i korektą podatku VAT.",
                "prerequisites": "Zwolniona blokada rozliczeń w zleceniu RE",
                "tables_involved": "VBRK, VBRP, BKPF",
                "doc_type": "G2 (Korekta)",
                "module": "SD/FI"
            }
        ]
    }
]
