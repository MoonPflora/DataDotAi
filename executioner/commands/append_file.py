import os
import json
from config import get_working_dir
from .parser import *  # parse_word, parse_xlsx, parse_text, parse_image, parse_csv

# Path to current.txt inside executioner/commands/
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")


def append_file(filename: str) -> str:
    """
    Load a file from the working directory, parse it based on extension,
    and append parsed content to current.txt in a JSON-safe way.

    Supports: pdf, docx, xlsx, csv, txt, images (png, jpg, jpeg, bmp, tiff).

    Returns the JSON-safe string that was appended.
    Prints errors only.
    """
    try:
        working_dir = get_working_dir()
        filepath = os.path.normpath(os.path.join(working_dir, filename))

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # --- Infer filetype from extension ---
        ft = os.path.splitext(filename)[1][1:].lower()  # strip dot

        # --- Parsing based on file type ---
        if ft in ("pdf", "doc", "docx"):
            content = parse_word(filepath)
        elif ft in ("xls", "xlsx"):
            content = parse_xlsx(filepath)
        elif ft == "csv":
            content = parse_csv(filepath)
        elif ft in ("png", "jpg", "jpeg", "bmp", "tiff"):
            content = parse_image(filepath)
        elif ft == "txt":
            content = parse_text(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ft}")

        # --- Ensure JSON-safe string ---
        if not isinstance(content, str):
            content_to_write = json.dumps(content, ensure_ascii=False)
            new_data = content
        else:
            try:
                loaded = json.loads(content)
                new_data = loaded
                content_to_write = content
            except json.JSONDecodeError:
                new_data = [content]  # wrap string as list
                content_to_write = json.dumps(new_data, ensure_ascii=False)

        # --- Read existing current.txt ---
        if os.path.exists(CURRENT_FILE):
            try:
                with open(CURRENT_FILE, "r", encoding="utf-8") as rf:
                    existing = json.load(rf)
                    if not isinstance(existing, list):
                        existing = [existing]
            except Exception:
                existing = []
        else:
            existing = []

        # --- Merge new_data into existing ---
        if isinstance(new_data, list):
            merged = existing + new_data
        else:
            merged = existing + [new_data]

        # --- Write merged content back ---
        with open(CURRENT_FILE, "w", encoding="utf-8") as wf:
            json.dump(merged, wf, ensure_ascii=False, indent=2)

        return json.dumps(merged, ensure_ascii=False)

    except Exception as e:
        print(f"Error in append_file(): {e}")
        return ""
