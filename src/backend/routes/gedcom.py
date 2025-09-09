"""
GEDCOM Management API Routes

This module provides REST API endpoints for GEDCOM file management including
upload, processing, status tracking, and deletion of genealogical data sources.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Dict, Any
import logging
from uuid import UUID

from utils.database import get_database_session
from models.source import Source
from services.gedcom_parser import GedcomParserService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_gedcom_file(
    file: UploadFile = File(...),
    source_name: str = None,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Upload and process a GEDCOM file.
    
    Args:
        file: Uploaded GEDCOM file
        source_name: Optional custom name for the data source
        db: Database session
        
    Returns:
        Dict containing source information and import statistics
        
    Raises:
        HTTPException: If file is invalid or processing fails
    """
    try:
        # Validate file
        if not file.filename.lower().endswith('.ged'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .ged files are supported"
            )
        
        if file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50MB limit"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        # Process GEDCOM file
        parser_service = GedcomParserService(db)
        source, import_stats = await parser_service.parse_and_import_file(
            file_content=file_content,
            filename=file.filename,
            source_name=source_name
        )
        
        logger.info(f"GEDCOM file processed successfully: {source.id}")
        
        return {
            "success": True,
            "source": source.to_dict(),
            "import_statistics": import_stats,
            "message": f"Successfully imported {import_stats['persons_imported']} persons and {import_stats['relationships_imported']} relationships"
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"GEDCOM upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process GEDCOM file: {str(e)}"
        )


@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_gedcom_sources(
    active_only: bool = True,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get list of all GEDCOM sources.
    
    Args:
        active_only: Whether to return only active sources
        db: Database session
        
    Returns:
        List of source information dictionaries
    """
    try:
        query = select(Source)
        
        if active_only:
            query = query.where(Source.is_active == True)
        
        result = await db.execute(query.order_by(Source.import_date.desc()))
        sources = result.scalars().all()
        
        return [source.to_dict() for source in sources]
        
    except Exception as e:
        logger.error(f"Failed to get GEDCOM sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GEDCOM sources"
        )


@router.get("/sources/{source_id}", response_model=Dict[str, Any])
async def get_gedcom_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get detailed information about a specific GEDCOM source.
    
    Args:
        source_id: UUID of the source
        db: Database session
        
    Returns:
        Detailed source information
        
    Raises:
        HTTPException: If source not found
    """
    try:
        result = await db.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source_id}"
            )
        
        return source.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve source information"
        )


@router.delete("/sources/{source_id}")
async def delete_gedcom_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Delete a GEDCOM source and all associated data.
    
    Args:
        source_id: UUID of the source to delete
        db: Database session
        
    Returns:
        Success confirmation
        
    Raises:
        HTTPException: If source not found or deletion fails
    """
    try:
        # Check if source exists
        result = await db.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source_id}"
            )
        
        source_name = source.name
        persons_count = source.persons_count
        
        # Delete source (cascade will handle related data)
        await db.execute(
            delete(Source).where(Source.id == source_id)
        )
        await db.commit()
        
        logger.info(f"Deleted GEDCOM source: {source_id} ({source_name})")
        
        return {
            "success": True,
            "message": f"Successfully deleted source '{source_name}' and {persons_count} associated persons",
            "deleted_source_id": str(source_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )


@router.get("/sources/{source_id}/statistics", response_model=Dict[str, Any])
async def get_source_statistics(
    source_id: UUID,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get detailed statistics for a GEDCOM source.
    
    Args:
        source_id: UUID of the source
        db: Database session
        
    Returns:
        Detailed statistics about the source data
        
    Raises:
        HTTPException: If source not found
    """
    try:
        # Get source
        result = await db.execute(
            select(Source).where(Source.id == source_id)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source not found: {source_id}"
            )
        
        # TODO: Add more detailed statistics queries
        # For now, return basic source statistics
        statistics = {
            "source_info": source.to_dict(),
            "data_quality": {
                "persons_with_birth_dates": 0,  # Would calculate from DB
                "persons_with_death_dates": 0,  # Would calculate from DB  
                "complete_names": 0,            # Would calculate from DB
                "relationships_verified": 0     # Would calculate from DB
            },
            "timeline": {
                "earliest_birth": None,         # Would calculate from DB
                "latest_birth": None,           # Would calculate from DB
                "span_years": 0                 # Would calculate from DB
            }
        }
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics for source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve source statistics"
        )