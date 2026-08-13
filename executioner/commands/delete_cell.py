import json
import os

def delete_cells_json(current_file, *cells):
    """
    Delete specific cells from a JSON array like our unparsed current.txt format.

    Args:
        current_file (str): Path to current.txt
        *cells: Variable number of (row, col) pairs to delete
            Example: delete_cells_json("current.txt", (1,2), (3,4))
    """
    if not os.path.exists(current_file):
        raise FileNotFoundError(f"{current_file} not found.")

    with open(current_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return "current.txt is not valid JSON."

    new_data = []
    for item in data:
        try:
            parts = item.split(",", 3)  # Sheet,row,col,value
            row_idx = int(parts[1])
            col_idx = int(parts[2])
        except Exception:
            new_data.append(item)  # keep invalid lines
            continue

        if (row_idx, col_idx) not in cells:
            new_data.append(item)

    with open(current_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(new_data, ensure_ascii=False))

    return f"Deleted {len(data)-len(new_data)} cells from {os.path.basename(current_file)}"
