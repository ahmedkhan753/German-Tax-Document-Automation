import os
import glob
import logging
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG = {
    'input_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'input', 'Daten Franklin'),
    'output_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output'),
    'watermark_dir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'watermarks'),
    # ... document_types dict with updated prefixes based on real files
    'document_types': {
        'anschreiben': {'prefixes': ['BaM', 'Übersendung'], 'watermark': 'Wasserzeichen Anschreiben.pdf', 'format': 'docx'},
        'jahresabschluss': {'prefixes': ['JA', 'Jahresabschluss', 'Offenlegung'], 'watermark': 'special', 'format': 'pdf'},
        'kst': {'prefixes': ['KSt'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},
        'ust': {'prefixes': ['USt'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},
        'est': {'prefixes': ['ESt'], 'watermark': 'Wasserzeichen Allgemein.pdf', 'format': 'pdf'},  # if appears later
        'deckblatt': {'prefixes': ['Deckblatt'], 'watermark': 'Wasserzeichen Deckblatt.pdf', 'format': 'docx'}  # may be missing
    },
    'merge_order': ['anschreiben', 'deckblatt', 'kst', 'ust', 'est', 'jahresabschluss']  # logical order; confirm with client
}

# File discovery function
def discover_files(input_dir):
    logging.info(f"Searching for files in: {os.path.abspath(input_dir)}")
    files_by_type = {t: None for t in CONFIG['document_types']}
    
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        return {}

    for file_path in glob.glob(os.path.join(input_dir, '*')):
        filename = os.path.basename(file_path)
        filename_lower = filename.lower()
        for doc_type, info in CONFIG['document_types'].items():
            prefixes = info.get('prefixes', [])
            if any(prefix.lower() in filename_lower for prefix in prefixes):
                if files_by_type[doc_type] is None:  # take first match
                    files_by_type[doc_type] = file_path
                    logging.info(f"Matched {doc_type}: {filename}")
                else:
                    logging.debug(f"Skipping additional match for {doc_type}: {filename}")
                    
    found = {k: v for k, v in files_by_type.items() if v is not None}
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
                page.merge_page(wm_page)  # Overlay
                writer.add_page(page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                logging.info(f"Watermarked {pdf_path} as {output.name}")
                return output.name
    except Exception as e:
        logging.error(f"Watermark failed for {pdf_path}: {e}")
        return pdf_path  # Return original on failure

# For special watermark logic
def apply_special_watermark(pdf_path):
    wm_deckblatt = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Deckblatt.pdf')
    wm_allgemein = os.path.join(CONFIG['watermark_dir'], 'Wasserzeichen Allgemein.pdf')
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            writer = PyPDF2.PdfWriter()

            # Page 1: Deckblatt
            if len(reader.pages) > 0:
                page1 = reader.pages[0]
                with open(wm_deckblatt, 'rb') as wm:
                    wm_page = PyPDF2.PdfReader(wm).pages[0]
                    page1.merge_page(wm_page)
                writer.add_page(page1)

            # Pages 2+: Allgemein
            for page in reader.pages[1:]:
                with open(wm_allgemein, 'rb') as wm:
                    wm_page = PyPDF2.PdfReader(wm).pages[0]
                    page.merge_page(wm_page)
                writer.add_page(page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
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
    
    converted_files = {}
    for dt, p in found_files.items():
        pdf_path = convert_to_pdf(p)
        if pdf_path:
            converted_files[dt] = pdf_path
            
    processed_files = {dt: apply_watermark(p, dt) for dt, p in converted_files.items()}
    merge_pdfs(processed_files)
    # Cleanup temps (add os.remove for each temp path if tracked)