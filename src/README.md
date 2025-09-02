# TreeTalk Application

TreeTalk is an innovative genealogy application that transforms how you explore and interact with your family history by combining conversational AI with comprehensive genealogical data management.

## Architecture

- **Frontend**: Streamlit web application with family tree visualization
- **Backend**: FastAPI REST API with PostgreSQL database
- **Database**: PostgreSQL with comprehensive genealogical schema
- **Chat AI**: OpenRouter API integration for conversational interface
- **Deployment**: Docker containers with docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenRouter API key (for chat functionality)

### Setup

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` file and add your configuration:
   - Set a secure database password
   - Add your OpenRouter API key
   - Optionally add FamilySearch client ID

3. Start the application:
```bash
docker-compose up -d
```

4. Access the application:
   - Frontend (Streamlit): http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### First Steps

1. Upload a GEDCOM file in the "GEDCOM Management" tab
2. Configure your OpenRouter API key in the "Configuration" tab
3. Explore your family tree in the "Data Exploration" tab
4. Chat with your family history data using natural language

## Development

### Local Development

For local development without Docker:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start PostgreSQL and Redis locally

3. Set environment variables from `.env` file

4. Start the backend:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

5. Start the frontend:
```bash
cd frontend
streamlit run main.py --server.port 8501
```

### Project Structure

```
src/
├── backend/           # FastAPI backend application
│   ├── models/        # SQLAlchemy database models
│   ├── routes/        # API endpoint routes
│   ├── services/      # Business logic services
│   └── utils/         # Utility functions
├── frontend/          # Streamlit frontend application
├── shared/            # Shared utilities and types
├── docker-compose.yml # Container orchestration
└── requirements.txt   # Python dependencies
```

## Features

### Current Features (MVP)

- ✅ GEDCOM file import and parsing
- ✅ PostgreSQL genealogical database
- ✅ Interactive family tree visualization
- ✅ Person search and filtering
- ✅ Chat interface with OpenRouter API
- ✅ Docker deployment
- ✅ Configuration management

### Planned Features

- [ ] Advanced family tree layouts
- [ ] FamilySearch API integration
- [ ] User authentication and multi-user support
- [ ] Media file management
- [ ] Advanced search and filtering
- [ ] Data export capabilities
- [ ] Mobile-responsive interface

## API Documentation

The FastAPI backend provides a comprehensive REST API. Once the backend is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI specification**: http://localhost:8000/openapi.json

### Key Endpoints

- `GET /api/sources` - List GEDCOM sources
- `POST /api/import/gedcom` - Upload GEDCOM file
- `GET /api/persons` - List persons with filtering
- `GET /api/persons/{id}/family-tree` - Get family tree visualization data
- `POST /api/chat/message` - Send chat message
- `POST /api/config/openrouter` - Configure OpenRouter API

## Database Schema

The application uses a comprehensive PostgreSQL schema designed for genealogical data:

- **persons**: Individual records with biographical data
- **relationships**: Family connections and relationships
- **sources**: Data provenance tracking
- **events**: Life events and milestones
- **places**: Geographical location data
- **chat_sessions/chat_messages**: Conversation history

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DB_PASSWORD` | PostgreSQL password | Yes |
| `OPENROUTER_API_KEY` | OpenRouter API key for chat | Yes |
| `FAMILYSEARCH_CLIENT_ID` | FamilySearch client ID | No |
| `DATABASE_URL` | Full database connection string | Yes |
| `BACKEND_URL` | Backend API URL for frontend | Yes |

### OpenRouter API

To use the chat functionality, you need an OpenRouter API key:

1. Sign up at https://openrouter.ai/
2. Get your API key from the dashboard
3. Add it to your `.env` file or configure it in the app

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check PostgreSQL container is running
   - Verify DATABASE_URL in environment

2. **Chat not working**
   - Ensure OPENROUTER_API_KEY is configured
   - Check API key is valid in configuration tab

3. **GEDCOM import fails**
   - Verify file is valid GEDCOM format (.ged)
   - Check backend logs for parsing errors

4. **Frontend can't connect to backend**
   - Ensure backend is running on port 8000
   - Check BACKEND_URL configuration

### Logs

View application logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the GNU GPLv3 License - see the LICENSE file for details.