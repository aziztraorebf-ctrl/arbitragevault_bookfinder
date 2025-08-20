from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.v1.routers import analyses, batches, health
from .core.database import create_tables
from .config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 ArbitrageVault BookFinder API starting...")
    if settings.app.debug:
        print("📊 Creating database tables (development mode)")
        create_tables()
    
    yield
    
    # Shutdown
    print("🛑 ArbitrageVault BookFinder API shutting down...")


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
