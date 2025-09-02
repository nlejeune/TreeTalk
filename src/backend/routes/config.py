"""
Configuration API routes - Handle API key management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os

from ..utils.database import get_db

router = APIRouter()

class OpenRouterConfig(BaseModel):
    api_key: str

class FamilySearchConfig(BaseModel):
    client_id: str

# Endpoint to save OpenRouter API configuration
@router.post("/openrouter")
async def save_openrouter_config(
    config: OpenRouterConfig,
    db: Session = Depends(get_db)
):
    """Save OpenRouter API configuration."""
    try:
        # In a production system, this would be encrypted and stored securely
        # For MVP, we'll use environment variables
        os.environ["OPENROUTER_API_KEY"] = config.api_key
        
        return {"message": "OpenRouter API key configured successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

# Endpoint to save FamilySearch API configuration
@router.post("/familysearch")
async def save_familysearch_config(
    config: FamilySearchConfig,
    db: Session = Depends(get_db)
):
    """Save FamilySearch API configuration."""
    try:
        # Store FamilySearch client ID
        os.environ["FAMILYSEARCH_CLIENT_ID"] = config.client_id
        
        return {"message": "FamilySearch configuration saved successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")

# Endpoint to get configuration status
@router.get("/status")
async def get_config_status():
    """Get configuration status."""
    return {
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "familysearch_configured": bool(os.getenv("FAMILYSEARCH_CLIENT_ID"))
    }