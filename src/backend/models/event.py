"""
Event Model - Life Events and Milestones for Persons

This module defines the Event model representing life events and milestones
associated with persons in the genealogical database.
"""

from sqlalchemy import Column, String, Text, Date, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from typing import Dict, Any

from utils.database import Base


class Event(Base):
    """Event model representing life events for persons."""
    
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    event_subtype = Column(String(50))
    event_date = Column(Date)
    date_qualifier = Column(String(20))  # 'about', 'before', 'after', etc.
    date_text = Column(String(100))  # Original date text
    
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    place_text = Column(String(255))  # Original place text
    other_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    
    description = Column(Text)
    notes = Column(Text)
    confidence = Column(String(10), default="medium")
    is_primary = Column(Boolean, default=True)
    
    # Relationships
    source = relationship("Source", back_populates="events")
    person = relationship("Person", foreign_keys=[person_id], back_populates="events")
    place = relationship("Place", back_populates="events")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Event instance to dictionary."""
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "person_id": str(self.person_id),
            "event_type": self.event_type,
            "event_subtype": self.event_subtype,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "date_qualifier": self.date_qualifier,
            "date_text": self.date_text,
            "place_id": str(self.place_id) if self.place_id else None,
            "place_text": self.place_text,
            "other_person_id": str(self.other_person_id) if self.other_person_id else None,
            "description": self.description,
            "notes": self.notes,
            "confidence": self.confidence,
            "is_primary": self.is_primary
        }