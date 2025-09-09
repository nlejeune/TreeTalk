"""
Source Model - GEDCOM File and Data Source Tracking

This module defines the Source model for tracking GEDCOM files and other data
sources imported into the TreeTalk application. Each source represents a complete
genealogical dataset with associated metadata and import status.

The Source model serves as the root entity for data provenance, ensuring that
all genealogical data can be traced back to its original source file.
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from utils.database import Base


class Source(Base):
    """
    Source model representing a data source (typically GEDCOM file) imported into TreeTalk.
    
    This model tracks:
    - File metadata (name, size, hash)
    - Import status and statistics
    - Relationship to all derived data
    
    Attributes:
        id (UUID): Unique identifier for the source
        name (str): Human-readable name of the source
        filename (str): Original filename of imported file
        source_type (str): Type of source ('gedcom', 'manual', etc.)
        file_size (int): Size of source file in bytes
        file_hash (str): SHA-256 hash to prevent duplicate imports
        status (str): Import status ('pending', 'processing', 'completed', 'error')
        import_date (datetime): When the source was first imported
        last_updated (datetime): Last modification timestamp
        persons_count (int): Number of persons imported from this source
        families_count (int): Number of family relationships imported
        description (str): User-provided description of the source
        notes (str): Additional notes about the source
        error_message (str): Error details if import failed
        is_active (bool): Whether the source is currently active
    """
    
    __tablename__ = "sources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core metadata
    name = Column(String(255), nullable=False, index=True)
    filename = Column(String(255))
    source_type = Column(String(50), nullable=False, default="gedcom", index=True)
    
    # File information
    file_size = Column(Integer)
    file_hash = Column(String(64), unique=True, index=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="pending", index=True)
    import_date = Column(DateTime(timezone=True), default=func.now())
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Statistics
    persons_count = Column(Integer, default=0)
    families_count = Column(Integer, default=0)
    
    # Descriptive fields
    description = Column(Text)
    notes = Column(Text)
    error_message = Column(Text)
    
    # Status flags
    is_active = Column(Boolean, default=True)
    
    # Relationships to dependent data
    persons = relationship("Person", back_populates="source", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="source", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="source", cascade="all, delete-orphan")
    places = relationship("Place", back_populates="source", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="active_source")
    
    def __repr__(self) -> str:
        """String representation of Source instance."""
        return f"<Source(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self) -> dict:
        """
        Convert Source instance to dictionary for API responses.
        
        Returns:
            dict: Source data as dictionary
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "filename": self.filename,
            "source_type": self.source_type,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "status": self.status,
            "import_date": self.import_date.isoformat() if self.import_date else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "persons_count": self.persons_count,
            "families_count": self.families_count,
            "description": self.description,
            "notes": self.notes,
            "error_message": self.error_message,
            "is_active": self.is_active
        }
    
    def update_statistics(self, persons_count: int = None, families_count: int = None):
        """
        Update source statistics after import or data modification.
        
        Args:
            persons_count (int, optional): New person count
            families_count (int, optional): New family count
        """
        if persons_count is not None:
            self.persons_count = persons_count
        if families_count is not None:
            self.families_count = families_count
        self.last_updated = datetime.utcnow()
    
    def mark_completed(self, persons_count: int, families_count: int):
        """
        Mark source import as completed with final statistics.
        
        Args:
            persons_count (int): Final count of imported persons
            families_count (int): Final count of imported families
        """
        self.status = "completed"
        self.persons_count = persons_count
        self.families_count = families_count
        self.last_updated = datetime.utcnow()
    
    def mark_error(self, error_message: str):
        """
        Mark source import as failed with error details.
        
        Args:
            error_message (str): Description of the error that occurred
        """
        self.status = "error"
        self.error_message = error_message
        self.last_updated = datetime.utcnow()