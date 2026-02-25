import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os

async def process_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF. Uses PyMuPDF for native text.
    Fallback to Tesseract OCR if the page is an image.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")

    doc = fitz.open(file_path)
    full_text = ""
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        
        # If very little text, assume it's a scanned image and run OCR
        if len(text.strip()) < 50:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
            
        full_text += text + "\n"
        
    return full_text
