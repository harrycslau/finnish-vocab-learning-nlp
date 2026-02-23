from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.compute_lemma_freq import compute_lemma_rank
from pipeline.config import load_pipeline_config
from pipeline.create_lemma_table import generate_lemma_table


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Universal workflow: frequency list -> lemma lookup CSV -> lemma rank CSV."
    )
    parser.add_argument(
        "--config",
        default="configs/fi.yaml",
        help="YAML configuration path (default: configs/fi.yaml)",
    )
    parser.add_argument(
        "--freq-list",
        help="Override frequency list path from config.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of unique surface forms when building lemma table.",
    )
    parser.add_argument(
        "--lemma-output",
        help="Override lemma lookup CSV output path.",
    )
    parser.add_argument(
        "--rank-output",
        help="Override lemma rank CSV output path.",
    )
    parser.add_argument(
        "--include-freq",
        action="store_true",
        help="Include frequency column in rank CSV output.",
    )
    parser.add_argument(
        "--skip-lemma",
        action="store_true",
        help="Skip lemma generation and use --lemma-output (or config default) as input.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_pipeline_config(args.config)

    freq_list = Path(args.freq_list).resolve() if args.freq_list else config.paths.freq_list
    lemma_csv = (
        Path(args.lemma_output).resolve()
        if args.lemma_output
        else (
            config.resolve_default_path("lemma_csv")
            if args.skip_lemma and args.limit is None
            else config.lemma_output_path(args.limit).resolve()
        )
    )
    rank_csv = (
        Path(args.rank_output).resolve()
        if args.rank_output
        else (
            config.resolve_default_path("rank_csv")
            if args.limit is None
            else config.rank_output_path(args.limit).resolve()
        )
    )
    if rank_csv is None:
        rank_csv = config.rank_output_path(args.limit).resolve()

    if args.skip_lemma:
        if not lemma_csv.exists():
            raise FileNotFoundError(f"Lemma CSV not found for --skip-lemma: {lemma_csv}")
        print(f"Skipping lemma generation; using existing CSV: {lemma_csv}")
    else:
        generate_lemma_table(
            config=config,
            input_file=freq_list,
            output_file=lemma_csv,
            limit=args.limit,
        )

    surface_count, lemma_count, matched, unmatched, zero_hits, rows_written = compute_lemma_rank(
        lemma_csv=lemma_csv,
        freq_list=freq_list,
        output_csv=rank_csv,
        include_freq=args.include_freq,
    )
    print(f"Loaded {surface_count} surface entries covering {lemma_count} lemmas.")
    print(f"Matched {matched} surface frequencies and skipped {unmatched} lines without a lemma.")
    print(f"{zero_hits} lemmas had zero surface frequency; wrote {rows_written} rows to {rank_csv}.")


if __name__ == "__main__":
    main()

