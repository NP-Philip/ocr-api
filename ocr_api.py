# Import the necessary modules from FastAPI and other libraries
# FastAPI: framework for creating web APIs
# UploadFile, File, Form: handle uploaded files and form data
from fastapi import FastAPI, UploadFile, File, Form

# pdf2image: converts PDF pages to images (so Tesseract can read them)
from pdf2image import convert_from_bytes

# pytesseract: Python wrapper for the Tesseract OCR engine
# io: used to handle binary streams (in-memory files)
import pytesseract, io

# PIL (Pillow): Python Imaging Library to work with image files
from PIL import Image


# Create a FastAPI application instance.
# This is your main API "app" that will serve routes (endpoints).
app = FastAPI(title="OCR API")


# Define a POST endpoint at the path "/ocr".
# This means clients (like your GPT action) will send an HTTP POST request here
# with a file to process.
@app.post("/ocr")
async def ocr_file(
    file: UploadFile = File(...),  # The uploaded file (PDF or image)
    lang: str = Form("eng")        # Optional form field to set OCR language (default: English)
):
    # Read the entire uploaded file into memory as bytes.
    # `await` is used because FastAPI supports asynchronous I/O (non-blocking operations).
    data = await file.read()

    # --- PDF handling ---
    # If the file name ends with ".pdf", it's treated as a PDF file.
    # Convert it to a list of image objects (one image per page).
    # The `dpi=300` means good OCR quality; `poppler_path` is where Poppler is installed.
    if file.filename.lower().endswith(".pdf"):
        images = convert_from_bytes(data, dpi=300, poppler_path=r"C:\poppler\Library\bin")

    # --- Image handling ---
    # If it's not a PDF (e.g., PNG, JPG, etc.), open it directly as an image.
    # `io.BytesIO(data)` lets Pillow read from memory (not a disk file).
    else:
        images = [Image.open(io.BytesIO(data)).convert("RGB")]

    # Initialize a variable to store OCR text from all pages.
    all_text = ""

    # Loop through each image (page-by-page for PDFs).
    # enumerate(..., start=1) gives us both the page number and the image object.
    for i, img in enumerate(images, start=1):
        # Use Tesseract to extract text from the image.
        # `lang` controls which language model Tesseract uses (e.g., "eng", "swe").
        text = pytesseract.image_to_string(img, lang=lang)

        # Add the extracted text to the `all_text` string.
        # Each page's content is labeled with its page number.
        all_text += f"\n--- Page {i} ---\n{text}"

    # Return the OCR result as a JSON response.
    # FastAPI automatically converts this Python dict into JSON.
    return {"text": all_text}
