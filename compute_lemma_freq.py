#!/usr/bin/env python3
'''
Convert the lemma table and the surface frequency list into a lemma frequency CSV.
'''
import argparse
import csv
from pathlib import Path
from typing import Dict, Set, Tuple


def load_surface_to_lemma(lemma_csv: Path) -> Tuple[Dict[str, str], Set[str]]:
    surface_to_lemma: Dict[str, str] = {}
    lemmas: Set[str] = set()
    with lemma_csv.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header_checked = False
        for row in reader:
            if not row:
                continue
            if not header_checked:
                normalized = [c.strip().lower() for c in row[:3]]
                if normalized[:3] in (("surface_form", "pos", "lemma"), ("surface form", "pos", "lemma")):
                    header_checked = True
                    continue
                header_checked = True
            surface = row[0].strip()
            if not surface:
                continue
            lemma = row[2].strip() if len(row) > 2 else ""
            if not lemma:
                continue
            surface_to_lemma.setdefault(surface, lemma)
            lemmas.add(lemma)
    return surface_to_lemma, lemmas


def accumulate_lemma_frequencies(surface_map: Dict[str, str], freq_list: Path, lemmas: Set[str]) -> Tuple[Dict[str, int], int, int]:
    lemma_freq = {lemma: 0 for lemma in lemmas}
    matched = 0
    unmatched = 0
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
            lemma = surface_map.get(surface)
            if lemma is None:
                unmatched += 1
                continue
            lemma_freq[lemma] += freq_value
            matched += 1
    return lemma_freq, matched, unmatched


def write_lemma_rank_csv(lemma_freq: Dict[str, int], output_csv: Path, include_freq: bool = False) -> int:
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a lemma frequency CSV by combining the lemma table and a surface frequency list."
    )
    parser.add_argument("--lemma-csv", "-l", default="output/fi_200000_lemmas.csv",
                        help="Lemma table CSV (default: output/fi_200000_lemmas.csv)")
    parser.add_argument("--freq-list", "-f", default="freqwords/fi_100k.txt",
                        help="Space-separated frequency file (default: freqwords/fi_100k.txt)")
    parser.add_argument("--output", "-o", default="output/fi_200000_lemmas_rank.csv",
                        help="Output CSV path (default: output/fi_200000_lemmas_rank.csv)")
    parser.add_argument("--include-freq", action="store_true",
                        help="Include frequency column in output (default: False)")
    args = parser.parse_args()

    lemma_csv = Path(args.lemma_csv)
    if not lemma_csv.exists():
        parser.error(f"lemma CSV not found: {lemma_csv}")
    freq_list = Path(args.freq_list)
    if not freq_list.exists():
        parser.error(f"frequency list not found: {freq_list}")

    surface_map, lemmas = load_surface_to_lemma(lemma_csv)
    if not lemmas:
        parser.error(f"no lemmas parsed from {lemma_csv}")

    lemma_freq, matched, unmatched = accumulate_lemma_frequencies(surface_map, freq_list, lemmas)
    zero_hits = sum(1 for value in lemma_freq.values() if value == 0)
    rows_written = write_lemma_rank_csv(lemma_freq, Path(args.output), args.include_freq)

    print(f"Loaded {len(surface_map)} surface entries covering {len(lemmas)} lemmas.")
    print(f"Matched {matched} surface frequencies and skipped {unmatched} lines without a lemma.")
    print(f"{zero_hits} lemmas had zero surface frequency; wrote {rows_written} rows to {args.output}.")


if __name__ == "__main__":
    main()
