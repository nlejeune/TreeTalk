"""
Unit Tests for TreeTalk Database Models

This module contains unit tests for all database models to ensure
proper functionality, validation, and relationships.
"""

import pytest
import uuid
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Import models
from src.backend.models.source import Source
from src.backend.models.person import Person
from src.backend.models.relationship import Relationship
from src.backend.models.event import Event
from src.backend.models.place import Place
from src.backend.models.chat_session import ChatSession
from src.backend.models.chat_message import ChatMessage
from src.backend.models.configuration import Configuration
from src.backend.utils.database import Base


class TestSourceModel:
    """Test cases for Source model."""
    
    def test_source_creation(self):
        """Test creating a Source instance."""
        source = Source(
            name="Test Family Tree",
            filename="test.ged",
            source_type="gedcom",
            file_size=1024,
            file_hash="abc123",
            status="completed"
        )
        
        assert source.name == "Test Family Tree"
        assert source.filename == "test.ged"
        assert source.source_type == "gedcom"
        assert source.file_size == 1024
        assert source.file_hash == "abc123"
        assert source.status == "completed"
        assert source.is_active == True  # Default value
    
    def test_source_to_dict(self):
        """Test Source to_dict method."""
        source = Source(
            name="Test Family Tree",
            filename="test.ged",
            persons_count=100,
            families_count=50
        )
        
        result = source.to_dict()
        
        assert isinstance(result, dict)
        assert result["name"] == "Test Family Tree"
        assert result["filename"] == "test.ged"
        assert result["persons_count"] == 100
        assert result["families_count"] == 50
    
    def test_source_update_statistics(self):
        """Test updating source statistics."""
        source = Source(name="Test")
        original_updated = source.last_updated
        
        source.update_statistics(persons_count=200, families_count=100)
        
        assert source.persons_count == 200
        assert source.families_count == 100
        assert source.last_updated != original_updated
    
    def test_source_mark_completed(self):
        """Test marking source as completed."""
        source = Source(name="Test", status="processing")
        
        source.mark_completed(persons_count=150, families_count=75)
        
        assert source.status == "completed"
        assert source.persons_count == 150
        assert source.families_count == 75
    
    def test_source_mark_error(self):
        """Test marking source with error."""
        source = Source(name="Test", status="processing")
        error_msg = "Invalid file format"
        
        source.mark_error(error_msg)
        
        assert source.status == "error"
        assert source.error_message == error_msg


class TestPersonModel:
    """Test cases for Person model."""
    
    def test_person_creation(self):
        """Test creating a Person instance."""
        person_id = uuid.uuid4()
        source_id = uuid.uuid4()
        
        person = Person(
            id=person_id,
            source_id=source_id,
            given_names="John William",
            surname="Smith",
            gender="M",
            birth_date=date(1850, 5, 15),
            death_date=date(1920, 8, 30),
            is_living=False
        )
        
        assert person.id == person_id
        assert person.source_id == source_id
        assert person.given_names == "John William"
        assert person.surname == "Smith"
        assert person.gender == "M"
        assert person.birth_date == date(1850, 5, 15)
        assert person.death_date == date(1920, 8, 30)
        assert person.is_living == False
    
    def test_person_get_full_name(self):
        """Test getting full name."""
        person = Person(given_names="John William", surname="Smith")
        assert person.get_full_name() == "John William Smith"
        
        person_no_surname = Person(given_names="John")
        assert person_no_surname.get_full_name() == "John"
        
        person_no_names = Person()
        assert person_no_names.get_full_name() == "Unknown"
    
    def test_person_get_display_name(self):
        """Test getting display name with nickname."""
        person = Person(given_names="John", surname="Smith", nickname="Jack")
        assert person.get_display_name() == "Jack (John Smith)"
        
        person_no_nickname = Person(given_names="John", surname="Smith")
        assert person_no_nickname.get_display_name() == "John Smith"
    
    def test_person_get_life_span(self):
        """Test getting formatted life span."""
        # Person with birth and death dates
        person = Person(
            birth_date=date(1850, 5, 15),
            death_date=date(1920, 8, 30),
            is_living=False
        )
        assert person.get_life_span() == "1850-1920"
        
        # Living person
        living_person = Person(birth_date=date(1980, 1, 1), is_living=True)
        assert living_person.get_life_span() == "1980-present"
        
        # Unknown death date but not living
        unknown_death = Person(birth_date=date(1800, 1, 1), is_living=False)
        assert unknown_death.get_life_span() == "1800-?"
    
    def test_person_get_age(self):
        """Test age calculation."""
        person = Person(birth_date=date(1980, 1, 1))
        
        # Age at specific date
        age_at_2020 = person.get_age(at_date=date(2020, 1, 1))
        assert age_at_2020 == 40
        
        # Age before birthday
        age_before_birthday = person.get_age(at_date=date(2019, 12, 31))
        assert age_before_birthday == 39
        
        # No birth date
        person_no_birth = Person()
        assert person_no_birth.get_age() is None
    
    def test_person_is_valid_gender(self):
        """Test gender validation."""
        assert Person(gender="M").is_valid_gender()
        assert Person(gender="F").is_valid_gender()
        assert Person(gender="U").is_valid_gender()
        assert Person(gender=None).is_valid_gender()
        assert not Person(gender="X").is_valid_gender()
    
    def test_person_to_dict(self):
        """Test Person to_dict method."""
        person = Person(
            given_names="John",
            surname="Smith",
            birth_date=date(1850, 1, 1),
            gender="M"
        )
        
        result = person.to_dict()
        
        assert isinstance(result, dict)
        assert result["given_names"] == "John"
        assert result["surname"] == "Smith"
        assert result["gender"] == "M"
        assert result["full_name"] == "John Smith"
        assert result["life_span"] == "1850-present"
        assert "private_notes" not in result  # Default is not to include private
        
        # Test with private notes included
        result_with_private = person.to_dict(include_private=True)
        assert "private_notes" in result_with_private


class TestRelationshipModel:
    """Test cases for Relationship model."""
    
    def test_relationship_creation(self):
        """Test creating a Relationship instance."""
        rel_id = uuid.uuid4()
        source_id = uuid.uuid4()
        person1_id = uuid.uuid4()
        person2_id = uuid.uuid4()
        
        relationship = Relationship(
            id=rel_id,
            source_id=source_id,
            person1_id=person1_id,
            person2_id=person2_id,
            relationship_type="parent-child",
            relationship_subtype="biological",
            marriage_date=date(1875, 6, 10)
        )
        
        assert relationship.id == rel_id
        assert relationship.source_id == source_id
        assert relationship.person1_id == person1_id
        assert relationship.person2_id == person2_id
        assert relationship.relationship_type == "parent-child"
        assert relationship.relationship_subtype == "biological"
        assert relationship.marriage_date == date(1875, 6, 10)
    
    def test_relationship_get_other_person_id(self):
        """Test getting the other person in a relationship."""
        person1_id = uuid.uuid4()
        person2_id = uuid.uuid4()
        
        relationship = Relationship(
            person1_id=person1_id,
            person2_id=person2_id,
            relationship_type="spouse"
        )
        
        assert relationship.get_other_person_id(person1_id) == person2_id
        assert relationship.get_other_person_id(person2_id) == person1_id
        assert relationship.get_other_person_id(uuid.uuid4()) is None
    
    def test_relationship_is_marriage_relationship(self):
        """Test identifying marriage relationships."""
        marriage = Relationship(
            relationship_type="spouse",
            marriage_date=date(1875, 6, 10)
        )
        assert marriage.is_marriage_relationship()
        
        not_marriage = Relationship(
            relationship_type="parent-child"
        )
        assert not not_marriage.is_marriage_relationship()
        
        spouse_no_date = Relationship(
            relationship_type="spouse"
        )
        assert not spouse_no_date.is_marriage_relationship()
    
    def test_relationship_is_active_marriage(self):
        """Test identifying active marriages."""
        active_marriage = Relationship(
            relationship_type="spouse",
            marriage_date=date(1875, 6, 10),
            is_current=True
        )
        assert active_marriage.is_active_marriage()
        
        divorced = Relationship(
            relationship_type="spouse",
            marriage_date=date(1875, 6, 10),
            divorce_date=date(1880, 1, 1),
            is_current=True
        )
        assert not divorced.is_active_marriage()
    
    def test_relationship_get_marriage_duration(self):
        """Test calculating marriage duration."""
        # Active marriage (no divorce date)
        marriage = Relationship(
            relationship_type="spouse",
            marriage_date=date(2000, 1, 1),
            is_current=True
        )
        duration = marriage.get_marriage_duration()
        assert duration is not None and duration >= 20  # At least 20 years
        
        # Divorced marriage
        divorced_marriage = Relationship(
            relationship_type="spouse",
            marriage_date=date(2000, 1, 1),
            divorce_date=date(2010, 1, 1),
            is_current=False
        )
        assert divorced_marriage.get_marriage_duration() == 10
        
        # Not a marriage
        parent_child = Relationship(
            relationship_type="parent-child"
        )
        assert parent_child.get_marriage_duration() is None


class TestEventModel:
    """Test cases for Event model."""
    
    def test_event_creation(self):
        """Test creating an Event instance."""
        event_id = uuid.uuid4()
        source_id = uuid.uuid4()
        person_id = uuid.uuid4()
        
        event = Event(
            id=event_id,
            source_id=source_id,
            person_id=person_id,
            event_type="birth",
            event_date=date(1850, 5, 15),
            description="Born in London"
        )
        
        assert event.id == event_id
        assert event.source_id == source_id
        assert event.person_id == person_id
        assert event.event_type == "birth"
        assert event.event_date == date(1850, 5, 15)
        assert event.description == "Born in London"
    
    def test_event_to_dict(self):
        """Test Event to_dict method."""
        event = Event(
            event_type="marriage",
            event_date=date(1875, 6, 10),
            description="Married in St. Mary's Church"
        )
        
        result = event.to_dict()
        
        assert isinstance(result, dict)
        assert result["event_type"] == "marriage"
        assert result["event_date"] == "1875-06-10"
        assert result["description"] == "Married in St. Mary's Church"


class TestPlaceModel:
    """Test cases for Place model."""
    
    def test_place_creation(self):
        """Test creating a Place instance."""
        place_id = uuid.uuid4()
        source_id = uuid.uuid4()
        
        place = Place(
            id=place_id,
            source_id=source_id,
            name="London",
            place_type="city",
            locality="London",
            country="England",
            latitude=51.5074,
            longitude=-0.1278
        )
        
        assert place.id == place_id
        assert place.source_id == source_id
        assert place.name == "London"
        assert place.place_type == "city"
        assert place.locality == "London"
        assert place.country == "England"
        assert place.latitude == 51.5074
        assert place.longitude == -0.1278
    
    def test_place_get_display_name(self):
        """Test getting formatted display name."""
        place = Place(
            name="St. Mary's Church",
            locality="London",
            county="Greater London",
            country="England"
        )
        
        display_name = place.get_display_name()
        assert display_name == "London, Greater London, England"
        
        # Place with only name
        simple_place = Place(name="Unknown Location")
        assert simple_place.get_display_name() == "Unknown Location"


class TestChatSessionModel:
    """Test cases for ChatSession model."""
    
    def test_chat_session_creation(self):
        """Test creating a ChatSession instance."""
        session_id = uuid.uuid4()
        
        session = ChatSession(
            id=session_id,
            title="Family History Chat",
            model_name="openai/gpt-3.5-turbo",
            temperature=0.7,
            max_context_messages=20
        )
        
        assert session.id == session_id
        assert session.title == "Family History Chat"
        assert session.model_name == "openai/gpt-3.5-turbo"
        assert session.temperature == 0.7
        assert session.max_context_messages == 20
        assert session.is_active == True  # Default
    
    def test_chat_session_to_dict(self):
        """Test ChatSession to_dict method."""
        session = ChatSession(
            title="Test Chat",
            model_name="openai/gpt-3.5-turbo",
            message_count=5
        )
        
        result = session.to_dict()
        
        assert isinstance(result, dict)
        assert result["title"] == "Test Chat"
        assert result["model_name"] == "openai/gpt-3.5-turbo"
        assert result["message_count"] == 5


class TestChatMessageModel:
    """Test cases for ChatMessage model."""
    
    def test_chat_message_creation(self):
        """Test creating a ChatMessage instance."""
        message_id = uuid.uuid4()
        session_id = uuid.uuid4()
        
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            message_type="user",
            content="Tell me about my ancestors",
            sequence_number=1
        )
        
        assert message.id == message_id
        assert message.session_id == session_id
        assert message.message_type == "user"
        assert message.content == "Tell me about my ancestors"
        assert message.sequence_number == 1
        assert message.is_error == False  # Default
    
    def test_chat_message_to_dict(self):
        """Test ChatMessage to_dict method."""
        message = ChatMessage(
            message_type="assistant",
            content="Based on your family tree data...",
            sequence_number=2,
            tokens_used=150,
            model_used="openai/gpt-3.5-turbo"
        )
        
        result = message.to_dict()
        
        assert isinstance(result, dict)
        assert result["message_type"] == "assistant"
        assert result["content"] == "Based on your family tree data..."
        assert result["sequence_number"] == 2
        assert result["tokens_used"] == 150
        assert result["model_used"] == "openai/gpt-3.5-turbo"


if __name__ == "__main__":
    pytest.main([__file__])