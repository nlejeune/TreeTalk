"""
Chat Service - Conversational AI Integration with OpenRouter

This service handles chat functionality for the TreeTalk application,
integrating with OpenRouter API for LLM interactions while providing
genealogical context from the database.

Key Features:
- OpenRouter API integration for multiple LLM models
- Genealogical context preparation and injection
- Chat session and message management
- Response processing and citation handling
"""

import httpx
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from models.person import Person
from models.configuration import Configuration
from services.family_service import FamilyService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service class for conversational AI functionality.
    
    This service handles:
    - Chat session management
    - OpenRouter API integration
    - Genealogical context preparation
    - Message history and conversation flow
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize the chat service.
        
        Args:
            db_session (AsyncSession): Database session for chat operations
        """
        self.db = db_session
        self.family_service = FamilyService(db_session)
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        
    async def send_message(self, session_id: UUID, message: str, 
                          model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to the chat session and get AI response.
        
        Args:
            session_id (UUID): Chat session ID
            message (str): User message content
            model_name (str, optional): Override default model for this message
            
        Returns:
            Dict[str, Any]: Chat response with message data and metadata
        """
        try:
            start_time = datetime.now()
            
            # Get or create chat session
            session = await self._get_or_create_session(session_id)
            
            # Save user message
            user_message = await self._save_message(
                session_id=session.id,
                message_type="user",
                content=message,
                sequence_number=session.message_count + 1
            )
            
            # Prepare genealogical context
            context_data = await self._prepare_genealogical_context(session, message)
            
            # Get AI response
            ai_response, response_metadata = await self._get_ai_response(
                session, message, context_data, model_name
            )
            
            # Save AI message
            ai_message = await self._save_message(
                session_id=session.id,
                message_type="assistant",
                content=ai_response,
                sequence_number=session.message_count + 2,
                model_used=response_metadata.get("model_used"),
                tokens_used=response_metadata.get("tokens_used"),
                response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                genealogy_context=context_data,
                cited_sources=response_metadata.get("cited_sources", [])
            )
            
            # Update session
            session.message_count += 2
            session.last_activity = datetime.utcnow()
            await self.db.commit()
            
            # Prepare response
            response_data = {
                "session_id": str(session.id),
                "user_message": user_message.to_dict(),
                "ai_message": ai_message.to_dict(),
                "context_used": bool(context_data),
                "response_metadata": response_metadata
            }
            
            logger.info(f"Chat message processed for session {session_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to process chat message: {e}")
            
            # Save error message
            try:
                await self._save_error_message(
                    session_id, f"Sorry, I encountered an error: {str(e)}"
                )
            except Exception:
                pass
            
            raise
    
    async def get_chat_history(self, session_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get chat message history for a session.
        
        Args:
            session_id (UUID): Chat session ID
            limit (int): Maximum number of messages to return
            
        Returns:
            List[Dict[str, Any]]: List of chat messages
        """
        try:
            result = await self.db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(desc(ChatMessage.sequence_number))
                .limit(limit)
            )
            
            messages = result.scalars().all()
            message_data = [msg.to_dict() for msg in reversed(messages)]
            
            logger.info(f"Retrieved {len(message_data)} messages for session {session_id}")
            return message_data
            
        except Exception as e:
            logger.error(f"Failed to get chat history for {session_id}: {e}")
            raise
    
    async def create_chat_session(self, title: Optional[str] = None,
                                focused_person_id: Optional[UUID] = None,
                                active_source_id: Optional[UUID] = None,
                                model_name: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            title (str, optional): Session title
            focused_person_id (UUID, optional): Person to focus chat on
            active_source_id (UUID, optional): Active data source
            model_name (str, optional): AI model to use
            
        Returns:
            ChatSession: Created chat session
        """
        try:
            # Get default model if not specified
            if not model_name:
                model_name = await self._get_default_model()
            
            # Create session
            session = ChatSession(
                title=title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                focused_person_id=focused_person_id,
                active_source_id=active_source_id,
                model_name=model_name,
                system_prompt=self._get_system_prompt()
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"Created chat session: {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available AI models from OpenRouter.
        
        Returns:
            List[Dict[str, Any]]: List of available models with metadata
        """
        try:
            api_key = await self._get_openrouter_api_key()
            if not api_key:
                return []
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://treetalk.ai",
                "X-Title": "TreeTalk"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openrouter_base_url}/models",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                
                models_data = response.json()
                
                # Filter and sort models
                filtered_models = []
                for model in models_data.get("data", []):
                    model_info = {
                        "id": model.get("id"),
                        "name": model.get("name", model.get("id")),
                        "pricing": model.get("pricing", {}),
                        "context_length": model.get("context_length", 0),
                        "description": model.get("description", "")
                    }
                    
                    # Calculate cost per 1K tokens
                    pricing = model.get("pricing", {})
                    if "prompt" in pricing:
                        cost_per_1k = float(pricing["prompt"]) * 1000
                        model_info["cost_per_1k_tokens"] = cost_per_1k
                    
                    filtered_models.append(model_info)
                
                # Sort by cost (free models first)
                filtered_models.sort(key=lambda x: x.get("cost_per_1k_tokens", 0))
                
                logger.info(f"Retrieved {len(filtered_models)} available models")
                return filtered_models
                
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def _get_or_create_session(self, session_id: UUID) -> ChatSession:
        """Get existing session or create new one."""
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            # Create new session
            session = await self.create_chat_session()
        
        return session
    
    async def _save_message(self, session_id: UUID, message_type: str, content: str,
                           sequence_number: int, **kwargs) -> ChatMessage:
        """Save chat message to database."""
        message = ChatMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            sequence_number=sequence_number,
            **kwargs
        )
        
        self.db.add(message)
        await self.db.flush()
        return message
    
    async def _save_error_message(self, session_id: UUID, error_content: str):
        """Save error message to chat history."""
        session = await self._get_or_create_session(session_id)
        
        await self._save_message(
            session_id=session_id,
            message_type="assistant",
            content=error_content,
            sequence_number=session.message_count + 1,
            is_error=True
        )
        
        session.message_count += 1
        await self.db.commit()
    
    async def _prepare_genealogical_context(self, session: ChatSession, 
                                          message: str) -> Dict[str, Any]:
        """Prepare genealogical context for AI prompt."""
        context = {}
        
        try:
            # Include focused person information
            if session.focused_person_id:
                person_details = await self.family_service.get_person_details(
                    session.focused_person_id,
                    include_events=True,
                    include_relationships=True
                )
                context["focused_person"] = person_details
            
            # Include family tree context if relevant
            if session.focused_person_id and ("family" in message.lower() or 
                                            "relative" in message.lower() or
                                            "ancestor" in message.lower() or
                                            "descendant" in message.lower()):
                family_tree = await self.family_service.get_family_tree(
                    session.focused_person_id, max_generations=3
                )
                context["family_tree"] = {
                    "persons": family_tree["persons"][:20],  # Limit for context size
                    "relationships": family_tree["relationships"][:30]
                }
            
            # Search for relevant persons if names mentioned
            potential_names = self._extract_names_from_message(message)
            if potential_names and session.active_source_id:
                relevant_persons = []
                for name in potential_names[:3]:  # Limit searches
                    persons = await self.family_service.search_persons(
                        name, session.active_source_id, limit=5
                    )
                    relevant_persons.extend(persons[:2])
                
                if relevant_persons:
                    context["mentioned_persons"] = relevant_persons
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare genealogical context: {e}")
            return {}
    
    async def _get_ai_response(self, session: ChatSession, message: str,
                             context_data: Dict[str, Any], 
                             model_override: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Get AI response from OpenRouter."""
        try:
            api_key = await self._get_openrouter_api_key()
            if not api_key:
                raise ValueError("OpenRouter API key not configured")
            
            model_name = model_override or session.model_name or "openai/gpt-3.5-turbo"
            
            # Build conversation history
            messages = [
                {"role": "system", "content": self._build_system_prompt(context_data)}
            ]
            
            # Add recent conversation history
            recent_messages = await self._get_recent_messages(session.id, limit=10)
            for msg in recent_messages:
                role = "user" if msg.message_type == "user" else "assistant"
                messages.append({"role": role, "content": msg.content})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://treetalk.ai",
                "X-Title": "TreeTalk",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": session.temperature or 0.7,
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openrouter_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                response_data = response.json()
                
                # Extract response and metadata
                ai_message = response_data["choices"][0]["message"]["content"]
                
                metadata = {
                    "model_used": response_data.get("model", model_name),
                    "tokens_used": response_data.get("usage", {}).get("total_tokens", 0),
                    "cited_sources": []  # Could be enhanced to extract citations
                }
                
                return ai_message, metadata
                
        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            return f"I'm sorry, I encountered an error processing your request: {str(e)}", {}
    
    def _build_system_prompt(self, context_data: Dict[str, Any]) -> str:
        """Build system prompt with genealogical context."""
        base_prompt = """You are TreeTalk, an AI assistant specializing in genealogy and family history. 
You help users explore and understand their family trees through natural conversation.

Key guidelines:
- Base your responses on the provided genealogical data only
- Be helpful and conversational while remaining accurate
- Suggest follow-up questions to encourage exploration
- Always cite your sources when mentioning specific people or facts
- If information is not available in the data, clearly state this

"""
        
        if context_data:
            base_prompt += "\n**Current Context:**\n"
            
            if "focused_person" in context_data:
                person = context_data["focused_person"]
                base_prompt += f"- Focused Person: {person.get('full_name')} ({person.get('life_span')})\n"
            
            if "family_tree" in context_data:
                tree = context_data["family_tree"]
                base_prompt += f"- Family Tree: {len(tree['persons'])} related persons available\n"
            
            if "mentioned_persons" in context_data:
                persons = context_data["mentioned_persons"]
                base_prompt += f"- Mentioned Persons: {len(persons)} potentially relevant persons found\n"
        
        return base_prompt
    
    async def _get_recent_messages(self, session_id: UUID, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages for conversation context."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.is_error == False)
            .order_by(desc(ChatMessage.sequence_number))
            .limit(limit)
        )
        
        messages = result.scalars().all()
        return list(reversed(messages))
    
    async def _get_openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key from configuration."""
        return await Configuration.get_value(self.db, "openrouter_api_key")
    
    async def _get_default_model(self) -> str:
        """Get default AI model from configuration."""
        return await Configuration.get_value(self.db, "default_model", "openai/gpt-3.5-turbo")
    
    def _get_system_prompt(self) -> str:
        """Get base system prompt template."""
        return "You are TreeTalk, an AI assistant for exploring family history and genealogy."
    
    def _extract_names_from_message(self, message: str) -> List[str]:
        """Extract potential person names from user message."""
        # Simple name extraction - could be enhanced with NLP
        words = message.split()
        potential_names = []
        
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                # Check if next word is also capitalized (likely a full name)
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    potential_names.append(f"{word} {words[i + 1]}")
                else:
                    potential_names.append(word)
        
        return list(set(potential_names))[:5]  # Return unique names, max 5