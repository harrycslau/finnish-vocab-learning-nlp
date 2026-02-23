from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


def create_schema(conn: sqlite3.Connection, lookup_table: str, rank_table: str) -> None:
    cur = conn.cursor()
    cur.executescript(
        f"""
    CREATE TABLE IF NOT EXISTS {lookup_table} (
      surface_form TEXT NOT NULL,
      pos TEXT NOT NULL,
      lemma TEXT NOT NULL,
      PRIMARY KEY(surface_form, pos)
    );
    CREATE INDEX IF NOT EXISTS idx_{lookup_table}_surface_form ON {lookup_table}(surface_form);

    CREATE TABLE IF NOT EXISTS {rank_table} (
      lemma TEXT NOT NULL PRIMARY KEY,
      freq INTEGER,
      rank INTEGER NOT NULL
    );
    """
    )
    conn.commit()


def load_lookup_csv(csv_path: Path) -> list[tuple[str, str, str]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = []
        first = True
        for r in reader:
            if not r:
                continue
            if first:
                first = False
                hdr = [c.strip().lower() for c in r]
                if hdr[:3] in (
                    ["surface_form", "pos", "lemma"],
                    ["surface form", "pos", "lemma"],
                ):
                    continue
            surface = r[0].strip()
            pos = r[1].strip() if len(r) > 1 else ""
            lemma = r[2].strip() if len(r) > 2 else ""
            if surface and pos and lemma:
                rows.append((surface, pos, lemma))
        return rows


def load_rank_csv(csv_path: Path) -> list[tuple[str, int | None, int]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for r in reader:
            lemma = r.get("lemma", "").strip()
            rank = r.get("rank", "").strip()
            freq = r.get("freq", "").strip()
            if lemma and rank:
                rows.append((lemma, int(freq) if freq else None, int(rank)))
        return rows


def write_db(
    db_path: Path,
    lookup_table: str,
    rank_table: str,
    lookup_rows: list[tuple[str, str, str]] | None = None,
    rank_rows: list[tuple[str, int | None, int]] | None = None,
    replace: bool = False,
) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if replace and db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        create_schema(conn, lookup_table=lookup_table, rank_table=rank_table)
        cur = conn.cursor()

        if lookup_rows:
            insert_lookup = (
                f"INSERT OR REPLACE INTO {lookup_table}(surface_form, pos, lemma) VALUES (?, ?, ?)"
            )
            cur.executemany(insert_lookup, lookup_rows)

        if rank_rows:
            insert_rank = (
                f"INSERT OR REPLACE INTO {rank_table}(lemma, freq, rank) VALUES (?, ?, ?)"
            )
            cur.executemany(insert_rank, rank_rows)

        conn.commit()
        return (len(lookup_rows) if lookup_rows else 0) + (len(rank_rows) if rank_rows else 0)
    finally:
        conn.close()

