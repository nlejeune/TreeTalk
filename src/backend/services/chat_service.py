"""
Chat Service - OpenRouter API Integration
Handles conversational queries about family history
"""

import httpx
import json
import os
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.person import Person
from ..models.relationship import Relationship
from ..models.chat_session import ChatSession, ChatMessage

class ChatService:
    """Service for handling chat interactions with OpenRouter API."""
    
    def __init__(self, db: Session):
        self.db = db
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "meta-llama/llama-3.1-8b-instruct:free"
    
    async def send_chat_message(
        self,
        message: str,
        session_id: str = "default",
        person_context: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message and get AI response.
        
        Args:
            message: User message
            session_id: Chat session identifier
            person_context: ID of person to focus context on
            model: OpenRouter model to use
            
        Returns:
            Dict with response and metadata
        """
        if not self.openrouter_api_key:
            return {
                "response": "OpenRouter API key not configured. Please set your API key in the Configuration tab.",
                "error": "api_key_missing"
            }
        
        try:
            # Get or create chat session
            chat_session = await self._get_or_create_session(session_id, person_context)
            
            # Build context from family data
            context = await self._build_family_context(person_context, chat_session)
            
            # Prepare messages for API
            messages = await self._prepare_messages(message, context, chat_session)
            
            # Call OpenRouter API
            start_time = datetime.utcnow()
            api_response = await self._call_openrouter_api(messages, model or self.default_model)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if api_response.get("error"):
                return {
                    "response": f"AI service error: {api_response['error']}",
                    "error": "api_error"
                }
            
            ai_response = api_response["choices"][0]["message"]["content"]
            
            # Save messages to database
            await self._save_messages(
                chat_session.id,
                message,
                ai_response,
                response_time,
                model or self.default_model,
                api_response.get("usage", {}).get("total_tokens", 0)
            )
            
            return {
                "response": ai_response,
                "session_id": session_id,
                "response_time_ms": response_time,
                "tokens_used": api_response.get("usage", {}).get("total_tokens", 0)
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "error": "service_error"
            }
    
    async def _get_or_create_session(
        self,
        session_id: str,
        person_context: Optional[str] = None
    ) -> ChatSession:
        """Get existing chat session or create new one."""
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            session = ChatSession(
                session_id=session_id,
                focused_person_id=person_context,
                status="active"
            )
            self.db.add(session)
            self.db.commit()
        else:
            # Update last activity
            session.last_activity = datetime.utcnow()
            if person_context:
                session.focused_person_id = person_context
            self.db.commit()
        
        return session
    
    async def _build_family_context(
        self,
        person_id: Optional[str],
        session: ChatSession
    ) -> str:
        """Build context string from family data."""
        context_parts = []
        
        # Get focused person info
        focused_person = None
        if person_id:
            focused_person = self.db.query(Person).filter(Person.id == person_id).first()
        elif session.focused_person_id:
            focused_person = self.db.query(Person).filter(Person.id == session.focused_person_id).first()
        
        if focused_person:
            context_parts.append(f"Currently focused on: {focused_person.name}")
            
            # Add person details
            person_info = []
            if focused_person.birth_date:
                person_info.append(f"Born: {focused_person.birth_date}")
            if focused_person.birth_place:
                person_info.append(f"Birth place: {focused_person.birth_place}")
            if focused_person.death_date:
                person_info.append(f"Died: {focused_person.death_date}")
            elif focused_person.is_living:
                person_info.append("Living")
            if focused_person.death_place:
                person_info.append(f"Death place: {focused_person.death_place}")
            if focused_person.occupation:
                person_info.append(f"Occupation: {focused_person.occupation}")
            
            if person_info:
                context_parts.append(f"Person details: {'; '.join(person_info)}")
            
            # Get family relationships
            relationships = self.db.query(Relationship).filter(
                (Relationship.person1_id == focused_person.id) |
                (Relationship.person2_id == focused_person.id)
            ).limit(20).all()
            
            if relationships:
                rel_info = []
                for rel in relationships:
                    other_person = None
                    rel_type = rel.relationship_type
                    
                    if rel.person1_id == focused_person.id:
                        other_person = rel.person2
                        # Flip relationship perspective
                        if rel_type == "parent":
                            rel_type = "child of"
                        elif rel_type == "child":
                            rel_type = "parent of"
                    else:
                        other_person = rel.person1
                        if rel_type == "parent":
                            rel_type = "parent of"
                        elif rel_type == "child":
                            rel_type = "child of"
                    
                    if other_person:
                        rel_info.append(f"{rel_type}: {other_person.name}")
                
                if rel_info:
                    context_parts.append(f"Family relationships: {'; '.join(rel_info)}")
        
        # Get recent conversation context
        recent_messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.timestamp.desc()).limit(5).all()
        
        if recent_messages:
            context_parts.append("Recent conversation context available.")
        
        return "\n".join(context_parts) if context_parts else "No specific family context available."
    
    async def _prepare_messages(
        self,
        user_message: str,
        context: str,
        session: ChatSession
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenRouter API."""
        system_prompt = f"""You are TreeTalk, a genealogical AI assistant that helps people explore their family history. 
You have access to the user's genealogical database and can answer questions about their family tree.

Current family context:
{context}

Guidelines:
- Provide accurate information based only on the available family data
- If you don't have specific information, say so clearly
- Suggest related questions or family members to explore
- Be conversational and engaging
- Focus on family history, relationships, and genealogical connections
- Always cite your information as coming from "your family tree data"

Remember: You can only access the family data provided in the context above. You cannot access external databases or make up information."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history
        recent_messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.timestamp.asc()).limit(10).all()
        
        for msg in recent_messages:
            role = "user" if msg.message_type == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def _call_openrouter_api(
        self,
        messages: List[Dict[str, str]],
        model: str
    ) -> Dict[str, Any]:
        """Call OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.openrouter_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API request failed with status {response.status_code}: {response.text}"
                }
    
    async def _save_messages(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        response_time: float,
        model: str,
        tokens: int
    ):
        """Save messages to database."""
        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            message_type="user",
            content=user_message
        )
        self.db.add(user_msg)
        
        # Save AI response
        ai_msg = ChatMessage(
            session_id=session_id,
            message_type="assistant",
            content=ai_response,
            response_time_ms=int(response_time),
            token_count=tokens,
            model_used=model
        )
        self.db.add(ai_msg)
        
        self.db.commit()
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return []
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        return [
            {
                "type": msg.message_type,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "response_time_ms": msg.response_time_ms,
                "tokens": msg.token_count
            }
            for msg in messages
        ]