from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class TransactionStatus(str, Enum):
    NEW = "NEW"
    APPROVED = "APPROVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PENDING_STOCK = "PENDING_STOCK"
    BLOCKED_CREDIT = "BLOCKED_CREDIT"
    ERROR = "ERROR"


@dataclass
class SapTransactionItem:
    tcode: str
    matnr: str
    maktx: str
    mtart: str = "ROH"
    werks: str = "JAN1"
    meins: str = "SZT"
    menge: float = 1.0
    status: str = TransactionStatus.NEW.value
    notes: str = ""
    id: Optional[int] = None
    created_at: Optional[str] = None
    customer_id: Optional[str] = None

    @classmethod
    def from_csv_line(cls, line: str) -> Optional['SapTransactionItem']:
        """
        Parsuje ciąg w formacie TCODE;MATNR;MAKTX;MTART;WERKS;MEINS;MENGE
        """
        parts = [p.strip() for p in line.strip().split(';')]
        if len(parts) < 7:
            return None
        
        try:
            menge_val = float(parts[6])
        except (ValueError, TypeError):
            menge_val = 1.0

        return cls(
            tcode=parts[0],
            matnr=parts[1],
            maktx=parts[2],
            mtart=parts[3],
            werks=parts[4],
            meins=parts[5],
            menge=menge_val
        )

    def to_csv_line(self) -> str:
        """
        Zwraca reprezentację w standardowym formacie CSV z separatorem ';'
        """
        # Jeśli liczba jest całkowita, wyświetl bez części dziesiętnej
        menge_str = str(int(self.menge)) if self.menge.is_integer() else str(self.menge)
        return f"{self.tcode};{self.matnr};{self.maktx};{self.mtart};{self.werks};{self.meins};{menge_str}"

    def to_lsmw_tsv(self) -> str:
        """
        Zwraca reprezentację zgodną z wsadem LSMW / Batch Input (rozdzielana tabulatorami)
        """
        menge_str = str(int(self.menge)) if self.menge.is_integer() else str(self.menge)
        return f"{self.tcode}\t{self.matnr}\t{self.maktx}\t{self.mtart}\t{self.werks}\t{self.meins}\t{menge_str}"

    def to_dict(self) -> dict:
        return asdict(self)
