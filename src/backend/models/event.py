"""
Event model for life events and milestones
"""

from sqlalchemy import Column, String, Date, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class Event(Base):
    __tablename__ = "events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event associations
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)
    # Valid types: 'birth', 'death', 'marriage', 'divorce', 'baptism', 'burial',
    # 'immigration', 'emigration', 'naturalization', 'military_service',
    # 'education', 'occupation_change', 'residence', 'census'
    
    event_date = Column(Date)
    event_date_text = Column(String(100))  # For imprecise dates
    place = Column(String(255))
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    description = Column(Text)
    
    # Additional participants (for marriages, baptisms, etc.)
    related_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    
    # Source information
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    citation = Column(Text)  # Source citation
    
    # Metadata
    confidence_level = Column(Integer, default=3)  # Data quality score 1-5
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = relationship("Person", foreign_keys=[person_id], back_populates="events")
    related_person = relationship("Person", foreign_keys=[related_person_id])
    place_rel = relationship("Place")
    source = relationship("Source", back_populates="events")
    
    def __repr__(self):
        return f"<Event(id={self.id}, type='{self.event_type}', person={self.person_id})>"