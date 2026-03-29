import os

def extract_text_from_file(filepath: str) -> str:
    ext = filepath.rsplit('.', 1)[-1].lower()
    
    if ext == 'pdf':
        return extract_from_pdf(filepath)
    elif ext in ('png', 'jpg', 'jpeg'):
        return extract_from_image(filepath)
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

def extract_from_pdf(filepath: str) -> str:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if text.strip():
            return text
        # If no text found, try OCR on each page
        return extract_pdf_with_ocr(filepath)
    except ImportError:
        return extract_pdf_with_ocr(filepath)
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_pdf_with_ocr(filepath: str) -> str:
    try:
        import fitz
        import pytesseract
        from PIL import Image
        import io
        
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img) + "\n"
        doc.close()
        return text
    except Exception as e:
        return f"OCR extraction failed: {str(e)}"

def extract_from_image(filepath: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(filepath)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"Image OCR failed: {str(e)}"
