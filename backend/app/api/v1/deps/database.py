from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from ....core.database import get_db as get_sync_db, SessionLocal
from ....config.settings import settings

# ============================================================================
# ASYNC DATABASE SESSION (1 session par requête via yield)
# ============================================================================

# Create async engine if needed (future enhancement)
# For Phase 1.3, we'll use sync sessions wrapped appropriately

async def get_db() -> AsyncGenerator[Session, None]:
    """Dependency to get database session for FastAPI
    
    Note: Using synchronous session for Phase 1.3
    Future: Migrate to async SQLAlchemy for true async operations
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alternative sync version for immediate use
def get_sync_db_dependency() -> Generator[Session, None, None]:
    """Synchronous database dependency"""
    return get_sync_db()
