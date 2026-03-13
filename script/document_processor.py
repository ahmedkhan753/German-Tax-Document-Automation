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
        'deckblatt': {
            'prefixes': ['Deckblatt', 'Deckblatt Steuer', 'Deckblatt Word', '440368', 'Cover', 'AP Deckblatt', 'JA AP', 'Deckblatt StE', 'deckblatt_steuererklaerung'], 
            'watermark': 'Wasserzeichen Deckblatt.pdf', 
            'format': 'docx'
        },
        'berechnungen': {
            'prefixes': ['Berechnung', 'Kalkulation', '440372', 'Overview', 'Summary'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'kst': {
            'prefixes': ['KSt Erklärung', 'KSt ', 'KSt Erklärung Freizeichnungsdokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'ust': {
            'prefixes': ['USt Erklärung', 'USt ', 'USt Erklärung Freizeichnungsdokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'est': {
            'prefixes': ['ESt Erklärung', 'Einkommensteuer', 'Est-Erklärung', 'ESt ', 'ESt Erklärung Freizeichnungsdokument'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'jahresabschluss': {
            'prefixes': ['JA Jahresabschluss', 'JA Abschluss', 'Jahresabschluss', 'Bilanz', 'E-Bilanz', '439111'], 
            'watermark': 'special', 
            'format': 'pdf'
        },
        'anlagen': {
            'prefixes': ['Anlage', 'JA Offenlegung', 'Offenlegung'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'attachments': {
            'prefixes': ['Beleg', 'Support', 'Nachweis', 'Dokument', 'Attachment'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
    },
    'merge_order': [
        'anschreiben',
        'deckblatt',
        'berechnungen',
        'kst',
        'ust',
        'est',
        'jahresabschluss',
        'anlagen',
        'attachments'
    ]
}

# Priority for file matching to handle overlaps correctly
# Sequence: [0] Cover Letter, [1] Cover Page, [2] Calculations
DISCOVERY_ORDER = [
    'anschreiben',
    'deckblatt',
    'berechnungen',
    'kst',
    'ust',
    'est',
    'jahresabschluss',
    'anlagen',
    'attachments'
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
    # Use 0.15 alpha for professional semi-transparent overlay on A4
    can.setFillAlpha(0.15)
    can.setFillColorRGB(0.4, 0.4, 0.4)
    can.setFont("Helvetica-Bold", 100)
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
                    
                    if is_dynamic_spec:
                        # Dynamic diagonal KOPIE: OVERLAY (content first, watermark on top)
                        final_page.merge_page(page)
                        final_page.merge_page(wm_to_merge)
                    else:
                        # Deckblatt file-based watermark: Underlay (logo behind content)
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

def get_watermark_page(page):
    """Generate dynamic KOPIE watermark matching page size exactly."""
    pw = float(page.mediabox.width)
    ph = float(page.mediabox.height)
    
    with NamedTemporaryFile(suffix='_watermark.pdf', delete=False) as tmp:
        tmp_path = tmp.name
    
    can = canvas.Canvas(tmp_path, pagesize=(pw, ph))
    can.saveState()
    can.setFillAlpha(0.15)
    can.setFillColorRGB(0.4, 0.4, 0.4)
    
    # Scale font proportionally to page width (e.g., width / 6) to fit "KOPIE" nicely diagonally
    font_size = pw / 6.0
    can.setFont("Helvetica-Bold", font_size)
    can.translate(pw / 2, ph / 2)
    can.rotate(45)
    can.drawCentredString(0, 0, "KOPIE")
    can.restoreState()
    can.save()
    
    wm_reader = PyPDF2.PdfReader(tmp_path)
    wm_page = copy(wm_reader.pages[0])
    
    try:
        os.remove(tmp_path)
    except Exception:
        pass
        
    return wm_page

def merge_pdfs_strict(processed_files):
    """Merge documents in strict sequence with Hybrid Z-Order Watermarking."""
    logging.info("=" * 60)
    logging.info("MERGE START: Building final document with hybrid Z-order watermarks")
    logging.info("=" * 60)
    
    ordered_pdfs = []
    for doc_type in CONFIG['merge_order']:
        if doc_type in processed_files:
            ordered_pdfs.append((doc_type, processed_files[doc_type]))
            logging.info(f"SEQUENCE: {doc_type} added to merge")
            
    if not ordered_pdfs:
        logging.error("No documents to merge!")
        return None
        
    output_writer = PyPDF2.PdfWriter()
    all_pages = []
    
    for doc_type, pdf_path in ordered_pdfs:
        try:
            reader = PyPDF2.PdfReader(pdf_path)
            all_pages.extend(reader.pages)
        except Exception as e:
            logging.error(f"  ERROR processing {doc_type}: {e}", exc_info=True)
            
    for page_index, page in enumerate(all_pages):
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        final_page = PyPDF2.PageObject.create_blank_page(width=pw, height=ph)
        final_page.mediabox = page.mediabox
        
        watermark_page = get_watermark_page(page)
        
        if page_index == 0:
            # Page 1 (Cover Letter / Anschreiben)
            # Apply watermark as UNDERLAY — merge watermark first, then content on top
            final_page.merge_page(watermark_page)
            final_page.merge_page(page)
            logging.info(f"    Page {page_index + 1}: UNDERLAY KOPIE (Cover Letter)")
        else:
            # Page 2+ (Cover Page, Tax Forms, Calculations, etc.)
            # Apply watermark as OVERLAY — merge watermark on top of content
            final_page.merge_page(page)
            final_page.merge_page(watermark_page)
            logging.info(f"    Page {page_index + 1}: OVERLAY KOPIE")
            
        output_writer.add_page(final_page)

    output_path = os.path.join(CONFIG['output_dir'], 'final_output.pdf')
    with open(output_path, 'wb') as f:
        output_writer.write(f)
    
    logging.info("=" * 60)
    logging.info(f"MERGE COMPLETE: {len(all_pages)} total pages")
    logging.info(f"  Output: {output_path}")
    logging.info("=" * 60)
    
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
        tax_form_types = ['kst', 'est', 'ust']
        
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
                            
                    elif dt == 'deckblatt':
                        # Cover Page MUST be exactly 1 page (Page 2)
                        logging.info(f"Enforcing 1-page limit for {dt} (Cover Page)")
                        reader = PyPDF2.PdfReader(section_pdf)
                        writer = PyPDF2.PdfWriter()
                        writer.add_page(reader.pages[0])
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as t:
                            writer.write(t)
                            section_pdf = t.name
                            
                    # Watermarking is now handled purely during strict merge phase
                    processed_files[dt] = section_pdf
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
                
                # COMPREHENSIVE CLEANUP (Move ALL input files to processed)
                try:
                    input_dir = CONFIG['input_dir']
                    # Move every file in input directory (catch-all approach)
                    if os.path.isdir(input_dir):
                        for item in os.listdir(input_dir):
                            item_path = os.path.join(input_dir, item)
                            # Skip subdirectories (processed/, error/) 
                            if os.path.isdir(item_path):
                                continue
                            logging.info(f"Moving to processed: {item}")
                            move_file_to_processed(item_path)
                except Exception as _e:
                    logging.warning(f"Error moving remaining input files: {_e}")

                # Final Absolute Purge
                try:
                    # Remove test files, check scripts, sample files, and other junk from root
                    purge_patterns = [
                        "test_*.py", "check_*.py", "sample_*", "debug_*",
                        "*.spec", "*.log", "*.tmp",
                        "run_log.txt", "run_log_*.txt",
                        "temp_*"
                    ]
                    for pattern in purge_patterns:
                        for f in glob.glob(os.path.join(BASE_DIR, pattern)):
                            try: 
                                if os.path.isfile(f): os.remove(f)
                                elif os.path.isdir(f): shutil.rmtree(f)
                                logging.info(f"Purged: {os.path.basename(f)}")
                            except Exception:
                                pass
                    
                    junk_dirs = ["build", "dist", ".pytest_cache", "tests", "__pycache__"]
                    for d in junk_dirs:
                        d_path = os.path.join(BASE_DIR, d)
                        if os.path.exists(d_path):
                            try:
                                shutil.rmtree(d_path)
                                logging.info(f"Purged directory: {d}")
                            except Exception:
                                pass
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
