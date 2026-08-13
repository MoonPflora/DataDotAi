import os
import json

def unparse_text(parsed_json_str, output_txt_path):
    """
    Write a JSON list of lines back to a plain .txt file with proper line breaks.
    """
    # Decode JSON if necessary
    if isinstance(parsed_json_str, str):
        try:
            lines = json.loads(parsed_json_str)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string passed to unparse_text")
    else:
        lines = parsed_json_str

    # Ensure lines is a list
    if not isinstance(lines, list):
        raise ValueError("Parsed text must be a JSON list")

    # Make sure each element is a string
    lines = [str(line) for line in lines]

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)

    # Write lines with proper line breaks
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
