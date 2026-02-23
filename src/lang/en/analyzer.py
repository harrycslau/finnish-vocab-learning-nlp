from __future__ import annotations

from pipeline.types import LemmaAnalysis


POS_MAP: dict[str, str] = {
    "NOUN": "NOUN",
    "VERB": "VERB",
    "ADJ": "ADJ",
    "ADV": "ADV",
    "PROPN": "PROPN",
    "PRON": "PRON",
    "NUM": "NUM",
    "ADP": "ADP",
    "DET": "PRON",
    "AUX": "VERB",
    "CCONJ": "CONJ",
    "SCONJ": "CONJ",
    "INTJ": "OTHER",
    "PUNCT": "OTHER",
    "SYM": "OTHER",
    "X": "OTHER",
    "N": "NOUN",
    "V": "VERB",
    "A": "ADJ",
    "R": "ADV",
    "P": "PRON",
}


class EnglishAnalyzer:
    def __init__(self, lowercase_fallback: bool = True) -> None:
        try:
            from lemminflect import getAllLemmas
        except ImportError as exc:
            raise RuntimeError(
                "LemmInflect is required for English analysis. Install with: pip install lemminflect"
            ) from exc
        self._get_all_lemmas = getAllLemmas
        self._lowercase_fallback = lowercase_fallback

    def analyze(self, surface_form: str) -> list[LemmaAnalysis]:
        raw = self._get_all_lemmas(surface_form)
        if not raw and self._lowercase_fallback:
            raw = self._get_all_lemmas(surface_form.lower())

        results: list[LemmaAnalysis] = []
        for raw_pos, lemmas in raw.items():
            pos = POS_MAP.get(str(raw_pos).upper())
            if not pos:
                continue
            for lemma in lemmas:
                results.append(LemmaAnalysis(pos=pos, lemma=lemma, source="lemminflect"))

        seen: set[tuple[str, str]] = set()
        unique_results: list[LemmaAnalysis] = []
        for result in results:
            key = (result.pos, result.lemma)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        return unique_results

    def close(self) -> None:
        pass
