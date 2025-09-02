from flask import Blueprint, request, jsonify
from app.services.family_data import FamilyDataService
from app.services.chat_service import ChatService

# Initialize services
family_service = FamilyDataService()
chat_service = ChatService(family_service)

api = Blueprint('api', __name__)

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "TreeChat Demo API"})

@api.route('/persons', methods=['GET'])
def get_all_persons():
    """Get all persons in the family tree"""
    persons = family_service.get_all_persons()
    return jsonify({
        "persons": [person.to_dict() for person in persons],
        "count": len(persons)
    })

@api.route('/persons/<person_id>', methods=['GET'])
def get_person(person_id):
    """Get a specific person by ID"""
    person = family_service.get_person_by_id(person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    
    return jsonify(person.to_dict())

@api.route('/persons/search', methods=['GET'])
def search_persons():
    """Search for persons by name"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    results = family_service.search_persons(query)
    return jsonify({
        "results": [person.to_dict() for person in results],
        "count": len(results),
        "query": query
    })

@api.route('/family-tree', methods=['GET'])
def get_family_tree():
    """Get family tree data for visualization"""
    tree_data = family_service.get_family_tree_data()
    return jsonify(tree_data)

@api.route('/persons/<person_id>/ancestors', methods=['GET'])
def get_ancestors(person_id):
    """Get ancestors of a specific person"""
    ancestors = family_service.get_ancestors(person_id)
    return jsonify({
        "ancestors": [person.to_dict() for person in ancestors],
        "count": len(ancestors),
        "personId": person_id
    })

@api.route('/persons/<person_id>/descendants', methods=['GET'])
def get_descendants(person_id):
    """Get descendants of a specific person"""
    descendants = family_service.get_descendants(person_id)
    return jsonify({
        "descendants": [person.to_dict() for person in descendants],
        "count": len(descendants),
        "personId": person_id
    })

@api.route('/chat', methods=['POST'])
def chat():
    """Process a chat message"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400
    
    response = chat_service.process_message(data['message'])
    return jsonify(response)

@api.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat conversation history"""
    history = chat_service.get_conversation_history()
    return jsonify({"history": history})

@api.route('/chat/history', methods=['DELETE'])
def clear_chat_history():
    """Clear chat conversation history"""
    chat_service.clear_history()
    return jsonify({"message": "Chat history cleared"})

@api.route('/sources', methods=['GET'])
def get_data_sources():
    """Get available data sources (mock data for demo)"""
    sources = [
        {
            "id": "demo_gedcom_1",
            "name": "Dupont Family GEDCOM",
            "type": "gedcom",
            "status": "active",
            "lastSync": "2024-01-01T00:00:00Z",
            "personCount": 10,
            "description": "Demo family data for TreeChat"
        },
        {
            "id": "familysearch_mock",
            "name": "FamilySearch (Demo)",
            "type": "familysearch",
            "status": "disconnected",
            "lastSync": None,
            "personCount": 0,
            "description": "Mock FamilySearch connection"
        }
    ]
    return jsonify({"sources": sources})

@api.route('/sources/<source_id>/sync', methods=['POST'])
def sync_data_source(source_id):
    """Trigger synchronization for a data source (mock)"""
    return jsonify({
        "message": f"Synchronization started for source {source_id}",
        "status": "in_progress",
        "sourceId": source_id
    })