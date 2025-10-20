FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip poppler-utils tesseract-ocr && \
    apt-get clean

# Set working directory
WORKDIR /app

# Copy your code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Render’s dynamic port
ENV PORT=10000
CMD ["bash", "-c", "uvicorn ocr_api:app --host 0.0.0.0 --port $PORT"]
