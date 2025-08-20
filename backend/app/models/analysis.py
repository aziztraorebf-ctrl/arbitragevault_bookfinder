from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Analysis(Base):
    """Analysis model for book arbitrage opportunities"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.id'), nullable=False)
    isbn_or_asin = Column(String(20), nullable=False)
    title = Column(String(500), nullable=True)
    current_price = Column(Decimal(10, 2), nullable=True)
    target_price = Column(Decimal(10, 2), nullable=True)
    profit = Column(Decimal(10, 2), nullable=True)
    roi_percent = Column(Decimal(5, 2), nullable=True)
    velocity_score = Column(Decimal(5, 2), nullable=True)
    risk_level = Column(String(20), nullable=True)
    bsr = Column(Integer, nullable=True)
    raw_keepa = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint pour éviter les doublons (utilisé dans PATCH 4)
    __table_args__ = (
        UniqueConstraint('batch_id', 'isbn_or_asin', name='uq_batch_isbn'),
    )
    
    # Relationship
    batch = relationship("Batch", back_populates="analyses")
