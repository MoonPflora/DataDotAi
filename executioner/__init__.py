import json
import time
from .core import execute_actions


def handle_message(json_str: str) -> str:
    """Route JSON to correct target after executing actions in core."""

    def error_response(msg):
        return json.dumps({
            "message": "",
            "action": [],
            "data": "",
            "history": [],
            "folder": [],
            "error": msg,
            "target": ["ai"]
        })

    try:
        json_data = json.loads(json_str)
    except json.JSONDecodeError:
        return error_response("Invalid JSON")

    # Ensure mandatory fields exist
    for key in ("message", "action", "data", "history", "input", "error", "target"):
        if key not in json_data:
            json_data[key] = "" if key in ("message", "data", "error") else []

    # Execute actions if present
    if json_data.get("action"):
        try:
            updated_json = execute_actions(json_data)
            # Handle 'get' special case
            if updated_json.get("data") and "get" in (updated_json.get("history")[-1] if updated_json.get("history") else ""):
                updated_json["target"] = ["ai"]
                updated_json["action"] = []

            # Clear action for successful executions
            updated_json["action"] = []

            # Small delay before returning
            time.sleep(3)
            return json.dumps(updated_json, ensure_ascii=False)

        except Exception as e:
            return error_response(f"Execution failed: {e}")

    # No action → send to terminal
    json_data["target"] = ["terminal"]
    return json.dumps(json_data, ensure_ascii=False)
