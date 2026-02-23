from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class LemmaAnalysis:
    pos: str
    lemma: str
    source: str = ""


@runtime_checkable
class Analyzer(Protocol):
    def analyze(self, surface_form: str) -> Sequence[LemmaAnalysis]:
        ...

    def close(self) -> None:
        ...

