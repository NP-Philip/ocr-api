# ============================================================
#  One-Image-At-a-Time OCR API (Fast & Memory-Safe for Render)
# ============================================================

from fastapi import FastAPI, UploadFile, File, Form
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import tempfile, os, gc

app = FastAPI(title="Sequential OCR API (Render Free Tier)")

DPI = 200  # accuracy sweet spot

@app.post("/ocr")
async def ocr_file(file: UploadFile = File(...), lang: str = Form("eng")):
    """Memory-safe OCR: process one page at a time and immediately free it."""

    # Save upload to disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            tmp.write(chunk)
        tmp_path = tmp.name

    texts = []

    try:
        if file.filename.lower().endswith(".pdf"):
            reader = PdfReader(tmp_path)
            num_pages = len(reader.pages)
            print(f"📄 Processing {num_pages} pages sequentially...")

            for i in range(num_pages):
                # Convert one page at a time to image
                images = convert_from_path(
                    tmp_path, dpi=DPI, first_page=i + 1, last_page=i + 1
                )

                # Always only one image
                img = images[0].convert("L")

                # OCR and free memory
                text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
                texts.append(f"\n--- Page {i + 1} ---\n{text}")

                del img, images
                gc.collect()

        else:
            # Single image input
            img = Image.open(tmp_path).convert("L")
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
            texts.append(text)
            del img
            gc.collect()

        return {"text": "".join(texts)}

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
