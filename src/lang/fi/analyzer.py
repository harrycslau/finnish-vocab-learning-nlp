from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pipeline.types import LemmaAnalysis


def map_voikko_pos(analysis: dict[str, Any]) -> str | None:
    v_class = analysis.get("CLASS", "")
    v_sijamuoto = analysis.get("SIJAMUOTO", "")

    if v_class == "nimisana":
        return "NOUN"
    if v_class in ["etunimi", "sukunimi", "paikannimi"]:
        return "PROPN"
    if v_class in ["teonsana", "kieltosana"]:
        return "VERB"
    if v_class in ["laatusana", "nimisana_laatusana"]:
        standard_cases = {
            "nimento",
            "osanto",
            "sisaolento",
            "omanto",
            "ulkoolento",
            "sisaantulento",
        }
        if v_sijamuoto in standard_cases:
            return "ADJ"
    if v_class == "seikkasana":
        return "ADV"
    if v_class in ["laatusana", "nimisana_laatusana"] and v_sijamuoto in ["kerrontosti", "keinonto"]:
        return "ADV"
    if v_class == "asemosana":
        return "PRON"
    if v_class == "lukusana":
        return "NUM"
    if v_class == "suhdesana":
        return "ADP"
    if v_class == "sidesana":
        return "CONJ"
    if v_class in ["huudahdussana"]:
        return "OTHER"
    return None


def map_spacy_pos(spacy_pos: str) -> str | None:
    if spacy_pos == "AUX":
        return "VERB"
    valid_tags = {"NOUN", "PROPN", "VERB", "ADJ", "ADV", "PRON", "NUM", "ADP"}
    if spacy_pos in valid_tags:
        return spacy_pos
    if spacy_pos in ["CCONJ", "SCONJ"]:
        return "CONJ"
    if spacy_pos in ["INTJ", "PUNCT", "SYM", "X"]:
        return "OTHER"
    return None


class FinnishAnalyzer:
    def __init__(
        self,
        voikko_language: str = "fi",
        voikko_library_path: str | None = "/opt/homebrew/opt/libvoikko/lib",
        spacy_model: str = "fi_core_news_md",
        spacy_model_path: str | None = None,
    ) -> None:
        try:
            from libvoikko import Voikko
        except ImportError as exc:
            raise RuntimeError("libvoikko is required for Finnish analysis. Install with: pip install libvoikko") from exc

        try:
            import spacy
        except ImportError as exc:
            raise RuntimeError("spaCy is required for Finnish analysis. Install with: pip install spacy") from exc

        if voikko_library_path:
            library_dir = Path(voikko_library_path)
            if library_dir.exists():
                Voikko.setLibrarySearchPath(str(library_dir))

        try:
            self._voikko = Voikko(voikko_language)
        except Exception as exc:  # pragma: no cover - depends on local native installation
            raise RuntimeError(f"Failed to initialize Voikko with language '{voikko_language}': {exc}") from exc

        try:
            self._nlp = spacy.load(spacy_model)
        except OSError:
            if spacy_model_path and Path(spacy_model_path).exists():
                self._nlp = spacy.load(spacy_model_path)
            else:
                self._voikko.terminate()
                msg = f"spaCy model '{spacy_model}' not found."
                if spacy_model_path:
                    msg += f" Fallback path missing: {spacy_model_path}"
                raise RuntimeError(msg)

    def _analyze_with_voikko(self, surface_form: str) -> list[LemmaAnalysis]:
        results: list[LemmaAnalysis] = []
        analyses = self._voikko.analyze(surface_form)

        for analysis in analyses:
            participle = analysis.get("PARTICIPLE", "")
            if participle in ["past_active", "past_passive", "present_active", "present_passive", "agent"]:
                wordbases = analysis.get("WORDBASES", "")
                if wordbases:
                    match = re.search(r"\+\w+\(([^)]+)\)", wordbases)
                    if match:
                        results.append(LemmaAnalysis(pos="VERB", lemma=match.group(1), source="voikko"))
                        continue

            if participle == "negation":
                wordbases = analysis.get("WORDBASES", "")
                if wordbases:
                    match = re.search(r"\+\w+\(([^)]+)\)", wordbases)
                    if match:
                        results.append(LemmaAnalysis(pos="ADJ", lemma=match.group(1), source="voikko"))
                        continue

            pos = map_voikko_pos(analysis)
            if pos:
                lemma = analysis.get("BASEFORM", surface_form)
                results.append(LemmaAnalysis(pos=pos, lemma=lemma, source="voikko"))

        return results

    def _analyze_with_spacy(self, surface_form: str) -> list[LemmaAnalysis]:
        results: list[LemmaAnalysis] = []
        doc = self._nlp(surface_form)
        for token in doc:
            pos = map_spacy_pos(token.pos_)
            if pos:
                results.append(LemmaAnalysis(pos=pos, lemma=token.lemma_, source="spacy"))
        return results

    def analyze(self, surface_form: str) -> list[LemmaAnalysis]:
        results = self._analyze_with_voikko(surface_form)
        if not results:
            results = self._analyze_with_spacy(surface_form)

        seen: set[tuple[str, str]] = set()
        unique_results: list[LemmaAnalysis] = []
        for result in results:
            key = (result.pos, result.lemma)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        return unique_results

    def close(self) -> None:
        self._voikko.terminate()

