# Installation & Setup Guide

## Prerequisites

- **Windows 7+** or **Linux/Mac** with Python 3.8+
- **Python 3.9+** recommended
- **Git** (for version control)
- **Visual C++ Redistributable** (for Windows EXE)

## Installation Steps

### Option 1: Using Python Script (Recommended for Development)

#### Step 1: Clone Repository
```bash
cd d:\PROJECTS\German-tax-automation-prod\German-tax-automation-prod\German-tax-automation-prod
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Run the Processor
```bash
python script/document_processor.py
```

### Option 2: Using Compiled Executable (Windows)

Simply run:
```bash
dist\document_processor.exe
```

No Python installation required.

## Configuration

### File Paths
Edit `script/document_processor.py`, modify the `CONFIG` dictionary:

```python
CONFIG = {
    'input_dir': 'input/Import Directory',            # Source documents
    'output_dir': 'output',                           # Output location
    'watermark_dir': 'watermarks',                    # Watermark PDFs
    'processed_dir': 'input/Import Directory/processed',   # Success location
    'error_dir': 'input/Import Directory/error',      # Error location
    'delete_input_after_processing': True,            # Auto-move files
}
```

### Adding Watermarks

1. Place watermark PDF in `watermarks/` folder
2. Name it descriptively (e.g., `Wasserzeichen_Custom.pdf`)
3. Update `CONFIG['document_types']` to reference it:
   ```python
   'my_doc_type': {
       'prefixes': ['Your Document Name'],
       'watermark': 'Wasserzeichen_Custom.pdf',
       'format': 'pdf'
   }
   ```

## Folder Structure Setup

### Expected Structure
```
project_root/
├── input/
│   └── Import Directory/          ← Place input documents here
│       ├── *.docx, *.pdf         ← Add source documents
│       ├── processed/             ← Auto-created after first run
│       └── error/                 ← Auto-created after first run
├── output/                        ← Auto-created
│   └── final_output.pdf          ← Generated output
├── watermarks/                    ← Must exist with PDFs
├── script/
│   └── document_processor.py      ← Main script
└── env/                           ← Virtual environment
```

### Create Directories
Directories are auto-created on first run, but you can manually create them:

```bash
mkdir "input\Import Directory"
mkdir "input\Import Directory\processed"
mkdir "input\Import Directory\error"
mkdir output
mkdir watermarks
```

## First Run Checklist

- [ ] Python 3.9+ installed (or using EXE)
- [ ] Virtual environment activated (if using Python)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Documents placed in `input/Import Directory/`
- [ ] Watermarks present in `watermarks/` folder
- [ ] Input folder has proper document naming (matches prefixes)

## Troubleshooting Installation

### "ModuleNotFoundError: No module named 'PyPDF2'"
```bash
pip install PyPDF2 docx2pdf reportlab
```

### "Python is not recognized"
- Add Python to PATH in Windows
- Or use full path: `C:\Python311\python.exe script/document_processor.py`

### "Virtual environment not activating"
```bash
# Bypass execution policy
powershell -ExecutionPolicy Bypass -NoProfile -Command "env\Scripts\Activate.ps1"
```

### Permission Denied (Linux/Mac)
```bash
chmod +x env/bin/activate
source env/bin/activate
```

## Rebuilding the EXE

If you modify `script/document_processor.py`, rebuild the executable:

```bash
# Activate virtual environment first
env\Scripts\Activate.ps1

# Install PyInstaller (if not already)
pip install pyinstaller

# Build executable
pyinstaller --onefile --name document_processor --distpath dist --buildpath build script/document_processor.py

# Output: dist/document_processor.exe
```

## Updating Dependencies

Check for updates:
```bash
pip list --outdated
```

Update specific package:
```bash
pip install --upgrade PyPDF2
```

Update all:
```bash
pip install --upgrade -r requirements.txt
```

## Getting Help

1. Check `CHANGELOG.md` for recent changes
2. See `README.md` for feature documentation
3. Review logs in console output
4. Check `input/Import Directory/error/` for failed files
5. Read TROUBLESHOOTING.md for common issues
