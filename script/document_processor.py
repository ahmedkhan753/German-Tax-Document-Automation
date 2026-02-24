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
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def safe_pause(message="\nPress Enter to continue..."):
    if sys.stdin and sys.stdin.isatty():
        try: input(message)
        except EOFError: pass

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
            'prefixes': ['Deckblatt Steuer', 'Deckblatt Word', '440368', 'Cover', 'Deckblatt Einkommensteuer', 'Deckblatt ESt'], 
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
            'prefixes': ['ESt Erklärung', 'Einkommensteuer'], 
            'exclude': ['Freizeichnungsdokument'],
            'watermark': 'Wasserzeichen Allgemein.pdf', 
            'format': 'pdf'
        },
        'est_freizeichnung': {
            'prefixes': ['ESt Erklärung Freizeichnungsdokument'], 
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
            if any(p.lower() in filename for p in prefixes):
                if not any(e.lower() in filename for e in excludes):
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
        logging.error(f"Conversion failed: {e}")
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

            for i, page in enumerate(pdf_reader.pages):
                w, h = float(page.mediabox.width), float(page.mediabox.height)
                rotation = page.get('/Rotate', 0)
                
                wm_w, wm_h = float(wm_page.mediabox.width), float(wm_page.mediabox.height)
                scale = min(w / wm_w, h / wm_h)
                off_x = (w - (wm_w * scale)) / 2
                off_y = (h - (wm_h * scale)) / 2
                
                trans = PyPDF2.Transformation().scale(scale).translate(off_x, off_y)
                wm_overlay = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                wm_overlay.merge_page(wm_page)
                
                # Handle rotation for the brand overlay
                if rotation != 0:
                    if rotation == 90: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(90).translate(w, 0))
                    elif rotation == 180: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(180).translate(w, h))
                    elif rotation == 270: wm_overlay.add_transformation(PyPDF2.Transformation().rotate(270).translate(0, h))
                
                wm_overlay.add_transformation(trans)
                
                # FOREGROUND MERGE: Content first, then BRAND overlay on top for maximum visibility (Revision 7)
                new_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                new_page.merge_page(page)
                new_page.merge_page(wm_overlay)
                writer.add_page(new_page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
                return output.name
    except Exception as e:
        logging.error(f"Watermarking failed: {e}")
        return pdf_path

def apply_special_watermark(pdf_path):
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
                
                # FOREGROUND MERGE
                new_page = PyPDF2.PageObject.create_blank_page(width=w, height=h)
                new_page.merge_page(page)
                new_page.merge_page(wm_overlay)
                writer.add_page(new_page)

            with NamedTemporaryFile(suffix='.pdf', delete=False) as output:
                writer.write(output)
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
    if not os.path.exists(CONFIG['output_dir']): os.makedirs(CONFIG['output_dir'])
    
    found_files = discover_files(CONFIG['input_dir'])
    if not found_files:
        logging.warning("No files found.")
        sys.exit(0)
    
    processed_files = {}
    for dt in CONFIG['merge_order']:
        if dt not in found_files: continue
            
        type_pdfs = []
        for p in found_files[dt]:
            pdf_path = convert_to_pdf(p)
            if pdf_path: type_pdfs.append(pdf_path)
        
        if not type_pdfs: continue
            
        if len(type_pdfs) > 1:
            merger = PyPDF2.PdfMerger()
            for pdf in type_pdfs: merger.append(pdf)
            with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                merger.write(tmp)
                section_pdf = tmp.name
        else:
            section_pdf = type_pdfs[0]
            
        watermarked = apply_watermark(section_pdf, dt)
        if watermarked: processed_files[dt] = watermarked
            
    final = merge_pdfs(processed_files)
    if final: print(f"\nFinal document created: {final}")
    safe_pause()
