import os
import json

def parse_text(txt_path):
    """
    Parse a .txt file into a JSON-safe array of lines.
    Each line becomes an element in a list, similar to other parsers.
    """
    if not os.path.exists(txt_path):
        return json.dumps([f"File not found: {txt_path}"], ensure_ascii=False)

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    return json.dumps(lines, ensure_ascii=False)
