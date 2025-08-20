from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ..deps.database import get_sync_db_dependency
from ..schemas.batch import BatchOut, BatchStatusUpdateIn
from ....models.batch import Batch, BatchStatus
from ....models.analysis import Analysis
from ....core.exceptions import map_exception_to_http, NotFoundError

router = APIRouter()


@router.get("/", response_model=List[BatchOut])
async def list_batches(
    db: Session = Depends(get_sync_db_dependency)
):
    """Liste des batches avec status + progress_metrics
    
    Récupère tous les batches avec leurs métriques de progression calculées :
    - Status du batch (PENDING, RUNNING, DONE, FAILED)
    - Compteurs d'items (total, processed, remaining)
    - Pourcentage de progression
    - Timestamps de création/démarrage/fin
    """
    try:
        # Récupérer batches avec comptage d'analyses
        batches_query = db.query(
            Batch,
            func.coalesce(func.count(Analysis.id), 0).label('analysis_count')
        ).outerjoin(Analysis).group_by(Batch.id).order_by(Batch.created_at.desc())
        
        batches_data = batches_query.all()
        
        result = []
        for batch, analysis_count in batches_data:
            # Mettre à jour items_total si pas défini
            if batch.items_total == 0 and analysis_count > 0:
                batch.items_total = analysis_count
                
            batch_out = BatchOut.from_orm(batch)
            result.append(batch_out)
        
        return result
        
    except Exception as e:
        raise map_exception_to_http(e)


@router.get("/stats", response_model=dict)
async def get_batches_stats(
    db: Session = Depends(get_sync_db_dependency)
):
    """Statistiques globales des batches
    
    Fournit un overview des batches et analyses :
    - Nombre total de batches par statut
    - Nombre total d'analyses
    - Batches actifs (RUNNING)
    - Métriques de performance globales
    """
    try:
        # Compter batches par statut
        status_counts = db.query(
            Batch.status,
            func.count(Batch.id).label('count')
        ).group_by(Batch.status).all()
        
        status_dict = {status.value: 0 for status in BatchStatus}
        for status, count in status_counts:
            status_dict[status.value] = count
        
        # Compter analyses totales
        total_analyses = db.query(func.count(Analysis.id)).scalar() or 0
        
        # Batches en cours
        running_batches = db.query(func.count(Batch.id)).filter(
            Batch.status == BatchStatus.RUNNING
        ).scalar() or 0
        
        # Batch le plus récent
        latest_batch = db.query(Batch).order_by(
            Batch.created_at.desc()
        ).first()
        
        return {
            "batches_by_status": status_dict,
            "total_batches": sum(status_dict.values()),
            "total_analyses": total_analyses,
            "running_batches": running_batches,
            "latest_batch_id": latest_batch.id if latest_batch else None,
            "latest_batch_created": latest_batch.created_at if latest_batch else None
        }
        
    except Exception as e:
        raise map_exception_to_http(e)


@router.patch("/{batch_id}/status", response_model=BatchOut)
async def update_batch_status(
    batch_id: int = Path(..., description="Batch ID"),
    status_update: BatchStatusUpdateIn = ...,
    db: Session = Depends(get_sync_db_dependency)
):
    """Mise à jour du statut de batch avec validation
    
    Met à jour le statut d'un batch avec validation dans le repository :
    - Validation des transitions de statut
    - Mise à jour des timestamps appropriés
    - Mise à jour du compteur d'items traités
    - Validation de cohérence des données
    """
    try:
        # Récupérer le batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise NotFoundError("Batch", batch_id)
        
        # Validation des transitions de statut
        old_status = batch.status
        new_status = status_update.status
        
        # Validation business logic pour transitions
        valid_transitions = {
            BatchStatus.PENDING: [BatchStatus.RUNNING, BatchStatus.FAILED],
            BatchStatus.RUNNING: [BatchStatus.DONE, BatchStatus.FAILED],
            BatchStatus.DONE: [],  # Terminal state
            BatchStatus.FAILED: [BatchStatus.PENDING]  # Peut redémarrer
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "invalid_status_transition",
                    "message": f"Cannot transition from {old_status.value} to {new_status.value}",
                    "current_status": old_status.value,
                    "requested_status": new_status.value
                }
            )
        
        # Mettre à jour le statut
        batch.status = new_status
        
        # Mettre à jour les timestamps selon le nouveau statut
        now = datetime.utcnow()
        
        if new_status == BatchStatus.RUNNING and old_status == BatchStatus.PENDING:
            batch.started_at = now
            
        elif new_status in [BatchStatus.DONE, BatchStatus.FAILED]:
            batch.finished_at = now
            
        elif new_status == BatchStatus.PENDING and old_status == BatchStatus.FAILED:
            # Reset pour redémarrage
            batch.started_at = None
            batch.finished_at = None
        
        # Mettre à jour le compteur si fourni
        if status_update.items_processed is not None:
            # Validation que items_processed <= items_total
            if batch.items_total > 0 and status_update.items_processed > batch.items_total:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": "invalid_items_processed",
                        "message": f"items_processed ({status_update.items_processed}) cannot exceed items_total ({batch.items_total})"
                    }
                )
            
            batch.items_processed = status_update.items_processed
        
        db.commit()
        
        return BatchOut.from_orm(batch)
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise map_exception_to_http(e)


@router.get("/{batch_id}", response_model=BatchOut)
async def get_batch(
    batch_id: int = Path(..., description="Batch ID"),
    db: Session = Depends(get_sync_db_dependency)
):
    """Récupération d'un batch spécifique
    
    Récupère les détails d'un batch avec ses métriques de progression.
    """
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise NotFoundError("Batch", batch_id)
        
        return BatchOut.from_orm(batch)
        
    except Exception as e:
        raise map_exception_to_http(e)
