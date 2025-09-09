"""
Place Model - Geographical Locations for Events

This module defines the Place model representing geographical locations
associated with genealogical events and addresses. Places support hierarchical
addressing and geographic coordinates for mapping functionality.
"""

from sqlalchemy import Column, String, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from typing import Dict, Any

from utils.database import Base


class Place(Base):
    """
    Place model representing geographical locations in genealogical data.
    
    Attributes:
        id (UUID): Unique identifier for the place
        source_id (UUID): Reference to the source that imported this place
        name (str): Primary name of the place
        place_type (str): Type of place ('city', 'county', 'cemetery', etc.)
        locality (str): Local area or city name
        county (str): County or administrative division
        state_province (str): State or province
        country (str): Country name
        postal_code (str): Postal/ZIP code
        full_address (str): Complete address string
        latitude (float): Geographic latitude coordinate
        longitude (float): Geographic longitude coordinate
        notes (str): Additional notes about the place
        alternative_names (str): Alternative or historical names
    """
    
    __tablename__ = "places"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core place information
    name = Column(String(255), nullable=False)
    place_type = Column(String(50))
    
    # Hierarchical address components
    locality = Column(String(100))
    county = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    full_address = Column(Text)
    
    # Geographic coordinates
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Additional information
    notes = Column(Text)
    alternative_names = Column(Text)
    
    # Relationships
    source = relationship("Source", back_populates="places")
    events = relationship("Event", back_populates="place")
    marriage_relationships = relationship("Relationship", back_populates="marriage_place")
    
    def __repr__(self) -> str:
        """String representation of Place instance."""
        return f"<Place(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Place instance to dictionary for API responses."""
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "name": self.name,
            "place_type": self.place_type,
            "locality": self.locality,
            "county": self.county,
            "state_province": self.state_province,
            "country": self.country,
            "postal_code": self.postal_code,
            "full_address": self.full_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "notes": self.notes,
            "alternative_names": self.alternative_names,
            "display_name": self.get_display_name()
        }
    
    def get_display_name(self) -> str:
        """Get formatted display name for the place."""
        parts = []
        if self.locality:
            parts.append(self.locality)
        if self.county and self.county != self.locality:
            parts.append(self.county)
        if self.state_province:
            parts.append(self.state_province)
        if self.country:
            parts.append(self.country)
        
        return ", ".join(parts) or self.name