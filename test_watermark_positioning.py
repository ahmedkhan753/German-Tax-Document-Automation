import PyPDF2
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import sys

# Mocking the scaling logic from the script
def apply_watermark_logic(target_page, wm_page):
    target_width = float(target_page.mediabox.width)
    target_height = float(target_page.mediabox.height)
    
    wm_width = float(wm_page.mediabox.width)
    wm_height = float(wm_page.mediabox.height)
    
    scale = min(target_width / wm_width, target_height / wm_height)
    off_x = (target_width - (wm_width * scale)) / 2
    off_y = (target_height - (wm_height * scale)) / 2
    
    trans = PyPDF2.Transformation().scale(scale).translate(off_x, off_y)
    # 1. Create a blank page for the watermark overlay
    wm_overlay = PyPDF2.PageObject.create_blank_page(width=target_width, height=target_height)
    # 2. Merge the watermark onto the overlay
    wm_overlay.merge_page(wm_page)
    # 3. Transform the overlay
    wm_overlay.add_transformation(trans)
    
    # 4. Merge overlay and target content
    new_page = PyPDF2.PageObject.create_blank_page(width=target_width, height=target_height)
    new_page.merge_page(wm_overlay)
    new_page.merge_page(target_page)
    return new_page

def create_dummy_pdf(width, height, text):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.drawString(width/2 - 50, height/2, text)
    can.save()
    packet.seek(0)
    return PyPDF2.PdfReader(packet).pages[0]

def create_watermark_pdf(width, height, color_name):
    # Just a colored box to represent watermark
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setStrokeColorRGB(0.5, 0.5, 0.5)
    can.rect(10, 10, width-20, height-20, stroke=1, fill=0) # Border
    can.drawString(20, height-40, f"Watermark: {color_name}")
    can.save()
    packet.seek(0)
    return PyPDF2.PdfReader(packet).pages[0]

def run_test():
    # 1. A4 Portrait Page (595x842)
    # 2. Letter Landscape Page (792x612)
    # 3. Small square page (400x400)
    
    pages = [
        (595, 842, "A4 Portrait"),
        (792, 612, "Letter Landscape"),
        (400, 400, "Square")
    ]
    
    # Common watermark (Let's say it's A4 size)
    wm_page = create_watermark_pdf(595, 842, "Standard A4 WM")
    
    writer = PyPDF2.PdfWriter()
    
    for w, h, name in pages:
        print(f"Testing {name}...")
        target = create_dummy_pdf(w, h, f"Target: {name}")
        output_page = apply_watermark_logic(target, wm_page)
        writer.add_page(output_page)
    
    output_path = "test_watermark_positioning.pdf"
    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"\nTest PDF created at: {output_path}")

if __name__ == "__main__":
    run_test()
