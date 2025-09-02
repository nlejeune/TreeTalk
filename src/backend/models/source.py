"""
Source Model - Data Provenance Tracking

This model tracks the sources of genealogical data imported into TreeTalk.
Essential for maintaining data quality and understanding data origins.

Key Features:
- Tracks GEDCOM files, FamilySearch imports, manual entries
- Import status and metadata management
- Cascade delete relationships to clean up related data
- JSON metadata storage for flexible source-specific information

Source Types:
- 'gedcom': GEDCOM file imports
- 'familysearch': FamilySearch API imports
- 'manual': User-entered data
- 'web': Web scraping or other online sources

Relationships:
- One-to-Many with Persons (individuals from this source)
- One-to-Many with Relationships (family connections)
- One-to-Many with Events (life events)
All relationships cascade on delete for data integrity.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class Source(Base):
    __tablename__ = "sources"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source information
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'gedcom', 'familysearch'
    description = Column(Text)
    file_path = Column(String(500))  # For GEDCOM files
    
    # Import tracking
    imported_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    imported_by = Column(UUID(as_uuid=True))  # Future user management
    status = Column(String(50), nullable=False, default='active')  # 'active', 'inactive', 'error'
    
    # Additional metadata
    source_metadata = Column(JSONB)  # Store additional source-specific data
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with cascade delete
    persons = relationship("Person", back_populates="source", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="source", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', type='{self.type}')>"