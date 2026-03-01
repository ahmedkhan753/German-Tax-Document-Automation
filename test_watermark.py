from script import document_processor
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tempfile import NamedTemporaryFile

# create dummy pdf with "Cover Letter" text
with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
    path = tmp.name
c = canvas.Canvas(path, pagesize=letter)
c.drawString(100, 700, "Cover Letter")
c.save()

print("Created test pdf", path)
# call apply_watermark
out = document_processor.apply_watermark(path, 'anschreiben')
print("Output path", out)
