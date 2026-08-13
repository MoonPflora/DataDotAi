import os
import tempfile
import json
import win32com.client
import openpyxl

# --- Helpers ---
def parse_xlsx(xlsx_path):
    """
    Parse an .xlsx file into JSON-safe strings.
    Format for each non-empty cell:
        SheetName,rowIndex,columnIndex,"cellValue"
    """
    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        parsed_cells = []

        for sheet in wb.worksheets:
            sheet_name = sheet.title.strip() or "Sheet"
            for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                for c_idx, val in enumerate(row):
                    if val is None or (isinstance(val, str) and val.strip() == ""):
                        continue  # skip empty cells
                    cell_text = str(val)
                    parsed_cells.append(f'{sheet_name},{r_idx},{c_idx},"{cell_text}"')

        return json.dumps(parsed_cells, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Failed to parse XLSX file {xlsx_path}: {e}")

# --- XLS → XLSX conversion using Excel COM ---
def _convert_xls_to_xlsx(xls_path):
    """
    Convert .xls → .xlsx using Excel COM (Windows only).
    Returns path to temporary .xlsx file.
    Fully silent: no prompts, no replace dialogs.
    """
    if not os.path.exists(xls_path):
        raise FileNotFoundError(f"File not found: {xls_path}")

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False  # suppress prompts (replace, etc.)
    try:
        wb = excel.Workbooks.Open(os.path.abspath(xls_path), ReadOnly=False)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(tmp_fd)
        wb.SaveAs(tmp_path, FileFormat=51)  # 51 = xlOpenXMLWorkbook (.xlsx)
        wb.Close(False)
    finally:
        excel.Quit()
    return tmp_path


# --- Main parser ---
def parse_excel(filepath):
    """
    Parse Excel file (.xls or .xlsx) into JSON-safe string.
    - .xlsx → openpyxl
    - .xls → converted to .xlsx via Excel COM, then parsed
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".xlsx":
        return _parse_xlsx(filepath)
    elif ext == ".xls":
        tmp_xlsx = _convert_xls_to_xlsx(filepath)
        try:
            return _parse_xlsx(tmp_xlsx)
        finally:
            if os.path.exists(tmp_xlsx):
                os.remove(tmp_xlsx)
    else:
        raise ValueError(f"Unsupported Excel file extension: {ext}")
