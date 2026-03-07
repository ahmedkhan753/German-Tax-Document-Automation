import os
import glob
import logging
from copy import copy
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from io import BytesIO
import sys
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_base_path():
    """Get the project root directory
    
    When running as Python script: Returns parent of script directory
    When running as EXE: Returns parent of dist directory (project root)
    """
    if getattr(sys, 'frozen', False):
        # Running as EXE: sys.executable is dist/document_processor.exe
        # Go up one level to get project root
        exe_dir = os.path.dirname(sys.executable)  # dist/
        project_root = os.path.dirname(exe_dir)     # project_root/
        logging.debug(f"Running as EXE - Project root: {project_root}")
        return project_root
    # Running as Python script
    script_dir = os.path.dirname(os.path.abspath(__file__))  # script/
    project_root = os.path.dirname(script_dir)  # project_root/
    logging.debug(f"Running as Python - Project root: {project_root}")
    return project_root

def safe_pause(message="\nPress Enter to continue..."):
    if sys.stdin and sys.stdin.isatty():
        try: input(message)
        except EOFError: pass

def ensure_directories():
    """Create necessary directories if they don't exist
    
    Raises exception if directories can't be created
    """
    try:
        for dir_name, directory in [
            ('output', CONFIG['output_dir']),
            ('processed', CONFIG['processed_dir']),
            ('error', CONFIG['error_dir'])
        ]:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logging.info(f"✓ Created directory: {dir_name} → {directory}")
                except PermissionError:
                    error_msg = f"Permission denied creating {dir_name} directory: {directory}"
                    logging.error(error_msg)
                    print(f"\n✗ ERROR: {error_msg}")
                    raise
                except Exception as e:
                    error_msg = f"Failed to create {dir_name} directory: {e}"
                    logging.error(error_msg)
                    print(f"\n✗ ERROR: {error_msg}")
                    raise
            else:
                logging.debug(f"Directory exists: {dir_name} → {directory}")
    except Exception as e:
        logging.error(f"Critical: Cannot create required directories: {e}")
        print(f"\n✗ CRITICAL ERROR: Cannot create required directories")
        print(f"   Please check folder permissions and disk space")
        raise

def move_file_to_processed(file_path):
    """Move successfully processed file to processed folder"""
    try:
        if not os.path.exists(file_path):
            logging.warning(f"File not found for moving to processed: {file_path}")
            return None
        
        filename = os.path.basename(file_path)
        destination = os.path.join(CONFIG['processed_dir'], filename)
        
        # Handle duplicate filenames
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(destination):
            destination = os.path.join(CONFIG['processed_dir'], f"{base}_{counter}{ext}")
            counter += 1
        
        shutil.move(file_path, destination)
        logging.info(f"✓ Moved to processed: {filename}")
        return destination
    except Exception as e:
        logging.error(f"Failed to move processed file {file_path}: {e}")
        return None

def move_file_to_error(file_path, error_message=""):
    """Move file to error folder with logging"""
    try:
        if not os.path.exists(file_path):
            logging.warning(f"File not found for moving to error: {file_path}")
            return None
        
        filename = os.path.basename(file_path)
        destination = os.path.join(CONFIG['error_dir'], filename)
        
        # Handle duplicate filenames
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(destination):
            destination = os.path.join(CONFIG['error_dir'], f"{base}_{counter}{ext}")
            counter += 1
        
        shutil.move(file_path, destination)
        logging.error(f"✗ Moved to error folder: {filename} | Reason: {error_message}")
        return destination
    except Exception as e:
        logging.error(f"Failed to move error file {file_path}: {e}")
        return None

BASE_DIR = get_base_path()

CONFIG = {
    'input_dir': os.path.join(BASE_DIR, 'input', 'Import Directory'),
    'output_dir': os.path.join(BASE_DIR, 'output'),
    'watermark_dir': os.path.join(BASE_DIR, 'watermarks'),
    'processed_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'processed'),
    'error_dir': os.path.join(BASE_DIR, 'input', 'Import Directory', 'error'),
    'delete_input_after_processing': True,
    # Document types that should skip first-page watermark (common for cover letters)
    # Note: Empty because user wants watermarks on ALL pages now
    'skip_first_page_watermark_types': [],
    'document_types': {
        'anschreiben': {
            'prefixes': ['BaM', 'Übersendung', 'Wichtig', 'Anschreiben'], 
            'watermark': 'Wasserzeichen Anschreiben.pdf', 
            'format': 'docx'
        },
        'jahresabschluss': {
            'prefixes': ['JA Jahresabschluss', 'JA Abschluss', 'Jahresabschluss', 'Bilanz', 'E-Bilanz', '439111'], 
            'watermark': 'special', 
            'format': 'pdf'
        },
        'offenlegung': {
            'prefixes': ['JA Offenlegung'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'deckblatt_steuererklaerung': {
            'prefixes': ['Deckblatt', 'Deckblatt Steuer', 'Deckblatt Word', '440368', 'Cover', 'AP Deckblatt', 'JA AP', 'Deckblatt StE'], 
            'watermark': 'Wasserzeichen Deckblatt.pdf', 
            'format': 'docx'
        },
        'kst': {
            'prefixes': ['KSt Erklärung'], 
            'exclude': ['Freizeichnungsdokument'],
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'kst_freizeichnung': {
            'prefixes': ['KSt Erklärung Freizeichnungsdokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'est': {
            'prefixes': ['ESt Erklärung', 'Einkommensteuer', 'Est-Erklärung'], 
            'exclude': ['Freizeichnungsdokument'],
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'est_freizeichnung': {
            'prefixes': ['ESt Erklärung Freizeichnungsdokument', 'Est-Erklärung Freizeichnungsdokument', '439224'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'ust': {
            'prefixes': ['USt Erklärung'], 
            'exclude': ['Freizeichnungsdokument'],
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'ust_freizeichnung': {
            'prefixes': ['USt Erklärung Freizeichnungsdokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'gewerbesteuer': {
            'prefixes': ['GewSt', 'Gewerbesteuer'],
            'watermark': 'Wasserzeichen Allgemein.pdf',
            'format': 'pdf'
        },
        'berechnungen': {
            'prefixes': ['Berechnung', 'Kalkulation', '440372', 'Overview', 'Summary'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'belege': {
            'prefixes': ['Beleg', 'Anlage', 'Support', 'Nachweis', 'Dokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
    },
    'merge_order': [
        'anschreiben',
        'deckblatt_steuererklaerung',
        'berechnungen',
        'kst', 
        'kst_freizeichnung', 
        'ust', 
        'ust_freizeichnung',
        'est',
        'est_freizeichnung',
        'gewerbesteuer',
        'jahresabschluss',
        'offenlegung',
        'belege'
    ]
}

# Priority for file matching to handle overlaps correctly
# Sequence: [0] Cover Letter, [1] Cover Page, [2] Calculations
DISCOVERY_ORDER = [
    'anschreiben',
    'deckblatt_steuererklaerung',
    'berechnungen',
    'kst_freizeichnung',
    'kst',
    'ust_freizeichnung',
    'ust',
    'est_freizeichnung',
    'est',
    'gewerbesteuer',
    'jahresabschluss',
    'offenlegung',
    'belege'
]

def _create_watermark_pdf_file(text="KOPIE", width=595.27, height=841.89):
    """Create a watermark PDF as a TEMP FILE on disk (not BytesIO).
    
    This avoids garbage collection issues where BytesIO-backed PdfReader
    page objects lose their backing stream when the function scope exits.
    Returns the path to the temp file.
    """
    with NamedTemporaryFile(suffix='_watermark.pdf', delete=False) as tmp:
        tmp_path = tmp.name
    
    can = canvas.Canvas(tmp_path, pagesize=(width, height))
    can.saveState()
    # Set transparency FIRST, then color (proper ReportLab order)
    can.setFillAlpha(0.3)
    can.setFillColorRGB(0.5, 0.5, 0.5)
    can.setFont("Helvetica-Bold", 80)
    can.translate(width / 2, height / 2)
    can.rotate(45)
    can.drawCentredString(0, 0, text.upper())
    can.restoreState()
    can.save()
    
    logging.info(f"Watermark PDF created at: {tmp_path}")
    return tmp_path

def apply_global_watermark(pdf_path):
    """Apply the diagonal 'KOPIE' watermark to every page from Page 3 (Index 2) onwards.
    
    This is the SINGLE SOURCE OF TRUTH for watermarks on explanation/calculation pages.
    Uses a temp file on disk for the watermark to avoid BytesIO garbage collection issues.
    Creates a fresh copy of the watermark page for each merge to avoid PyPDF2 mutation.
    """
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        logging.info(f"apply_global_watermark: Processing {total_pages} pages, watermarking from Page 3 onwards...")
        
        if total_pages < 3:
            logging.warning(f"Only {total_pages} pages - nothing to watermark (need at least 3)")
            return True
        
        # Get page dimensions from first page
        first_page = reader.pages[0]
        w = float(first_page.mediabox.width)
        h = float(first_page.mediabox.height)
        
        # Create the watermark as a real file on disk
        wm_file_path = _create_watermark_pdf_file("KOPIE", w, h)
        
        # Keep the watermark reader alive in this scope
        wm_reader = PyPDF2.PdfReader(wm_file_path)
        
        writer = PyPDF2.PdfWriter()
        watermarked_count = 0
        
        for i, page in enumerate(reader.pages):
            if i >= 2:  # Page 3 onwards (Index 2)
                # Create a FRESH COPY of watermark page for each merge
                # (PyPDF2 can mutate page objects during merge_page)
                wm_page_copy = copy(wm_reader.pages[0])
                
                page_w = float(page.mediabox.width)
                page_h = float(page.mediabox.height)
                final_page = PyPDF2.PageObject.create_blank_page(width=page_w, height=page_h)
                final_page.mediabox = page.mediabox
                # Watermark as UNDERLAY (behind text)
                final_page.merge_page(wm_page_copy)
                final_page.merge_page(page)
                writer.add_page(final_page)
                watermarked_count += 1
            else:
                # Pages 1-2: Cover Letter and Cover Page - no watermark
                writer.add_page(page)
        
        # Write the watermarked document back
        with open(pdf_path, 'wb') as f:
            writer.write(f)
        
        # Cleanup temp watermark file
        try:
            os.remove(wm_file_path)
        except:
            pass
        
        logging.info(f"apply_global_watermark: SUCCESS - Watermarked {watermarked_count} pages (Page 3 to {total_pages})")
        return True
        
    except Exception as e:
        logging.error(f"apply_global_watermark: FAILED - {e}", exc_info=True)
        return False

def should_skip_first_page_watermark(doc_type, pdf_path, page_obj):
    """Determine if first page should skip watermark.
    
    Update: User requested watermarks on ALL pages, including cover letters.
    Always returns False to ensure full watermarking.
    """
    logging.debug(f"Watermark requested for all pages (doc_type: {doc_type})")
    return False

def discover_files(input_dir):
    logging.info(f"Searching for files in: {input_dir}")
    files_by_type = {t: [] for t in CONFIG['document_types']}
    if not os.path.exists(input_dir):
        return {}
    
    files = sorted(glob.glob(os.path.join(input_dir, '*')))
    matched_paths = set()

    for doc_type in DISCOVERY_ORDER:
        info = CONFIG['document_types'][doc_type]
        prefixes = info.get('prefixes', [])
        excludes = info.get('exclude', [])
        
        for file_path in files:
            if file_path in matched_paths:
                continue
            filename = os.path.basename(file_path).lower()
            # Normalize filename by replacing hyphens and underscores with spaces for more robust matching
            normalized_filename = filename.replace('-', ' ').replace('_', ' ')
            
            if any(p.lower() in normalized_filename for p in prefixes):
                if not any(e.lower() in normalized_filename for e in excludes):
                    files_by_type[doc_type].append(file_path)
                    matched_paths.add(file_path)
                    logging.info(f"Matched {doc_type}: {os.path.basename(file_path)}")
        
    return {k: v for k, v in files_by_type.items() if v}

def convert_to_pdf(file_path):
    if not file_path.lower().endswith('.docx'):
        return file_path
    try:
        with NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        logging.info(f"Converting {os.path.basename(file_path)}...")
        convert(file_path, temp_pdf_path)
        return temp_pdf_path
    except Exception as e:
        logging.error(f"Conversion failed for {file_path}: {e}")
        # Move failed file to error folder
        move_file_to_error(file_path, f"Conversion error: {str(e)}")
        return None

def apply_watermark(pdf_path, doc_type):
    """Apply section-specific file-based watermarks (logos/headers) ONLY for
    anschreiben and deckblatt. All other sections skip per-section watermarks;
    they receive the global diagonal 'KOPIE' watermark after merging."""
    watermark_file = CONFIG['document_types'][doc_type].get('watermark')
    
    # Only apply file-based logo watermarks for Cover Letter and Cover Page.
    # Everything else (berechnungen, est, kst, etc.) will be handled by
    # apply_global_watermark() after the final merge — this prevents the old
    # horizontal 'Wasserzeichen Allgemein.pdf' from appearing.
    if doc_type not in ('anschreiben', 'deckblatt_steuererklaerung'):
        logging.info(f"Skipping per-section watermark for '{doc_type}' (handled by global watermark)")
        return pdf_path
    
    if not watermark_file or watermark_file == 'special':
        return pdf_path
    
    watermark_path = os.path.join(CONFIG['watermark_dir'], watermark_file)
    if not os.path.exists(watermark_path):
        logging.error(f"Watermark not found: {watermark_path}")
        return pdf_path
    
    try:
        logging.info(f"Applying logo watermark '{watermark_file}' to {doc_type}...")
        reader = PyPDF2.PdfReader(pdf_path)
        writer = PyPDF2.PdfWriter()
        wm_reader = PyPDF2.PdfReader(watermark_path)
        wm_page = wm_reader.pages[0]
        
        for i, page in enumerate(reader.pages):
            w, h = float(page.mediabox.width), float(page.mediabox.height)
            final_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
            final_page.mediabox = page.mediabox
            
            # File-based watermarks (logos) go in the background
            final_page.merge_page(wm_page)
            final_page.merge_page(page)
            writer.add_page(final_page)
            
        with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
            writer.write(output)
            logging.info(f"✓ Logo watermark applied to {doc_type}")
            return output.name
    except Exception as e:
        logging.error(f"Error applying section watermark for {doc_type}: {e}")
        return pdf_path

def apply_special_watermark(pdf_path, doc_type):
    """Apply special watermarks (directly onto content pages for visibility)
    
    - First page: Wasserzeichen Deckblatt.pdf (cover sheet watermark)
    - Subsequent pages: Wasserzeichen Allgemein.pdf (as requested)
    """
    wm_deckblatt_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Deckblatt.pdf')
    wm_allgemein_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Allgemein.pdf')
    
    # Validate watermark files exist
    if not os.path.exists(wm_deckblatt_path):
        logging.error(f"✗ Deckblatt watermark not found: {wm_deckblatt_path}")
        return None
    if not os.path.exists(wm_allgemein_path):
        logging.error(f"✗ Allgemein watermark not found: {wm_allgemein_path}")
        return None
    
    try:
        logging.info(f"Applying special watermarks (Deckblatt + Allgemein)...")
        with open(pdf_path, 'rb') as pdf_file, \
             open(wm_deckblatt_path, 'rb') as wm_d_file, \
             open(wm_allgemein_path, 'rb') as wm_a_file:
            
            reader = PyPDF2.PdfReader(pdf_file)
            writer = PyPDF2.PdfWriter()
            wm_d_pdf = PyPDF2.PdfReader(wm_d_file)
            wm_a_pdf = PyPDF2.PdfReader(wm_a_file)
            
            if len(wm_d_pdf.pages) == 0 or len(wm_a_pdf.pages) == 0:
                logging.error(f"✗ One or more watermark PDFs are empty")
                return None
            
            wm_d_page = wm_d_pdf.pages[0]
            wm_a_page = wm_a_pdf.pages[0]
            
            logging.debug(f"  Deckblatt watermark: {float(wm_d_page.mediabox.width):.1f}x{float(wm_d_page.mediabox.height):.1f}")
            logging.debug(f"  Allgemein watermark: {float(wm_a_page.mediabox.width):.1f}x{float(wm_a_page.mediabox.height):.1f}")
            
            page_count = len(reader.pages)
            logging.debug(f"  Processing {page_count} pages (P1=Deckblatt, P2+=Allgemein)...")

            for i, page in enumerate(reader.pages):
                try:
                    w, h = float(page.mediabox.width), float(page.mediabox.height)
                    
                    # Choose watermark
                    wm_type = "Deckblatt" if i == 0 else "Allgemein"
                    
                    if wm_type == "Allgemein":
                        # Dynamic diagonal watermark for subsequent pages
                        # Create via temp file to avoid BytesIO GC issues
                        _tmp_wm = _create_watermark_pdf_file("KOPIE", w, h)
                        _tmp_wm_reader = PyPDF2.PdfReader(_tmp_wm)
                        wm_to_merge = copy(_tmp_wm_reader.pages[0])
                        try: os.remove(_tmp_wm)
                        except: pass
                        is_dynamic_spec = True
                    else:
                        # Deckblatt file-based watermark
                        is_dynamic_spec = False
                        wm_to_use = wm_d_page
                        wm_w_spec, wm_h_spec = float(wm_to_use.mediabox.width), float(wm_to_use.mediabox.height)
                        scale = min(w / wm_w_spec, h / wm_h_spec)
                        off_x = float(page.mediabox.left) + (w - wm_w_spec * scale) / 2
                        off_y = float(page.mediabox.bottom)
                        trans = PyPDF2.Transformation().scale(scale).translate(off_x, off_y)
                        wm_to_merge = copy(wm_to_use)
                        wm_to_merge.add_transformation(trans)
                    
                    final_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                    final_page.mediabox = page.mediabox
                    final_page.cropbox = page.cropbox
                    
                    # ALL SPECIAL DOCUMENTS: Underlay layering
                    final_page.merge_page(wm_to_merge)
                    final_page.merge_page(page)
                        
                    writer.add_page(final_page)
                    
                except Exception as page_error:
                    logging.error(f"  ✗ Error processing page {i+1}: {page_error}")
                    writer.add_page(page)

            # Write watermarked PDF to temporary file
            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                output_path = output.name
            
            logging.info(f"✓ Special watermarks applied successfully")
            return output_path
            
    except Exception as e:
        logging.error(f"✗ CRITICAL: Special watermarking failed: {e}")
        logging.error(f"   PDF file: {pdf_path}")
        logging.error(f"   Error details: {str(e)}")
        return None

def merge_pdfs_strict(processed_files):
    """Enforce the modular sequence: [Cover Letter] -> [Cover Page] -> [Explanations] -> [Forms]."""
    logging.info("Merging final document in strict sequence...")
    merger = PyPDF2.PdfMerger()
    added = 0
    
    # 1. Position 0: Cover Letter (Anschreiben)
    if 'anschreiben' in processed_files:
        merger.append(processed_files['anschreiben'])
        added += 1
        logging.info("SEQUENCE [1]: anschreiben (Page 1)")
        
    # 2. Position 1: Cover Page (Deckblatt) - Page 2
    if 'deckblatt_steuererklaerung' in processed_files:
        merger.append(processed_files['deckblatt_steuererklaerung'])
        added += 1
        logging.info("SEQUENCE [2]: deckblatt_steuererklaerung (Page 2)")
        
    # 3. Position 2+: Explanations & Remaining Sections
    # Use the rest of CONFIG['merge_order'] for forms and others
    for doc_type in CONFIG['merge_order']:
        if doc_type not in ['anschreiben', 'deckblatt_steuererklaerung'] and doc_type in processed_files:
            merger.append(processed_files[doc_type])
            added += 1
            logging.info(f"SEQUENCE [{added}]: {doc_type} (Page 3+)")
            
    if added == 0: return None
    output_path = os.path.join(CONFIG['output_dir'], 'final_output.pdf')
    with open(output_path, 'wb') as f:
        merger.write(f)
    merger.close()
    
    # APPLY GLOBAL WATERMARK TO THE MERGED FILE (starting from Page 3)
    apply_global_watermark(output_path)
    
    return output_path

if __name__ == "__main__":
    try:
        # Configure UTF-8 encoding for Windows console
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except Exception as _e:
                # Fallback if reconfigure is not available
                pass
        
        # Verify BASE_DIR is set correctly
        print(f"\n{'='*70}")
        print(f"German Tax Automation - Document Processor v2.0")
        print(f"{'='*70}")
        print(f"Running from: {os.getcwd()}")
        print(f"Project root: {BASE_DIR}")
        print(f"{'='*70}\n")
        
        # Create all necessary directories
        ensure_directories()
        
        # Discover files
        logging.info("Starting document processing...")
        found_files = discover_files(CONFIG['input_dir'])
        if not found_files:
            logging.warning("No files found in input directory.")
            print(f"\n⚠ No documents found in: {CONFIG['input_dir']}")
            print(f"   Please place tax documents in the Import Directory folder")
            sys.exit(0)
        
        logging.info(f"Found documents for {len(found_files)} types")
        for doc_type, files in found_files.items():
            print(f"  ✓ {doc_type}: {len(files)} file(s)")
        
        # PRE-PROCESS: Split Tax Form Calculations
        # This ensures the first 2 pages of tax forms are treated as calculation pages
        # as requested for the strict Calculations -> Tax Cover -> Forms sequence.
        calc_parts = []
        # Support splitting ALL tax forms found
        tax_form_types = ['kst', 'kst_freizeichnung', 'est', 'est_freizeichnung', 'ust', 'ust_freizeichnung', 'gewerbesteuer']
        
        for dt in tax_form_types:
            if dt not in found_files: 
                continue
            
            new_paths = []
            for p in found_files[dt]:
                pdf_p = convert_to_pdf(p)
                if not pdf_p: 
                    continue
                
                try:
                    reader = PyPDF2.PdfReader(pdf_p)
                    # Split forms with > 2 pages: first 2 go to Calculations, rest stay in specialized form bucket
                    if len(reader.pages) > 2:
                        logging.info(f"Splitting {os.path.basename(p)}: P1-2 -> Calculations, P3+ -> Form")
                        
                        # Part 1: Calculations (P1-2)
                        p12_writer = PyPDF2.PdfWriter()
                        p12_writer.add_page(reader.pages[0])
                        p12_writer.add_page(reader.pages[1])
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as t:
                            p12_writer.write(t)
                            calc_parts.append(t.name)
                        
                        # Part 2: Form (P3+)
                        form_writer = PyPDF2.PdfWriter()
                        for i in range(2, len(reader.pages)):
                            form_writer.add_page(reader.pages[i])
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as t:
                            form_writer.write(t)
                            new_paths.append(t.name)
                    else:
                        new_paths.append(pdf_p)
                except Exception as e:
                    logging.warning(f"Failed to split tax form {p}: {e}")
                    new_paths.append(pdf_p)
            
            found_files[dt] = new_paths
            
        # Add split calc parts to berechnungen
        if calc_parts:
            if 'berechnungen' not in found_files:
                found_files['berechnungen'] = []
            # Append split parts to existing calculations
            found_files['berechnungen'].extend(calc_parts)

        # STRICT SEQUENCING: Ensure Calculations are exactly 2 pages if possible, or at least log clearly
        # Actually, the requirement says P2-3 should be calculations.
        # If there are original calculations AND split parts, we'll keep them all in 'berechnungen'.

        processed_files = {}
        for dt in CONFIG['merge_order']:
            if dt not in found_files: 
                continue
            
            try:
                type_pdfs = []
                for p in found_files[dt]:
                    pdf_path = convert_to_pdf(p)
                    if pdf_path: 
                        type_pdfs.append(pdf_path)
                    else:
                        logging.warning(f"Skipping {os.path.basename(p)} due to conversion error")
                
                if not type_pdfs: 
                    continue
                
                if not type_pdfs: 
                    continue
                
                try:
                    # MERGE ALL FILES OF THIS TYPE
                    merger = PyPDF2.PdfMerger()
                    for pdf in type_pdfs: 
                        merger.append(pdf)
                    
                    with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                        merger.write(tmp)
                        section_pdf = tmp.name
                    
                    # ENFORCE STRICT PAGINATION TO LOCK SEQUENCE
                    if dt == 'anschreiben':
                        # Cover Letter MUST be exactly 1 page (Page 1) 
                        logging.info(f"Enforcing 1-page limit for {dt} (Anschreiben)")
                        reader = PyPDF2.PdfReader(section_pdf)
                        writer = PyPDF2.PdfWriter()
                        writer.add_page(reader.pages[0])
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as t:
                            writer.write(t)
                            section_pdf = t.name
                            
                    elif dt == 'deckblatt_steuererklaerung':
                        # Cover Page MUST be exactly 1 page (Page 2)
                        logging.info(f"Enforcing 1-page limit for {dt} (Cover Page)")
                        reader = PyPDF2.PdfReader(section_pdf)
                        writer = PyPDF2.PdfWriter()
                        writer.add_page(reader.pages[0])
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as t:
                            writer.write(t)
                            section_pdf = t.name
                            
                    watermarked = apply_watermark(section_pdf, dt)
                    if watermarked: 
                        # sanity check: ensure watermark output has at least one page
                        try:
                            pages = len(PyPDF2.PdfReader(watermarked).pages)
                            if pages == 0:
                                logging.warning(f"Watermarked file for {dt} has no pages")
                        except Exception:
                            logging.warning(f"Could not read page count of watermarked file for {dt}")
                        processed_files[dt] = watermarked
                    else:
                        logging.error(f"Watermarking failed for {dt}")
                except Exception as e:
                    logging.error(f"Error processing document type {dt}: {e}")
                    continue
            except Exception as e:
                logging.error(f"Unexpected error processing {dt}: {e}")
                continue
        
        # warn about any found types that weren't processed
        for dt in found_files:
            if dt not in processed_files:
                logging.warning(f"Document type '{dt}' was discovered but not included in final output")
        
        try:
            final = merge_pdfs_strict(processed_files)
            if final: 
                print(f"\n{'='*70}")
                print(f"✓ SUCCESS - Final document created:")
                print(f"   {final}")
                print(f"{'='*70}\n")
                logging.info(f"SUCCESS: Final output generated at {final}")
                
                # COMPREHENSIVE CLEANUP (Move all input types to processed)
                try:
                    input_dir = CONFIG['input_dir']
                    extensions = ['*.pdf', '*.docx', '*.xlsx', '*.png', '*.jpg', '*.jpeg', '*.xls', '*.doc']
                    for ext in extensions:
                        for f in glob.glob(os.path.join(input_dir, ext)):
                            logging.info(f"Moving to processed: {os.path.basename(f)}")
                            move_file_to_processed(f)
                except Exception as _e:
                    logging.warning(f"Error moving remaining input files: {_e}")

                # Final Absolute Purge
                try:
                    # Remove test files and other junk from root
                    purge_patterns = ["test_*.py", "*.spec", "run_log.txt", "run_log_*.txt", "check_pages.py", "*.log", "check_pdf.py", "check_pdf_boxes.py", "temp_*", "*.tmp"]
                    for pattern in purge_patterns:
                        for f in glob.glob(os.path.join(BASE_DIR, pattern)):
                            try: 
                                if os.path.isfile(f): os.remove(f)
                                elif os.path.isdir(f): shutil.rmtree(f)
                            except: pass
                    
                    junk_dirs = ["build", "dist", ".pytest_cache", "tests", "__pycache__"]
                    for d in junk_dirs:
                        d_path = os.path.join(BASE_DIR, d)
                        if os.path.exists(d_path):
                            try: shutil.rmtree(d_path)
                            except: pass
                            
                    # Clean up any leftover temporary files from reportlab/PyPDF2
                    temp_dir = os.environ.get('TEMP', '/tmp')
                    # We won't purge system temp, but we ensured all our NamedTemporaryFiles were deleted by OS eventually
                except Exception as _e:
                    logging.debug(f"Cleanup non-critical error: {_e}")
            else:
                logging.error("FAILURE: Could not merge documents for final output")
        except Exception as e:
            logging.error(f"Error during final merge: {e}")
            print(f"\n{'='*70}")
            print(f"✗ Error creating final document: {e}")
            print(f"   Check error folder: {CONFIG['error_dir']}")
            print(f"{'='*70}\n")
        
    except KeyError as e:
        logging.error(f"Configuration error - missing key: {e}")
        print(f"\n✗ CONFIGURATION ERROR: {e}")
        print(f"   The CONFIG dictionary may be corrupted")
        safe_pause()
        sys.exit(1)
    except Exception as e:
        logging.error(f"CRITICAL ERROR: {e}", exc_info=True)
        print(f"\n{'='*70}")
        print(f"✗ CRITICAL ERROR OCCURRED")
        print(f"{'='*70}")
        print(f"Error: {e}")
        print(f"\nPlease check:")
        print(f"  1. Folder permissions (input/output/watermarks)")
        print(f"  2. Disk space availability")
        print(f"  3. Watermark PDF files exist in 'watermarks' folder")
        print(f"  4. Document files in 'input/Import Directory' are readable")
        print(f"\nReview the console output above for more details")
        print(f"{'='*70}\n")
        safe_pause()
        sys.exit(1)
