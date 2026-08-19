from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import Optional, List

from app import models
from app.models import DocumentStatus

# ============================================================
# CREATE
# ============================================================

def create_document(
    db: Session,
    filename: str,
    file_path: str,
    file_size: int
) -> models.Document:
    """
    Create a new document record.
    
    WHY: When a user uploads a PDF, we need to save its metadata.
    """
    document = models.Document(
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        status=DocumentStatus.UPLOADED
    )
    db.add(document)
    db.commit()
    db.refresh(document)  # Get the generated ID from database
    return document

# ============================================================
# READ (Get)
# ============================================================

def get_document(
    db: Session,
    document_id: UUID
) -> Optional[models.Document]:
    """
    Get a single document by ID.
    
    WHY: When a user wants to see a specific document.
    """
    return db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()

def get_all_documents(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Document]:
    """
    Get all documents (paginated).
    
    WHY: When a user wants to see their document list.
    skip/limit = pagination - don't return everything at once.
    """
    return db.query(models.Document).order_by(
        desc(models.Document.created_at)  # Newest first
    ).offset(skip).limit(limit).all()

# ============================================================
# UPDATE
# ============================================================

def update_document_status(
    db: Session,
    document_id: UUID,
    status: DocumentStatus,
    error_message: Optional[str] = None
) -> Optional[models.Document]:
    """
    Update document status.
    
    WHY: Track progress through the processing pipeline.
    """
    document = get_document(db, document_id)
    if not document:
        return None
    
    document.status = status
    
    # If error, store the error message
    if error_message:
        document.raw_llm_response = error_message
    
    db.commit()
    db.refresh(document)
    return document

def save_analysis_result(
    db: Session,
    document_id: UUID,
    extracted_data: dict,
    raw_response: str
) -> Optional[models.Document]:
    """
    Save the LLM extraction results.
    
    WHY: This is the core value of the app - saving what the AI extracted.
    """
    document = get_document(db, document_id)
    if not document:
        return None
    
    document.extracted_data = extracted_data
    document.raw_llm_response = raw_response
    document.status = DocumentStatus.DONE
    
    db.commit()
    db.refresh(document)
    return document

# ============================================================
# DELETE
# ============================================================

def delete_document(
    db: Session,
    document_id: UUID
) -> bool:
    """
    Delete a document from database.
    
    WHY: User might want to remove a document.
    """
    document = get_document(db, document_id)
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    return True