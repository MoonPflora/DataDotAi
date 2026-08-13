import os
import csv
import json
from config import get_working_dir

def escape_cell(value):
    """Escape quotes, backslashes, and newlines for JSON safety."""
    if value is None:
        return ""
    return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

def parse_csv(filename):
    """
    Parse a CSV file from the working directory and return unified parser output as JSON-safe string.

    Output format per cell: "sheet,row,col,\"value\""
    Silent on success; prints errors only.
    """
    try:
        working_dir = get_working_dir()
        rel_path = filename if filename.lower().endswith(".csv") else f"{filename}.csv"
        filepath = os.path.normpath(os.path.join(working_dir, rel_path))

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        parsed_lines = []
        sheet_name = "sheet 0"  # CSV has only one sheet
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row_i, row in enumerate(reader):
                for col_i, cell in enumerate(row):
                    cell_text = escape_cell(cell)
                    parsed_lines.append(f'{sheet_name},{row_i},{col_i},"{cell_text}"')

        # Return JSON-safe string instead of writing to current.txt
        return json.dumps(parsed_lines, ensure_ascii=False)

    except Exception as e:
        print(f"Error in parse_csv(): {e}")
        return json.dumps([])
