"""
Person Management API Routes

This module provides REST API endpoints for person search, retrieval,
and family tree data access for the TreeTalk genealogical application.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging
from uuid import UUID

from utils.database import get_database_session
from services.family_service import FamilyService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_persons(
    q: str = Query(..., description="Search query (name or partial name)"),
    source_id: Optional[UUID] = Query(None, description="Limit search to specific source"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Search for persons by name or other criteria.
    
    Args:
        q: Search query string
        source_id: Optional source ID to limit search
        limit: Maximum number of results to return (1-100)
        db: Database session
        
    Returns:
        List of matching persons with relevance scoring
        
    Raises:
        HTTPException: If search fails
    """
    try:
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long"
            )
        
        family_service = FamilyService(db)
        persons = await family_service.search_persons(
            query=q,
            source_id=source_id,
            limit=limit
        )
        
        logger.info(f"Person search '{q}' returned {len(persons)} results")
        
        return persons
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Person search failed for '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/{person_id}", response_model=Dict[str, Any])
async def get_person_details(
    person_id: UUID,
    include_events: bool = Query(True, description="Include life events"),
    include_relationships: bool = Query(True, description="Include family relationships"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get detailed information about a specific person.
    
    Args:
        person_id: UUID of the person
        include_events: Whether to include life events
        include_relationships: Whether to include family relationships
        db: Database session
        
    Returns:
        Detailed person information
        
    Raises:
        HTTPException: If person not found
    """
    try:
        family_service = FamilyService(db)
        person_data = await family_service.get_person_details(
            person_id=person_id,
            include_events=include_events,
            include_relationships=include_relationships
        )
        
        return person_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get person details for {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve person details"
        )


@router.get("/{person_id}/family-tree", response_model=Dict[str, Any])
async def get_family_tree(
    person_id: UUID,
    max_generations: int = Query(4, ge=1, le=8, description="Maximum generations to include"),
    source_id: Optional[UUID] = Query(None, description="Limit to specific source"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get family tree data centered on a specific person.
    
    Args:
        person_id: UUID of the focal person
        max_generations: Maximum generations to include (1-8)
        source_id: Optional source ID to limit data
        db: Database session
        
    Returns:
        Family tree data with persons and relationships
        
    Raises:
        HTTPException: If person not found or retrieval fails
    """
    try:
        family_service = FamilyService(db)
        family_tree_data = await family_service.get_family_tree(
            focal_person_id=person_id,
            max_generations=max_generations,
            source_id=source_id
        )
        
        logger.info(f"Retrieved family tree for {person_id}: "
                   f"{family_tree_data['metadata']['total_persons']} persons")
        
        return family_tree_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get family tree for {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve family tree data"
        )


@router.get("/{person1_id}/relationship-path/{person2_id}", response_model=Optional[List[Dict[str, Any]]])
async def get_relationship_path(
    person1_id: UUID,
    person2_id: UUID,
    max_depth: int = Query(6, ge=1, le=10, description="Maximum path depth to search"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Find the relationship path between two persons.
    
    Args:
        person1_id: UUID of the first person
        person2_id: UUID of the second person
        max_depth: Maximum path depth to search (1-10)
        db: Database session
        
    Returns:
        Relationship path between the persons, or null if no connection
        
    Raises:
        HTTPException: If either person not found or search fails
    """
    try:
        if person1_id == person2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot find relationship path between the same person"
            )
        
        family_service = FamilyService(db)
        relationship_path = await family_service.get_relationship_path(
            person1_id=person1_id,
            person2_id=person2_id,
            max_depth=max_depth
        )
        
        if relationship_path:
            logger.info(f"Found relationship path between {person1_id} and {person2_id}")
        else:
            logger.info(f"No relationship path found between {person1_id} and {person2_id}")
        
        return relationship_path
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find relationship path between {person1_id} and {person2_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find relationship path"
        )


@router.get("/{person_id}/ancestors", response_model=List[Dict[str, Any]])
async def get_ancestors(
    person_id: UUID,
    generations: int = Query(4, ge=1, le=10, description="Number of ancestor generations"),
    source_id: Optional[UUID] = Query(None, description="Limit to specific source"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get ancestors of a specific person.
    
    Args:
        person_id: UUID of the person
        generations: Number of generations to retrieve
        source_id: Optional source ID to limit data
        db: Database session
        
    Returns:
        List of ancestor persons
        
    Raises:
        HTTPException: If person not found or retrieval fails
    """
    try:
        # This would be implemented using the family service
        # For now, return a placeholder response
        family_service = FamilyService(db)
        
        # Use family tree data and filter for ancestors
        family_tree = await family_service.get_family_tree(
            focal_person_id=person_id,
            max_generations=generations,
            source_id=source_id
        )
        
        # Filter for ancestor persons (would implement proper ancestor logic)
        ancestors = [
            person for person in family_tree["persons"]
            if person["id"] != str(person_id)  # Exclude focal person
        ]
        
        return ancestors
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get ancestors for {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ancestors"
        )


@router.get("/{person_id}/descendants", response_model=List[Dict[str, Any]])
async def get_descendants(
    person_id: UUID,
    generations: int = Query(4, ge=1, le=10, description="Number of descendant generations"),
    source_id: Optional[UUID] = Query(None, description="Limit to specific source"),
    db: AsyncSession = Depends(get_database_session)
):
    """
    Get descendants of a specific person.
    
    Args:
        person_id: UUID of the person
        generations: Number of generations to retrieve
        source_id: Optional source ID to limit data
        db: Database session
        
    Returns:
        List of descendant persons
        
    Raises:
        HTTPException: If person not found or retrieval fails
    """
    try:
        # This would be implemented using the family service
        # For now, return a placeholder response
        family_service = FamilyService(db)
        
        # Use family tree data and filter for descendants
        family_tree = await family_service.get_family_tree(
            focal_person_id=person_id,
            max_generations=generations,
            source_id=source_id
        )
        
        # Filter for descendant persons (would implement proper descendant logic)
        descendants = [
            person for person in family_tree["persons"]
            if person["id"] != str(person_id)  # Exclude focal person
        ]
        
        return descendants
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get descendants for {person_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve descendants"
        )