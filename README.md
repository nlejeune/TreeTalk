# TreeTalk - Converse with Your Family History

## Overview

TreeTalk is an innovative genealogical application that transforms how you explore and interact with your family history. By combining the power of conversational artificial intelligence with comprehensive genealogical data management, TreeTalk creates an intelligent and interactive experience that makes family research as natural as having a conversation with a knowledgeable family historian.

### Key Features

- 📁 **GEDCOM Import**: Upload and parse standard GEDCOM genealogy files
- 🌳 **Interactive Family Tree**: Visualize relationships with dynamic, color-coded tree diagrams
- 💬 **AI-Powered Chat**: Ask questions about your family history in natural language
- 🔍 **Smart Search**: Find family members quickly with intelligent search and filtering
- 🎨 **Rich Visualization**: Gender-coded family trees with relationship mapping
- 🔧 **Easy Configuration**: Simple API key management for chat functionality
- 🐳 **Docker Ready**: One-command deployment with full containerization

## Architecture

TreeTalk follows a modern three-tier architecture optimized for genealogical data management:

### Frontend (Streamlit)
- **Technology**: Python 3.11+ with Streamlit framework
- **Visualization**: Plotly + NetworkX for interactive family trees
- **UI Components**: Tabbed interface with search, configuration, and file management
- **Performance**: Cached API responses and optimized rendering

### Backend (FastAPI)  
- **Technology**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Design**: RESTful endpoints with automatic documentation
- **Services**: Modular business logic for GEDCOM parsing, family operations, and chat

### Database (PostgreSQL)
- **Schema**: Comprehensive genealogical data model
- **Tables**: persons, relationships, sources, events, places, chat_sessions
- **Features**: Multi-source support, data integrity, optimized indexing
- **Performance**: Full-text search, relationship traversal optimization

### External Integrations
- **OpenRouter API**: LLM provider for conversational chat interface
- **FamilySearch API**: External genealogy data synchronization (planned)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenRouter API key (for chat functionality)
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TreeTalk
   ```

2. **Create environment configuration**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file with your configuration**
   ```env
   # Database password (change this!)
   DB_PASSWORD=your_secure_password_here
   
   # OpenRouter API key for chat functionality
   OPENROUTER_API_KEY=your_openrouter_api_key
   
   # Optional: FamilySearch integration
   FAMILYSEARCH_CLIENT_ID=your_familysearch_client_id
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - **Frontend (Streamlit)**: http://localhost:8501
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

### First Steps

1. **Upload GEDCOM File**: Go to the "GEDCOM Management" tab and upload your family tree data
2. **Configure API Key**: Set your OpenRouter API key in the "Configuration" tab  
3. **Explore Family Data**: Browse your family tree in the "Data Exploration" tab
4. **Chat with History**: Ask questions about your family using natural language

## Usage Guide

### GEDCOM File Management

TreeTalk supports standard GEDCOM (.ged) files up to 50MB in size. The application:

- Parses GEDCOM 5.5 format variations
- Validates data integrity before import
- Prevents duplicate imports
- Supports multiple GEDCOM files in the same database
- Provides cleanup tools for duplicate management

**Supported GEDCOM Features:**
- Individual records (INDI)
- Family records (FAM) 
- Birth, marriage, death events
- Parent-child relationships
- Spouse relationships
- Places and dates
- Notes and sources

### Family Tree Visualization

The interactive family tree provides:

- **Color Coding**: Blue for males, pink for females, green for unknown gender
- **Relationship Lines**: Solid lines for parent-child, dotted lines for marriages  
- **Interactive Navigation**: Click and drag, hover for details
- **Performance Optimization**: Automatic limiting for large trees
- **Search Integration**: Find and focus on specific family members

### Chat Interface

Ask natural language questions about your family history:

- "Tell me about John Smith"
- "Who are Mary's children?"
- "Show me the ancestors of the selected person"
- "What do you know about the Smith family?"

The AI responses are based exclusively on your imported family data and include source citations.

### Configuration Management

- **OpenRouter API**: Required for chat functionality
- **FamilySearch API**: Optional for external data synchronization
- **Secure Storage**: API keys are encrypted and persist across container restarts

## Development

### Local Development Setup

For development without Docker:

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker for database only
   docker run -d --name treetalk-db -e POSTGRES_DB=treetalk -e POSTGRES_USER=treetalk -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
   docker run -d --name treetalk-redis -p 6379:6379 redis:7-alpine
   ```

3. **Set environment variables**
   ```bash
   export DATABASE_URL=postgresql://treetalk:password@localhost:5432/treetalk
   export OPENROUTER_API_KEY=your_api_key
   ```

4. **Start backend server**
   ```bash
   cd src
   uvicorn backend.main:app --reload --port 8000
   ```

5. **Start frontend application**
   ```bash
   cd src  
   streamlit run frontend/main.py --server.port 8501
   ```

### Project Structure

```
src/
├── backend/                 # FastAPI backend application
│   ├── main.py             # Application entry point
│   ├── models/             # SQLAlchemy database models
│   │   ├── person.py       # Person entity model
│   │   ├── relationship.py # Family relationships
│   │   ├── source.py       # Data source tracking
│   │   ├── chat_session.py # Chat conversation storage
│   │   ├── place.py        # Geographic locations
│   │   └── event.py        # Life events and milestones
│   ├── routes/             # API endpoint routes
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── persons.py      # Person management API
│   │   ├── import_routes.py # GEDCOM import processing
│   │   ├── chat.py         # Chat interface API
│   │   ├── sources.py      # Data source management
│   │   └── config.py       # Configuration management
│   ├── services/           # Business logic services
│   │   ├── gedcom_parser.py # GEDCOM file processing
│   │   ├── family_service.py # Family tree operations
│   │   └── chat_service.py # OpenRouter integration
│   ├── utils/              # Utility functions
│   │   └── database.py     # Database connection setup
│   └── sql/
│       └── init.sql        # Database schema initialization
├── frontend/               # Streamlit frontend application
│   └── main.py            # Main UI application
├── shared/                 # Shared utilities and types
├── docker-compose.yml      # Container orchestration
└── requirements.txt        # Python dependencies
```

### API Documentation

The FastAPI backend provides comprehensive API documentation:

- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Specification**: http://localhost:8000/openapi.json

### Key API Endpoints

**Data Management:**
- `GET /api/sources` - List imported GEDCOM files
- `POST /api/import/gedcom` - Upload and import GEDCOM file
- `DELETE /api/sources/{id}` - Remove GEDCOM file and data

**Family Data:**
- `GET /api/persons` - List persons with filtering
- `GET /api/persons/{id}` - Get person details
- `GET /api/persons/{id}/family-tree` - Get family tree visualization data

**Chat Interface:**
- `POST /api/chat/message` - Send chat message and get AI response
- `GET /api/chat/sessions` - List chat conversation history

**Configuration:**
- `POST /api/config/openrouter` - Configure OpenRouter API key
- `GET /api/config/status` - Check configuration status

### Database Schema

TreeTalk uses a comprehensive PostgreSQL schema designed for genealogical data:

**Core Tables:**
- **sources**: Track data provenance (GEDCOM files, external APIs)
- **persons**: Individual records with biographical data
- **relationships**: Family connections (parent/child, spouse)
- **events**: Life events (birth, marriage, death, etc.)
- **places**: Standardized geographical locations
- **chat_sessions/chat_messages**: Conversation history

**Key Features:**
- Multi-source data support
- Full-text search indexes
- Referential integrity constraints
- Performance optimization for family tree traversal
- UUID primary keys for scalability

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DB_PASSWORD` | PostgreSQL database password | Yes | - |
| `OPENROUTER_API_KEY` | OpenRouter API key for chat functionality | Yes | - |
| `FAMILYSEARCH_CLIENT_ID` | FamilySearch API client ID | No | - |
| `DATABASE_URL` | Full PostgreSQL connection string | Yes | Auto-generated |
| `BACKEND_URL` | Backend API URL for frontend | Yes | http://localhost:8000 |

### OpenRouter API Setup

1. Sign up at https://openrouter.ai/
2. Generate an API key from your dashboard
3. Add the key to your `.env` file or configure it in the application
4. The key is encrypted and stored securely

### Performance Tuning

For large family trees (>1000 people):

- **Database**: Increase PostgreSQL shared_buffers and work_mem
- **Frontend**: Tree visualization automatically limits to 75 people for performance
- **Caching**: API responses are cached for 5-10 minutes
- **Indexes**: Full-text and relationship indexes optimize queries

## Troubleshooting

### Common Issues

**Database Connection Failed**
- Verify PostgreSQL container is running: `docker-compose ps`
- Check DATABASE_URL in environment configuration
- Ensure database password matches in .env file

**Chat Functionality Not Working**
- Confirm OPENROUTER_API_KEY is set and valid
- Check configuration status in Configuration tab
- Verify OpenRouter API key has sufficient credits

**GEDCOM Import Fails**
- Ensure file is valid GEDCOM format (.ged extension)
- Check file size is under 50MB limit
- Review backend logs for parsing errors: `docker-compose logs backend`

**Frontend Cannot Connect to Backend**
- Verify backend is running on port 8000: `curl http://localhost:8000/health`
- Check BACKEND_URL configuration
- Ensure no firewall blocking port 8000

**Performance Issues with Large Family Trees**
- Family tree visualization automatically limits display
- Use search functionality to find specific individuals
- Consider breaking large GEDCOM files into smaller chunks

### Viewing Logs

Monitor application logs for debugging:

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Health Checks

Check system status:

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend accessibility  
curl http://localhost:8501

# Database connectivity
docker-compose exec db pg_isready -U treetalk
```

## Contributing

We welcome contributions to TreeTalk! Please follow these guidelines:

### Development Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the coding standards
4. Add or update tests as necessary
5. Update documentation for any API changes
6. Submit a pull request with a clear description

### Coding Standards

- **Python**: Follow PEP 8 style guidelines
- **Documentation**: Use comprehensive docstrings for functions and classes
- **Testing**: Add unit tests for new functionality
- **API**: Maintain backward compatibility when possible
- **Database**: Include migration scripts for schema changes

### Testing

Run the test suite locally:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run backend tests
cd src/backend
pytest tests/

# Run integration tests
pytest tests/integration/
```

## Roadmap

### Upcoming Features

**Version 1.1**
- Enhanced family tree layouts (timeline view, descendant chart)
- Improved search with phonetic name matching
- Media file support (photos, documents)
- Export functionality (PDF reports, GEDCOM export)

**Version 1.2** 
- User authentication and multi-user support
- FamilySearch API integration
- Collaborative family trees with sharing
- Advanced chat with conversation memory

**Version 2.0**
- Mobile-responsive interface
- Geographic mapping of family history
- DNA integration support
- Advanced analytics and insights

### Known Limitations

- Single-user application (no authentication yet)
- Limited to GEDCOM import (no direct database editing)
- Chat responses limited by OpenRouter API context window
- Family tree visualization performance with very large trees (>1000 people)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### GPL v3 License Summary

- ✅ **Freedom to use**: Run the program for any purpose
- ✅ **Freedom to study**: Access and modify the source code  
- ✅ **Freedom to share**: Distribute copies to help others
- ✅ **Freedom to improve**: Share your modifications with the community

**Important**: Any derivative works must also be licensed under GPL v3, ensuring the software remains free and open source.

## Support

### Getting Help

- **Documentation**: Check this README and API documentation at http://localhost:8000/docs
- **Issues**: Report bugs and request features on GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

### Commercial Support

For commercial deployments or custom development:
- Professional installation and configuration
- Custom feature development
- Performance optimization for large datasets
- Integration with existing genealogy systems

## Acknowledgments

TreeTalk builds upon these excellent open source projects:

- **Streamlit**: Rapid web app development framework
- **FastAPI**: Modern, fast web framework for APIs
- **PostgreSQL**: Robust, scalable relational database
- **SQLAlchemy**: Powerful Python ORM
- **Plotly**: Interactive visualization library
- **NetworkX**: Graph analysis and visualization
- **OpenRouter**: AI model access platform

Special thanks to the genealogy community for feedback and testing during development.

---

**TreeTalk** - Transforming family history research through conversational AI and modern data management.
