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
        'anschreiben': {'prefixes': ['BaM', 'Übersendung'], 'watermark': 'WZ_Anschreiben.pdf', 'format': 'docx'},
        'jahresabschluss': {'prefixes': ['JA', 'Jahresabschluss', 'Offenlegung'], 'watermark': 'special', 'format': 'pdf'},
        'kst': {'prefixes': ['KSt'], 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},
        'ust': {'prefixes': ['USt'], 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},
        'est': {'prefixes': ['ESt'], 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},  # if appears later
        'deckblatt': {'prefixes': ['Deckblatt'], 'watermark': 'WZ_Deckblatt.pdf', 'format': 'docx'}  # may be missing
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
    if not file_path.endswith('.docx'):
        return file_path  # Already PDF
    try:
        with NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            convert(file_path, temp_pdf.name)
            logging.info(f"Converted {file_path} to {temp_pdf.name}")
            return temp_pdf.name
    except Exception as e:
        logging.error(f"Conversion failed for {file_path}: {e}")
        return None  # Skip on error

if __name__ == "__main__":
    found_files = discover_files(CONFIG['input_dir'])
    print(found_files)  # e.g., {'anschreiben': 'Input/BaM_Anschreiben_2024.docx', ...}