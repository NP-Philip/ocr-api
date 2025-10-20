# ============================================================
#  Memory-Optimized OCR API using FastAPI, pdf2image & Tesseract
# ============================================================

# FastAPI: framework for building web APIs
from fastapi import FastAPI, UploadFile, File, Form

# pdf2image: converts PDF pages to images (Tesseract needs images)
from pdf2image import convert_from_path

# PyPDF2: lightweight PDF reader, used to count pages
from PyPDF2 import PdfReader

# PIL (Pillow): Python Imaging Library for image processing
from PIL import Image

# pytesseract: Python wrapper for the Tesseract OCR engine
import pytesseract

# tempfile: allows us to store uploaded files temporarily on disk
# os: for file cleanup
import tempfile, os


# ------------------------------------------------------------
# Create FastAPI app
# ------------------------------------------------------------
app = FastAPI(title="Optimized OCR API")


# ------------------------------------------------------------
# Define OCR endpoint (POST /ocr)
# ------------------------------------------------------------
@app.post("/ocr")
async def ocr_file(
    file: UploadFile = File(...),   # The uploaded file (PDF or image)
    lang: str = Form("eng")         # OCR language, default English ("eng")
):
    """
    Endpoint that performs OCR (Optical Character Recognition)
    on uploaded PDF or image files using Tesseract.
    Optimized for memory efficiency — suitable for low-RAM environments like Render.
    """

    # -------------------------------
    # Step 1: Save uploaded file to disk (not in memory)
    # -------------------------------
    # We avoid reading the whole file into RAM by writing it in chunks to a temp file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            tmp.write(chunk)
        tmp_path = tmp.name  # path to the saved temporary file

    texts = []  # will collect extracted text from each page

    try:
        # -------------------------------
        # Step 2: Handle PDFs (multi-page)
        # -------------------------------
        if file.filename.lower().endswith(".pdf"):
            # Use PyPDF2 to count how many pages are in the PDF
            reader = PdfReader(tmp_path)

            # Process each page one at a time to minimize memory use
            for i in range(len(reader.pages)):
                # Convert only one page to an image at a time
                # DPI lowered to 200 for smaller memory footprint (adjustable)
                images = convert_from_path(
                    tmp_path, dpi=200, first_page=i + 1, last_page=i + 1
                )

                # Extract text from the page using Tesseract
                text = pytesseract.image_to_string(images[0], lang=lang)

                # Append page text with a clear label
                texts.append(f"\n--- Page {i + 1} ---\n{text}")

                # Explicitly free memory from the image object
                del images

        # -------------------------------
        # Step 3: Handle images directly
        # -------------------------------
        else:
            # Open image file from disk, convert to RGB for consistency
            img = Image.open(tmp_path).convert("RGB")

            # Extract text via Tesseract
            text = pytesseract.image_to_string(img, lang=lang)
            texts.append(text)

        # -------------------------------
        # Step 4: Combine and return result
        # -------------------------------
        # Joining text list avoids inefficient string concatenation
        return {"text": "".join(texts)}

    finally:
        # -------------------------------
        # Step 5: Clean up temp file
        # -------------------------------
        os.remove(tmp_path)
