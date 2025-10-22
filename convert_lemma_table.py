import csv
import sqlite3
from pathlib import Path
import argparse
import sys

def create_schema(conn):
    cur = conn.cursor()
    cur.executescript("""
    -- Table for the surface->lemma mapping
    CREATE TABLE IF NOT EXISTS fi-FI_lemma_lookup (
      surface_form TEXT NOT NULL,
      pos TEXT NOT NULL,
      lemma TEXT NOT NULL,
      PRIMARY KEY(surface_form, pos)
    );
    -- An index for when POS is not known
    CREATE INDEX IF NOT EXISTS idx_surface_form ON fi_lemma_lookup(surface_form);
    """)
    conn.commit()

def load_csv_rows(csv_path):
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = []
        first = True
        for r in reader:
            if not r:
                continue
            # Skip header row if present
            if first:
                first = False
                hdr = [c.strip().lower() for c in r]
                if hdr[:3] == ["surface_form", "pos", "lemma"] or hdr[:3] == ["surface form", "pos", "lemma"]:
                    continue
            # Expect at least 3 cols; take first three
            surface = r[0].strip()
            pos = r[1].strip() if len(r) > 1 else ""
            lemma = r[2].strip() if len(r) > 2 else ""
            if surface and pos and lemma:
                rows.append((surface, pos, lemma))
        return rows

def write_db(db_path, rows, replace=False):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if replace and db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        create_schema(conn)
        cur = conn.cursor()
        insert_sql = "INSERT OR REPLACE INTO fi_lemma_lookup(surface_form, pos, lemma) VALUES (?, ?, ?)"
        batch_size = 1000
        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            cur.executemany(insert_sql, batch)
            total += len(batch)
            conn.commit()
        return total
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert fi_*_lemma.csv to dictionary.sqlite")
    parser.add_argument("input_csv", nargs="?", default="output/fi_200000_lemmas.csv",
                        help="CSV file to read (default: output/fi_200000_lemmas.csv)")
    parser.add_argument("output_sqlite", nargs="?", default="output/dictionary.sqlite",
                        help="SQLite file to create (default: output/dictionary.sqlite)")
    parser.add_argument("--replace", action="store_true", help="Overwrite existing SQLite file")
    args = parser.parse_args()

    csv_path = Path(args.input_csv)
    db_path = Path(args.output_sqlite)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    print(f"Reading CSV: {csv_path}")
    rows = load_csv_rows(csv_path)
    if not rows:
        print("No valid rows found in CSV.", file=sys.stderr)
        sys.exit(3)

    print(f"Creating SQLite DB: {db_path} (rows: {len(rows)})")
    inserted = write_db(db_path, rows, replace=args.replace)
    print(f"Done. Inserted {inserted} rows into {db_path}")

if __name__ == "__main__":
    main()
