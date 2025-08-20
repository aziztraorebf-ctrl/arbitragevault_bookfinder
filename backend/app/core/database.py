from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
from ..config.settings import settings

# Create engine with settings
engine = create_engine(
    settings.database_url,
    echo=settings.database.echo_sql,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # ✅ TECH DEBT: Keep objects accessible after commit
    bind=engine
)

# Base for models
Base = declarative_base()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions for testing and setup
def create_tables():
    """Create all tables (for development/testing)"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables (for development/testing)"""
    Base.metadata.drop_all(bind=engine)

def get_session() -> Session:
    """Get a database session (for scripts/testing)"""
    return SessionLocal()
