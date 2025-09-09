"""
TreeTalk Backend - FastAPI Application Main Entry Point

This module serves as the main entry point for the TreeTalk backend service.
It configures and starts the FastAPI application with all necessary routes,
middleware, and database connections for genealogical data management and
conversational AI integration.

Key Features:
- FastAPI REST API with automatic OpenAPI documentation
- PostgreSQL database integration with SQLAlchemy
- GEDCOM file processing and import
- OpenRouter LLM integration for chat functionality
- Encrypted configuration management
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from models.configuration import get_database_url
from routes import auth, chat, persons, gedcom, config
from utils.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles:
    - Database connection initialization
    - Table creation if needed
    - Graceful cleanup on shutdown
    """
    # Startup
    try:
        # Initialize database connection
        database_url = await get_database_url()
        engine = create_async_engine(database_url, echo=True)
        
        # Create tables if they don't exist
        await create_tables(engine)
        
        # Store engine in app state
        app.state.engine = engine
        app.state.SessionLocal = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        print("✅ TreeTalk Backend started successfully")
        yield
        
    except Exception as e:
        print(f"❌ Failed to start TreeTalk Backend: {e}")
        raise
    finally:
        # Shutdown
        if hasattr(app.state, "engine"):
            await app.state.engine.dispose()
        print("🔄 TreeTalk Backend shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="TreeTalk API",
    description="Genealogical data management and conversational AI for family history exploration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint providing API information and health status.
    
    Returns:
        dict: API information including name, version, and status
    """
    return {
        "name": "TreeTalk API",
        "version": "1.0.0",
        "description": "Genealogical data management and conversational AI",
        "status": "healthy",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: System health status
    """
    try:
        # Basic health check - could be extended to check database connectivity
        return {
            "status": "healthy",
            "service": "TreeTalk Backend",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# Database dependency
async def get_db():
    """Database dependency for FastAPI routes."""
    async with app.state.SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

# Override the database dependency in routes
from utils.database import get_database_session
app.dependency_overrides[get_database_session] = get_db

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(config.router, prefix="/api/config", tags=["Configuration"])
app.include_router(gedcom.router, prefix="/api/gedcom", tags=["GEDCOM Management"])
app.include_router(persons.router, prefix="/api/persons", tags=["Person Management"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat & AI"])


# Main entry point for development
if __name__ == "__main__":
    """
    Development server entry point.
    
    For production deployment, use:
    uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
    """
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )