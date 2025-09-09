"""
Configuration Management API Routes

This module provides REST API endpoints for application configuration
management including API keys, model settings, and user preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from utils.database import get_database_session
from models.configuration import Configuration

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for request/response
class ConfigurationRequest(BaseModel):
    """Request model for setting configuration values."""
    key: str
    value: Any


class ApiKeyRequest(BaseModel):
    """Request model for setting API keys."""
    openrouter_api_key: Optional[str] = None
    default_model: Optional[str] = None


@router.post("/api-key")
async def set_api_configuration(
    request: ApiKeyRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Set API configuration (OpenRouter key and default model).
    
    Args:
        request: API configuration request
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If configuration fails
    """
    try:
        updates = []
        
        if request.openrouter_api_key:
            if len(request.openrouter_api_key.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid API key format"
                )
            
            await Configuration.set_value(db, "openrouter_api_key", request.openrouter_api_key.strip())
            updates.append("OpenRouter API key")
        
        if request.default_model:
            await Configuration.set_value(db, "default_model", request.default_model)
            updates.append("Default model")
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No configuration values provided"
            )
        
        logger.info(f"Updated configuration: {', '.join(updates)}")
        
        return {
            "success": True,
            "message": f"Successfully updated: {', '.join(updates)}",
            "updated_fields": updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set API configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/api-key/status")
async def get_api_key_status(
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get status of API key configuration (without revealing the keys).
    
    Args:
        db: Database session
        
    Returns:
        API key configuration status
    """
    try:
        openrouter_key = await Configuration.get_value(db, "openrouter_api_key")
        default_model = await Configuration.get_value(db, "default_model", "openai/gpt-3.5-turbo")
        
        status_info = {
            "openrouter_api_key_configured": bool(openrouter_key),
            "default_model": default_model,
            "chat_available": bool(openrouter_key),
            "configuration_complete": bool(openrouter_key)
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get API key status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration status"
        )


@router.post("/setting")
async def set_configuration_value(
    request: ConfigurationRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Set a general configuration value.
    
    Args:
        request: Configuration request
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If setting fails
    """
    try:
        if not request.key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration key cannot be empty"
            )
        
        # Validate key format (simple validation)
        if not request.key.replace('_', '').replace('-', '').isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid configuration key format"
            )
        
        await Configuration.set_value(db, request.key, request.value)
        
        logger.info(f"Set configuration value: {request.key}")
        
        return {
            "success": True,
            "message": f"Successfully set configuration '{request.key}'",
            "key": request.key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set configuration {request.key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set configuration: {str(e)}"
        )


@router.get("/setting/{key}")
async def get_configuration_value(
    key: str,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get a configuration value (non-sensitive values only).
    
    Args:
        key: Configuration key
        db: Database session
        
    Returns:
        Configuration value
        
    Raises:
        HTTPException: If key is sensitive or not found
    """
    try:
        # Block access to sensitive keys
        sensitive_keys = ["openrouter_api_key", "secret_key", "password", "token"]
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot retrieve sensitive configuration values"
            )
        
        value = await Configuration.get_value(db, key)
        
        if value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration key not found: {key}"
            )
        
        return {
            "key": key,
            "value": value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get configuration {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )


@router.delete("/setting/{key}")
async def delete_configuration_value(
    key: str,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete a configuration value.
    
    Args:
        key: Configuration key to delete
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Block deletion of critical keys
        protected_keys = ["database_url", "secret_key"]
        if key.lower() in protected_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete protected configuration keys"
            )
        
        deleted = await Configuration.delete_value(db, key)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration key not found: {key}"
            )
        
        logger.info(f"Deleted configuration value: {key}")
        
        return {
            "success": True,
            "message": f"Successfully deleted configuration '{key}'",
            "deleted_key": key
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete configuration {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete configuration: {str(e)}"
        )