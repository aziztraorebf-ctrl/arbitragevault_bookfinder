from enum import Enum
from typing import List, Union, Any, Optional, TypeVar, Generic
from decimal import Decimal
from pydantic import BaseModel
from sqlalchemy import Column, and_, asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

T = TypeVar('T')

class FilterCondition(str, Enum):
    EQ = "eq"
    IN = "in"      # ✅ PATCH 1: Support filtrage multi-ISBN
    GTE = "gte"
    LTE = "lte" 
    GT = "gt"
    LT = "lt"

class FilterCriteria(BaseModel):
    field: str
    condition: FilterCondition  
    value: Union[str, int, float, Decimal, List[str]]  # ✅ Support List[str] pour IN

class Page(BaseModel, Generic[T]):
    """Generic pagination container"""
    items: List[T]
    page: int
    page_size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        arbitrary_types_allowed = True

class InvalidFilterFieldError(Exception):
    """Raised when trying to filter on invalid field"""
    pass

class InvalidSortFieldError(Exception):
    """✅ PATCH 2: Raised when trying to sort on invalid field"""
    pass

class DuplicateIsbnInBatchError(Exception):
    """✅ PATCH 4: Raised when trying to create duplicate ISBN in same batch"""
    pass

class BaseRepository(Generic[T]):
    """Enhanced base repository with advanced pagination and filtering"""
    
    FILTERABLE_FIELDS: set = set()
    SORTABLE_FIELDS: set = set()  # ✅ PATCH 2: Validation stricte
    
    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class
    
    def _build_filter_condition(self, column: Column, criteria: FilterCriteria):
        """Build SQLAlchemy filter condition from criteria"""
        
        if criteria.condition == FilterCondition.EQ:
            return column == criteria.value
        elif criteria.condition == FilterCondition.IN:
            # ✅ PATCH 1: Support pour IN avec liste de valeurs
            if not isinstance(criteria.value, list):
                raise ValueError(f"IN condition requires list value, got {type(criteria.value)}")
            return column.in_(criteria.value)
        elif criteria.condition == FilterCondition.GTE:
            return column >= criteria.value
        elif criteria.condition == FilterCondition.LTE:
            return column <= criteria.value
        elif criteria.condition == FilterCondition.GT:
            return column > criteria.value
        elif criteria.condition == FilterCondition.LT:
            return column < criteria.value
        else:
            raise ValueError(f"Unsupported filter condition: {criteria.condition}")
    
    def _paginate(  # ✅ FIX: Remove async for synchronous SQLAlchemy
        self, 
        query, 
        page: int, 
        page_size: int, 
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ) -> Page[T]:
        """Execute paginated query with sorting"""
        
        # ✅ PATCH 2: Validation stricte des champs de tri
        if sort_by:
            if sort_by not in self.SORTABLE_FIELDS:
                raise InvalidSortFieldError(f"Field {sort_by} is not sortable. Allowed: {self.SORTABLE_FIELDS}")
            
            column = getattr(self.model_class, sort_by)
            if sort_desc:
                query = query.order_by(desc(column), asc(self.model_class.id))
            else:
                query = query.order_by(asc(column), asc(self.model_class.id))
        else:
            # Default stable sorting
            query = query.order_by(asc(self.model_class.id))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        pages = (total + page_size - 1) // page_size
        has_next = page < pages
        has_prev = page > 1
        
        return Page(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )