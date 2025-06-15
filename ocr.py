import pytesseract
from PIL import Image

class OCRProcessor:
    def __init__(self, lang='jpn+eng'):
        self.lang = lang

    def extract_text(self, image: Image.Image) -> str:
        try:
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            return f"[OCRエラー]: {e}"
