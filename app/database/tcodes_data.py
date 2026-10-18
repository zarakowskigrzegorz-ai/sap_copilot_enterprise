# Kompletny katalog transakcji modułu SAP SD (Sales and Distribution)
# Podział na kategorie, role, tabele systemowe oraz ścieżki SPRO

SD_TCODES_DATA = [
    # --- 1. ZLECENIA I ZAPYTANIA SPRZEDAŻOWE (SALES ORDERS & INQUIRIES) ---
    {
        "tcode": "VA01",
        "name": "Utworzenie zlecenia sprzedaży (Create Sales Order)",
        "category": "SALES_ORDERS",
        "description": "Tworzenie zlecenia sprzedaży (Order-to-Cash). Wymaga zdefiniowania AUART (np. TA, OR, ZOR1), obszaru sprzedaży (VKORG/VTWEG/SPART) i kontrahenta KUNNR.",
        "tables_involved": "VBAK, VBAP, VBEP, KONV, PRCD_ELEMENTS",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA02",
        "name": "Zmiana zlecenia sprzedaży (Change Sales Order)",
        "category": "SALES_ORDERS",
        "description": "Modyfikacja pozycji zlecenia, ilości, terminów dostaw, blokad fakturowania i wysyłki (LIFSK/FAKSK) oraz warunków cenowych.",
        "tables_involved": "VBAK, VBAP, VBEP, CDPOS, CDHDR",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA03",
        "name": "Wyświetlenie zlecenia sprzedaży (Display Sales Order)",
        "category": "SALES_ORDERS",
        "description": "Podgląd zlecenia sprzedaży, przepływu dokumentów (Doc Flow), statusu realizacji pozycji i analizy cenowej.",
        "tables_involved": "VBAK, VBAP, VBFA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA05",
        "name": "Lista zleceń sprzedaży (List of Sales Orders)",
        "category": "SALES_ORDERS",
        "description": "Zestawienie dokumentów sprzedaży wg odbiorcy, materiału lub obszaru sprzedaży. Raport operacyjny.",
        "tables_involved": "VBAK, VBAP, VBUK, VBUP",
        "spro_path": "Transakcja raportowa",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA05N",
        "name": "Lista zleceń sprzedaży - rozszerzona (Sales Orders List Extended)",
        "category": "SALES_ORDERS",
        "description": "Nowsza wersja raportu VA05 zoptymalizowana pod S/4HANA z dodatkowymi filtrami i polami analitycznymi.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Transakcja raportowa",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA11",
        "name": "Utworzenie zapytania ofertowego (Create Inquiry)",
        "category": "SALES_ORDERS",
        "description": "Rejestracja zapytania klienta w fazie pre-sales. Rodzaj dokumentu IN.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA12",
        "name": "Zmiana zapytania ofertowego (Change Inquiry)",
        "category": "SALES_ORDERS",
        "description": "Edycja pozycji i warunków w zapytaniu ofertowym klienta.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA13",
        "name": "Wyświetlenie zapytania ofertowego (Display Inquiry)",
        "category": "SALES_ORDERS",
        "description": "Podgląd zapytania ofertowego i powiązanych dokumentów.",
        "tables_involved": "VBAK, VBAP, VBFA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA21",
        "name": "Utworzenie oferty sprzedaży (Create Quotation)",
        "category": "SALES_ORDERS",
        "description": "Tworzenie wiążącej oferty handlowej dla klienta (rodzaj dokumentu QT). Zawiera okres ważności BDATU/EDATU.",
        "tables_involved": "VBAK, VBAP, KONV",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA22",
        "name": "Zmiana oferty sprzedaży (Change Quotation)",
        "category": "SALES_ORDERS",
        "description": "Aktualizacja cen, rabatów i pozycji w ofercie handlowej.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA23",
        "name": "Wyświetlenie oferty sprzedaży (Display Quotation)",
        "category": "SALES_ORDERS",
        "description": "Podgląd oferty handlowej oraz statusu jej akceptacji/zamiany na zlecenie VA01.",
        "tables_involved": "VBAK, VBAP, VBFA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA25",
        "name": "Lista ofert sprzedaży (List of Quotations)",
        "category": "SALES_ORDERS",
        "description": "Raport ofert sprzedaży z podziałem na statusy ważności i stopień konwersji w zlecenia.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Transakcja raportowa",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA31",
        "name": "Utworzenie planu dostaw (Create Scheduling Agreement)",
        "category": "SALES_ORDERS",
        "description": "Tworzenie długoterminowego planu dostaw z harmonogramem wywołań (kluczowe w branży Automotive).",
        "tables_involved": "VBAK, VBAP, VBEP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Plany dostaw",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA32",
        "name": "Zmiana planu dostaw (Change Scheduling Agreement)",
        "category": "SALES_ORDERS",
        "description": "Edycja linii harmonogramu, numerów wywołań EDI i ilości skumulowanych w planie dostaw.",
        "tables_involved": "VBAK, VBAP, VBEP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA33",
        "name": "Wyświetlenie planu dostaw (Display Scheduling Agreement)",
        "category": "SALES_ORDERS",
        "description": "Podgląd planu dostaw i historii realizacji wywołań.",
        "tables_involved": "VBAK, VBAP, VBEP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA41",
        "name": "Utworzenie kontraktu sprzedaży (Create Sales Contract)",
        "category": "SALES_ORDERS",
        "description": "Tworzenie kontraktu ilościowego (KM) lub wartościowego (WK1/WK2) na dany okres rozliczeniowy.",
        "tables_involved": "VBAK, VBAP, VEDA",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Kontrakty",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA42",
        "name": "Zmiana kontraktu sprzedaży (Change Sales Contract)",
        "category": "SALES_ORDERS",
        "description": "Modyfikacja limitów wartościowych, reguł odwołań i terminów ważności kontraktu.",
        "tables_involved": "VBAK, VBAP, VEDA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VA43",
        "name": "Wyświetlenie kontraktu sprzedaży (Display Sales Contract)",
        "category": "SALES_ORDERS",
        "description": "Podgląd kontraktu i stopnia jego wykorzystania przez zlecenia odwołania (Release Orders).",
        "tables_involved": "VBAK, VBAP, VBFA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V.01",
        "name": "Lista niekompletnych zleceń sprzedaży (Incomplete Sales Orders)",
        "category": "SALES_ORDERS",
        "description": "Wyszukiwanie dokumentów z brakującymi danymi na podstawie procedury niekompletności (Incompletion Log).",
        "tables_involved": "VBAK, VBAP, VBUK, VBUP",
        "spro_path": "Raport operacyjny",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V.14",
        "name": "Zlecenia zablokowane dla dostawy (Orders Blocked for Delivery)",
        "category": "SALES_ORDERS",
        "description": "Wykaz zleceń z nałożoną blokadą dostawy (LIFSK) wymagających zwolnienia.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Raport operacyjny",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V.23",
        "name": "Zlecenia zablokowane dla fakturowania (Orders Blocked for Billing)",
        "category": "SALES_ORDERS",
        "description": "Wykaz zleceń i żądań faktur z blokadą fakturowania (FAKSK), np. reklamacje CR/DR.",
        "tables_involved": "VBAK, VBAP",
        "spro_path": "Raport operacyjny",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 2. WYSYŁKA, DOSTAWY I TRANSPORT (SHIPPING, DELIVERY & TRANSPORT) ---
    {
        "tcode": "VL01N",
        "name": "Utworzenie dostawy wychodzącej z referencją (Create Outbound Delivery)",
        "category": "SHIPPING_DELIVERY",
        "description": "Tworzenie dostawy wychodzącej do zlecenia sprzedaży. Wymaga podania punktu wysyłki (VSTEL) i daty wyboru.",
        "tables_involved": "LIKP, LIPS, VBFA",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Dostawy",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL01NO",
        "name": "Dostawa wychodząca bez referencji (Delivery Without Reference)",
        "category": "SHIPPING_DELIVERY",
        "description": "Utworzenie dostawy bez wcześniejszego zlecenia sprzedaży (np. wysyłki specjalne lub gratisy).",
        "tables_involved": "LIKP, LIPS",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL02N",
        "name": "Zmiana dostawy wychodzącej / PGI (Change Delivery & Post Goods Issue)",
        "category": "SHIPPING_DELIVERY",
        "description": "Zarządzanie dostawą: kompletacja (picking), pakowanie (packing) oraz księgowanie wydania towarów (PGI).",
        "tables_involved": "LIKP, LIPS, VBUP, MKPF, MSEG",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL03N",
        "name": "Wyświetlenie dostawy wychodzącej (Display Outbound Delivery)",
        "category": "SHIPPING_DELIVERY",
        "description": "Podgląd dostawy, statusu wydania materiału (WBSTK), jednostek obsługi ładunku (HU) i przepływu dokumentów.",
        "tables_involved": "LIKP, LIPS, VBFA",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL04",
        "name": "Kolejka zleceń do wysyłki (Process Delivery Due List)",
        "category": "SHIPPING_DELIVERY",
        "description": "Zbiorcze tworzenie dostaw wychodzących dla otwartych zleceń sprzedaży w tle lub dialogu.",
        "tables_involved": "VBAK, VBAP, LIKP, LIPS",
        "spro_path": "Przetwarzanie masowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL06O",
        "name": "Monitor dostaw wychodzących (Outbound Delivery Monitor)",
        "category": "SHIPPING_DELIVERY",
        "description": "Główne narzędzie kierownika magazynu/logistyki: monitorowanie dostaw do kompletacji, załadunku i wydania towaru.",
        "tables_involved": "LIKP, LIPS",
        "spro_path": "Raportowanie & Monitor operacyjny",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL06P",
        "name": "Monitor kompletacji dostaw (Picking Monitor)",
        "category": "SHIPPING_DELIVERY",
        "description": "Filtrowanie i masowe zlecanie kompletacji (picking) dla dostaw wychodzących.",
        "tables_involved": "LIKP, LIPS",
        "spro_path": "Monitor logistyczny",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL06G",
        "name": "Zbiorcze wydanie towarów (Post Goods Issue Mass Processing)",
        "category": "SHIPPING_DELIVERY",
        "description": "Masowe księgowanie wydania zewnętrznego (Post Goods Issue) dla skompletowanych dostaw wychodzących.",
        "tables_involved": "LIKP, LIPS, MKPF, MSEG",
        "spro_path": "Przetwarzanie masowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL09",
        "name": "Storno wydania towarów (Cancel Goods Issue for Delivery)",
        "category": "SHIPPING_DELIVERY",
        "description": "Anulowanie zaksięgowanego wydania materiału (PGI). Przywraca stan magazynowy i status dostawy. Wymaga uprzedniego storna faktury!",
        "tables_involved": "LIKP, LIPS, MKPF, MSEG, BKPF",
        "spro_path": "Transakcja korygująca",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL10A",
        "name": "Zbiorcze tworzenie dostaw - zlecenia sprzedaży (Sales Orders Due for Delivery)",
        "category": "SHIPPING_DELIVERY",
        "description": "Nowoczesny procesor tworzenia dostaw w tle dla zleceń sprzedaży.",
        "tables_involved": "VBAK, VBAP, LIKP",
        "spro_path": "Przetwarzanie masowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VL71",
        "name": "Druk dokumentów wysyłkowych (Output from Outbound Deliveries)",
        "category": "SHIPPING_DELIVERY",
        "description": "Ponowny wydruk dokumentów dostawy, listów przewozowych (CMR), etykiet paletowych i specyfikacji wysyłkowych.",
        "tables_involved": "NAST, LIKP",
        "spro_path": "Transakcja wydruków",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VT01N",
        "name": "Utworzenie transportu (Create Shipment)",
        "category": "SHIPPING_DELIVERY",
        "description": "Tworzenie dokumentu transportu (LE-TRA) z przypisaniem dostaw, spedytora i trasy przewozu.",
        "tables_involved": "VTTK, VTTP",
        "spro_path": "SPRO -> Logistyka -> Transport",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VT02N",
        "name": "Zmiana transportu (Change Shipment)",
        "category": "SHIPPING_DELIVERY",
        "description": "Zarządzanie etapami transportu: rejestracja odprawy, załadunku, wyjazdu i kalkulacja kosztów frachtu (VI01).",
        "tables_involved": "VTTK, VTTP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 3. FAKTUROWANIE I ROZLICZENIA (BILLING & REVENUE) ---
    {
        "tcode": "VF01",
        "name": "Utworzenie faktury sprzedaży (Create Billing Document)",
        "category": "BILLING_INVOICE",
        "description": "Wystawienie faktury sprzedaży na podstawie dostawy (F2) lub zlecenia. Uruchamia determinację cen i kont VKOA.",
        "tables_involved": "VBRK, VBRP, KONV, PRCD_ELEMENTS",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF02",
        "name": "Zmiana faktury / Zwolnienie do FI (Change Billing Doc & Release to FI)",
        "category": "BILLING_INVOICE",
        "description": "Podgląd i modyfikacja faktury, ręczne zwolnienie do księgowości (zielona flaga) oraz analiza determinacji kont i cen.",
        "tables_involved": "VBRK, VBRP, BKPF, BSEG",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF03",
        "name": "Wyświetlenie faktury sprzedaży (Display Billing Document)",
        "category": "BILLING_INVOICE",
        "description": "Wyświetlenie faktury, powiązanego dokumentu księgowego (FI Document) oraz historii płatności.",
        "tables_involved": "VBRK, VBRP, VBFA, BKPF",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF04",
        "name": "Kolejka fakturowania (Maintain Billing Due List)",
        "category": "BILLING_INVOICE",
        "description": "Kolejka zrealizowanych dostaw i zleceń oczekujących na wystawienie faktury. Zbiorcze fakturowanie.",
        "tables_involved": "VKDFS, VBRK, VBRP",
        "spro_path": "Przetwarzanie masowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF05",
        "name": "Lista faktur sprzedaży (List Billing Documents)",
        "category": "BILLING_INVOICE",
        "description": "Raport wystawionych faktur dla danego płatnika, odbiorcy lub okresu fakturowania.",
        "tables_involved": "VBRK, VBRP",
        "spro_path": "Raportowanie",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF06",
        "name": "Masowe fakturowanie w tle (Billing in Background)",
        "category": "BILLING_INVOICE",
        "description": "Zlecanie zadania w tle (batch job) dla programu RV60SBAT do nocnego fakturowania dokumentów.",
        "tables_involved": "VKDFS, VBRK",
        "spro_path": "Zadania w tle",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF11",
        "name": "Anulowanie faktury sprzedaży (Cancel Billing Document)",
        "category": "BILLING_INVOICE",
        "description": "Wystawienie dokumentu stornującego (rodzaj S1) dla błędnie wystawionej faktury. Automatycznie stornuje zapis w FI.",
        "tables_involved": "VBRK, VBRP, BKPF, BSEG",
        "spro_path": "Transakcja korygująca",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VFX3",
        "name": "Zwalnianie faktur zablokowanych dla księgowości (Release Blocked Invoices)",
        "category": "BILLING_INVOICE",
        "description": "Kluczowa transakcja wsparcia serwisowego SD/FI: lista faktur ze statusem błędu (np. brak VKOA, zablokowane konto). Umożliwia ponowne zaksięgowanie.",
        "tables_involved": "VBRK, VBRP, T030",
        "spro_path": "Narzędzie diagnostyczne SD/FI",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF31",
        "name": "Ponowny wydruk faktur (Output from Billing Documents)",
        "category": "BILLING_INVOICE",
        "description": "Masowe generowanie wydruków, wysyłka e-faktur PDF i komunikatów EDI dla faktur sprzedaży.",
        "tables_involved": "NAST, VBRK",
        "spro_path": "Transakcja wydruków",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VF21",
        "name": "Utworzenie zestawienia faktur (Create Invoice List)",
        "category": "BILLING_INVOICE",
        "description": "Generowanie zestawień faktur (rodzaj LR/LG) dla centralnych płatników w zdefiniowanych interwałach.",
        "tables_involved": "VBRK, VBRP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Zestawienia faktur",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 4. TECHNIKA WARUNKÓW CENOWYCH (PRICING CONDITION TECHNIQUE) ---
    {
        "tcode": "VK11",
        "name": "Utworzenie rekordu warunku cenowego (Create Condition Record)",
        "category": "PRICING_CONDITIONS",
        "description": "Wprowadzanie cen podstawowych (PR00), rabatów (K004, K007), narzutów frachtowych (KF00) i stawek podatkowych.",
        "tables_involved": "KONH, KONP, A001..A999",
        "spro_path": "Menu SAP -> Logistyka -> Sprzedaż i dystrybucja -> Dane podstawowe -> Ceny",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VK12",
        "name": "Zmiana rekordu warunku cenowego (Change Condition Record)",
        "category": "PRICING_CONDITIONS",
        "description": "Modyfikacja kwot, stawek procentowych, walut i okresów ważności rekordów warunków.",
        "tables_involved": "KONH, KONP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VK13",
        "name": "Wyświetlenie rekordu warunku cenowego (Display Condition Record)",
        "category": "PRICING_CONDITIONS",
        "description": "Podgląd obowiązujących stawek cenowych i skal ilościowych/wartościowych.",
        "tables_involved": "KONH, KONP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VK14",
        "name": "Utworzenie rekordu cenowego z referencją (Create Condition with Reference)",
        "category": "PRICING_CONDITIONS",
        "description": "Kopiowanie istniejącego rekordu warunku z możliwością procentowej zmiany wartości.",
        "tables_involved": "KONH, KONP",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VK31",
        "name": "Masowe utrzymanie cen (Condition Maintenance Mass)",
        "category": "PRICING_CONDITIONS",
        "description": "Szybka aktualizacja cenników z podziałem na grupy klientów i grupy materiałowe.",
        "tables_involved": "KONH, KONP",
        "spro_path": "Utrzymanie masowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/03",
        "name": "Utworzenie tabeli warunków cenowych (Create Condition Table)",
        "category": "PRICING_CONDITIONS",
        "description": "Definiowanie klucza tabeli kondycyjnej (np. Tabela 501: VKORG + VTWEG + KUNNR + MATNR). Tworzy tabelę fizyczną A501.",
        "tables_involved": "T681, T681T",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Sterowanie wyceną -> Definiuj tabele warunków",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/04",
        "name": "Zmiana tabeli warunków cenowych (Change Condition Table)",
        "category": "PRICING_CONDITIONS",
        "description": "Modyfikacja pól klucza w tabeli warunków.",
        "tables_involved": "T681",
        "spro_path": "SPRO -> Wycena",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/05",
        "name": "Wyświetlenie tabeli warunków cenowych (Display Condition Table)",
        "category": "PRICING_CONDITIONS",
        "description": "Podgląd struktury pól tabeli warunków.",
        "tables_involved": "T681",
        "spro_path": "SPRO -> Wycena",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/06",
        "name": "Definicja rodzajów warunków cenowych (Define Condition Types)",
        "category": "PRICING_CONDITIONS",
        "description": "Konfiguracja rodzajów warunków (KSCHL, np. PR00, ZPR1): klasa warunku, reguła kalkulacji, sekwencja dostępu, modyfikowalność ręczna.",
        "tables_involved": "T685, T685T",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Rodzaje warunków",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/07",
        "name": "Definicja sekwencji dostępu (Define Access Sequences)",
        "category": "PRICING_CONDITIONS",
        "description": "Ustalanie hierarchii przeszukiwania tabel warunków dla danego warunku cenowego (od najbardziej szczegółowej do ogólnej).",
        "tables_involved": "T682, T682T, T682I",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Sekwencje dostępu",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "V/08",
        "name": "Definicja schematów kalkulacji (Define Pricing Procedures)",
        "category": "PRICING_CONDITIONS",
        "description": "Kluczowa konfiguracja wyceny SD: schemat kalkulacji (KALSM, np. RVAA01), kolejność kroków, bazy obliczeń, klucze kont (ERL/ERS) i wymagania (Requirements).",
        "tables_involved": "T683, T683S, T683T",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Schematy kalkulacji",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVKK",
        "name": "Przypisanie schematu kalkulacji (Pricing Procedure Determination)",
        "category": "PRICING_CONDITIONS",
        "description": "Reguła wyznaczania schematu cenowego: Obszar sprzedaży (VKORG/VTWEG/SPART) + Schemat klienta (KALKS) + Schemat dokumentu (KALVG) -> Schemat kalkulacji (KALSM).",
        "tables_involved": "T683V",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Ustalanie schematu kalkulacji",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 5. USTALANIE KONT I INTEGRACJA FI (ACCOUNT DETERMINATION & FI) ---
    {
        "tcode": "VKOA",
        "name": "Ustalanie kont przychodów (Revenue Account Determination)",
        "category": "ACCOUNT_DETERMINATION",
        "description": "Główna konfiguracja alokacji przychodów SD->FI. Tabele 001-005, Plan kont (KTOPL), Jednostka sprzedaży, Grupa rozliczeniowa klienta/materiału -> Konto KG.",
        "tables_involved": "T030, C001, C002, C003, C004, C005",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Ustalanie kont/Koszty -> Ustalanie kont przychodów",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OV34",
        "name": "Przypisanie kont dla rabatów retrospektywnych (Rebate Account Determination)",
        "category": "ACCOUNT_DETERMINATION",
        "description": "Konfiguracja kont rozliczenia rezerw i wypłat porozumień rabatowych.",
        "tables_involved": "T030",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Rozliczenia końcowe -> Porozumienia rabatowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOFM",
        "name": "Rutyny i formuły ABAP w SD (Requirements & Formulas)",
        "category": "ACCOUNT_DETERMINATION",
        "description": "Zarządzanie formułami wyceny (podstawa warunku, wartość warunku), warunkami określania pozycji i wymogami fakturowania.",
        "tables_involved": "TFRM, TFRMT",
        "spro_path": "SPRO -> Narzędzie techniczne ABAP / SD",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 6. SPRO: RODZAJE DOKUMENTÓW I KATEGORIE POZYCJI (DOCUMENT CUSTOMIZING) ---
    {
        "tcode": "VOV8",
        "name": "Definicja rodzajów zleceń sprzedaży (Define Sales Document Types)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Konfiguracja AUART (np. TA, OR, ZOR1): numeracja, profil dostawy, schemat fakturowania, profil sprawdzania kredytu i blokady.",
        "tables_involved": "TVAK, TVAKT",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży -> Nagłówek dokumentu sprzedaży",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOV7",
        "name": "Definicja kategorii pozycji (Define Item Categories)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Parametryzacja kategorii pozycji (PSTYV, np. TAN, ZTAN, REN): kontrola fakturowania, ATP, istotność dla wyceny, dopuszczalność stanu zero.",
        "tables_involved": "TVAP, TVAPT",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży -> Pozycja dokumentu sprzedaży",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOV4",
        "name": "Przypisanie kategorii pozycji (Assign Item Categories)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Macierz wyznaczania pozycji: Rodzaj zlecenia (AUART) + Grupa kat. pozycji (MTPOS) + Zastosowanie + Kategoria nadrzędna -> Domyślna kategoria pozycji (PSTYV).",
        "tables_involved": "T184",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży -> Przypisanie kategorii pozycji",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOV6",
        "name": "Definicja kategorii linii harmonogramu (Define Schedule Line Categories)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Konfiguracja linii harmonogramu (ETTYP, np. CP, CN): ruch materiałowy, istotność dla planowania zapotrzebowań (MRP) i kontrola dostępności.",
        "tables_involved": "TVEP, TVEPT",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Linie harmonogramu",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOV5",
        "name": "Przypisanie linii harmonogramu (Assign Schedule Line Categories)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Ustalanie linii harmonogramu w zależności od kategorii pozycji i typu planowania MRP.",
        "tables_involved": "TVEPA",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Przypisanie linii harmonogramu",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VOFA",
        "name": "Definicja rodzajów faktur (Define Billing Types)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Konfiguracja rodzajów faktur (FKART, np. F2, ZF2, G2, RE): rodzaj dokumentu księgowego FI, reguła anulowania, blokady księgowania.",
        "tables_involved": "TVFK, TVFKT",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Dokumenty fakturowania",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVLK",
        "name": "Definicja rodzajów dostaw (Define Delivery Types)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Konfiguracja rodzajów dostaw wychodzących (LFART, np. LF, ZLF, LR dla zwrotów): reguły numeracji, profil kompletacji i trasy.",
        "tables_involved": "TVLK, TVLKT",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Dostawy -> Rodzaje dostaw",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVLP",
        "name": "Definicja pozycji dostawy (Define Delivery Item Categories)",
        "category": "CUSTOMIZING_SPRO",
        "description": "Sterowanie pozycjami dostawy (np. czy pozycja wymaga kompletacji, pakowania, czy generuje PGI).",
        "tables_involved": "TVLP, TVLPT",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Dostawy -> Pozycje dostawy",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 7. STEROWANIE KOPIOWANIEM (COPY CONTROL) ---
    {
        "tcode": "VTAA",
        "name": "Sterowanie kopiowaniem: Zlecenie do Zlecenia (Copy Control: Order to Order)",
        "category": "COPY_CONTROL",
        "description": "Reguły przepływu danych między zleceniami (np. z oferty QT do zlecenia TA lub ze zlecenia do zlecenia zwrotu RE).",
        "tables_involved": "TVCPA, TVCPAP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Sterowanie kopiowaniem",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VTLA",
        "name": "Sterowanie kopiowaniem: Zlecenie do Dostawy (Copy Control: Order to Delivery)",
        "category": "COPY_CONTROL",
        "description": "Definiowanie przenoszenia danych ze zlecenia sprzedaży do dostawy wychodzącej (np. TA -> LF).",
        "tables_involved": "TVCPL, TVCPLP",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Kopiowanie danych",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VTFL",
        "name": "Sterowanie kopiowaniem: Dostawa do Faktury (Copy Control: Delivery to Billing)",
        "category": "COPY_CONTROL",
        "description": "Kluczowe sterowanie fakturowaniem dostaw (LF -> F2): wyznaczanie cen na nowo, podział faktur (Billing Split) i statusy.",
        "tables_involved": "TVCPF, TVCPFP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Sterowanie kopiowaniem",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VTFA",
        "name": "Sterowanie kopiowaniem: Zlecenie do Faktury (Copy Control: Order to Billing)",
        "category": "COPY_CONTROL",
        "description": "Fakturowanie bezpośrednio na podstawie zlecenia sprzedaży (np. usługi BV/CS, zlecenia zafakturowane z góry).",
        "tables_involved": "TVCPF, TVCPFP",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Sterowanie kopiowaniem",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VTFF",
        "name": "Sterowanie kopiowaniem: Faktura do Faktury (Copy Control: Billing to Billing)",
        "category": "COPY_CONTROL",
        "description": "Kopiowanie faktury do noty kredytowej/debetowej lub stornującej.",
        "tables_involved": "TVCPF, TVCPFP",
        "spro_path": "SPRO -> Fakturowanie",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 8. ZARZĄDZANIE KREDYTEM (CREDIT MANAGEMENT) ---
    {
        "tcode": "OVA8",
        "name": "Automatyczna kontrola kredytowa (Automatic Credit Control)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Konfiguracja reguł blokad kredytowych: Obszar kontroli kredytowej (KKBER) + Grupa ryzyka klienta + Grupa kredytowa dokumentu -> Reakcja (ostrzeżenie / blokada).",
        "tables_involved": "T014, T014T, T691F",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Zarządzanie kredytem",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VKM1",
        "name": "Zablokowane dokumenty sprzedaży SD (Blocked SD Documents)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Zestawienie dokumentów zatrzymanych przez kontrolę kredytową z możliwością zwolnienia przez analityka ryzyka.",
        "tables_involved": "VBAK, VBUK",
        "spro_path": "Zarządzanie ryzykiem",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VKM3",
        "name": "Zwalnianie zleceń sprzedaży z blokadą kredytową (Release Sales Orders)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Bezpośrednie zwalnianie pojedynczego zlecenia sprzedaży z blokady limitu kupieckiego.",
        "tables_involved": "VBAK, VBUK",
        "spro_path": "Transakcja operacyjna",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VKM4",
        "name": "Zbiorcze zwalnianie dokumentów SD (Release SD Documents Mass)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Zaawansowany pulpit analityka kredytowego do masowego zwalniania zleceń i dostaw.",
        "tables_involved": "VBAK, LIKP",
        "spro_path": "Pulpit analityka",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "FD32",
        "name": "Karta zarządzania kredytem klienta ECC (Credit Management Customer Master)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Utrzymanie limitu kredytowego, klasy ryzyka i wskaźników płatności kontrahenta (w ECC 6.0).",
        "tables_involved": "KNKK, KNB1",
        "spro_path": "Dane podstawowe",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "UKM_BP",
        "name": "Zarządzanie kredytem Partnera Biznesowego S/4HANA (FSCM Credit Management)",
        "category": "CREDIT_MANAGEMENT",
        "description": "Wycena scoringowa, reguły limitów i decyzje kredytowe w standardzie S/4HANA FSCM Credit Management.",
        "tables_involved": "UKMBP_CMS, BUT000",
        "spro_path": "S/4HANA FSCM Credit Management",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 9. FUNKCJE PODSTAWOWE, OKREŚLANIE TRAS I PUNKTÓW WYSYŁKI ---
    {
        "tcode": "OVL2",
        "name": "Określanie punktu wysyłki (Shipping Point Determination)",
        "category": "BASIC_FUNCTIONS",
        "description": "Macierz wyznaczania punktu wysyłki (VSTEL): Warunek wysyłki odbiorcy (VSBED) + Grupa załadunku materiału (LADGR) + Zakład dostarczający (WERKS) -> Punkt wysyłki.",
        "tables_involved": "TVSTZ",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Podstawowe funkcje wysyłki -> Wyznaczanie punktu wysyłki",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVRO",
        "name": "Definicja tras przewozu (Define Routes)",
        "category": "BASIC_FUNCTIONS",
        "description": "Konfiguracja tras transportowych (ROUTE), etapów i czasów tranzytu.",
        "tables_involved": "TVRO, TVROT",
        "spro_path": "SPRO -> Logistyka -> Transport -> Trasy",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVRP",
        "name": "Ustalanie tras (Route Determination)",
        "category": "BASIC_FUNCTIONS",
        "description": "Automatyczne wyznaczanie trasy: Kraj/Strefa wyjazdu + Warunek wysyłki + Grupa transportowa + Kraj/Strefa odbiorcy -> Trasa.",
        "tables_involved": "TVEG",
        "spro_path": "SPRO -> Logistyka -> Wysyłka -> Podstawowe funkcje wysyłki -> Wyznaczanie tras",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "OVZ9",
        "name": "Reguły kontroli dostępności ATP (Define ATP Checking Rule)",
        "category": "BASIC_FUNCTIONS",
        "description": "Konfiguracja zakresu sprawdzania dostępności zapasów (zapas bezpieczny, zamówienia w toku, zapotrzebowania produkcyjne).",
        "tables_involved": "T441V",
        "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Kontrola dostępności i przekazywanie zapotrzebowań",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VB01",
        "name": "Utworzenie listowania / wykluczenia materiałów (Create Listing/Exclusion)",
        "category": "BASIC_FUNCTIONS",
        "description": "Konfiguracja ograniczeń asortymentowych: lista materiałów dozwolonych do sprzedaży dla klienta lub lista towarów zablokowanych.",
        "tables_involved": "KOND, KONDD",
        "spro_path": "Menu SAP -> Logistyka -> Sprzedaż i dystrybucja -> Dane podstawowe -> Produkty",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VB11",
        "name": "Utworzenie podstawienia materiału (Create Material Determination)",
        "category": "BASIC_FUNCTIONS",
        "description": "Automatyczne podstawianie indeksu (np. stary wycofany produkt zastępowany nowym indeksem z zachowaniem kodu kreskowego EAN).",
        "tables_involved": "KONH, KONP",
        "spro_path": "Menu SAP -> Logistyka -> Sprzedaż i dystrybucja -> Dane podstawowe -> Podstawienie",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "VBN1",
        "name": "Utworzenie reguły towaru darmowego (Create Free Goods)",
        "category": "BASIC_FUNCTIONS",
        "description": "Definicja gratisów handlowych (np. kup 10 sztuk -> otrzymaj 1 gratis wliczony lub osobną pozycję darmową).",
        "tables_involved": "KONDN",
        "spro_path": "Menu SAP -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Towary darmowe",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 10. RAPORTY I SYSTEM INFORMACYJNY SD (SIS & REPORTING) ---
    {
        "tcode": "MCTA",
        "name": "SIS: Analiza klientów (Customer Sales Analysis)",
        "category": "REPORTING_SIS",
        "description": "Standardowa analiza wielowymiarowa przychodów, ilości i marż wg kontrahentów.",
        "tables_involved": "S001, S002, S003",
        "spro_path": "Raporty SIS",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "MCTC",
        "name": "SIS: Analiza materiałowa (Material Sales Analysis)",
        "category": "REPORTING_SIS",
        "description": "Zestawienie sprzedaży wg grup towarowych, wyrobów i kanałów dystrybucji.",
        "tables_involved": "S001, S004",
        "spro_path": "Raporty SIS",
        "is_custom_z": False,
        "company_id": None
    },
    {
        "tcode": "MCSI",
        "name": "SIS: Otwarty pulpit analityczny (Open Sales Analysis)",
        "category": "REPORTING_SIS",
        "description": "Elastyczny pulpit raportowy struktur infostruktur SD.",
        "tables_involved": "S001..S006",
        "spro_path": "Raporty SIS",
        "is_custom_z": False,
        "company_id": None
    },

    # --- 11. KODY Z* SPECYFICZNE DLA KLIENTÓW (MULTI-COMPANY EXTENSIONS) ---
    {
        "tcode": "ZOR1_FAST",
        "name": "Ekspresowe zlecenia sprzedaży krajowej (Klient A Custom)",
        "category": "CUSTOM_Z_CODES",
        "description": "Customowa transakcja wsadowego wprowadzania ekspresowych zleceń ZOR1 z automatycznym ominięciem bufora ATP.",
        "tables_involved": "VBAK, ZSD_EXP_LOG",
        "spro_path": "Klient A Rozszerzenie Z*",
        "is_custom_z": True,
        "company_id": "CLIENT_A"
    },
    {
        "tcode": "ZSD_AUTO_INV",
        "name": "Automatyczne fakturowanie nocne bez weryfikacji VAT (Klient A Custom)",
        "category": "CUSTOM_Z_CODES",
        "description": "Dedykowany program fakturowania dostaw z automatycznym rozliczeniem VKOA dla rynku motoryzacyjnego.",
        "tables_involved": "VBRK, VBRP, ZSD_INV_PARAMS",
        "spro_path": "Klient A Rozszerzenie Z*",
        "is_custom_z": True,
        "company_id": "CLIENT_A"
    },
    {
        "tcode": "ZEXP_CHECK",
        "name": "Weryfikacja deklaracji Intrastat dla dostaw nordyckich (Klient B Custom)",
        "category": "CUSTOM_Z_CODES",
        "description": "Specyficzny moduł walidacji transgranicznej dla zamówień ZEXP na rynku skandynawskim.",
        "tables_involved": "VBAK, LIKP, ZSE_INTRASTAT",
        "spro_path": "Klient B Rozszerzenie Z*",
        "is_custom_z": True,
        "company_id": "CLIENT_B"
    },
    {
        "tcode": "ZPR1_MAINT",
        "name": "Utrzymanie nordyckiej matrycy marż ZPR1 (Klient B Custom)",
        "category": "CUSTOM_Z_CODES",
        "description": "Interaktywny kokpit wyceny dla warunku ZPR1 z przelicznikiem walut SEK/EUR.",
        "tables_involved": "KONH, KONP, ZSE_PRICING",
        "spro_path": "Klient B Rozszerzenie Z*",
        "is_custom_z": True,
        "company_id": "CLIENT_B"
    }
]
