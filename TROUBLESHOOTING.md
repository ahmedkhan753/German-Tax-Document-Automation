# Troubleshooting Guide

## Common Issues & Solutions

### � EXE-Specific Issues

#### Issue: EXE creates 'output' folder in dist/ directory
**Problem**: Running .exe creates `dist/output/` instead of using project's `output/` folder
**Solution**: ✅ **FIXED in latest build**
- The EXE now correctly detects the project root (one level up from dist/)
- All folders (input, output, watermarks) are now found correctly
- To use the fix: Download the latest `dist/document_processor.exe`

**If still having issues**:
1. Delete the incorrectly created `dist/output/` folder
2. Delete the old .exe file
3. Rebuild the EXE: `pyinstaller --onefile --name document_processor --distpath dist --workpath build script/document_processor.py`

#### Issue: EXE crashes with warning messages
**Problem**: .exe file crashes or closes without clear error message
**Solution**: ✅ **FIXED in latest build**
- Added comprehensive error handling
- Now displays clear error messages instead of crashing
- Checks for:
  - Missing folders (input/output/watermarks)
  - Permission errors
  - Disk space issues
  - Invalid watermark files

**Troubleshooting crashed EXE**:
1. Run from command prompt (don't double-click) to see error messages:
   ```bash
   dist\document_processor.exe
   ```
2. Read the error message displayed on screen
3. Common fixes:
   - Verify `watermarks/` folder has PDF files
   - Check `input/Import Directory/` folder exists
   - Ensure output folder has write permissions
   - Check disk space available

#### Issue: "Project root" or file path warnings on startup
**Problem**: Console shows path resolution messages
**Solution**: Normal behavior - not an error
- These are informational messages
- Verify the "Project root:" path shown is correct:
  - Should be: `D:\PROJECTS\.../German-tax-automation-prod`
  - Should NOT be: `D:\PROJECTS\.../dist`

---

### 📂 Folder & File Management


#### Issue: "No files found" message
**Problem**: The processor runs but finds no documents
**Solutions**:
1. Verify documents are in `input/Import Directory/` folder
2. Check file names match the document type prefixes:
   ```
   BaM, Übersendung, 440372 → Anschreiben
   JA Jahresabschluss, JA Abschluss → Jahresabschluss
   ```
3. Use exact German characters (ä, ö, ü) in filenames
4. Ensure files are actual PDFs or DOCX, not renamed copies
5. Check file extensions are lowercase (.pdf, .docx, not .PDF, .DOCX)

#### Issue: Files stay in Import Directory without processing
**Problem**: Files aren't being discovered or processed
**Solutions**:
1. Enable logging level DEBUG in `script/document_processor.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG, ...)
   ```
2. Check console output for which documents were discovered
3. Verify CONFIG['input_dir'] points to correct path
4. Place test file with clear prefix (e.g., "BaM Test.pdf")

#### Issue: Processed files not moving to 'processed/' folder
**Problem**: Files remain in Import Directory after successful processing
**Solutions**:
1. Check `CONFIG['delete_input_after_processing']` is `True`
2. Verify `processed/` folder exists or will be created
3. Check file permissions (read/write access)
4. Check disk space availability
5. Review console logs for move operation errors

#### Issue: Error files stuck in Import Directory
**Problem**: Failed files not moving to error folder
**Solutions**:
1. Manually move files to `input/Import Directory/error/`
2. Check error folder has write permissions
3. Review error logs in console for specific error message
4. Check if error is about missing watermark file

---

### 📄 PDF & Watermark Issues

#### Issue: Watermark appears ON TOP of text (text not readable)
**CRITICAL**: This should NOT happen in v2.0.0+
**Solutions if it occurs**:
1. Verify you're using the latest version (check git log)
2. Check `apply_watermark()` function has `# CRITICAL Z-LAYER ORDER` comment
3. Verify `merge_page()` order is correct:
   ```python
   new_page.merge_page(wm_overlay)  # Watermark first (background)
   new_page.merge_page(page)        # Content second (foreground)
   ```
4. Reimport the watermark PDF - it might have wrong layering

#### Issue: Watermark file not found
**Problem**: "Watermark file not found" error
**Solutions**:
1. Check file name exists in `watermarks/` folder exactly as referenced:
   ```
   CONFIG must say: 'Wasserzeichen Deckblatt.pdf'

- **Cover-page text hidden by watermark?**
  The processor now looks for keywords like "Cover Letter", "Anschreiben" or
  "Deckblatt" on the first page.  If any are found, the watermark will be *skipped*
  on that page and a warning will be logged.  Check the output and logs if the
  title still appears unclear; you may need to adjust the watermark PDF or the
  document content.
   File must exist: watermarks/Wasserzeichen Deckblatt.pdf
   ```
2. Check German special characters (ä, ö, ü, ß) are spelled correctly
3. Verify file extension is .pdf (lowercase)
4. List watermarks folder:
   ```bash
   dir watermarks
   ```
5. If watermark is missing, add it, then re-run processor

#### Issue: Watermark is blurry or distorted
**Problem**: Watermark quality issues in output
**Solutions**:
1. Source watermark PDF might be low resolution
2. Try with higher quality watermark PDF
3. Check watermark scaling factor in logs (should be close to 1.0)
4. Verify watermark aspect ratio matches document

#### Issue: Final PDF has blank pages
**Problem**: Missing content in final_output.pdf
**Solutions**:
1. Check that at least one document type was found
2. Verify document files aren't corrupted
3. Check merge_order in CONFIG - should match found document types
4. Try converting DOCX to PDF manually to test:
   ```python
   from docx2pdf import convert
   convert('test.docx', 'test.pdf')
   ```

---

### 🔄 Conversion Issues

#### Issue: "Conversion failed for *.docx"
**Problem**: DOCX to PDF conversion error
**Solutions**:
1. Verify file is actual DOCX, not renamed Word file
2. Try opening DOCX in Microsoft Word - fix any corruption
3. Check docx2pdf is installed: `pip install docx2pdf`
4. On Windows, verify Word or LibreOffice is installed
5. Try manual conversion:
   ```bash
   python -c "from docx2pdf import convert; convert('file.docx', 'file.pdf')"
   ```

#### Issue: "Module not found: docx2pdf"
**Problem**: Missing converter library
**Solutions**:
1. Install specifically: `pip install docx2pdf`
2. Verify installation:
   ```bash
   python -c "import docx2pdf; print(docx2pdf.__file__)"
   ```
3. Reinstall entire requirements:
   ```bash
   pip install --force-reinstall -r requirements.txt
   ```

---

### 🖥️ Execution Issues

#### Issue: "Python is not recognized"
**Problem**: Command not found when running Python
**Solutions**:
1. Use full path:
   ```bash
   C:\Python311\python.exe script/document_processor.py
   ```
2. Add Python to PATH in Windows
3. Or activate virtual environment first:
   ```bash
   env\Scripts\Activate.ps1
   ```

#### Issue: "Access denied" when running EXE
**Problem**: Windows blocks execution
**Solutions**:
1. Right-click EXE → Properties → General → Unblock
2. Or run from command line (admin not required)
3. Disable Windows Defender/Antivirus temporarily for testing

#### Issue: EXE doesn't output final PDF
**Problem**: Executable runs but no output file created
**Solutions**:
1. Check `output/` folder exists and has write permissions
2. Try Python version: `python script/document_processor.py`
3. Check event viewer for error details
4. Verify watermark files readable by EXE

---

### 🔐 Permission Issues

#### Issue: "Permission denied" reading/writing files
**Problem**: File access errors
**Solutions**:
1. Close the file in PDF viewer or Excel
2. Give folder read/write permissions:
   ```bash
   icacls "input\Import Directory" /grant Users:M
   ```
3. Run from admin command prompt
4. Disable file encryption on folder

#### Issue: Cannot write to output folder
**Problem**: Output PDF not created
**Solutions**:
1. Check output folder has write permissions
2. Check disk space available
3. Verify output folder path is accessible
4. Try different output location in CONFIG

---

### 🐛 Debug Techniques

#### Enable Debug Logging
Edit `script/document_processor.py`:
```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
```

#### Check Discovered Files
Add to main block:
```python
found_files = discover_files(CONFIG['input_dir'])
print(f"DEBUG: Found files = {found_files}")
```

#### Verify Watermark Merging
Add to apply_watermark function:
```python
logging.debug(f"Watermark dimensions: {wm_w}x{wm_h}")
logging.debug(f"Page dimensions: {w}x{h}")
logging.debug(f"Scale factor: {scale}")
```

---

### 📊 Log Analysis

#### Where are logs?
- **Console output** - printed while running
- **Run output** - .log files if you redirect: `python script/document_processor.py > run.log`

#### What to look for:
```
✓ Matched <type>: <filename>     → File was recognized
✓ Moved to processed: <file>     → File processed successfully
✗ Moved to error folder: <file>  → File had error
ERROR: <message>                  → Problem occurred
```

---

### 🔗 Getting More Help

1. **Check recent changes**: Read `CHANGELOG.md`
2. **Review configuration**: See CONFIG examples in `README.md`
3. **Check file structure**: Verify against `INSTALL.md` folder layout
4. **Review script**: Open `script/document_processor.py` and check function names
5. **Test isolation**: Try with single document type first

### Performance Tips

- Single document merge is faster than multiple per type
- Large PDFs (>50MB) take longer to process
- Watermark application is most time-consuming step
- Consider splitting large batches into smaller runs

---

## Contact & Support

If issue persists after trying above solutions:
1. Check error message in `input/Import Directory/error/` folder
2. Enable DEBUG logging and save output to file
3. Verify all file names match exactly (case-sensitive on Linux)
4. Verify watermark PDFs are valid, uncorrupted PDFs

**Note**: Custom watermark issues often require recreating watermark PDF files with correct z-order layering.
