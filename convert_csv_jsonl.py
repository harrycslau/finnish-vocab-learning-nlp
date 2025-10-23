import csv
import json
import sys

def convert_csv_to_jsonl(input_file, output_file):
    """
    Converts a CSV file to a JSONL (NDJSON) file.

    Each row in the CSV (read as a dictionary) is converted to
    a JSON object on a new line in the output file.
    """
    try:
        with open(input_file, mode='r', encoding='utf-8-sig') as csv_file:
            # Use DictReader to read CSV rows as dictionaries.
            # The first row is automatically used as the keys (headers).
            # 'utf-8-sig' handles potential BOM (Byte Order Mark) at the start of the file.
            csv_reader = csv.DictReader(csv_file)

            with open(output_file, mode='w', encoding='utf-8') as jsonl_file:
                # Iterate over each row in the CSV
                for row in csv_reader:
                    # Convert the dictionary (row) to a JSON string
                    json_line = json.dumps(row, ensure_ascii=False)
                    
                    # Write the JSON string followed by a newline character
                    jsonl_file.write(json_line + '\n')
                    
        print(f"Successfully converted '{input_file}' to '{output_file}'.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    # This block makes the script runnable from the command line
    
    if len(sys.argv) != 3:
        print("\nUsage: python convert_csv_jsonl.py <input_csv_file> <output_jsonl_file>\n")
        print("Example: python convert_csv_jsonl.py data.csv data.jsonl\n")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    convert_csv_to_jsonl(input_path, output_path)
