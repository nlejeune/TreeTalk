from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from app.routes.api import api
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'treechat-demo-secret-key'
    
    # Enable CORS for all routes
    CORS(app, origins=["http://localhost:3000"])
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000")
    
    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/')
    def index():
        return {
            "message": "TreeChat Demo Backend API",
            "version": "0.1.0",
            "endpoints": [
                "/api/health",
                "/api/persons",
                "/api/family-tree",
                "/api/chat",
                "/api/sources"
            ]
        }
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('status', {'message': 'Connected to TreeChat Demo'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Handle real-time chat messages via WebSocket"""
        from app.services.family_data import FamilyDataService
        from app.services.chat_service import ChatService
        
        family_service = FamilyDataService()
        chat_service = ChatService(family_service)
        
        message = data.get('message', '')
        if message:
            response = chat_service.process_message(message)
            emit('chat_response', response)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting TreeChat Demo Backend on port {port}")
    print("API Documentation:")
    print("- GET /api/health - Health check")
    print("- GET /api/persons - Get all persons")
    print("- GET /api/family-tree - Get family tree data")
    print("- POST /api/chat - Send chat message")
    print("- GET /api/sources - Get data sources")
    print("\nFrontend should be running on http://localhost:3000")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)