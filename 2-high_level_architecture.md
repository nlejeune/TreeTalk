# TreeTalk High Level Architecture

## 1. Architecture Overview

TreeTalk follows a three-tier architecture pattern optimized for genealogical data management and conversational AI integration:

- **Frontend Layer**: Streamlit-based user interface
- **Backend Layer**: FastAPI REST service 
- **Data Layer**: PostgreSQL database with specialized genealogical schema

## 2. System Components

### 2.1 Frontend (Streamlit Application)
- **Technology**: Python with Streamlit framework
- **Components**:
  - GEDCOM file upload and management interface
  - Interactive family tree visualization
  - Search and person selection functionality
  - Chat interface with OpenRouter API integration
  - Configuration management for API keys
- **Key Features**:
  - Three-tab navigation (Data Exploration, Configuration, GEDCOM Management)
  - Real-time family tree visualization with D3.js-style components
  - ChatGPT-like conversational interface

### 2.2 Backend (FastAPI Service)
- **Technology**: Python with FastAPI framework
- **Core Services**:
  - **GEDCOM Parser Service**: Parse and validate .ged files
  - **Family Service**: Family tree operations and relationship queries
  - **Chat Service**: OpenRouter API integration and context management
  - **Configuration Service**: Encrypted API key storage
- **API Endpoints**:
  - `/api/gedcom/upload` - GEDCOM file processing
  - `/api/persons` - Person search and retrieval
  - `/api/family-tree/{person_id}` - Family tree data
  - `/api/chat/message` - Chat interaction
  - `/api/config` - Configuration management

### 2.3 Data Layer (PostgreSQL)
- **Database**: PostgreSQL with genealogical-optimized schema
- **Core Tables**:
  - `sources` - Track GEDCOM file imports
  - `persons` - Individual records with biographical data
  - `relationships` - Family connections (parent/child, spouse)
  - `events` - Life events (birth, marriage, death)
  - `places` - Geographical locations
  - `configuration` - Encrypted application settings
- **Features**:
  - Multi-source data support (multiple GEDCOM imports)
  - Full-text search capabilities
  - Relationship traversal optimization

## 3. Data Flow Architecture

### 3.1 GEDCOM Import Flow
1. User uploads .ged file via Streamlit interface
2. Frontend sends file to FastAPI backend
3. GEDCOM Parser Service validates and parses file
4. Data is normalized and stored in PostgreSQL
5. Import status reported back to frontend

### 3.2 Family Tree Visualization Flow
1. User selects person from search results
2. Frontend requests family tree data from backend
3. Backend queries PostgreSQL for relationships (4 degrees)
4. Relationship data formatted and returned
5. Frontend renders interactive D3.js-style visualization

### 3.3 Chat Interaction Flow
1. User enters natural language query
2. Frontend sends query to backend chat service
3. Backend retrieves relevant genealogical context from PostgreSQL
4. OpenRouter API called with context and user query
5. LLM response processed and returned to frontend
6. Chat history preserved for session continuity

## 4. Technology Stack

### 4.1 Frontend Technologies
- **Python 3.11+**: Core programming language
- **Streamlit**: Web application framework
- **Plotly/D3.js**: Family tree visualization
- **NetworkX**: Graph analysis for relationships

### 4.2 Backend Technologies
- **Python 3.11+**: Core programming language
- **FastAPI**: Async web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **python-gedcom**: GEDCOM file parsing

### 4.3 Data & Infrastructure
- **PostgreSQL 15+**: Primary database
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **OpenRouter API**: LLM integration

## 5. Security Architecture

### 5.1 API Key Management
- OpenRouter API keys encrypted at rest
- Configuration stored in PostgreSQL with encryption
- No sensitive data in environment variables (development only)

### 5.2 Data Privacy
- All genealogical data remains local (no external transmission except to LLM)
- Chat context limited to relevant family data only
- Optional chat history tied to specific GEDCOM sources

### 5.3 File Upload Security
- Strict .ged file format validation
- File size limits (50MB maximum)
- Input sanitization for GEDCOM parsing

## 6. Scalability Considerations

### 6.1 Database Optimization
- Indexed search fields for person names
- Relationship traversal optimization with recursive CTEs
- Connection pooling for concurrent requests

### 6.2 Performance Limits
- Family tree visualization limited to 4 relationship degrees
- Large tree rendering automatically optimized
- API response caching for frequently accessed data

### 6.3 Multi-Source Support
- Database schema supports multiple GEDCOM imports
- Data deduplication strategies
- Source tracking for data provenance

## 7. Deployment Architecture

### 7.1 Docker Containerization
- **Frontend Container**: Streamlit application (port 8501)
- **Backend Container**: FastAPI service (port 8000)  
- **Database Container**: PostgreSQL (port 5432)
- **Reverse Proxy**: Nginx for production deployment (optional)

### 7.2 Container Communication
- Internal Docker network for service communication
- Volume mounts for persistent database storage
- Environment-based configuration injection

### 7.3 Development vs Production
- **Development**: Direct container access, debug logging
- **Production**: Nginx proxy, SSL termination, log aggregation

## 8. Integration Points

### 8.1 OpenRouter API Integration
- RESTful API calls for LLM interactions
- Model selection and pricing integration
- Rate limiting and error handling

### 8.2 Future Integrations (Planned)
- FamilySearch API for data enrichment
- DNA analysis tool integration
- Export capabilities (PDF, enhanced GEDCOM)

## 9. Risk Mitigation

### 9.1 Technical Risks
- **Large GEDCOM Files**: Streaming parsing, progress indicators
- **Complex Family Trees**: Visualization limits, progressive loading
- **API Rate Limits**: Caching, graceful degradation

### 9.2 Data Risks
- **GEDCOM Format Variations**: Flexible parsing, validation reporting
- **Data Corruption**: Transaction integrity, backup recommendations
- **Privacy Concerns**: Local-only processing, clear data policies

## 10. Architecture Decision Records

### 10.1 Streamlit vs React/Vue
- **Decision**: Streamlit chosen for MVP
- **Rationale**: Rapid development, Python-native, minimal frontend complexity
- **Trade-off**: Less customization vs faster time-to-market

### 10.2 FastAPI vs Flask/Django
- **Decision**: FastAPI selected
- **Rationale**: Async support, automatic documentation, modern Python patterns
- **Trade-off**: Newer framework vs proven ecosystem

### 10.3 PostgreSQL vs NoSQL
- **Decision**: PostgreSQL for structured genealogical data
- **Rationale**: ACID compliance, complex relationships, mature tooling
- **Trade-off**: Schema rigidity vs data integrity guarantees