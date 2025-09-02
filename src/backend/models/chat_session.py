"""
Chat session and messages models
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from ..utils.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True))  # Future user management
    
    # Session metadata
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_activity = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(20), default='active')  # 'active', 'archived'
    
    # Context information
    focused_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"))
    context_data = Column(JSONB)  # Store conversation context
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session")
    focused_person = relationship("Person")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}')>"

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Message content
    message_type = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Response metadata
    response_time_ms = Column(Integer)  # Time taken for AI response
    token_count = Column(Integer)       # Tokens used in LLM call
    model_used = Column(String(100))    # OpenRouter model identifier
    
    # Context references
    referenced_persons = Column(ARRAY(UUID(as_uuid=True)))  # Array of person IDs mentioned
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type='{self.message_type}', session={self.session_id})>"