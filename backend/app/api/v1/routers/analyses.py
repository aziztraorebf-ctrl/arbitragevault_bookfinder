from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal

from ..deps.database import get_sync_db_dependency
from ..schemas.analysis import (
    AnalysisOut, AnalysisCreateIn, AnalysisFilters, TopAnalysisParams
)
from ..schemas.common import PageOut
from ....repositories.analysis import AnalysisRepository
from ....repositories.base import FilterCriteria, FilterCondition, Page
from ....core.exceptions import map_exception_to_http, NotFoundError
from ....models.batch import Batch

router = APIRouter()


@router.post("/", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_in: AnalysisCreateIn,
    db: Session = Depends(get_sync_db_dependency)
):
    """Création d'analyse — admin/outil interne uniquement
    
    Crée une nouvelle analyse pour un batch donné.
    Gère automatiquement la normalisation ISBN et la détection de doublons.
    """
    try:
        # Vérifier que le batch existe
        batch = db.query(Batch).filter(Batch.id == analysis_in.batch_id).first()
        if not batch:
            raise NotFoundError("Batch", analysis_in.batch_id)
        
        # Créer l'analyse via repository
        repo = AnalysisRepository(db)
        analysis = repo.create_analysis(
            batch_id=analysis_in.batch_id,
            isbn_or_asin=analysis_in.isbn_or_asin,
            title=analysis_in.title,
            current_price=analysis_in.current_price,
            target_price=analysis_in.target_price,
            profit=analysis_in.profit,
            roi_percent=analysis_in.roi_percent,
            velocity_score=analysis_in.velocity_score,
            risk_level=analysis_in.risk_level,
            bsr=analysis_in.bsr,
            raw_keepa=analysis_in.raw_keepa
        )
        
        db.commit()
        return analysis
        
    except Exception as e:
        db.rollback()
        raise map_exception_to_http(e)


@router.get("/", response_model=PageOut[AnalysisOut])
async def list_analyses(
    batch_id: int = Query(..., description="Batch ID (required)"),
    min_roi: Optional[Decimal] = Query(None, ge=0, description="Minimum ROI percentage"),
    max_roi: Optional[Decimal] = Query(None, ge=0, description="Maximum ROI percentage"),
    min_velocity: Optional[Decimal] = Query(None, ge=0, description="Minimum velocity score"),
    max_velocity: Optional[Decimal] = Query(None, ge=0, description="Maximum velocity score"),
    profit_min: Optional[Decimal] = Query(None, description="Minimum profit"),
    profit_max: Optional[Decimal] = Query(None, description="Maximum profit"),
    isbn_list: Optional[str] = Query(None, description="Comma-separated ISBN/ASIN list"),
    sort: Optional[str] = Query("roi_percent", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=1000, description="Limit for pagination"),
    db: Session = Depends(get_sync_db_dependency)
):
    """Liste + filtres des analyses
    
    Récupère les analyses d'un batch avec filtrage avancé :
    - Filtres par ROI, velocity, profit (min/max)
    - Filtrage par liste d'ISBN/ASIN
    - Tri configurable avec validation
    - Pagination avec offset/limit
    """
    try:
        # Vérifier que le batch existe
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise NotFoundError("Batch", batch_id)
        
        repo = AnalysisRepository(db)
        
        # Construction des filtres
        filters = []
        
        if min_roi is not None:
            filters.append(FilterCriteria(
                field="roi_percent",
                condition=FilterCondition.GTE,
                value=min_roi
            ))
            
        if max_roi is not None:
            filters.append(FilterCriteria(
                field="roi_percent",
                condition=FilterCondition.LTE,
                value=max_roi
            ))
            
        if min_velocity is not None:
            filters.append(FilterCriteria(
                field="velocity_score",
                condition=FilterCondition.GTE,
                value=min_velocity
            ))
            
        if max_velocity is not None:
            filters.append(FilterCriteria(
                field="velocity_score",
                condition=FilterCondition.LTE,
                value=max_velocity
            ))
            
        if profit_min is not None:
            filters.append(FilterCriteria(
                field="profit",
                condition=FilterCondition.GTE,
                value=profit_min
            ))
            
        if profit_max is not None:
            filters.append(FilterCriteria(
                field="profit",
                condition=FilterCondition.LTE,
                value=profit_max
            ))
        
        # Parse ISBN list
        isbn_list_parsed = None
        if isbn_list:
            isbn_list_parsed = [isbn.strip() for isbn in isbn_list.split(",") if isbn.strip()]
        
        # Calculer page et page_size depuis offset/limit
        page_size = limit
        page = (offset // page_size) + 1
        
        # Récupérer analyses filtrées
        result = repo.list_filtered(
            batch_id=batch_id,
            filters=filters if filters else None,
            isbn_list=isbn_list_parsed,
            sort_by=sort if sort else None,
            sort_desc=sort_desc,
            page=page,
            page_size=page_size
        )
        
        # Convertir Page[Analysis] vers PageOut[AnalysisOut]
        return PageOut(
            items=[AnalysisOut.from_orm(item) for item in result.items],
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )
        
    except Exception as e:
        raise map_exception_to_http(e)


@router.get("/top", response_model=List[AnalysisOut])
async def get_top_analyses(
    batch_id: int = Query(..., description="Batch ID (required)"),
    n: int = Query(10, ge=1, le=100, description="Number of top items"),
    strategy: str = Query("balanced", regex="^(roi|velocity|profit|balanced)$", 
                         description="Strategy: roi|velocity|profit|balanced"),
    db: Session = Depends(get_sync_db_dependency)
):
    """Top N analyses par stratégie
    
    Récupère les meilleures analyses selon la stratégie choisie :
    - roi: Tri par ROI décroissant
    - velocity: Tri par score de vélocité décroissant
    - profit: Tri par profit décroissant  
    - balanced: Score pondéré (60% ROI + 40% velocity)
    """
    try:
        # Vérifier que le batch existe
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise NotFoundError("Batch", batch_id)
        
        repo = AnalysisRepository(db)
        
        # Récupérer top analyses
        top_analyses = repo.top_n_for_batch(
            batch_id=batch_id,
            strategy=strategy,
            limit=n
        )
        
        return [AnalysisOut.from_orm(analysis) for analysis in top_analyses]
        
    except Exception as e:
        raise map_exception_to_http(e)
