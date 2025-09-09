"""
Chat API Routes - Conversational AI Integration

This module provides REST API endpoints for chat functionality including
message handling, session management, and AI model integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from uuid import UUID

from utils.database import get_database_session
from services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for request/response
class ChatMessageRequest(BaseModel):
    """Request model for sending chat messages."""
    message: str
    model_name: Optional[str] = None
    session_id: Optional[UUID] = None
    

class CreateSessionRequest(BaseModel):
    """Request model for creating chat sessions."""
    title: Optional[str] = None
    focused_person_id: Optional[UUID] = None
    active_source_id: Optional[UUID] = None
    model_name: Optional[str] = None


@router.post("/message", response_model=Dict[str, Any])
async def send_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Send a message to the chat AI and get response.
    
    Args:
        request: Chat message request data
        db: Database session
        
    Returns:
        Chat response with message data and metadata
        
    Raises:
        HTTPException: If message processing fails
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        if len(request.message) > 4000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (maximum 4000 characters)"
            )
        
        chat_service = ChatService(db)
        
        # Use provided session ID or create new session
        session_id = request.session_id
        if not session_id:
            new_session = await chat_service.create_chat_session()
            session_id = new_session.id
        
        # Process message
        response_data = await chat_service.send_message(
            session_id=session_id,
            message=request.message,
            model_name=request.model_name
        )
        
        logger.info(f"Chat message processed successfully for session {session_id}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/sessions", response_model=Dict[str, Any])
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new chat session.
    
    Args:
        request: Session creation request data
        db: Database session
        
    Returns:
        Created session information
        
    Raises:
        HTTPException: If session creation fails
    """
    try:
        chat_service = ChatService(db)
        
        session = await chat_service.create_chat_session(
            title=request.title,
            focused_person_id=request.focused_person_id,
            active_source_id=request.active_source_id,
            model_name=request.model_name
        )
        
        logger.info(f"Created chat session: {session.id}")
        
        return {
            "success": True,
            "session": session.to_dict(),
            "message": "Chat session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages", response_model=List[Dict[str, Any]])
async def get_chat_history(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of messages"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get chat message history for a session.
    
    Args:
        session_id: UUID of the chat session
        limit: Maximum number of messages to return (1-200)
        db: Database session
        
    Returns:
        List of chat messages in chronological order
        
    Raises:
        HTTPException: If session not found or retrieval fails
    """
    try:
        chat_service = ChatService(db)
        
        messages = await chat_service.get_chat_history(
            session_id=session_id,
            limit=limit
        )
        
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get chat history for {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_available_models(
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get list of available AI models from OpenRouter.
    
    Args:
        db: Database session
        
    Returns:
        List of available models with pricing and metadata
        
    Raises:
        HTTPException: If model list retrieval fails
    """
    try:
        chat_service = ChatService(db)
        
        models = await chat_service.get_available_models()
        
        if not models:
            # Return default models if OpenRouter is not available (sorted by cost)
            models = [
                {
                    "id": "meta-llama/llama-3.1-8b-instruct:free",
                    "name": "Llama 3.1 8B Instruct (Free)",
                    "cost_per_1k_tokens": 0.0,
                    "context_length": 131072,
                    "description": "Free open-source model with good performance"
                },
                {
                    "id": "openai/gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "cost_per_1k_tokens": 0.0002,
                    "context_length": 128000,
                    "description": "Affordable small model with high intelligence"
                },
                {
                    "id": "anthropic/claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "cost_per_1k_tokens": 0.0008,
                    "context_length": 200000,
                    "description": "Fastest model with strong performance"
                },
                {
                    "id": "openai/gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "cost_per_1k_tokens": 0.002,
                    "context_length": 4096,
                    "description": "Fast and efficient model for conversational AI"
                }
            ]
        
        logger.info(f"Retrieved {len(models)} available AI models")
        
        return models
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        # Return basic models instead of failing
        return [
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "cost_per_1k_tokens": 0.002,
                "context_length": 4096,
                "description": "Default model (OpenRouter API key required for full access)"
            }
        ]


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get information about a specific chat session.
    
    Args:
        session_id: UUID of the chat session
        db: Database session
        
    Returns:
        Chat session information
        
    Raises:
        HTTPException: If session not found
    """
    try:
        from sqlalchemy import select
        from models.chat_session import ChatSession
        
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session not found: {session_id}"
            )
        
        return session.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session information"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete a chat session and all its messages.
    
    Args:
        session_id: UUID of the chat session to delete
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If session not found or deletion fails
    """
    try:
        from sqlalchemy import select, delete
        from models.chat_session import ChatSession
        
        # Check if session exists
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session not found: {session_id}"
            )
        
        session_title = session.title
        
        # Delete session (cascade will handle messages)
        await db.execute(
            delete(ChatSession).where(ChatSession.id == session_id)
        )
        await db.commit()
        
        logger.info(f"Deleted chat session: {session_id}")
        
        return {
            "success": True,
            "message": f"Successfully deleted chat session '{session_title}'",
            "deleted_session_id": str(session_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )