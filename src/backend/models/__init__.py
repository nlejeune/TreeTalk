"""
TreeTalk Backend Models Package

This package contains all SQLAlchemy database models for the TreeTalk application.
Models are organized by domain and follow the database schema defined in the
project documentation.

Key Models:
- Source: GEDCOM file and data source tracking
- Person: Individual person records with biographical data
- Relationship: Family connections between persons
- Event: Life events and milestones
- Place: Geographical locations
- ChatSession: Chat conversation contexts
- ChatMessage: Individual chat messages
- Configuration: Encrypted application settings
"""

from .source import Source
from .person import Person
from .relationship import Relationship
from .event import Event
from .place import Place
from .chat_session import ChatSession
from .chat_message import ChatMessage
from .configuration import Configuration

__all__ = [
    "Source",
    "Person", 
    "Relationship",
    "Event",
    "Place",
    "ChatSession",
    "ChatMessage",
    "Configuration"
]