import os
import glob
import logging
from docx2pdf import convert
import PyPDF2
from tempfile import NamedTemporaryFile

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG = {
    'input_dir': 'Input/Datens Franklin/',  # or use os.path.join for robustness
    'output_dir': 'Output/',
    'watermark_dir': 'Watermarks/',
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
    files_by_type = {t: None for t in CONFIG['document_types']}
    for file_path in glob.glob(os.path.join(input_dir, '*')):
        filename_lower = os.path.basename(file_path).lower()
        for doc_type, info in CONFIG['document_types'].items():
            if any(prefix.lower() in filename_lower for prefix in info.get('prefixes', [info['prefix']])):
                if files_by_type[doc_type] is None:  # take first match
                    files_by_type[doc_type] = file_path
                    logging.info(f"Matched {doc_type}: {file_path}")
    return {k: v for k, v in files_by_type.items() if v is not None}

if __name__ == "__main__":
    found_files = discover_files(CONFIG['input_dir'])
    print(found_files)  # e.g., {'anschreiben': 'Input/BaM_Anschreiben_2024.docx', ...}