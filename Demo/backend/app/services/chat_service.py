from typing import List, Dict, Optional
from app.services.family_data import FamilyDataService
import random

class ChatService:
    def __init__(self, family_service: FamilyDataService):
        self.family_service = family_service
        self.conversation_history = []
        
        # Predefined responses for demo purposes
        self.response_templates = {
            "greeting": [
                "Hello! I'm here to help you explore the Dupont family history. What would you like to know?",
                "Welcome to TreeChat! I can tell you about the Dupont family. How can I assist you today?"
            ],
            "person_info": [
                "{name} was born on {birth_date} in {birth_place}. {additional_info}",
                "Let me tell you about {name}. Born {birth_date} in {birth_place}. {additional_info}"
            ],
            "family_relations": [
                "{person} had {count} children: {children}.",
                "The children of {person} are: {children}."
            ],
            "search_results": [
                "I found {count} person(s) matching '{query}': {results}",
                "Here are the people I found for '{query}': {results}"
            ],
            "unknown": [
                "I'm not sure about that. Could you ask me something about the Dupont family?",
                "I don't have information about that. Try asking about Jean, Marie, Pierre, or other family members."
            ]
        }
    
    def process_message(self, message: str) -> Dict:
        """Process a chat message and return a response"""
        message_lower = message.lower()
        
        # Add to conversation history
        self.conversation_history.append({"type": "user", "message": message})
        
        response = self._generate_response(message_lower)
        suggestions = self._generate_suggestions(message_lower)
        
        # Add response to history
        self.conversation_history.append({"type": "assistant", "message": response})
        
        return {
            "response": response,
            "suggestions": suggestions,
            "timestamp": "2024-01-01T00:00:00Z"  # Mock timestamp
        }
    
    def _generate_response(self, message: str) -> str:
        """Generate a contextual response based on the message"""
        
        # Greeting detection
        if any(word in message for word in ["hello", "hi", "bonjour", "salut"]):
            return random.choice(self.response_templates["greeting"])
        
        # Person search
        persons = self.family_service.search_persons(message)
        if persons:
            if len(persons) == 1:
                person = persons[0]
                additional_info = ""
                if person.spouse:
                    spouse = self.family_service.get_person_by_id(person.spouse)
                    if spouse:
                        additional_info += f" Married to {spouse.full_name}."
                if person.children:
                    additional_info += f" Has {len(person.children)} children."
                if not person.is_alive and person.death_date:
                    additional_info += f" Passed away on {person.death_date}."
                
                return self.response_templates["person_info"][0].format(
                    name=person.full_name,
                    birth_date=person.birth_date,
                    birth_place=person.birth_place or "unknown location",
                    additional_info=additional_info
                )
            else:
                results = ", ".join([p.full_name for p in persons])
                return self.response_templates["search_results"][0].format(
                    count=len(persons),
                    query=message,
                    results=results
                )
        
        # Family relationship queries
        if "children" in message or "enfants" in message:
            # Look for a person mentioned in the message
            for person in self.family_service.get_all_persons():
                if person.first_name.lower() in message or person.last_name.lower() in message:
                    if person.children:
                        children_names = []
                        for child_id in person.children:
                            child = self.family_service.get_person_by_id(child_id)
                            if child:
                                children_names.append(child.full_name)
                        return self.response_templates["family_relations"][0].format(
                            person=person.full_name,
                            count=len(children_names),
                            children=", ".join(children_names)
                        )
        
        # Ancestors/descendants queries
        if "ancestors" in message or "ancêtres" in message:
            for person in self.family_service.get_all_persons():
                if person.first_name.lower() in message:
                    ancestors = self.family_service.get_ancestors(person.id)
                    if ancestors:
                        ancestor_names = [a.full_name for a in ancestors]
                        return f"The ancestors of {person.full_name} are: {', '.join(ancestor_names)}"
        
        if "descendants" in message or "descendants" in message:
            for person in self.family_service.get_all_persons():
                if person.first_name.lower() in message:
                    descendants = self.family_service.get_descendants(person.id)
                    if descendants:
                        descendant_names = [d.full_name for d in descendants]
                        return f"The descendants of {person.full_name} are: {', '.join(descendant_names)}"
        
        # Default response
        return random.choice(self.response_templates["unknown"])
    
    def _generate_suggestions(self, message: str) -> List[str]:
        """Generate follow-up question suggestions"""
        suggestions = [
            "Tell me about Jean Dupont",
            "Who are Pierre's children?",
            "Show me the family tree",
            "Search for Marie",
            "What do you know about the Bernard family?"
        ]
        
        # Contextual suggestions based on the message
        if "jean" in message.lower():
            suggestions = [
                "Tell me about Marie Durand, Jean's wife",
                "Who are Jean's children?",
                "What do you know about Jean's grandchildren?"
            ]
        elif "pierre" in message.lower():
            suggestions = [
                "Tell me about Anne Martin, Pierre's wife",
                "Who are Pierre's parents?",
                "What about Pierre's siblings?"
            ]
        elif "family tree" in message.lower():
            suggestions = [
                "Tell me about the oldest generation",
                "Who has the most children?",
                "Show me all the grandchildren"
            ]
        
        return random.sample(suggestions, min(3, len(suggestions)))
    
    def get_conversation_history(self) -> List[Dict]:
        """Return the conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = []