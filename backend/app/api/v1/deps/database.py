from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session

from ....core.database import get_db as get_sync_db, SessionLocal
from ....config.settings import settings

# ============================================================================
# DATABASE SESSION (1 session par requête via yield)
# ============================================================================

# For Phase 1.3, we use sync sessions to match our repository layer
# Future enhancement: Move to async SQLAlchemy for true async operations

def get_sync_db_dependency() -> Generator[Session, None, None]:
    """Dependency to get synchronous database session for FastAPI
    
    Provides 1 session per request via yield pattern.
    Session is automatically closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alternative async wrapper (future enhancement)
async def get_async_db_dependency() -> AsyncGenerator[Session, None]:
    """Async wrapper for database session
    
    Note: Currently wraps sync session for Phase 1.3 compatibility
    Future: Replace with native async SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
