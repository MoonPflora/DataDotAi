<p align="center">
  <img src="ai.ico" alt="DataDotAI Logo" width="180">
</p>

<h1 align="center">DataDotAI</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3">
</p>

<p align="center">
  <b>A Python-based DSL Communication Tool that bridges natural language, AI, and file operations through a strict JSON-based protocol.</b>
</p>

---

## Overview

DataDotAI is a Python application that understands file operations through a **Domain-Specific Language (DSL)**. It connects a terminal interface, an AI backend, and a file execution engine into a seamless pipeline for reading, writing, analyzing, and transforming documents.

**Architecture goal:** Support both **local AI models** (e.g., fine-tuned Llama, Gemma) and **cloud API providers** (e.g., Mistral, OpenAI, Anthropic).  
**Current status:** API-only mode (Mistral) for ease of testing. Local model support is planned via the `Finetune/` pipeline.

Instead of fine-tuning the AI on every possible command (which fails due to hardware limits and poor generalization), DataDotAI uses a **regex/embedded command system** where the AI pulls command descriptions from a structured registry when it needs to execute an action. Future versions will replace this with a **vector database** for semantic command retrieval.

---

## Architecture

```
┌─────────────┐
│   Terminal  │  ← User types natural language
└──────┬──────┘
       │ Sends JSON → handle_message(json_str)
       ▼
┌───────────────────────────────┐
│ Communicator: handle_message  │
│  1. Parse JSON                │
│  2. Route to AI / Executioner │
│  3. Manage history & retries  │
└──────┬────────────────────────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌─────────────┐
│  AI  │ │ Executioner │ ← Executes file commands
│Mistral│ │  (core.py)  │
└──┬───┘ └──────┬──────┘
   │            │
   └──────┬─────┘
          ▼
   ┌─────────────┐
   │   Terminal  │  ← User sees results
   └─────────────┘
```

### Three Main Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Terminal** | `Terminal.py` | CLI UI, session management, folder tree building, user input/output |
| **Communicator** | `Communicator.py` | JSON routing between Terminal ↔ AI ↔ Executioner, retry logic, history management |
| **Executioner** | `Executioner/core.py` + `Executioner/commands/` | Parses action strings, executes file operations, manages `current.txt` as working memory |

---

## JSON Communication Schema

All messages between components follow this strict envelope. Every field has a specific contract — who writes it, who reads it, and what rules govern it.

### The JSON Envelope

```json
{
  "message": "Human-readable text from AI",
  "action": "load(file.xlsx),save(new.docx)",
  "data": "[\"Sheet1,0,0,\\\"Name\\\"\", \"Sheet1,0,1,\\\"Age\\\"\"]",
  "history": ["User asked to convert Excel to Word"],
  "folder": {},
  "error": "",
  "session_id": "uuid-here",
  "target": ["terminal"]
}
```

### Field-by-Field Contract

| Field | Type | Who Writes | Who Reads | Mutable | Rules |
|-------|------|------------|-----------|---------|-------|
| `message` | string | AI | Terminal | ✅ | Conversation text only. Can include markdown (`**bold**`, `*italic*`, lists). **Never** contains commands. AI explains actions, asks questions, or reports results here. |
| `action` | string | AI | Executioner | ✅ | Comma-separated command sequence. **Lowercase, no spaces.** Example: `load(a.xlsx),save(b.docx)`. Arguments preserve case. No escaping or newlines inside arguments. |
| `data` | string | Executioner / AI | Executioner / AI | ✅ | Payload for read/write. Always a **JSON-safe flat array of strings**. When written by Executioner, it's the result of `get()` or file parsing. When written by AI, it's data to be posted to `current.txt`. |
| `history` | array | AI | AI (context) | ✅ | One-liner summaries of **user requests, errors, or context**. AI **never** logs its own commands here. Backend logs executed actions. Copy existing history entirely, append new lines only. Keep short for token efficiency. |
| `folder` | object | Terminal | Terminal | ❌ | Snapshot of the working directory. AI **always** responds with empty `{}` to save tokens. Never copies or edits this field from received JSON. |
| `error` | string | Executioner / Communicator | AI | ✅ | Backend error string. AI resolves errors internally — never sets this field directly. If unresolvable, AI uses `clear()` command and appends a short note in `history`. |
| `session_id` | string | Terminal | All | ❌ | Unique session ID. Copied verbatim by every component. Never modified. |
| `target` | array | AI / Communicator | Communicator | ✅ | Routing directive. `["terminal"]` = display to user. `["executioner"]` = run commands. `["ai"]` = process by AI. Can combine: `["executioner", "terminal"]`. |

### Routing Rules (Communicator)

The Communicator is the central router. It decides where each JSON message goes based on this priority order:

```
1. Invalid JSON format        → Wrap in error JSON → send_to_ai
2. error field is non-empty   → send_to_ai (AI resolves)
3. action field exists        → send_to_executioner
4. target includes "executioner" → send_to_executioner
5. target includes "terminal" AND no action → send_to_terminal
6. Default fallback           → send_to_ai
```

**Why this matters:** The AI never decides routing directly. It sets `target` and `action`, and the Communicator enforces the rules. This prevents infinite loops and ensures errors always reach the AI for resolution.

### Example Lifecycle

**Step 1 — User asks a question:**
```json
{
  "message": "Convert my budget spreadsheet to a Word document",
  "action": "",
  "data": "",
  "history": [],
  "folder": {"budget.xlsx": {}, "report.docx": {}},
  "error": "",
  "session_id": "sess_abc123",
  "target": ["ai"]
}
```
→ Communicator sees `target: ["ai"]`, no action → sends to AI.

**Step 2 — AI responds with commands:**
```json
{
  "message": "I converted 'budget.xlsx' to 'budget.docx'.",
  "action": "load(budget.xlsx),save(budget.docx)",
  "data": "",
  "history": ["User asked to convert Excel to Word"],
  "folder": {},
  "error": "",
  "session_id": "sess_abc123",
  "target": ["executioner"]
}
```
→ Communicator sees `action` → sends to Executioner.

**Step 3 — Executioner runs commands, returns result:**
```json
{
  "message": "I converted 'budget.xlsx' to 'budget.docx'.",
  "action": "",
  "data": "",
  "history": ["User asked to convert Excel to Word", "Loaded budget.xlsx", "Saved budget.docx"],
  "folder": {},
  "error": "",
  "session_id": "sess_abc123",
  "target": ["terminal"]
}
```
→ Communicator sees `target: ["terminal"]`, no action → sends to Terminal for display.

---

## Command Reference

Commands are written in action strings as `command(arg1,arg2)`. They are executed sequentially, separated by commas.

### `load(filename.ext)`
Loads a file from the working directory into `current.txt`, parsing it according to its file type.

**Example:**
```json
{
  "action": "load(budget.xlsx)",
  "target": ["executioner"]
}
```
*Parses `budget.xlsx` into the Excel DSL format and stores it in `current.txt`.*

---

### `save(filename.ext)`
Saves the content of `current.txt` to a specified file. Supports `.docx`, `.xlsx`, `.txt`, `.csv`, `.pdf`.

**Example:**
```json
{
  "action": "load(report.docx),save(fixed.docx)",
  "target": ["executioner"]
}
```
*Loads a Word document, AI modifies it in `current.txt`, then saves back as a new Word file.*

---

### `append(json_data, filepath?)`
Appends the `data` field to `current.txt` or another file. Supports `.txt`, `.md`, `.csv`, `.log`, `.json`, `.xlsx`.

**Example:**
```json
{
  "action": "post(),save(output.txt)",
  "data": "[\"This is a sample document.\",\"It contains spelling mistakes.\"]",
  "target": ["executioner"]
}
```

---

### `append_file(filename.ext)`
Loads a file and appends its parsed content to `current.txt` without overwriting existing data.

**Example:**
```json
{
  "action": "load(sales.xlsx),append_file(january.xlsx)",
  "target": ["executioner"]
}
```
*Merges two Excel files into working memory.*

---

### `append_data(json_data)`
Appends `current.txt` content into the `data` field of the JSON object.

**Example:**
```json
{
  "action": "load(sheet.xlsx),append_data(),load(picture.png),append_data(),get()",
  "target": ["executioner"]
}
```
*Loads two files, combines their data, and returns it to the AI for cross-checking.*

---

### `post()`
Writes the `data` field to `current.txt` safely. Unwraps JSON strings, preserves formatting.

**Example:**
```json
{
  "action": "post(),save(fixed.docx)",
  "data": "[\"This is a sample document.\",\"It contains a few spelling mistakes.\",\"fix them all.\"]",
  "target": ["executioner"]
}
```

---

### `get()`
Returns the content of `current.txt` in the `data` field back to the AI.

**Example:**
```json
{
  "action": "load(report.docx),get()",
  "target": ["executioner"]
}
```
*Loads a file and sends its parsed content to the AI for analysis.*

---

### `clear()`
Resets the `data` field to an empty JSON array `[]`.

**Example:**
```json
{
  "action": "clear()",
  "target": ["executioner"]
}
```

---

### `delete_cell((row,col), ...)`
Deletes specific cells from `current.txt` when it contains JSON arrays in Excel/CSV format. Zero-based indices.

**Example:**
```json
{
  "action": "delete_cell((1,2),(3,4))",
  "target": ["executioner"]
}
```

---

### `delete_row(filename.ext, row1, row2, ...)`
Deletes rows from an Excel or CSV file. Up to 4 rows per command. Deletes in descending order to avoid shifting.

**Example:**
```json
{
  "action": "delete_row(\"Books.xlsx\", 2)",
  "target": ["executioner"]
}
```

---

### `filter(filename?, filter1, filter2, ...)`
Filters data in CSV/Excel files or `current.txt`. Supports operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `~` (contains).

**Example:**
```json
{
  "action": "filter(\"employees.csv\", \"Salary>50000\")",
  "target": ["executioner"]
}
```

---

### `analyze(query)`
Sends `current.txt` content to the AI for analysis based on a natural-language query. Output saved as `[query]_analysis.txt`.

**Example:**
```json
{
  "action": "load(sales.docx),analyze(clarity)",
  "target": ["executioner"]
}
```
*Analyzes a document for clarity and saves the report.*

---

### `make_report(filename)`
Generates a clean AI report from a file. Content is chunked (~3000 chars) and sent to AI API.

**Example:**
```json
{
  "action": "make_report(\"data.txt\")",
  "target": ["executioner"]
}
```

---

### `normalize(filetype)`
Normalizes broken JSON in `current.txt` using AI. Splits into chunks, sends to API with filetype-specific prompts.

**Example:**
```json
{
  "action": "normalize(\"xlsx\")",
  "target": ["executioner"]
}
```

---

## Parsing Styles

### Excel
```json
["Sheet1,0,0,\"Name\"", "Sheet1,0,1,\"Age\"", "Sheet1,1,0,\"Alice\"", "Sheet1,1,1,\"30\""]
```
*Each cell: `SheetName,row,col,"value"`. Zero-based indices.*

### Word
```
paragraph Introduction
paragraph This is the second paragraph.
Table0,0,0,"Name"
Table0,0,1,"Age"
Table0,1,0,"Alice"
Table0,1,1,"30"
Table0,2,0,"Bob"
Table0,2,1,""
```
*Paragraphs appear before tables. Only `Table` entries are reconstructed during unparse.*

### PDF / Image (OCR)
```json
["paragraph ...", "First paragraph text...", "Second paragraph text..."]
```
*Each string is one paragraph. Preserves all formatting artifacts.*

### Plain Text
```json
["Line 1 text", "**Bold and italic** line", "Line 3 with symbols:;,:_"]
```
*Each string is one line. Markdown formatting markers preserved.*

---

## Installation

```bash
# Clone the repository
git clone https://github.com/MoonPflora/DataDotAi.git
cd DataDotAi

# Install dependencies
pip install -r requirements.txt

# Set your API key (Mistral, or configure for another provider)
echo "MISTRAL_API_KEY=your_key_here" > .env

# Run
python App.py
```

### Requirements
- Python 3.8+
- `requests`, `python-dotenv`
- `openpyxl`, `pandas` (for Excel/CSV operations)
- `PyPDF2` or `pdfplumber` (for PDF parsing)
- `pytesseract` + `Pillow` (for image OCR)
- `python-docx` (for Word operations)
- `win32com.client` (for Word/Excel automation on Windows)

---

## Usage Flow Example

**User:** "Convert my budget spreadsheet to a Word document"

1. Terminal sends JSON with `message: "Convert my budget spreadsheet to a Word document"` and `target: ["ai"]`
2. Communicator routes to AI
3. AI responds: `message: "I converted 'budget.xlsx' to 'budget.docx'"`, `action: "load(budget.xlsx),save(budget.docx)"`, `target: ["executioner"]`
4. Communicator routes to Executioner
5. Executioner runs `load()` → parses Excel to DSL format in `current.txt`
6. Executioner runs `save()` → unparses DSL format to Word document
7. Executioner returns JSON with `target: ["terminal"]`
8. Terminal displays: "I converted 'budget.xlsx' to 'budget.docx'"

---

## Project Structure

```
DataDotAI/
├── App.py                    # Entry point
├── Communicator.py           # Message router (Terminal ↔ AI ↔ Executioner)
├── Terminal.py               # CLI user interface
├── Config.py                 # Working directory configuration
├── A.py                      # UI component A
├── B_adapter.py              # UI adapter B
├── B_design.py               # UI design B
├── Ai.ico                    # Application icon
├── Logo.png                  # Project logo
├── Executioner/
│   ├── __init__.py           # JSON validation & routing
│   ├── core.py               # Action parser & command executor
│   ├── commands/
│   │   ├── __init__.py       # Command exports
│   │   ├── load.py           # File parser dispatcher
│   │   ├── save.py           # File unparser dispatcher
│   │   ├── append.py         # Append data to files
│   │   ├── append_file.py    # Append file to current.txt
│   │   ├── append_data.py    # Append current.txt to data field
│   │   ├── post.py           # Write data to current.txt
│   │   ├── get.py            # Read current.txt to data field
│   │   ├── clear.py          # Clear data field
│   │   ├── delete_cell.py    # Delete cells from Excel/CSV
│   │   ├── delete_row.py     # Delete rows from Excel/CSV
│   │   ├── filter.py         # Filter Excel/CSV data
│   │   ├── analyze.py        # AI analysis of current.txt
│   │   ├── make_report.py    # Generate AI report from file
│   │   ├── normalize.py      # Fix broken JSON with AI
│   │   ├── Parser/           # Parsers: excel, word, pdf, csv, image, text
│   │   └── Unparser/         # Unparsers: excel, word, pdf, csv, txt
│   └── current.txt           # Working memory (runtime, not committed)
├── Flow.txt                  # ASCII architecture diagram
├── .env                      # API keys (not committed)
├── requirements.txt          # Python dependencies
├── .gitignore
├── LICENSE                   # AGPL-3.0
└── README.md                 # This file
```

---

## Future Roadmap

| Feature | Status | Description |
|---------|--------|-------------|
| **Local Model Support** | Planned | Replace API-only mode with local model inference (Llama, Gemma) via the `Finetune/` pipeline. Architecture already supports pluggable AI backends. |
| **Vector Database** | Planned | Replace regex command matching with semantic retrieval (e.g., ChromaDB, FAISS) so the AI pulls the most relevant command descriptions based on user intent |
| **Command Enrichment** | Planned | Expand command registry with more file types, operations, and metadata |
| **Better Parsing** | Planned | Improve DSL parsing robustness, handle edge cases, add validation layers |
| **Concurrency / Streaming** | Planned | Stream AI responses to the terminal in real-time instead of waiting for full completion |
| **GUI Interface** | WIP | `App.py` contains a PyQt5 skeleton for a graphical interface |

---

## Design Philosophy

> **Don't fine-tune the AI on commands — give it a command registry.**

The original approach attempted to fine-tune the AI on all possible command combinations. This failed due to:
1. Hardware limitations (local training is expensive)
2. Poor generalization (AI couldn't handle unseen command patterns)

The correct approach (implemented here) is:
1. Keep a structured command registry with descriptions, arguments, and examples
2. When the AI needs to execute, it references the registry
3. Future: use a **vector database** for semantic command matching based on natural language intent

---

## Contributing

Contributions are welcome! Please ensure your code follows the existing JSON schema and adds appropriate tests for new commands.

## License

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0).

See [LICENSE](LICENSE) for details.
