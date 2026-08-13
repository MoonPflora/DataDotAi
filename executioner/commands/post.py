import os
import json

EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")

def post(data: str):
    """
    Appends/merges 'data' into current.txt safely.
    - Loads existing JSON, wraps into list if invalid.
    - Unwraps input JSON string if possible.
    - Always produces valid JSON.
    - Preserves arrays and merges by extending.
    """
    # Step 1: Load current.txt
    if os.path.exists(CURRENT_FILE):
        try:
            with open(CURRENT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    else:
        existing = []

    # Ensure existing is list
    if not isinstance(existing, list):
        existing = [existing]

    # Step 2: Parse incoming data
    if not data:
        new_data = []
    else:
        try:
            parsed = json.loads(data)
            new_data = parsed if isinstance(parsed, (list, dict)) else [parsed]
        except json.JSONDecodeError:
            new_data = [data]

    # Step 3: Merge
    if isinstance(new_data, list):
        existing.extend(new_data)
    else:
        existing.append(new_data)

    # Step 4: Save back
    with open(CURRENT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False)

    return {"log": "current.txt merged with posted data."}
