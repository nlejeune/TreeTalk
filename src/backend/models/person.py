"""
Person Model - Individual Records in Genealogical Database

This model represents individual people in the family tree.
Stores biographical information, life events, and relationships.

Key Features:
- Comprehensive person data (names, dates, places)
- Source tracking for data provenance
- Support for both living and deceased individuals
- Integration with GEDCOM import system
- Flexible date handling (exact dates and text descriptions)

Relationships:
- Many-to-One with Source (data provenance)
- One-to-Many with Events (birth, death, marriage, etc.)
- Many-to-Many with other Persons via Relationships
- Many-to-One with Places (birth/death locations)
"""

from sqlalchemy import Column, String, Date, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class Person(Base):
    __tablename__ = "persons"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source tracking
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    gedcom_id = Column(String(255))  # Original GEDCOM identifier (@I1@, etc.)
    external_id = Column(String(255))  # FamilySearch Person ID
    
    # Name information
    name = Column(String(255), nullable=False)
    given_names = Column(Text)
    surname = Column(String(255))
    name_suffix = Column(String(50))  # Jr., Sr., III, etc.
    nickname = Column(String(100))
    
    # Basic information
    gender = Column(String(1))  # M, F, U (Male, Female, Unknown)
    is_living = Column(Boolean, default=False)
    
    # Birth information
    birth_date = Column(Date)
    birth_date_text = Column(String(100))  # For imprecise dates like "about 1850"
    birth_place = Column(String(255))
    birth_place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    
    # Death information
    death_date = Column(Date)
    death_date_text = Column(String(100))
    death_place = Column(String(255))
    death_place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    
    # Additional information
    occupation = Column(String(255))
    religion = Column(String(100))
    notes = Column(Text)
    
    # Metadata
    confidence_level = Column(Integer, default=3)  # Data quality score 1-5
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Source", back_populates="persons")
    birth_place_rel = relationship("Place", foreign_keys=[birth_place_id])
    death_place_rel = relationship("Place", foreign_keys=[death_place_id])
    events = relationship("Event", foreign_keys="Event.person_id", back_populates="person")
    related_events = relationship("Event", foreign_keys="Event.related_person_id")
    
    # Family relationships
    relationships_as_person1 = relationship("Relationship", foreign_keys="Relationship.person1_id")
    relationships_as_person2 = relationship("Relationship", foreign_keys="Relationship.person2_id")
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}', birth_date={self.birth_date})>"