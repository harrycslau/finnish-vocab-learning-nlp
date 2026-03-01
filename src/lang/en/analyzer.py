from __future__ import annotations

from pathlib import Path

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
    "DET": "DET",
    "PART": "PART",
    "AUX": "VERB",
    "CCONJ": "CCONJ",
    "SCONJ": "SCONJ",
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

OPEN_CLASS_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV", "NUM"}
CLOSED_CLASS_POS = {"PRON", "DET", "ADP", "PART", "AUX", "CCONJ", "SCONJ", "OTHER"}


class EnglishAnalyzer:
    def __init__(
        self,
        lowercase_fallback: bool = True,
        spacy_model: str = "en_core_web_sm",
        spacy_model_path: str | None = None,
    ) -> None:
        try:
            from lemminflect import getAllLemmas
        except ImportError as exc:
            raise RuntimeError(
                "LemmInflect is required for English analysis. Install with: pip install lemminflect"
            ) from exc
        try:
            import spacy
        except ImportError as exc:
            raise RuntimeError("spaCy is required for English fallback analysis. Install with: pip install spacy") from exc

        try:
            self._nlp = spacy.load(spacy_model)
        except OSError:
            if spacy_model_path and Path(spacy_model_path).exists():
                self._nlp = spacy.load(spacy_model_path)
            else:
                msg = f"spaCy model '{spacy_model}' not found."
                if spacy_model_path:
                    msg += f" Fallback path missing: {spacy_model_path}"
                raise RuntimeError(msg)

        self._get_all_lemmas = getAllLemmas
        self._lowercase_fallback = lowercase_fallback

    def _spacy_analyses(self, surface_form: str) -> list[LemmaAnalysis]:
        results: list[LemmaAnalysis] = []
        doc = self._nlp(surface_form)
        for token in doc:
            pos = POS_MAP.get(token.pos_.upper(), token.pos_.upper())
            # PTB determiner/possessive tags should resolve to DET.
            if token.tag_ in {"DT", "WDT", "PDT", "PRP$"}:
                pos = "DET"
            lemma = token.lemma_ if token.lemma_ else token.text.lower()
            results.append(LemmaAnalysis(pos=pos, lemma=lemma, source="spacy_fallback"))
        return results

    def analyze(self, surface_form: str) -> list[LemmaAnalysis]:
        if "-" in surface_form:
            return [LemmaAnalysis(pos="OTHER", lemma=surface_form, source="hyphen_rule")]

        raw = self._get_all_lemmas(surface_form)
        if not raw and self._lowercase_fallback:
            raw = self._get_all_lemmas(surface_form.lower())

        spacy_results = self._spacy_analyses(surface_form)
        spacy_primary_pos = spacy_results[0].pos if spacy_results else "OTHER"

        results: list[LemmaAnalysis] = []
        if spacy_primary_pos in CLOSED_CLASS_POS:
            results = spacy_results
        else:
            for raw_pos, lemmas in raw.items():
                pos = POS_MAP.get(str(raw_pos).upper())
                if pos not in OPEN_CLASS_POS:
                    continue
                for lemma in lemmas:
                    results.append(LemmaAnalysis(pos=pos, lemma=lemma, source="lemminflect"))
            if not results:
                results = spacy_results

        if surface_form.endswith("'s") or surface_form.endswith("’s"):
            results = [
                r for r in results if not (r.pos == "PART" and r.lemma in {"'s", "’s"})
            ]

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
