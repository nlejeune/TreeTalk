-- TreeTalk Database Initialization Script
-- This script sets up the basic database with extensions

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable full-text search extensions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance (these will be created by SQLAlchemy as well)
-- Additional custom indexes can be added here if needed

-- Insert sample data if needed (commented out for now)
-- This would be useful for development/testing

COMMENT ON DATABASE treetalk IS 'TreeTalk - Converse with Your Family History';