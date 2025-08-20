from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import and_, or_, func, literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ✅ FIX: Import missing exception
from .base import BaseRepository, FilterCriteria, Page, DuplicateIsbnInBatchError, InvalidFilterFieldError
from ..models.analysis import Analysis

class AnalysisRepository(BaseRepository[Analysis]):
    """Repository for Analysis operations with enhanced filtering and sorting"""
    
    # ✅ PATCH 2: Validation stricte des champs
    SORTABLE_FIELDS = {
        'roi_percent', 'velocity_score', 'profit', 'current_price', 'bsr', 'created_at'
    }
    
    FILTERABLE_FIELDS = {
        'roi_percent', 'velocity_score', 'profit', 'current_price', 'bsr', 
        'risk_level', 'isbn_or_asin'
    }
    
    def __init__(self, session: Session):
        super().__init__(session, Analysis)
    
    def create_analysis(  # ✅ FIX: Remove async - synchronous SQLAlchemy
        self,
        batch_id: int,
        isbn_or_asin: str,
        title: Optional[str] = None,
        current_price: Optional[Decimal] = None,
        target_price: Optional[Decimal] = None,
        profit: Optional[Decimal] = None,
        roi_percent: Optional[Decimal] = None,
        velocity_score: Optional[Decimal] = None,
        risk_level: Optional[str] = None,
        bsr: Optional[int] = None,
        raw_keepa: Optional[str] = None
    ) -> Analysis:
        """Create new analysis with duplicate protection"""
        
        # Normaliser ISBN/ASIN
        isbn_or_asin = isbn_or_asin.strip().upper()
        
        analysis = Analysis(
            batch_id=batch_id,
            isbn_or_asin=isbn_or_asin,
            title=title,
            current_price=current_price,
            target_price=target_price,
            profit=profit,
            roi_percent=roi_percent,
            velocity_score=velocity_score,
            risk_level=risk_level,
            bsr=bsr,
            raw_keepa=raw_keepa
        )
        
        try:
            self.session.add(analysis)
            self.session.flush()  # ✅ FIX: Synchronous flush
            return analysis
        except IntegrityError as e:
            # ✅ PATCH 4: Gestion d'erreur avec rollback
            self.session.rollback()  # ✅ FIX: Synchronous rollback
            if "uq_batch_isbn" in str(e.orig):
                raise DuplicateIsbnInBatchError(
                    f"ISBN/ASIN {isbn_or_asin} already exists in batch {batch_id}"
                )
            raise  # Re-raise other integrity errors
    
    def list_filtered(  # ✅ FIX: Remove async 
        self,
        batch_id: int,
        filters: Optional[List[FilterCriteria]] = None,
        isbn_list: Optional[List[str]] = None,  # ✅ PATCH 1: Support isbn_list
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> Page[Analysis]:
        """List analyses with complex filtering including ISBN list"""
        
        query = self.session.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        # ✅ PATCH 1: Filtrage par liste d'ISBN/ASIN
        if isbn_list:
            # Normaliser la liste
            normalized_isbns = [isbn.strip().upper() for isbn in isbn_list]
            query = query.filter(Analysis.isbn_or_asin.in_(normalized_isbns))
        
        # Application des autres filtres
        if filters:
            for criteria in filters:
                if criteria.field not in self.FILTERABLE_FIELDS:
                    raise InvalidFilterFieldError(f"Field {criteria.field} is not filterable")
                
                column = getattr(Analysis, criteria.field)
                condition = self._build_filter_condition(column, criteria)
                query = query.filter(condition)
        
        # ✅ PATCH 2: Validation stricte du tri via _paginate
        return self._paginate(query, page, page_size, sort_by, sort_desc)  # ✅ FIX: Remove await
    
    def top_n_for_batch(  # ✅ FIX: Remove async
        self,
        batch_id: int,
        strategy: str = "balanced",
        limit: int = 10
    ) -> List[Analysis]:
        """Get top N analyses for batch using specified strategy"""
        
        query = self.session.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        if strategy == "roi":
            query = query.order_by(Analysis.roi_percent.desc())
        elif strategy == "velocity":
            query = query.order_by(Analysis.velocity_score.desc())
        elif strategy == "profit":
            query = query.order_by(Analysis.profit.desc())
        elif strategy == "balanced":
            # ✅ PATCH 3: Stratégie balanced avec Decimal précis
            balanced_score = (
                Analysis.roi_percent * literal(Decimal("0.6")) +
                Analysis.velocity_score * literal(Decimal("0.4"))
            )
            query = query.order_by(balanced_score.desc())
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Stable sort avec ID
        query = query.order_by(Analysis.id.asc())
        
        return query.limit(limit).all()
    
    def count_by_thresholds(  # ✅ FIX: Remove async
        self,
        batch_id: int,
        roi_threshold: Optional[Decimal] = None,
        velocity_threshold: Optional[Decimal] = None,
        profit_threshold: Optional[Decimal] = None
    ) -> Dict[str, int]:
        """Count analyses by various thresholds"""
        
        base_query = self.session.query(Analysis).filter(Analysis.batch_id == batch_id)
        
        results = {
            "total": base_query.count()
        }
        
        if roi_threshold:
            results["high_roi"] = base_query.filter(
                Analysis.roi_percent >= roi_threshold
            ).count()
        
        if velocity_threshold:
            results["high_velocity"] = base_query.filter(
                Analysis.velocity_score >= velocity_threshold
            ).count()
        
        if profit_threshold:
            results["high_profit"] = base_query.filter(
                Analysis.profit >= profit_threshold
            ).count()
        
        # Golden opportunities (multi-criteria)
        if all([roi_threshold, velocity_threshold, profit_threshold]):
            results["golden"] = base_query.filter(
                and_(
                    Analysis.roi_percent >= roi_threshold,
                    Analysis.velocity_score >= velocity_threshold,
                    Analysis.profit >= profit_threshold
                )
            ).count()
        
        return results
    
    def delete_by_batch(self, batch_id: int) -> int:  # ✅ FIX: Remove async
        """Delete all analyses for a batch"""
        count = self.session.query(Analysis).filter(
            Analysis.batch_id == batch_id
        ).count()
        
        self.session.query(Analysis).filter(
            Analysis.batch_id == batch_id
        ).delete()
        
        return count
    
    def delete_by_ids(self, analysis_ids: List[int]) -> int:  # ✅ FIX: Remove async
        """Delete analyses by ID list"""
        count = self.session.query(Analysis).filter(
            Analysis.id.in_(analysis_ids)
        ).count()
        
        self.session.query(Analysis).filter(
            Analysis.id.in_(analysis_ids)
        ).delete(synchronize_session=False)
        
        return count