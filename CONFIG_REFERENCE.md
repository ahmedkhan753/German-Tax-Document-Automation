# Configuration Reference

## Complete CONFIG Dictionary

### Location
File: `script/document_processor.py`, lines ~80-110

### Base Configuration

```python
CONFIG = {
    # Directory paths
    'input_dir': os.path.join(BASE_DIR, 'input', 'Import Directory'),
    'output_dir': os.path.join(BASE_DIR, 'output'),
    'watermark_dir': os.path.join(BASE_DIR, 'watermarks'),
    'processed_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'processed'),
    'error_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'error'),
    
    # Processing behavior
    'delete_input_after_processing': True,  # Move files to processed/ after success
    
    # Document type definitions...
    # Merge sequence...
}
```

---

## Document Type Configuration

### Structure
Each document type entry contains:

```python
'document_type_name': {
    'prefixes': ['Prefix1', 'Prefix2', ...],      # File name prefixes to match
    'exclude': ['ExcludePrefix', ...],            # Optional: prefixes to exclude
    'watermark': 'filename.pdf',                  # Watermark file name or 'special'
    'format': 'pdf' or 'docx',                    # Source file format
}
```

### All Supported Types

#### 1. Anschreiben (Cover Letter)
```python
'anschreiben': {
    'prefixes': ['BaM', 'Übersendung', '440372'],
    'watermark': 'Wasserzeichen Anschreiben.pdf',
    'format': 'docx'
}
```
**Meaning**: Cover letter/transmission letter for tax documents
**Input**: DOCX files
**Watermark**: Special Anschreiben watermark
**Example File**: `BaM Übersendung JA 2024.docx`

#### 2. Jahresabschluss (Annual Report)
```python
'jahresabschluss': {
    'prefixes': ['JA Jahresabschluss', 'JA Abschluss'],
    'watermark': 'special',
    'format': 'pdf'
}
```
**Meaning**: Annual financial report
**Input**: PDF files
**Watermark**: Special watermarking (Deckblatt for page 1, Allgemein for rest)
**Example File**: `JA Jahresabschluss 2024.pdf`

#### 3. Offenlegung (Disclosure)
```python
'offenlegung': {
    'prefixes': ['JA Offenlegung'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Public disclosure (Bundesanzeiger)
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `JA Offenlegung Bundesanzeiger 2024.pdf`

#### 4. Deckblatt Steuererklärung (Tax Declaration Cover)
```python
'deckblatt_steuererklaerung': {
    'prefixes': ['Deckblatt', 'Deckblatt Steuer', 'Deckblatt Word', '440368', 
                 'Cover', 'Deckblatt Einkommensteuer', 'Deckblatt ESt', 
                 'AP Deckblatt', 'JA AP'],
    'watermark': 'Wasserzeichen Deckblatt.pdf',
    'format': 'docx'
}
```
**Meaning**: Cover page for tax declarations
**Input**: DOCX files  
**Watermark**: Cover sheet specific watermark
**Example File**: `Deckblatt Einkommensteuer 2024.docx`

#### 5. KSt Erklärung (Corporate Income Tax)
```python
'kst': {
    'prefixes': ['KSt Erklärung'],
    'exclude': ['Freizeichnungsdokument'],  # Don't match if contains this
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Corporate income tax declaration (without exemption document)
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `KSt Erklärung 2024.pdf`

#### 6. KSt Freizeichnung (Corporate Tax Exemption)
```python
'kst_freizeichnung': {
    'prefixes': ['KSt Erklärung Freizeichnungsdokument'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Corporate income tax declaration - exemption document
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `KSt Erklärung Freizeichnungsdokument 2024.pdf`

#### 7. Est Erklärung (Income Tax)
```python
'est': {
    'prefixes': ['ESt Erklärung', 'Einkommensteuer', 'Est-Erklärung'],
    'exclude': ['Freizeichnungsdokument'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Income tax declaration (without exemption document)
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `ESt Erklärung 2024.pdf`

#### 8. Est Freizeichnung (Income Tax Exemption)
```python
'est_freizeichnung': {
    'prefixes': ['ESt Erklärung Freizeichnungsdokument', 
                 'Est-Erklärung Freizeichnungsdokument'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Income tax declaration - exemption document
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `ESt Erklärung Freizeichnungsdokument 2024.pdf`

#### 9. Ust Erklärung (Sales Tax)
```python
'ust': {
    'prefixes': ['USt Erklärung'],
    'exclude': ['Freizeichnungsdokument'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Sales/VAT tax declaration (without exemption)
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `USt Erklärung 2024.pdf`

#### 10. Ust Freizeichnung (Sales Tax Exemption)
```python
'ust_freizeichnung': {
    'prefixes': ['USt Erklärung Freizeichnungsdokument'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Sales/VAT tax declaration - exemption document
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `USt Erklärung Freizeichnungsdokument 2024.pdf`

#### 11. Gewerbesteuer (Business Tax)
```python
'gewerbesteuer': {
    'prefixes': ['GewSt', 'Gewerbesteuer'],
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}
```
**Meaning**: Business tax declaration
**Input**: PDF files
**Watermark**: General watermark
**Example File**: `GewSt 2024.pdf`

---

## Merge Order

The sequence in which document types appear in the final output:

```python
'merge_order': [
    'anschreiben',                 # 1st: Cover letter
    'jahresabschluss',            # 2nd: Annual report
    'deckblatt_steuererklaerung', # 3rd: Tax declaration cover
    'offenlegung',                # 4th: Disclosure
    'kst',                        # 5th: Corporate income tax
    'kst_freizeichnung',          # 6th: Corporate tax exemption
    'est',                        # 7th: Income tax
    'est_freizeichnung',          # 8th: Income tax exemption
    'ust',                        # 9th: Sales tax
    'ust_freizeichnung',          # 10th: Sales tax exemption
    'gewerbesteuer'               # 11th: Business tax
]
```

**Important**: This order is CRITICAL - documents appear in output in this sequence, not in file discovery order.

---

## Discovery Order

The priority order for file matching (resolves conflicts):

```python
DISCOVERY_ORDER = [
    'anschreiben',                 # Check BaM first (overlaps with others)
    'deckblatt_steuererklaerung',  # Then Deckblatt (could overlap)
    'jahresabschluss',
    'offenlegung',
    'kst_freizeichnung',           # Check specific before general
    'kst',
    'est_freizeichnung',
    'est',
    'ust_freizeichnung',
    'ust',
    'gewerbesteuer'
]
```

**Why order matters**: If file matches multiple prefixes, the FIRST in this list wins.

---

## Advanced Configuration

### Modify Directory Paths

```python
CONFIG = {
    'input_dir': 'D:/Tax Documents/Input',     # Absolute path
    'output_dir': 'D:/Tax Documents/Output',
    'watermark_dir': r'C:\Watermarks',         # Windows path with raw string
    'processed_dir': 'D:/Tax Documents/Processed',
    'error_dir': 'D:/Tax Documents/Errors',
    # ... rest of config
}
```

### Disable File Movement

To keep files in input directory instead of moving them:

```python
CONFIG = {
    # ... other config ...
    'delete_input_after_processing': False,   # Don't move files
}
```

### Add Custom Document Type

Example: Add "Finanzamt Brief" (Tax Office Letter)

```python
'finanzamt_brief': {
    'prefixes': ['FA Brief', 'Finanzamt Schreiben'],
    'exclude': ['Verwarnung'],                 # Don't match warnings
    'watermark': 'Wasserzeichen Allgemein.pdf',
    'format': 'pdf'
}

# Then add to merge_order (position matters!)
'merge_order': [
    'anschreiben',
    'finanzamt_brief',              # ← New type inserted
    'jahresabschluss',
    # ... rest ...
]

# And add to DISCOVERY_ORDER
DISCOVERY_ORDER = [
    'anschreiben',
    'finanzamt_brief',              # ← Add here too
    'deckblatt_steuererklaerung',
    # ... rest ...
]
```

### Use Different Watermarks

```python
# Modern/Colorful watermark
'est': {
    'prefixes': ['ESt Erklärung'],
    'watermark': 'Wasserzeichen_Modern.pdf',  # Different file
    'format': 'pdf'
}

# Or special watermark
'special_doc': {
    'prefixes': ['Special'],
    'watermark': 'special',        # Uses special logic
    'format': 'pdf'
}
```

---

## Watermark Files

### Required Files
All these must exist in `watermarks/` folder:

```
watermarks/
├── Wasserzeichen Deckblatt.pdf      (Cover sheet - used on page 1)
├── Wasserzeichen Anschreiben.pdf    (Cover letter specific)
├── Wasserzeichen Allgemein.pdf      (General/default for most docs)
└── [Any custom watermarks defined in CONFIG]
```

### Special Watermark Logic
When `'watermark': 'special'` is set:
- Page 1: Uses `Wasserzeichen Deckblatt.pdf`
- Pages 2+: Uses `Wasserzeichen Allgemein.pdf`

```python
# In apply_special_watermark() function:
if page_number == 0:
    watermark = 'Wasserzeichen Deckblatt.pdf'
else:
    watermark = 'Wasserzeichen Allgemein.pdf'
```

---

## Configuration Example File

Save this as `config_example.py` for reference:

```python
# Example configuration with all options explained

import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_path()

CONFIG_EXAMPLE = {
    # ============ DIRECTORY CONFIGURATION ============
    
    'input_dir': os.path.join(BASE_DIR, 'input', 'Import Directory'),
    # Where to look for documents to process
    # Create: input/Import Directory/file1.pdf, file2.docx, etc.
    
    'output_dir': os.path.join(BASE_DIR, 'output'),
    # Where to save final_output.pdf
    # Auto-created if missing
    
    'watermark_dir': os.path.join(BASE_DIR, 'watermarks'),
    # Where watermark PDF files are stored
    # Must exist with required PDFs
    
    'processed_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'processed'),
    # Where to move successfully processed files
    # Auto-created if missing
    
    'error_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'error'),
    # Where to move files with processing errors
    # Auto-created if missing
    
    # ============ PROCESSING BEHAVIOR ============
    
    'delete_input_after_processing': True,
    # True: Move input files to processed/ or error/ folders
    # False: Leave files where they are
    
    # ============ DOCUMENT TYPE DEFINITIONS ============
    
    'document_types': {
        # Structure for each type:
        # 'type_name': {
        #     'prefixes': [...],          # Match file names starting with these
        #     'exclude': [...],           # Optional: skip if contains these
        #     'watermark': 'file.pdf',    # File to use, or 'special'
        #     'format': 'pdf' or 'docx'   # What format to expect
        # }
        
        'anschreiben': {
            'prefixes': ['BaM', 'Übersendung', '440372'],
            'watermark': 'Wasserzeichen Anschreiben.pdf',
            'format': 'docx'
        },
        
        # ... other types ...
    },
    
    # ============ MERGE SEQUENCE ============
    # This determines the order in final_output.pdf
    
    'merge_order': [
        'anschreiben',
        'jahresabschluss',
        'deckblatt_steuererklaerung',
        # ... etc
    ]
}
```

---

## Troubleshooting Configuration

### "No files found"
- Check: `input_dir` path is accessible
- Check: Files exist in exactly that path
- Check: File prefixes match exactly

### Watermark not appearing
- Check: `watermark_dir` path is correct
- Check: Watermark filename matches exactly (case-sensitive on Linux)
- Check: Watermark PDF file is not corrupted

### Wrong merge order in output
- Check: `merge_order` list
- Check: DISCOVERY_ORDER has priorities right

### Created wrong file sequence
- Check: `merge_order` position of each type
- Re-run after fixing order in CONFIG

---

## Best Practices

1. **Test with one document type first**
   - Don't add all document types at once
   - Find a sample file matching a prefix
   - Run processor, check output
   
2. **Verify file names match prefixes**
   - File: `ESt Erklärung 2024.pdf`
   - Prefix: `'ESt Erklärung'` in config
   - Match: ✓ YES
   
3. **Keep merge_order in logical sequence**
   - Anschreiben (letter) should be first
   - Supporting docs in sensible order
   - Don't randomize order unless needed
   
4. **Use exclude wisely**
   - `'exclude': ['Freizeichnung']` to handle variants
   - Separates main form from exemption docs
   - Reduces duplicate matching

5. **Backup before modifying CONFIG**
   - Keep version of working config
   - Test changes in copy first
   - Easy rollback if things break
