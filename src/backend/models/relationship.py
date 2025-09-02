"""
Relationship model for family connections
"""

from sqlalchemy import Column, String, Date, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class Relationship(Base):
    __tablename__ = "relationships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Person references
    person1_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    person2_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    
    # Relationship type
    relationship_type = Column(String(50), nullable=False)
    # Valid types: 'parent', 'child', 'spouse', 'partner', 'sibling', 
    # 'adoptive_parent', 'adoptive_child', 'step_parent', 'step_child', 'guardian', 'ward'
    
    # Additional relationship information
    start_date = Column(Date)  # Marriage date, adoption date, etc.
    end_date = Column(Date)    # Divorce date, death date, etc.
    place = Column(String(255))  # Where relationship event occurred
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    
    # Metadata
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    notes = Column(Text)
    confidence_level = Column(Integer, default=3)  # Data quality score 1-5
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person1 = relationship("Person", foreign_keys=[person1_id])
    person2 = relationship("Person", foreign_keys=[person2_id])
    source = relationship("Source")
    place_rel = relationship("Place")
    
    def __repr__(self):
        return f"<Relationship(id={self.id}, type='{self.relationship_type}', person1={self.person1_id}, person2={self.person2_id})>"