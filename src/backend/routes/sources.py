"""
Sources API routes - Handle GEDCOM sources and data sources
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from ..utils.database import get_db
from ..models.source import Source
from ..models.person import Person

router = APIRouter()

# Endpoint to get all sources with statistics
@router.get("/", response_model=List[Dict[str, Any]])
async def get_sources(db: Session = Depends(get_db)):
    """Get all data sources."""
    try:
        sources = db.query(Source).filter(Source.status == "active").all()
        
        result = []
        for source in sources:
            # Count persons for this source
            person_count = db.query(Person).filter(Person.source_id == source.id).count()
            
            result.append({
                "id": str(source.id),
                "name": source.name,
                "type": source.type,
                "description": source.description,
                "file_path": source.file_path,
                "imported_at": source.imported_at.isoformat() if source.imported_at else None,
                "status": source.status,
                "metadata": source.source_metadata,
                "person_count": person_count
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")

# Endpoint to get a specific source by ID with detailed statistics
@router.get("/{source_id}")
async def get_source(source_id: str, db: Session = Depends(get_db)):
    """Get a specific source by ID."""
    try:
        source = db.query(Source).filter(Source.id == uuid.UUID(source_id)).first()
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Get detailed statistics
        person_count = db.query(Person).filter(Person.source_id == source.id).count()
        
        return {
            "id": str(source.id),
            "name": source.name,
            "type": source.type,
            "description": source.description,
            "file_path": source.file_path,
            "imported_at": source.imported_at.isoformat() if source.imported_at else None,
            "status": source.status,
            "metadata": source.source_metadata,
            "person_count": person_count,
            "created_at": source.created_at.isoformat(),
            "updated_at": source.updated_at.isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching source: {str(e)}")
    
# Endpoint to delete a source and all associated data
@router.delete("/{source_id}")
async def delete_source(source_id: str, db: Session = Depends(get_db)):
    """Delete a source and all associated data."""
    try:
        source = db.query(Source).filter(Source.id == uuid.UUID(source_id)).first()
        
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Delete the source (cascade will handle related records)
        db.delete(source)
        db.commit()
        
        return {"message": f"Source '{source.name}' and all associated data deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source ID format")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting source: {str(e)}")

# Endpoint to clean up duplicate GEDCOM sources
@router.post("/cleanup-duplicates")
async def cleanup_duplicate_sources(db: Session = Depends(get_db)):
    """Remove duplicate GEDCOM sources, keeping the most recent one."""
    try:
        from sqlalchemy import func, and_
        
        # Find duplicate sources by name and type
        duplicates = (
            db.query(Source.name, func.count(Source.id).label('count'))
            .filter(and_(Source.type == "gedcom", Source.status == "active"))
            .group_by(Source.name)
            .having(func.count(Source.id) > 1)
            .all()
        )
        
        removed_sources = []
        total_removed = 0
        
        for duplicate_name, count in duplicates:
            # Get all sources with this name, ordered by creation date (newest first)
            sources_to_process = (
                db.query(Source)
                .filter(and_(
                    Source.name == duplicate_name,
                    Source.type == "gedcom",
                    Source.status == "active"
                ))
                .order_by(Source.created_at.desc())
                .all()
            )
            
            # Keep the first (newest) and remove the rest
            sources_to_remove = sources_to_process[1:]
            
            for source in sources_to_remove:
                removed_sources.append({
                    "id": str(source.id),
                    "name": source.name,
                    "created_at": source.created_at.isoformat()
                })
                
                # Delete the source (cascade will handle related records)
                db.delete(source)
                total_removed += 1
        
        db.commit()
        
        return {
            "message": f"Cleanup completed: {total_removed} duplicate sources removed",
            "removed_sources": removed_sources,
            "total_removed": total_removed
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")