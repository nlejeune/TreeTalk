"""
Database Connection and Session Management

This module configures SQLAlchemy for the TreeTalk application.
Provides database engine, session management, and connection utilities.

Features:
- PostgreSQL connection with connection pooling
- Session dependency injection for FastAPI
- Base class for all SQLAlchemy models
- Database initialization utilities

Environment Variables:
- DATABASE_URL: PostgreSQL connection string
  Format: postgresql://user:password@host:port/database
"""

# Standard library imports
import os
from typing import Generator

# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Get database URL from environment with fallback default
# In production, this should always be set via environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://treetalk:treetalk@localhost:5432/treetalk"  # Development default
)

# =============================================================================
# SQLALCHEMY ENGINE SETUP
# =============================================================================

# Create SQLAlchemy engine with production-ready settings
engine = create_engine(
    DATABASE_URL,
    # Connection pool configuration
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=300,        # Recycle connections after 5 minutes
    pool_size=20,            # Maximum number of permanent connections
    max_overflow=0,          # No additional connections beyond pool_size
    
    # Performance and reliability settings
    echo=False,              # Set to True for SQL query logging in development
)

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

# Create session factory with recommended settings
# autocommit=False: Explicit transaction control
# autoflush=False: Manual control over when changes are flushed
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep objects usable after commit
)

# =============================================================================
# MODEL BASE CLASS
# =============================================================================

# Base class for all SQLAlchemy models
# All model classes should inherit from this
Base = declarative_base()

# =============================================================================
# SESSION DEPENDENCY INJECTION
# =============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide database sessions.
    
    This function creates a database session for each request,
    yields it to the route handler, and ensures proper cleanup.
    Used with FastAPI's Depends() for automatic injection.
    
    Usage:
        @app.get("/api/example")
        def example_route(db: Session = Depends(get_db)):
            # Use db session here
            pass
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        The session is automatically closed in the finally block,
        ensuring no connection leaks even if exceptions occur.
    """
    # Create new session for this request
    db = SessionLocal()
    try:
        # Yield session to the route handler
        yield db
    finally:
        # Ensure session is always closed, even on exceptions
        db.close()

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db() -> None:
    """
    Initialize database schema by creating all tables.
    
    This function imports all model modules to register them
    with SQLAlchemy, then creates the corresponding database
    tables if they don't already exist.
    
    Should be called once at application startup or during
    deployment to ensure the database schema is up to date.
    
    Note:
        This is idempotent - safe to call multiple times.
        Existing tables and data will not be affected.
    """
    # Import all model modules to register them with SQLAlchemy
    # This ensures all tables are known before creation
    from ..models import (
        person,        # Person/Individual records
        relationship,  # Family relationships
        source,       # Data sources (GEDCOM files, etc.)
        chat_session, # AI chat history
        place,        # Geographic places
        event         # Life events (birth, death, etc.)
    )
    
    # Create all tables based on registered models
    # This is idempotent - existing tables won't be modified
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully")