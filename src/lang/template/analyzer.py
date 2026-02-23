from __future__ import annotations

from pipeline.types import LemmaAnalysis


class TemplateAnalyzer:
    """Copy this file into src/lang/<lang>/analyzer.py and implement analyze()."""

    def __init__(self, **_: object) -> None:
        pass

    def analyze(self, surface_form: str) -> list[LemmaAnalysis]:
        raise NotImplementedError(f"Implement analyzer for input: {surface_form}")

    def close(self) -> None:
        pass

