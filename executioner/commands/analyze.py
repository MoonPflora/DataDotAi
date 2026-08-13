import os
import json
import time
import requests
from config import get_working_dir

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = "YOUR_MISTRAL_API_KEY"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}
MAX_RETRIES = 3
CHUNK_SIZE = 3000  # characters per chunk
CHUNK_WAIT = 30    # seconds between chunks

EXECUTIONER_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_DIR, "current.txt")


def call_mistral_chat(prompt: str, system="You are a helpful assistant.") -> str:
    """Call Mistral API with retries."""
    payload = {
        "model": "mistral-medium-latest",
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
            response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"[Analyze] API call failed (status {response.status_code}), attempt {attempt}/{MAX_RETRIES}")
        except Exception as e:
            print(f"[Analyze] API exception: {e}, attempt {attempt}/{MAX_RETRIES}")
        time.sleep(5)

    raise RuntimeError(f"Failed to get response from AI after {MAX_RETRIES} attempts.")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE):
    """Split text into chunks of approximately chunk_size characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def analyze(json_data, *args):
    """
    Analyze current.txt content using Mistral, with optional query.
    Saves output cleanly to WORKING_DIR/[query]_analysis.txt, chunking large files.
    """
    if not args:
        raise ValueError("No query provided for analysis.")
    query = args[0]

    if not os.path.exists(CURRENT_FILE):
        raise FileNotFoundError(f"{CURRENT_FILE} not found.")

    with open(CURRENT_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("current.txt is empty.")

    # Flatten JSON lists if needed
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            text = "\n".join(parsed)
        else:
            text = str(parsed)
    except Exception:
        text = content

    chunks = chunk_text(text, CHUNK_SIZE)

    # Prepare output file in WORKING_DIR
    output_dir = get_working_dir()
    os.makedirs(output_dir, exist_ok=True)
    safe_query = "".join(c if c.isalnum() or c in "-_ " else "_" for c in query)
    output_file = os.path.join(output_dir, f"{safe_query}_analysis.txt")

    # Clear existing file
    open(output_file, "w", encoding="utf-8").close()

    # Send each chunk to AI and append result
    for i, chunk in enumerate(chunks):
        prompt = f"Analyze the following based on '{query}':\n\n{chunk}"
        response = call_mistral_chat(prompt)

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(response + "\n\n")  # Clean output, no chunk markers

        if i < len(chunks) - 1:
            time.sleep(CHUNK_WAIT)

    return f"Analysis complete. Output written to {output_file}"
