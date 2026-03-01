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
    pdf = make_pdf("Cover Letter")
    # apply watermark for 'anschreiben' type (should skip first page)
    out = document_processor.apply_watermark(pdf, 'anschreiben')
    assert out is not None
    # confirm that the returned pdf still contains the "Cover Letter" text
    text = extract_first_page_text(out)
    assert "Cover Letter" in text
    # original pdf should also still contain text (sanity)
    assert "Cover Letter" in extract_first_page_text(pdf)


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__)])
