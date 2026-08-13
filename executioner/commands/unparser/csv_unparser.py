import csv
import json
import re

def unparse_csv(parsed_json_str, output_csv_path):
    """
    Reverse the CSV parser output back into a CSV file.

    Input: JSON string containing text in this format:
      SheetName:
      row,col,"value";
      ...
    """

    # Decode JSON string to get the text with proper escapes handled
    try:
        parsed_text = json.loads(parsed_json_str)
    except Exception as e:
        raise ValueError(f"Invalid JSON input: {e}")

    lines = parsed_text.splitlines()
    if not lines:
        raise ValueError("Empty input text")

    # First line is sheet name, e.g. "Sheet 0:"
    sheet_name = lines[0].rstrip(":").strip()

    # Collect cell data into dict[row][col] = value
    cell_data = {}

    max_row = -1
    max_col = -1

    # Regex to parse lines like: 0,1,"some value";
    pattern = re.compile(r'(\d+),(\d+),"((?:[^"\\]|\\.)*)";')

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        m = pattern.match(line)
        if not m:
            continue

        r, c, val = m.groups()
        r, c = int(r), int(c)

        # Unescape quotes and backslashes
        val = val.replace('\\\\', '\\').replace('\\"', '"')

        if r not in cell_data:
            cell_data[r] = {}
        cell_data[r][c] = val

        if r > max_row:
            max_row = r
        if c > max_col:
            max_col = c

    # Build rows list for CSV, filling missing cells with empty strings
    rows = []
    for r in range(max_row + 1):
        row = []
        for c in range(max_col + 1):
            cell_val = cell_data.get(r, {}).get(c, "")
            row.append(cell_val)
        rows.append(row)

    # Write the rows into CSV file
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
