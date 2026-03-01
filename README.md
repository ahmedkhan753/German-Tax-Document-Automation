# German Tax Automation - Document Processor

A robust Python-based tax document processing system that converts, merges, and applies watermarks to German tax documents.

## ✨ Key Features

### 1. **Intelligent Document Discovery**
- Automatically identifies tax documents by type (Anschreiben, Jahresabschluss, ESt-Erklärung, etc.)
- Handles multiple formats (DOCX → PDF conversion)
- Priority-based matching to resolve overlaps correctly

### 2. **Watermark Management** 
- **Z-Order Layering**: Watermarks positioned as background layers, ensuring text remains readable
- Type-specific watermarks (cover sheet: Deckblatt, general documents: Allgemein)
- Intelligent scaling and centering for all page sizes
- Rotation handling for correctly oriented watermarks

### 3. **Document Processing Pipeline**
- Converts DOCX files to PDF format automatically
- Merges document sections in correct sequence order
- Creates unified final output (final_output.pdf)
- Comprehensive error logging throughout the process

### 4. **Smart File Management**
- **Processed Folder**: Successfully processed files moved to `input/Import Directory/processed/`
- **Error Folder**: Failed files moved to `input/Import Directory/error/` with error details
- Prevents re-processing of completed documents
- Automatic cleanup with detailed logging

## 📁 Directory Structure

```
├── script/
│   └── document_processor.py      # Main processing script
├── input/
│   └── Import Directory/           # Input documents folder
│       ├── *.docx, *.pdf          # Tax documents to process
│       ├── processed/              # Successfully processed files
│       └── error/                  # Files with processing errors
├── output/
│   └── final_output.pdf           # Final merged & watermarked document
├── watermarks/
│   ├── Wasserzeichen Deckblatt.pdf    # Cover sheet watermark
│   ├── Wasserzeichen Allgemein.pdf    # General watermark

> ⚠️ If the first page of a document contains a prominent title such as "Cover Letter",
>     the watermarking step will now **skip the watermark on that page** to avoid
>     obscuring the text.  A warning is logged when this occurs.  The rest of the
>     document is processed as normal.
│   └── ...                            # Other document-specific watermarks
├── dist/
│   └── document_processor.exe     # Compiled executable (Windows)
├── env/                            # Python virtual environment
└── requirements.txt               # Python dependencies

```

## 🚀 Usage

### From Python Script
```bash
# Activate virtual environment
env\Scripts\Activate.ps1

# Run the processor
python script/document_processor.py
```

### From Compiled Executable
```bash
# Windows
dist\document_processor.exe
```

## 📋 Supported Document Types

| Type | File Prefixes | Watermark | Format |
|------|---------------|-----------|--------|
| **Anschreiben** (Cover Letter) | BaM, Übersendung, 440372 | Deckblatt | DOCX |
| **Jahresabschluss** (Annual Report) | JA Jahresabschluss, JA Abschluss | Special | PDF |
| **Offenlegung** (Disclosure) | JA Offenlegung | Allgemein | PDF |
| **Deckblatt** (Title Page) | Deckblatt, 440368, Cover | Deckblatt | DOCX |
| **KSt Erklärung** | KSt Erklärung (excl. Freizeichnung) | Allgemein | PDF |
| **Est-Erklärung** (Income Tax) | ESt Erklärung, Einkommensteuer | Allgemein | PDF |
| **Ust-Erklärung** (Sales Tax) | USt Erklärung | Allgemein | PDF |
| **Gewerbesteuer** | GewSt, Gewerbesteuer | Allgemein | PDF |

## 🔧 Configuration

Edit `CONFIG` dictionary in `script/document_processor.py`:

```python
CONFIG = {
    'input_dir': 'input/Import Directory',      # Source documents
    'output_dir': 'output',                     # Final output folder
    'watermark_dir': 'watermarks',              # Watermark files
    'processed_dir': 'input/Import Directory/processed',  # Processed files
    'error_dir': 'input/Import Directory/error',         # Failed files
    'delete_input_after_processing': True,      # Move to processed/ after success
    # ... document type definitions ...
}
```

## 📊 Processing Flow

```
Input Files
    ↓
Discover Documents (by type)
    ↓
Convert DOCX → PDF (if needed)
    ↓
Merge Multiple per Type
    ↓
Apply Watermark (Background Layer)
    ↓
Final Merge by Sequence
    ↓
Output: final_output.pdf
    ↓
Move to processed/ folder
```

## ✅ Recent Improvements (v2.0)

- ✨ **Watermark Z-Order Fix**: Watermarks now positioned as background layers (text always readable)
- 📁 **Folder Rename**: "Daten Franklin" → "Import Directory" for clarity
- 📂 **Smart File Movement**: Auto-move processed files to `processed/` and errors to `error/`
- 🧹 **Clean Codebase**: Removed all test files, keeping only production-ready code
- 🏗️ **Improved Error Handling**: Comprehensive error tracking with audit trail
- 📝 **Better Logging**: Enhanced logging for debugging and monitoring
- 🔒 **Robust Processing**: Error handling at each step with graceful degradation

## 📦 Dependencies

- `PyPDF2` - PDF manipulation and merging
- `docx2pdf` - DOCX to PDF conversion
- `reportlab` - PDF generation capabilities
- `pyinstaller` - Executable compilation
- `pywin32` - Windows integration (included in env)

## 🐛 Troubleshooting

### Files not processed
- Check `input/Import Directory/error/` for failed files
- Review logs in console for error messages
- Verify file naming matches document type prefixes

### Watermark issues
- Verify watermark PDFs exist in `watermarks/` folder
- Check watermark file permissions
- Ensure watermark PDFs have white backgrounds for proper transparency

### Missing PDF output
- Check `output/` folder for `final_output.pdf`
- Verify at least one document type was found
- Check console logs for processing errors

## 👤 Author

German Tax Automation Team

## 📄 License

Proprietary - German Tax Automation System

## 🔄 Version History

### v2.0 (Current)
- Production-ready codebase
- Complete watermark z-order implementation
- Smart file movement system
- Enhanced error handling and logging

### v1.0
- Initial release with basic functionality
