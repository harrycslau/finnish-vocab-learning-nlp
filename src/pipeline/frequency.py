from __future__ import annotations

from pathlib import Path


def load_frequency_words(filepath: Path, limit: int | None = None) -> list[str]:
    """Load unique word tokens from a frequency list in `word count` format."""
    surface_forms: list[str] = []
    seen: set[str] = set()

    with filepath.open("r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.strip().split()
            if not parts:
                continue
            word = parts[0]
            if word in seen:
                continue
            surface_forms.append(word)
            seen.add(word)
            if limit is not None and len(surface_forms) >= limit:
                break

    return surface_forms

