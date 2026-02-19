import os
import glob
import logging
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration (make this a dict for easy changes)
CONFIG = {
    'input_dir': 'Input/',
    'output_dir': 'Output/',
    'watermark_dir': 'Watermarks/',
    'document_types': {
        'anschreiben': {'prefix': 'BaM', 'watermark': 'WZ_Anschreiben.pdf', 'format': 'docx'},
        'deckblatt': {'prefix': 'Deckblatt', 'watermark': 'WZ_Deckblatt.pdf', 'format': 'docx'},  # Adjust prefix if needed
        'kst': {'prefix': 'KSt', 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},
        'ust': {'prefix': 'USt', 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},
        'est': {'prefix': 'ESt', 'watermark': 'WZ_Allgemein.pdf', 'format': 'pdf'},  # Or 'USt' if typo in examples
        'jahresabschluss': {'prefix': 'JA', 'watermark': 'special', 'format': 'pdf'}  # Special handling
    },
    'merge_order': ['anschreiben', 'deckblatt', 'kst', 'ust', 'est', 'jahresabschluss']
}

# File discovery function
def discover_files(input_dir):
    files_by_type = {}
    for file_path in glob.glob(os.path.join(input_dir, '*')):
        filename = os.path.basename(file_path).lower()
        for doc_type, info in CONFIG['document_types'].items():
            if filename.startswith(info['prefix'].lower()):
                files_by_type[doc_type] = file_path
                logging.info(f"Found {doc_type}: {file_path}")
                break  # Assume one file per type
    return files_by_type