"""
Authentication API routes - Basic auth placeholder
"""

from fastapi import APIRouter

router = APIRouter()

# Placeholder endpoints for login and logout
@router.post("/login")
async def login():
    """Login endpoint - placeholder for future implementation."""
    return {"message": "Authentication not implemented in MVP"}

# Placeholder logout endpoint
@router.post("/logout")
async def logout():
    """Logout endpoint - placeholder for future implementation."""
    return {"message": "Authentication not implemented in MVP"}