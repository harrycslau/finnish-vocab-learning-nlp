#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Finnish pipeline parity between legacy two-step flow and universal build flow."
    )
    parser.add_argument(
        "--config",
        default="configs/fi_parity_fixture.yaml",
        help="Config path for parity fixture run (default: configs/fi_parity_fixture.yaml)",
    )
    parser.add_argument(
        "--expected-lemma",
        default="tests/fixtures/fi/lemma_fixture_expected.csv",
        help="Expected lemma CSV for fixture parity.",
    )
    parser.add_argument(
        "--expected-rank",
        default="tests/fixtures/fi/rank_fixture_expected.csv",
        help="Expected rank CSV for fixture parity.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print command outputs on success.",
    )
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path, verbose: bool = False) -> None:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Command failed ({result.returncode}): {' '.join(cmd)}", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(1)
    if verbose:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)


def read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return [row for row in csv.reader(fh) if row]


def assert_csv_equal(actual: Path, expected: Path, label: str) -> None:
    actual_rows = read_csv(actual)
    expected_rows = read_csv(expected)
    if actual_rows != expected_rows:
        print(f"{label} mismatch:", file=sys.stderr)
        print(f"  actual:   {actual}", file=sys.stderr)
        print(f"  expected: {expected}", file=sys.stderr)
        max_len = max(len(actual_rows), len(expected_rows))
        for idx in range(max_len):
            a = actual_rows[idx] if idx < len(actual_rows) else None
            e = expected_rows[idx] if idx < len(expected_rows) else None
            if a != e:
                print(f"  first diff at row {idx + 1}: actual={a} expected={e}", file=sys.stderr)
                break
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    config = (repo_root / args.config).resolve()
    expected_lemma = (repo_root / args.expected_lemma).resolve()
    expected_rank = (repo_root / args.expected_rank).resolve()

    if not config.exists():
        raise SystemExit(f"Config not found: {config}")
    if not expected_lemma.exists():
        raise SystemExit(f"Expected lemma fixture not found: {expected_lemma}")
    if not expected_rank.exists():
        raise SystemExit(f"Expected rank fixture not found: {expected_rank}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        legacy_lemma = tmp / "legacy_lemma.csv"
        legacy_rank = tmp / "legacy_rank.csv"
        unified_lemma = tmp / "unified_lemma.csv"
        unified_rank = tmp / "unified_rank.csv"

        run_cmd(
            [
                sys.executable,
                "create_lemma_table.py",
                "--config",
                str(config),
                "--output",
                str(legacy_lemma),
            ],
            cwd=repo_root,
            verbose=args.verbose,
        )
        run_cmd(
            [
                sys.executable,
                "compute_lemma_freq.py",
                "--config",
                str(config),
                "--lemma-csv",
                str(legacy_lemma),
                "--output",
                str(legacy_rank),
            ],
            cwd=repo_root,
            verbose=args.verbose,
        )
        run_cmd(
            [
                sys.executable,
                "build_lemma_assets.py",
                "--config",
                str(config),
                "--lemma-output",
                str(unified_lemma),
                "--rank-output",
                str(unified_rank),
            ],
            cwd=repo_root,
            verbose=args.verbose,
        )

        assert_csv_equal(legacy_lemma, unified_lemma, "legacy vs unified lemma")
        assert_csv_equal(legacy_rank, unified_rank, "legacy vs unified rank")
        assert_csv_equal(unified_lemma, expected_lemma, "unified lemma vs expected fixture")
        assert_csv_equal(unified_rank, expected_rank, "unified rank vs expected fixture")

    print("FI parity check passed: lemma and rank outputs match legacy flow and expected fixtures.")


if __name__ == "__main__":
    main()
