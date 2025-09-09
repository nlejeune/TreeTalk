"""
Chat Session Model - Conversation Context Management

This module defines the ChatSession model for managing chat conversation
contexts and settings for the TreeTalk conversational AI feature.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from typing import Dict, Any

from utils.database import Base


class ChatSession(Base):
    """Chat session model representing conversation contexts."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_activity = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    focused_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    active_source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    model_name = Column(String(100))
    system_prompt = Column(Text)
    max_context_messages = Column(Integer, default=20)
    temperature = Column(Float, default=0.7)
    
    # Relationships
    focused_person = relationship("Person", back_populates="focused_chat_sessions")
    active_source = relationship("Source", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ChatSession instance to dictionary."""
        return {
            "id": str(self.id),
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "focused_person_id": str(self.focused_person_id) if self.focused_person_id else None,
            "active_source_id": str(self.active_source_id) if self.active_source_id else None,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "max_context_messages": self.max_context_messages,
            "temperature": self.temperature
        }