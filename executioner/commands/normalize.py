import os
import json
import time
import requests

# === Constants ===
MAX_TOKENS_PER_CHUNK = 3000
MAX_RETRIES = 3
WAIT_BETWEEN_CHUNKS = 10  # seconds

# === Paths ===
EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")
PROMPT_DIR = EXECUTIONER_COMMANDS_DIR  # Prompts stored in same dir

# === Mistral API ===
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}",
    "Content-Type": "application/json"
}

# --- Token estimation ---
def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 chars"""
    return max(1, len(text) // 4)

# --- Chunking ---
def split_chunks_by_text(items: list, max_tokens: int = MAX_TOKENS_PER_CHUNK) -> list:
    """
    Split a list of JSON strings (cells or paragraphs) into chunks
    where total token estimate per chunk <= max_tokens.
    """
    chunks = []
    current_chunk = []
    token_count = 0

    for item in items:
        item_text = json.dumps(item, ensure_ascii=False)
        item_tokens = estimate_tokens(item_text)

        if token_count + item_tokens > max_tokens and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            token_count = 0

        current_chunk.append(item)
        token_count += item_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# --- Load prompt ---
def load_prompt(filetype: str) -> str:
    prompt_file = os.path.join(PROMPT_DIR, f"{filetype.lower()}_prompt.txt")
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found for filetype '{filetype}': {prompt_file}")
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()

# --- Call Mistral API ---
def call_mistral_api(batch: list, prompt: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            payload = {
                "model": "mistral-7b-chat",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
                ],
                "max_tokens": 3000
            }
            response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                raise RuntimeError(f"AI API call failed after {MAX_RETRIES} retries: {e}")

# --- Main normalization ---
def normalize(filetype: str):
    """
    Normalize current.txt content using AI. Handles chunking and merging.
    Always updates current.txt safely.
    """
    if not os.path.exists(CURRENT_FILE):
        raise FileNotFoundError(f"{CURRENT_FILE} not found")

    # Read current.txt JSON array
    with open(CURRENT_FILE, "r", encoding="utf-8") as f:
        try:
            items = json.loads(f.read())
            if not isinstance(items, list):
                raise ValueError("current.txt must contain a JSON array")
        except Exception as e:
            raise RuntimeError(f"Failed to read or parse current.txt: {e}")

    # Load AI prompt for filetype
    prompt = load_prompt(filetype)

    # Split into chunks based on token count
    chunks = split_chunks_by_text(items)
    merged_items = []

    temp_file = CURRENT_FILE + ".tmp"

    for i, chunk in enumerate(chunks):
        ai_output = call_mistral_api(chunk, prompt)
        try:
            parsed_chunk = json.loads(ai_output)
        except Exception as e:
            raise RuntimeError(f"Failed to parse AI JSON output for chunk {i}: {e}")

        if not isinstance(parsed_chunk, list):
            raise ValueError(f"AI output for chunk {i} is not a JSON array")

        merged_items.extend(parsed_chunk)

        if i < len(chunks) - 1:
            time.sleep(WAIT_BETWEEN_CHUNKS)

    # Write merged result to temp file
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(merged_items, ensure_ascii=False))

    # Atomic replace
    os.replace(temp_file, CURRENT_FILE)

    print(f"Normalization complete for filetype '{filetype}'. current.txt updated successfully.")
