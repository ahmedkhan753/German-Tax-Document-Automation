import os
import glob
import logging
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile

import sys

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_base_path():
    if getattr(sys, 'frozen', False):
        # If running as an EXE
        exe_dir = os.path.dirname(sys.executable)
        # If running from 'dist' folder, go one level up to project root
        if os.path.basename(exe_dir).lower() == 'dist':
            return os.path.dirname(exe_dir)
        return exe_dir
    # If running as a script (~/script/document_processor.py)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def safe_pause(message="\nPress Enter to continue..."):
    """Pauses the script only if stdin is available."""
    if sys.stdin and sys.stdin.isatty():
        try:
            input(message)
        except EOFError:
            pass

BASE_DIR = get_base_path()

CONFIG = {
    'input_dir': os.path.join(BASE_DIR, 'input', 'Daten Franklin'),
    'output_dir': os.path.join(BASE_DIR, 'output'),
    'watermark_dir': os.path.join(BASE_DIR, 'watermarks'),
    'document_types': {
        'anschreiben': {
            'prefixes': ['BaM', 'Übersendung'], 
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
            'prefixes': ['Deckblatt Steuererklärung'], 
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
        'offenlegung', 
        'deckblatt_steuererklaerung', 
        'kst', 
        'kst_freizeichnung', 
        'ust', 
        'ust_freizeichnung',
        'gewerbesteuer'
    ]
}

# File discovery function
def discover_files(input_dir):
    logging.info(f"Searching for files in: {os.path.abspath(input_dir)}")
    files_by_type = {t: [] for t in CONFIG['document_types']}
    
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        return {}

    # Get all files and sort them
    files = sorted(glob.glob(os.path.join(input_dir, '*')))
    matched_paths = set()

    # We iterate over merge_order to prioritize matching in that order if needed,
    # but the primary goal is unique matching.
    for doc_type in CONFIG['merge_order']:
        info = CONFIG['document_types'][doc_type]
        prefixes = info.get('prefixes', [])
        excludes = info.get('exclude', [])
        
        for file_path in files:
            if file_path in matched_paths:
                continue
                
            filename = os.path.basename(file_path).lower()
            
            # Check if any prefix matches
            if any(prefix.lower() in filename for prefix in prefixes):
                # Check if any exclusion applies
                if not any(exclude.lower() in filename for exclude in excludes):
                    files_by_type[doc_type].append(file_path)
                    matched_paths.add(file_path)
                    logging.info(f"Matched {doc_type}: {os.path.basename(file_path)}")
        
    found = {k: v for k, v in files_by_type.items() if v}
    logging.info(f"Discovery complete. Found {len(found)} file types.")
    return found


# function to convert word file to pdf file
def convert_to_pdf(file_path):
    if not file_path.lower().endswith('.docx'):
        return file_path  # Already PDF
    try:
        # On Windows, we need to close the handle before docx2pdf can write to it
        with NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        logging.info(f"Converting {os.path.basename(file_path)} to PDF...")
        convert(file_path, temp_pdf_path)
        logging.info(f"Successfully converted to {temp_pdf_path}")
        return temp_pdf_path
    except Exception as e:
        logging.error(f"Conversion failed for {file_path}: {e}")
        # Clean up temp file if it was created but conversion failed
        if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
            try: os.remove(temp_pdf_path)
            except: pass
        return None

# Fucntion to apply watermark
def apply_watermark(pdf_path, doc_type):
    watermark_file = CONFIG['document_types'][doc_type]['watermark']
    if watermark_file == 'special':
        return apply_special_watermark(pdf_path)
    
    watermark_path = os.path.join(CONFIG['watermark_dir'], watermark_file)
    try:
        with open(pdf_path, 'rb') as pdf_file, open(watermark_path, 'rb') as wm_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            wm_reader = PyPDF2.PdfReader(wm_file)
            wm_page = wm_reader.pages[0]

            writer = PyPDF2.PdfWriter()
            for page in pdf_reader.pages:
                # Merge watermark on top of the document page
                page.merge_page(wm_page)
                writer.add_page(page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Watermarked {os.path.basename(pdf_path)} for {doc_type}")
                return output.name
    except Exception as e:
        logging.error(f"Watermark failed for {pdf_path}: {e}")
        return pdf_path

# For special watermark logic
def apply_special_watermark(pdf_path):
    wm_deckblatt_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Deckblatt.pdf')
    wm_allgemein_path = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Allgemein.pdf')
    try:
        with open(pdf_path, 'rb') as pdf_file, \
             open(wm_deckblatt_path, 'rb') as wm_d_file, \
             open(wm_allgemein_path, 'rb') as wm_a_file:
            
            reader = PyPDF2.PdfReader(pdf_file)
            writer = PyPDF2.PdfWriter()
            
            wm_deckblatt_page = PyPDF2.PdfReader(wm_d_file).pages[0]
            wm_allgemein_page = PyPDF2.PdfReader(wm_a_file).pages[0]

            for i, page in enumerate(reader.pages):
                if i == 0:
                    # Page 1: Deckblatt
                    page.merge_page(wm_deckblatt_page)
                else:
                    # Pages 2+: Allgemein
                    page.merge_page(wm_allgemein_page)
                writer.add_page(page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Special watermark (JA) applied to {os.path.basename(pdf_path)}")
                return output.name
    except Exception as e:
        logging.error(f"Special watermark failed: {e}")
        return pdf_path

# fucntion to merge all pdf in proper order
def merge_pdfs(processed_files):
    merger = PyPDF2.PdfMerger()
    for doc_type in CONFIG['merge_order']:
        if doc_type in processed_files:
            merger.append(processed_files[doc_type])
            logging.info(f"Added {doc_type} to merge")
    output_path = os.path.join(CONFIG['output_dir'], 'final_output.pdf')
    
    # Ensure handle is closed after writing
    try:
        with open(output_path, 'wb') as output:
            merger.write(output)
        logging.info(f"Merged PDF saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write final output: {e}")
        return None
    return output_path

def validate_environment():
    """Ensure required directories exist and log environment info."""
    logging.info(f"--- Environment Information ---")
    logging.info(f"Base Directory: {BASE_DIR}")
    logging.info(f"Running as EXE: {getattr(sys, 'frozen', False)}")
    
    # Ensure output directory exists
    if not os.path.exists(CONFIG['output_dir']):
        logging.info(f"Creating output directory: {CONFIG['output_dir']}")
        os.makedirs(CONFIG['output_dir'], exist_ok=True)
        
    # Check input directory
    if not os.path.exists(CONFIG['input_dir']):
        logging.error(f"CRITICAL: Input directory not found: {CONFIG['input_dir']}")
        print(f"\nERROR: Input directory not found!\nPlease make sure there is an 'input' folder containing 'Daten Franklin' at: {CONFIG['input_dir']}")
        return False
        
    # Check watermark directory
    if not os.path.exists(CONFIG['watermark_dir']):
        logging.error(f"CRITICAL: Watermark directory not found: {CONFIG['watermark_dir']}")
        print(f"\nERROR: Watermark directory not found!\nPlease make sure the 'watermarks' folder exists at: {CONFIG['watermark_dir']}")
        return False
        
    return True

if __name__ == "__main__":
    if not validate_environment():
        safe_pause("\nPress Enter to exit...")
        sys.exit(1)
        
    found_files = discover_files(CONFIG['input_dir'])
    
    if not found_files:
        logging.warning("No files found to process.")
        print("\nNo matching files found in the input directory.")
        safe_pause("Press Enter to exit...")
        sys.exit(0)
    
    # Process files type by type
    processed_files = {}
    for dt in CONFIG['merge_order']:
        if dt not in found_files:
            continue
            
        # Convert and collect all PDFs for this type
        type_pdfs = []
        for p in found_files[dt]:
            pdf_path = convert_to_pdf(p)
            if pdf_path:
                type_pdfs.append(pdf_path)
        
        if not type_pdfs:
            continue
            
        # If multiple files for this type, merge them first
        if len(type_pdfs) > 1:
            merger = PyPDF2.PdfMerger()
            for pdf in type_pdfs:
                merger.append(pdf)
            with NamedTemporaryFile(suffix='.pdf', delete=False) as temp_merged:
                merger.write(temp_merged)
                section_pdf = temp_merged.name
            logging.info(f"Merged {len(type_pdfs)} files for {dt}")
        else:
            section_pdf = type_pdfs[0]
            
        # Watermark the entire section
        watermarked = apply_watermark(section_pdf, dt)
        if watermarked:
            processed_files[dt] = watermarked
            
    final_pdf = merge_pdfs(processed_files)
    if final_pdf:
        print(f"\nSuccessfully created: {final_pdf}")
    else:
        print("\nFailed to create final PDF.")
    safe_pause("\nProcessing complete. Press Enter to exit...")
