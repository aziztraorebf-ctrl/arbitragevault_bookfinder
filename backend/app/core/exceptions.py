from fastapi import HTTPException, status
from typing import Dict, Type


class ArbitrageVaultException(Exception):
    """Base exception for ArbitrageVault"""
    pass


class NotFoundError(ArbitrageVaultException):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str | int):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with identifier '{identifier}' not found")


# HTTP exception mapping
EXCEPTION_MAP: Dict[Type[Exception], int] = {
    # Repository exceptions → HTTP status codes
    NotFoundError: status.HTTP_404_NOT_FOUND,
}


def map_exception_to_http(exc: Exception) -> HTTPException:
    """Map custom exceptions to HTTP exceptions
    
    Erreurs → HTTP mapping selon spécifications:
    - InvalidSortFieldError → 422
    - DuplicateIsbnInBatchError → 409  
    - NotFoundError → 404
    - Le reste → 500 loggé
    """
    from ..repositories.base import InvalidSortFieldError, DuplicateIsbnInBatchError
    
    if isinstance(exc, InvalidSortFieldError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "invalid_sort_field",
                "message": str(exc),
                "type": "InvalidSortFieldError"
            }
        )
    
    elif isinstance(exc, DuplicateIsbnInBatchError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_isbn",
                "message": str(exc),
                "type": "DuplicateIsbnInBatchError"
            }
        )
    
    elif isinstance(exc, NotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": str(exc),
                "resource": exc.resource,
                "identifier": str(exc.identifier),
                "type": "NotFoundError"
            }
        )
    
    else:
        # Le reste → 500 loggé
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_server_error",
                "message": "An internal error occurred",
                "type": type(exc).__name__
            }
        )
