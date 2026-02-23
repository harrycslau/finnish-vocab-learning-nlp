from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from pipeline.config import load_pipeline_config
from pipeline.sqlite_export import load_lookup_csv, load_rank_csv, write_db


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert lemma and rank CSVs to SQLite")
    parser.add_argument(
        "--config",
        default="configs/fi.yaml",
        help="YAML configuration path (default: configs/fi.yaml)",
    )
    parser.add_argument("--lookup-csv", help="Lookup CSV path")
    parser.add_argument("--rank-csv", help="Rank CSV path")
    parser.add_argument("--output", help="Output SQLite path")
    parser.add_argument("--lookup-table", help="Override lookup table name")
    parser.add_argument("--rank-table", help="Override rank table name")
    parser.add_argument("--replace", action="store_true", help="Overwrite existing SQLite file")
    return parser.parse_args(argv)


def _path_or_none(value: str | None) -> Path | None:
    return Path(value).resolve() if value else None


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_pipeline_config(args.config)

    lookup_csv = _path_or_none(args.lookup_csv) or config.resolve_default_path("lemma_csv")
    rank_csv = _path_or_none(args.rank_csv) or config.resolve_default_path("rank_csv")
    output_sqlite = _path_or_none(args.output) or config.sqlite_output_path().resolve()

    lookup_rows = None
    rank_rows = None

    if lookup_csv and lookup_csv.exists():
        print(f"Reading lookup CSV: {lookup_csv}")
        lookup_rows = load_lookup_csv(lookup_csv)
    elif lookup_csv:
        print(f"Warning: lookup CSV not found: {lookup_csv}")

    if rank_csv and rank_csv.exists():
        print(f"Reading rank CSV: {rank_csv}")
        rank_rows = load_rank_csv(rank_csv)
    elif rank_csv:
        print(f"Warning: rank CSV not found: {rank_csv}")

    if not lookup_rows and not rank_rows:
        print("Error: no data to insert.", file=sys.stderr)
        sys.exit(3)

    lookup_table = args.lookup_table or config.language.lookup_table
    rank_table = args.rank_table or config.language.rank_table

    total = write_db(
        db_path=output_sqlite,
        lookup_table=lookup_table,
        rank_table=rank_table,
        lookup_rows=lookup_rows,
        rank_rows=rank_rows,
        replace=args.replace,
    )
    print(f"Done. Inserted {total} total rows into {output_sqlite}")


if __name__ == "__main__":
    main()
