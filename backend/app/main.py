from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .api.v1.routers import analyses, batches, health
from .core.database import create_tables
from .core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 ArbitrageVault BookFinder API starting...")
    logger.info(f"📊 Version: {settings.app.version}")
    logger.info(f"🔧 Debug mode: {settings.app.debug}")
    
    if settings.app.debug:
        logger.info("💾 Creating database tables (development mode)")
        create_tables()
    
    yield
    
    # Shutdown
    logger.info("🛑 ArbitrageVault BookFinder API shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application with all configurations"""
    
    app = FastAPI(
        title=settings.app.app_name,
        version=settings.app.version,
        description="Tool for identifying profitable book arbitrage opportunities using Keepa API data analysis",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )
    
    # Add custom middleware (order matters - first added = outer layer)
    app.add_middleware(ErrorHandlingMiddleware)
    
    if settings.app.debug:
        app.add_middleware(RequestLoggingMiddleware)
    
    # CORS configuration for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React dev server
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ] if settings.app.debug else [],  # Restrict in production
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(
        analyses.router,
        prefix="/api/v1/analyses",
        tags=["analyses"]
    )
    
    app.include_router(
        batches.router,
        prefix="/api/v1/batches",
        tags=["batches"]
    )
    
    app.include_router(
        health.router,
        prefix="/api/v1/health",
        tags=["health"]
    )
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "ArbitrageVault BookFinder API",
            "version": settings.app.version,
            "status": "running",
            "docs_url": "/docs" if not settings.is_production else None
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
        log_level="info"
    )