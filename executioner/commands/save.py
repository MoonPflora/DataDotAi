import os
import json
import tempfile
from config import get_working_dir
from .unparser import excel_unparser, word_unparser, txt_unparser, csv_unparser, pdf_unparser

try:
    import win32com.client
except ImportError:
    win32com = None

EXECUTIONER_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_FILE = os.path.join(EXECUTIONER_COMMANDS_DIR, "current.txt")

def save(output_filename: str):
    """
    Save current.txt back to a file using the extension in output_filename to determine format.
    Excel and Word use temp files + win32com automation.
    Other types use Python unparsers directly.
    Returns JSON string of the parsed content.
    Example usage: save("new.xlsx"), save("report.pdf")
    """
    if not os.path.exists(CURRENT_FILE):
        raise FileNotFoundError(f"{CURRENT_FILE} not found")

    # Read current.txt
    with open(CURRENT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure parsed_text is a Python object
    try:
        parsed_text = json.loads(content)
    except json.JSONDecodeError:
        parsed_text = content

    # Extract extension and normalize
    base_name, ext = os.path.splitext(output_filename)
    if not ext:
        raise ValueError("Output filename must include extension, e.g., 'new.xlsx'")
    new_filetype = ext[1:].lower()

    ext_map = {
        "xls": "xlsx",
        "xlsx": "xlsx",
        "excel": "xlsx",
        "doc": "docx",
        "docx": "docx",
        "word": "docx"
    }
    normalized_ext = ext_map.get(new_filetype, new_filetype)
    output_filename = f"{base_name}.{normalized_ext}"

    # Ensure working directory exists
    working_dir = get_working_dir()
    os.makedirs(working_dir, exist_ok=True)
    output_path = os.path.join(working_dir, output_filename)

    # --- Excel / Word handling via temp + win32com ---
    try:
        if normalized_ext in ("xlsx", "docx"):
            if win32com is None:
                raise ImportError("win32com.client required for Excel/Word automation")

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{normalized_ext}") as tmp:
                temp_path = tmp.name

            if normalized_ext == "xlsx":
                excel_unparser.unparse_excel(parsed_text, temp_path)
                excel_app = win32com.client.Dispatch("Excel.Application")
                excel_app.DisplayAlerts = False
                wb = excel_app.Workbooks.Open(temp_path)
                wb.SaveAs(os.path.abspath(output_path))
                wb.Close(SaveChanges=True)
                excel_app.Quit()
            elif normalized_ext == "docx":
                word_unparser.unparse_word(parsed_text, temp_path)
                word_app = win32com.client.Dispatch("Word.Application")
                word_app.DisplayAlerts = 0
                doc = word_app.Documents.Open(temp_path)
                doc.SaveAs(os.path.abspath(output_path))
                doc.Close(False)
                word_app.Quit()

            os.remove(temp_path)

        # --- Other types directly via Python unparser ---
        elif normalized_ext == "csv":
            csv_unparser.unparse_csv(parsed_text, output_path)
        elif normalized_ext == "txt":
            txt_unparser.unparse_text(parsed_text, output_path)
        elif normalized_ext == "pdf":
            pdf_unparser.unparse_pdf(parsed_text, output_path)
        else:
            raise ValueError(f"Unsupported output file type: {normalized_ext}")

    except Exception as e:
        raise RuntimeError(f"[save] Failed to save file {output_filename}: {e}")

    # Return JSON string for communicator
    if isinstance(parsed_text, (list, dict)):
        return json.dumps(parsed_text, ensure_ascii=False)
    else:
        return json.dumps([parsed_text], ensure_ascii=False)
