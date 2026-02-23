# finnish-vocab-learning-nlp

A small NLP project for vocabulary-learning data preparation.  
The pipeline is now config-driven and organized to support multiple languages.

## Install Dependencies

```bash
pip install -e .[core,fi]
```

## Repository Layout

- `src/pipeline/`: language-agnostic pipeline logic
- `src/lang/`: language-specific analyzer implementations
- `configs/`: per-language YAML configs
- `docs/sop/`: language SOP documents
- `data/freqwords/`: recommended location for large local frequency lists (not committed)
- Root scripts remain as compatibility entrypoints and call into `src/pipeline`.

## Analyzer Requirement

- Each language `analyzer.py` should use a morphology dictionary/lexicon that returns all valid lemma possibilities per surface form (including ambiguous POS when available).
- A small language-specific library is acceptable if it returns multiple `(pos, lemma)` candidates.

## Finnish Pipeline (Current)

### 0. Universal workflow command
For any configured language, the universal pipeline is:
```bash
python build_lemma_assets.py --config configs/<lang>.yaml --limit <N>
```
This runs both steps:
- lemma lookup generation
- lemma rank generation

### 1. Generate lemma mapping
```bash
python create_lemma_table.py --config configs/fi.yaml --limit 200000
```
Input: `data/freqwords/fi/fi_100k.txt`  
Output: `output/fi_200000_lemmas.csv`

### 2. Compute lemma ranks
```bash
python compute_lemma_freq.py --config configs/fi.yaml --lemma-csv output/fi_200000_lemmas.csv --freq-list data/freqwords/fi/fi_100k.txt --output output/fi_200000_lemmas_rank.csv
```
Rule: when a surface form has multiple lemmas, all surface frequency is assigned to the highest-frequency lemma candidate.

### 3. Export to JSON
```bash
python convert_csv_json.py output/fi_200000_lemmas.csv output/fi_FI_lookup_v1.json --key fi_FI_lemma_lookup --minify
python convert_csv_json.py output/fi_200000_lemmas_rank.csv output/fi_FI_rank_v1.json --key fi_FI_lemma_rank --minify
```

### 4. Export to SQLite
```bash
python convert_lemma_table.py --config configs/fi.yaml --lookup-csv output/fi_200000_lemmas.csv --rank-csv output/fi_200000_lemmas_rank.csv --output output/dictionary.sqlite --replace
```
Output: `output/dictionary.sqlite` with `fi_FI_lemma_lookup` and `fi_FI_lemma_rank`.

## SOPs

- Finnish SOP: `docs/sop/fi.md`
- New language template: `docs/sop/TEMPLATE.md`

## Dependency Model

- Shared pipeline (`build_lemma_assets.py`, rank/export utilities): `pip install -e .[core]`
- Language analyzers are optional extras (for example Finnish): `pip install -e .[fi]`
- English analyzer extra (LemmInflect): `pip install -e .[en]`
- If you already have a lemma CSV, you can skip analyzer dependencies:
  - `python build_lemma_assets.py --config configs/<lang>.yaml --skip-lemma --lemma-output <existing_lemma_csv>`


## Running the Pipeline

### Preparation
Prepare the freqwords file.
Ask LLM to create the yaml file for the target language.
Find suitable morph analyzer, and as LLM to create the analyzer.py for the target langauge.
We will take "en" as an example below.

### 1) Create lemmas and lemmas_rank CSV (Amend the *.yaml first!)
PYTHONPATH=src .venv/bin/python -m pipeline.build_lemma_assets --config configs/en.yaml --limit 500000

### 2) Lookup JSON
PYTHONPATH=src .venv/bin/python -m pipeline.convert_csv_json \
  output/en_500000_lemmas.csv \
  output/en_US_lookup_v1.json \
  --key en_US_lemma_lookup \
  --minify

### 3) Rank JSON
PYTHONPATH=src .venv/bin/python -m pipeline.convert_csv_json \
  output/en_500000_lemmas_rank.csv \
  output/en_US_rank_v1.json \
  --key en_US_lemma_rank \
  --minify

### 4) SQLite (both tables in one DB)
PYTHONPATH=src .venv/bin/python -m pipeline.convert_lemma_table \
  --config configs/en.yaml \
  --lookup-csv output/en_500000_lemmas.csv \
  --rank-csv output/en_500000_lemmas_rank.csv \
  --output output/en_US_dictionary_v1.sqlite \
  --replace