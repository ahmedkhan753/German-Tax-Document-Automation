import os
import glob
import logging
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from io import BytesIO
import sys

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
        
        os.rename(file_path, destination)
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
        
        os.rename(file_path, destination)
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
    'document_types': {
        'anschreiben': {
            'prefixes': ['BaM', 'Übersendung', '440372'], 
            'watermark': 'Wasserzeichen Anschreiben.pdf', 
            'format': 'docx'
        },
        'jahresabschluss': {
            'prefixes': ['JA Jahresabschluss', 'JA Abschluss'], 
            'watermark': 'special', 
            'format': 'pdf'
        },
        'offenlegung': {
            'prefixes': ['JA Offenlegung'], 
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'deckblatt_steuererklaerung': {
            'prefixes': ['Deckblatt', 'Deckblatt Steuer', 'Deckblatt Word', '440368', 'Cover', 'Deckblatt Einkommensteuer', 'Deckblatt ESt', 'AP Deckblatt', 'JA AP'], 
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
            'prefixes': ['ESt Erklärung Freizeichnungsdokument', 'Est-Erklärung Freizeichnungsdokument'], 
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
    },
    'merge_order': [
        'anschreiben',
        'jahresabschluss', 
        'deckblatt_steuererklaerung', 
        'offenlegung', 
        'kst', 
        'kst_freizeichnung', 
        'est',
        'est_freizeichnung',
        'ust', 
        'ust_freizeichnung',
        'gewerbesteuer'
    ]
}

# Priority for file matching to handle overlaps correctly
DISCOVERY_ORDER = [
    'anschreiben',                 # Catch BaM/Übersendung first
    'deckblatt_steuererklaerung',  # Then catch Deckblatt/440368
    'jahresabschluss',
    'offenlegung',
    'kst_freizeichnung',
    'kst',
    'est_freizeichnung',
    'est',
    'ust_freizeichnung',
    'ust',
    'gewerbesteuer'
]

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
        # Optionally remove original input file after successful conversion
        try:
            if CONFIG.get('delete_input_after_processing'):
                try:
                    # Move file to processed folder instead of permanent deletion
                    move_file_to_processed(file_path)
                    logging.info(f"Moved to processed after conversion: {file_path}")
                except Exception as _e:
                    logging.warning(f"Could not move original input {file_path}: {_e}")
        except Exception:
            pass
        return temp_pdf_path
    except Exception as e:
        logging.error(f"Conversion failed for {file_path}: {e}")
        # Move failed file to error folder
        move_file_to_error(file_path, f"Conversion error: {str(e)}")
        return None

def apply_watermark(pdf_path, doc_type):
    watermark_file = CONFIG['document_types'][doc_type]['watermark']
    if watermark_file == 'special':
        return apply_special_watermark(pdf_path)
    
    watermark_path = os.path.join(CONFIG['watermark_dir'], watermark_file)
    try:
        with open(pdf_path, 'rb') as pdf_file, open(watermark_path, 'rb') as wm_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            wm_page = PyPDF2.PdfReader(wm_file).pages[0]
            writer = PyPDF2.PdfWriter()
            
            wm_w, wm_h = float(wm_page.mediabox.width), float(wm_page.mediabox.height)
            logging.info(f"Watermark '{watermark_file}' dimensions: {wm_w}x{wm_h}")

            for i, page in enumerate(pdf_reader.pages):
                w, h = float(page.mediabox.width), float(page.mediabox.height)
                rotation = page.get('/Rotate', 0)
                
                scale = min(w / wm_w, h / wm_h)
                off_x = (w - (wm_w * scale)) / 2
                off_y = (h - (wm_h * scale)) / 2
                
                if i == 0:
                    logging.info(f"  Page {i+1} size: {w}x{h}, scale factor: {scale:.2f}, offset: ({off_x:.1f}, {off_y:.1f})")
                
                trans = PyPDF2.Transformation().scale(scale).translate(off_x, off_y)
                wm_overlay = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                wm_overlay.merge_page(wm_page)
                
                # Handle rotation for the brand overlay
                if rotation != 0:
                    if rotation == 90: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(90).translate(w, 0))
                    elif rotation == 180: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(180).translate(w, h))
                    elif rotation == 270: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(270).translate(0, h))
                
                wm_overlay.add_transformation(trans)
                
                # CRITICAL Z-LAYER ORDER: Place watermark BEHIND content so text remains readable
                # The background must be created first, then watermark merged, then content merged on top
                new_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                new_page.merge_page(wm_overlay)  # Watermark layer (background)
                new_page.merge_page(page)        # Content layer (foreground)
                writer.add_page(new_page)
                logging.debug(f"  Page {i+1}: Watermark positioned as background layer ✓")

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Watermark applied successfully with proper z-order (background)")
                return output.name
    except Exception as e:
        logging.error(f"Watermarking failed: {e}")
        return pdf_path

def apply_special_watermark(pdf_path):
    """Apply special watermarks with proper z-order (background layer)
    
    - First page: Wasserzeichen Deckblatt.pdf (cover sheet watermark)
    - Other pages: Wasserzeichen Allgemein.pdf (general watermark)
    """
    wm_deckblatt_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Deckblatt.pdf')
    wm_allgemein_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Allgemein.pdf')
    try:
        with open(pdf_path, 'rb') as pdf_file, \
             open(wm_deckblatt_path, 'rb') as wm_d_file, \
             open(wm_allgemein_path, 'rb') as wm_a_file:
            
            reader = PyPDF2.PdfReader(pdf_file)
            writer = PyPDF2.PdfWriter()
            wm_d_page = PyPDF2.PdfReader(wm_d_file).pages[0]
            wm_a_page = PyPDF2.PdfReader(wm_a_file).pages[0]

            for i, page in enumerate(reader.pages):
                w, h = float(page.mediabox.width), float(page.mediabox.height)
                rotation = page.get('/Rotate', 0)
                wm_to_use = wm_d_page if i == 0 else wm_a_page
                
                wm_w, wm_h = float(wm_to_use.mediabox.width), float(wm_to_use.mediabox.height)
                scale = min(w / wm_w, h / wm_h)
                off_x, off_y = (w - (wm_w * scale)) / 2, (h - (wm_h * scale)) / 2
                trans = PyPDF2.Transformation().scale(scale).translate(off_x, off_y)
                
                wm_overlay = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                wm_overlay.merge_page(wm_to_use)
                if rotation != 0:
                    if rotation == 90: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(90).translate(w, 0))
                    elif rotation == 180: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(180).translate(w, h))
                    elif rotation == 270: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(270).translate(0, h))

                wm_overlay.add_transformation(trans)
                
                # CRITICAL Z-LAYER ORDER: Place watermark BEHIND content so text remains readable
                # The background must be created first, then watermark merged, then content merged on top
                new_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                new_page.merge_page(wm_overlay)  # Watermark layer (background)
                new_page.merge_page(page)        # Content layer (foreground)
                writer.add_page(new_page)
                logging.debug(f"  Page {i+1}: Special watermark positioned as background layer ✓")

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Special watermark applied successfully with proper z-order (background)")
                return output.name
    except Exception as e:
        logging.error(f"Special watermarking failed: {e}")
        return pdf_path

def merge_pdfs(processed_files):
    logging.info("Merging final document...")
    merger = PyPDF2.PdfMerger()
    added = 0
    for doc_type in CONFIG['merge_order']:
        if doc_type in processed_files:
            merger.append(processed_files[doc_type])
            added += 1
            logging.info(f"SEQUENCE [{added}]: Added {doc_type}")
            
    if added == 0: return None
    output_path = os.path.join(CONFIG['output_dir'], 'final_output.pdf')
    with open(output_path, 'wb') as f:
        merger.write(f)
    merger.close()
    return output_path

if __name__ == "__main__":
    try:
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
                
                try:
                    if len(type_pdfs) > 1:
                        merger = PyPDF2.PdfMerger()
                        for pdf in type_pdfs: 
                            merger.append(pdf)
                        with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                            merger.write(tmp)
                            section_pdf = tmp.name
                    else:
                        section_pdf = type_pdfs[0]
                    
                    watermarked = apply_watermark(section_pdf, dt)
                    if watermarked: 
                        processed_files[dt] = watermarked
                    else:
                        logging.error(f"Watermarking failed for {dt}")
                except Exception as e:
                    logging.error(f"Error processing document type {dt}: {e}")
                    continue
            except Exception as e:
                logging.error(f"Unexpected error processing {dt}: {e}")
                continue
        
        try:
            final = merge_pdfs(processed_files)
            if final: 
                print(f"\n{'='*70}")
                print(f"✓ SUCCESS - Final document created:")
                print(f"   {final}")
                print(f"{'='*70}\n")
                logging.info(f"SUCCESS: Final output generated at {final}")
            else:
                print(f"\n{'='*70}")
                print(f"✗ FAILURE - Could not create final document")
                print(f"   Check error folder: {CONFIG['error_dir']}")
                print(f"{'='*70}\n")
                logging.error("FAILURE: Could not merge documents for final output")
        except Exception as e:
            logging.error(f"Error during final merge: {e}")
            print(f"\n{'='*70}")
            print(f"✗ Error creating final document: {e}")
            print(f"   Check error folder: {CONFIG['error_dir']}")
            print(f"{'='*70}\n")

        safe_pause()
        
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
