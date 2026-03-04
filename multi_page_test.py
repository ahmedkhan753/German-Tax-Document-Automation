from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tempfile import NamedTemporaryFile
from script import document_processor
import PyPDF2

# create multi-page pdf
tmp = NamedTemporaryFile(suffix='.pdf', delete=False)
path = tmp.name
tmp.close()
c = canvas.Canvas(path,pagesize=letter)
# page1
c.drawString(100,700,"Cover Letter")
c.showPage()
# page2 - large white box
c.setFillColorRGB(1,1,1)
c.rect(0,0,letter[0],letter[1],fill=1,stroke=0)
c.setFillColorRGB(0,0,0)
c.drawString(100,700,"Second page content")
c.showPage()
# page3 normal
c.drawString(100,700,"Third page")
c.save()

print('input file',path)
pdf = document_processor.convert_to_pdf(path)
print('after conv',pdf)
water=document_processor.apply_watermark(pdf,'anschreiben')
print('watermarked',water)
final=document_processor.merge_pdfs({'anschreiben':water})
print('final',final)
print('pages',len(PyPDF2.PdfReader(final).pages))
