# -*- coding: utf-8 -*-
"""
Serwis zaawansowanej diagnostyki błędów modułu SAP SD (Sales and Distribution).
Działa jako wirtualny Senior Konsultant i Architekt Rozwiązań SAP O2C.
Dostarcza wyczerpujące ekspertyzy, analizy przyczyn, wielowariantowe rozwiązania,
rekomendacje architektoniczne oraz precyzyjne ścieżki transakcyjne SPRO.
"""
import re
from typing import Optional, Dict, Any, List

class ErrorDiagnosisService:
    """
    Baza wiedzy i silnik ekspercki Senior Konsultanta SAP SD.
    Oferuje pełną, pogłębioną analizę techniczną i biznesową błędów O2C.
    """

    SD_ERRORS_CATALOG = {
        "VF067": {
            "code": "VF067",
            "title": "Konto przychodów nie zostało ustalone (Account determination error)",
            "category": "Billing & FI Integration (VKOA)",
            "keywords": ["vf067", "vkoa", "konto przychod", "brak konta", "nie ustalono konta", "account could not be determined", "faktura nie ksieg", "zablokowana faktura"],
            "summary": "System SAP zablokował księgowanie faktury w module FI z powodu braku przypisania konta księgi głównej w tabeli VKOA.",
            "business_impact": "Faktura nie generuje dokumentu księgowego (status VBRK-RFBSK = 'B'). Blokuje to rozrachunki z odbiorcą, uniemożliwia wysyłkę e-faktury (KSeF / EDI) oraz powoduje rozbieżność między raportami sprzedaży a księgą główną.",
            "technical_mechanism": "W trakcie tworzenia/zwalniania faktury (VF01/VF02) wywoływana jest procedura KOFI00 dla aplikacji 'V' i rodzaju warunku 'KOFI'. System sekwencyjnie przeszukuje tabele kondycyjne (001: Klient/Materiał, 002: Klient, 003: Materiał, 005: Organizacja sprzedaży, 004: Ogólna). Jeśli w żadnej tabeli nie ma aktywnego rekordu dla danego planu kont (KTOPL) i klucza konta (np. ERL, ERS), transakcja zostaje przerwana z błędem VF067.",
            "solution_variants": [
                {
                    "name": "Wariant A (Rekomendowany - Best Practice SPRO)",
                    "desc": "Uzupełnienie brakującej reguły w tabeli VKOA na poziomie organizacji sprzedaży lub grup rozliczeniowych:",
                    "steps": [
                        "Uruchom VF02 -> wpisz numer faktury -> Środowisko -> Analiza -> Ustalanie kont -> Konta przychodów (sprawdź, który klucz, np. ERL, ma czerwony status).",
                        "Uruchom transakcję VKOA i wybierz odpowiednią tabelę (zazwyczaj Tabelę 001 dla specyficznych grup lub Tabelę 005 dla ogólnych przychodów organizacji).",
                        "Dodaj wpis: Plan kont + Organizacja sprzedaży + Klucz konta (ERL) -> Wskaż właściwe konto księgi głównej.",
                        "Zwolnij fakturę do księgowania w VFX3 (zielona flaga)."
                    ]
                },
                {
                    "name": "Wariant B (Szybkie obejście doraźne / Krytyczny koniec miesiąca)",
                    "desc": "Jeśli faktura musi zostać natychmiast zaksięgowana w FI, a nie znasz jeszcze docelowej matrycy kont analitycznych:",
                    "steps": [
                        "W transakcji VKOA wejdź do Tabeli 004 (Ustalanie ogólne).",
                        "Wprowadź wpis dla samego Planu kont + Klucza konta (ERL) z domyślnym kontem przychodów ze sprzedaży.",
                        "Zwolnij fakturę w VF02. Wszystkie kolejne dokumenty z tym kluczem skorzystają z wpisu fallback, zapobiegając blokadom."
                    ]
                },
                {
                    "name": "Wariant C (Korekta danych podstawowych klienta lub materiału)",
                    "desc": "Gdy błąd wynika z braku grup rozliczeniowych w kartotekach:",
                    "steps": [
                        "Sprawdź w MM02 (Sprzedaż: Org. sprzedaży 2) pole 'Grupa rozliczenia materiału' (KTGRM).",
                        "Sprawdź w BP / XD03 (segment Sprzedaż -> Fakturowanie) pole 'Grupa rozliczenia klienta' (KTGRD).",
                        "Jeśli grupa była pusta w zleceniu, po uzupełnieniu kartoteki zaktualizuj wycenę w VF02 lub anuluj fakturę w VF11 i wystaw ponownie."
                    ]
                }
            ],
            "tcodes": ["VKOA", "VFX3", "VF02", "MM02", "BP", "FS00"],
            "tables": ["VKOA", "VBRK", "VBRP", "KNVV", "MVKE"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Ustalanie kont/kalkulacja -> Ustalanie kont przychodów -> Zdefiniuj przyporządkowanie kont przychodów (VKOA)",
            "pitfalls_and_secondary": [
                "Po odblokowaniu konta przychodów SAP natychmiast waliduje konta podatkowe – jeśli w OB40 brak konta VAT, pojawi się błąd FF704.",
                "Jeśli faktura ma datę z ubiegłego miesiąca, upewnij się, że okres księgowy FI jest otwarty w OB52 (błąd F5151).",
                "Upewnij się, że konto KG wprowadzone w VKOA istnieje w transakcji FS00 dla danej jednostki BUKRS."
            ],
            "quick_fix": True,
            "quick_fix_type": "vkoa"
        },
        "FF704": {
            "code": "FF704",
            "title": "Brak konta podatkowego w procedurze podatkowej (Tax account determination error)",
            "category": "Taxes & FI Integration (OB40)",
            "keywords": ["ff704", "podatkow", "konto podatk", "mwst", "mws", "vat", "tax account"],
            "summary": "Klucz transakcji podatkowej ze schematu kalkulacyjnego nie ma zdefiniowanego konta księgowego w konfiguracji finansowej FI.",
            "business_impact": "Faktura sprzedażowa nie może zostać zaksięgowana w rejestrze VAT ani w księdze głównej, co uniemożliwia prawidłowe rozliczenie deklaracji podatkowej (JPK_V7 / VAT return).",
            "technical_mechanism": "Warunek podatkowy ze schematu kalkulacyjnego SD (np. MWST) generuje wiersz podatku przypisany do klucza operacji podatkowej (zazwyczaj MWS dla podatku należnego ze schematu TAXPL/TAXDE). Moduł FI podczas generowania dokumentu księgowego odpytuje tabelę T030K dla kombinacji Plan kont + Operacja MWS. Brak wpisu blokuje generowanie dokumentu BKPF.",
            "solution_variants": [
                {
                    "name": "Wariant A (Konfiguracja reguły w OB40 - Standard)",
                    "desc": "Zdefiniowanie konta rozliczenia podatku VAT należnego w konfiguracji finansowej:",
                    "steps": [
                        "Uruchom transakcję OB40 i wybierz operację 'MWS' (Podatek należny / Output tax).",
                        "Podaj aktywny plan kont firmy.",
                        "Wprowadź konto księgi głównej VAT należnego (np. 221-xxx) i zapisz na zleceniu transportowym.",
                        "Wróć do VFX3 i zwolnij zablokowaną fakturę."
                    ]
                },
                {
                    "name": "Wariant B (Weryfikacja wskaźnika podatkowego w FTXP)",
                    "desc": "Jeśli konto w OB40 istnieje, ale wskaźnik podatku ma niepoprawną definicję:",
                    "steps": [
                        "Uruchom FTXP -> Kraj (np. PL) -> Wskaźnik podatku z faktury (np. 23%).",
                        "Sprawdź, czy wiersz operacji MWS zawiera stawkę procentową i czy jest aktywny w bieżącym roku obrachunkowym.",
                        "Upewnij się w FS00, czy konto KG ma poprawną kategorię podatku (pole MWSKZ = '>' lub '*')."
                    ]
                }
            ],
            "tcodes": ["OB40", "FTXP", "VF02", "VFX3", "FS00"],
            "tables": ["T030K", "BSEG", "VBRK"],
            "spro_path": "SPRO -> Rachunkowość finansowa -> Ustawienia podstawowe -> Podatek od towarów i usług -> Księgowanie -> Zdefiniuj konta podatkowe (OB40)",
            "pitfalls_and_secondary": [
                "Upewnij się, że wskaźnik podatku na fakturze nie jest zwolniony z VAT bez wymaganej prawem podstawy prawnej.",
                "Częstym błędem jest brak konta dla transakcji WNT (nabycia wewnątrzwspólnotowe) lub transakcji trójstronnych."
            ],
            "quick_fix": False
        },
        "OB52": {
            "code": "OB52",
            "title": "Okres obrachunkowy nie jest otwarty dla księgowania w FI (Komunikat F5151)",
            "category": "FI Posting Periods (OB52)",
            "keywords": ["ob52", "f5151", "zamkniety okres", "zamknięty okres", "okres obrachunkowy", "posting period closed", "okres zamkniety"],
            "summary": "Data księgowania dokumentu sprzedaży przypada na zamknięty okres obrachunkowy w jednostce gospodarczej.",
            "business_impact": "Całkowita blokada księgowania faktur i wydań towarów przypadających na dany miesiąc.",
            "technical_mechanism": "System weryfikuje tabelę T001B dla wariantu okresów obrachunkowych przypisanego do jednostki gospodarczej BUKRS. Jeśli data księgowania przypada na okres spoza zakresu Od-Do dla danego rodzaju konta ('+' lub 'D'/'S'), transakcja zwraca komunikat F5151.",
            "solution_variants": [
                {
                    "name": "Wariant A (Otwarcie okresu w OB52 przez zespół Księgowości)",
                    "desc": "Zwiększenie zakresu otwartych okresów w konfiguracji FI:",
                    "steps": [
                        "Uruchom transakcję OB52 dla wariantu okresów aktywnej firmy.",
                        "W kolumnach 'Od okresu 1' i 'Do okresu 1' ustaw bieżący miesiąc i rok.",
                        "Upewnij się, że okres jest otwarty zarówno dla rodzaju konta '+' (ogólny), jak i 'D' (Odbiorcy) oraz 'S' (Konta KG).",
                        "Zapisz i ponów księgowanie w VFX3."
                    ]
                },
                {
                    "name": "Wariant B (Zmiana daty fakturowania na bieżący okres)",
                    "desc": "Jeśli okres poprzedni został bezwzględnie zamknięty bilansowo i księgowość nie wyraża zgody na jego otwarcie:",
                    "steps": [
                        "Otwórz fakturę w VF02 -> przejdź do nagłówka (Dane nagłówka).",
                        "Zmień 'Datę księgowania' (Posting Date) oraz 'Datę fakturowania' na bieżący, otwarty miesiąc.",
                        "Zapisz dokument i zwolnij do FI."
                    ]
                }
            ],
            "tcodes": ["OB52", "VF02", "VFX3", "MMPV", "MMRV"],
            "tables": ["T001B", "T001", "BKPF"],
            "spro_path": "SPRO -> Rachunkowość finansowa -> Ustawienia podstawowe -> Okresy obrachunkowe -> Otwórz i zamknij okresy obrachunkowe (OB52)",
            "pitfalls_and_secondary": [
                "Jeśli błąd dotyczy wydania towaru (PGI w VL02N), konieczne jest również przesunięcie okresu materiałowego MM w transakcji MMPV.",
                "Zawsze upewnij się, że data kursu walutowego odpowiada nowej dacie fakturowania."
            ],
            "quick_fix": False
        },
        "VF024": {
            "code": "VF024",
            "title": "Dokument fakturowania jest zablokowany przez innego użytkownika lub proces",
            "category": "System Locks & Concurrency (SM12)",
            "keywords": ["vf024", "zablokowany", "lock table", "jest przetwarzany", "document locked"],
            "summary": "Faktura znajduje się w centralnej tabeli blokad serwera aplikacji SAP i nie może być edytowana ani księgowana.",
            "business_impact": "Przestój operacyjny – konsultant ani zadanie wsadowe w tle nie może zamknąć procesu fakturowania.",
            "technical_mechanism": "Serwer Enqueue SAP umieszcza w tabeli blokad rekord dla tabeli VBRK z kluczem dokumentu, aby zapobiec jednoczesnej modyfikacji przez dwie sesje. Blokada może pozostać aktywna po zerwaniu połączenia GUI lub awarii zadania w tle.",
            "solution_variants": [
                {
                    "name": "Wariant A (Usunięcie osieroconej blokady w SM12)",
                    "desc": "Standardowa procedura odblokowania obiektu bazy:",
                    "steps": [
                        "Uruchom transakcję SM12 w nowym oknie.",
                        "W polu 'Nazwa tabeli' wpisz VBRK i kliknij 'Wyświetl'.",
                        "Sprawdź czas utworzenia blokady – jeśli trwa od dłuższego czasu i użytkownik nie pracuje na dokumencie, zaznacz wpis i kliknij 'Usuń blokadę' (Kosz).",
                        "Wróć do VF02 i przeprowadź fakturowanie."
                    ]
                }
            ],
            "tcodes": ["SM12", "SM04", "VF02", "VFX3"],
            "tables": ["VBRK", "VBSK"],
            "spro_path": "N/A (Operacja administracyjna Basis/SD)",
            "pitfalls_and_secondary": [
                "Nigdy nie usuwaj blokady, jeśli inny użytkownik faktycznie edytuje fakturę – grozi to utratą spójności danych."
            ],
            "quick_fix": False
        },
        "V1382": {
            "code": "V1382",
            "title": "Kategoria pozycji nie jest zdefiniowana dla kombinacji AUART / Grupa kat. / Zastosowanie",
            "category": "Sales Document Processing (VOV4)",
            "keywords": ["v1382", "kategoria pozycji", "item category", "nie jest zdefiniowana", "vov4", "vov7"],
            "summary": "System nie potrafi przypisać domyślnej kategorii pozycji (np. TAN, ZTAN) dla wprowadzonego materiału w danym rodzaju zlecenia sprzedaży.",
            "business_impact": "Brak możliwości wprowadzenia pozycji materiałowej do zlecenia w VA01/VA02.",
            "technical_mechanism": "Podczas wprowadzania indeksu do zlecenia system odczytuje grupę kategorii pozycji z kartoteki materiału (MARA/MVKE pole MTPOS) i odpytuje tabelę TVAPZ na podstawie kombinacji: Rodzaj zlecenia (AUART) + Grupa kat. pozycji (MTPOS) + Zastosowanie pozycji + Kategoria pozycji nadrzędnej. Brak wpisu wywołuje twardy błąd V1382.",
            "solution_variants": [
                {
                    "name": "Wariant A (Konfiguracja tabeli przyporządkowania w VOV4 - Standard)",
                    "desc": "Dodanie poprawnej kombinacji do konfiguracji SD:",
                    "steps": [
                        "Sprawdź w MM02 na wglądzie 'Sprzedaż: Org. sprzedaży 2' pole MTPOS (np. NORM dla towaru, DIEN dla usługi, BANS dla zamówienia obcego).",
                        "Uruchom transakcję VOV4 -> kliknij 'Nowe wpisy'.",
                        "Wprowadź: Rodzaj zlecenia AUART (np. TA lub ZOR1) + Grupa MTPOS -> Przypisz domyślną kategorię PSTYV (np. TAN) oraz kategorie dopuszczalne (np. TANN dla gratisu).",
                        "Zapisz na zleceniu transportowym i utwórz zlecenie w VA01."
                    ]
                },
                {
                    "name": "Wariant B (Korekta grupy w kartotece materiałowej)",
                    "desc": "Jeśli błąd wynika z błędnego zaklasyfikowania materiału podczas migracji:",
                    "steps": [
                        "W transakcji MM02 zmień grupę pozycji na standardową 'NORM'.",
                        "Zapisz i spróbuj ponownie dodać pozycję w VA01."
                    ]
                }
            ],
            "tcodes": ["VOV4", "VOV7", "MM02", "VA01", "VA02"],
            "tables": ["T184", "TVAP", "MARA", "MVKE"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Pozycje dokumentu sprzedaży -> Przyporządkuj kategorie pozycji (VOV4)",
            "pitfalls_and_secondary": [
                "Upewnij się w VOV7, że nowa kategoria pozycji ma właściwie ustawioną flagę 'Trafność dla dostawy' i 'Kontrolę wyceny'.",
                "Dla pozycji zlecenia z nową kategorią upewnij się, że w schemacie wyceny wyznaczy się cena PR00 (błąd V1408)."
            ],
            "quick_fix": False
        },
        "V1003": {
            "code": "V1003",
            "title": "Partner nie istnieje w danym obszarze sprzedaży (Brak roli partnera AG/WE/RE/RG)",
            "category": "Partner Determination & Master Data",
            "keywords": ["v1003", "partner nie istnieje", "partner does not exist", "brak roli partnera", "zleceniodawca nie istnieje", "odbiorca materiału nie istnieje"],
            "summary": "Podany w zleceniu sprzedaży numer klienta nie został rozszerzony o segment danych sprzedaży dla danej organizacji, kanału i działu.",
            "business_impact": "Brak możliwości założenia zlecenia sprzedaży na danego kontrahenta.",
            "technical_mechanism": "System sprawdza tabelę KNVV dla kombinacji KUNNR + VKORG + VTWEG + SPART. Jeśli rekord nie istnieje lub brakuje powiązań funkcji partnera w tabeli KNVP, tworzenie dokumentu sprzedaży zostaje zablokowane.",
            "solution_variants": [
                {
                    "name": "Wariant A (Rozszerzenie Partnera Biznesowego w BP - S/4HANA)",
                    "desc": "Uzupełnienie segmentu obszaru sprzedaży w kartotece kontrahenta:",
                    "steps": [
                        "Uruchom transakcję BP i wybierz rolę FLCU01 (Klient w module Sprzedaż).",
                        "Kliknij przycisk 'Dane obszaru sprzedaży' w górnym menu.",
                        "Wprowadź kombinację VKORG/VTWEG/SPART aktywnego profilu klienta.",
                        "Uzupełnij wymagane parametry handlowe: Waluta, Grupa cenowa, Schemat kalkulacyjny klienta, Warunki płatności.",
                        "Na zakładce 'Funkcje partnera' potwierdź obecność ról: SP (Zleceniodawca), BP (Płatnik), PY (Odbiorca faktury), SH (Odbiorca dostawy).",
                        "Zapisz i utwórz zlecenie w VA01."
                    ]
                }
            ],
            "tcodes": ["BP", "VOPAN", "VD01", "XD01", "VA01"],
            "tables": ["BUT000", "KNVV", "KNVP", "TPAER"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Ustalanie partnerów -> Skonfiguruj ustalanie partnerów (VOPAN)",
            "pitfalls_and_secondary": [
                "Upewnij się, że klient nie ma aktywnego znacznika blokady zamówień w tabeli KNA1/KNVV."
            ],
            "quick_fix": False
        },
        "V1408": {
            "code": "V1408",
            "title": "Brak obowiązkowego warunku cenowego (np. PR00) w schemacie kalkulacji",
            "category": "Pricing & Conditions (V/08, VK11)",
            "keywords": ["v1408", "v1053", "brak ceny", "cena obowiazkowa", "mandatory condition", "brak warunku pr00", "pr00", "pricing error"],
            "summary": "W pozycji zlecenia sprzedaży brakuje wartości dla warunku cenowego oznaczonego w schemacie kalkulacyjnym jako obowiązkowy.",
            "business_impact": "Zlecenie otrzymuje status niekompletnego i ma zablokowaną dostawę oraz fakturowanie.",
            "technical_mechanism": "W trakcie wyceny SD (procedura PRICING) system analizuje schemat kalkulacyjny (tabela T683S). Jeśli którykolwiek warunek oznaczony flagą 'Obowiązkowy' (KOBLI = 'X') nie odnajdzie rekordu w tabelach kondycyjnych Axxx, zlecenie zgłasza błąd niekompletności.",
            "solution_variants": [
                {
                    "name": "Wariant A (Utrzymanie rekordu ceny w VK11 - Standard)",
                    "desc": "Dodanie ważnego rekordu ceny bazowej dla materiału:",
                    "steps": [
                        "W zleceniu w VA02 wejdź w pozycję -> Warunki -> przycisk 'Analiza', aby sprawdzić przeszukane tabele kondycyjne.",
                        "Uruchom transakcję VK11 dla rodzaju warunku PR00.",
                        "Wprowadź rekord ceny (np. Organizacja/Materiał lub Klient/Materiał) z odpowiednią walutą i jednostką miary.",
                        "Wróć do zlecenia w VA02 i na zakładce Warunki kliknij 'Nowa wycena' (Update -> opcja B).",
                        "Zapisz zlecenie."
                    ]
                },
                {
                    "name": "Wariant B (Wprowadzenie ceny ręcznej)",
                    "desc": "Jeśli rodzaj warunku dopuszcza wprowadzanie ręczne:",
                    "steps": [
                        "W VA02 na zakładce Warunki pozycji dodaj wiersz PR00 ręcznie i wpisz stawkę jednostkową.",
                        "Zapisz zlecenie."
                    ]
                }
            ],
            "tcodes": ["VK11", "VK12", "V/08", "VA02", "V/06"],
            "tables": ["KONV", "PRCD_ELEMENTS", "T685A", "T683S"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Wycena -> Kontrola wyceny -> Zdefiniuj schematy kalkulacyjne (V/08)",
            "pitfalls_and_secondary": [
                "Zwróć uwagę na datę ustalania cen w nagłówku zlecenia – rekordy VK11 mają ścisłe ramy ważności dat."
            ],
            "quick_fix": False
        },
        "V4001": {
            "code": "V4001",
            "title": "Blokada kredytowa: Przekroczony limit kredytowy dla odbiorcy",
            "category": "Credit Management (FSCM / VKM1)",
            "keywords": ["v4001", "limit kredytowy", "blokada kredytowa", "credit limit exceeded", "vkm1", "vkm3", "vkm4"],
            "summary": "Automatyczna kontrola kredytowa zablokowała realizację zlecenia z powodu przekroczenia limitu kupieckiego lub przeterminowanych należności.",
            "business_impact": "Blokada tworzenia dostawy (VL01N) i wysyłki towaru do klienta.",
            "technical_mechanism": "W trakcie zapisu zlecenia system sumuje otwarte pozycje, otwarte dostawy i bieżące zlecenie, porównując wynik z limitem kredytowym w obszarze kontroli KKBER / segmencie kredytowym FSCM. W razie przekroczenia flaga CMGST w VBAK/VBUK przyjmuje wartość 'B' (Zablokowane).",
            "solution_variants": [
                {
                    "name": "Wariant A (Zwolnienie doraźne przez Menadżera Kredytowego w VKM1 / VKM3)",
                    "desc": "Odblokowanie konkretnego zlecenia bez trwałego zwiększania limitu:",
                    "steps": [
                        "Uruchom transakcję VKM1 lub VKM3, zlokalizuj dokument zlecenia.",
                        "Zaznacz pozycję, kliknij ikonę zielonej flagi ('Zwolnij') i zapisz.",
                        "Zlecenie natychmiast staje się gotowe do tworzenia dostawy w VL01N."
                    ]
                },
                {
                    "name": "Wariant B (Trwałe podniesienie limitu kredytowego w BP FSCM)",
                    "desc": "Zwiększenie limitu kupieckiego dla zaufanego kontrahenta:",
                    "steps": [
                        "W transakcji BP przejdź do roli UKM000 (Zarządzanie kredytami SAP) -> wejdź w segment kredytowy.",
                        "Zaktualizuj kwotę w polu 'Limit kredytowy' i zapisz.",
                        "W środowisku ECC analogiczną operację wykonaj w transakcji FD32."
                    ]
                }
            ],
            "tcodes": ["VKM1", "VKM3", "VKM4", "BP", "FD32", "OVA8"],
            "tables": ["VBUK", "VBAK", "UKMBP_CMS_SGM", "KNKK"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Zarządzanie kredytem/zarządzanie ryzykiem -> Kontrola kredytowa (OVA8)",
            "pitfalls_and_secondary": [
                "Każda późniejsza edycja ilości lub ceny w odblokowanym zleceniu wywoła ponowną blokadę kredytową!"
            ],
            "quick_fix": False
        },
        "VL150": {
            "code": "VL150",
            "title": "Nie można ustalić punktu wysyłkowego dla pozycji dostawy",
            "category": "Shipping & Delivery (OVL2)",
            "keywords": ["vl150", "punkt wysyłkowy", "shipping point", "brak punktu wysylkowego", "shipping point determination", "ovl2"],
            "summary": "System nie może wyznaczyć punktu wysyłkowego (VSTEL), co uniemożliwia utworzenie dokumentu dostawy wychodzącej w VL01N.",
            "business_impact": "Całkowite wstrzymanie procesu wydania i wysyłki towaru z magazynu.",
            "technical_mechanism": "Punkt wysyłkowy w SAP SD wyznaczany jest ściśle według wzoru: Warunek wysyłki (z kartoteki klienta KNVV-VSBED) + Grupa załadunku (z kartoteki materiału MARC-LADGR) + Zakład dostarczający (z pozycji zlecenia VBAP-WERKS). Brak powiązania tej trójki w tabeli TVSTZ skutkuje błędem VL150.",
            "solution_variants": [
                {
                    "name": "Wariant A (Konfiguracja reguły w OVL2 - Standard SPRO)",
                    "desc": "Zdefiniowanie powiązania punktu wysyłkowego w konfiguracji IMG:",
                    "steps": [
                        "Uruchom OVL2 -> kliknij 'Nowe wpisy'.",
                        "Wprowadź: [Warunek wysyłki, np. 01] + [Grupa załadunku, np. 0001] + [Zakład dostarczający, np. 1000] -> [Proponowany punkt wysyłkowy VSTEL].",
                        "Zapisz na zleceniu transportowym i ponów tworzenie dostawy w VL01N."
                    ]
                },
                {
                    "name": "Wariant B (Korekta danych w zleceniu lub kartotekach)",
                    "desc": "Jeśli w pozycji zlecenia podano błędny zakład lub w kartotece materiału pominięto grupę załadunku:",
                    "steps": [
                        "Sprawdź w MM02 (Sprzedaż: Zakład/Magazyn) pole 'Grupa załadunku'.",
                        "W VA02 upewnij się, że zakład w pozycji odpowiada właściwemu magazynowi wysyłkowemu."
                    ]
                }
            ],
            "tcodes": ["OVL2", "MM02", "BP", "VL01N", "VA02"],
            "tables": ["TVSTZ", "VBAP", "MVKE", "MARC"],
            "spro_path": "SPRO -> Logistyka ogólna -> Wysyłka -> Funkcje podstawowe -> Ustalanie punktu wysyłkowego i punktu odbioru towarów -> Przyporządkuj punkty wysyłkowe (OVL2)",
            "pitfalls_and_secondary": [
                "Po wyznaczeniu punktu wysyłkowego upewnij się, że zlecenie osiągnęło termin realizacji (błąd VL303) oraz że w magazynie jest wolny zapas (M7021)."
            ],
            "quick_fix": False
        },
        "VL303": {
            "code": "VL303",
            "title": "Brak pozycji do wysyłki / Zlecenie nie osiągnęło terminu realizacji",
            "category": "Delivery Creation & Scheduling (VL01N)",
            "keywords": ["vl303", "brak pozycji do dostawy", "no delivery-relevant items", "data wysyłki w przyszłości", "vl01n"],
            "summary": "W transakcji VL01N data wyboru jest wcześniejsza niż data gotowości materiałowej z linii harmonogramu zlecenia.",
            "business_impact": "Niemożność wygenerowania dostawy wychodzącej w planowanym terminie.",
            "technical_mechanism": "Harmonogramowanie dostaw SD przelicza czas transportu, załadunku i kompletacji. Jeśli potwierdzona linia harmonogramu (VBEP) przypada na datę późniejszą niż parametr 'Data wyboru' w ekranie selekcji VL01N, SAP traktuje zlecenie jako jeszcze niedojrzałe do wysyłki.",
            "solution_variants": [
                {
                    "name": "Wariant A (Przesunięcie daty wyboru w VL01N)",
                    "desc": "Proste dostosowanie parametru w ekranie początkowym tworzenia dostawy:",
                    "steps": [
                        "W VL01N w polu 'Data wyboru' wprowadź datę o kilka dni późniejszą (np. koniec bieżącego tygodnia).",
                        "Zatwierdź Enterem – pozycje zostaną wczytane do dostawy."
                    ]
                },
                {
                    "name": "Wariant B (Weryfikacja ilości potwierdzonej w VA02)",
                    "desc": "Jeśli w linii harmonogramu potwierdzona ilość wynosi 0 z powodu braku zapasu:",
                    "steps": [
                        "Sprawdź w VA02 zakładkę 'Podziały na linie' oraz stan w transakcji CO09 (kontrola ATP).",
                        "Po uzupełnieniu zapasu uruchom ponownie kontrolę dostępności w zleceniu."
                    ]
                }
            ],
            "tcodes": ["VL01N", "VA02", "VL10A", "CO09"],
            "tables": ["VBEP", "VBAK", "LIPS"],
            "spro_path": "N/A (Harmonogramowanie dostaw i linii VBEP)",
            "pitfalls_and_secondary": [
                "Dla masowego tworzenia dostaw w oparciu o profil czasowy warto korzystać z transakcji VL10A/VL10B zamiast pojedynczej VL01N."
            ],
            "quick_fix": False
        },
        "M7021": {
            "code": "M7021",
            "title": "Brak wolnego zapasu materiału w składzie (Deficit of SL Unrestricted-use stock)",
            "category": "Inventory & ATP (MMBE / CO09)",
            "keywords": ["m7021", "brak zapasu", "deficit of stock", "zapas nieograniczony", "niewystarczający zapas", "brak towaru", "co09", "mmbe"],
            "summary": "Ilość materiału wolnego do wykorzystania w danym składzie jest mniejsza niż ilość wymagana na pozycji dostawy podczas księgowania wydania towarów PGI.",
            "business_impact": "Brak możliwości zakończenia etapu logistycznego i zaksięgowania wydania materiałów (PGI) w transakcji VL02N.",
            "technical_mechanism": "Ruch materiałowy 601 (Wydanie towaru dla dostawy SD) wymaga zapasu w statusie 'Wolny do wykorzystania' (tabela MARD pole LABST). Zapas zablokowany, w kontroli jakości (QI) lub zarezerwowany przez inne dokumenty w CO09 nie może zostać rozksięgowany.",
            "solution_variants": [
                {
                    "name": "Wariant A (Przesunięcie zapasu z innego składu lub przyjęcie w MIGO)",
                    "desc": "Doraźne uzupełnienie fizycznego stanu na składzie wysyłkowym:",
                    "steps": [
                        "Sprawdź stany we wszystkich składach w MMBE.",
                        "W razie obecności zapasu w innym składzie: wykonaj przesunięcie międzymagazynowe ruchem 311 w MIGO.",
                        "Wróć do dostawy w VL02N i zaksięguj wydanie towaru (PGI)."
                    ]
                },
                {
                    "name": "Wariant B (Zwolnienie z kontroli jakości lub przeksiegowanie)",
                    "desc": "Jeśli zapas znajduje się w kontroli jakości QI:",
                    "steps": [
                        "W module QM / transakcji MIGO ruch 321 przeksięguj zapas z kontroli jakości do zapasu wolnego.",
                        "Zaksięguj wydanie towaru w VL02N."
                    ]
                }
            ],
            "tcodes": ["MMBE", "CO09", "MD04", "MIGO", "VL02N"],
            "tables": ["MARD", "MBEW", "MSKA"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Kontrola dostępności i przekazywanie zapotrzebowań (OVZ9)",
            "pitfalls_and_secondary": [
                "Po zaksięgowaniu PGI kolejnym krokiem jest fakturowanie w VF01 – upewnij się, że reguły sterowania kopiowaniem VTFL są aktywne."
            ],
            "quick_fix": False
        },
        "VL622": {
            "code": "VL622",
            "title": "Wymagany podział na partie lub brak przypisania partii w pozycji dostawy",
            "category": "Batch Management (VCH1 / VL02N)",
            "keywords": ["vl622", "brak partii", "podział na partie", "batch split", "zarządzanie partiami", "batch determination"],
            "summary": "Materiał podlega gospodarce partiami, jednak w dostawie wychodzącej nie wskazano konkretnej partii z wolnym zapasem.",
            "business_impact": "Blokada księgowania wydania towarów PGI.",
            "technical_mechanism": "Flaga MARA-XCHPF = 'X' wymusza wskazanie numeru partii (LIPS-CHARG) przed zaksięgowaniem ruchu materiałowego 601.",
            "solution_variants": [
                {
                    "name": "Wariant A (Ręczny podział na partie w VL02N)",
                    "desc": "Szybkie przypisanie partii bezpośrednio na dokumencie dostawy:",
                    "steps": [
                        "W VL02N zaznacz pozycję dostawy i kliknij ikonę 'Podział na partie' (Batch Split).",
                        "Wprowadź numer dostępnej partii (CHARG) i rozksięguj ilość.",
                        "Zapisz i zaksięguj wydanie towarów."
                    ]
                },
                {
                    "name": "Wariant B (Automatyczna determinacja partii w VCH1)",
                    "desc": "Docelowa automatyzacja doboru partii wg daty ważności FEFO lub produkcji FIFO:",
                    "steps": [
                        "Uruchom VCH1 i skonfiguruj strategię wyszukiwania partii dla rodzaju dostawy.",
                        "System będzie dobierał właściwe partie automatycznie przy tworzeniu dostawy."
                    ]
                }
            ],
            "tcodes": ["VL02N", "VCH1", "MSC1N", "MSC2N"],
            "tables": ["MCH1", "LIPS", "MARA"],
            "spro_path": "SPRO -> Logistyka ogólna -> Zarządzanie partiami -> Ustalanie partii w SD (V/C1)",
            "pitfalls_and_secondary": [
                "Upewnij się, że partia wybrana do wysyłki nie ma statusu 'Zablokowana'."
            ],
            "quick_fix": False
        },
        "VTFL": {
            "code": "VTFL",
            "title": "Brak reguły sterowania kopiowaniem dla relacji Dostawa -> Faktura",
            "category": "Copy Control (VTFL / VTFA)",
            "keywords": ["vtfl", "vtfa", "vtla", "sterowanie kopiowaniem", "copy control", "brak wpisu kopiowania", "brak sterowania kopiowaniem"],
            "summary": "System nie potrafi skopiować danych z dokumentu dostawy do faktury z powodu braku powiązania rodzajów dokumentów lub kategorii pozycji.",
            "business_impact": "Niemożność wystawienia faktury w transakcji VF01 / VF04.",
            "technical_mechanism": "Tabele TVCPFL (nagłówek) oraz TVCPFLP (pozycja) definiują zasady przenoszenia danych, przeliczania cen (Pricing Type) i sprawdzania statusów między dostawą źródłową a fakturą docelową.",
            "solution_variants": [
                {
                    "name": "Wariant A (Konfiguracja sterowania kopiowaniem w VTFL - SPRO)",
                    "desc": "Uzupełnienie brakującego wpisu w konfiguracji O2C:",
                    "steps": [
                        "Uruchom VTFL -> wybierz rodzaj faktury docelowej (np. F2) oraz rodzaj dostawy źródłowej (np. LF).",
                        "Jeśli brak wpisu w nagłówku: utwórz wpis kopiując referencję standardową F2/LF.",
                        "Wejdź w poziom 'Pozycja' -> dodaj kategorię pozycji występującą w dostawie (np. TAN lub ZTAN).",
                        "Ustaw Typ ustalania cen (Pricing Type, np. 'G' dla zachowania cen z przeliczeniem podatków) oraz Rutynę ilości fakturowanej (001).",
                        "Zapisz na zleceniu transportowym i ponów fakturowanie w VF01."
                    ]
                }
            ],
            "tcodes": ["VTFL", "VTFA", "VF01", "VF04"],
            "tables": ["TVCPFLP", "TVCPFL"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Dokumenty fakturowania -> Sterowanie kopiowaniem (VTFL)",
            "pitfalls_and_secondary": [
                "Po przejściu VTFL natychmiast następuje determinacja kont VKOA – upewnij się, że plan kont klienta ma zdefiniowane reguły przychodowe."
            ],
            "quick_fix": False
        },
        "V1058": {
            "code": "V1058",
            "title": "Brak przypisania kategorii podziału na linie harmonogramu (Schedule Line Category)",
            "category": "Schedule Lines & Planning (VOV5 / VOV6)",
            "keywords": ["v1058", "linia harmonogramu", "schedule line", "vov5", "vov6", "brak linii harmonogramu"],
            "summary": "Kategoria pozycji nie ma przypisanej kategorii linii harmonogramu dla danego typu planowania MRP.",
            "business_impact": "Pozycja zlecenia nie może zaplanować daty dostawy ani zarezerwować zapasu.",
            "technical_mechanism": "Tabela TVEPZ powiązuje kategorię pozycji (PSTYV) z typem MRP z kartoteki materiału (DISMM), wyznaczając kategorię linii ETTYP (np. CP lub CN).",
            "solution_variants": [
                {
                    "name": "Wariant A (Przypisanie w VOV5)",
                    "desc": "Uzupełnienie relacji kategorii pozycji i typu MRP:",
                    "steps": [
                        "Uruchom VOV5 -> kliknij 'Nowe wpisy'.",
                        "Wprowadź: [Kategoria pozycji PSTYV] + [Typ MRP DISMM] -> [Domyślna linia harmonogramu ETTYP, np. CP].",
                        "Zapisz i utwórz ponownie pozycję w VA01."
                    ]
                }
            ],
            "tcodes": ["VOV5", "VOV6", "MM02", "VA01"],
            "tables": ["TVEP", "TVEPZ", "VBAP"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Pozycje dokumentu sprzedaży -> Podziały na linie harmonogramu -> Przyporządkuj kategorie (VOV5)",
            "pitfalls_and_secondary": [
                "Upewnij się w VOV6, że kategoria linii ma aktywny znacznik 'Trafność dla dostawy'."
            ],
            "quick_fix": False
        },
        "V4040": {
            "code": "V4040",
            "title": "Błąd generowania zapotrzebowania zakupowego (Banf) dla pozycji trójstronnej TAS",
            "category": "Third-Party Order & MM Integration",
            "keywords": ["v4040", "tas", "handel trojstronny", "dropshipping", "brak banf", "nie utworzono zapotrzebowania", "third party"],
            "summary": "Podczas zapisywania zlecenia sprzedaży z pozycją TAS system nie wygenerował automatycznego zapotrzebowania zakupowego (Banf) w tabeli EBAN.",
            "business_impact": "Dział zakupów nie widzi zapotrzebowania, brak możliwości wysłania zamówienia PO do dostawcy. Zablokowany proces dostawy bezpośredniej do klienta.",
            "technical_mechanism": "Dla pozycji TAS linia harmonogramu CS musi posiadać typ pozycji zamówienia 'S' (Third-party) oraz typ przypisania konta 'X'. Ponadto w tabeli T161A musi istnieć dozwolona relacja rodzaju zapotrzebowania 'NB' z rodzajem zamówienia.",
            "solution_variants": [
                {
                    "name": "Wariant A (Weryfikacja kategorii linii harmonogramu w VOV6)",
                    "desc": "Sprawdzenie parametrów zamówieniowych linii harmonogramu CS:",
                    "steps": [
                        "Uruchom VOV6 -> wybierz kategorię linii 'CS'.",
                        "Upewnij się, że zaznaczono 'Trafność dla zamówienia' (Order item rel.) = 'X'.",
                        "Wskaż rodzaj dokumentu zakupu 'NB' oraz typ pozycji 'S' (Third-party).",
                        "Zapisz i utwórz zlecenie ponownie w VA01."
                    ]
                },
                {
                    "name": "Wariant B (Uzupełnienie rekordu informacyjnego i grupy zaopatrzeniowej)",
                    "desc": "Gdy błąd wynika z braku danych zaopatrzeniowych materiału w MM02:",
                    "steps": [
                        "Sprawdź w MM02 widok 'Zakupy' czy materiał ma przypisaną Grupę zaopatrzeniową (EKGRP).",
                        "W ME11 utwórz rekord informacyjny dla dostawcy ze statusem 'Standard' z warunkami cenowymi zakupu."
                    ]
                }
            ],
            "tcodes": ["VOV6", "VOV5", "MM02", "ME11", "VA02", "ME53N"],
            "tables": ["TVEP", "EBAN", "VBAP", "VBEP"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Pozycje dokumentu sprzedaży -> Podziały na linie harmonogramu -> Zdefiniuj kategorie (VOV6)",
            "pitfalls_and_secondary": [
                "Jeśli materiał nie ma widoku Zakupów w danym zakładzie, system wyrzuci błąd braku danych walidacji materiałowej.",
                "Upewnij się, że pole Adres dostawy w zleceniu poprawnie dziedziczy dane odbiorcy końcowego (Ship-to)."
            ],
            "quick_fix": False
        },
        "V1324": {
            "code": "V1324",
            "title": "Błąd kalkulacji zlecenia sprzedaży lub brak klasy zapotrzebowań (MTO)",
            "category": "Make-to-Order & Controlling (PP-CO)",
            "keywords": ["v1324", "mto", "klasa zapotrzebowan", "kalkulacja zlecenia", "requirement class", "zapas e", "make to order"],
            "summary": "Zlecenie MTO (pozycja TAK/TAC) nie może wyznaczyć klasy zapotrzebowań lub kalkulacja kosztów zlecenia sprzedaży nie powiodła się.",
            "business_impact": "Brak możliwości zaplanowania zlecenia produkcyjnego pod zlecenie klienta, brak alokacji kosztów rzeczywistych w CO-PC.",
            "technical_mechanism": "System wyznacza rodzaj zapotrzebowań (Requirement Type) w tabeli T459K na podstawie strategii planowania (MARC-STRGR) lub typu pozycji (VBAP-PSTYV). Brak powiązania w OVZH/OVZG uniemożliwia utworzenie zapasu specjalnego 'E'.",
            "solution_variants": [
                {
                    "name": "Wariant A (Weryfikacja przypisania typu zapotrzebowań w OVZI)",
                    "desc": "Skonfigurowanie determinacji klasy zapotrzebowań z typu pozycji:",
                    "steps": [
                        "Uruchom OVZI i odszukaj parę: Typ pozycji (TAK) + Typ MRP (np. PD lub ND).",
                        "Przypisz rodzaj zapotrzebowania 'KE' (Zlecenie sprzedaży bez konfiguracji).",
                        "W OVZG sprawdź czy Klasa zapotrzebowań '040' ma aktywny 'Zapas specjalny E' oraz 'Wycenę zlecenia'."
                    ]
                }
            ],
            "tcodes": ["OVZG", "OVZH", "OVZI", "CK51N", "VA02", "CO01"],
            "tables": ["T459K", "T459A", "VBAP", "MSKA"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Sprawdzanie dostępności i przekazywanie zapotrzebowań -> Przekazywanie zapotrzebowań -> Zdefiniuj klasy zapotrzebowań (OVZG)",
            "pitfalls_and_secondary": [
                "Jeśli zlecenie ma status błędu kalkulacji, nie zwolnisz dostawy w VL01N bez zdjęcia blokady kalkulacji."
            ],
            "quick_fix": False
        },
        "VF072": {
            "code": "VF072",
            "title": "Błąd fakturowania wewnętrznego Intercompany (Brak warunku PI01/PI02 lub klienta IV)",
            "category": "Intercompany Billing & Cross-Company",
            "keywords": ["vf072", "intercompany", "faktura iv", "pi01", "pi02", "miedzyfirmowa", "cross company"],
            "summary": "Podczas generowania faktury wewnętrznej IV (Spółka Produkcyjna B -> Spółka Handlowa A) system nie ustalił cen transferowych lub brak jest klienta wewnętrznego przypisanego do jednostki BUKRS.",
            "business_impact": "Brak możliwości rozliczenia dostaw między spółkami w grupie kapitałowej, zablokowane fakturowanie wewnętrzne i rozrachunki konsolidacyjne.",
            "technical_mechanism": "W transakcji OOCF każda jednostka BUKRS musi mieć zdefiniowaną organizację sprzedaży i przyporządkowanego klienta wewnętrznego. W procedurze cenowej faktury IV wymagany jest warunek cen transferowych PI01 (kwotowy) lub PI02 (procentowy).",
            "solution_variants": [
                {
                    "name": "Wariant A (Konfiguracja klienta wewnętrznego w OOCF)",
                    "desc": "Przypisanie klienta wewnętrznego do jednostki gospodarczej:",
                    "steps": [
                        "Uruchom SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Rozliczenia międzyfirmowe -> Zdefiniuj jednostki gospodarcze dla fakturowania międzyfirmowego.",
                        "Dla jednostki handlowej (BUKRS 1000) przypisz numer klienta (KUNNR) utworzonego w jednostce dostarczającej (BUKRS 2000).",
                        "Upewnij się, że klient ma rozszerzenie na organizację sprzedaży jednostki dostarczającej."
                    ]
                },
                {
                    "name": "Wariant B (Utrzymanie rekordu cenowego PI01 w VK11)",
                    "desc": "Wprowadzenie ceny transferowej w jednostce dostarczającej:",
                    "steps": [
                        "Uruchom VK11 -> wybierz rodzaj warunku 'PI01' (Wewnętrzna cena).",
                        "Wprowadź: Org. sprzedaży dostarczająca + Jednostka odbiorcza + Materiał -> Kwota ceny transferowej.",
                        "Zapisz i zaktualizuj wycenę w VF02 (typ faktury IV)."
                    ]
                }
            ],
            "tcodes": ["OOCF", "VK11", "VF01", "VF02", "BP"],
            "tables": ["TVKO", "KNVV", "KONV", "VBRK", "VBRP"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Fakturowanie -> Rozliczenia międzyfirmowe",
            "pitfalls_and_secondary": [
                "Klient wewnętrzny w OOCF musi być przypisany do właściwego obszaru sprzedaży dostarczającego.",
                "Faktura zewnętrzna F2 dla klienta końcowego może być wystawiona, ale bez IV nie zamkniesz okresu FI w spółce produkcyjnej."
            ],
            "quick_fix": False
        },
        "M7022": {
            "code": "M7022",
            "title": "Deficyt zapasu konsygnacyjnego klienta (Brak stanu W przy pobraniu KE)",
            "category": "Consignment Inventory (MM-SD)",
            "keywords": ["m7022", "brak zapasu w", "konsygnacja", "pobranie ke", "deficyt konsygnacji", "msku", "zapas w"],
            "summary": "Podczas księgowania wydania towaru (ruch 633) dla zlecenia pobrania z konsygnacji (KE) system zgłasza deficyt ilościowy w zapasie specjalnym 'W'.",
            "business_impact": "Brak możliwości zafakturowania zużytego towaru konsygnacyjnego, rozbieżność między raportem klienta a stanem w SAP.",
            "technical_mechanism": "Zapas konsygnacyjny klienta ewidencjonowany jest w tabeli MSKU dla pary [Materiał + Zakład + Odbiorca KUNNR]. Pobranie ruchem 633 wymaga wcześniejszego zatowarowania ruchem 631 (zlecenie KB).",
            "solution_variants": [
                {
                    "name": "Wariant A (Weryfikacja stanu konsygnacyjnego w MB58 / MMBE)",
                    "desc": "Sprawdzenie rzeczywistego stanu zapasu specjalnego 'W':",
                    "steps": [
                        "Uruchom MB58 (Zapas konsygnacyjny u odbiorcy) -> podaj numer klienta i materiału.",
                        "Sprawdź czy ilość w kolumnie 'Zapas konsygnacyjny' pokrywa zgłoszone pobranie.",
                        "Jeśli stan jest zerowy, utwórz zlecenie uzupełnienia konsygnacji (KB) w VA01 i zaksięguj wydanie w VL02N (ruch 631)."
                    ]
                }
            ],
            "tcodes": ["MB58", "MMBE", "VA01", "VL02N", "VF01"],
            "tables": ["MSKU", "MSEG", "MKPF"],
            "spro_path": "Transakcja operacyjna zapasów specjalnych (MB58 / MMBE)",
            "pitfalls_and_secondary": [
                "Upewnij się, że numer klienta KUNNR w zleceniu KE jest identyczny z odbiorcą, dla którego zaksięgowano zapas W w zleceniu KB."
            ],
            "quick_fix": False
        },
        "DP90_ERR": {
            "code": "DP90_ERR",
            "title": "Błąd wyznaczania pozycji dynamicznych w rozliczeniach nakładczych (DIP Profile Error)",
            "category": "Resource-Related Billing & Services (SD-CS-PS)",
            "keywords": ["dp90", "dip", "dynamic item", "rrb", "uslugi nakladcze", "blad dip", "brak cennika rrb"],
            "summary": "Transakcja DP90 nie może przekształcić rzeczywistych kosztów (robocizna CATS, delegacje, materiały) na pozycje cennikowe zlecenia DMR.",
            "business_impact": "Brak możliwości wystawienia faktury za zrealizowane usługi serwisowe i konsultingowe (Time & Material).",
            "technical_mechanism": "Profil DIP (Dynamic Item Processor) konfiguruje reguły mapowania rodzajów kosztów (Cost Elements) z CO na materiały usługowe w SD. Jeśli w profilu ODP1 brakuje mapowania lub brak cen w VK11 dla materiału wynikowego, DP90 odrzuca rozliczenie.",
            "solution_variants": [
                {
                    "name": "Wariant A (Weryfikacja profilu DIP w ODP1)",
                    "desc": "Uzupełnienie mapowania rodzajów kosztów w profilu dynamicznym:",
                    "steps": [
                        "Uruchom ODP1 -> wybierz profil DIP przypisany w zleceniu serwisowym/projekcie.",
                        "Przejdź do 'Cechy' i 'Kryteria wyboru' -> upewnij się, że rodzaj kosztów zaksięgowany w CATS/KB21N wchodzi w zakres profilu.",
                        "W sekcji 'Ustalanie materiału' sprawdź czy rodzaj kosztu mapuje się na aktywny indeks materiału usługowego (np. SRV-01)."
                    ]
                },
                {
                    "name": "Wariant B (Uzupełnienie cennika usług w VK11)",
                    "desc": "Zapewnienie stawki roboczogodziny:",
                    "steps": [
                        "W VK11 wprowadź warunek PR00 dla materiału usługi określonego w profilu DIP.",
                        "Uruchom ponownie DP90 i zatwierdź propozycję rozliczenia."
                    ]
                }
            ],
            "tcodes": ["DP90", "ODP1", "VK11", "VA02", "IW32", "CJ20N"],
            "tables": ["AD01* (DIP)", "VBAK", "VBAP", "COEP"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja -> Sprzedaż -> Dokumenty sprzedaży -> Pozycje dokumentu sprzedaży -> Fakturowanie na podstawie nakładów (DIP)",
            "pitfalls_and_secondary": [
                "Upewnij się, że godziny w CATS zostały zatwierdzone i przeniesione do CO transakcją CAT9/CATA."
            ],
            "quick_fix": False
        }
    }

    @classmethod
    def diagnose_error_structured(cls, prompt: str, profile: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Zwraca pełny ustrukturyzowany słownik diagnozy błędu z głęboką ekspertyzą i wariantami rozwiązań.
        """
        prompt_clean = prompt.lower().strip()
        matched_entry = None

        # 1. Dokładne dopasowanie po kodzie błędu
        for code, data in cls.SD_ERRORS_CATALOG.items():
            pattern = rf'(?:|(?<=[^a-zA-Z0-9])){re.escape(code.lower())}(?:|(?=[^a-zA-Z0-9]))'
            spaced_code = code[:2] + r'\s*' + code[2:]
            if re.search(pattern, prompt_clean) or re.search(spaced_code, prompt_clean, re.IGNORECASE):
                matched_entry = data
                break

        # 2. Dopasowanie semantyczne po słowach kluczowych
        if not matched_entry:
            best_score = 0
            for code, data in cls.SD_ERRORS_CATALOG.items():
                score = sum(1 for kw in data['keywords'] if kw in prompt_clean)
                if score > best_score and score >= 2:
                    best_score = score
                    matched_entry = data
                elif score > best_score and any(kw in prompt_clean for kw in [data['code'].lower(), data['code'][:2].lower() + ' ' + data['code'][2:].lower()]):
                    best_score = score
                    matched_entry = data

        profile = profile or {}
        client_name = profile.get('name', 'Bieżący profil')
        ktopl = profile.get('ktopl', 'INT')
        bukrs = profile.get('bukrs', '1000')

        if not matched_entry:
            error_triggers = ['błąd', 'blad', 'error', 'nie działa', 'zablokowan', 'nie moge', 'failed', 'problem', 'dump', 'st22', 'se91', 'awaria', 'usterka', 'kolejny błąd', 'inny problem']
            if any(t in prompt_clean for t in error_triggers):
                return cls._generate_generic_structured_framework(prompt, profile)
            return None

        # Formatowanie głębokiego raportu ekspertyzy
        markdown_rep = cls._format_comprehensive_expert_report(matched_entry, profile)
        return {
            "code": matched_entry["code"],
            "title": matched_entry["title"],
            "category": matched_entry["category"],
            "summary": matched_entry.get("summary", ""),
            "business_impact": matched_entry.get("business_impact", ""),
            "technical_mechanism": matched_entry.get("technical_mechanism", ""),
            "solution_variants": matched_entry.get("solution_variants", []),
            "tcodes": matched_entry["tcodes"],
            "tables": matched_entry["tables"],
            "spro_path": matched_entry["spro_path"],
            "pitfalls_and_secondary": matched_entry.get("pitfalls_and_secondary", []),
            "quick_fix": matched_entry.get("quick_fix", False),
            "quick_fix_type": matched_entry.get("quick_fix_type", None),
            "company": {
                "name": client_name,
                "ktopl": ktopl,
                "bukrs": bukrs
            },
            "markdown_report": markdown_rep
        }

    @classmethod
    def diagnose_error(cls, prompt: str, profile: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Zwraca sformatowany tekst markdown z diagnozą błędu.
        """
        diag = cls.diagnose_error_structured(prompt, profile)
        if diag:
            return diag.get("markdown_report")
        return None

    @classmethod
    def _format_comprehensive_expert_report(cls, data: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Formatuje czytelną, głęboką, elegancką ekspertyzę Senior Konsultanta SD.
        """
        profile = profile or {}
        client_name = profile.get('name', 'Bieżący profil')
        ktopl = profile.get('ktopl', 'INT')
        bukrs = profile.get('bukrs', '1000')

        tcodes_badges = ' '.join([f'`{tc}`' for tc in data['tcodes']])
        tables_badges = ' '.join([f'`{tb}`' for tb in data['tables']])

        # Warianty rozwiązań
        variants_blocks = []
        for var in data.get('solution_variants', []):
            steps_text = "\n".join([f"     • {s}" for s in var['steps']])
            variants_blocks.append(f"**{var['name']}**:\n  _{var['desc']}_\n{steps_text}")
        variants_section = "\n\n".join(variants_blocks)

        # Pułapki i błędy wtórne
        pitfalls_list = "\n".join([f"  • {p}" for p in data.get('pitfalls_and_secondary', [])])

        quick_fix_note = ""
        if data.get('quick_fix'):
            quick_fix_note = (
                "\n\n⚡ **Szybka Naprawa Copilota (1-Click Quick-Fix)**:\n"
                "Możesz rozwiązać ten błąd jednym kliknięciem bez wchodzenia do SAP GUI w zakładce **🩺 VKOA Troubleshooter**!"
            )

        report = (
            f"[GUIDE] 🚨 **Diagnoza Błędu: {data['code']}**\n"
            f"**{data['title']}**\n"
            f"*Obszar*: {data['category']} | *Aktywny Klient*: **{client_name}** (Plan kont: `{ktopl}`, BUKRS: `{bukrs}`)\n\n"
            f"---\n\n"
            f"### 🔍 Analiza Problemu & Wpływ Biznesowy:\n"
            f"{data['business_impact']}\n\n"
            f"### ⚙️ Mechanizm Techniczny w SAP:\n"
            f"{data['technical_mechanism']}\n\n"
            f"### 💡 Warianty Rozwiązania Problemów:\n"
            f"{variants_section}\n\n"
            f"### 🛠️ Transakcje & Konfiguracja SPRO:\n"
            f"• **Kluczowe transakcje**: {tcodes_badges}\n"
            f"• **Tabele systemowe**: {tables_badges}\n"
            f"• **Ścieżka SPRO (IMG)**: `{data['spro_path']}`\n\n"
            f"### ⚠️ Uwagi Architekta & Błędy Wtórne (Na co uważać):\n"
            f"{pitfalls_list}"
            f"{quick_fix_note}"
        )
        return report

    @classmethod
    def _generate_generic_structured_framework(cls, prompt: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generuje uniwersalną metodykę diagnozy nietypowych problemów SD.
        """
        profile = profile or {}
        client_name = profile.get('name', 'Bieżący profil')
        ktopl = profile.get('ktopl', 'INT')
        bukrs = profile.get('bukrs', '1000')

        markdown_rep = (
            f"[GUIDE] 🩺 **Metodyka Diagnozy Problemów SAP SD (Troubleshooting Framework - {client_name})**:\n\n"
            f"### 🔍 Rekomendacja Postępowania Konsultanta:\n"
            f"Dla zgłoszonego problemu w module Sprzedaży i Dystrybucji rekomenduję standardowy proces analizy:\n\n"
            f"1. **Identyfikacja komunikatu w `SE91`**: Odczytaj klasę i numer wiadomości ze szczegółów technicznych błędu w SAP GUI. W SE91 znajdziesz dokładny program ABAP i warunek, który zablokował transakcję.\n\n"
            f"2. **Weryfikacja brakujących uprawnień w `SU53`**: Jeśli transakcja zwraca komunikat braku autoryzacji, uruchom natychmiast transakcję `SU53` i przekaż obiekt autoryzacyjny do zespołu Basis.\n\n"
            f"3. **Analiza zrzutów pamięci w `ST22`**: W razie nagłego błędu systemowego (Short Dump) transakcja `ST22` wskaże dokładną przyczynę techniczną (np. MESSAGE_TYPE_X, CONVT_NO_NUMBER).\n\n"
            f"4. **Analiza logów determinacji (`VA02` / `VF02`)**: Skorzystaj z wbudowanych analiz SAP: *Warunki ➔ Analiza* (dla cen) lub *Środowisko ➔ Analiza ➔ Ustalanie kont* (dla faktur).\n\n"
            f"5. **Weryfikacja blokad tabel w `SM12`**: Upewnij się, że tabele `VBAK`, `VBAP` lub `VBRK` nie są zablokowane przez osierocone sesje użytkowników.\n\n"
            f"💡 *Podaj dokładny kod błędu (np. `VF067`, `V1382`, `VL150`, `FF704`, `M7021`, `V4001`) lub wklej treść komunikatu, a przedstawię precyzyjne warianty rozwiązania!*"
        )

        return {
            "code": "SD-DIAG",
            "title": "Metodyka Diagnozy Problemów SAP SD (Troubleshooting Framework)",
            "category": "SD Diagnostic Methodology",
            "summary": "Nietypowy lub złożony błąd w procesie O2C wymagający analizy logów systemowych i zrzutów pamięci.",
            "business_impact": "Przestój w przetwarzaniu dokumentu sprzedaży lub dostawy.",
            "technical_mechanism": "Wymaga zbadania logów wiadomości, tabel bazodanowych oraz ewentualnych zrzutów pamięci ABAP.",
            "solution_variants": [
                {
                    "name": "Wariant 1: Analiza komunikatu w SE91 i SU53",
                    "desc": "Sprawdzenie programu źródłowego i brakujących obiektów uprawnień",
                    "steps": ["SE91: Odczyt komunikatu błędu", "SU53: Weryfikacja brakujących autoryzacji", "ST22: Sprawdzenie dumpów"]
                }
            ],
            "tcodes": ["SE91", "SU53", "ST22", "VA02", "VF02", "SM12"],
            "tables": ["T100", "USR02", "VBAK", "VBAP", "VBRK"],
            "spro_path": "SPRO -> Sprzedaż i dystrybucja",
            "pitfalls_and_secondary": [
                "Podaj dokładny kod błędu, aby uzyskać dedykowaną analizę wariantów naprawczych."
            ],
            "quick_fix": False,
            "quick_fix_type": None,
            "company": {
                "name": client_name,
                "ktopl": ktopl,
                "bukrs": bukrs
            },
            "markdown_report": markdown_rep
        }
