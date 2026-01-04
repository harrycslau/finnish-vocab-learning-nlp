import csv
import json
import sys
import argparse

# Usage 1: python convert_csv_json.py output/fi_200000_lemmas_rank.csv output/fi_FI_rank_v1.json --key fi_FI_lemma_rank --minify
# Usage 2: python convert_csv_json.py output/fi_200000_lemmas.csv output/fi_FI_lookup_v1.json --key fi_FI_lemma_lookup --minify

def convert_csv_to_json(input_file, output_file, root_key=None, indent=2):
    """
    Converts a CSV file to a JSON file.

    Reads the CSV and converts it to a JSON array of objects.
    If root_key is provided, wraps the array in a dictionary with that key.
    """
    try:
        with open(input_file, mode='r', encoding='utf-8-sig') as csv_file:
            # Use DictReader to read CSV rows as dictionaries.
            # The first row is automatically used as the keys (headers).
            csv_reader = csv.DictReader(csv_file)
            
            # Convert all rows to a list
            rows = list(csv_reader)
            
            # Prepare output data
            if root_key:
                data = {root_key: rows}
            else:
                data = rows
            
            # Write to JSON file
            with open(output_file, mode='w', encoding='utf-8') as json_file:
                separators = (',', ':') if indent is None else None
                json.dump(data, json_file, ensure_ascii=False, indent=indent, separators=separators)
                    
        print(f"Successfully converted '{input_file}' to '{output_file}' ({len(rows)} records).")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV to JSON")
    parser.add_argument("input_file", help="Input CSV file path")
    parser.add_argument("output_file", help="Output JSON file path")
    parser.add_argument("--key", help="Optional root key to wrap the array", default=None)
    parser.add_argument("--tabs", action="store_true", help="Use tabs for indentation (saves space vs spaces)")
    parser.add_argument("--minify", action="store_true", help="Minify output (removes all whitespace for min storage)")
    
    args = parser.parse_args()
    
    if args.minify:
        indent = None
    elif args.tabs:
        indent = '\t'
    else:
        indent = 2
    
    convert_csv_to_json(args.input_file, args.output_file, args.key, indent)
