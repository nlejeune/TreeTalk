"""
Chat API routes - Handle chat interactions with family history
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..utils.database import get_db
from ..services.chat_service import ChatService

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    person_context: Optional[str] = None
    model: Optional[str] = None

# Endpoint to send a chat message and get AI response
@router.post("/message")
async def send_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response."""
    try:
        chat_service = ChatService(db)
        response = await chat_service.send_chat_message(
            message=request.message,
            session_id=request.session_id,
            person_context=request.person_context,
            model=request.model
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

# Endpoint to get chat history for a session
@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a session."""
    try:
        chat_service = ChatService(db)
        history = await chat_service.get_chat_history(session_id)
        
        return {
            "session_id": session_id,
            "messages": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")