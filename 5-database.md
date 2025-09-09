# TreeTalk Database Schema Documentation

## Overview

TreeTalk uses PostgreSQL as its primary database for storing genealogical data with full support for multiple GEDCOM imports, relationship management, and conversational AI context. The schema is optimized for complex genealogical queries while maintaining data integrity and source provenance.

## Database Design Principles

1. **Multi-Source Support**: All data is linked to source records to enable multiple GEDCOM imports
2. **Referential Integrity**: Foreign key constraints ensure data consistency
3. **Performance Optimization**: Strategic indexes for genealogical queries
4. **Flexible Relationships**: Support for complex family structures
5. **Audit Trail**: Track data origin and modification history

## Core Tables

### 1. sources
Tracks data sources (GEDCOM files, manual entries, external APIs)

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    source_type VARCHAR(50) NOT NULL DEFAULT 'gedcom',
    file_size INTEGER,
    file_hash VARCHAR(64) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    import_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    persons_count INTEGER DEFAULT 0,
    families_count INTEGER DEFAULT 0,
    description TEXT,
    notes TEXT,
    error_message TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sources_status ON sources(status);
CREATE INDEX idx_sources_type ON sources(source_type);
CREATE INDEX idx_sources_hash ON sources(file_hash);
```

**Key Features:**
- UUID primary keys for distributed systems
- File hash prevents duplicate imports
- Status tracking for import progress
- Statistics for UI display
- Error handling support

### 2. persons
Individual person records with biographical information

```sql
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    gedcom_id VARCHAR(50),
    given_names VARCHAR(255),
    surname VARCHAR(255),
    maiden_name VARCHAR(255),
    nickname VARCHAR(100),
    gender VARCHAR(10),
    birth_date DATE,
    death_date DATE,
    is_living BOOLEAN DEFAULT TRUE,
    occupation VARCHAR(255),
    education TEXT,
    religion VARCHAR(100),
    notes TEXT,
    private_notes TEXT
);

CREATE INDEX idx_persons_source ON persons(source_id);
CREATE INDEX idx_persons_names ON persons(given_names, surname);
CREATE INDEX idx_persons_gedcom ON persons(source_id, gedcom_id);
CREATE INDEX idx_persons_dates ON persons(birth_date, death_date);
CREATE INDEX idx_persons_search ON persons USING GIN (
    to_tsvector('english', COALESCE(given_names, '') || ' ' || COALESCE(surname, ''))
);
```

**Key Features:**
- Full-text search capabilities
- Flexible date handling (partial dates supported)
- Privacy-sensitive notes separation
- Source tracking for multi-GEDCOM support
- Gender-neutral design

### 3. relationships
Family relationships between persons (parent-child, spouse, etc.)

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    person1_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    person2_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_subtype VARCHAR(50),
    is_primary BOOLEAN DEFAULT TRUE,
    marriage_date DATE,
    marriage_place_id UUID REFERENCES places(id),
    divorce_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    confidence VARCHAR(10) DEFAULT 'high',
    notes TEXT
);

CREATE INDEX idx_relationships_persons ON relationships(person1_id, person2_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
CREATE INDEX idx_relationships_source ON relationships(source_id);
CREATE INDEX idx_relationships_marriage ON relationships(marriage_date) WHERE marriage_date IS NOT NULL;
```

**Key Features:**
- Directional relationships (person1 ’ person2)
- Support for multiple marriage/divorce cycles
- Confidence levels for uncertain relationships
- Relationship subtypes (biological, adoptive, step)

### 4. places
Geographical locations for events and addresses

```sql
CREATE TABLE places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    place_type VARCHAR(50),
    locality VARCHAR(100),
    county VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    full_address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    notes TEXT,
    alternative_names TEXT
);

CREATE INDEX idx_places_hierarchy ON places(locality, county, state_province, country);
CREATE INDEX idx_places_coordinates ON places(latitude, longitude) WHERE latitude IS NOT NULL;
CREATE INDEX idx_places_source ON places(source_id);
CREATE INDEX idx_places_search ON places USING GIN (
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(full_address, ''))
);
```

**Key Features:**
- Hierarchical addressing system
- Geographic coordinates support
- Full-text search for location names
- Alternative names for historical places

### 5. events
Life events and milestones for persons

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_subtype VARCHAR(50),
    event_date DATE,
    date_qualifier VARCHAR(20),
    date_text VARCHAR(100),
    place_id UUID REFERENCES places(id),
    place_text VARCHAR(255),
    other_person_id UUID REFERENCES persons(id),
    description TEXT,
    notes TEXT,
    confidence VARCHAR(10) DEFAULT 'medium',
    is_primary BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_events_person_type ON events(person_id, event_type);
CREATE INDEX idx_events_date ON events(event_date) WHERE event_date IS NOT NULL;
CREATE INDEX idx_events_source ON events(source_id);
CREATE INDEX idx_events_type ON events(event_type);
```

**Key Features:**
- Flexible date handling with qualifiers
- Support for event participants (marriages, etc.)
- Original text preservation from sources
- Data quality indicators

### 6. chat_sessions
Chat conversation contexts and settings

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    focused_person_id UUID REFERENCES persons(id),
    active_source_id UUID REFERENCES sources(id),
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    model_name VARCHAR(100),
    system_prompt TEXT,
    max_context_messages INTEGER DEFAULT 20,
    temperature FLOAT DEFAULT 0.7
);

CREATE INDEX idx_chat_sessions_activity ON chat_sessions(last_activity);
CREATE INDEX idx_chat_sessions_active ON chat_sessions(is_active) WHERE is_active = TRUE;
```

### 7. chat_messages
Individual messages within chat sessions

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sequence_number INTEGER NOT NULL,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    genealogy_context JSONB,
    cited_sources JSONB,
    is_error BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

CREATE INDEX idx_chat_messages_session_seq ON chat_messages(session_id, sequence_number);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX idx_chat_messages_type ON chat_messages(message_type);
```

### 8. configuration
Encrypted application configuration

```sql
CREATE TABLE configuration (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configuration_updated ON configuration(updated_at);
```

## Relationships and Constraints

### Foreign Key Relationships

```
sources (1) ’ (N) persons
sources (1) ’ (N) relationships
sources (1) ’ (N) places
sources (1) ’ (N) events

persons (1) ’ (N) events
persons (1) ’ (N) relationships (as person1)
persons (1) ’ (N) relationships (as person2)
persons (1) ’ (N) chat_sessions (as focused_person)

places (1) ’ (N) events
places (1) ’ (N) relationships (marriage_place)

chat_sessions (1) ’ (N) chat_messages
sources (1) ’ (N) chat_sessions (as active_source)
```

### Data Integrity Rules

1. **Cascade Deletes**: Deleting a source removes all associated data
2. **Referential Integrity**: All foreign keys must reference existing records
3. **Date Validation**: Death dates must be after birth dates (application level)
4. **Gender Constraints**: Gender values limited to M, F, U (Unknown)
5. **Status Validation**: Limited to predefined status values

## Performance Optimizations

### Indexes for Genealogical Queries

1. **Name Search**: Full-text search indexes on person names
2. **Relationship Traversal**: Composite indexes on person pairs
3. **Date Ranges**: Indexes on birth/death dates for timeline queries
4. **Geographic Search**: Spatial indexes for location-based queries
5. **Source Filtering**: Indexes for multi-GEDCOM data isolation

### Query Optimization Patterns

```sql
-- Efficient family tree traversal using recursive CTE
WITH RECURSIVE family_tree AS (
    -- Anchor: Start with focal person
    SELECT id, given_names, surname, 1 as generation
    FROM persons WHERE id = $focal_person_id
    
    UNION ALL
    
    -- Recursive: Add parents and children
    SELECT p.id, p.given_names, p.surname, ft.generation + 1
    FROM persons p
    JOIN relationships r ON (r.person1_id = p.id OR r.person2_id = p.id)
    JOIN family_tree ft ON (
        (r.person1_id = ft.id AND r.relationship_type = 'parent-child') OR
        (r.person2_id = ft.id AND r.relationship_type = 'parent-child')
    )
    WHERE ft.generation < 4  -- Limit generations
)
SELECT * FROM family_tree;
```

## Security Considerations

### Data Encryption

1. **API Keys**: Encrypted using Fernet (cryptography library)
2. **Private Notes**: Considered for column-level encryption
3. **Connection Security**: SSL/TLS for database connections
4. **Access Control**: Role-based database permissions

### Privacy Protection

1. **Data Isolation**: Source-based data partitioning
2. **Anonymization**: Remove PII for testing environments
3. **Audit Logs**: Track access to sensitive genealogical data
4. **GDPR Compliance**: Support for data deletion requests