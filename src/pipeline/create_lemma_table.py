from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

from pipeline.analyzers import load_analyzer
from pipeline.config import PipelineConfig, load_pipeline_config
from pipeline.frequency import load_frequency_words


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate lemma table from a language frequency list."
    )
    parser.add_argument(
        "--config",
        default="configs/fi.yaml",
        help="YAML configuration path (default: configs/fi.yaml)",
    )
    parser.add_argument(
        "--input-file",
        help="Override frequency list path from config.",
    )
    parser.add_argument(
        "--output",
        help="Override output CSV path. If omitted, uses config naming templates.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most this many unique surface forms.",
    )
    return parser.parse_args(argv)


def generate_lemma_table(
    *,
    config: PipelineConfig,
    input_file: Path,
    output_file: Path,
    limit: int | None = None,
) -> tuple[int, int]:
    if not input_file.exists():
        raise FileNotFoundError(f"Frequency list not found: {input_file}")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading frequency words from {input_file}...")
    surface_forms = load_frequency_words(input_file, limit=limit)
    print(f"Loaded {len(surface_forms)} unique surface forms.")

    print(f"Initializing analyzer: {config.analyzer.module}.{config.analyzer.class_name}")
    analyzer = load_analyzer(config.analyzer)

    print(f"Processing words and writing to {output_file}...")
    total_rows = 0
    unanalyzable: list[str] = []

    try:
        with output_file.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["surface_form", "pos", "lemma"])

            for surface_form in surface_forms:
                results = analyzer.analyze(surface_form)
                if results:
                    for result in results:
                        writer.writerow([surface_form, result.pos, result.lemma])
                        total_rows += 1
                else:
                    unanalyzable.append(surface_form)
    finally:
        analyzer.close()

    print("Processing complete.")
    print(f"Total rows written: {total_rows}")
    print(f"Output file: {output_file}")
    if unanalyzable:
        print(f"{len(unanalyzable)} token(s) could not be analyzed.")
    return total_rows, len(unanalyzable)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_pipeline_config(args.config)

    input_file = Path(args.input_file).resolve() if args.input_file else config.paths.freq_list
    output_file = (
        Path(args.output).resolve()
        if args.output
        else config.lemma_output_path(args.limit).resolve()
    )
    generate_lemma_table(
        config=config,
        input_file=input_file,
        output_file=output_file,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
