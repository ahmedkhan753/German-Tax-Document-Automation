import PyPDF2
import os

watermarks_dir = r"d:\PROJECTS\German-tax-automation-prod\watermarks"
files = ["Wasserzeichen Allgemein.pdf", "Wasserzeichen Anschreiben.pdf", "Wasserzeichen Deckblatt.pdf"]

print("--- PDF Inspection ---")
for f in files:
    path = os.path.join(watermarks_dir, f)
    if os.path.exists(path):
        try:
            with open(path, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                print(f"FILE: {f}")
                print(f"  Pages: {len(reader.pages)}")
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    print(f"  Page {i+1} text sample: '{text[:50].strip() if text else 'NO TEXT'}'")
        except Exception as e:
            print(f"  Error reading {f}: {e}")
    else:
        print(f"  {f} NOT FOUND")
