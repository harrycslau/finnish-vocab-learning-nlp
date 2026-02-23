from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_surface_to_lemma(lemma_csv: Path) -> Tuple[Dict[str, List[str]], Set[str]]:
    """Load all candidate lemmas for each surface form."""
    surface_to_lemmas: Dict[str, List[str]] = {}
    lemmas: Set[str] = set()
    with lemma_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header_checked = False
        for row in reader:
            if not row:
                continue
            if not header_checked:
                normalized = [c.strip().lower() for c in row[:3]]
                if normalized[:3] in (
                    ["surface_form", "pos", "lemma"],
                    ["surface form", "pos", "lemma"],
                ):
                    header_checked = True
                    continue
                header_checked = True
            surface = row[0].strip()
            if not surface:
                continue
            lemma = row[2].strip() if len(row) > 2 else ""
            if not lemma:
                continue
            if surface not in surface_to_lemmas:
                surface_to_lemmas[surface] = []
            if lemma not in surface_to_lemmas[surface]:
                surface_to_lemmas[surface].append(lemma)
            lemmas.add(lemma)
    return surface_to_lemmas, lemmas


def accumulate_lemma_frequencies(
    surface_map: Dict[str, List[str]], freq_list: Path, lemmas: Set[str]
) -> Tuple[Dict[str, int], int, int, Dict[str, int]]:
    """Accumulate frequencies to all candidate lemmas; return map + summary metrics."""
    lemma_freq = {lemma: 0 for lemma in lemmas}
    matched = 0
    unmatched = 0
    surface_freq_map: Dict[str, int] = {}
    with freq_list.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            surface = parts[0].strip()
            if not surface:
                continue
            freq_str = parts[1]
            try:
                freq_value = int(freq_str)
            except ValueError:
                continue
            candidates = surface_map.get(surface)
            if candidates is None:
                unmatched += 1
                continue
            surface_freq_map[surface] = freq_value
            for lemma in candidates:
                lemma_freq[lemma] += freq_value
            matched += 1
    return lemma_freq, matched, unmatched, surface_freq_map


def consolidate_to_best_lemmas(
    lemma_freq: Dict[str, int],
    surface_map: Dict[str, List[str]],
    surface_freq_map: Dict[str, int],
) -> Dict[str, int]:
    """For each ambiguous surface, keep frequency only on highest-frequency lemma."""
    consolidated_freq = lemma_freq.copy()
    for surface, candidates in surface_map.items():
        if len(candidates) <= 1:
            continue
        freq_for_surface = surface_freq_map.get(surface, 0)
        if freq_for_surface == 0:
            continue
        best_lemma = max(candidates, key=lambda lem: lemma_freq.get(lem, 0))
        for lemma in candidates:
            if lemma == best_lemma:
                consolidated_freq[lemma] = lemma_freq[lemma]
            else:
                consolidated_freq[lemma] = max(0, lemma_freq[lemma] - freq_for_surface)
    return consolidated_freq


def write_lemma_rank_csv(
    lemma_freq: Dict[str, int], output_csv: Path, include_freq: bool = False
) -> int:
    ordered = sorted(lemma_freq.items(), key=lambda item: (-item[1], item[0]))
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if include_freq:
            writer.writerow(["lemma", "freq", "rank"])
            for rank, (lemma, freq) in enumerate(ordered, start=1):
                writer.writerow([lemma, freq, rank])
        else:
            writer.writerow(["lemma", "rank"])
            for rank, (lemma, _) in enumerate(ordered, start=1):
                writer.writerow([lemma, rank])
    return len(ordered)
