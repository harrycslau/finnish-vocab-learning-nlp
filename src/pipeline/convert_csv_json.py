from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pipeline.json_export import convert_csv_to_json


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert CSV to JSON")
    parser.add_argument("input_file", help="Input CSV file path")
    parser.add_argument("output_file", help="Output JSON file path")
    parser.add_argument("--key", help="Optional root key to wrap the array", default=None)
    parser.add_argument("--tabs", action="store_true", help="Use tabs for indentation")
    parser.add_argument("--minify", action="store_true", help="Minify output")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if args.minify:
        indent = None
    elif args.tabs:
        indent = "\t"
    else:
        indent = 2

    count = convert_csv_to_json(
        input_file=Path(args.input_file).resolve(),
        output_file=Path(args.output_file).resolve(),
        root_key=args.key,
        indent=indent,
    )
    print(
        f"Successfully converted '{args.input_file}' to '{args.output_file}' ({count} records)."
    )


if __name__ == "__main__":
    main()

