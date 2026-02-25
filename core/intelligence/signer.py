import fitz # PyMuPDF
import os

async def sign_pdf(pdf_path: str, signature_png_path: str, output_path: str, x: int = 100, y: int = 100):
    """
    Overlays a PNG signature onto the first page of a PDF.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF file not found.")
    if not os.path.exists(signature_png_path):
        raise FileNotFoundError("Signature PNG not found.")
        
    doc = fitz.open(pdf_path)
    page = doc[0] # Sign on first page for now
    
    # Define rectangle where signature will be placed
    # Dimensions (150x50) are arbitrary; in a real app these come from coordinates in the frontend
    rect = fitz.Rect(x, y, x + 150, y + 50)
    
    # Insert image
    page.insert_image(rect, filename=signature_png_path)
    
    doc.save(output_path)
    doc.close()
    
    return True
