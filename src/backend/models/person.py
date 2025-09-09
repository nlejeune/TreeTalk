"""
Person Model - Individual Person Records with Biographical Information

This module defines the Person model representing individual people in the
genealogical database. Each person record contains biographical data, life
events, and relationships to other persons and places.

The Person model is central to the TreeTalk application, serving as the focal
point for family tree visualization and conversational AI queries.
"""

from sqlalchemy import Column, String, Text, Boolean, Date, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, remote
import uuid
from typing import Optional, Dict, Any

from utils.database import Base


class Person(Base):
    """
    Person model representing an individual in the genealogical database.
    
    This model stores:
    - Basic biographical information (names, dates, gender)
    - Life details (occupation, education, religion)
    - Privacy-sensitive notes
    - Relationships to source data and other entities
    
    Attributes:
        id (UUID): Unique identifier for the person
        source_id (UUID): Reference to the source that imported this person
        gedcom_id (str): Original GEDCOM identifier from source file
        given_names (str): Given names (first, middle names)
        surname (str): Family name/last name
        maiden_name (str): Birth surname (for married individuals)
        nickname (str): Commonly used nickname
        gender (str): Gender ('M', 'F', 'U' for unknown)
        birth_date (Date): Date of birth
        death_date (Date): Date of death (null if living)
        is_living (bool): Whether the person is currently living
        occupation (str): Primary occupation or profession
        education (str): Educational background
        religion (str): Religious affiliation
        notes (str): General notes about the person
        private_notes (str): Private notes (potentially encrypted)
    """
    
    __tablename__ = "persons"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference (required for data provenance)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    gedcom_id = Column(String(50))  # Original GEDCOM ID
    
    # Name fields
    given_names = Column(String(255))
    surname = Column(String(255))
    maiden_name = Column(String(255))
    nickname = Column(String(100))
    
    # Basic demographics
    gender = Column(String(10))  # M, F, U (Unknown)
    birth_date = Column(Date)
    death_date = Column(Date)
    is_living = Column(Boolean, default=True)
    
    # Life details
    occupation = Column(String(255))
    education = Column(Text)
    religion = Column(String(100))
    
    # Notes and additional information
    notes = Column(Text)
    private_notes = Column(Text)  # Could be encrypted in future
    
    # Relationships
    source = relationship("Source", back_populates="persons")
    events = relationship("Event", back_populates="person", cascade="all, delete-orphan", primaryjoin="Person.id == remote(Event.person_id)")
    
    # Relationships as person1 (primary person in relationship)
    relationships_as_person1 = relationship(
        "Relationship",
        foreign_keys="Relationship.person1_id",
        back_populates="person1",
        cascade="all, delete-orphan"
    )
    
    # Relationships as person2 (secondary person in relationship)
    relationships_as_person2 = relationship(
        "Relationship",
        foreign_keys="Relationship.person2_id",
        back_populates="person2"
    )
    
    # Chat sessions focused on this person
    focused_chat_sessions = relationship("ChatSession", back_populates="focused_person")
    
    def __repr__(self) -> str:
        """String representation of Person instance."""
        full_name = self.get_full_name()
        return f"<Person(id={self.id}, name='{full_name}', birth={self.birth_date})>"
    
    def get_full_name(self) -> str:
        """
        Get the full name of the person in standard format.
        
        Returns:
            str: Full name combining given names and surname
        """
        parts = []
        if self.given_names:
            parts.append(self.given_names.strip())
        if self.surname:
            parts.append(self.surname.strip())
        return " ".join(parts) or "Unknown"
    
    def get_display_name(self) -> str:
        """
        Get the preferred display name, using nickname if available.
        
        Returns:
            str: Display name (nickname or full name)
        """
        if self.nickname:
            return f"{self.nickname} ({self.get_full_name()})"
        return self.get_full_name()
    
    def get_life_span(self) -> str:
        """
        Get formatted life span string.
        
        Returns:
            str: Life span in format "YYYY-YYYY", "YYYY-present", "YYYY-?", or "?-?"
        """
        birth_str = self.birth_date.strftime("%Y") if self.birth_date else "?"
        if self.death_date:
            death_str = self.death_date.strftime("%Y")
            return f"{birth_str}-{death_str}"
        elif not self.is_living:
            return f"{birth_str}-?"
        else:
            # For living people with no death date
            if not self.birth_date:
                return "?-?"
            # Check age if birth date is known
            current_age = self.get_age()
            if current_age is not None and current_age >= 100:
                return f"{birth_str}-?"
            return f"{birth_str}-present"
    
    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        """
        Convert Person instance to dictionary for API responses.
        
        Args:
            include_private (bool): Whether to include private notes
            
        Returns:
            dict: Person data as dictionary
        """
        data = {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "gedcom_id": self.gedcom_id,
            "given_names": self.given_names,
            "surname": self.surname,
            "maiden_name": self.maiden_name,
            "nickname": self.nickname,
            "gender": self.gender,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "death_date": self.death_date.isoformat() if self.death_date else None,
            "is_living": self.is_living,
            "occupation": self.occupation,
            "education": self.education,
            "religion": self.religion,
            "notes": self.notes,
            "full_name": self.get_full_name(),
            "display_name": self.get_display_name(),
            "life_span": self.get_life_span()
        }
        
        if include_private:
            data["private_notes"] = self.private_notes
            
        return data
    
    def get_age(self, at_date: Optional[Date] = None) -> Optional[int]:
        """
        Calculate age at a specific date or current age.
        
        Args:
            at_date (Date, optional): Date to calculate age at. Defaults to death date or today.
            
        Returns:
            int: Age in years, or None if birth date unknown
        """
        if not self.birth_date:
            return None
            
        end_date = at_date or self.death_date
        if not end_date:
            from datetime import date
            end_date = date.today()
            
        age = end_date.year - self.birth_date.year
        
        # Adjust for birthday not yet reached
        if end_date.month < self.birth_date.month or (
            end_date.month == self.birth_date.month and 
            end_date.day < self.birth_date.day
        ):
            age -= 1
            
        return max(0, age)
    
    def get_relationships(self) -> list:
        """
        Get all relationships for this person (both as person1 and person2).
        
        Returns:
            list: All Relationship objects involving this person
        """
        return list(self.relationships_as_person1) + list(self.relationships_as_person2)
    
    def is_valid_gender(self) -> bool:
        """
        Check if gender value is valid.
        
        Returns:
            bool: True if gender is valid or None
        """
        valid_genders = {'M', 'F', 'U', None}
        return self.gender in valid_genders