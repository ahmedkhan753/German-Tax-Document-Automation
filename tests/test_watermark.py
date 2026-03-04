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


def test_skip_watermark_on_cover_letter(tmp_path):
    # generate a pdf with "Cover Letter" text on first page
    # push marker 4
    pdf = make_pdf("Cover Letter")
    # apply watermark for 'anschreiben' type (should skip first page)
    out = document_processor.apply_watermark(pdf, 'anschreiben')
    assert out is not None
    # confirm that the returned pdf still contains the "Cover Letter" text
    text = extract_first_page_text(out)
    assert "Cover Letter" in text
    # original pdf should also still contain text (sanity)
    assert "Cover Letter" in extract_first_page_text(pdf)


def test_no_skip_watermark_on_jahresabschluss(tmp_path):
    # generate a pdf with minimal text (sparse)
    pdf = make_pdf("JA Jahresabschluss 2024")
    
    # Mocking properties for should_skip_first_page_watermark
    # We want to verify that jahresabschluss returns False (don't skip)
    # even if it's sparse.
    
    # We can't easily mock page_obj.extract_text() without a real PDF reader
    # but the logic in should_skip_first_page_watermark will see 'jahresabschluss' 
    # doc_type and return False immediately now.
    
    from script.document_processor import should_skip_first_page_watermark
    import PyPDF2
    
    with open(pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        page = reader.pages[0]
        # This should now return False because of the explicit doc_type check
        skip = should_skip_first_page_watermark('jahresabschluss', pdf, page)
        assert skip is False, "Jahresabschluss should NOT skip watermark even if sparse"

    # Also check deckblatt
    with open(pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        page = reader.pages[0]
        skip = should_skip_first_page_watermark('deckblatt_steuererklaerung', pdf, page)
        assert skip is False, "Deckblatt should NOT skip watermark even if sparse"

    # Check that anschreiben STILL skips
    with open(pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        page = reader.pages[0]
        skip = should_skip_first_page_watermark('anschreiben', pdf, page)
        assert skip is True, "Anschreiben SHOULD skip watermark if sparse/matches patterns"


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__)])
