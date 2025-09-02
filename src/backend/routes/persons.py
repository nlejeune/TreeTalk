"""
Person API Routes - Individual Management Endpoints

This module provides RESTful API endpoints for managing individual persons
in the genealogy database. Core functionality for family tree exploration.

Available Endpoints:
- GET /api/persons/ - List all persons with pagination and filtering
- GET /api/persons/{person_id} - Get individual person details  
- GET /api/persons/{person_id}/family-tree - Get family tree data for visualization
- PUT /api/persons/{person_id} - Update person information
- DELETE /api/persons/{person_id} - Delete person (admin only)

Features:
- Comprehensive person data retrieval
- Family tree generation for visualization
- Search and filtering capabilities
- Source-based data filtering
- Performance-optimized database queries

Family Tree Generation:
The family-tree endpoint generates optimized data structures for
frontend visualization, including:
- Person details with birth/death information
- Relationship mappings for graph generation  
- Color coding by gender and living status
- Efficient data formatting for Plotly/NetworkX
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from ..utils.database import get_db
from ..models.person import Person
from ..models.relationship import Relationship
from ..services.family_service import FamilyService

router = APIRouter()

# Endpoint to get a list of persons with optional filtering and pagination
@router.get("/", response_model=List[Dict[str, Any]])
async def get_persons(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    search: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get persons with optional filtering."""
    try:
        query = db.query(Person)
        
        # Filter by source
        if source_id:
            query = query.filter(Person.source_id == uuid.UUID(source_id))
        
        # Search by name
        if search:
            query = query.filter(Person.name.ilike(f"%{search}%"))
        
        # Apply pagination
        persons = query.offset(offset).limit(limit).all()
        
        result = []
        for person in persons:
            result.append({
                "id": str(person.id),
                "source_id": str(person.source_id),
                "gedcom_id": person.gedcom_id,
                "name": person.name,
                "given_names": person.given_names,
                "surname": person.surname,
                "gender": person.gender,
                "is_living": person.is_living,
                "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                "birth_date_text": person.birth_date_text,
                "birth_place": person.birth_place,
                "death_date": person.death_date.isoformat() if person.death_date else None,
                "death_date_text": person.death_date_text,
                "death_place": person.death_place,
                "occupation": person.occupation,
                "religion": person.religion,
                "notes": person.notes
            })
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching persons: {str(e)}")

# Endpoint to get details of a specific person by ID
@router.get("/{person_id}")
async def get_person(person_id: str, db: Session = Depends(get_db)):
    """Get a specific person by ID."""
    try:
        person = db.query(Person).filter(Person.id == uuid.UUID(person_id)).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        return {
            "id": str(person.id),
            "source_id": str(person.source_id),
            "gedcom_id": person.gedcom_id,
            "external_id": person.external_id,
            "name": person.name,
            "given_names": person.given_names,
            "surname": person.surname,
            "name_suffix": person.name_suffix,
            "nickname": person.nickname,
            "gender": person.gender,
            "is_living": person.is_living,
            "birth_date": person.birth_date.isoformat() if person.birth_date else None,
            "birth_date_text": person.birth_date_text,
            "birth_place": person.birth_place,
            "death_date": person.death_date.isoformat() if person.death_date else None,
            "death_date_text": person.death_date_text,
            "death_place": person.death_place,
            "occupation": person.occupation,
            "religion": person.religion,
            "notes": person.notes,
            "confidence_level": person.confidence_level,
            "created_at": person.created_at.isoformat(),
            "updated_at": person.updated_at.isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching person: {str(e)}")

# Endpoint to get family tree data for a specific person
@router.get("/{person_id}/family-tree")
async def get_family_tree(
    person_id: str,
    generations: int = Query(3, ge=1, le=5, description="Number of generations to include"),
    db: Session = Depends(get_db)
):
    """Get family tree data for visualization."""
    try:
        person = db.query(Person).filter(Person.id == uuid.UUID(person_id)).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        family_service = FamilyService(db)
        tree_data = await family_service.get_family_tree(person.id, generations)
        
        return tree_data
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching family tree: {str(e)}")

# Endpoint to get ancestors of a specific person
@router.get("/{person_id}/ancestors")
async def get_ancestors(
    person_id: str,
    generations: int = Query(5, ge=1, le=10, description="Number of generations to go back"),
    db: Session = Depends(get_db)
):
    """Get ancestors of a person."""
    try:
        person = db.query(Person).filter(Person.id == uuid.UUID(person_id)).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        family_service = FamilyService(db)
        ancestors = await family_service.get_ancestors(person.id, generations)
        
        return {
            "person_id": str(person.id),
            "person_name": person.name,
            "ancestors": ancestors
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ancestors: {str(e)}")
    
# Endpoint to get descendants of a specific person
@router.get("/{person_id}/descendants")
async def get_descendants(
    person_id: str,
    generations: int = Query(5, ge=1, le=10, description="Number of generations to go forward"),
    db: Session = Depends(get_db)
):
    """Get descendants of a person."""
    try:
        person = db.query(Person).filter(Person.id == uuid.UUID(person_id)).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        family_service = FamilyService(db)
        descendants = await family_service.get_descendants(person.id, generations)
        
        return {
            "person_id": str(person.id),
            "person_name": person.name,
            "descendants": descendants
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching descendants: {str(e)}")

# Endpoint to get all relationships of a specific person
@router.get("/{person_id}/relationships")
async def get_relationships(person_id: str, db: Session = Depends(get_db)):
    """Get all relationships for a person."""
    try:
        person = db.query(Person).filter(Person.id == uuid.UUID(person_id)).first()
        
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        # Get relationships where this person is involved
        relationships = db.query(Relationship).filter(
            (Relationship.person1_id == person.id) | 
            (Relationship.person2_id == person.id)
        ).all()
        
        result = []
        for rel in relationships:
            # Determine the other person and relationship direction
            if rel.person1_id == person.id:
                other_person = rel.person2
                relationship_type = rel.relationship_type
            else:
                other_person = rel.person1
                # Flip relationship perspective
                if rel.relationship_type == "parent":
                    relationship_type = "child"
                elif rel.relationship_type == "child":
                    relationship_type = "parent"
                else:
                    relationship_type = rel.relationship_type
            
            result.append({
                "relationship_id": str(rel.id),
                "relationship_type": relationship_type,
                "related_person": {
                    "id": str(other_person.id),
                    "name": other_person.name,
                    "birth_date": other_person.birth_date.isoformat() if other_person.birth_date else None,
                    "death_date": other_person.death_date.isoformat() if other_person.death_date else None,
                    "gender": other_person.gender,
                    "is_living": other_person.is_living
                },
                "start_date": rel.start_date.isoformat() if rel.start_date else None,
                "end_date": rel.end_date.isoformat() if rel.end_date else None,
                "place": rel.place,
                "notes": rel.notes
            })
        
        return {
            "person_id": str(person.id),
            "person_name": person.name,
            "relationships": result
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid person ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching relationships: {str(e)}")