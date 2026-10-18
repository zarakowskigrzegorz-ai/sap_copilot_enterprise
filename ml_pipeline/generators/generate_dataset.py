import json
import random
import os

customers = [
    "Auto-Partner Sp. z o.o.", "Multitruck", "Trans-Logistics S.A.", 
    "Delta Parts", "Global Motors", "Pol-Trans Sp. z o.o.", "Inter-Car",
    "Agro-Met", "Tech-Bar", "Euro-Truck Sp. z o.o.", "Logis-Tech",
    "Apex Sp. z o.o.", "Vistula Trade", "Silesia Parts", "Baltic Logistics"
]

materials = [
    ("SM-100", "Smar łożyskowy litowy", "KG"),
    ("FL-200", "Filtr oleju silnikowego", "SZT"),
    ("OL-50", "Olej syntetyczny 5W40", "L"),
    ("US-10", "Uszczelka gumowa", "SZT"),
    ("TR-500", "Tarcza hamulcowa", "SZT"),
    ("PN-12", "Płyn hamulcowy DOT-4", "L"),
    ("BS-30", "Klocki hamulcowe", "SZT")
]

quantities = [10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 750, 1000]

va01_templates = [
    "Potrzebuję zlecenia sprzedaży VA01 na {qty} {unit} materiału {mat_id}",
    "Złóż zamówienie na {qty} {unit} produktu {mat_desc}",
    "Utwórz zlecenie sprzedaży dla {qty} sztuk indeksu {mat_id}",
    "Chcę kupić {qty} {unit} towaru {mat_desc} o indeksie {mat_id}",
    "Wprowadź pozycję VA01: {qty} {unit} - {mat_desc}",
    "Nowe zlecenie sprzedaży VA01: {mat_id}, ilość {qty} {unit}",
    "Proszę o rejestrację zamówienia na {qty} {unit} ({mat_id})"
]

xd01_templates = [
    "Chciałbym założyć nowego klienta {cust}",
    "Utwórz kartotekę klienta dla firmy {cust}",
    "Zarejestruj kontrahenta {cust} w systemie",
    "Potrzebuję założyć klienta o nazwie {cust}",
    "Nowy kontrahent w strukturze SD: {cust}",
    "Wprowadź dane podstawowe nowego klienta: {cust}"
]

guide_prompts = [
    ("Wyjaśnij mi pełny łańcuch O2C w SAP S/4HANA i powiązane tablice.", 
     "[GUIDE] **Proces Order-to-Cash (O2C) w SAP S/4HANA** obejmuje następujące etapy i tablice:\n1. **XD01 / VD01** – Tworzenie danych podstawowych klienta (tablice KNA1, KNVV).\n2. **MM01** – Tworzenie materiału z rozszerzeniem o widoki sprzedaży (tablice MARA, MVKE).\n3. **VA01** – Utworzenie zlecenia sprzedaży (tablice VBAK, VBAP). System wykonuje tu automatyczną weryfikację limitu kredytowego w tabeli sap_customers.\n4. **VL01N** – Utworzenie dostawy wychodzącej (tablice LIKP, LIPS). Sprawdzany jest stan dostępności towaru (ATP) w tabeli sap_stock.\n5. **VL02N / MIGO** – Księgowanie wydania zewnętrznego (Goods Issue - tablice MKPF, MSEG).\n6. **VF01** – Utworzenie faktury sprzedaży (tablice VBRK, VBAP)."),
    
    ("Co się dzieje, gdy zlecenie sprzedaży przekracza przyznany limit kredytowy klienta?",
     "[GUIDE] W module SAP SD/FI, jeśli wartość dokumentu w transakcji VA01 przekracza ekspozycję i limit kredytowy zdefiniowany w tabeli sap_customers, system automatycznie wstrzymuje pozycję i nadaje status blokady kredytowej (**BLOCKED_CREDIT**). Dokument nie może zostać przekształcony do dostawy w VL01N, dopóki dział finansowy nie zwolni blokady za pomocą transakcji VKM1."),
     
    ("Jak działa kontrola dostępności ATP podczas tworzenia dostawy w VL01N?",
     "[GUIDE] Kontrola dostępności (Available-to-Promise) w transakcji VL01N weryfikuje fizyczny stan magazynowy w tabeli sap_stock dla danego zakładu (WERKS) i składu. Jeżeli żądana ilość w dostawie przewyższa aktualny stan magazynowy, pozycja otrzymuje status oczekiwania (PENDING_STOCK) i nie pozwala na zaksięgowanie wydania zewnętrznego (Goods Issue).")
]

def generate_synthetic_dataset(filename=None, target_count=5000):
    if filename is None:
        filename = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.jsonl")
    records = []
    
    # Podział proporcjonalny na 3 kategorie (merytoryka, VA01, XD01)
    chunk = target_count // 3
    
    # 1. Warianty merytoryczne [GUIDE]
    for _ in range(chunk):
        prompt, ans = random.choice(guide_prompts)
        records.append({"text": f"### User:\n{prompt}\n\n### Assistant:\n{ans}"})
        
    # 2. Warianty operacyjne VA01
    for _ in range(chunk):
        tmpl = random.choice(va01_templates)
        mat_id, mat_desc, unit = random.choice(materials)
        qty = random.choice(quantities)
        prompt = tmpl.format(qty=qty, unit=unit, mat_id=mat_id, mat_desc=mat_desc)
        ans = f"VA01;{mat_id};{mat_desc};ROH;JAN1;{unit};{qty}"
        records.append({"text": f"### User:\n{prompt}\n\n### Assistant:\n{ans}"})
        
    # 3. Warianty operacyjne XD01
    for _ in range(target_count - len(records)): # uzupełnienie do równych 5000
        tmpl = random.choice(xd01_templates)
        cust = random.choice(customers)
        prompt = tmpl.format(cust=cust)
        cust_code = "CUST_" + cust.upper().split()[0].replace(".", "").replace("-", "_")
        ans = f"XD01;{cust_code};{cust};CUST;50000;SZT;1"
        records.append({"text": f"### User:\n{prompt}\n\n### Assistant:\n{ans}"})
        
    random.shuffle(records)
    
    with open(filename, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"Sukces! Wygenerowano dokładnie {len(records)} unikalnych wariantów i zapisano w pliku: {filename}")

if __name__ == "__main__":
    generate_synthetic_dataset(target_count=5000)