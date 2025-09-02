"""
Place model for geographical locations
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class Place(Base):
    __tablename__ = "places"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Place information
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False)  # Standardized format
    place_type = Column(String(50))  # city, county, state, country, etc.
    
    # Hierarchical structure
    parent_place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    
    # Geographic coordinates
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # Administrative divisions
    city = Column(String(100))
    county = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_place = relationship("Place", remote_side=[id])
    child_places = relationship("Place")
    
    def __repr__(self):
        return f"<Place(id={self.id}, name='{self.name}', type='{self.place_type}')>"