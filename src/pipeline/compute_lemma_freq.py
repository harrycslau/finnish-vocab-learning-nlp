from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.config import load_pipeline_config
from pipeline.rank import (
    accumulate_lemma_frequencies,
    consolidate_to_best_lemmas,
    load_surface_to_lemma,
    write_lemma_rank_csv,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a lemma frequency CSV by combining a lemma table and a surface frequency list."
    )
    parser.add_argument(
        "--config",
        default="configs/fi.yaml",
        help="YAML configuration path (default: configs/fi.yaml)",
    )
    parser.add_argument(
        "--lemma-csv",
        "-l",
        help="Lemma table CSV. Defaults to config.defaults.lemma_csv or generated output name.",
    )
    parser.add_argument(
        "--freq-list",
        "-f",
        help="Space-separated frequency file. Defaults to paths.freq_list in config.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output CSV path. Defaults to config.defaults.rank_csv or generated output name.",
    )
    parser.add_argument(
        "--include-freq",
        action="store_true",
        help="Include frequency column in output.",
    )
    return parser.parse_args(argv)


def compute_lemma_rank(
    *,
    lemma_csv: Path,
    freq_list: Path,
    output_csv: Path,
    include_freq: bool = False,
) -> tuple[int, int, int, int, int, int]:
    if not lemma_csv.exists():
        raise FileNotFoundError(f"Lemma CSV not found: {lemma_csv}")
    if not freq_list.exists():
        raise FileNotFoundError(f"Frequency list not found: {freq_list}")

    surface_map, lemmas = load_surface_to_lemma(lemma_csv)
    if not lemmas:
        raise ValueError(f"No lemmas parsed from {lemma_csv}")

    lemma_freq, matched, unmatched, surface_freq_map = accumulate_lemma_frequencies(
        surface_map, freq_list, lemmas
    )
    lemma_freq = consolidate_to_best_lemmas(lemma_freq, surface_map, surface_freq_map)
    zero_hits = sum(1 for value in lemma_freq.values() if value == 0)
    rows_written = write_lemma_rank_csv(
        lemma_freq,
        output_csv=output_csv,
        include_freq=include_freq,
    )
    return len(surface_map), len(lemmas), matched, unmatched, zero_hits, rows_written


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_pipeline_config(args.config)

    if args.lemma_csv:
        lemma_csv = Path(args.lemma_csv).resolve()
    else:
        lemma_csv = config.resolve_default_path("lemma_csv")
    if lemma_csv is None:
        lemma_csv = config.lemma_output_path(limit=None).resolve()

    freq_list = Path(args.freq_list).resolve() if args.freq_list else config.paths.freq_list

    if args.output:
        output_csv = Path(args.output).resolve()
    else:
        output_csv = config.resolve_default_path("rank_csv")
    if output_csv is None:
        output_csv = config.rank_output_path(limit=None).resolve()

    surface_count, lemma_count, matched, unmatched, zero_hits, rows_written = compute_lemma_rank(
        lemma_csv=lemma_csv,
        freq_list=freq_list,
        output_csv=output_csv,
        include_freq=args.include_freq,
    )

    print(f"Loaded {surface_count} surface entries covering {lemma_count} lemmas.")
    print(f"Matched {matched} surface frequencies and skipped {unmatched} lines without a lemma.")
    print(f"{zero_hits} lemmas had zero surface frequency; wrote {rows_written} rows to {output_csv}.")


if __name__ == "__main__":
    main()
