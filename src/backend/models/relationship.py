"""
Relationship Model - Family Connections Between Persons

This module defines the Relationship model representing connections between
persons in the genealogical database. Relationships include parent-child,
spouse, sibling, and other family connections with associated metadata.

The Relationship model enables family tree traversal and genealogical queries
essential for the TreeTalk visualization and chat features.
"""

from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from typing import Dict, Any, Optional

from utils.database import Base


class Relationship(Base):
    """
    Relationship model representing connections between two persons.
    
    This model stores:
    - Directional relationships (person1 → person2)
    - Relationship type and subtype
    - Marriage/divorce details for spouse relationships
    - Confidence levels and validation status
    
    Attributes:
        id (UUID): Unique identifier for the relationship
        source_id (UUID): Reference to the source that imported this relationship
        person1_id (UUID): Primary person in the relationship
        person2_id (UUID): Secondary person in the relationship
        relationship_type (str): Type of relationship ('parent-child', 'spouse', 'sibling')
        relationship_subtype (str): Subtype ('biological', 'adoptive', 'step', etc.)
        is_primary (bool): Whether this is the primary relationship of this type
        marriage_date (Date): Date of marriage (for spouse relationships)
        marriage_place_id (UUID): Place where marriage occurred
        divorce_date (Date): Date of divorce (if applicable)
        is_current (bool): Whether relationship is currently active
        confidence (str): Confidence level ('high', 'medium', 'low')
        notes (str): Additional notes about the relationship
    """
    
    __tablename__ = "relationships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference (required for data provenance)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Person references (directional relationship)
    person1_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    person2_id = Column(UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationship classification
    relationship_type = Column(String(50), nullable=False, index=True)  # parent-child, spouse, sibling
    relationship_subtype = Column(String(50))  # biological, adoptive, step, etc.
    is_primary = Column(Boolean, default=True)
    
    # Marriage/divorce details (for spouse relationships)
    marriage_date = Column(Date)
    marriage_place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    divorce_date = Column(Date)
    is_current = Column(Boolean, default=True)
    
    # Data quality
    confidence = Column(String(10), default="high")  # high, medium, low
    notes = Column(Text)
    
    # Relationships
    source = relationship("Source", back_populates="relationships")
    person1 = relationship("Person", foreign_keys=[person1_id], back_populates="relationships_as_person1")
    person2 = relationship("Person", foreign_keys=[person2_id], back_populates="relationships_as_person2")
    marriage_place = relationship("Place", foreign_keys=[marriage_place_id])
    
    def __repr__(self) -> str:
        """String representation of Relationship instance."""
        return f"<Relationship(id={self.id}, type='{self.relationship_type}', person1={self.person1_id}, person2={self.person2_id})>"
    
    def to_dict(self, include_persons: bool = False) -> Dict[str, Any]:
        """
        Convert Relationship instance to dictionary for API responses.
        
        Args:
            include_persons (bool): Whether to include full person data
            
        Returns:
            dict: Relationship data as dictionary
        """
        data = {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "person1_id": str(self.person1_id),
            "person2_id": str(self.person2_id),
            "relationship_type": self.relationship_type,
            "relationship_subtype": self.relationship_subtype,
            "is_primary": self.is_primary,
            "marriage_date": self.marriage_date.isoformat() if self.marriage_date else None,
            "marriage_place_id": str(self.marriage_place_id) if self.marriage_place_id else None,
            "divorce_date": self.divorce_date.isoformat() if self.divorce_date else None,
            "is_current": self.is_current,
            "confidence": self.confidence,
            "notes": self.notes
        }
        
        if include_persons:
            data["person1"] = self.person1.to_dict() if self.person1 else None
            data["person2"] = self.person2.to_dict() if self.person2 else None
            
        return data
    
    def get_relationship_description(self, from_person_id: UUID) -> str:
        """
        Get human-readable relationship description from a specific person's perspective.
        
        Args:
            from_person_id (UUID): ID of the person from whose perspective to describe
            
        Returns:
            str: Relationship description (e.g., "father", "daughter", "spouse")
        """
        if self.relationship_type == "parent-child":
            if str(from_person_id) == str(self.person1_id):
                # person1 is parent of person2, so from person1's perspective, person2 is child
                return "child" if not self.person2 else (
                    "son" if self.person2.gender == "M" else 
                    "daughter" if self.person2.gender == "F" else "child"
                )
            else:
                # person2 is child of person1, so from person2's perspective, person1 is parent
                return "parent" if not self.person1 else (
                    "father" if self.person1.gender == "M" else 
                    "mother" if self.person1.gender == "F" else "parent"
                )
        
        elif self.relationship_type == "spouse":
            return "spouse" if not self.is_current else (
                "husband" if (str(from_person_id) == str(self.person2_id) and self.person1 and self.person1.gender == "M") else
                "wife" if (str(from_person_id) == str(self.person2_id) and self.person1 and self.person1.gender == "F") else
                "husband" if (str(from_person_id) == str(self.person1_id) and self.person2 and self.person2.gender == "M") else
                "wife" if (str(from_person_id) == str(self.person1_id) and self.person2 and self.person2.gender == "F") else
                "spouse"
            )
        
        elif self.relationship_type == "sibling":
            other_person = self.person2 if str(from_person_id) == str(self.person1_id) else self.person1
            if other_person:
                return (
                    "brother" if other_person.gender == "M" else
                    "sister" if other_person.gender == "F" else
                    "sibling"
                )
            return "sibling"
        
        else:
            return self.relationship_type
    
    def get_other_person_id(self, person_id: UUID) -> Optional[UUID]:
        """
        Get the ID of the other person in the relationship.
        
        Args:
            person_id (UUID): ID of one person in the relationship
            
        Returns:
            UUID: ID of the other person, or None if person_id not in relationship
        """
        if str(person_id) == str(self.person1_id):
            return self.person2_id
        elif str(person_id) == str(self.person2_id):
            return self.person1_id
        return None
    
    def is_marriage_relationship(self) -> bool:
        """
        Check if this is a marriage relationship.
        
        Returns:
            bool: True if this is a spouse relationship with marriage date
        """
        return self.relationship_type == "spouse" and self.marriage_date is not None
    
    def is_active_marriage(self) -> bool:
        """
        Check if this is an active (non-divorced) marriage.
        
        Returns:
            bool: True if married and not divorced
        """
        return (
            self.relationship_type == "spouse" and 
            self.marriage_date is not None and 
            self.divorce_date is None and 
            self.is_current
        )
    
    def get_marriage_duration(self) -> Optional[int]:
        """
        Calculate marriage duration in years.
        
        Returns:
            int: Duration in years, or None if not a marriage or missing dates
        """
        if not self.is_marriage_relationship():
            return None
            
        end_date = self.divorce_date
        if not end_date and not self.is_current:
            # Marriage ended but no divorce date - assume death
            return None
        elif not end_date:
            # Still married
            from datetime import date
            end_date = date.today()
            
        years = end_date.year - self.marriage_date.year
        
        # Adjust for anniversary not yet reached
        if (end_date.month < self.marriage_date.month or 
            (end_date.month == self.marriage_date.month and end_date.day < self.marriage_date.day)):
            years -= 1
            
        return max(0, years)