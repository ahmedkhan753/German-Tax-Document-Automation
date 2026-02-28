# CHANGELOG

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-28

### 🎨 CRITICAL FEATURES

#### Watermark Z-Order Fix (Priority 1)
- **Issue**: Watermark text was positioned OVER document content (z-order problem)
- **Solution**: Watermark now rendered as background layer, content rendered above
- **Impact**: Text always remains fully readable, watermark provides subtle branding
- **Technical**: Modified `apply_watermark()` and `apply_special_watermark()` functions
- **Verification**: Check `watermarks/` folder content layer positioning

#### Folder Renaming (Clarity)
- **Old**: `input/Daten Franklin/`
- **New**: `input/Import Directory/`
- **Reason**: More intuitive English folder naming for international users
- **Updated**: All CONFIG references in `script/document_processor.py`

#### Smart File Management (New Feature)
- **Processed Files**: Successfully processed documents automatically moved to `input/Import Directory/processed/`
- **Error Files**: Failed documents moved to `input/Import Directory/error/` with error logging
- **Benefits**: Prevents re-processing, maintains audit trail, easy troubleshooting
- **New Functions**: 
  - `ensure_directories()` - Creates required folder structure
  - `move_file_to_processed()` - Move successful files
  - `move_file_to_error()` - Move error files with reason logging

### 🧹 CLEANUP

- Removed all test files:
  - `diagnostic_discovery.py`, `inspect_pdfs.py`
  - `test_discovery.py`, `test_est_discovery.py`, `test_footer.py`, `test_rotated_footer.py`, `test_watermark_positioning.py`
  - All test output files (`.pdf`, `.log`, `.txt`)
  
- Removed build artifacts:
  - `build/` folder (PyInstaller intermediates - can be regenerated)
  - `document_processor.spec` (can be recreated if needed)
  - `diagnostic_results.txt`, `README.txt`

- Result: Production-ready lean codebase (~40KB → ~15KB)

### 🔧 IMPROVEMENT

- Enhanced error handling across all processing steps
- Better logging with status indicators (✓ ✗)
- Improved try-catch blocks with detailed error messages
- More descriptive logging at each processing stage

### 📚 DOCUMENTATION

- Comprehensive README.md with:
  - Feature overview
  - Directory structure
  - Configuration guide
  - Troubleshooting section
  - Version history

### ✅ TESTING STATUS

- ✓ File discovery: All document types identified correctly
- ✓ DOCX to PDF conversion: Working with error handling
- ✓ Watermark layering: Background positioning verified
- ✓ File merging: Correct sequence order maintained
- ✓ File movement: Processed/error folders functioning
- ✓ Error logging: Comprehensive audit trail

## [1.0.0] - Prior

### Initial Features
- Document type discovery and classification
- DOCX to PDF conversion
- Watermark application
- Document merging in sequence order
- Logging and error handling

---

## Maintenance Notes

### To Rebuild EXE
```bash
pyinstaller --onefile script/document_processor.py --distpath dist --buildpath build
```

### To Update Configuration
Edit the `CONFIG` dictionary in `script/document_processor.py`

### To Add New Document Types
1. Add entry under `CONFIG['document_types']`
2. Add to `CONFIG['merge_order']` for sequence
3. Add to `DISCOVERY_ORDER` for matching priority
4. Add watermark PDF to `watermarks/` folder
5. Test with sample document

### Dependencies Update
Current versions in `requirements.txt`:
- PyPDF2 (PDF manipulation)
- docx2pdf (DOCX conversion)
- reportlab (PDF generation)
- pyinstaller (EXE compilation)

To update: `pip install --upgrade <package_name>`
