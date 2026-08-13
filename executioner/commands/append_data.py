import os
import json

# Path to executioner/commands/current.txt
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")


def append_data(json_data: dict):
    """
    Append the contents of current.txt into the 'data' field of a JSON object.

    Args:
        json_data (dict): JSON object with optional 'data' field

    Returns:
        dict: Updated JSON object with 'data' field appended with current.txt content
    """
    # --- Load current.txt ---
    if os.path.exists(CURRENT_FILE):
        with open(CURRENT_FILE, "r", encoding="utf-8") as f:
            try:
                current_content = json.load(f)
            except json.JSONDecodeError:
                current_content = []
    else:
        current_content = []

    # Ensure current_content is a list
    if not isinstance(current_content, list):
        current_content = [current_content]

    # --- Prepare json_data['data'] ---
    if "data" not in json_data or not json_data["data"]:
        json_data["data"] = current_content
    else:
        try:
            existing_data = json.loads(json_data["data"])
            if not isinstance(existing_data, list):
                existing_data = [existing_data]
        except json.JSONDecodeError:
            existing_data = [json_data["data"]]

        # Append current.txt content
        existing_data.extend(current_content)
        json_data["data"] = existing_data

    # --- Return updated JSON object ---
    return json_data
