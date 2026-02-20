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
        return os.path.dirname(sys.executable)
    # If running as a script (~/script/document_processor.py)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_path()

CONFIG = {
    'input_dir': os.path.join(BASE_DIR, 'input', 'Daten Franklin'),
    'output_dir': os.path.join(BASE_DIR, 'output'),
    'watermark_dir': os.path.join(BASE_DIR, 'watermarks'),
    # ... document_types dict with updated prefixes based on real files
    'document_types': {
        'anschreiben': {'prefixes': ['BaM', 'Übersendung'], 'watermark': 'Wasserzeichen Anschreiben.pdf', 'format': 'docx'},
        'jahresabschluss': {'prefixes': ['JA ', 'Jahresabschluss', 'Offenlegung'], 'watermark': 'special', 'format': 'pdf'},
        'kst': {'prefixes': ['KSt Erklärung'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},
        'ust': {'prefixes': ['USt Erklärung'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},
        'est': {'prefixes': ['ESt'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},
        'deckblatt': {'prefixes': ['Deckblatt'], 'watermark': 'Wasserzeichen Deckblatt.pdf', 'format': 'docx'}
    },
    'merge_order': ['anschreiben', 'deckblatt', 'kst', 'ust', 'est', 'jahresabschluss']
}

# File discovery function
def discover_files(input_dir):
    logging.info(f"Searching for files in: {os.path.abspath(input_dir)}")
    files_by_type = {t: [] for t in CONFIG['document_types']}
    
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        return {}

    # Sort files to ensure stable discovery (e.g. JA 2024 comes before JA 2024_12)
    files = sorted(glob.glob(os.path.join(input_dir, '*')))
    for file_path in files:
        filename = os.path.basename(file_path)
        filename_lower = filename.lower()
        for doc_type, info in CONFIG['document_types'].items():
            prefixes = info.get('prefixes', [])
            if any(prefix.lower() in filename_lower for prefix in prefixes):
                files_by_type[doc_type].append(file_path)
                logging.info(f"Matched {doc_type}: {filename}")
                    
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
    watermark_path = os.path.join(CONFIG['watermark_dir'], CONFIG['document_types'][doc_type]['watermark'])
    if doc_type == 'jahresabschluss':
        return apply_special_watermark(pdf_path)  # Handle later
    try:
        with open(pdf_path, 'rb') as pdf_file, open(watermark_path, 'rb') as wm_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            wm_reader = PyPDF2.PdfReader(wm_file)
            wm_page = wm_reader.pages[0]  # Assume single-page watermark

            writer = PyPDF2.PdfWriter()
            for page in pdf_reader.pages:
                # To put watermark UNDER, we merge the document page ON TOP of a copy of the watermark page
                # This ensures the document text stays on top and dimensions are preserved
                new_page = PyPDF2.PageObject.create_blank_page(
                    width=page.mediabox.width, 
                    height=page.mediabox.height
                )
                new_page.merge_page(wm_page) # Watermark first
                new_page.merge_page(page)    # Document content on top
                writer.add_page(new_page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Watermarked {os.path.basename(pdf_path)} for {doc_type}")
                return output.name
    except Exception as e:
        logging.error(f"Watermark failed for {pdf_path}: {e}")
        return pdf_path  # Return original on failure

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

            # Page 1: Deckblatt
            if len(reader.pages) > 0:
                page1 = reader.pages[0]
                new_page1 = PyPDF2.PageObject.create_blank_page(width=page1.mediabox.width, height=page1.mediabox.height)
                new_page1.merge_page(wm_deckblatt_page)
                new_page1.merge_page(page1)
                writer.add_page(new_page1)

            # Pages 2+: Allgemein
            for page in reader.pages[1:]:
                new_page = PyPDF2.PageObject.create_blank_page(width=page.mediabox.width, height=page.mediabox.height)
                new_page.merge_page(wm_allgemein_page)
                new_page.merge_page(page)
                writer.add_page(new_page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Special watermark applied to {os.path.basename(pdf_path)}")
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
    with open(output_path, 'wb') as output:
        merger.write(output)
    logging.info(f"Merged PDF saved to {output_path}")
    return output_path

if __name__ == "__main__":
    found_files = discover_files(CONFIG['input_dir'])
    
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
            
    merge_pdfs(processed_files)