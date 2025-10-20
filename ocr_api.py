# ============================================================
#  Fast OCR API for Render (Free Plan)
#  - Parallel OCR for PDFs
#  - Grayscale conversion (faster)
#  - Keeps 200 DPI for accuracy
# ============================================================

from fastapi import FastAPI, UploadFile, File, Form
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import tempfile
import os
import gc
from concurrent.futures import ThreadPoolExecutor


# ------------------------------------------------------------
# Create FastAPI app
# ------------------------------------------------------------
app = FastAPI(title="Fast OCR API (Render Free Tier)")

# Default settings
DPI = 200  # accuracy sweet spot


# ------------------------------------------------------------
# OCR helper for one PDF page
# ------------------------------------------------------------
def ocr_page(tmp_path: str, page_num: int, lang: str):
    """Convert one page of PDF to image and run Tesseract OCR."""
    try:
        # Convert one page at a time
        images = convert_from_path(
            tmp_path, dpi=DPI, first_page=page_num, last_page=page_num
        )

        # Convert to grayscale for speed
        img = images[0].convert("L")

        # OCR text extraction
        text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")

        # Clean up explicitly
        del images, img
        gc.collect()

        return f"\n--- Page {page_num} ---\n{text}"

    except Exception as e:
        return f"\n--- Page {page_num} ---\n[Error processing page: {e}]"


# ------------------------------------------------------------
# POST /ocr endpoint
# ------------------------------------------------------------
@app.post("/ocr")
async def ocr_file(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
):
    """
    Perform OCR (Optical Character Recognition) on uploaded PDF or image files.
    Designed for the free Render plan (single-core, limited memory) but optimized for speed.
    """

    # Step 1: Save upload to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            tmp.write(chunk)
        tmp_path = tmp.name

    texts = []

    try:
        # Step 2: Handle PDF (multi-page)
        if file.filename.lower().endswith(".pdf"):
            reader = PdfReader(tmp_path)
            num_pages = len(reader.pages)
            print(f"📄 Processing {num_pages} pages...")

            # Use all available CPU threads automatically
            with ThreadPoolExecutor() as executor:
                results = executor.map(
                    lambda i: ocr_page(tmp_path, i + 1, lang),
                    range(num_pages),
                )
                texts = list(results)

        # Step 3: Handle images
        else:
            img = Image.open(tmp_path).convert("L")
            text = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
            texts.append(text)
            del img
            gc.collect()

        # Step 4: Combine text and return
        result_text = "".join(texts)
        return {"text": result_text}

    finally:
        # Step 5: Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
