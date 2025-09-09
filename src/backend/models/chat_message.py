"""
Chat Message Model - Individual Chat Messages

This module defines the ChatMessage model for storing individual messages
within chat sessions for the TreeTalk conversational AI feature.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from typing import Dict, Any

from utils.database import Base


class ChatMessage(Base):
    """Chat message model representing individual messages in conversations."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    message_type = Column(String(20), nullable=False, index=True)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    sequence_number = Column(Integer, nullable=False)
    
    # AI response metadata
    model_used = Column(String(100))
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    genealogy_context = Column(JSONB)
    cited_sources = Column(JSONB)
    
    # Error handling
    is_error = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ChatMessage instance to dictionary."""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "message_type": self.message_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sequence_number": self.sequence_number,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "response_time_ms": self.response_time_ms,
            "genealogy_context": self.genealogy_context,
            "cited_sources": self.cited_sources,
            "is_error": self.is_error,
            "error_message": self.error_message
        }