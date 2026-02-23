from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def convert_csv_to_json(
    input_file: Path, output_file: Path, root_key: str | None = None, indent: Any = 2
) -> int:
    with input_file.open(mode="r", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    data: Any = {root_key: rows} if root_key else rows
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open(mode="w", encoding="utf-8") as json_file:
        separators = (",", ":") if indent is None else None
        json.dump(data, json_file, ensure_ascii=False, indent=indent, separators=separators)
    return len(rows)


def convert_csv_to_jsonl(input_file: Path, output_file: Path) -> int:
    total = 0
    with input_file.open(mode="r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open(mode="w", encoding="utf-8") as jsonl_file:
            for row in reader:
                jsonl_file.write(json.dumps(row, ensure_ascii=False))
                jsonl_file.write("\n")
                total += 1
    return total

