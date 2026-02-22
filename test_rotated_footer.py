import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os
import sys

# Add script dir
sys.path.append(os.path.join(os.getcwd(), 'script'))
from document_processor import apply_footer_to_pdf

def create_rotated_pdf(output_path):
    writer = PyPDF2.PdfWriter()
    
    # Page 1: Normal
    p1 = PyPDF2.PageObject.create_blank_page(width=600, height=800)
    writer.add_page(p1)
    
    # Page 2: Rotated 90
    p2 = PyPDF2.PageObject.create_blank_page(width=600, height=800)
    p2.rotate(90)
    writer.add_page(p2)
    
    # Page 3: Landscape (width > height)
    p3 = PyPDF2.PageObject.create_blank_page(width=800, height=600)
    writer.add_page(p3)
    
    with open(output_path, 'wb') as f:
        writer.write(f)

if __name__ == "__main__":
    dummy_in = "rotated_test_in.pdf"
    create_rotated_pdf(dummy_in)
    
    # Run the function
    output_pdf = apply_footer_to_pdf(dummy_in)
    print(f"Rotated test output: {output_pdf}")
    
    # Safe rename
    final_out = "test_rotation_output.pdf"
    import shutil
    try:
        shutil.copy2(output_pdf, final_out)
        print(f"Final test PDF copied to: {os.path.abspath(final_out)}")
    except Exception as e:
        print(f"Error copying output: {e}")

