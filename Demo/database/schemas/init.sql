-- TreeChat Demo Database Schema
-- This schema supports the genealogical data structure for the demo

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Persons table
CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE, -- For GEDCOM/FamilySearch IDs
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    full_name VARCHAR(511) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    birth_date DATE,
    death_date DATE,
    birth_place TEXT,
    death_place TEXT,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data sources table
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'gedcom', 'familysearch', etc.
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'disconnected', 'syncing'
    last_sync TIMESTAMP,
    metadata JSONB, -- Store source-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Person sources - link persons to their data sources
CREATE TABLE person_sources (
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    source_person_id VARCHAR(255), -- Original ID in the source
    PRIMARY KEY (person_id, source_id)
);

-- Relationships table
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person1_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    person2_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'parent', 'child', 'spouse', 'sibling'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(person1_id, person2_id, relationship_type)
);

-- Events table (births, deaths, marriages, etc.)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'birth', 'death', 'marriage', 'baptism', etc.
    event_date DATE,
    event_place TEXT,
    description TEXT,
    source_id UUID REFERENCES data_sources(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat conversations table
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255),
    message_type VARCHAR(20) NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    metadata JSONB, -- Store suggestions, context, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_persons_full_name ON persons USING gin(to_tsvector('english', full_name));
CREATE INDEX idx_persons_birth_date ON persons(birth_date);
CREATE INDEX idx_persons_external_id ON persons(external_id);
CREATE INDEX idx_relationships_person1 ON relationships(person1_id);
CREATE INDEX idx_relationships_person2 ON relationships(person2_id);
CREATE INDEX idx_events_person_id ON events(person_id);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_chat_session ON chat_conversations(session_id, created_at);

-- Insert demo data
INSERT INTO data_sources (name, type, status, last_sync, metadata) VALUES 
('Dupont Family GEDCOM', 'gedcom', 'active', CURRENT_TIMESTAMP, '{"filename": "dupont_family.ged", "person_count": 10}'),
('FamilySearch Demo', 'familysearch', 'disconnected', NULL, '{"api_version": "v1", "last_error": "Authentication required"}');

-- Insert demo persons (this would normally be done through the application)
-- Note: In a real scenario, this would be handled by the GEDCOM parser or API sync

COMMENT ON TABLE persons IS 'Store individual person records from genealogical sources';
COMMENT ON TABLE relationships IS 'Store family relationships between persons';
COMMENT ON TABLE events IS 'Store life events for persons (birth, death, marriage, etc.)';
COMMENT ON TABLE data_sources IS 'Track different sources of genealogical data';
COMMENT ON TABLE person_sources IS 'Link persons to their originating data sources';
COMMENT ON TABLE chat_conversations IS 'Store chat history for the conversational interface';