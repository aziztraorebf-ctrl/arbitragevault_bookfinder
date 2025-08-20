from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class BatchStatus(enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

class Batch(Base):
    """Batch model for analysis runs"""
    __tablename__ = 'batches'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING)
    items_total = Column(Integer, default=0)
    items_processed = Column(Integer, default=0)
    strategy_snapshot = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationship
    analyses = relationship("Analysis", back_populates="batch", cascade="all, delete-orphan")
