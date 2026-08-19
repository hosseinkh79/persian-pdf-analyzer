import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.db import get_db
from app.models import DocumentStatus
from app.services.pdf_analyzer import analysis_service

router = APIRouter(prefix="/documents", tags=["documents"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        content = await file.read()
        file_size = len(content)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save file: {str(e)}")
    
    try:
        document = crud.create_document(db=db, filename=file.filename, file_path=file_path, file_size=file_size)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save document metadata: {str(e)}")
    
    return schemas.UploadResponse(id=document.id, filename=document.filename, status=document.status, message="File uploaded successfully")

@router.post("/{document_id}/analyze", response_model=schemas.AnalysisResponse)
def analyze_document(document_id: UUID, model: Optional[str] = None, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    if document.status == DocumentStatus.DONE.value or document.status == DocumentStatus.DONE:
        return schemas.AnalysisResponse(id=document.id, filename=document.filename, status=document.status, extracted_data=document.extracted_data)
    
    try:
        result = analysis_service.analyze_document(db=db, document_id=str(document_id), model=model)
        return schemas.AnalysisResponse(id=result["id"], filename=result["filename"], status=result["status"], extracted_data=result["extracted_data"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PDF file not found: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        crud.update_document_status(db=db, document_id=document_id, status=DocumentStatus.ERROR, error_message=error_msg)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Analysis failed: {error_msg}")

@router.get("/", response_model=list[schemas.DocumentListItem])
async def get_all_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_all_documents(db, skip=skip, limit=limit)

@router.get("/{document_id}", response_model=schemas.DocumentDetail)
async def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document

@router.delete("/{document_id}", response_model=schemas.DeleteResponse)
async def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")
            
    crud.delete_document(db, document_id)
    return schemas.DeleteResponse(message="Document deleted successfully", id=document_id)