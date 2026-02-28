# API Reference & Function Documentation

## Overview

This document describes all functions in `script/document_processor.py` and how to use/extend them.

---

## Core Functions

### 1. `get_base_path()`

**Purpose**: Determine the base directory for the application (works in Python and compiled EXE)

```python
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

**Returns**: `str` - Absolute path to project root

**Behavior**:
- If running as EXE: Returns directory containing .exe file
- If running as Python: Returns parent of script directory

**Usage**: Called once at module load to set BASE_DIR

**Example**:
```python
base = get_base_path()
print(base)  # C:\Users\User\projects\German-tax-automation
```

---

### 2. `safe_pause(message)`

**Purpose**: Pause execution and wait for user input (works in interactive terminals, silent in automated mode)

```python
def safe_pause(message="\nPress Enter to continue..."):
    if sys.stdin and sys.stdin.isatty():
        try: input(message)
        except EOFError: pass
```

**Parameters**:
- `message` (str): Message to display. Default: `"\nPress Enter to continue..."`

**Returns**: `None`

**Behavior**:
- Shows prompt if running in interactive terminal
- Silent if running in batch/automated mode
- Gracefully handles EOF (end of file) in pipes

**Usage**: Called at end of main script execution

**Example**:
```python
safe_pause("Script complete. Press Enter to exit...")
```

---

### 3. `ensure_directories()`

**Purpose**: Create all required directories if they don't exist

```python
def ensure_directories():
    for directory in [CONFIG['output_dir'], CONFIG['processed_dir'], CONFIG['error_dir']]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Created directory: {directory}")
```

**Parameters**: None

**Returns**: `None`

**Side Effects**:
- Creates output/, processed/, and error/ directories
- Logs creation events

**Called By**: Main execution block

**Example**:
```python
ensure_directories()
# Creates:
# - output/
# - input/Import Directory/processed/
# - input/Import Directory/error/
```

---

### 4. `discover_files(input_dir)`

**Purpose**: Search input directory and categorize files by document type using prefix matching

```python
def discover_files(input_dir):
    # Returns: {doc_type: [file_paths]}
```

**Parameters**:
- `input_dir` (str): Path to search for documents

**Returns**: `dict` - Keys are document types, values are lists of matching file paths

```python
{
    'anschreiben': ['/path/to/BaM File.docx'],
    'est': ['/path/to/ESt Erklärung 2024.pdf'],
    'kst': ['/path/to/KSt File 1.pdf', '/path/to/KSt File 2.pdf']
}
```

**Behavior**:
- Scans input directory for all files (sorted)
- Matches against DISCOVERY_ORDER (prevents duplicates)
- Logs matched files
- Respects exclude prefixes

**Important**: Uses DISCOVERY_ORDER not merge_order!

**Example**:
```python
files = discover_files('input/Import Directory')
if 'est' in files:
    print(f"Found {len(files['est'])} ESt documents")
```

---

### 5. `convert_to_pdf(file_path)`

**Purpose**: Convert DOCX files to PDF format

```python
def convert_to_pdf(file_path):
    # Returns: pdf_path (temporary file) or None if error
```

**Parameters**:
- `file_path` (str): Path to document file

**Returns**: 
- `str` - Path to temporary PDF (if successful)
- `None` - If conversion failed

**Behavior**:
- If file is already PDF: Returns as-is
- If file is DOCX: Converts to temporary PDF
- Moves source file to processed/ on success
- Moves source file to error/ on failure
- Logs all operations

**Side Effects**:
- Creates temporary PDF file
- May move input file to processed/error folder
- Updates logs

**Requirements**: docx2pdf library must be installed

**Example**:
```python
pdf = convert_to_pdf('input/Import Directory/Document.docx')
if pdf:
    print(f"Converted to: {pdf}")
else:
    print("Conversion failed")
```

---

### 6. `apply_watermark(pdf_path, doc_type)`

**Purpose**: Apply document-type-specific watermark to PDF (CRITICAL Z-ORDER)

```python
def apply_watermark(pdf_path, doc_type):
    # Returns: watermarked_pdf_path or original_path on error
```

**Parameters**:
- `pdf_path` (str): Path to PDF to watermark
- `doc_type` (str): Document type key (e.g., 'est', 'anschreiben')

**Returns**:
- `str` - Path to watermarked temporary PDF
- `str` - Original path if error (watermark skipped)

**Behavior**:
- Reads watermark PDF from CONFIG
- If watermark is 'special': Uses `apply_special_watermark()`
- Scales watermark to fit page
- **CRITICAL**: Merges watermark as BACKGROUND layer
- Positions at center of each page
- Handles page rotations
- Returns temporary file (needs cleanup elsewhere)

**Z-Order Important**:
```python
# CORRECT ORDER:
new_page = PyPDF2.PageObject.create_blank_page(...)
new_page.merge_page(wm_overlay)  # Watermark FIRST (background)
new_page.merge_page(page)        # Content SECOND (foreground)
```

**Example**:
```python
watermarked = apply_watermark('temp.pdf', 'est')
if watermarked:
    print(f"Watermarked: {watermarked}")
    # Watermark is now background layer
```

---

### 7. `apply_special_watermark(pdf_path)`

**Purpose**: Apply special watermarking (different for page 1 vs. rest)

```python
def apply_special_watermark(pdf_path):
    # Page 1: Wasserzeichen Deckblatt.pdf
    # Pages 2+: Wasserzeichen Allgemein.pdf
```

**Parameters**:
- `pdf_path` (str): Path to PDF to watermark

**Returns**: `str` - Path to watermarked temporary PDF

**Behavior**:
- Used for 'jahresabschluss' type
- Page 0 (first): Applies Deckblatt watermark
- Pages 1+: Applies Allgemein watermark
- Handles rotation per page
- Scales appropriately
- **CRITICAL**: Maintains Z-order (watermark as background)

**When Used**: When CONFIG has `'watermark': 'special'`

**Example**:
```python
# In apply_watermark():
if watermark_file == 'special':
    return apply_special_watermark(pdf_path)
```

---

### 8. `merge_pdfs(processed_files)`

**Purpose**: Merge all processed documents in correct sequence order

```python
def merge_pdfs(processed_files):
    # Returns: final_output.pdf path or None
```

**Parameters**:
- `processed_files` (dict): `{doc_type: pdf_path}` from processing

**Returns**:
- `str` - Path to final merged PDF
- `None` - If no documents to merge

**Behavior**:
- Uses CONFIG['merge_order'] for sequence
- Merges PDFs in order
- Skips missing types
- Writes to CONFIG['output_dir']/final_output.pdf
- Logs each merge step

**Example**:
```python
processed = {
    'anschreiben': '/tmp/tmp123.pdf',
    'est': '/tmp/tmp456.pdf'
}
final = merge_pdfs(processed)
# Result: output/final_output.pdf
```

---

### 9. `move_file_to_processed(file_path)`

**Purpose**: Move successfully processed file to processed folder

```python
def move_file_to_processed(file_path):
    # Returns: destination path or None on error
```

**Parameters**:
- `file_path` (str): Source file path

**Returns**:
- `str` - Destination path in processed folder
- `None` - If move failed

**Behavior**:
- Checks file exists
- Determines destination path
- Handles filename conflicts (adds _1, _2, etc.)
- Logs move operation
- Returns destination for verification

**When Called**: After successful conversion from DOCX to PDF

**Example**:
```python
result = move_file_to_processed('input/Import Directory/File.docx')
if result:
    print(f"Moved to: {result}")
```

---

### 10. `move_file_to_error(file_path, error_message)`

**Purpose**: Move failed file to error folder with logging

```python
def move_file_to_error(file_path, error_message=""):
    # Returns: destination path or None on error
```

**Parameters**:
- `file_path` (str): Source file path
- `error_message` (str): Error description

**Returns**:
- `str` - Destination path in error folder
- `None` - If move failed

**Behavior**:
- Checks file exists
- Moves to error folder
- Logs error with error message
- Handles filename conflicts
- Provides audit trail

**When Called**: When conversion or processing fails

**Example**:
```python
move_file_to_error(file_path, f"Conversion error: {str(e)}")
# Logs: ✗ Moved to error folder: File.docx | Reason: Conversion error...
```

---

## Helper Functions (Internal)

### `get_base_path()` - Already Documented

### `safe_pause()` - Already Documented

---

## Configuration Access

### Global CONFIG Dictionary

All functions access settings from `CONFIG`:

```python
CONFIG = {
    'input_dir': str,           # Read by discover_files()
    'output_dir': str,          # Written by merge_pdfs()
    'watermark_dir': str,       # Read by apply_watermark()
    'processed_dir': str,       # Written by move_file_to_processed()
    'error_dir': str,           # Written by move_file_to_error()
    'delete_input_after_processing': bool,  # Read by convert_to_pdf()
    'document_types': dict,     # Read by discover_files(), apply_watermark()
    'merge_order': list         # Read by merge_pdfs()
}
```

### Global DISCOVERY_ORDER List

Used only by `discover_files()` for prefix matching priority:

```python
DISCOVERY_ORDER = [
    'anschreiben',
    'deckblatt_steuererklaerung',
    'jahresabschluss',
    # ... etc
]
```

---

## Logging

### Logging Setup

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Log Levels Used

- **DEBUG**: Page-level Watermark Details
- **INFO**: File operations, converts, merges
- **WARNING**: Non-critical issues
- **ERROR**: Failed operations, file movements

### Example Log Output

```
2026-02-28 14:32:15,123 - INFO - Searching for files in: input/Import Directory
2026-02-28 14:32:15,234 - INFO - Matched anschreiben: BaM File.docx
2026-02-28 14:32:15,345 - INFO - Converting BaM File.docx...
2026-02-28 14:32:16,456 - INFO - ✓ Moved to processed: BaM File.docx
2026-02-28 14:32:16,567 - INFO - Merging final document...
2026-02-28 14:32:16,678 - INFO - SEQUENCE [1]: Added anschreiben
```

---

## Main Execution Flow

### Entry Point

```python
if __name__ == "__main__":
    ensure_directories()                    # Create folders
    found_files = discover_files(...)       # Find documents
    processed_files = {}                    # Store results
    
    # Process each document type
    for dt in CONFIG['merge_order']:
        # Convert DOCX → PDF
        # Merge multiple files
        # Apply watermark (background layer)
        # Store in processed_files
    
    final = merge_pdfs(processed_files)     # Merge all
    safe_pause()                            # Wait for user
```

---

## Error Handling Strategy

### Process Failures

| Stage | Error Handling | Result |
|-------|---|---|
| Discovery | No files found | Exit gracefully |
| Conversion | DOCX error | Move to error/, continue |
| Watermarking | Missing watermark | Skip watermark, use original |
| Merging | Type not found | Skip type, continue |
| Final merge | No documents | Print error, exit |

### File Movement Logic

```
Input File
    ↓
Successful Processing
    ↓
Move to processed/ folder
    ✓ File availability preserved

Error occurs
    ↓
Move to error/ folder
    + Error message logged
    ✓ Audit trail maintained
```

---

## Extending the System

### Add New Document Type

```python
CONFIG['document_types']['my_type'] = {
    'prefixes': ['MyPrefix'],
    'watermark': 'Wasserzeichen_Custom.pdf',
    'format': 'pdf'
}

# Update discovery and merge order...
```

### Add New Processing Step

Example: Add validation function

```python
def validate_pdf(pdf_path):
    """Check PDF is valid before processing"""
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        return len(reader.pages) > 0
    except:
        return False

# Call in processing loop:
if not validate_pdf(pdf_path):
    move_file_to_error(file_path, "Invalid PDF")
    continue
```

### Custom Watermark Logic

```python
def apply_company_watermark(pdf_path, company):
    """Apply company-specific watermark"""
    watermark_file = f'Wasserzeichen_{company}.pdf'
    # ... custom logic ...
```

---

## Performance Characteristics

### Time Complexity
- File discovery: O(n) where n = files in input directory
- Per-file conversion: Depends on file size
- Watermarking: O(pages) where pages count in PDF
- Merging: O(total_pages)

### Space Requirements
- Temporary PDFs: ~1.5x input file size
- Watermark: Minimal (~100-500KB)
- Final output: Sum of all input sizes

### Optimization Tips
- Process in batches if >50 documents
- Watermark step is slowest (O(pages))
- File I/O is next slowest
- Discovery is very fast

---

## Testing Functions

### Test File Discovery

```python
files = discover_files('input/Import Directory')
print(f"Found: {files}")
```

### Test Conversion

```python
pdf = convert_to_pdf('test.docx')
if pdf:
    print(f"Converted successfully: {pdf}")
```

### Test Watermarking

```python
watermarked = apply_watermark('test.pdf', 'est')
print(f"Watermarked: {watermarked}")
```

### Test Merging

```python
processed = {'est': 'test.pdf'}
final = merge_pdfs(processed)
print(f"Final: {final}")
```

---

## Common Patterns

### Safe File Operations

```python
try:
    # Do file operation
    os.rename(src, dst)
except Exception as e:
    logging.error(f"Failed: {e}")
    return None
```

### Configuration Access

```python
path = CONFIG['output_dir']
watermark_path = os.path.join(CONFIG['watermark_dir'], filename)
```

### Document Type Iteration

```python
for doc_type in CONFIG['merge_order']:
    if doc_type in found_files:
        # Process this type
```

### Logging Operations

```python
logging.info(f"Processing {filename}")
logging.error(f"Failed: {error_msg}")
logging.debug(f"Detail: {value}")
```
