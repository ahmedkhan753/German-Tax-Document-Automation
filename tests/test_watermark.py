import os
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tempfile import NamedTemporaryFile
from script import document_processor


def make_pdf(text):
    with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        path = tmp.name
    c = canvas.Canvas(path, pagesize=letter)
    c.drawString(100, 700, text)
    c.save()
    return path


def extract_first_page_text(pdf_path):
    reader = document_processor.PyPDF2.PdfReader(pdf_path)
    return reader.pages[0].extract_text()


def test_no_skip_watermark_on_any_type(tmp_path):
    # generate a pdf with minimal text (sparse) or cover-letter keywords
    pdf = make_pdf("Cover Letter - Very Truly Yours")
    
    from script.document_processor import should_skip_first_page_watermark
    import PyPDF2
    
    # All types should now return False (don't skip)
    test_types = ['anschreiben', 'jahresabschluss', 'deckblatt_steuererklaerung', 'offenlegung']
    
    with open(pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        page = reader.pages[0]
        for doc_type in test_types:
            skip = should_skip_first_page_watermark(doc_type, pdf, page)
            assert skip is False, f"{doc_type} should NOT skip watermark anymore"


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__)])
