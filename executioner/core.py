import os
import json
import time
from config import get_working_dir

# Import all commands
from .commands import *

# Path to current.txt inside executioner
EXECUTIONER_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_DIR, "current.txt")

# Commands dictionary
COMMANDS = {
    "load": load,
    "save": save,
    "append": append,
    "delete_cells_json": delete_cells_json,
    "delete_row": delete_row,
    "filter_excel": filter,
    "post": post,
    "clear": clear,
    "get": get,
    "analyze": analyze,
    "make_report": make_report,
}

# --- Utilities ---
def split_commands_balanced(line: str) -> list[str]:
    """Split a line like 'load("Book1","xlsx"), save()' into individual commands"""
    commands = []
    bracket_level = 0
    current = []
    i = 0
    while i < len(line):
        char = line[i]
        if char == '(':
            bracket_level += 1
            current.append(char)
        elif char == ')':
            bracket_level -= 1
            current.append(char)
        elif char == ',' and bracket_level == 0:
            cmd = ''.join(current).strip()
            if cmd:
                commands.append(cmd)
            current = []
        else:
            current.append(char)
        i += 1
    cmd = ''.join(current).strip()
    if cmd:
        commands.append(cmd)
    return commands

def parse_command_args(cmd_str: str):
    """
    Parse a command string like 'load(Book1,xlsx)' into ('load', ['Book1','xlsx'])
    Strips quotes from arguments.
    """
    if '(' not in cmd_str:
        return cmd_str.strip(), []

    name_part, args_part = cmd_str.split('(', 1)
    name = name_part.strip()
    args_str = args_part.rsplit(')', 1)[0].strip()

    args = []
    current_arg = []
    bracket_level = 0
    for char in args_str:
        if char == ',' and bracket_level == 0:
            arg = ''.join(current_arg).strip().strip('"').strip("'")
            if arg:
                args.append(arg)
            current_arg = []
        else:
            if char == '(':
                bracket_level += 1
            elif char == ')':
                bracket_level -= 1
            current_arg.append(char)
    last_arg = ''.join(current_arg).strip().strip('"').strip("'")
    if last_arg:
        args.append(last_arg)

    return name, args

# --- Main executor ---
def execute_actions(json_data: dict) -> dict:
    """
    Executes commands in json_data['action'], passing arguments automatically.
    Handles retries, writes/reads current.txt, preserves history and folder,
    and returns updated JSON.
    """
    json_data.setdefault("history", [])
    json_data.setdefault("folder", {})  # Preserve folder as dict

    action_str = json_data.get("action", "")
    if not action_str:
        json_data["target"] = ["terminal"]
        return json_data

    working_dir = get_working_dir()
    commands = split_commands_balanced(action_str)

    for cmd_str in commands:
        try:
            # Read current.txt
            current_content = ""
            if os.path.exists(CURRENT_FILE):
                with open(CURRENT_FILE, "r", encoding="utf-8") as f:
                    current_content = f.read()

            # Parse command
            name, args = parse_command_args(cmd_str)
            if name not in COMMANDS:
                raise ValueError(f"Unknown command: '{name}'")

            command_func = COMMANDS[name]

            # Retry logic
            for attempt in range(3):
                try:
                    updated_content = command_func(*args)
                    if updated_content is not None:
                        current_content = updated_content
                        # Write immediately after command
                        with open(CURRENT_FILE, "w", encoding="utf-8") as f:
                            f.write(current_content)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(3)
                    else:
                        raise

            # Special case for get(): return to AI
            if name == "get":
                json_data["data"] = current_content
                json_data["target"] = ["ai"]
                json_data["action"] = []
                return json_data

            json_data.setdefault("history", []).append(f"Command '{name}' executed successfully.")

            # Clear data field for post/clear commands
            if name in ("post", "clear"):
                json_data["data"] = ""

        except Exception as e:
            json_data["message"] = ""
            json_data["action"] = ""
            json_data.setdefault("history", []).append(f"Error: {str(e)}")
            json_data["error"] = str(e)
            json_data["target"] = ["ai"]
            json_data.setdefault("folder", {})  # preserve folder even on error
            return json_data

    json_data["error"] = ""
    json_data["action"] = []
    json_data["target"] = ["terminal"]

    return json_data
