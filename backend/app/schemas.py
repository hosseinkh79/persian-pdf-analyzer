# app/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from enum import Enum

# ============================================================
# ENUMS (Match the model)
# ============================================================

class DocumentStatus(str, Enum):
    """Document status - matches the model enum."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

# ============================================================
# RESPONSE SCHEMAS (What users get back)
# ============================================================

class DocumentBase(BaseModel):
    """
    Base document fields shared across all responses.
    
    WHY: DRY - reuse common fields instead of repeating them.
    """
    id: UUID
    filename: str
    status: DocumentStatus
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allow converting SQLAlchemy models to schemas

class DocumentListItem(DocumentBase):
    """
    Document in a list view (no extracted data).
    
    WHY: For the "Get All" endpoint, we don't need the heavy extracted_data.
    This makes the response smaller and faster.
    """
    pass

class DocumentDetail(DocumentBase):
    """
    Full document detail with extracted data.
    
    WHY: For the "Get One" endpoint, we include all data.
    """
    extracted_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    """
    Response after uploading a file.
    
    WHY: User needs to know:
    1. The ID to reference later
    2. The filename they uploaded
    3. The current status
    4. A success message
    """
    id: UUID = Field(..., description="Document ID for future reference")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Current status")
    message: str = Field(..., description="Human-readable message")

class AnalysisResponse(BaseModel):
    """
    Response after analysis is complete.
    
    WHY: User needs:
    1. Document identification (id, filename)
    2. Current status
    3. The extracted data (what they wanted!)
    """
    id: UUID
    filename: str
    status: DocumentStatus
    extracted_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class DeleteResponse(BaseModel):
    """Response after deleting a document."""
    message: str = Field(..., description="Success message")
    id: UUID = Field(..., description="Deleted document ID")

# ============================================================
# REQUEST SCHEMAS (What users send)
# ============================================================

# Note: We don't need many request schemas for this app!
# Upload uses multipart/form-data (file upload)
# Analyze uses URL parameter (document ID)
# So no JSON bodies needed!