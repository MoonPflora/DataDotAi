import os
import json

# Path to executioner/commands/current.txt
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")

def get():
    """
    Reads current.txt and returns its content as a JSON-safe string
    for the 'data' field. Preserves exact content (including slashes
    and quotes) without altering it.
    Returns empty JSON array "[]" if file missing or empty.
    """
    if not os.path.exists(CURRENT_FILE):
        return json.dumps([])  # empty JSON array

    try:
        with open(CURRENT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return json.dumps([])  # empty JSON array

        # Wrap the raw content as a JSON string
        return json.dumps(content, ensure_ascii=False)

    except Exception as e:
        # Return error as JSON string
        return json.dumps(f"Error reading current.txt: {str(e)}", ensure_ascii=False)
