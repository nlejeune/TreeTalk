-- TreeTalk Database Initialization Script
-- This script sets up the initial database schema and configuration

-- Create database (if not exists)
-- Note: The database is created by the POSTGRES_DB environment variable

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create initial configuration table manually (before SQLAlchemy creates tables)
-- This ensures we can store configuration even before the app starts
CREATE TABLE IF NOT EXISTS configuration (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration values
INSERT INTO configuration (key, value) VALUES 
    ('database_version', '"1.0.0"'),
    ('app_initialized', 'false'),
    ('default_model', '"openai/gpt-3.5-turbo"')
ON CONFLICT (key) DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_configuration_updated ON configuration(updated_at);

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'TreeTalk database initialized successfully';
END $$;