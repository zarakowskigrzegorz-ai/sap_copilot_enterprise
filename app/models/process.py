from dataclasses import dataclass, asdict


@dataclass
class ProcessStep:
    step: int
    tcode: str
    desc: str
    prereq: str
    tables: str

    def to_dict(self) -> dict:
        return asdict(self)
