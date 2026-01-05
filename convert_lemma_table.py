#!/usr/bin/env python3
"""
Convert lemma lookup and rank CSVs into a dictionary.sqlite database.

Sample Usage:
    python convert_lemma_table.py --lookup-csv output/fi_200000_lemmas.csv --rank-csv output/fi_200000_lemmas_rank.csv --output output/fi_FI_v1.sqlite
"""
import csv
import sqlite3
from pathlib import Path
import argparse
import sys

def create_schema(conn):
    cur = conn.cursor()
    cur.executescript("""
    -- Table for the surface->lemma mapping
    CREATE TABLE IF NOT EXISTS fi_FI_lemma_lookup (
      surface_form TEXT NOT NULL,
      pos TEXT NOT NULL,
      lemma TEXT NOT NULL,
      PRIMARY KEY(surface_form, pos)
    );
    -- An index for when POS is not known
    CREATE INDEX IF NOT EXISTS idx_surface_form ON fi_FI_lemma_lookup(surface_form);

    -- Table for lemma ranks/frequencies
    CREATE TABLE IF NOT EXISTS fi_FI_lemma_rank (
      lemma TEXT NOT NULL PRIMARY KEY,
      freq INTEGER,
      rank INTEGER NOT NULL
    );
    """)
    conn.commit()

def load_lookup_csv(csv_path):
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
                if hdr[:3] in (["surface_form", "pos", "lemma"], ["surface form", "pos", "lemma"]):
                    continue
            surface = r[0].strip()
            pos = r[1].strip() if len(r) > 1 else ""
            lemma = r[2].strip() if len(r) > 2 else ""
            if surface and pos and lemma:
                rows.append((surface, pos, lemma))
        return rows

def load_rank_csv(csv_path):
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

def write_db(db_path, lookup_rows=None, rank_rows=None, replace=False):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if replace and db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    try:
        create_schema(conn)
        cur = conn.cursor()
        
        if lookup_rows:
            print(f"Inserting {len(lookup_rows)} lookup rows...")
            insert_sql = "INSERT OR REPLACE INTO fi_FI_lemma_lookup(surface_form, pos, lemma) VALUES (?, ?, ?)"
            cur.executemany(insert_sql, lookup_rows)
            
        if rank_rows:
            print(f"Inserting {len(rank_rows)} rank rows...")
            insert_sql = "INSERT OR REPLACE INTO fi_FI_lemma_rank(lemma, freq, rank) VALUES (?, ?, ?)"
            cur.executemany(insert_sql, rank_rows)
            
        conn.commit()
        return (len(lookup_rows) if lookup_rows else 0) + (len(rank_rows) if rank_rows else 0)
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert lemma and rank CSVs to dictionary.sqlite")
    parser.add_argument("--lookup-csv", default="output/fi_200000_lemmas.csv",
                        help="Lookup CSV file (default: output/fi_200000_lemmas.csv)")
    parser.add_argument("--rank-csv", help="Rank CSV file (e.g. output/fi_200000_lemmas_rank.csv)")
    parser.add_argument("--output", default="output/dictionary.sqlite",
                        help="Output SQLite file (default: output/dictionary.sqlite)")
    parser.add_argument("--replace", action="store_true", help="Overwrite existing SQLite file")
    args = parser.parse_args()

    db_path = Path(args.output)
    lookup_rows = None
    rank_rows = None

    if args.lookup_csv:
        csv_path = Path(args.lookup_csv)
        if csv_path.exists():
            print(f"Reading lookup CSV: {csv_path}")
            lookup_rows = load_lookup_csv(csv_path)
        else:
            print(f"Warning: Lookup CSV not found: {csv_path}")

    if args.rank_csv:
        csv_path = Path(args.rank_csv)
        if csv_path.exists():
            print(f"Reading rank CSV: {csv_path}")
            rank_rows = load_rank_csv(csv_path)
        else:
            print(f"Warning: Rank CSV not found: {csv_path}")

    if not lookup_rows and not rank_rows:
        print("Error: No data to insert.", file=sys.stderr)
        sys.exit(3)

    print(f"Updating SQLite DB: {db_path}")
    total = write_db(db_path, lookup_rows, rank_rows, replace=args.replace)
    print(f"Done. Inserted {total} total rows into {db_path}")

if __name__ == "__main__":
    main()
