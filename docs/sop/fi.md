# SOP: Finnish (`fi_FI`)

## 1. Prerequisites
- Install core + Finnish dependencies:
  - `pip install -e .[core,fi]`
- Ensure Finnish frequency list exists:
  - `data/freqwords/fi/fi_100k.txt`

## 2. Config
- Primary config: `configs/fi.yaml`
- Validate with a small run:
  - `python create_lemma_table.py --config configs/fi.yaml --limit 100`

## 3. Generate lemma mapping
- `python create_lemma_table.py --config configs/fi.yaml --limit 200000`
- Expected output:
  - `output/fi_200000_lemmas.csv`

## 4. Universal workflow (recommended)
- `python build_lemma_assets.py --config configs/fi.yaml --limit 200000`
- If `output/fi_200000_lemmas.csv` already exists and you only need rank:
  - `python build_lemma_assets.py --config configs/fi.yaml --skip-lemma --lemma-output output/fi_200000_lemmas.csv --rank-output output/fi_200000_lemmas_rank.csv`

## 5. Compute lemma rank (standalone)
- `python compute_lemma_freq.py --config configs/fi.yaml --lemma-csv output/fi_200000_lemmas.csv --freq-list data/freqwords/fi/fi_100k.txt --output output/fi_200000_lemmas_rank.csv`

## 6. Export app assets
- Lookup JSON:
  - `python convert_csv_json.py output/fi_200000_lemmas.csv output/fi_FI_lookup_v1.json --key fi_FI_lemma_lookup --minify`
- Rank JSON:
  - `python convert_csv_json.py output/fi_200000_lemmas_rank.csv output/fi_FI_rank_v1.json --key fi_FI_lemma_rank --minify`
- SQLite:
  - `python convert_lemma_table.py --config configs/fi.yaml --lookup-csv output/fi_200000_lemmas.csv --rank-csv output/fi_200000_lemmas_rank.csv --output output/dictionary.sqlite --replace`
