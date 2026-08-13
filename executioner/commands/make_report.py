import os
import time
import requests
from config import get_working_dir

# Constants
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = "YOUR_MISTRAL_API_KEY"  # replace with your real key
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}
MAX_RETRIES = 3
CHUNK_TOKENS = 3000          # Rough chunk size (approx chars)
CHUNK_DELAY = 30             # seconds between chunks

# Path to current.txt inside executioner/commands/
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")


def call_mistral_chat(prompt: str, system="You are a helpful assistant.") -> str:
    """Call Mistral API with retries and return AI response."""
    payload = {
        "model": "mistral-medium",
        "temperature": 0.3,
        "top_p": 1,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return content
        except Exception as e:
            print(f"[make_report] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            time.sleep(5)
    raise RuntimeError(f"Failed to get AI response after {MAX_RETRIES} attempts.")


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of max_chars size, preserving lines."""
    lines = text.splitlines()
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) + 1 > max_chars:
            if current:
                chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks


def make_report(filepath: str) -> dict:
    """
    Generate a report from a file in the working directory.
    Writes output to [filename]_report.txt in the same folder.
    First chunk starts the report immediately.
    Subsequent chunks continue the report with chunk context.
    """
    working_dir = get_working_dir()
    filename = os.path.basename(filepath)
    file_base, _ = os.path.splitext(filename)
    input_path = os.path.join(working_dir, filepath)

    if not os.path.exists(input_path):
        return {"log": f"Error: file not found: {input_path}"}

    analysis_path = os.path.join(working_dir, f"{file_base}_report.txt")

    # Read input content
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        return {"log": f"Error reading file: {e}"}

    if not text.strip():
        return {"log": "Error: file is empty."}

    # Chunk content
    chunks = chunk_text(text, CHUNK_TOKENS)

    # Remove old analysis file if exists
    if os.path.exists(analysis_path):
        os.remove(analysis_path)

    for idx, chunk in enumerate(chunks, start=1):
        if idx == 1:
            # First chunk → start report immediately
            prompt = (
                f"Write a detailed text report for the following content. "
                f"Do not say 'here is' or give explanations, just start writing the report immediately:\n\n{chunk}"
            )
        else:
            # Subsequent chunks → continue report
            prompt = (
                f"This is a continuation chunk ({idx}/{len(chunks)}). "
                f"Continue the report from the previous content, keeping the style and context:\n\n{chunk}"
            )

        try:
            answer = call_mistral_chat(prompt)
        except Exception as e:
            return {"log": f"Error in AI call for chunk {idx}: {e}"}

        # Append AI response only
        with open(analysis_path, "a", encoding="utf-8") as f:
            f.write(answer + "\n")

        if idx < len(chunks):
            time.sleep(CHUNK_DELAY)

    return {"log": f"Report generated successfully: {analysis_path}"}
