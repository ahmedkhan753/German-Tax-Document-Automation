import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from io import BytesIO
import os

# Copy logic from document_processor.py for verification
ORANGE_BAR_COLOR = HexColor('#f27f1c') 
FOOTER_HEIGHT = 20
LOGO_TEXT = ""

def create_footer_watermark(width, height):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFillColor(ORANGE_BAR_COLOR)
    can.rect(0, 0, width, FOOTER_HEIGHT, fill=1, stroke=0)
    center_x = width / 2
    center_y = FOOTER_HEIGHT / 2
    can.setStrokeColor(HexColor('#ffffff'))
    can.setLineWidth(1)
    can.setFillColor(HexColor('#ffffff'))
    can.setFont("Helvetica-Bold", FOOTER_HEIGHT * 0.6)
    can.drawCentredString(center_x, center_y - (FOOTER_HEIGHT * 0.2), LOGO_TEXT)
    can.save()
    packet.seek(0)
    return PyPDF2.PdfReader(packet).pages[0]

def test_generation():
    # Create a dummy 1-page PDF
    dummy_packet = BytesIO()
    c = canvas.Canvas(dummy_packet, pagesize=(595, 842)) # A4
    c.drawString(100, 750, "Test Document Content")
    c.save()
    dummy_packet.seek(0)
    
    reader = PyPDF2.PdfReader(dummy_packet)
    writer = PyPDF2.PdfWriter()
    
    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    
    footer = create_footer_watermark(width, height)
    page.merge_page(footer)
    writer.add_page(page)
    
    output_path = "test_footer_output.pdf"
    with open(output_path, "wb") as f:
        writer.write(f)
    
    print(f"Verification PDF created at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    test_generation()
