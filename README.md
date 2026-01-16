# finnish-vocab-learning-nlp

A small NLP project enable Finnish learners to learn new vocabulary. Still in its infancy.

## Data Preparation Pipeline

Follow these steps to generate the lookup and rank data for the application.

### 1. Generate Lemma Mapping
Process a Finnish frequency list to create a mapping between surface forms and their lemmas using Voikko and spaCy.
```bash
python create_lemma_table.py --limit 200000
```
*   **Input**: `freqwords/fi_100k.txt` (or other frequency list)
*   **Output**: `output/fi_200000_lemmas.csv`

### 2. Compute Lemma Ranks
Aggregate surface frequencies into lemma-level frequencies and assign ranks.
```bash
python compute_lemma_freq.py --lemma-csv output/fi_200000_lemmas.csv --freq-list freqwords/fi_100k.txt --output output/fi_200000_lemmas_rank.csv
```
*   **Rule**: (from Revision 2) When a surface form has multiple lemmas, the script now credits all frequency to the lemma that accumulated the highest total across candidates.
*   **Output**: `output/fi_200000_lemmas_rank.csv`


### 3. Export to JSON (App Assets)
Convert the CSV files to minified JSON with root keys for use in the app.
```bash
# Lookup JSON
python convert_csv_json.py output/fi_200000_lemmas.csv output/fi_FI_lookup_v1.json --key fi_FI_lemma_lookup --minify

# Rank JSON
python convert_csv_json.py output/fi_200000_lemmas_rank.csv output/fi_FI_rank_v1.json --key fi_FI_lemma_rank --minify
```

### 4. Export to SQLite
Combine both lookup and rank data into a single SQLite database.
```bash
python convert_lemma_table.py --lookup-csv output/fi_200000_lemmas.csv --rank-csv output/fi_200000_lemmas_rank.csv --output output/dictionary.sqlite --replace
```
*   **Output**: `output/dictionary.sqlite` (Tables: `fi_FI_lemma_lookup`, `fi_FI_lemma_rank`)
