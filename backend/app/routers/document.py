from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import os
import shutil
from datetime import datetime
import json
from typing import Optional

from app.db import get_db
from app import crud, schemas, models
from app.models import DocumentStatus

from app.services.pdf_analyzer import analysis_service


# Create router
router = APIRouter(
    prefix="/documents",
    tags=["documents"]  # For OpenAPI documentation grouping
)

# Upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# ENDPOINT 1: UPLOAD
# ============================================================

@router.post("/upload", response_model=schemas.UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),  # The file from the user
    db: Session = Depends(get_db)  # Database session
):
    """
    Upload a PDF file.

    1. Validate it's a PDF
    2. Save the file to disk
    3. Save metadata to database
    4. Return the document ID
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Create unique filename to prevent overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save file to disk
    try:
        # Read the file content
        content = await file.read()
        file_size = len(content)
        
        # Write to disk
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Save to database
    try:
        document = crud.create_document(
            db=db,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size
        )
    except Exception as e:
        # Clean up file if database save fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document metadata: {str(e)}"
        )
    
    return schemas.UploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
        message="File uploaded successfully"
    )

# ============================================================
# ENDPOINT 2: ANALYZE
# ============================================================
# ANALYZE ENDPOINT - UPDATED WITH REAL SERVICE!
# ============================================================

@router.post("/{document_id}/analyze", response_model=schemas.AnalysisResponse)
async def analyze_document(
    document_id: UUID,
    model: Optional[str] = None,  # Allow overriding the LLM model
    db: Session = Depends(get_db)
):
    """
    Analyze a PDF and extract information using LLM.
    
    Now uses the real analysis service with:
    1. PDF text extraction (pdfplumber/PyPDF2)
    2. LLM API call (OpenAI/Claude/Ollama)
    3. Structured data extraction
    4. Results saved to database
    """
    # Get the document
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if already analyzed
    if document.status == DocumentStatus.DONE:
        # Return existing results
        return schemas.AnalysisResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            extracted_data=document.extracted_data
        )
    
    try:
        # ════════════════════════════════════════════════════════════
        # 🔥 THE MAGIC HAPPENS HERE - REAL ANALYSIS!
        # ════════════════════════════════════════════════════════════
        
        # Use the analysis service to:
        # 1. Extract text from PDF
        # 2. Call LLM API
        # 3. Parse and validate response
        # 4. Save results to database
        
        result = analysis_service.analyze_document(
            db=db,
            document_id=str(document_id),
            model=model
        )
        
        # Return the results
        return schemas.AnalysisResponse(
            id=result["id"],
            filename=result["filename"],
            status=result["status"],
            extracted_data=result["extracted_data"]
        )
        
    except ValueError as e:
        # Handle specific errors (e.g., document not found)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileNotFoundError as e:
        # Handle missing PDF file
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found: {str(e)}"
        )
    except ImportError as e:
        # Handle missing PDF libraries
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing PDF library: {str(e)}. Please install pdfplumber or PyPDF2."
        )
    except Exception as e:
        # Handle any other errors
        error_msg = str(e)
        
        # Update status to ERROR
        crud.update_document_status(
            db=db,
            document_id=document_id,
            status=DocumentStatus.ERROR,
            error_message=error_msg
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {error_msg}"
        )
# ============================================================
# ENDPOINT 3: GET ALL
# ============================================================

@router.get("/", response_model=list[schemas.DocumentListItem])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all documents (paginated).
    
    skip: How many to skip (for pagination)
    limit: How many to return (max 100)
    
    WHY: Users need to see their uploaded documents.
    """
    documents = crud.get_all_documents(db, skip=skip, limit=limit)
    return documents

# ============================================================
# ENDPOINT 4: GET ONE
# ============================================================

@router.get("/{document_id}", response_model=schemas.DocumentDetail)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single document with its extracted data.
    
    WHY: Users need to see the full details of a specific document.
    """
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

# ============================================================
# ENDPOINT 5: DELETE
# ============================================================

@router.delete("/{document_id}", response_model=schemas.DeleteResponse)
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a document.
    
    1. Get the document
    2. Delete the file from disk
    3. Delete the record from database
    
    WHY: Users need to remove unwanted documents.
    """
    # Get the document
    document = crud.get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            # Log error but continue
            print(f"Failed to delete file: {e}")
    
    # Delete from database
    crud.delete_document(db, document_id)
    
    return schemas.DeleteResponse(
        message="Document deleted successfully",
        id=document_id
    )