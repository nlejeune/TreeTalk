"""
Configuration Model - Encrypted Application Settings

This module defines the Configuration model for storing encrypted application
settings including API keys and user preferences for the TreeTalk application.
"""

from sqlalchemy import Column, String, Text, DateTime, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import os
import base64
from typing import Optional, Any
import json

from utils.database import Base


class Configuration(Base):
    """Configuration model for encrypted application settings."""
    
    __tablename__ = "configuration"
    
    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    @staticmethod
    def _get_cipher() -> Fernet:
        """Get encryption cipher for configuration values."""
        key = os.environ.get("TREETALK_SECRET_KEY")
        if not key:
            # Generate a new key if none exists (development only)
            key = Fernet.generate_key()
            print(f"Generated new secret key: {key.decode()}")
            print("Set TREETALK_SECRET_KEY environment variable for production")
        else:
            # If key is provided as string, assume it's base64-encoded
            try:
                key = key.encode()
            except AttributeError:
                # Key is already bytes
                pass
            
            # Validate that the key is properly formatted for Fernet
            try:
                # Test the key by creating a Fernet instance
                test_cipher = Fernet(key)
            except Exception:
                # If the provided key is invalid, generate a new one for development
                print(f"Invalid TREETALK_SECRET_KEY provided, generating new one")
                key = Fernet.generate_key()
                print(f"Generated new secret key: {key.decode()}")
                print("Set TREETALK_SECRET_KEY environment variable with this value")
        
        return Fernet(key)
    
    @classmethod
    async def set_value(cls, db: AsyncSession, key: str, value: Any):
        """Set encrypted configuration value."""
        cipher = cls._get_cipher()
        
        # Convert value to JSON string
        json_value = json.dumps(value)
        
        # Encrypt the value
        encrypted_value = cipher.encrypt(json_value.encode()).decode()
        
        # Store or update in database
        result = await db.execute(select(cls).where(cls.key == key))
        config = result.scalar_one_or_none()
        if config:
            config.value = encrypted_value
            config.updated_at = func.now()
        else:
            config = cls(key=key, value=encrypted_value)
            db.add(config)
        
        await db.commit()
    
    @classmethod
    async def get_value(cls, db: AsyncSession, key: str, default: Any = None) -> Any:
        """Get decrypted configuration value."""
        result = await db.execute(select(cls).where(cls.key == key))
        config = result.scalar_one_or_none()
        if not config:
            return default
        
        try:
            cipher = cls._get_cipher()
            decrypted_value = cipher.decrypt(config.value.encode()).decode()
            return json.loads(decrypted_value)
        except Exception:
            return default
    
    @classmethod
    async def delete_value(cls, db: AsyncSession, key: str) -> bool:
        """Delete configuration value."""
        result = await db.execute(select(cls).where(cls.key == key))
        config = result.scalar_one_or_none()
        if config:
            db.delete(config)
            await db.commit()
            return True
        return False


async def get_database_url() -> str:
    """Get database URL from environment or configuration."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
    
    # Default development database URL
    return "postgresql+asyncpg://postgres:password@localhost:5432/treetalk"