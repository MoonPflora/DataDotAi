from . import word_parser, image_parser
import pdfplumber
import os
import json

def pdf_has_text(pdf_path):
    """Check if PDF has meaningful selectable text (more than 1 short line)."""
    if not os.path.exists(pdf_path):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    texts.extend(text.strip().splitlines())

            # No text at all → scanned
            if not texts:
                return False

            # 1-liner or garbage → treat as scanned
            if len(texts) == 1 and len(texts[0]) < 20:
                return False

            # Sometimes it outputs "insert image here" or similar placeholders
            if all("image" in line.lower() or "paragraph" in line.lower() for line in texts):
                return False

            return True
    except Exception:
        return False


def parse_pdf(pdf_path):
    """
    Parse a PDF:
    - Meaningful selectable text → word_parser.parse_pdf_as_word
    - Empty/garbage text → image_parser.parse_image
    Returns JSON-safe output.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    try:
        if pdf_has_text(pdf_path):
            parsed = word_parser.parse_pdf_as_word(pdf_path)
        else:
            parsed = image_parser.parse_image(pdf_path)
    except Exception as e:
        parsed = [f"paragraph PDF parsing failed: {str(e)}"]

    # Ensure JSON-safe
    if not isinstance(parsed, str):
        parsed = json.dumps(parsed, ensure_ascii=False)
    else:
        try:
            json.loads(parsed)
        except json.JSONDecodeError:
            parsed = json.dumps(parsed, ensure_ascii=False)

    return parsed
