import os
import sys

# Add the script directory to path
script_dir = os.path.abspath(os.path.join(os.getcwd(), 'script'))
sys.path.append(script_dir)

from document_processor import CONFIG, discover_files
import PyPDF2

with open('diagnostic_results.txt', 'w', encoding='utf-8') as out:
    def log(msg):
        print(msg)
        out.write(msg + '\n')

    log("--- DIAGNOSTIC START ---")
    input_dir = CONFIG['input_dir']
    log(f"Input Dir: {input_dir}")

    found = discover_files(input_dir)

    for dt in CONFIG['merge_order']:
        if dt in found:
            log(f"TYPE: {dt}")
            for f in found[dt]:
                pages = "N/A"
                if f.lower().endswith('.pdf'):
                    try:
                        with open(f, 'rb') as fh:
                            reader = PyPDF2.PdfReader(fh)
                            pages = len(reader.pages)
                    except:
                        pass
                log(f"  File: {os.path.basename(f)} (Pages: {pages})")
        else:
            log(f"TYPE: {dt} (NOT FOUND)")

    log("--- DIAGNOSTIC END ---")
