import re
from typing import List, Dict, Any
from app.database.db_manager import get_sd_tcodes, get_active_company_id

class TCodeService:
    """
    Serwis wyszukiwania i dynamicznego doboru transakcji SAP SD (T-Codes RAG Retriever).
    Umożliwia błyskawiczne odnalezienie odpowiedniej transakcji w bazie 200+ T-Codów
    oraz wstrzyknięcie precyzyjnego kontekstu do promptu LLM.
    """

    KEYWORD_MAPPINGS = {
        'storno': ['VL09', 'VF11'],
        'anulowanie': ['VF11', 'VL09'],
        'pgi': ['VL02N', 'VL09', 'VL06G'],
        'wydanie towaru': ['VL02N', 'VL09', 'VL06G'],
        'kompletacja': ['VL06P', 'VL02N'],
        'picking': ['VL06P', 'VL02N'],
        'kolejka dostaw': ['VL04', 'VL10A'],
        'kolejka faktur': ['VF04', 'VF06'],
        'fakturowanie': ['VF01', 'VF02', 'VF04', 'VFX3'],
        'zablokowane dla księgowości': ['VFX3', 'VF02'],
        'vkoa': ['VKOA', 'VF02'],
        'konta przychodów': ['VKOA', 'OV34'],
        'rodzaj zlecenia': ['VOV8', 'VA01'],
        'auart': ['VOV8', 'VA01'],
        'kategoria pozycji': ['VOV7', 'VOV4'],
        'pstyv': ['VOV7', 'VOV4'],
        'linie harmonogramu': ['VOV6', 'VOV5'],
        'kopiowanie': ['VTAA', 'VTLA', 'VTFL', 'VTFA'],
        'copy control': ['VTAA', 'VTLA', 'VTFL', 'VTFA'],
        'schemat kalkulacji': ['V/08', 'OVKK', 'V/06'],
        'kalkulacja': ['V/08', 'V/06', 'VK11'],
        'ceny': ['VK11', 'VK12', 'V/08', 'V/06'],
        'rabat': ['VK11', 'V/06', 'OV34'],
        'vat': ['VK11', 'V/06', 'VKOA'],
        'podatek': ['VK11', 'V/06', 'VKOA'],
        'punkt wysyłki': ['OVL2', 'VL01N'],
        'trasa': ['OVRO', 'OVRP'],
        'atp': ['OVZ9', 'VA02'],
        'dostępność': ['OVZ9', 'VA02'],
        'kredyt': ['OVA8', 'VKM1', 'VKM3', 'FD32', 'UKM_BP'],
        'limit kredytowy': ['OVA8', 'VKM1', 'VKM3', 'FD32'],
        'blokada kredytowa': ['OVA8', 'VKM1', 'VKM3'],
        'darmowy towar': ['VBN1', 'VBN2'],
        'gratis': ['VBN1', 'VBN2'],
        'podstawienie': ['VB11', 'VB12'],
        'wykluczenie': ['VB01', 'VB02'],
        'listowanie': ['VB01', 'VB02'],
        'kontrakt': ['VA41', 'VA42', 'VA43'],
        'oferta': ['VA21', 'VA22', 'VA23'],
        'zapytanie': ['VA11', 'VA12', 'VA13'],
        'plan dostaw': ['VA31', 'VA32', 'VA33'],
        'transport': ['VT01N', 'VT02N'],
        'niekompletne': ['V.01', 'VA02'],
        'incompletion': ['V.01', 'VUA'],
        'rutyny': ['VOFM'],
        'vofm': ['VOFM']
    }

    @classmethod
    def get_relevant_tcodes_for_prompt(cls, prompt: str, company_id: str = None, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Dobiera najbardziej relewantne kody transakcji dla zadanego pytania konsultanta.
        """
        if not company_id:
            company_id = get_active_company_id()

        prompt_lower = prompt.lower().strip()
        matched_tcode_ids = []

        # 1. Wykrywanie bezpośrednich kodów transakcji w zapytaniu (np. 'VOV8', 'VKOA', 'VL09')
        tokens = re.findall(r'\b[A-Za-z0-9_./\-]{3,12}\b', prompt)
        for tok in tokens:
            tok_upper = tok.upper()
            found = get_sd_tcodes(query=tok_upper, company_id=company_id, limit=3)
            for item in found:
                if item['tcode'].upper() == tok_upper and item['tcode'] not in matched_tcode_ids:
                    matched_tcode_ids.append(item['tcode'])

        # 2. Wykrywanie po słowach kluczowych reguł biznesowych
        for kw, tcodes in cls.KEYWORD_MAPPINGS.items():
            if kw in prompt_lower:
                for tc in tcodes:
                    if tc not in matched_tcode_ids:
                        matched_tcode_ids.append(tc)

        # 3. Jeśli mamy dopasowane T-Codes, pobieramy ich pełne dane
        results = []
        for tc in matched_tcode_ids[:top_k]:
            items = get_sd_tcodes(query=tc, company_id=company_id, limit=1)
            if items:
                results.append(items[0])

        # 4. Jeśli nic nie dopasowano z reguł, wykonaj ogólne wyszukiwanie pełnotekstowe
        if not results:
            clean_words = [w for w in re.split(r'\W+', prompt_lower) if len(w) > 3]
            for w in clean_words[:2]:
                found = get_sd_tcodes(query=w, company_id=company_id, limit=2)
                for item in found:
                    if item['tcode'] not in [r['tcode'] for r in results]:
                        results.append(item)
                if len(results) >= top_k:
                    break

        return results[:top_k]

    @classmethod
    def format_tcodes_for_system_prompt(cls, tcodes: List[Dict[str, Any]]) -> str:
        """
        Formatuje wybrane transakcje do zwięzłego, precyzyjnego bloku dla LLM.
        """
        if not tcodes:
            return ""

        lines = ["RELEWANTNE TRANSAKCJE SAP SD (DYNAMICZNY RETRIEVER):"]
        for t in tcodes:
            spro = f" | SPRO: {t['spro_path']}" if t['spro_path'] else ""
            tables = f" | Tabele: {t['tables_involved']}" if t['tables_involved'] else ""
            lines.append(f"- [{t['tcode']}] {t['name']}: {t['description']}{tables}{spro}")

        return "\n" + "\n".join(lines) + "\n"
