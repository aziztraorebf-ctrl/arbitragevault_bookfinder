from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class BatchStatusEnum(str, Enum):
    """Batch status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class BatchOut(BaseModel):
    """Batch output schema"""
    id: int = Field(..., description="Batch ID")
    name: str = Field(..., description="Batch name")
    status: BatchStatusEnum = Field(..., description="Batch status")
    items_total: int = Field(..., description="Total items in batch")
    items_processed: int = Field(..., description="Items processed")
    strategy_snapshot: Optional[str] = Field(None, description="Strategy configuration snapshot")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Processing finish timestamp")
    
    # Computed progress metrics
    progress_percent: Optional[float] = Field(None, description="Processing progress percentage")
    items_remaining: int = Field(..., description="Items remaining to process")
    
    class Config:
        from_attributes = True
        use_enum_values = True
        
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate progress metrics
        if self.items_total > 0:
            self.progress_percent = round((self.items_processed / self.items_total) * 100, 1)
        else:
            self.progress_percent = 0.0
        
        self.items_remaining = max(0, self.items_total - self.items_processed)


class BatchStatusUpdateIn(BaseModel):
    """Batch status update input schema"""
    status: BatchStatusEnum = Field(..., description="New batch status")
    items_processed: Optional[int] = Field(None, ge=0, description="Update processed count")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "RUNNING",
                "items_processed": 25
            }
        }
