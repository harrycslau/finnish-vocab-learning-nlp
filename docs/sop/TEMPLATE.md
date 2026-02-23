# SOP: `<language>`

## 1. Prerequisites
- Install core dependencies: `pip install -e .[core]`
- Install language extras: `pip install -e .[<lang>]`
- Confirm frequency list exists at `data/freqwords/<lang>/...`
- Record the source URL and retrieval date for the frequency file in this SOP.

## 2. Validate config
- Copy `configs/TEMPLATE.yaml` to `configs/<lang>.yaml`
- Fill language/analyzer/path fields
- Run a smoke validation:
  - `python create_lemma_table.py --config configs/<lang>.yaml --limit 100`

## 3. Generate lemma table
- `python create_lemma_table.py --config configs/<lang>.yaml --limit <N>`
- Output should be under `output/`

## 4. Universal workflow (recommended)
- `python build_lemma_assets.py --config configs/<lang>.yaml --limit <N>`
- If lemma CSV is prepared by another tool, skip analyzer step:
  - `python build_lemma_assets.py --config configs/<lang>.yaml --skip-lemma --lemma-output <lemma_csv> --rank-output <rank_csv>`

## 5. Compute lemma ranks (standalone)
- `python compute_lemma_freq.py --config configs/<lang>.yaml --lemma-csv <lemma_csv> --output <rank_csv>`

## 6. Export app assets
- Lookup JSON:
  - `python convert_csv_json.py <lemma_csv> <lookup_json> --key <locale>_lemma_lookup --minify`
- Rank JSON:
  - `python convert_csv_json.py <rank_csv> <rank_json> --key <locale>_lemma_rank --minify`
- SQLite:
  - `python convert_lemma_table.py --config configs/<lang>.yaml --lookup-csv <lemma_csv> --rank-csv <rank_csv> --output <sqlite> --replace`

## 7. Quality checks
- Verify header integrity (`surface_form,pos,lemma` and `lemma,rank` or `lemma,freq,rank`)
- Spot-check ambiguous forms and POS tags
- Keep run logs with config hash and command history
