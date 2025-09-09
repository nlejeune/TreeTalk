"""
Database Utilities and Base Configuration

This module provides database connection management, base model definition,
and utility functions for the TreeTalk application's PostgreSQL integration.

Key Functions:
- Base model for SQLAlchemy declarative mapping
- Database connection and session management
- Table creation and migration utilities
- Database health checking
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import AsyncGenerator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy declarative base for all models
Base = declarative_base()


async def create_tables(engine):
    """
    Create all database tables if they don't exist.
    
    Args:
        engine: SQLAlchemy async engine instance
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models import (
                Source, Person, Relationship, Event, Place, 
                ChatSession, ChatMessage, Configuration
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
            
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def check_database_health(engine) -> bool:
    """
    Check database connectivity and health.
    
    Args:
        engine: SQLAlchemy async engine instance
        
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✅ Database health check passed")
            return True
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for FastAPI routes.
    
    This function is designed to be used with FastAPI's dependency injection.
    It retrieves the database session from the app state.
    
    Yields:
        AsyncSession: Database session for use in API endpoints
    """
    # This will be properly configured when used as a FastAPI dependency
    # The FastAPI app will have the engine in app.state
    from fastapi import Request
    # For now, we'll handle this in the main.py dependency setup
    pass


def get_connection_info() -> dict:
    """
    Get database connection information for debugging.
    
    Returns:
        dict: Connection metadata (without sensitive data)
    """
    import os
    
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/treetalk")
    
    # Parse URL components safely
    if "://" in db_url:
        protocol_and_rest = db_url.split("://", 1)
        protocol = protocol_and_rest[0]
        
        if len(protocol_and_rest) > 1 and "@" in protocol_and_rest[1]:
            auth_and_host = protocol_and_rest[1].split("@", 1)
            if len(auth_and_host) > 1:
                host_and_db = auth_and_host[1]
                if "/" in host_and_db:
                    host_port, database = host_and_db.rsplit("/", 1)
                    if ":" in host_port:
                        host, port = host_port.rsplit(":", 1)
                    else:
                        host, port = host_port, "5432"
                else:
                    host, port, database = host_and_db, "5432", "treetalk"
            else:
                host, port, database = "localhost", "5432", "treetalk"
        else:
            host, port, database = "localhost", "5432", "treetalk"
    else:
        protocol, host, port, database = "postgresql+asyncpg", "localhost", "5432", "treetalk"
    
    return {
        "protocol": protocol,
        "host": host,
        "port": port,
        "database": database,
        "status": "configured"
    }