# Database Schema Documentation - TreeChat

## Overview

TreeChat uses PostgreSQL as its primary database to store genealogical data imported from GEDCOM files and synchronized from FamilySearch API. The schema is designed to support multiple data sources, maintain data integrity, and enable efficient querying for family tree operations.

## Design Principles

- **Multi-Source Support**: Enable multiple GEDCOM imports and external API synchronization
- **Data Integrity**: Foreign key constraints and data validation
- **Query Optimization**: Proper indexing for family tree traversal and search operations
- **Extensibility**: Schema design allows for future enhancements
- **Standards Compliance**: Follow genealogical data standards where applicable

## Core Tables

### 1. Sources Table
Tracks data provenance for all imported genealogical information.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('gedcom', 'familysearch')),
    description TEXT,
    file_path VARCHAR(500), -- For GEDCOM files
    imported_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    imported_by UUID, -- Future user management
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    metadata JSONB, -- Store additional source-specific data
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 2. Persons Table
Core table storing individual genealogical records.

```sql
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    gedcom_id VARCHAR(255), -- Original GEDCOM identifier (@I1@, etc.)
    external_id VARCHAR(255), -- FamilySearch Person ID
    
    -- Name information
    name VARCHAR(255) NOT NULL,
    given_names TEXT,
    surname VARCHAR(255),
    name_suffix VARCHAR(50), -- Jr., Sr., III, etc.
    nickname VARCHAR(100),
    
    -- Basic information
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'U')), -- Male, Female, Unknown
    is_living BOOLEAN DEFAULT FALSE,
    
    -- Birth information
    birth_date DATE,
    birth_date_text VARCHAR(100), -- For imprecise dates like "about 1850"
    birth_place VARCHAR(255),
    birth_place_id UUID, -- Reference to places table
    
    -- Death information
    death_date DATE,
    death_date_text VARCHAR(100),
    death_place VARCHAR(255),
    death_place_id UUID, -- Reference to places table
    
    -- Additional information
    occupation VARCHAR(255),
    religion VARCHAR(100),
    notes TEXT,
    
    -- Metadata
    confidence_level INTEGER DEFAULT 3 CHECK (confidence_level BETWEEN 1 AND 5), -- Data quality score
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(source_id, gedcom_id),
    UNIQUE(source_id, external_id)
);
```

### 3. Relationships Table
Manages family relationships between individuals.

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person1_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    person2_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    
    -- Additional relationship information
    start_date DATE, -- Marriage date, adoption date, etc.
    end_date DATE, -- Divorce date, death date, etc.
    place VARCHAR(255), -- Where relationship event occurred
    place_id UUID, -- Reference to places table
    
    -- Metadata
    source_id UUID NOT NULL REFERENCES sources(id),
    notes TEXT,
    confidence_level INTEGER DEFAULT 3 CHECK (confidence_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CHECK (person1_id != person2_id), -- Prevent self-relationships
    CHECK (relationship_type IN (
        'parent', 'child', 'spouse', 'partner',
        'sibling', 'adoptive_parent', 'adoptive_child',
        'step_parent', 'step_child', 'guardian', 'ward'
    )),
    UNIQUE(person1_id, person2_id, relationship_type)
);
```

### 4. Events Table
Store life events and milestones for individuals.

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    
    -- Event details
    event_date DATE,
    event_date_text VARCHAR(100), -- For imprecise dates
    place VARCHAR(255),
    place_id UUID, -- Reference to places table
    description TEXT,
    
    -- Additional participants (for marriages, baptisms, etc.)
    related_person_id UUID REFERENCES persons(id),
    
    -- Source information
    source_id UUID NOT NULL REFERENCES sources(id),
    citation TEXT, -- Source citation
    
    -- Metadata
    confidence_level INTEGER DEFAULT 3 CHECK (confidence_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CHECK (event_type IN (
        'birth', 'death', 'marriage', 'divorce', 'baptism', 'burial',
        'immigration', 'emigration', 'naturalization', 'military_service',
        'education', 'occupation_change', 'residence', 'census'
    ))
);
```

### 5. Places Table
Standardized location information for better geographical consistency.

```sql
CREATE TABLE places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL, -- Standardized format
    place_type VARCHAR(50), -- city, county, state, country, etc.
    
    -- Hierarchical structure
    parent_place_id UUID REFERENCES places(id),
    
    -- Geographic coordinates
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Administrative divisions
    city VARCHAR(100),
    county VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(normalized_name, place_type)
);
```

### 6. Chat Sessions Table
Store conversation history for the chat interface.

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID, -- Future user management
    
    -- Session metadata
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    
    -- Context information
    focused_person_id UUID REFERENCES persons(id),
    context_data JSONB, -- Store conversation context
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 7. Chat Messages Table
Individual chat messages within sessions.

```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    -- Message content
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Response metadata
    response_time_ms INTEGER, -- Time taken for AI response
    token_count INTEGER, -- Tokens used in LLM call
    model_used VARCHAR(100), -- OpenRouter model identifier
    
    -- Context references
    referenced_persons UUID[], -- Array of person IDs mentioned
    
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

## Supporting Tables

### 8. Families Table (Optional - for complex family structures)
Groups individuals into family units for better organization.

```sql
CREATE TABLE families (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    gedcom_id VARCHAR(255), -- Original GEDCOM family ID (@F1@, etc.)
    
    -- Family identification
    family_name VARCHAR(255),
    description TEXT,
    
    -- Key relationships
    husband_id UUID REFERENCES persons(id),
    wife_id UUID REFERENCES persons(id),
    
    -- Family events
    marriage_date DATE,
    marriage_place VARCHAR(255),
    divorce_date DATE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(source_id, gedcom_id)
);
```

### 9. Media Table (Future enhancement)
Store references to photos, documents, and other media.

```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_size BIGINT,
    file_path VARCHAR(500),
    
    -- Media metadata
    title VARCHAR(255),
    description TEXT,
    date_taken DATE,
    
    -- Associations
    person_id UUID REFERENCES persons(id),
    event_id UUID REFERENCES events(id),
    source_id UUID REFERENCES sources(id),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

## Indexes

### Performance Optimization Indexes

```sql
-- Person search and lookup indexes
CREATE INDEX idx_persons_name ON persons USING GIN (to_tsvector('english', name));
CREATE INDEX idx_persons_given_names ON persons USING GIN (to_tsvector('english', given_names));
CREATE INDEX idx_persons_surname ON persons (surname);
CREATE INDEX idx_persons_birth_date ON persons (birth_date);
CREATE INDEX idx_persons_death_date ON persons (death_date);
CREATE INDEX idx_persons_source ON persons (source_id);
CREATE INDEX idx_persons_gedcom_id ON persons (source_id, gedcom_id);

-- Relationship traversal indexes
CREATE INDEX idx_relationships_person1 ON relationships (person1_id);
CREATE INDEX idx_relationships_person2 ON relationships (person2_id);
CREATE INDEX idx_relationships_type ON relationships (relationship_type);
CREATE INDEX idx_relationships_composite ON relationships (person1_id, relationship_type);

-- Event lookups
CREATE INDEX idx_events_person ON events (person_id);
CREATE INDEX idx_events_date ON events (event_date);
CREATE INDEX idx_events_type ON events (event_type);

-- Chat system indexes
CREATE INDEX idx_chat_sessions_active ON chat_sessions (status, last_activity);
CREATE INDEX idx_chat_messages_session ON chat_messages (session_id, timestamp);

-- Place lookups
CREATE INDEX idx_places_normalized ON places (normalized_name);
CREATE INDEX idx_places_geographic ON places (latitude, longitude);
```

## Data Migration Scripts

### Initial Schema Creation

```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create all tables in dependency order
-- (Sources first, then tables that reference it)

-- Add foreign key constraints for place references
ALTER TABLE persons ADD CONSTRAINT fk_persons_birth_place 
    FOREIGN KEY (birth_place_id) REFERENCES places(id);
ALTER TABLE persons ADD CONSTRAINT fk_persons_death_place 
    FOREIGN KEY (death_place_id) REFERENCES places(id);
ALTER TABLE relationships ADD CONSTRAINT fk_relationships_place 
    FOREIGN KEY (place_id) REFERENCES places(id);
ALTER TABLE events ADD CONSTRAINT fk_events_place 
    FOREIGN KEY (place_id) REFERENCES places(id);
```

### Sample Data for Testing

```sql
-- Insert a sample GEDCOM source
INSERT INTO sources (name, type, description) VALUES 
('Sample Family Tree', 'gedcom', 'Test GEDCOM file for development');

-- Insert sample persons
INSERT INTO persons (source_id, name, given_names, surname, gender, birth_date, death_date) VALUES 
((SELECT id FROM sources WHERE name = 'Sample Family Tree'), 'John Smith', 'John', 'Smith', 'M', '1850-03-15', '1920-12-10'),
((SELECT id FROM sources WHERE name = 'Sample Family Tree'), 'Mary Smith', 'Mary', 'Smith', 'F', '1855-07-22', '1925-05-18');
```

## Query Examples

### Common Genealogical Queries

```sql
-- Find all children of a person
SELECT p2.* FROM persons p1
JOIN relationships r ON p1.id = r.person1_id
JOIN persons p2 ON r.person2_id = p2.id
WHERE p1.id = $person_id AND r.relationship_type = 'parent';

-- Find ancestors up to 3 generations
WITH RECURSIVE ancestors AS (
    SELECT id, name, 1 as generation FROM persons WHERE id = $person_id
    UNION ALL
    SELECT p.id, p.name, a.generation + 1
    FROM persons p
    JOIN relationships r ON p.id = r.person1_id
    JOIN ancestors a ON r.person2_id = a.id
    WHERE r.relationship_type = 'parent' AND a.generation < 3
)
SELECT * FROM ancestors WHERE generation > 1;

-- Search persons by name
SELECT * FROM persons 
WHERE to_tsvector('english', name) @@ to_tsquery('english', $search_term)
ORDER BY similarity(name, $search_term) DESC;
```

## Data Integrity Rules

### Business Rules Enforced by Database

1. **Relationship Consistency**: Parent-child relationships should be reciprocal
2. **Date Validation**: Birth date should precede death date
3. **Living Status**: Living persons cannot have death information
4. **Source Tracking**: All data must be associated with a source
5. **Unique Identifiers**: GEDCOM IDs must be unique within each source

### Triggers for Data Integrity

```sql
-- Trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_persons_updated_at BEFORE UPDATE ON persons
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON relationships
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Backup and Maintenance

### Backup Strategy
- Daily full backups during off-peak hours
- Point-in-time recovery enabled with WAL archiving
- Regular backup validation and restore testing

### Maintenance Tasks
- Weekly VACUUM and ANALYZE operations
- Monthly index rebuilding for heavily updated tables
- Quarterly statistics updates for query optimization
- Annual schema review and optimization

This database schema provides a robust foundation for TreeChat's genealogical data management while maintaining flexibility for future enhancements and ensuring data integrity across multiple import sources.