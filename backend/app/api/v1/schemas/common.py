from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PageOut(BaseModel, Generic[T]):
    """Generic pagination response schema"""
    items: List[T] = Field(..., description="List of items for current page")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ErrorDetail(BaseModel):
    """Error detail schema"""
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    field: str | None = Field(None, description="Field causing error (if applicable)")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    error: str = Field(..., description="Error category")
    detail: str = Field(..., description="Error description")
    errors: List[ErrorDetail] | None = Field(None, description="Detailed error list")
