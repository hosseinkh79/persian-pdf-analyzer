from sqlalchemy import Column, String, DateTime, JSON, Text, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db import Base
import uuid
import enum

class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"      # File saved, waiting for processing
    PROCESSING = "processing"   # Currently being analyzed
    DONE = "done"              # Analysis complete
    ERROR = "error"            # Analysis failed

class Document(Base):
    __tablename__ = "documents"
    
    # Primary Key
    # UUID: Random, hard to guess, no sequential IDs
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # File metadata
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(BigInteger, nullable=False)  # BigInteger for large files
    
    # Status
    status = Column(
        Enum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        index=True
    )
    
    # Analysis results (the core data!)
    # JSON: Flexible schema - LLM output can vary
    extracted_data = Column(JSON, nullable=True)
    
    # Raw response for debugging
    raw_llm_response = Column(Text, nullable=True)
    
    # Timestamps
    # server_default: Set by PostgreSQL when inserted
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # onupdate: Auto-update when row changes
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
    
    def __repr__(self):
        """Human-readable representation for debugging."""
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"