import os
import json
from config import get_working_dir
from .parser import *  # parse_word, parse_xlsx, parse_text, parse_image, parse_csv

# Path to current.txt inside executioner/commands/
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")


def load(filename: str) -> str:
    """
    Load a file from the working directory, parse it based on extension,
    write parsed content to current.txt, and return JSON-safe string.

    Silent on success; prints errors only.
    Supports: pdf, docx, xlsx, csv, txt, images (png, jpg, jpeg, bmp, tiff).
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
            content = parse_word(filepath)  # unified call for all Word/PDF files
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
        else:
            try:
                json.loads(content)
                content_to_write = content
            except json.JSONDecodeError:
                content_to_write = json.dumps(content, ensure_ascii=False)

        # --- Write parsed content to current.txt ---
        with open(CURRENT_FILE, "w", encoding="utf-8") as wf:
            wf.write(content_to_write)

        return content_to_write

    except Exception as e:
        print(f"Error in load(): {e}")
        return ""
