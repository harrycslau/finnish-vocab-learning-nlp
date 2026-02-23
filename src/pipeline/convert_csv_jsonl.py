from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.json_export import convert_csv_to_jsonl


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert CSV to JSONL")
    parser.add_argument("input_file", help="Input CSV file path")
    parser.add_argument("output_file", help="Output JSONL file path")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    count = convert_csv_to_jsonl(
        input_file=Path(args.input_file).resolve(),
        output_file=Path(args.output_file).resolve(),
    )
    print(
        f"Successfully converted '{args.input_file}' to '{args.output_file}' ({count} records)."
    )


if __name__ == "__main__":
    main()

