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
                logger.warning("No OpenRouter API key configured, returning default models")
                return self._get_default_models()
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://treetalk.ai",
                "X-Title": "TreeTalk"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.openrouter_base_url}/models",
                    headers=headers,
                    timeout=15.0
                )
                response.raise_for_status()
                
                models_data = response.json()
                logger.info(f"Received {len(models_data.get('data', []))} models from OpenRouter API")
                
                # Filter and process models
                filtered_models = []
                for model in models_data.get("data", []):
                    # Skip models without pricing information or that are not available
                    if not model.get("pricing") or model.get("pricing", {}).get("prompt") is None:
                        continue
                    
                    # Calculate cost per 1K tokens (OpenRouter pricing is per token)
                    pricing = model.get("pricing", {})
                    prompt_cost = float(pricing.get("prompt", "0"))
                    completion_cost = float(pricing.get("completion", "0"))
                    
                    # Use average of prompt and completion for display (per 1K tokens)
                    cost_per_1k_tokens = ((prompt_cost + completion_cost) / 2) * 1000
                    
                    model_info = {
                        "id": model.get("id"),
                        "name": model.get("name", model.get("id")),
                        "cost_per_1k_tokens": round(cost_per_1k_tokens, 4),
                        "context_length": model.get("context_length", 0),
                        "description": model.get("description", ""),
                        "pricing": {
                            "prompt": prompt_cost,
                            "completion": completion_cost
                        }
                    }
                    
                    filtered_models.append(model_info)
                
                # Sort by cost (free/cheaper models first)
                filtered_models.sort(key=lambda x: x.get("cost_per_1k_tokens", 0))
                
                logger.info(f"Processed {len(filtered_models)} available models with pricing")
                return filtered_models
                
        except Exception as e:
            logger.error(f"Failed to get available models from OpenRouter: {e}")
            # Return default models on error
            return self._get_default_models()
    
    def _get_default_models(self) -> List[Dict[str, Any]]:
        """Return default models when OpenRouter API is not available."""
        models = [
            {
                "id": "meta-llama/llama-3.1-8b-instruct:free",
                "name": "Llama 3.1 8B Instruct (Free)",
                "cost_per_1k_tokens": 0.0,
                "context_length": 131072,
                "description": "Free open-source model with good performance",
                "pricing": {"prompt": 0.0, "completion": 0.0}
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini",
                "cost_per_1k_tokens": 0.0002,
                "context_length": 128000,
                "description": "Affordable small model with high intelligence",
                "pricing": {"prompt": 0.00000015, "completion": 0.0000006}
            },
            {
                "id": "anthropic/claude-3-haiku",
                "name": "Claude 3 Haiku",
                "cost_per_1k_tokens": 0.0008,
                "context_length": 200000,
                "description": "Fastest model with strong performance",
                "pricing": {"prompt": 0.00000025, "completion": 0.00000125}
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "cost_per_1k_tokens": 0.002,
                "context_length": 4096,
                "description": "Fast and efficient model for general conversation",
                "pricing": {"prompt": 0.000001, "completion": 0.000002}
            }
        ]
        # Ensure models are sorted by cost (free first)
        models.sort(key=lambda x: x.get("cost_per_1k_tokens", 0))
        return models
    
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
            # Search for relevant persons if names mentioned (do this first)
            potential_names = self._extract_names_from_message(message)
            mentioned_persons = []
            
            if potential_names:
                for name in potential_names[:3]:  # Limit searches
                    persons = await self.family_service.search_persons(
                        name, session.active_source_id, limit=5
                    )
                    for person in persons[:2]:  # Top 2 matches per name
                        # Get detailed information for each mentioned person
                        try:
                            person_details = await self.family_service.get_person_details(
                                person['id'],
                                include_events=True,
                                include_relationships=True
                            )
                            mentioned_persons.append(person_details)
                        except Exception as e:
                            logger.warning(f"Could not get details for person {person['id']}: {e}")
                            mentioned_persons.append(person)
                
                if mentioned_persons:
                    context["mentioned_persons"] = mentioned_persons
            
            # Include focused person information (expand if someone was mentioned)
            if session.focused_person_id:
                person_details = await self.family_service.get_person_details(
                    session.focused_person_id,
                    include_events=True,
                    include_relationships=True
                )
                context["focused_person"] = person_details
            
            # Include family tree context more broadly (not just for specific keywords)
            family_keywords = [
                "family", "relative", "ancestor", "descendant", "parent", "child", 
                "mother", "father", "son", "daughter", "brother", "sister",
                "grandmother", "grandfather", "grandson", "granddaughter",
                "uncle", "aunt", "nephew", "niece", "cousin", "spouse", "wife", "husband",
                "born", "died", "married", "children", "relationship", "related"
            ]
            
            if (session.focused_person_id and 
                any(keyword in message.lower() for keyword in family_keywords)):
                
                try:
                    family_tree = await self.family_service.get_family_tree(
                        session.focused_person_id, max_generations=3
                    )
                    context["family_tree"] = {
                        "persons": family_tree["persons"][:20],  # Limit for context size
                        "relationships": family_tree["relationships"][:30]
                    }
                except Exception as e:
                    logger.warning(f"Could not get family tree for focused person: {e}")
            
            # If we found mentioned persons but no focused person, set the first mentioned as context
            elif mentioned_persons and not session.focused_person_id:
                try:
                    primary_person = mentioned_persons[0]
                    family_tree = await self.family_service.get_family_tree(
                        primary_person['id'], max_generations=2
                    )
                    context["family_tree"] = {
                        "persons": family_tree["persons"][:15],
                        "relationships": family_tree["relationships"][:20]
                    }
                except Exception as e:
                    logger.warning(f"Could not get family tree for mentioned person: {e}")
            
            # Log context preparation for debugging
            logger.info(f"Prepared context with: "
                       f"focused_person={'focused_person' in context}, "
                       f"family_tree={'family_tree' in context}, "
                       f"mentioned_persons={len(mentioned_persons)} persons")
            
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
            
            # Validate API key format (basic check)
            if not api_key.strip() or len(api_key.strip()) < 10:
                raise ValueError("OpenRouter API key appears to be invalid or corrupted")
            
            model_name = model_override or session.model_name or "openai/gpt-3.5-turbo"
            logger.info(f"Making API request to OpenRouter with model: {model_name}")
            
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
                "Authorization": f"Bearer {api_key.strip()}",
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
                
                # Enhanced error handling for different HTTP status codes
                if response.status_code == 401:
                    logger.error("OpenRouter API key authentication failed - key may be invalid")
                    raise ValueError("OpenRouter API key is invalid or expired. Please check your API key configuration.")
                elif response.status_code == 429:
                    logger.error("OpenRouter API rate limit exceeded")
                    raise ValueError("Rate limit exceeded. Please try again later.")
                elif response.status_code == 402:
                    logger.error("OpenRouter API insufficient credits")
                    raise ValueError("Insufficient credits in your OpenRouter account. Please add credits.")
                
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
        base_prompt = """You are TreeTalk, a specialized AI assistant for exploring family history data stored in a PostgreSQL database.

**CRITICAL INSTRUCTIONS - MUST FOLLOW:**

1. **DATABASE-ONLY RESPONSES**: You MUST only provide information that exists in the provided genealogical database context. DO NOT use any external knowledge, internet information, or general historical facts.

2. **NO HALLUCINATION**: If you don't have specific information about a person, date, place, or relationship in the provided data, you MUST say "I don't have that information in your family tree data" rather than guessing or providing general information.

3. **EXACT DATA ONLY**: When providing facts (names, dates, places, relationships), use EXACTLY what appears in the database. Do not embellish, correct, or add details that aren't explicitly provided.

4. **CLEAR LIMITATIONS**: If the user asks about information not available in the context data, clearly explain that you can only access their uploaded family tree data, not external historical records or internet sources.

5. **CITE SOURCES**: Always reference which person or relationship in their tree the information comes from (e.g., "According to your family tree data for John Smith...")

6. **DATA VALIDATION**: If data appears incomplete or uncertain in the database (like partial dates or approximate years), acknowledge this uncertainty explicitly.

**RESPONSE FORMAT:**
- Start responses with references to "your family tree data" or "in your genealogical database"
- Use phrases like "Based on the information in your tree..." 
- End with suggestions for exploring related family members when appropriate
- If no relevant data exists, suggest what types of information would be helpful to add

**FORBIDDEN ACTIONS:**
- Do NOT provide biographical information from general knowledge
- Do NOT suggest historical context unless it's in the database
- Do NOT "fill in gaps" with likely scenarios or common practices
- Do NOT provide dates, places, or relationships not explicitly in the data

"""
        
        # Add specific structured data from the database
        if context_data:
            base_prompt += "\n**GENEALOGICAL DATABASE RECORDS - USE ONLY THIS DATA:**\n"
            
            if "focused_person" in context_data:
                person = context_data["focused_person"]
                base_prompt += f"\n=== PRIMARY PERSON RECORD ===\n"
                base_prompt += f"Name: {person.get('full_name', 'Unknown')}\n"
                base_prompt += f"Life Span: {person.get('life_span', 'Unknown dates')}\n"
                base_prompt += f"Gender: {person.get('gender', 'Unknown')}\n"
                
                # Add birth/death details if available
                if person.get('birth_date'):
                    base_prompt += f"Birth Date: {person.get('birth_date')}\n"
                if person.get('birth_place'):
                    base_prompt += f"Birth Place: {person.get('birth_place')}\n"
                if person.get('death_date'):
                    base_prompt += f"Death Date: {person.get('death_date')}\n"
                if person.get('death_place'):
                    base_prompt += f"Death Place: {person.get('death_place')}\n"
                
                # Add additional biographical details
                if person.get('occupation'):
                    base_prompt += f"Occupation: {person.get('occupation')}\n"
                if person.get('religion'):
                    base_prompt += f"Religion: {person.get('religion')}\n"
                if person.get('education'):
                    base_prompt += f"Education: {person.get('education')}\n"
                
                # Add events
                events = person.get('events', [])
                if events:
                    base_prompt += f"\nLife Events ({len(events)}):\n"
                    for event in events[:8]:  # Increased limit for events
                        event_desc = f"  - {event.get('event_type', 'Unknown')}"
                        if event.get('event_date'):
                            event_desc += f" on {event.get('event_date')}"
                        if event.get('place'):
                            event_desc += f" at {event.get('place')}"
                        if event.get('description'):
                            event_desc += f": {event.get('description')}"
                        base_prompt += event_desc + "\n"
                
                # Enhanced relationships with detailed family structure
                relationships = person.get('relationships', [])
                if relationships:
                    base_prompt += f"\nFamily Relationships ({len(relationships)}):\n"
                    
                    # Group relationships by type for better organization
                    parents = []
                    children = []
                    spouses = []
                    siblings = []
                    other_relations = []
                    
                    for rel in relationships:
                        rel_type = rel.get('relationship_type', 'Unknown')
                        other_person = rel.get('other_person', {})
                        description = rel.get('description', rel_type)
                        
                        rel_info = {
                            'name': other_person.get('full_name', 'Unknown'),
                            'life_span': other_person.get('life_span', 'dates unknown'),
                            'birth_place': other_person.get('birth_place'),
                            'death_place': other_person.get('death_place'),
                            'occupation': other_person.get('occupation'),
                            'description': description,
                            'rel': rel
                        }
                        
                        if 'parent' in description.lower() or 'father' in description.lower() or 'mother' in description.lower():
                            parents.append(rel_info)
                        elif 'child' in description.lower() or 'son' in description.lower() or 'daughter' in description.lower():
                            children.append(rel_info)
                        elif 'spouse' in description.lower() or 'husband' in description.lower() or 'wife' in description.lower():
                            spouses.append(rel_info)
                        elif 'sibling' in description.lower() or 'brother' in description.lower() or 'sister' in description.lower():
                            siblings.append(rel_info)
                        else:
                            other_relations.append(rel_info)
                    
                    if parents:
                        base_prompt += "  Parents:\n"
                        for parent in parents:
                            parent_info = f"    - {parent['description'].title()}: {parent['name']} ({parent['life_span']})"
                            if parent['birth_place']:
                                parent_info += f", born in {parent['birth_place']}"
                            if parent['occupation']:
                                parent_info += f", {parent['occupation']}"
                            base_prompt += parent_info + "\n"
                    
                    if spouses:
                        base_prompt += "  Spouses:\n"
                        for spouse in spouses:
                            spouse_info = f"    - {spouse['description'].title()}: {spouse['name']} ({spouse['life_span']})"
                            if spouse['birth_place']:
                                spouse_info += f", born in {spouse['birth_place']}"
                            # Add marriage details if available
                            if spouse['rel'].get('marriage_date'):
                                spouse_info += f", married {spouse['rel'].get('marriage_date')}"
                                if spouse['rel'].get('marriage_place_id'):
                                    spouse_info += f" at {spouse['rel'].get('marriage_place_id')}"
                            base_prompt += spouse_info + "\n"
                    
                    if siblings:
                        base_prompt += "  Siblings:\n"
                        for sibling in siblings:
                            sibling_info = f"    - {sibling['description'].title()}: {sibling['name']} ({sibling['life_span']})"
                            if sibling['birth_place']:
                                sibling_info += f", born in {sibling['birth_place']}"
                            if sibling['occupation']:
                                sibling_info += f", {sibling['occupation']}"
                            base_prompt += sibling_info + "\n"
                    
                    if children:
                        base_prompt += "  Children:\n"
                        for child in children:
                            child_info = f"    - {child['description'].title()}: {child['name']} ({child['life_span']})"
                            if child['birth_place']:
                                child_info += f", born in {child['birth_place']}"
                            if child['occupation']:
                                child_info += f", {child['occupation']}"
                            base_prompt += child_info + "\n"
                    
                    if other_relations:
                        base_prompt += "  Other Relations:\n"
                        for rel in other_relations:
                            rel_info = f"    - {rel['description'].title()}: {rel['name']} ({rel['life_span']})"
                            if rel['birth_place']:
                                rel_info += f", born in {rel['birth_place']}"
                            base_prompt += rel_info + "\n"
            
            if "family_tree" in context_data:
                tree = context_data["family_tree"]
                base_prompt += f"\n=== EXTENDED FAMILY TREE CONTEXT ===\n"
                base_prompt += f"Connected Persons: {len(tree.get('persons', []))}\n"
                base_prompt += f"Family Relationships: {len(tree.get('relationships', []))}\n"
                
                # Enhanced family tree display with more details
                persons = tree.get('persons', [])
                if persons:
                    base_prompt += "Extended Family Members:\n"
                    for person in persons[:12]:  # Show more family members
                        person_line = f"  - {person.get('display_name', 'Unknown')} ({person.get('life_span', 'dates unknown')})"
                        if person.get('birth_place'):
                            person_line += f", born in {person['birth_place']}"
                        if person.get('occupation'):
                            person_line += f", {person['occupation']}"
                        base_prompt += person_line + "\n"
                
                # Add relationship details from family tree
                relationships = tree.get('relationships', [])
                if relationships:
                    base_prompt += f"\nFamily Connections:\n"
                    for rel in relationships[:15]:  # Show more relationships
                        rel_line = f"  - {rel.get('relationship_type', 'Unknown')} relationship"
                        if rel.get('person1_name') and rel.get('person2_name'):
                            rel_line = f"  - {rel.get('person1_name')} is {rel.get('relationship_type', 'related to')} {rel.get('person2_name')}"
                        base_prompt += rel_line + "\n"
            
            if "mentioned_persons" in context_data:
                persons = context_data["mentioned_persons"]
                base_prompt += f"\n=== DETAILED SEARCH RESULTS ===\n"
                base_prompt += f"Persons matching search criteria: {len(persons)}\n"
                for person in persons:
                    base_prompt += f"\n--- {person.get('display_name', 'Unknown')} ---\n"
                    base_prompt += f"Life Span: {person.get('life_span', 'dates unknown')}\n"
                    
                    # Birth information
                    if person.get('birth_date') or person.get('birth_place'):
                        birth_info = "Birth: "
                        if person.get('birth_date'):
                            birth_info += f"{person['birth_date']}"
                        if person.get('birth_place'):
                            birth_info += f" in {person['birth_place']}"
                        base_prompt += birth_info + "\n"
                    
                    # Death information
                    if person.get('death_date') or person.get('death_place'):
                        death_info = "Death: "
                        if person.get('death_date'):
                            death_info += f"{person['death_date']}"
                        if person.get('death_place'):
                            death_info += f" in {person['death_place']}"
                        base_prompt += death_info + "\n"
                    
                    # Additional details
                    if person.get('occupation'):
                        base_prompt += f"Occupation: {person['occupation']}\n"
                    if person.get('religion'):
                        base_prompt += f"Religion: {person['religion']}\n"
                    
                    # Family relationships for mentioned persons
                    if person.get('relationships'):
                        base_prompt += f"Family: "
                        family_members = []
                        for rel in person['relationships'][:6]:  # Limit to 6 key relationships
                            other_person = rel.get('other_person', {})
                            if other_person.get('full_name'):
                                family_members.append(f"{rel.get('description', 'related to')} {other_person['full_name']}")
                        if family_members:
                            base_prompt += ", ".join(family_members) + "\n"
        
        base_prompt += "\n**REMINDER**: This is ALL the data available. Do not add information not explicitly listed above. If asked about details not present in this data, clearly state that the information is not available in the family tree database.\n"
        
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