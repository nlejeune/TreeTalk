# TreeTalk High Level Architecture

## 1. Architecture Overview

TreeTalk follows a three-tier architecture pattern optimized for genealogical data management and conversational AI integration:

- **Frontend Layer**: Streamlit-based user interface (`src/frontend/main.py`)
- **Backend Layer**: FastAPI REST service (`src/backend/main.py`)
- **Data Layer**: PostgreSQL database with specialized genealogical schema

## 2. System Components

### 2.1 Frontend (Streamlit Application)
- **Technology**: Python 3.11+ with Streamlit framework
- **Main File**: `src/frontend/main.py` (864 lines)
- **Components**:
  - GEDCOM file upload and management interface
  - Interactive family tree visualization using Plotly and NetworkX
  - Person search and selection functionality
  - Chat interface with OpenRouter API integration
  - Configuration management for API keys and AI models
- **Key Features**:
  - Three-tab navigation: Data Exploration, Configuration, GEDCOM Management
  - Real-time family tree visualization with network graphs
  - ChatGPT-style conversational interface with genealogical context
  - Multi-source GEDCOM support with source selection
  - Family tree limited to 4 degrees of relationship for performance

### 2.2 Backend (FastAPI Service)
- **Technology**: Python 3.11+ with FastAPI framework and async/await
- **Main File**: `src/backend/main.py` with async lifespan management
- **Core Services**:
  - **GEDCOM Parser Service**: Parse and validate .ged files using python-gedcom library
  - **Family Service**: Family tree operations and relationship queries
  - **Chat Service**: OpenRouter API integration with genealogical context injection
  - **Configuration Service**: Encrypted API key storage in database
- **API Route Structure**:
  - `/api/auth` - Authentication endpoints
  - `/api/config` - Configuration management (API keys, models)
  - `/api/gedcom` - GEDCOM upload, processing, and source management
  - `/api/persons` - Person search, details, and family tree queries
  - `/api/chat` - Chat interactions and AI model selection
- **Key Features**:
  - Async database operations with SQLAlchemy
  - CORS support for Streamlit frontend integration
  - Automatic OpenAPI documentation at `/docs`
  - Database dependency injection pattern

### 2.3 Data Layer (PostgreSQL)
- **Database**: PostgreSQL with async SQLAlchemy ORM
- **Core Models** (in `src/backend/models/`):
  - `Source` - Track GEDCOM file imports with metadata
  - `Person` - Individual records with biographical data and life spans
  - `Relationship` - Family connections (parent-child, spouse, sibling) with directional mapping
  - `Event` - Life events (birth, death, marriage, residence, occupation)
  - `Place` - Geographical locations with hierarchical structure
  - `Configuration` - Encrypted application settings and API keys
  - `ChatSession` - Chat conversation sessions with focused persons
  - `ChatMessage` - Individual chat messages with AI model metadata
- **Features**:
  - Multi-source data support (multiple GEDCOM imports with source tracking)
  - Relationship traversal optimization for family tree queries
  - Full-text search capabilities on person names
  - Encrypted configuration storage for API keys
  - Chat history preservation with genealogical context

## 3. Data Flow Architecture

### 3.1 GEDCOM Import Flow
1. User uploads .ged file via Streamlit interface (max 50MB)
2. Frontend sends multipart file data to `/api/gedcom/upload`
3. **GedcomParserService** validates file hash and checks for duplicates
4. Creates **Source** record and parses GEDCOM using python-gedcom library
5. Data extracted and normalized:
   - **Persons** with biographical data and life events
   - **Relationships** (parent-child, spouse, sibling) with marriage details
   - **Events** (birth, death, marriage, residence, occupation)
   - **Places** with automatic deduplication
6. All data committed to PostgreSQL with source tracking
7. Import statistics returned to frontend with error reporting

### 3.2 Family Tree Visualization Flow
1. User searches and selects person from results
2. Frontend calls `/api/persons/{person_id}/family-tree` with max_generations=4
3. **FamilyService** performs relationship traversal using recursive queries
4. Returns focused person, connected persons, and relationships
5. Frontend uses **NetworkX** to create graph layout
6. **Plotly** renders interactive network visualization with:
   - Color-coded nodes by gender (blue=male, pink=female, green=unknown)
   - Sized nodes (focal person larger)
   - Hover info showing names and life spans
   - Connection lines showing relationships

### 3.3 Chat Interaction Flow
1. User enters natural language query in chat interface
2. Frontend sends message to `/api/chat/message` with session_id
3. **ChatService** creates or retrieves existing chat session
4. Genealogical context preparation:
   - Extracts potential names from user message
   - Searches for mentioned persons in database
   - Retrieves focused person details and family tree (3 degrees)
   - Builds structured context with persons, relationships, and events
5. **OpenRouter API** integration:
   - Constructs system prompt with genealogical data constraints
   - Adds conversation history (last 10 messages)
   - Calls selected AI model with temperature and token limits
6. AI response processed and saved to **ChatMessage** table
7. Response returned with metadata (tokens used, model, timing)
8. Chat history preserved with genealogical context for continuity

## 4. Technology Stack

### 4.1 Frontend Technologies
- **Python 3.11+**: Core programming language
- **Streamlit 1.28.2**: Web application framework with real-time updates
- **Plotly 5.17.0**: Interactive network graph visualization
- **NetworkX 3.2.1**: Graph analysis and layout algorithms for family trees
- **Pandas 2.1.4**: Data manipulation for search results and statistics
- **Requests 2.31.0**: HTTP client for backend API communication

### 4.2 Backend Technologies  
- **Python 3.11+**: Core programming language with async/await support
- **FastAPI 0.104.1**: Async web framework with automatic OpenAPI docs
- **Uvicorn 0.24.0**: ASGI server for FastAPI application
- **SQLAlchemy 2.0.23**: Async ORM for PostgreSQL operations
- **AsyncPG 0.29.0**: PostgreSQL async driver
- **Pydantic 2.5.0**: Data validation and serialization
- **python-gedcom 1.0.0**: GEDCOM file parsing and validation
- **HTTPX 0.25.2**: Async HTTP client for OpenRouter API calls
- **Cryptography 42.0.0+**: API key encryption and secure configuration storage

### 4.3 Data & Infrastructure
- **PostgreSQL**: Primary database with async operations
- **AsyncPG**: Native PostgreSQL async driver for performance
- **Alembic 1.13.1**: Database migration management
- **OpenRouter API**: Multi-model LLM integration platform
- **No Docker**: Application runs directly with Python virtual environment

## 5. Security Architecture

### 5.1 API Key Management
- OpenRouter API keys encrypted at rest using **Cryptography** library
- Configuration stored in **PostgreSQL Configuration** table with encryption
- Secure key retrieval and validation in **ChatService**
- API key status checking without exposing actual key values
- Clear configuration option for key rotation

### 5.2 Data Privacy & AI Integration
- All genealogical data remains local (only chat queries sent to OpenRouter)
- **Strict AI prompting**: System prompts enforce database-only responses
- Chat context limited to relevant family data with person/relationship limits
- No external knowledge injection - AI forbidden from using general historical data
- Chat sessions tied to specific GEDCOM sources with user control
- Conversation history preserved locally with full user access

### 5.3 File Upload Security  
- Strict .ged file format validation using **python-gedcom** parser
- File size limits (50MB maximum) enforced at frontend and backend
- SHA-256 file hash calculation for duplicate detection
- Input sanitization and error handling for malformed GEDCOM data
- Temporary file handling with automatic cleanup
- Source tracking for data provenance and isolation

## 6. Scalability Considerations

### 6.1 Database Optimization
- **Async Operations**: Full async/await pattern with AsyncPG driver
- **Indexed Fields**: Person names, source IDs, and relationship types indexed
- **Relationship Traversal**: Optimized queries for family tree generation
- **Source Isolation**: Multi-tenant data with source-based filtering
- **Connection Pooling**: AsyncPG handles connection management

### 6.2 Performance Limits & Optimizations
- **Family Tree Scope**: Limited to 4 relationship degrees to prevent performance issues
- **Graph Rendering**: NetworkX spring layout with iteration limits (50)
- **Chat Context**: Person and relationship limits in AI context (20 persons, 30 relationships)  
- **Search Results**: Configurable limits (10-50 results) with pagination potential
- **File Processing**: Streaming GEDCOM parsing with progress tracking

### 6.3 Multi-Source Architecture
- **Source Tracking**: All data tied to specific GEDCOM imports via `source_id`
- **Duplicate Prevention**: SHA-256 hash checking prevents re-import of same files
- **Data Isolation**: Users can select active source for searches and chat
- **Place Deduplication**: Automatic place record reuse across sources
- **Relationship Mapping**: Cross-source relationship detection possible

## 7. Deployment Architecture

### 7.1 Current Deployment (No Docker)
- **Frontend**: Streamlit dev server on port 8501 (`streamlit run src/frontend/main.py`)
- **Backend**: Uvicorn ASGI server on port 8000 (`uvicorn src.backend.main:app`)
- **Database**: External PostgreSQL instance (configured via environment/config)
- **Development**: Direct Python execution with hot reloading

### 7.2 Production Considerations
- **ASGI Server**: Gunicorn with Uvicorn workers for production FastAPI
- **Reverse Proxy**: Nginx recommended for static files and SSL termination  
- **Database**: Managed PostgreSQL service with connection pooling
- **Environment**: Configuration via environment variables or `.config/.env`
- **Monitoring**: Application logging with structured output

### 7.3 Scaling Options
- **Horizontal**: Multiple backend instances behind load balancer
- **Database**: PostgreSQL read replicas for query scaling
- **Caching**: Redis integration for chat session and search caching
- **File Storage**: Object storage (S3) for large GEDCOM file archival

## 8. Integration Points

### 8.1 OpenRouter API Integration
- **Multi-Model Access**: Dynamic model list retrieval with pricing information
- **Cost Optimization**: Free and low-cost models prioritized in selection
- **Error Handling**: Comprehensive error handling for authentication, rate limits, and credit issues
- **Model Flexibility**: User-configurable model selection with fallback options
- **Request Management**: Timeout handling (30s) and retry logic for robust API calls

### 8.2 GEDCOM Ecosystem Integration
- **Standard Compliance**: Full GEDCOM 5.5 support via python-gedcom library
- **Multiple Formats**: Handles various GEDCOM dialect variations
- **Import Flexibility**: Source name customization and metadata preservation
- **Export Potential**: Database structure supports future GEDCOM export capability

### 8.3 Future Integration Opportunities
- **FamilySearch API**: Person matching and data enrichment potential
- **DNA Analysis Tools**: MyHeritage, AncestryDNA integration possibilities
- **Export Formats**: PDF reports, enhanced GEDCOM, family tree images
- **External Storage**: Cloud backup for GEDCOM files and generated content

## 9. Risk Mitigation

### 9.1 Technical Risk Management
- **Large GEDCOM Files**: Temporary file processing with automatic cleanup, 50MB size limits
- **Complex Family Trees**: 4-degree relationship limits, graph layout optimizations
- **API Dependencies**: Multiple model support, local fallback prompts, graceful degradation
- **Memory Management**: Async operations prevent blocking, pagination for large datasets
- **Database Performance**: Indexed fields, source-based data isolation, connection pooling

### 9.2 Data Integrity & Privacy
- **GEDCOM Parsing Errors**: Comprehensive error collection and reporting during import
- **Data Corruption Prevention**: Transaction-based imports with rollback capability
- **Privacy Protection**: No data transmission except user chat queries to OpenRouter
- **Source Isolation**: Complete data segregation by GEDCOM source with user control
- **Chat Context Limits**: Structured limits prevent excessive data exposure to AI

### 9.3 AI Integration Risks
- **Hallucination Prevention**: Strict system prompts forbid external knowledge use
- **Data Accuracy**: Clear citations and database-only response requirements
- **Token Management**: Cost controls with model pricing transparency
- **Rate Limiting**: OpenRouter handles rate limits, application provides graceful handling

## 10. Architecture Decision Records

### 10.1 Streamlit vs React/Vue
- **Decision**: Streamlit chosen for MVP development
- **Rationale**: Python-native development, rapid prototyping, built-in components
- **Trade-offs**: Limited customization vs development velocity, single-language stack
- **Implementation**: 864-line single-file architecture with modular component functions

### 10.2 FastAPI vs Flask/Django
- **Decision**: FastAPI selected for backend API
- **Rationale**: Native async support, automatic OpenAPI docs, modern Python patterns
- **Trade-offs**: Newer ecosystem vs established frameworks, learning curve vs performance
- **Implementation**: Full async/await pattern, dependency injection, structured routing

### 10.3 PostgreSQL vs NoSQL (MongoDB/Document DB)
- **Decision**: PostgreSQL chosen for genealogical data
- **Rationale**: ACID compliance, complex relationship queries, JSON support when needed
- **Trade-offs**: Schema constraints vs data consistency, relational complexity vs query flexibility
- **Implementation**: Async SQLAlchemy ORM, indexed relationship traversal, multi-source architecture

### 10.4 OpenRouter vs Direct LLM APIs
- **Decision**: OpenRouter for AI integration  
- **Rationale**: Multi-model access, cost optimization, unified API interface
- **Trade-offs**: Additional service dependency vs model flexibility and cost control
- **Implementation**: Dynamic model selection, pricing transparency, comprehensive error handling
