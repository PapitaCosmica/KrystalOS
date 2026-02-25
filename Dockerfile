FROM python:3.12-slim-bookworm

WORKDIR /app

# Removed old apt-get update. 
# Re-adding apt-get for tesseract and poppler needed by the intelligence module.
# (Temporarily commented out due to Debian repo network timeout in your Docker Desktop)
# RUN apt-get update && apt-get install -y \
#     tesseract-ocr \
#     poppler-utils \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
