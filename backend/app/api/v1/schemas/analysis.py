from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisOut(BaseModel):
    """Analysis output schema (sans raw_keepa par défaut)"""
    id: int = Field(..., description="Analysis ID")
    batch_id: int = Field(..., description="Batch ID")
    isbn_or_asin: str = Field(..., description="ISBN or ASIN")
    title: Optional[str] = Field(None, description="Book title")
    current_price: Optional[Decimal] = Field(None, description="Current market price")
    target_price: Optional[Decimal] = Field(None, description="Target selling price")
    profit: Optional[Decimal] = Field(None, description="Expected profit")
    roi_percent: Optional[Decimal] = Field(None, description="Return on investment percentage")
    velocity_score: Optional[Decimal] = Field(None, description="Velocity score (higher = faster turnover)")
    risk_level: Optional[str] = Field(None, description="Risk level assessment")
    bsr: Optional[int] = Field(None, description="Best Seller Rank")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class AnalysisDetailOut(AnalysisOut):
    """Analysis with raw_keepa data (for admin/detailed views)"""
    raw_keepa: Optional[str] = Field(None, description="Raw Keepa API response")


class AnalysisCreateIn(BaseModel):
    """Analysis creation input schema"""
    batch_id: int = Field(..., description="Batch ID")
    isbn_or_asin: str = Field(..., min_length=1, max_length=20, description="ISBN or ASIN")
    title: Optional[str] = Field(None, max_length=500, description="Book title")
    current_price: Optional[Decimal] = Field(None, ge=0, description="Current market price")
    target_price: Optional[Decimal] = Field(None, ge=0, description="Target selling price")
    profit: Optional[Decimal] = Field(None, description="Expected profit")
    roi_percent: Optional[Decimal] = Field(None, ge=0, le=1000, description="ROI percentage")
    velocity_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Velocity score")
    risk_level: Optional[str] = Field(None, max_length=20, description="Risk level")
    bsr: Optional[int] = Field(None, ge=1, description="Best Seller Rank")
    raw_keepa: Optional[str] = Field(None, description="Raw Keepa API response")


class AnalysisFilters(BaseModel):
    """Analysis filtering parameters"""
    batch_id: int = Field(..., description="Batch ID (required)")
    min_roi: Optional[Decimal] = Field(None, ge=0, description="Minimum ROI percentage")
    max_roi: Optional[Decimal] = Field(None, ge=0, description="Maximum ROI percentage")
    min_velocity: Optional[Decimal] = Field(None, ge=0, description="Minimum velocity score")
    max_velocity: Optional[Decimal] = Field(None, ge=0, description="Maximum velocity score")
    profit_min: Optional[Decimal] = Field(None, description="Minimum profit")
    profit_max: Optional[Decimal] = Field(None, description="Maximum profit")
    isbn_list: Optional[str] = Field(None, description="Comma-separated ISBN/ASIN list")
    sort: Optional[str] = Field("roi_percent", description="Sort field")
    sort_desc: bool = Field(True, description="Sort descending")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    limit: int = Field(50, ge=1, le=1000, description="Limit for pagination")


class TopAnalysisParams(BaseModel):
    """Top analysis query parameters"""
    batch_id: int = Field(..., description="Batch ID (required)")
    n: int = Field(10, ge=1, le=100, description="Number of top items")
    strategy: str = Field("balanced", description="Strategy: roi|velocity|profit|balanced")
    
    class Config:
        schema_extra = {
            "example": {
                "batch_id": 1,
                "n": 10,
                "strategy": "balanced"
            }
        }
