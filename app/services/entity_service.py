import re
from typing import Optional, Dict, Any
from app.database.db_manager import get_db_connection, get_active_company_id

class EntityService:
    @staticmethod
    def extract_quantity(text: str, default: float = 1.0) -> float:
        """
        Wyciąga liczbę sztuk / ilość z tekstu użytkownika.
        Obsługuje wzorce typu: 'na 25 sztuk', 'ilość: 100', '50 kg', '20.5'.
        """
        match = re.search(r'(?:ilość|ilosci|sztuk|szt|kg|litrów|l)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:sztuk|szt|kg|l|litrów)?', text, re.IGNORECASE)
        if match:
            numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
            if numbers:
                try:
                    return float(numbers[0].replace(',', '.'))
                except ValueError:
                    pass
        return default

    @staticmethod
    def find_material(text: str, company_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Wyszukuje indeks materiałowy w bazie sap_materials z uwzględnieniem profilu firmy:
        1. Dopasowanie bezpośredniego kodu indeksu (MATNR)
        2. Dopasowanie po słowach kluczowych z opisu (MAKTX)
        """
        if not company_id:
            company_id = get_active_company_id()
        con = get_db_connection()
        materials = con.execute(
            "SELECT matnr, maktx, mtart, werks, meins, stprs, ktgrm FROM sap_materials WHERE company_id = ?",
            [company_id]
        ).fetchall()
        text_lower = text.lower()

        # 1. Sprawdzenie po kodzie indeksu
        for mat in materials:
            matnr = mat[0]
            if matnr.lower() in text_lower:
                return {
                    "matnr": mat[0],
                    "maktx": mat[1],
                    "mtart": mat[2],
                    "werks": mat[3],
                    "meins": mat[4],
                    "stprs": float(mat[5]),
                    "ktgrm": mat[6]
                }

        # 2. Sprawdzenie po słowach kluczowych z opisu
        for mat in materials:
            maktx = mat[1].lower()
            keywords = [w for w in re.split(r'\W+', maktx) if len(w) > 3]
            for kw in keywords:
                if kw in text_lower:
                    return {
                        "matnr": mat[0],
                        "maktx": mat[1],
                        "mtart": mat[2],
                        "werks": mat[3],
                        "meins": mat[4],
                        "stprs": float(mat[5]),
                        "ktgrm": mat[6]
                    }

        return None

    @staticmethod
    def find_customer(text: str, company_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Wyszukuje kontrahenta w bazie sap_customers w ramach aktywnej firmy:
        1. Po identyfikatorze KUNNR
        2. Po fragmencie nazwy firmy (NAME1)
        """
        if not company_id:
            company_id = get_active_company_id()
        con = get_db_connection()
        customers = con.execute(
            "SELECT kunnr, name1, credit_limit, current_exposure, vkorg, ktgrd FROM sap_customers WHERE company_id = ?",
            [company_id]
        ).fetchall()
        text_lower = text.lower()

        # 1. Po kodzie KUNNR
        for cust in customers:
            kunnr = cust[0]
            if kunnr.lower() in text_lower:
                return {
                    "kunnr": cust[0],
                    "name1": cust[1],
                    "credit_limit": float(cust[2]),
                    "current_exposure": float(cust[3]),
                    "vkorg": cust[4],
                    "ktgrd": cust[5]
                }

        # 2. Po nazwie kontrahenta
        for cust in customers:
            name1 = cust[1].lower()
            name_parts = [p for p in re.split(r'[\s.,-]+', name1) if len(p) > 3 and p not in ['spółka', 'z o.o.', 's.a.', 'ab', 'gmbh']]
            for part in name_parts:
                if part in text_lower:
                    return {
                        "kunnr": cust[0],
                        "name1": cust[1],
                        "credit_limit": float(cust[2]),
                        "current_exposure": float(cust[3]),
                        "vkorg": cust[4],
                        "ktgrd": cust[5]
                    }

        return None
