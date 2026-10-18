# ⚡ SAP SD Enterprise Copilot (S/4HANA Order-to-Cash Assistant)

Zaawansowany asystent konsultanta **SAP S/4HANA Sales and Distribution (SD)** łączący deterministyczne silniki diagnostyczne SAP z lokalnym modelem językowym (Ollama / QLoRA) oraz bazą analityczną **DuckDB**.

## 🚀 Główne moduły i możliwości

1. **💬 Asystent Konsultanta SAP SD & Karty Ekspertyz Błędów**:
   - Natychmiastowa diagnostyka **18+ krytycznych błędów Order-to-Cash** (m.in. `VF067`, `V1382`, `FF704`, `VL150`, `M7021`, `V1042`, `V2015`, `VF072`, `VK104`, `VP199`, `V1208`) z podziałem na warianty naprawcze (*Wariant A – Szybki Fix*, *Wariant B – Konfiguracja SPRO*, *Wariant C – Rozwiązanie Docelowe*).
   - Izolowana pamięć kontekstowa **Smart Memory** (`ai_memory`) ucząca się specyficznych reguł i kodów `Z*` dla każdego obsługiwanego przedsiębiorstwa.

2. **🩺 VKOA Account Determination Troubleshooter (`KOFI00`) & 💰 Symulator Wyceny (`V/08` ➔ `VKOA`)**:
   - **Symulator `KOFI00`**: Krok po kroku weryfikuje tabele dostępu `001` – `005` (`C001`–`C005`) dla kombinacji `KTOPL / VKORG / KTGRD / KTGRM / KVSL` i generuje **1-Click Quick-Fix** dopisujący brakujące konto księgi głównej (`SAKNR`).
   - **Symulator Procedury Wyceny `V/08` (`PRCD_ELEMENTS`)**: Przelicza kaskadę warunków cenowych (`PR00`/`ZPR1` ➔ `K004`/`K007`/`ZREB` ➔ `NETWR` ➔ `KF00`/`ZFRE` ➔ `MWST` ➔ `VPRS` ➔ `BRUTTO`) i automatycznie sprawdza determinację kont FI w `VKOA` dla każdego aktywnego klucza konta (`ERL`, `ERS`, `ERF`, `MWS`).

3. **🛡️ Master Data Governance (MDG) & 1-Click Auto-Fix**:
   - Audyt gotowości kartotek klientów (`KNA1/KNVV/KNVI`), materiałów (`MARA/MVKE/MARC`), dostawców/podwykonawców (`LFA1/LFM1`) oraz matrycy `VKOA`.
   - Przycisk **⚡ Auto-Fix MDG (100%)** automatycznie uzupełniający brakujące grupy `KTGRD`, `KTGRM`, klasyfikacje `TAXKD`, reguły `Incoterms`, grupy `MTVFP (ATP)` oraz brakujące wpisy w Tabeli `001` VKOA.
   - Import/eksport danych podstawowych z plików CSV (`SE16N`, `MM60`, `VCUST`) oraz generator próbki korporacyjnej (**3 500 pozycji zleceń `VBAK/VBAP`**).

4. **🔄 Auto-Discovery Procesów Biznesowych & Cross-Module Document Flow**:
   - Automatyczne wykrywanie **10 procesów przedsiębiorstwa** na podstawie kartotek SAP (*MTS*, *MTO `TAK`*, *Handel Trójstronny `TAS`/`BANF`*, *Kooperacja z podwykonawstwem ruch `541`*, *Konsygnacja `KB/KE/KR/KA`*, *Intercompany `IV`/`PI01`*, *Usługi `DP90`*, *Fakturowanie zaliczkowe `FAZ`*, *Reklamacje `RE/G2/L2`*, *Eksport/WDT*).
   - Wizualna oś czasu przepływu dokumentów (**Document Flow Timeline**) obejmująca moduły `SD`, `MM`, `PP`, `FI`, `CO`, `PS` i `QM`.

5. **🔍 Katalog 200+ Transakcji SAP SD & SPRO (Spotlight Search `⌘K`)**:
   - Błyskawiczna wyszukiwarka ponad 200 transakcji SAP SD, tabel systemowych i ścieżek SPRO z możliwością dodawania własnych transakcji `Z* / Y*`.

---

## 🛠️ Uruchomienie lokalne

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Aplikacja uruchomi się pod adresem `http://127.0.0.1:5001` (domyślny kod PIN ekranu blokady: `2026` lub autoryzacja `Face ID`).
