from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import traceback

from .exceptions import map_exception_to_http

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware pour gestion globale des erreurs"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            start_time = time.time()
            
            response = await call_next(request)
            
            # Log request timing
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} - "
                f"{response.status_code} - {process_time:.3f}s"
            )
            
            return response
            
        except HTTPException:
            # FastAPI HTTPExceptions, let them pass through
            raise
            
        except Exception as exc:
            # Map custom exceptions to HTTP
            http_exc = map_exception_to_http(exc)
            
            # Log the original exception for debugging
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: "
                f"{type(exc).__name__}: {exc}",
                exc_info=True
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=http_exc.status_code,
                content=http_exc.detail
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware pour logging des requêtes"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"→ {request.method} {request.url.path} {dict(request.query_params)}")
        
        try:
            response = await call_next(request)
            
            # Log successful response
            process_time = time.time() - start_time
            logger.info(
                f"← {response.status_code} {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )
            
            return response
            
        except Exception as exc:
            # Log failed request
            process_time = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} failed after {process_time:.3f}s: "
                f"{type(exc).__name__}: {exc}"
            )
            raise
