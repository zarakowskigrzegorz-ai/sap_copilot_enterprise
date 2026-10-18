from app.database.db_manager import get_db_connection
from app.config import Config
from app.models.transaction import SapTransactionItem, TransactionStatus

def validate_plant(item: SapTransactionItem) -> SapTransactionItem:
    """
    Weryfikuje istnienie zakładu (WERKS) w bazie materiałowej.
    W razie braku, podstawia domyślny poprawny zakład.
    """
    con = get_db_connection()
    if item.werks != 'AUTO':
        plant_exists = con.execute("SELECT COUNT(*) FROM sap_materials WHERE werks = ?", [item.werks]).fetchone()[0]
        if plant_exists == 0:
            valid_plant = con.execute("SELECT werks FROM sap_materials LIMIT 1").fetchone()
            if valid_plant:
                item.werks = valid_plant[0]
    return item

def apply_business_logic(item: SapTransactionItem) -> SapTransactionItem:
    """
    Stosuje reguły biznesowe SAP:
    1. Obliczenie wartości pozycji w oparciu o cenę ewidencyjną (STPRS).
    2. Wymóg akceptacji menedżerskiej powyżej progu z Config.APPROVAL_THRESHOLD_PLN.
    3. Kontrola dostępności zapasów (ATP) dla zleceń sprzedaży (VA01).
    4. Kontrola limitu kupieckiego kontrahenta (SD Credit Management).
    """
    con = get_db_connection()
    status = TransactionStatus.NEW.value
    notes = []

    # 1. Pobranie ceny jednostkowej
    mat_row = con.execute("SELECT stprs FROM sap_materials WHERE matnr = ?", [item.matnr]).fetchone()
    price = float(mat_row[0]) if mat_row and mat_row[0] else Config.DEFAULT_PRICE_PLN
    total_value = item.menge * price
    notes.append(f"Wartość: {total_value:.2f} PLN (Cena jedn.: {price} PLN)")

    # 2. Weryfikacja progu menedżerskiego
    if total_value > Config.APPROVAL_THRESHOLD_PLN:
        status = TransactionStatus.PENDING_APPROVAL.value
        notes.append(f"⚠️ Przekroczono próg {Config.APPROVAL_THRESHOLD_PLN:.0f} PLN – wymagana akceptacja menedżerska.")

    # 3. Weryfikacja dostępności ATP dla zleceń sprzedaży
    if item.tcode in ['VA01']:
        stock_row = con.execute("SELECT labst FROM sap_stock WHERE matnr = ? AND werks = ?", [item.matnr, item.werks]).fetchone()
        stock_qty = float(stock_row[0]) if stock_row else 0.0
        if item.menge > stock_qty:
            status = TransactionStatus.PENDING_STOCK.value
            notes.append(f"❌ Brak wystarczającego stanu! Dostępne: {stock_qty} {item.meins}")
        else:
            notes.append(f"✅ Stan magazynowy OK ({stock_qty} {item.meins})")

    # Dla przyjęcia zewnętrznego MIGO (Ruch 101) - informacja o powiększeniu stanu
    elif item.tcode == 'MIGO':
        stock_row = con.execute("SELECT labst FROM sap_stock WHERE matnr = ? AND werks = ?", [item.matnr, item.werks]).fetchone()
        stock_qty = float(stock_row[0]) if stock_row else 0.0
        notes.append(f"📥 Przyjęcie towaru (Aktualny stan magazynowy przed PZ: {stock_qty} {item.meins})")

    # 4. Weryfikacja limitu kredytowego
    if item.tcode == 'VA01':
        # Jeśli wskazano konkretnego klienta w item, szukaj po ID, w przeciwnym razie domyślny pierwszy
        if item.customer_id:
            cust_row = con.execute("SELECT credit_limit, current_exposure, name1 FROM sap_customers WHERE kunnr = ?", [item.customer_id]).fetchone()
        else:
            cust_row = con.execute("SELECT credit_limit, current_exposure, name1 FROM sap_customers LIMIT 1").fetchone()

        if cust_row:
            credit_limit, current_exposure, cust_name = float(cust_row[0]), float(cust_row[1]), cust_row[2]
            if current_exposure + total_value > credit_limit:
                status = TransactionStatus.BLOCKED_CREDIT.value
                notes.append(f"⛔ Blokada kredytowa ({cust_name})! Limit: {credit_limit:.2f} PLN, bieżąca ekspozycja: {current_exposure:.2f} PLN")
            else:
                remaining = credit_limit - (current_exposure + total_value)
                notes.append(f"✅ Limit kredytowy ({cust_name}) OK (Pozostało: {remaining:.2f} PLN)")

    item.status = status
    item.notes = " | ".join(notes)
    return item

# --- Funkcje zgodności wstecznej (Backward compatibility) ---
def validate_with_duckdb(csv_output: str) -> str:
    item = SapTransactionItem.from_csv_line(csv_output)
    if item:
        item = validate_plant(item)
        return item.to_csv_line()
    return csv_output

def apply_business_logic_legacy(csv_output: str):
    item = SapTransactionItem.from_csv_line(csv_output)
    if item:
        item = apply_business_logic(item)
        return item.to_csv_line(), item.status, item.notes
    return csv_output, "ERROR", "Nieprawidłowy format linii CSV"
