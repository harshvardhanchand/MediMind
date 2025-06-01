from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/", summary="Health Check", response_model=dict)
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: A simple response containing a status message.
    """
    return {"status": "ok", "message": "Medical Data Hub API is running"} 