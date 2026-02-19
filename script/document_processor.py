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