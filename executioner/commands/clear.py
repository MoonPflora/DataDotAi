import os
import json

# Path to current.txt inside executioner/commands/
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")

def clear(json_data: dict = None):
    """
    Clears the 'data' field in the passed JSON object.
    If no JSON object is passed, it just returns a log message.
    """
    if json_data is not None and isinstance(json_data, dict):
        json_data["data"] = ""
        return {"log": "JSON 'data' field cleared successfully.", "json_data": json_data}
    else:
        return {"log": "No JSON provided. Nothing cleared."}
