import io
import pandas as pd
from app.database.db_manager import get_db_connection, get_active_company_id
from app.models.transaction import SapTransactionItem
from app.services.llm_service import process_llm_query
from app.services.guardrails_service import validate_plant, apply_business_logic
from app.services.entity_service import EntityService

class TransactionService:
    @staticmethod
    def process_text_input(prompt: str, company_id: str = None) -> dict:
        """
        Przetwarza pojedyncze polecenie tekstowe z uwzględnieniem aktywnego profilu firmy:
        - przekazuje do routera / modelu LLM z kontekstem firmy
        - jeśli odpowiedź doradcza -> zwraca typu 'guide'
        - jeśli transakcyjna -> parsuje do SapTransactionItem,
          przypisuje wykrytego kontrahenta, przeprowadza walidację i zapisuje w buforze eksportu.
        """
        if not company_id:
            company_id = get_active_company_id()

        from app.database.db_manager import get_company_profile
        from app.services.error_diagnosis_service import ErrorDiagnosisService
        profile = get_company_profile(company_id)
        structured_diag = ErrorDiagnosisService.diagnose_error_structured(prompt, profile)
        if structured_diag:
            return {
                "type": "diagnosis",
                "content": structured_diag.get("markdown_report", ""),
                "diagnosis": structured_diag
            }

        raw_output = process_llm_query(prompt, company_id=company_id)

        # Sprawdzenie czy to odpowiedź doradcza [GUIDE] lub nietransakcyjna
        if raw_output.startswith('[GUIDE]') or ';' not in raw_output:
            clean_guide = raw_output.replace('[GUIDE]', '').strip()
            return {"type": "guide", "content": clean_guide}

        item = SapTransactionItem.from_csv_line(raw_output)
        if not item:
            return {"type": "guide", "content": raw_output}

        # Wykrycie kontrahenta z promptu w kontekście aktywnego klienta
        customer = EntityService.find_customer(prompt, company_id=company_id)
        if customer:
            item.customer_id = customer['kunnr']

        # 1. Walidacja zakładu i struktur
        item = validate_plant(item)

        # 2. Sprawdzenie reguł biznesowych (ATP, limit kupiecki, próg akceptacji)
        item = apply_business_logic(item)

        # 3. Zapis do bufora eksportu (sap_export)
        con = get_db_connection()
        max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM sap_export").fetchone()[0] + 1
        item.id = max_id

        menge_str = str(int(item.menge)) if item.menge.is_integer() else str(item.menge)
        con.execute(
            "INSERT INTO sap_export (id, company_id, tcode, matnr, maktx, mtart, werks, meins, menge, status, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            [item.id, company_id, item.tcode, item.matnr, item.maktx, item.mtart, item.werks, item.meins, menge_str, item.status, item.notes]
        )

        return {
            "type": "transaction",
            "csv_output": item.to_csv_line(),
            "status": item.status,
            "notes": item.notes,
            "item": item.to_dict(),
            "company_id": company_id
        }

    @staticmethod
    def process_batch_file(file_storage, company_id: str = None) -> int:
        if not company_id:
            company_id = get_active_company_id()

        if file_storage.filename.endswith('.csv'):
            df = pd.read_csv(file_storage)
        else:
            df = pd.read_excel(file_storage)

        count = 0
        for _, row in df.iterrows():
            text_desc = str(row.iloc[0]).strip()
            if not text_desc or text_desc.lower() == 'nan':
                continue

            result = TransactionService.process_text_input(text_desc, company_id=company_id)
            if result.get("type") == "transaction":
                count += 1

        return count

    @staticmethod
    def get_lsmw_export_content(company_id: str = None) -> str:
        con = get_db_connection()
        if company_id:
            rows = con.execute(
                "SELECT tcode, matnr, maktx, mtart, werks, meins, menge "
                "FROM sap_export WHERE company_id = ? AND status IN ('NEW', 'APPROVED')",
                [company_id]
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT tcode, matnr, maktx, mtart, werks, meins, menge "
                "FROM sap_export WHERE status IN ('NEW', 'APPROVED')"
            ).fetchall()

        output = io.StringIO()
        for r in rows:
            output.write("\t".join([str(val) for val in r]) + "\n")
        return output.getvalue()
