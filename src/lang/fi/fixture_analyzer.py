from __future__ import annotations

from pipeline.types import LemmaAnalysis


class FixtureFinnishAnalyzer:
    """Deterministic analyzer for CI parity fixtures."""

    def __init__(self) -> None:
        self._mapping: dict[str, list[LemmaAnalysis]] = {
            "koira": [LemmaAnalysis(pos="NOUN", lemma="koira", source="fixture")],
            "koirat": [LemmaAnalysis(pos="NOUN", lemma="koira", source="fixture")],
            "juoksi": [LemmaAnalysis(pos="VERB", lemma="juosta", source="fixture")],
            "juoksee": [LemmaAnalysis(pos="VERB", lemma="juosta", source="fixture")],
            "on": [LemmaAnalysis(pos="VERB", lemma="olla", source="fixture")],
            "kuusi": [
                LemmaAnalysis(pos="NUM", lemma="kuusi_num", source="fixture"),
                LemmaAnalysis(pos="NOUN", lemma="kuusi_tree", source="fixture"),
            ],
        }

    def analyze(self, surface_form: str) -> list[LemmaAnalysis]:
        return self._mapping.get(surface_form, [])

    def close(self) -> None:
        pass

