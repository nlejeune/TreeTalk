"""
Import API routes - Handle GEDCOM file uploads and processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from ..utils.database import get_db
from ..services.gedcom_parser import GedcomParserService

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoint to upload and process a GEDCOM file
@router.post("/gedcom")
async def upload_gedcom(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a GEDCOM file."""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.ged', '.gedcom')):
            raise HTTPException(status_code=400, detail="Only GEDCOM (.ged) files are supported")
        
        # Use transaction for duplicate checking and creation
        from ..models.source import Source
        from sqlalchemy import and_
        
        try:
            # Start transaction
            db.begin()
            
            # Check for existing sources with the same filename (case insensitive)
            existing_source = db.query(Source).filter(
                and_(
                    Source.name.ilike(file.filename),  # Case insensitive comparison
                    Source.type == "gedcom",
                    Source.status == "active"
                )
            ).with_for_update().first()  # Lock for update to prevent race conditions
            
            if existing_source:
                db.rollback()
                return {
                    "message": f"GEDCOM file '{file.filename}' already exists",
                    "task_id": "duplicate",
                    "source_id": str(existing_source.id),
                    "statistics": {
                        "individuals_imported": 0,
                        "relationships_imported": 0
                    },
                    "duplicate": True
                }
            
            # If we get here, no duplicate exists, continue with import
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error checking for duplicates: {str(e)}")
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.ged")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process GEDCOM file
        parser_service = GedcomParserService(db)
        result = await parser_service.parse_and_import_gedcom(
            file_path=file_path,
            source_name=file.filename,
            source_description=f"Uploaded GEDCOM file: {file.filename}"
        )
        
        return {
            "message": "GEDCOM file uploaded and processed successfully",
            "task_id": file_id,
            "source_id": result["source_id"],
            "statistics": {
                "individuals_imported": result["individuals_imported"],
                "relationships_imported": result["relationships_imported"]
            },
            "duplicate": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing GEDCOM file: {str(e)}")

# Endpoint to get the status of an import task
@router.get("/status/{task_id}")
async def get_import_status(task_id: str):
    """Get the status of a GEDCOM import task."""
    # In a production system, this would check a task queue or database
    # For now, we'll assume all imports are completed immediately
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "message": "Import completed successfully"
    }