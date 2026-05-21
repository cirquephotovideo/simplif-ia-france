"""OCR via Tesseract (français) avec fallback PDF."""
from io import BytesIO
import pytesseract
from PIL import Image
import pypdf


def ocr_image(data: bytes) -> str:
    img = Image.open(BytesIO(data))
    return pytesseract.image_to_string(img, lang="fra")


def extract_pdf_text(data: bytes) -> str:
    reader = pypdf.PdfReader(BytesIO(data))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text(data: bytes, mime: str) -> str:
    if mime in ("application/pdf",):
        text = extract_pdf_text(data)
        if text.strip():
            return text
        # PDF scanné → OCR page par page n'est pas ici; en MVP on retourne vide
        return ""
    if mime.startswith("image/"):
        return ocr_image(data)
    if mime.startswith("text/"):
        return data.decode("utf-8", errors="replace")
    return ""
