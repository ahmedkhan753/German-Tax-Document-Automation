from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tempfile import NamedTemporaryFile
from script import document_processor
import PyPDF2

with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
    path = tmp.name
c = canvas.Canvas(path, pagesize=letter)
c.drawString(100,700,"Cover Letter")
c.save()

print("input", path)
pdf = document_processor.convert_to_pdf(path)
print("after conv", pdf)
water = document_processor.apply_watermark(pdf, 'anschreiben')
print("watermarked", water)
final = document_processor.merge_pdfs({'anschreiben': water})
print("final", final)
print("pages", len(PyPDF2.PdfReader(final).pages))
# push marker 3
