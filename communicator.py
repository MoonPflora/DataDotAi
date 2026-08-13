# communicator.py
import os
import json
import requests
import time
from queue import Queue
from dotenv import load_dotenv

from executioner.core import execute_actions  # core executor

# --- Load environment ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY not found in .env")

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

# --- AI response queue ---
_ai_response_queue = Queue()
MAX_RETRIES = 3
MAX_HISTORY = 10

# --- Send functions ---

def send_to_terminal(json_data: dict):
    """Queue JSON to terminal. Silent on success."""
    try:
        _ai_response_queue.put(json.dumps(json_data, ensure_ascii=False))
    except Exception as e:
        print(f"Error sending to terminal: {e}")


def send_to_executioner(json_data: dict):
    """Send JSON to executioner and queue updated JSON to terminal."""
    try:
        updated_json = execute_actions(json_data)
        incoming_history = json_data.get("history", [])
        new_history = [h for h in updated_json.get("history", []) if h not in incoming_history]
        updated_json["history"] = incoming_history + new_history

        # Ensure terminal is a target
        targets = updated_json.get("target", [])
        if "terminal" not in targets:
            targets.append("terminal")
        updated_json["target"] = targets

        _ai_response_queue.put(json.dumps(updated_json, ensure_ascii=False))
    except Exception as e:
        print(f"Error in send_to_executioner: {e}")


def send_to_ai(json_data: dict):
    """Send JSON to AI. Handles retries and preserves history/folder."""
    incoming_history = json_data.get("history", [])
    incoming_folder = json_data.get("folder", {})

    system_prompt = """
You are an AI assistant. Respond ONLY with a JSON object like this:
{
  "message": "<your response here>",
  "action": [],
  "data": "",
  "history": [],
  "folder": {},
  "error": "",
  "target": ["terminal"]
}
Do NOT use markdown code blocks or extra formatting.
"""

    payload = {
        "model": "mistral-medium",
        "temperature": 0.3,
        "top_p": 1,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(json_data, ensure_ascii=False)}
        ]
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
            resp.raise_for_status()
            ai_content = resp.json()["choices"][0]["message"]["content"].strip()

            try:
                ai_json = json.loads(ai_content)
            except Exception:
                # Wrap plain text in schema
                ai_json = {
                    "message": ai_content,
                    "action": [],
                    "data": "",
                    "history": [],
                    "folder": {},
                    "error": "",
                    "target": ["terminal"]
                }

            # Merge history and preserve folder
            ai_json["history"] = incoming_history + [h for h in ai_json.get("history", []) if h not in incoming_history]
            ai_json["folder"] = incoming_folder
            if "terminal" not in ai_json.get("target", []):
                ai_json["target"].append("terminal")

            _ai_response_queue.put(json.dumps(ai_json, ensure_ascii=False))
            return  # silent on success

        except Exception as e:
            print(f"⚠️ Retry {attempt+1}/{MAX_RETRIES} failed: {e}")
            time.sleep(5)

    # Failed all retries
    error_json = {
        "message": "Failed to contact AI API",
        "action": [],
        "data": "",
        "history": incoming_history.copy(),
        "folder": incoming_folder.copy(),
        "error": "Failed to contact AI API",
        "target": ["terminal"]
    }
    _ai_response_queue.put(json.dumps(error_json, ensure_ascii=False))


# --- Receive function ---

def receive_from_ai() -> str:
    """Get JSON from AI queue. Silent if empty."""
    if _ai_response_queue.empty():
        return ""
    resp_str = _ai_response_queue.get()
    try:
        resp_json = json.loads(resp_str)
        # Clear sensitive fields for terminal display
        resp_json["error"] = ""
        resp_json["folder"] = {}  # preserve schema as dict
        return json.dumps(resp_json, ensure_ascii=False)
    except Exception:
        return resp_str


# --- Utilities ---

def truncate_history(json_data: dict):
    """Keep last MAX_HISTORY items."""
    history = json_data.get("history", [])
    if len(history) > MAX_HISTORY:
        json_data["history"] = history[-MAX_HISTORY:]


def get_folder_tree(path: str):
    """Recursively return folder structure."""
    tree = {}
    try:
        for entry in os.scandir(path):
            if entry.is_dir():
                tree[entry.name] = get_folder_tree(os.path.join(path, entry.name))
            else:
                tree[entry.name] = None
    except Exception as e:
        tree = {"error": str(e)}
    return tree


# --- Main router ---

def handle_message(json_str: str):
    """Route incoming JSON messages to AI, executioner, or terminal."""
    try:
        json_data = json.loads(json_str)
    except json.JSONDecodeError:
        error_json = {
            "message": "",
            "action": [],
            "data": "",
            "history": [],
            "folder": {},
            "error": "Invalid JSON",
            "target": ["ai"]
        }
        _ai_response_queue.put(json.dumps(error_json, ensure_ascii=False))
        return

    truncate_history(json_data)

    error = json_data.get("error", "")
    action = json_data.get("action", [])
    target = [t.lower() for t in json_data.get("target", [])]

    # --- Error: send to AI ---
    if error:
        send_to_ai(json_data)
        return

    # --- Executioner action ---
    if action or "executioner" in target:
        send_to_executioner(json_data)
        return

    # --- Terminal message ---
    if (not action or len(action) == 0) and "terminal" in target:
        send_to_terminal(json_data)
        return

    # --- Fallback ---
    send_to_ai(json_data)
