import re
from app.database.db_manager import get_db_connection, get_company_profile, get_active_company_id

class VkoaTroubleshooterService:
    """
    Moduł diagnostyczny dla SAP SD: Ustalanie kont przychodów (Account Determination VKOA).
    Analizuje błędy księgowania faktur VF01 / VF02 / VFX3 (np. błąd VF067:
    'Account determination for entry ... not possible').
    Symuluje standardową sekwencję dostępu KOFI00 w tabelach 001 - 005.
    """

    ACCESS_TABLES_METADATA = {
        '001': {
            'name': 'Tabela 001: Klient / Materiał / Klucz konta',
            'fields': ['ktopl', 'vkorg', 'ktgrd_cust', 'ktgrm_mat', 'kvsl'],
            'description': 'Najbardziej szczegółowy poziom alokacji przychodów (AAG Klienta + AAG Materiału + Klucz konta)'
        },
        '002': {
            'name': 'Tabela 002: Klient / Klucz konta',
            'fields': ['ktopl', 'ktgrd_cust', 'kvsl'],
            'description': 'Alokacja wg grupy rozliczeniowej klienta (np. kraj vs zagranica) niezależnie od materiału'
        },
        '003': {
            'name': 'Tabela 003: Materiał / Klucz konta',
            'fields': ['ktopl', 'ktgrm_mat', 'kvsl'],
            'description': 'Alokacja wg grupy rozliczeniowej materiału (np. towary handlowe vs wyroby gotowe vs usługi)'
        },
        '005': {
            'name': 'Tabela 005: Obszar sprzedaży / Klucz konta',
            'fields': ['ktopl', 'vkorg', 'kvsl'],
            'description': 'Alokacja wg jednostki sprzedaży (VKORG) i klucza konta'
        },
        '004': {
            'name': 'Tabela 004: Ogólny klucz konta (Fallback)',
            'fields': ['ktopl', 'kvsl'],
            'description': 'Domyślne konto księgi głównej dla danego klucza konta (ostatnia deska ratunku)'
        }
    }

    SUGGESTED_ACCOUNTS_MAP = {
        'INT': {
            'ERL': {
                '01': {'01': '800000', '02': '800100', '03': '800300'},
                '02': {'01': '800200', '02': '800250', '03': '800350'},
                'default': '800000'
            },
            'ERS': {'default': '809000'},
            'MWS': {'default': '175000'},
            'ERF': {'default': '805000'}
        },
        'SE01': {
            'ERL': {
                '01': {'01': '300000', '02': '300050', '03': '300100'},
                '02': {'01': '300200', '02': '300250', '03': '300300'},
                'default': '300000'
            },
            'ERS': {'default': '374000'},
            'MWS': {'default': '261000'},
            'ERF': {'default': '352000'}
        }
    }

    @classmethod
    def parse_error_string(cls, raw_input: str, default_ktopl: str = 'INT', default_vkorg: str = '1000') -> dict:
        """
        Parsuje log błędu z SAP (np. VF067, FF704) lub swobodny ciąg konsultanta.
        Przykłady wejścia:
        - "VF067: Account determination for entry INT 1000 01 02 ERL not possible"
        - "Błąd VF067 brak ustalenia konta INT 1000 01 02 ERL"
        - "KTOPL: INT, VKORG: 1000, KTGRD: 01, KTGRM: 02, KVSL: ERL"
        """
        text = raw_input.strip()
        result = {
            'ktopl': default_ktopl,
            'vkorg': default_vkorg,
            'ktgrd_cust': '01',
            'ktgrm_mat': '01',
            'kvsl': 'ERL',
            'appl': 'V',
            'kschl': 'KOFI',
            'raw_parsed': False
        }

        # 1. Wzorzec typowy dla SAP VF067: "... entry KTOPL VKORG KTGRD KTGRM KVSL ..."
        match_vf067 = re.search(
            r'(?:VF\s*0?67|FF\s*704|entry|wpisu|dla)\s+([A-Z0-9]{3,4})\s+([A-Z0-9]{2,4})\s+([0-9]{2})\s+([0-9]{2})\s+([A-Z0-9]{3})',
            text,
            re.IGNORECASE
        )
        if match_vf067:
            result['ktopl'] = match_vf067.group(1).upper()
            result['vkorg'] = match_vf067.group(2).upper()
            result['ktgrd_cust'] = match_vf067.group(3)
            result['ktgrm_mat'] = match_vf067.group(4)
            result['kvsl'] = match_vf067.group(5).upper()
            result['raw_parsed'] = True
            return result

        # 2. Wzorzec z separatorami slash lub myślnik: INT/1000/01/02/ERL
        match_slash = re.search(
            r'([A-Z0-9]{3,4})[/\-]([A-Z0-9]{2,4})[/\-]([0-9]{2})[/\-]([0-9]{2})[/\-]([A-Z0-9]{3})',
            text,
            re.IGNORECASE
        )
        if match_slash:
            result['ktopl'] = match_slash.group(1).upper()
            result['vkorg'] = match_slash.group(2).upper()
            result['ktgrd_cust'] = match_slash.group(3)
            result['ktgrm_mat'] = match_slash.group(4)
            result['kvsl'] = match_slash.group(5).upper()
            result['raw_parsed'] = True
            return result

        # 3. Wyszukiwanie par klucz-wartość (KTOPL=..., VKORG=...)
        ktopl_m = re.search(r'KTOPL[:=\s]+([A-Z0-9]{3,4})', text, re.IGNORECASE)
        vkorg_m = re.search(r'VKORG[:=\s]+([A-Z0-9]{2,4})', text, re.IGNORECASE)
        ktgrd_m = re.search(r'KTGRD[:=\s]+([0-9]{2})', text, re.IGNORECASE)
        ktgrm_m = re.search(r'KTGRM[:=\s]+([0-9]{2})', text, re.IGNORECASE)
        kvsl_m = re.search(r'(?:KVSL|KFRST|KLUCZ)[:=\s]+([A-Z0-9]{3})', text, re.IGNORECASE)

        if ktopl_m: result['ktopl'] = ktopl_m.group(1).upper(); result['raw_parsed'] = True
        if vkorg_m: result['vkorg'] = vkorg_m.group(1).upper(); result['raw_parsed'] = True
        if ktgrd_m: result['ktgrd_cust'] = ktgrd_m.group(1); result['raw_parsed'] = True
        if ktgrm_m: result['ktgrm_mat'] = ktgrm_m.group(1); result['raw_parsed'] = True
        if kvsl_m: result['kvsl'] = kvsl_m.group(1).upper(); result['raw_parsed'] = True

        return result

    @classmethod
    def simulate_account_determination(
        cls,
        company_id: str,
        ktopl: str,
        vkorg: str,
        ktgrd_cust: str,
        ktgrm_mat: str,
        kvsl: str,
        appl: str = 'V',
        kschl: str = 'KOFI'
    ) -> dict:
        """
        Symuluje standardową sekwencję dostępu SAP KOFI00 dla aktywnego profilu klienta.
        Kolejność weryfikacji tabel VKOA:
        1. Tabela 001 (KTOPL + VKORG + KTGRD + KTGRM + KVSL)
        2. Tabela 002 (KTOPL + KTGRD + KVSL)
        3. Tabela 003 (KTOPL + KTGRM + KVSL)
        4. Tabela 005 (KTOPL + VKORG + KVSL)
        5. Tabela 004 (KTOPL + KVSL)
        """
        con = get_db_connection()
        sequence_steps = []
        determined_account = None
        matched_table = None
        matched_rule = None

        # Definicja sekwencji kroków SAP VKOA
        access_sequence = [
            {
                'step': 1,
                'table_num': '001',
                'name': cls.ACCESS_TABLES_METADATA['001']['name'],
                'query': """
                    SELECT id, saknr, description FROM sd_vkoa_rules 
                    WHERE company_id = ? AND table_num = '001' AND ktopl = ? AND vkorg = ? 
                      AND ktgrd_cust = ? AND ktgrm_mat = ? AND kvsl = ?
                """,
                'params': [company_id, ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl],
                'evaluated_keys': {
                    'Plan kont (KTOPL)': ktopl,
                    'Jedn. sprzedaży (VKORG)': vkorg,
                    'Grupa klienta (KTGRD)': ktgrd_cust,
                    'Grupa materiału (KTGRM)': ktgrm_mat,
                    'Klucz konta (KVSL)': kvsl
                }
            },
            {
                'step': 2,
                'table_num': '002',
                'name': cls.ACCESS_TABLES_METADATA['002']['name'],
                'query': """
                    SELECT id, saknr, description FROM sd_vkoa_rules 
                    WHERE company_id = ? AND table_num = '002' AND ktopl = ? 
                      AND ktgrd_cust = ? AND kvsl = ?
                """,
                'params': [company_id, ktopl, ktgrd_cust, kvsl],
                'evaluated_keys': {
                    'Plan kont (KTOPL)': ktopl,
                    'Grupa klienta (KTGRD)': ktgrd_cust,
                    'Klucz konta (KVSL)': kvsl
                }
            },
            {
                'step': 3,
                'table_num': '003',
                'name': cls.ACCESS_TABLES_METADATA['003']['name'],
                'query': """
                    SELECT id, saknr, description FROM sd_vkoa_rules 
                    WHERE company_id = ? AND table_num = '003' AND ktopl = ? 
                      AND ktgrm_mat = ? AND kvsl = ?
                """,
                'params': [company_id, ktopl, ktgrm_mat, kvsl],
                'evaluated_keys': {
                    'Plan kont (KTOPL)': ktopl,
                    'Grupa materiału (KTGRM)': ktgrm_mat,
                    'Klucz konta (KVSL)': kvsl
                }
            },
            {
                'step': 4,
                'table_num': '005',
                'name': cls.ACCESS_TABLES_METADATA['005']['name'],
                'query': """
                    SELECT id, saknr, description FROM sd_vkoa_rules 
                    WHERE company_id = ? AND table_num = '005' AND ktopl = ? 
                      AND vkorg = ? AND kvsl = ?
                """,
                'params': [company_id, ktopl, vkorg, kvsl],
                'evaluated_keys': {
                    'Plan kont (KTOPL)': ktopl,
                    'Jedn. sprzedaży (VKORG)': vkorg,
                    'Klucz konta (KVSL)': kvsl
                }
            },
            {
                'step': 5,
                'table_num': '004',
                'name': cls.ACCESS_TABLES_METADATA['004']['name'],
                'query': """
                    SELECT id, saknr, description FROM sd_vkoa_rules 
                    WHERE company_id = ? AND table_num = '004' AND ktopl = ? 
                      AND kvsl = ?
                """,
                'params': [company_id, ktopl, kvsl],
                'evaluated_keys': {
                    'Plan kont (KTOPL)': ktopl,
                    'Klucz konta (KVSL)': kvsl
                }
            }
        ]

        # Iteracja po sekwencji dostępu
        for access in access_sequence:
            row = con.execute(access['query'], access['params']).fetchone()
            if row:
                status = "FOUND"
                account = row[1]
                rule_id = row[0]
                rule_desc = row[2]
                if not determined_account:
                    determined_account = account
                    matched_table = access['table_num']
                    matched_rule = {
                        'id': rule_id,
                        'table_num': access['table_num'],
                        'saknr': account,
                        'description': rule_desc
                    }
            else:
                status = "NOT_FOUND"
                account = None

            sequence_steps.append({
                'step': access['step'],
                'table_num': access['table_num'],
                'table_name': access['name'],
                'status': status,
                'account': account,
                'keys': access['evaluated_keys'],
                'description': cls.ACCESS_TABLES_METADATA[access['table_num']]['description']
            })

            # Jeśli konto znalezione, standardowy SAP przerywa dalsze przeszukiwanie sekwencji (Exclusive access)
            if determined_account:
                break

        # Ustalenie statusu końcowego
        if determined_account:
            return {
                'success': True,
                'status': 'DETERMINED',
                'account': determined_account,
                'matched_table': matched_table,
                'rule_details': matched_rule,
                'steps': sequence_steps,
                'company_id': company_id,
                'inputs': {
                    'ktopl': ktopl,
                    'vkorg': vkorg,
                    'ktgrd_cust': ktgrd_cust,
                    'ktgrm_mat': ktgrm_mat,
                    'kvsl': kvsl,
                    'appl': appl,
                    'kschl': kschl
                },
                'message': f"✅ Ustalanie konta powiodło się! Wyznaczono konto KG: {determined_account} w Tabeli {matched_table}."
            }
        else:
            # Propozycja konta i rozwiązanie
            suggested_acc = cls._suggest_account(ktopl, kvsl, ktgrd_cust, ktgrm_mat)
            quick_fix_data = {
                'company_id': company_id,
                'table_num': '001',
                'ktopl': ktopl,
                'vkorg': vkorg,
                'ktgrd_cust': ktgrd_cust,
                'ktgrm_mat': ktgrm_mat,
                'kvsl': kvsl,
                'saknr': suggested_acc,
                'description': f"Auto-Fix VKOA dla {kvsl} ({ktgrd_cust}/{ktgrm_mat})"
            }

            expert_guide = cls._generate_expert_guide(
                ktopl, vkorg, ktgrd_cust, ktgrm_mat, kvsl, suggested_acc
            )

            return {
                'success': False,
                'status': 'FAILED',
                'error_code': 'VF067',
                'account': None,
                'matched_table': None,
                'steps': sequence_steps,
                'company_id': company_id,
                'inputs': {
                    'ktopl': ktopl,
                    'vkorg': vkorg,
                    'ktgrd_cust': ktgrd_cust,
                    'ktgrm_mat': ktgrm_mat,
                    'kvsl': kvsl,
                    'appl': appl,
                    'kschl': kschl
                },
                'missing_combination': f"{ktopl} / {vkorg} / AAG Klienta: {ktgrd_cust} / AAG Materiału: {ktgrm_mat} / Klucz: {kvsl}",
                'suggested_account': suggested_acc,
                'quick_fix': quick_fix_data,
                'expert_guide': expert_guide,
                'message': f"❌ Błąd VF067: Brak wpisu w VKOA dla kombinacji: Plan kont {ktopl}, Jedn. {vkorg}, Klient {ktgrd_cust}, Materiał {ktgrm_mat}, Klucz {kvsl}."
            }

    @classmethod
    def apply_quick_fix(cls, fix_data: dict) -> dict:
        """
        Dodaje brakujący wpis do tabeli sd_vkoa_rules aktywnego klienta w DuckDB
        i natychmiast re-symuluje determinację konta.
        """
        con = get_db_connection()
        company_id = fix_data.get('company_id') or get_active_company_id()
        table_num = fix_data.get('table_num', '001')
        ktopl = fix_data.get('ktopl', 'INT')
        vkorg = fix_data.get('vkorg', '1000')
        ktgrd = fix_data.get('ktgrd_cust', '01')
        ktgrm = fix_data.get('ktgrm_mat', '01')
        kvsl = fix_data.get('kvsl', 'ERL')
        saknr = fix_data.get('saknr', '800000')
        desc = fix_data.get('description', f"Wpis VKOA dla {kvsl}")

        # Generowanie ID
        count = con.execute("SELECT COUNT(*) FROM sd_vkoa_rules").fetchone()[0]
        rule_id = f"VK_FIX_{company_id}_{count + 1}"

        con.execute("""
            INSERT INTO sd_vkoa_rules (
                id, company_id, appl, kschl, table_num, ktopl, vkorg, 
                ktgrd_cust, ktgrm_mat, kvsl, saknr, hkont_accrual, description
            ) VALUES (?, ?, 'V', 'KOFI', ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        """, [rule_id, company_id, table_num, ktopl, vkorg, ktgrd, ktgrm, kvsl, saknr, desc])

        # Ponowna symulacja
        simulation = cls.simulate_account_determination(
            company_id=company_id,
            ktopl=ktopl,
            vkorg=vkorg,
            ktgrd_cust=ktgrd,
            ktgrm_mat=ktgrm,
            kvsl=kvsl
        )
        simulation['quick_fix_applied'] = True
        simulation['new_rule_id'] = rule_id
        return simulation

    @classmethod
    def _suggest_account(cls, ktopl: str, kvsl: str, ktgrd: str, ktgrm: str) -> str:
        accounts = cls.SUGGESTED_ACCOUNTS_MAP.get(ktopl, cls.SUGGESTED_ACCOUNTS_MAP['INT'])
        key_group = accounts.get(kvsl, accounts.get('ERL'))
        if isinstance(key_group, dict):
            cust_dict = key_group.get(ktgrd)
            if isinstance(cust_dict, dict):
                return cust_dict.get(ktgrm, key_group.get('default', '800000'))
            return key_group.get('default', '800000')
        return '800000'

    @classmethod
    def _generate_expert_guide(cls, ktopl: str, vkorg: str, ktgrd: str, ktgrm: str, kvsl: str, suggested_acc: str) -> dict:
        return {
            'tcode': 'VKOA',
            'spro_path': 'SPRO -> Sprzedaż i dystrybucja -> Funkcje podstawowe -> Ustalanie kont/Koszty -> Ustalanie kont przychodów -> Zdefiniuj przypisanie kont',
            'analysis_tcode': 'VF02',
            'analysis_steps': [
                'Uruchom transakcję VF02 dla faktury zablokowanej dla księgowości',
                'Wybierz z menu górnego: Środowisko (Environment) -> Analiza ustalania kont (Account determination analysis) -> Konta przychodów (Revenue accounts)',
                'Rozwiń gałąź warunku (np. PR00 lub KOFI) i sprawdź, który krok sekwencji zgłasza żółty/czerwony status'
            ],
            'master_data_checks': [
                f"Sprawdź kartotekę odbiorcy w KNVV: pole KTGRD (aktualnie przekazane: {ktgrd}). Zmiana w transakcji BP / XD02 na zakładce Faktura.",
                f"Sprawdź kartotekę materiałową w MVKE: pole KTGRM (aktualnie przekazane: {ktgrm}). Zmiana w transakcji MM02 na widoku Sprzedaż 2."
            ],
            'recommended_fix_row': {
                'Aplikacja': 'V (Sprzedaż/Dystrybucja)',
                'Rodzaj warunku': 'KOFI (z przypisaniem konta CO)',
                'Tabela': '001 (Klient/Materiał/Klucz konta)',
                'Plan kont (KTOPL)': ktopl,
                'Jedn. sprzedaży (VKORG)': vkorg,
                'Grupa klienta (KTGRD)': ktgrd,
                'Grupa materiału (KTGRM)': ktgrm,
                'Klucz konta (KVSL)': kvsl,
                'Konto KG (SAKNR)': suggested_acc
            }
        }
