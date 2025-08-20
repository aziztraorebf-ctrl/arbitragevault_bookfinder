from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from ..deps.database import get_sync_db_dependency
from ....config.settings import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app.app_name,
        "version": settings.app.version,
        "timestamp": time.time()
    }


@router.get("/db")
async def database_health_check(db: Session = Depends(get_sync_db_dependency)):
    """Database connectivity health check"""
    try:
        start_time = time.time()
        
        # Simple database query
        result = db.execute(text("SELECT 1")).scalar()
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # ms
        
        if result == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "response_time_ms": response_time,
                "timestamp": time.time()
            }
        else:
            return {
                "status": "unhealthy",
                "database": "query_failed",
                "response_time_ms": response_time,
                "timestamp": time.time()
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "connection_failed",
            "error": str(e),
            "timestamp": time.time()
        }
