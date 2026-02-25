import datetime
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from core.intelligence.ocr_engine import process_pdf
from core.intelligence.vector_db import store_document_embedding, search_documents
import shutil
import os

router = APIRouter()
UPLOAD_DIR = os.path.join(os.getcwd(), "storage", "documents")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger OCR and Vector Embedding in background (simplified for now)
    # In a real app, use Celery or FastAPI BackgroundTasks
    text = await process_pdf(file_path)
    embedding_id = await store_document_embedding(file.filename, text)
    
    return {
        "status": "success",
        "filename": file.filename,
        "message": "Document processed and embedded successfully.",
        "embedding_id": embedding_id
    }

@router.get("/search")
async def semantic_search(query: str):
    results = await search_documents(query)
    return {"query": query, "results": results}
