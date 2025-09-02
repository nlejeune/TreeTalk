"""
TreeTalk - FastAPI Backend Application

This is the main entry point for the TreeTalk API backend.
Provides RESTful API endpoints for the Streamlit frontend to:
- Import and manage GEDCOM genealogy files
- Query family tree data and relationships  
- Chat with AI about family history
- Manage data sources and authentication

Architecture:
- FastAPI web framework for async REST API
- SQLAlchemy ORM with PostgreSQL database
- Modular route structure organized by domain
- CORS enabled for frontend communication
"""

# Standard library imports
import os
import uuid
from typing import List, Optional

# Third-party imports
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

# Local imports - database utilities
from .utils.database import get_db, engine, Base

# Local imports - data models (import to register with SQLAlchemy)
from .models import person, relationship, source, chat_session, place, event

# Local imports - API route modules
from .routes import auth, persons, import_routes, chat, sources, config

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

# Create all database tables based on SQLAlchemy models
# This runs at application startup to ensure schema exists
Base.metadata.create_all(bind=engine)

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

# Initialize FastAPI application with metadata
app = FastAPI(
    title="TreeTalk API",
    description="Backend API for TreeTalk - Converse with Your Family History",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc"  # ReDoc endpoint
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# Configure CORS middleware to allow frontend communication
# Streamlit default ports: 8501 for main app, 8502 for additional instances
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",    # Streamlit default port
        "http://127.0.0.1:8501",   # Alternative localhost format
    ],
    allow_credentials=True,         # Allow cookies/auth headers
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all headers
)

# =============================================================================
# API ROUTE REGISTRATION
# =============================================================================

# Register route modules with URL prefixes and OpenAPI tags
# Each module handles a specific domain of functionality
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(persons.router, prefix="/api/persons", tags=["persons"])
app.include_router(import_routes.router, prefix="/api/import", tags=["import"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])

# =============================================================================
# CORE API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API information and status.
    
    Returns basic information about the TreeTalk API,
    including version and operational status.
    
    Returns:
        dict: API metadata including message, version, and status
    """
    return {
        "message": "TreeTalk API - Converse with Your Family History",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.
    
    Performs a simple database connectivity test to ensure
    the application is healthy and ready to serve requests.
    
    Args:
        db (Session): Database session dependency
        
    Returns:
        dict: Health status including database connectivity
        
    Raises:
        HTTPException: 503 Service Unavailable if database is unreachable
    """
    try:
        # Execute simple query to test database connectivity
        # Using SQLAlchemy text() to ensure proper query execution
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
    except Exception as e:
        # Log error and return 503 Service Unavailable
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Direct execution - start Uvicorn server
    # In production, this would typically be handled by a process manager
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,       # Default port for TreeTalk API
        reload=False     # Disable auto-reload in production
    )